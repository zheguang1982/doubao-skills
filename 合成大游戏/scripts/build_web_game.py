#!/usr/bin/env python3
"""用处理好的贴图生成自包含单文件网页游戏。

图片以 base64 内嵌，不依赖任何外部图床——这是刻意为之：
图床通常不返回 CORS 头，canvas 引用外链贴图会加载失败。

用法:
    python3 build_web_game.py --sprites out/ --title "合成大猫猫" --out game.html
"""
import argparse
import base64
import io
import json
import os
import re
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow: pip3 install Pillow")

TPL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'assets', 'game_template.html')

# 与 GAME_SIZES 对应的物理半径，决定手感与合成节奏
RADII = [20, 24, 29, 34, 41, 49, 57, 67, 78, 91, 106]


def encode(path, maxd=200, colors=128):
    """压成 base64。调色板量化把体积压到约 1/7，扁平风格肉眼无损。"""
    im = Image.open(path).convert('RGBA')
    if im.width > maxd:
        im = im.resize((maxd, round(im.height * maxd / im.width)), Image.LANCZOS)
    q = im.quantize(colors=colors, method=Image.FASTOCTREE)
    buf = io.BytesIO()
    q.save(buf, 'PNG', optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), len(buf.getvalue())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sprites', required=True, help='prepare_sprites.py 的输出目录')
    ap.add_argument('--title', default='合成大西瓜', help='游戏标题')
    ap.add_argument('--out', required=True, help='输出 html 路径')
    ap.add_argument('--names', help='逗号分隔的各级名称，用于结算展示')
    ap.add_argument('--max-dim', type=int, default=200, help='内嵌图最大边长')
    ap.add_argument('--sayings', default='',
                    help='逗号分隔的高级合成台词，如 "加油,稳住"；留空则不弹台词气泡。文案内部不要用英文逗号')
    ap.add_argument('--say-from', type=int, default=3,
                    help='从第几级（0 基 index）开始弹台词，默认 3，即合成出显示 Lv.4 起')
    ap.add_argument('--over-title', default='又叠塌了', help='游戏结束面板标题')
    args = ap.parse_args()

    files = sorted(
        [f for f in os.listdir(args.sprites) if f.endswith('.png')],
        key=lambda f: int(re.search(r'lv(\d+)', f).group(1))
        if re.search(r'lv(\d+)', f) else 0
    )
    if not files:
        sys.exit(f"未找到贴图: {args.sprites}")

    names = [n.strip() for n in args.names.split(',')] if args.names else []

    cats, total = [], 0
    print(f"内嵌 {len(files)} 张贴图")
    for i, f in enumerate(files):
        uri, size = encode(os.path.join(args.sprites, f), args.max_dim)
        total += size
        cats.append({
            "r": RADII[i] if i < len(RADII) else RADII[-1] + (i - len(RADII) + 1) * 14,
            "url": uri,
            "name": names[i] if i < len(names) else f"第{i + 1}级"
        })
        print(f"  lv{i:<2} {f:<32} {size / 1024:6.1f} KB")

    with open(TPL, encoding='utf-8') as fh:
        html = fh.read()

    cats_js = json.dumps(cats, ensure_ascii=False, separators=(',', ':'))
    sayings = [s.strip() for s in args.sayings.split(',') if s.strip()]
    sayings_js = json.dumps(sayings, ensure_ascii=False, separators=(',', ':'))
    html = html.replace('var CATS = /*__CATS_JSON__*/[];', 'var CATS = ' + cats_js + ';')
    html = html.replace('var SAYINGS = /*__SAYINGS_JSON__*/[];',
                        'var SAYINGS = ' + sayings_js + ';')
    html = html.replace('/*__SAY_FROM__*/', str(args.say_from))
    html = html.replace('__TITLE__', args.title)
    html = html.replace('__OVER_TITLE__', args.over_title)

    # 落盘前自检：占位符必须全部替换掉，否则页面必然白屏
    for ph in ('__CATS_JSON__', '__SAYINGS_JSON__', '__SAY_FROM__', '__TITLE__', '__OVER_TITLE__'):
        if ph in html:
            sys.exit(f"模板占位符未替换: {ph}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fh:
        fh.write(html)

    # 回读校验
    back = open(args.out, encoding='utf-8').read()
    n_img = len(re.findall(r'data:image/png;base64', back))
    n_ext = len(re.findall(r'https?://[^"\']*\.(?:png|jpg|jpeg|webp)', back))
    print(f"\n输出 {args.out}  {os.path.getsize(args.out) / 1024:.0f} KB")
    print(f"  内嵌图片 {n_img} 张（应为 {len(files)}）")
    print(f"  外部图片引用 {n_ext} 处（应为 0）")
    if n_img != len(files) or n_ext:
        sys.exit("校验失败")
    print("  校验通过，双击即可运行")


if __name__ == '__main__':
    main()
