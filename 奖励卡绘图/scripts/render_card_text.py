#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_card_text.py — 在「无字插画」上叠加水墨奖励卡的文字系统。

用途：当模型直接写字不可靠时（中文错字率高），先生成一张只有插画、
下部完全留白的 1:1 图，再用本脚本叠手写行楷、朱红奖励项目、印章与落款。

用法：
  python render_card_text.py --image illo.png --reward "作业全对" \\
      --quote "你把每个字|都写得很认真" --name "李子涵" --date "2026.11.18" \\
      --seal "进步" --out card.png

  # 不传 --image 时输出一张纯空白卡，用于先排文字位置
  python render_card_text.py --reward "作业全对" --quote "你把每个字|都写得很认真"

依赖：Pillow（pip install pillow）
"""

import argparse
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

PAPER = (251, 248, 241)       # #FBF8F1 宣纸白
INK = (43, 43, 43)            # #2B2B2B 焦墨
INK_SOFT = (110, 110, 110)    # #6E6E6E 灰墨
VERMILION = (179, 58, 43)     # #B33A2B 朱红

FONT_CANDIDATES = [
    r"C:\\Windows\\Fonts\\STXINGKA.TTF",   # 华文行楷
    r"C:\\Windows\\Fonts\\STKAITI.TTF",    # 华文楷体
    r"C:\\Windows\\Fonts\\simkai.ttf",     # 楷体
    r"C:\\Windows\\Fonts\\simhei.ttf",     # 黑体（最后兜底）
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/truetype/arphic/ukai.ttc",
]


def pick_font_path():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def load_font(path, size):
    if path is None:
        return ImageFont.load_default()
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def text_width(font, s, tracking=0):
    w = 0
    for ch in s:
        bb = font.getbbox(ch)
        w += (bb[2] - bb[0]) + tracking
    return max(w - tracking, 1) if s else 1


def fit_font(font_path, s, max_width, start_size, tracking_ratio=0.12):
    """按可用宽度自动缩字号。"""
    size = start_size
    while size > 12:
        f = load_font(font_path, size)
        if text_width(f, s, int(size * tracking_ratio)) <= max_width:
            return f, int(size * tracking_ratio)
        size -= 2
    f = load_font(font_path, 12)
    return f, 1


def draw_hand_line(canvas, text, font_path, size, center_x, top_y,
                   fill=INK, tracking_ratio=0.14, jitter=1.0, bleed=True):
    """逐字绘制，带轻微抖动与墨渗，模拟手写。返回行高。

    所有字形先画进同一张全幅图层，再整体模糊一次做墨渗，
    保证渗色与字形严丝合缝，不产生偏移阴影。
    """
    if not text:
        return 0
    font = load_font(font_path, size)
    tracking = int(size * tracking_ratio)
    total = text_width(font, text, tracking)
    x = center_x - total / 2
    ascent, descent = font.getmetrics()
    line_h = ascent + descent

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    xx = x
    for ch in text:
        bb = font.getbbox(ch)
        glyph = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glyph)
        gd.text((4 - bb[0], 4 - bb[1]), ch, font=font, fill=fill + (255,))
        ang = random.uniform(-jitter, jitter)
        if abs(ang) > 0.05:
            glyph = glyph.rotate(ang, resample=Image.BICUBIC, expand=True)
        px = int(xx - 4 + random.uniform(-0.6, 0.6))
        py = int(top_y + random.uniform(-0.8, 0.8))
        layer.paste(glyph, (px, py), glyph)
        xx += (bb[2] - bb[0]) + tracking

    if bleed:
        soft = layer.filter(ImageFilter.GaussianBlur(0.9))
        alpha = soft.getchannel("A").point(lambda a: int(a * 0.34))
        soft.putalpha(alpha)
        canvas.alpha_composite(soft)
    canvas.alpha_composite(layer)
    return line_h


def paper_texture(img, strength=1.0):
    """极淡纸纤维颗粒。"""
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random(7)
    n = int(w * h / 1500 * strength)
    for _ in range(n):
        x = rnd.uniform(0, w)
        y = rnd.uniform(0, h)
        a = rnd.randint(2, 5)
        d.point((x, y), fill=(120, 112, 96, a))
    return img


def _match_paper(illo, paper=PAPER):
    """把插画的纸底按通道增益校正到宣纸白，消除贴图色差。"""
    w, h = illo.size
    samples = []
    for x in range(0, w, 6):
        samples.append(illo.getpixel((x, 2)))
        samples.append(illo.getpixel((x, h - 3)))
    for y in range(0, h, 6):
        samples.append(illo.getpixel((2, y)))
        samples.append(illo.getpixel((w - 3, y)))
    light = [p for p in samples if sum(p[:3]) / 3 > 200]
    if not light:
        return illo
    mean = [sum(p[i] for p in light) / len(light) for i in range(3)]
    r, g, b = illo.split()
    gains = [max(0.80, min(1.30, paper[i] / max(mean[i], 1))) for i in range(3)]
    return Image.merge("RGB", (
        r.point(lambda v, k=gains[0]: min(255, int(v * k))),
        g.point(lambda v, k=gains[1]: min(255, int(v * k))),
        b.point(lambda v, k=gains[2]: min(255, int(v * k))),
    ))


def paste_illustration(canvas, illo, ox, oy):
    """羽化边缘 + 底色匹配，让插画与宣纸底无缝融合，避免矩形接缝。"""
    illo = illo.convert("RGB")
    illo = _match_paper(illo)
    paper_layer = Image.new("RGB", illo.size, PAPER)
    illo = Image.blend(illo, paper_layer, 0.06)

    w, h = illo.size
    feather = max(10, int(min(w, h) * 0.09))
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([feather, feather, w - feather - 1, h - feather - 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather / 1.6))

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.paste(illo, (0, 0))
    layer.putalpha(mask)
    canvas.alpha_composite(layer, (int(ox), int(oy)))


def draw_seal(canvas, chars, cx, cy, side, color=VERMILION, seed=3):
    """朱红方印：不规则边缘 + 斑驳缺口 + 反白字。"""
    rnd = random.Random(seed)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    half = side / 2
    # 不规则方形
    pts = []
    steps = 28
    for i in range(steps):
        t = i / steps * 4
        if t < 1:
            x, y = -half + t * side, -half
        elif t < 2:
            x, y = half, -half + (t - 1) * side
        elif t < 3:
            x, y = half - (t - 2) * side, half
        else:
            x, y = -half, half - (t - 3) * side
        pts.append((cx + x + rnd.uniform(-1.6, 1.6), cy + y + rnd.uniform(-1.6, 1.6)))
    d.polygon(pts, fill=color + (235,))

    # 斑驳：挖掉若干小点
    for _ in range(int(side * side / 90)):
        px = cx + rnd.uniform(-half, half)
        py = cy + rnd.uniform(-half, half)
        r = rnd.uniform(0.4, 1.5)
        d.ellipse([px - r, py - r, px + r, py + r], fill=(0, 0, 0, 0))

    # 反白字（二字竖排，四字田字）
    font_path = pick_font_path()
    n = len(chars)
    if n <= 2:
        fs = int(side * 0.46)
        font = load_font(font_path, fs)
        gap = side * 0.10
        for i, ch in enumerate(chars):
            top = cy - (fs + gap) * (n - 1) / 2 - fs / 2 + (fs + gap) * i
            bb = font.getbbox(ch)
            d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], top + fs * 0.06), ch, font=font,
                   fill=PAPER + (250,))
    elif n == 4:
        fs = int(side * 0.40)
        font = load_font(font_path, fs)
        off = side * 0.22
        for i, ch in enumerate(chars):
            cxx = cx + (off if i % 2 else -off)
            cyy = cy + (off if i >= 2 else -off)
            bb = font.getbbox(ch)
            d.text((cxx - (bb[2] - bb[0]) / 2 - bb[0], cyy - fs * 0.55), ch, font=font,
                   fill=PAPER + (245,))
    else:
        fs = int(side * 0.30)
        font = load_font(font_path, fs)
        bb = font.getbbox(chars)
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - fs * 0.55), chars, font=font,
               fill=PAPER + (245,))

    canvas.alpha_composite(layer)


def main():
    ap = argparse.ArgumentParser(description="水墨奖励卡叠字")
    ap.add_argument("--image", help="无字插画（可省略，省略则输出空白卡）")
    ap.add_argument("--reward", default="", help="奖励项目，朱红大字")
    ap.add_argument("--quote", default="", help="金句，用 | 分行，最多 2 行")
    ap.add_argument("--name", default="", help="学生姓名")
    ap.add_argument("--date", default="", help="日期")
    ap.add_argument("--seal", default="", help="印章文字，2-4 字")
    ap.add_argument("--sign", default="", help="落款人，如 李老师")
    ap.add_argument("--layout", default="l1", choices=["l1", "l2", "l3"])
    ap.add_argument("--accent", default="#B33A2B", help="奖励项目颜色")
    ap.add_argument("--size", type=int, default=1440, help="输出边长，默认 1440")
    ap.add_argument("--out", default="card.png")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    random.seed(args.seed)
    S = args.size
    accent = tuple(int(args.accent.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    canvas = Image.new("RGBA", (S, S), PAPER + (255,))

    # ---- 插画区 ----
    pad = int(S * 0.06)                   # 外边距 6%
    max_w = S - pad * 2
    illo_zone_top = int(S * 0.07)
    illo_zone_h = int(S * 0.50)          # 到 y≈0.57
    if args.image and os.path.exists(args.image):
        illo = Image.open(args.image).convert("RGBA")
        if args.layout == "l2":
            max_w = int(S * 0.62)
        else:
            max_w = int(S * 0.92)
        max_h = illo_zone_h
        k = min(max_w / illo.width, max_h / illo.height)
        illo = illo.resize((max(1, int(illo.width * k)), max(1, int(illo.height * k)),),
                           Image.LANCZOS)
        if args.layout == "l2":
            ox = int(S - pad * 0.4 - illo.width)
        else:
            ox = (S - illo.width) // 2
        oy = illo_zone_top + (illo_zone_h - illo.height) // 2
        paste_illustration(canvas, illo, ox, oy)

    font_path = pick_font_path()
    if font_path:
        print("[font] %s" % font_path)
    else:
        print("[font] 未找到中文字体，已降级为默认字体（字形会不准）")

    # ---- 文字区排版 ----
    if args.layout == "l2":
        # 楹联式：左侧竖排奖励项目
        fs = int(S * 0.082)
        y = int(S * 0.105)
        for ch in args.reward:
            draw_hand_line(canvas, ch, font_path, fs, pad + fs * 0.62, y,
                           fill=accent, jitter=1.2)
            y += int(fs * 1.24)
        # 右下金句（两行右对齐于插画下方）
        lines = [x for x in args.quote.split("|") if x][:2]
        ty = int(S * 0.715)
        for ln in lines:
            f, tr = fit_font(font_path, ln, int(S * 0.60), int(S * 0.050))
            fsize = int(getattr(f, "size", int(S * 0.050)))
            draw_hand_line(canvas, ln, font_path, fsize, int(S * 0.68), ty, fill=INK)
            ty += int(fsize * 1.45)
    else:
        # L1 / L3：奖励项目 + 金句 + 落款，垂直堆叠
        y = int(S * 0.605)
        if args.reward:
            f, tr = fit_font(font_path, args.reward, max_w, int(S * 0.085))
            fsize = int(getattr(f, "size", int(S * 0.085)))
            draw_hand_line(canvas, args.reward, font_path, fsize, S // 2, y,
                           fill=accent, jitter=1.0, tracking_ratio=0.09)
            y += int(fsize * 1.35)
        lines = [x for x in args.quote.split("|") if x][:2]
        if lines:
            qsize = int(S * 0.048)
            if len(lines) == 1:
                qsize = int(S * 0.056)
            for ln in lines:
                f, tr = fit_font(font_path, ln, max_w, qsize)
                fsize = int(getattr(f, "size", qsize))
                draw_hand_line(canvas, ln, font_path, fsize, S // 2, y, fill=INK)
                y += int(fsize * 1.45)

    # ---- 印章与落款（所有版式共用）----
    if args.seal:
        side = int(S * 0.075)
        draw_seal(canvas, args.seal[:4], int(S - pad - side // 2),
                  int(S - pad * 0.8 - side // 2), side)
    if args.sign:
        fs = int(S * 0.024)
        f = load_font(font_path, fs)
        d = ImageDraw.Draw(canvas)
        sign_x = int(S - pad - S * 0.075 - S * 0.10)
        d.text((sign_x, int(S * 0.855)), args.sign, font=f, fill=INK_SOFT + (255,))
    if args.name or args.date:
        label = " · ".join([x for x in [args.name, args.date] if x])
        fs = int(S * 0.026)
        f = load_font(font_path, fs)
        d = ImageDraw.Draw(canvas)
        d.text((pad, int(S * 0.905)), label, font=f, fill=INK_SOFT + (255,))

    canvas = paper_texture(canvas)
    out = canvas.convert("RGB")
    out.save(args.out, "PNG")
    print("[ok] %s  %dx%d" % (args.out, S, S))


if __name__ == "__main__":
    main()
