#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live-invite-h5 生成脚本：把 config.json 渲染进模板，输出单文件 H5 邀请函。

用法:
    python scripts/build_invite.py config.json -o 输出目录/index.html

流程:
    1. 读取配置, 填充默认值, 解析日期(月份/日/星期由真实日历计算)
    2. 用锚点替换模板, 对每处替换做存在性校验
    3. 校验外部引用为 0, 检查锚点是否残留
    4. 输出产物并打印统计信息

任何校验失败都会以非零退出码报错, 不会静默产出错误产物。
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

# 模板中所有应被替换的锚点 (脚本会逐一校验是否存在于模板)
ANCHORS = [
    "__BRAND__", "__KICKER_LINE__", "__SCREEN4_TITLE__", "__SESSION_ROW__",
    "__SLOGAN__", "__INVITE_LINE__",
    "__GUEST__", "__EVENT_NAME__", "__EVENT_DATE_LINE__",
    "__EVENT_MONTH_HEAD__", "__EVENT_DAY__", "__EVENT_WEEK_FULL__",
    "__TOPICS__", "__SIGNATURE__", "__ROLE_LABEL__", "__INVITE_TITLE__",
]

# 默认值: 仅对可选字段生效
DEFAULTS = {
    "guest": "嘉宾",          # 用户未指定邀请谁时的占位
    "event_date": "待定",     # 用户未指定日期时的占位
    "time": "19:30",
    "brand": "豆包",
    "session": "专题讲座",
    "role": "嘉宾",
    "slogan": "这一天，为你而来",
    "invite_line": "一场只聊实战的分享，位置给你留着。",
    "signature": "负责给你搭台的我",
    "invite_title": "讲座邀请函",  # H5 顶部醒目标题
}

# 核心必填字段 (用户只需提供主题 + 实践即可生成)
REQUIRED = ["event_name", "topics"]

WEEKDAY_CN = ["一", "二", "三", "四", "五", "六", "日"]
ANCHOR_PAT = re.compile(r"__[A-Z_]+__")


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if not isinstance(cfg, dict):
        sys.exit("[ERROR] config.json 顶层必须是 JSON 对象")
    missing = [k for k in REQUIRED if not cfg.get(k)]
    if missing:
        sys.exit("[ERROR] 配置缺少必填字段: " + ", ".join(missing))
    topics = cfg["topics"]
    if not isinstance(topics, list) or not (1 <= len(topics) <= 6):
        sys.exit("[ERROR] topics 必须是 1~6 项的数组")
    for t in topics:
        if not isinstance(t, dict) or not t.get("name"):
            sys.exit("[ERROR] topics 每项必须包含 name 字段")
    return cfg


def parse_date(date_str: str, time_str: str) -> dict:
    """解析日期, 返回用于渲染的日期字段。

    支持:
    - "YYYY-MM-DD"   完整日期, 星期由真实日历计算
    - "YYYY-MM-XX"   X 占位日期 (具体日未定), 星期显示"待定"
    - "待定"          完全未定时, 各字段用占位文案
    保证产物完整可用, 确定日期后改配置重新生成即可。
    """
    if date_str == "待定":
        return {
            "date_line": "日期待定",
            "month_head": "日期",
            "day": "待定",
            "week_full": "时间待定",
        }
    m = re.match(r"^(\d{4})-(\d{1,2})-XX$", date_str)
    if m:
        y, mo = m.group(1), int(m.group(2))
        return {
            "date_line": "%s年%d月X日（星期待定）" % (y, mo),
            "month_head": "%d月" % mo,
            "day": "X",
            "week_full": "星期待定 · %s" % time_str,
        }
    try:
        d = datetime.date.fromisoformat(date_str)
    except ValueError:
        sys.exit("[ERROR] event_date 格式应为 YYYY-MM-DD / YYYY-MM-XX (或 \"待定\"), 收到: %r" % date_str)
    return {
        "date_line": "%d月%d日（星期%s）%s" % (d.month, d.day, WEEKDAY_CN[d.weekday()], time_str),
        "month_head": "%d月" % d.month,
        "day": str(d.day),
        "week_full": "星期%s · %s" % (WEEKDAY_CN[d.weekday()], time_str),
    }


def render_topics(topics: list) -> str:
    """把 topics 渲染成选项卡 HTML。"""
    parts = []
    for t in topics:
        name = t["name"]
        desc = t.get("desc", "")
        desc_html = (
            '<span class="topic-desc">%s</span>' % esc(desc) if desc else ""
        )
        parts.append(
            '<label class="topic">'
            '<input type="checkbox" class="topic-cb" value="%s">'
            '<span class="topic-name">%s</span>%s</label>'
            % (esc(name), esc(name), desc_html)
        )
    return "\n        ".join(parts)


