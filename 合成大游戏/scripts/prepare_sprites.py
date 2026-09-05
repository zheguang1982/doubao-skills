#!/usr/bin/env python3
"""把任意图片批量处理成合成大西瓜类游戏所需的各级贴图。

处理链：去白底 -> 等比缩放 -> 居中贴透明画布 -> 写盘后回读断言。

用法:
    python3 prepare_sprites.py --src <图片目录或文件列表> --out <输出目录>
    python3 prepare_sprites.py --src imgs/ --out out/ --sizes 80,92,108
"""
import argparse
import os
import re
import sys
from collections import deque

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow: pip3 install Pillow")

# 游戏 10 个水果槽位的真实尺寸（源自 liyupi/daxigua 实测，勿改）
GAME_SIZES = [
    (80, 80), (108, 108), (119, 119), (153, 152), (183, 183),
    (193, 193), (258, 258), (308, 308), (308, 309), (408, 408),
]

IMG_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}


def flood_remove_bg(im, tol=28):
    """四角泛洪去白底。

    只删除与画布边框连通的浅色区域，主体内部的白色（白毛、白描边、
    高光）完整保留——这是与"全局删白"最关键的区别。
    """
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()

    def is_bg(c):
        return c[0] >= 255 - tol and c[1] >= 255 - tol and c[2] >= 255 - tol

    seen = bytearray(w * h)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            dq.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            dq.append((x, y))

    while dq:
        x, y = dq.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        if not is_bg(px[x, y]):
            continue
        px[x, y] = (255, 255, 255, 0)
        dq.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return im


def crop_to_content(im):
    """裁到主体外接框，避免留白导致主体偏小。"""
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def fit_canvas(im, tw, th, fill=0.94):
    """等比缩放后居中贴到 tw x th 透明画布。

    等比而非拉伸，因此 153x152 这类非正方尺寸也不会变形。
    """
    im = crop_to_content(im)
    sw, sh = im.size
    scale = min(tw * fill / sw, th * fill / sh)
    nw, nh = max(1, round(sw * scale)), max(1, round(sh * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    canvas.paste(im, ((tw - nw) // 2, (th - nh) // 2), im)
    return canvas


def natural_key(path):
    """自然排序键：让 2.png 排在 10.png 前面。

    默认字符串排序会把 "10" 排到 "2" 之前（逐字符比较 '1'<'2'），
    用户按 1.png..10.png 命名时顺序会静默错乱，故按数字段切分比较。
    """
    name = os.path.basename(path)
    parts = re.split(r'(\d+)', name)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def collect(src):
    """收集源图片。

    目录：按自然排序，保证 1,2,...,10 的直觉顺序。
    逗号分隔列表：严格保留用户给定的先后顺序，不重排。
    """
    if os.path.isdir(src):
        files = [os.path.join(src, f) for f in os.listdir(src)
                 if os.path.splitext(f)[1].lower() in IMG_EXT]
        files.sort(key=natural_key)
    else:
        files = [f.strip() for f in src.split(',') if f.strip()]
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='图片目录，或逗号分隔的文件列表')
    ap.add_argument('--out', required=True, help='输出目录')
    ap.add_argument('--sizes', help='自定义尺寸 80,92,108（缺省用游戏 10 级标准尺寸）')
    ap.add_argument('--no-bg-removal', action='store_true', help='源图已透明时跳过去底')
    ap.add_argument('--tol', type=int, default=28, help='去底容差，默认 28')
    args = ap.parse_args()

    if args.sizes:
        sizes = []
        for part in args.sizes.split(','):
            part = part.strip()
            if not part:
                continue
            if 'x' in part.lower():
                a, b = part.lower().split('x')
                sizes.append((int(a), int(b)))
            else:
                sizes.append((int(part), int(part)))
    else:
        sizes = GAME_SIZES

    files = collect(args.src)
    if not files:
        sys.exit(f"未找到图片: {args.src}")

    print(f"源图 {len(files)} 张，目标 {len(sizes)} 个尺寸")
    if len(files) < len(sizes):
        print(f"  注意：源图不足，将循环复用补齐 {len(sizes)} 级")

    os.makedirs(args.out, exist_ok=True)
    results, failed = [], []

    for idx, (tw, th) in enumerate(sizes):
        src_file = files[idx % len(files)]
        try:
            im = Image.open(src_file)
            im = im.convert('RGBA') if args.no_bg_removal else flood_remove_bg(im, args.tol)
            out_im = fit_canvas(im, tw, th)
            name = f"sprite_lv{idx}_{tw}x{th}.png"
            path = os.path.join(args.out, name)
            out_im.save(path, 'PNG', optimize=True)

            # 写盘后回读断言——不信任内存对象，只信盘上结果
            chk = Image.open(path)
            assert chk.size == (tw, th), f"尺寸不符 {chk.size}"
            assert chk.mode == 'RGBA', f"模式不符 {chk.mode}"
            a = chk.getchannel('A')
            corners = [a.getpixel(p) for p in
                       [(0, 0), (tw - 1, 0), (0, th - 1), (tw - 1, th - 1)]]
            transparent = all(v == 0 for v in corners)

            results.append((idx, name, tw, th, transparent))
            flag = 'OK' if transparent else 'OK(角落不透明)'
            print(f"  lv{idx:<2} {tw}x{th:<4} <- {os.path.basename(src_file):<28} {flag}")
        except Exception as e:
            failed.append((idx, src_file, str(e)))
            print(f"  lv{idx:<2} {tw}x{th:<4} 失败: {e}")

    print(f"\n完成 {len(results)}/{len(sizes)}，输出目录 {args.out}")
    if failed:
        print("失败项:")
        for i, f, e in failed:
            print(f"  lv{i} {f}: {e}")
        sys.exit(1)
    opaque = [r for r in results if not r[4]]
    if opaque:
        print(f"提示：{len(opaque)} 张四角不透明，可能去底不净，建议调大 --tol")


if __name__ == '__main__':
    main()
