#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载「国家中小学智慧教育平台」(basic.smartedu.cn) 电子教材 PDF，无需登录。

原理（三跳，均为基础 HTTP）：
  1) 教材清单：GET https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/version/data_version.json
     -> {"urls": "part_100.json,part_101.json,..."}，逐个拉取得到全部教材条目（含 id/title/tag_list）。
  2) 元数据：GET https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/resources/tch_material/details/{contentId}.json
     -> ti_items 中 ti_is_source_file=True 且 ti_format="pdf" 的 ti_storages[0] 即 PDF 直链。
  3) 下载：对 r1-ndr-private.ykt.cbern.com.cn 直链做 UTF-8 百分号编码后 GET，
     携带占位鉴权头（Authorization: Bearer 0 / X-ND-AUTH: MAC id="0",nonce="0",mac="0"），
     校验响应以 %PDF 开头且大小与元数据一致。

用法示例：
  python download_tchmaterial.py detail "https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=2e3dc199-9c42-486b-bbee-7731bd0ee227&catalogType=tchMaterial&subCatalog=tchMaterial" -o ./books
  python download_tchmaterial.py list --filter "小学/语文/统编版" --grade 一年级
  python download_tchmaterial.py batch --filter "小学/语文/统编版" -o ./books
  python download_tchmaterial.py batch "https://basic.smartedu.cn/tchMaterial?defaultTag=e7bbb2de-.../6a749654-..." -o ./books
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from urllib.parse import urlsplit, urlunsplit, parse_qs, quote, unquote

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://basic.smartedu.cn/",
    "Origin": "https://basic.smartedu.cn",
    "Authorization": "Bearer 0",
    "X-ND-AUTH": 'MAC id="0",nonce="0",mac="0"',
}

# 教材清单分片索引
VERSION_INDEX = "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/version/data_version.json"
# 标签层级（tag_id -> 名称，用于解析目录页 defaultTag）
TAG_HIERARCHY = "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/tch_material_tag.json"
# 私有 CDN 前缀（元数据里 cs_path:${ref-path} 的替代值）
PRIVATE_CDN = "https://r1-ndr-private.ykt.cbern.com.cn"

DIM_STAGE = "zxxxd"   # 学段：小学/初中/高中
DIM_SUBJECT = "zxxxk" # 学科：语文/数学...
DIM_EDITION = "zxxbb" # 版别：统编版/人教版...
DIM_GRADE = "zxxnj"   # 年级：一年级~六年级...
DIM_SEM = "zxxcc"     # 册次：上册/下册


def _request(url, timeout=120):
    """带平台鉴权头的 GET，返回原始字节。"""
    req = urllib.request.Request(url, headers=BASE_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def fetch_json(url, timeout=120):
    _, raw = _request(url, timeout)
    return json.loads(raw.decode("utf-8"))


def encode_url_path(url):
    """对 URL 的 path 做 UTF-8 百分号编码（中文/• 等字符不能直接进请求行）。"""
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, quote(p.path), p.query, p.fragment))


def load_books():
    """拉取全部电子教材条目。返回 list[dict]，每项含 id/title/tag_list 等。"""
    ver = fetch_json(VERSION_INDEX)
    urls = [u.strip() for u in ver["urls"].split(",") if u.strip()]
    books = []
    for u in urls:
        books.extend(fetch_json(u))
    return books


def tag_map(book):
    """book 的 tag_list -> {tag_dimension_id: tag_name} 与 {tag_name: tag_id}。"""
    by_dim, by_name = {}, {}
    for t in book.get("tag_list") or []:
        by_dim[t.get("tag_dimension_id")] = t.get("tag_name")
        by_name[t.get("tag_name")] = t.get("tag_id")
    return by_dim, by_name


def build_tag_name_index():
    """拉取标签层级，返回 {tag_id: tag_name}，用于把目录页 defaultTag 的 id 转成名称。"""
    data = fetch_json(TAG_HIERARCHY)
    mapping = {}

    def walk(nodes):
        for n in nodes or []:
            if n.get("tag_id"):
                mapping[n["tag_id"]] = n.get("tag_name")
            walk(n.get("hierarchies") or n.get("children"))
            for ch in n.get("children") or []:
                mapping[ch.get("tag_id")] = ch.get("tag_name")
                walk(ch.get("hierarchies") or [])

    walk(data.get("hierarchies"))
    return mapping