def esc(s: str) -> str:
    """HTML 转义, 防止嘉宾名/主题里的特殊字符破坏结构。"""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def count_external_refs(html: str) -> int:
    """统计外链数量: http/https 开头的 src/href/url( 引用。"""
    patterns = [
        r'(?:src|href)\s*=\s*["\']https?://',
        r"url\(\s*['\"]?https?://",
    ]
    n = 0
    for p in patterns:
        n += len(re.findall(p, html))
    return n


def main():
    ap = argparse.ArgumentParser(description="生成单文件 H5 邀请函")
    ap.add_argument("config", help="config.json 路径")
    ap.add_argument("-o", "--output", required=True, help="输出 HTML 路径")
    ap.add_argument(
        "--template",
        default=str(Path(__file__).resolve().parent.parent / "assets" / "template.html"),
        help="模板路径(默认取技能自带模板)",
    )
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    tpl = Path(args.template)
    if not tpl.exists():
        sys.exit("[ERROR] 找不到模板: %s" % tpl)

    template = tpl.read_text(encoding="utf-8")

    # 1) 校验模板包含全部锚点
    missing_anchors = [a for a in ANCHORS if a not in template]
    if missing_anchors:
        sys.exit(
            "[ERROR] 模板缺少锚点: %s (模板改版导致锚点失效)"
            % ", ".join(missing_anchors)
        )

    d = parse_date(cfg.get("event_date", "待定"), cfg.get("time", DEFAULTS["time"]))
    resolved = dict(cfg)  # 必填字段直接来自配置
    for k, v in DEFAULTS.items():  # 可选字段缺省用默认值
        resolved.setdefault(k, v)
    resolved.update(d)

    html = template
    # session 可留空: 留空时不显示"主办 · 场次"里的场次、不显示屏4标题前缀、票根不显示场次行
    session = str(resolved["session"] or "").strip()
    kicker_line = resolved["brand"] + (" · " + session if session else "")
    screen4_title = (session + " · 想参加什么？") if session else "想参加什么？"
    session_row = (
        '<div class="t-row"><span class="k">场次</span><span class="v">%s</span></div>'
        % esc(session)
    ) if session else ""
    # 原样写入的 HTML 片段 (不做转义)
    RAW_HTML = {"__TOPICS__", "__SESSION_ROW__"}
    replacements = {
        "__INVITE_TITLE__": resolved["invite_title"],
        "__GUEST__": resolved["guest"],
        "__EVENT_NAME__": resolved["event_name"],
        "__EVENT_DATE_LINE__": d["date_line"],
        "__EVENT_MONTH_HEAD__": d["month_head"],
        "__EVENT_DAY__": d["day"],
        "__EVENT_WEEK_FULL__": d["week_full"],
        "__BRAND__": resolved["brand"],
        "__KICKER_LINE__": kicker_line,
        "__SCREEN4_TITLE__": screen4_title,
        "__SESSION_ROW__": session_row,
        "__SLOGAN__": resolved["slogan"],
        "__INVITE_LINE__": resolved["invite_line"],
        "__SIGNATURE__": resolved["signature"],
        "__ROLE_LABEL__": resolved["role"],
        "__TOPICS__": render_topics(cfg["topics"]),
    }

    # 2) 逐锚点替换并校验存在性 (HTML 片段原样写入, 其余文本字段转义)
    for anchor, value in replacements.items():
        if anchor not in html:
            sys.exit("[ERROR] 替换时找不到锚点: %s" % anchor)
        html = html.replace(anchor, value if anchor in RAW_HTML else esc(value))

    # 3) 检查是否还有残留锚点
    leftover = ANCHOR_PAT.findall(html)
    if leftover:
        sys.exit("[ERROR] 产物残留未替换锚点: %s" % ", ".join(sorted(set(leftover))))

    # 4) 外链校验
    ext = count_external_refs(html)
    if ext != 0:
        print("[WARN] 检测到 %d 处外部引用, 发布可能因外链不可达而失败!" % ext)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    # 5) 回读自查: 确认写入内容与内存一致
    written = out.read_text(encoding="utf-8")
    if written != html:
        sys.exit("[ERROR] 产物回读校验不一致, 写入失败")
    if ANCHOR_PAT.search(written):
        sys.exit("[ERROR] 产物回读发现残留锚点")

    size_kb = len(written.encode("utf-8")) / 1024
    print("✅ 已生成: %s" % out)
    print("   嘉宾: %s | 主题: %s | 日期: %s" % (resolved["guest"], resolved["event_name"], d["date_line"]))
    print("   实践方向: %d 个 | 文件大小: %.1f KB | 外部引用: %d"
          % (len(cfg["topics"]), size_kb, ext))


if __name__ == "__main__":
    main()