def decode_catalog_url(url):
    """把 tchMaterial 目录页 URL 的 defaultTag（tag_id 列表）解析为 tag_name 列表。"""
    q = parse_qs(urlsplit(url).query)
    tag_ids = [unquote(x) for x in q.get("defaultTag", [""])[0].split("/") if x]
    if not tag_ids:
        return []
    mapping = build_tag_name_index()
    return [mapping.get(tid, tid) for tid in tag_ids]


def matches(book, filters, grade=None, semester=None):
    by_dim, by_name = tag_map(book)
    if filters:
        for seg in filters:
            if seg and seg not in by_name:
                return False
    if grade and by_dim.get(DIM_GRADE) != grade:
        return False
    if semester and by_dim.get(DIM_SEM) != semester:
        return False
    return True


def select_books(books, filters=None, grade=None, semester=None):
    return [b for b in books if matches(b, filters, grade, semester)]


def meta_of(content_id):
    """获取教材元数据 JSON，返回 dict。"""
    url = f"https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/resources/tch_material/details/{content_id}.json"
    return fetch_json(url)


def pdf_url_of(meta):
    """从元数据 ti_items 中提取 PDF 源文件直链与大小。"""
    for item in meta.get("ti_items", []):
        if not item.get("ti_is_source_file"):
            continue
        if item.get("ti_format") != "pdf":
            continue
        url = item.get("ti_storage") or ""
        if url.startswith("cs_path"):
            url = url.replace("cs_path:${ref-path}", PRIVATE_CDN)
        elif not url:
            url = next((u for u in item.get("ti_storages") or [] if u), None)
        return url, item.get("ti_size")
    # 兜底：按 ti_file_flag 判断
    for item in meta.get("ti_items", []):
        if item.get("ti_file_flag") != "source":
            continue
        if item.get("ti_format") != "pdf":
            continue
        url = item.get("ti_storage") or next((u for u in item.get("ti_storages") or [] if u), None)
        if url:
            return url, item.get("ti_size")
    return None, None


def pretty_name(book):
    """生成简洁文件名：学科+年级+册次.pdf，缺标签则回退到标题。"""
    by_dim, _ = tag_map(book)
    subject = by_dim.get(DIM_SUBJECT) or ""
    grade = by_dim.get(DIM_GRADE) or ""
    sem = by_dim.get(DIM_SEM) or ""
    if subject and (grade or sem):
        base = f"{subject}{grade}{sem}"
    else:
        gtitle = book.get("global_title") or {}
        base = gtitle.get("zh-CN") or book.get("title") or book["id"]
    base = re.sub(r'[\\/:*?"<>|]', "_", base).strip()
    return f"{base}.pdf"


def download_pdf(content_id, out_path, timeout=180):
    """下载单本教材，返回 (ok, message, size)。"""
    meta = meta_of(content_id)
    url, meta_size = pdf_url_of(meta)
    if not url:
        return False, "元数据中未找到 PDF 源文件", 0
    status, data = _request(encode_url_path(url), timeout=timeout)
    if status != 200:
        return False, f"HTTP {status}", len(data)
    if not data.startswith(b"%PDF"):
        return False, f"非 PDF 响应（前8字节={data[:8]!r}）", len(data)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    size = os.path.getsize(out_path)
    if meta_size and abs(size - meta_size) > 2:
        return True, f"大小不一致(实际{size}/元数据{meta_size})", size
    return True, "OK", size


def cmd_detail(args):
    raw = args.url_or_id
    if raw.startswith("http"):
        cid = parse_qs(urlsplit(raw).query).get("contentId", [None])[0]
    else:
        cid = raw
    if not cid:
        print("无法从输入解析 contentId")
        sys.exit(1)
    meta = meta_of(cid)
    gtitle = meta.get("global_title") or {}
    title = gtitle.get("zh-CN") or meta.get("title") or cid
    out_dir = args.output or "."
    name = args.name or (re.sub(r'[\\/:*?"<>|]', "_", title).strip() + ".pdf")
    out = os.path.join(out_dir, name)
    print(f"书名: {title}")
    ok, msg, size = download_pdf(cid, out, args.timeout)
    print(f"[{'OK' if ok else 'FAIL'}] {name}  {size} 字节  {msg}")
    if ok and args.verify:
        verify_pdf(out)
    sys.exit(0 if ok else 1)


def cmd_list(args):
    books = load_books()
    filters = args.filter.split("/") if args.filter else []
    selected = select_books(books, filters, args.grade, args.semester)
    if not selected:
        print("未找到匹配的教材，可尝试放宽 --filter/--grade/--semester")
        sys.exit(1)
    selected.sort(key=lambda b: (
        (tag_map(b)[0].get(DIM_STAGE) or ""),
        (tag_map(b)[0].get(DIM_SUBJECT) or ""),
        (tag_map(b)[0].get(DIM_GRADE) or ""),
        (tag_map(b)[0].get(DIM_SEM) or ""),
    ))
    for b in selected:
        by_dim, _ = tag_map(b)
        print(" | ".join(filter(None, [
            by_dim.get(DIM_STAGE), by_dim.get(DIM_SUBJECT), by_dim.get(DIM_EDITION),
            by_dim.get(DIM_GRADE), by_dim.get(DIM_SEM), b["id"],
        ])), "|", b.get("title"))
    if args.json:
        print("\n--json--")
        print(json.dumps([{**tag_map(b)[0], "id": b["id"], "title": b["title"]} for b in selected], ensure_ascii=False, indent=2))


def cmd_batch(args):
    filters = []
    if args.url and "tchMaterial" in args.url and "detail" not in args.url:
        filters = decode_catalog_url(args.url)
        print("目录页标签:", "/".join(filters) or "(空)")
    if args.filter:
        filters = args.filter.split("/")
    books = load_books()
    selected = select_books(books, filters, args.grade, args.semester)
    if not selected:
        print("未找到匹配的教材")
        sys.exit(1)
    print(f"匹配 {len(selected)} 本：")
    for b in selected:
        print("  -", b.get("title"))
    out_dir = args.output or "."
    ok_n = 0
    for b in selected:
        name = pretty_name(b)
        out = os.path.join(out_dir, name)
        if args.skip_existing and os.path.exists(out) and os.path.getsize(out) > 1000:
            print(f"[SKIP] {name} 已存在")
            ok_n += 1
            continue
        ok, msg, size = download_pdf(b["id"], out, args.timeout)
        print(f"[{'OK' if ok else 'FAIL'}] {name}  {size} 字节  {msg}")
        ok_n += 1 if ok else 0
        time.sleep(args.sleep)
    print(f"\n成功 {ok_n}/{len(selected)}")


def verify_pdf(path):
    """可选：用 pymupdf 检查页数与首页文字（未安装则跳过）。"""
    try:
        import pymupdf
    except ImportError:
        print("(未安装 pymupdf，跳过页数校验)")
        return
    doc = pymupdf.open(path)
    p1 = " ".join(doc[0].get_text().split())[:40]
    print(f"页数: {doc.page_count}  首页: {p1}")
    doc.close()


def main():
    ap = argparse.ArgumentParser(description="国家中小学智慧教育平台电子教材下载器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_detail = sub.add_parser("detail", help="下载单本教材：传入详情页 URL 或 contentId")
    p_detail.add_argument("url_or_id", help="详情页 URL 或 contentId")
    p_detail.add_argument("-o", "--output", default=".", help="输出目录（默认当前目录）")
    p_detail.add_argument("--name", help="自定义文件名（默认按书名）")
    p_detail.add_argument("--verify", action="store_true", help="下载后用 pymupdf 校验页数")
    p_detail.add_argument("--timeout", type=int, default=180)
    p_detail.set_defaults(func=cmd_detail)

    p_list = sub.add_parser("list", help="列出符合筛选条件的教材（不下载）")
    p_list.add_argument("--filter", help="按标签名筛选，/ 分隔，如 小学/语文/统编版")
    p_list.add_argument("--grade", help="年级，如 一年级")
    p_list.add_argument("--semester", help="册次，如 上册")
    p_list.add_argument("--json", action="store_true", help="额外输出 JSON")
    p_list.set_defaults(func=cmd_list)

    p_batch = sub.add_parser("batch", help="批量下载符合筛选条件的教材")
    p_batch.add_argument("url", nargs="?", help="可选：tchMaterial 目录页 URL（自动解析 defaultTag）")
    p_batch.add_argument("--filter", help="按标签名筛选，/ 分隔，如 小学/语文/统编版")
    p_batch.add_argument("--grade", help="年级，如 一年级")
    p_batch.add_argument("--semester", help="册次，如 上册")
    p_batch.add_argument("-o", "--output", default=".", help="输出目录")
    p_batch.add_argument("--skip-existing", action="store_true", help="跳过已存在的文件")
    p_batch.add_argument("--sleep", type=float, default=0.3, help="每本之间间隔秒数")
    p_batch.add_argument("--timeout", type=int, default=180)
    p_batch.set_defaults(func=cmd_batch)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
