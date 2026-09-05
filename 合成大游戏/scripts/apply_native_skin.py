#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原版 daxigua 素材替换脚本（主题无关）

用法:
    python3 apply_native_skin.py --game <daxigua目录> --sprites <贴图目录>
    python3 apply_native_skin.py --game ./daxigua --sprites ./out --restore   # 回滚

说明:
  liyupi/daxigua 的素材是 UUID 文件名，Cocos 按 UUID 索引资源，
  因此只能"同名同后缀同尺寸覆盖"，不能改名或新增。
  本脚本自动完成：备份 -> 尺寸适配 -> 覆盖 -> 校验。

映射依据：逐张打开仓库素材视觉确认，非按尺寸推测。
注意仓库中存在同尺寸干扰项（216x216 是签到按钮、92x92 是首页按钮、
89x89 是鼠标光标），脚本已排除，不会误伤。
"""
import argparse
import os
import shutil
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("缺少 Pillow，请先执行: pip3 install pillow")

# ---------------------------------------------------------------
# 水果贴图 UUID 映射表（已逐张视觉核验）
# level: 游戏内层级序号，对应 extraSettings.js 的 firstFruit / startFruits
# ---------------------------------------------------------------
FRUIT_SLOTS = [
    # level, 相对路径, 尺寸(w,h), 原始水果
    (0,  "res/raw-assets/0c/0cbb3dbb-2a85-42a5-be21-9839611e5af7.png", (80, 80),   "葡萄"),
    (1,  "res/raw-assets/d0/d0c676e4-0956-4a03-90af-fee028cfabe4.png", (108, 108), "橘子"),
    (2,  "res/raw-assets/74/74237057-2880-4e1f-8a78-6d8ef00a1f5f.png", (119, 119), "柠檬"),
    (3,  "res/raw-assets/13/132ded82-3e39-4e2e-bc34-fc934870f84c.png", (153, 152), "猕猴桃"),
    (4,  "res/raw-assets/03/03c33f55-5932-4ff7-896b-814ba3a8edb8.png", (183, 183), "西红柿"),
    (5,  "res/raw-assets/66/665a0ec9-6c43-4858-974c-025514f2a0e7.png", (193, 193), "桃"),
    (6,  "res/raw-assets/84/84bc9d40-83d0-480c-b46a-3ef59e603e14.png", (258, 258), "菠萝"),
    (7,  "res/raw-assets/5f/5fa0264d-acbf-4a7b-8923-c106ec3b9215.png", (308, 308), "椰子"),
    (8,  "res/raw-assets/56/564ba620-6a55-4cbe-a5a6-6fa3edd80151.png", (308, 309), "半个西瓜"),
    (9,  "res/raw-assets/50/5035266c-8df3-4236-8d82-a375e97a0d9c.png", (408, 408), "大西瓜"),
]

BACKUP_DIR = ".skin_backup"


def log(msg):
    print(msg, flush=True)


def find_cat_images(sprites_dir):
    """收集贴图并按面积升序，保证合成链视觉上由小到大"""
    files = []
    for fn in os.listdir(sprites_dir):
        if not fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        p = os.path.join(sprites_dir, fn)
        try:
            with Image.open(p) as im:
                files.append((im.size[0] * im.size[1], p))
        except Exception:
            continue
    files.sort(key=lambda x: x[0])
    return [p for _, p in files]


def fit(img, tw, th):
    """等比缩放并居中贴到透明画布，避免主体变形。
    尺寸必须严格等于目标值，否则物理碰撞半径会错位。"""
    img = img.convert("RGBA")
    bbox = img.split()[3].getbbox()
    if bbox:
        img = img.crop(bbox)
    ratio = min(tw / img.width, th / img.height)
    nw = max(1, round(img.width * ratio))
    nh = max(1, round(img.height * ratio))
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(img, ((tw - nw) // 2, (th - nh) // 2), img)
    return canvas


def do_backup(game_dir):
    bdir = os.path.join(game_dir, BACKUP_DIR)
    os.makedirs(bdir, exist_ok=True)
    n = 0
    for _, rel, _, _ in FRUIT_SLOTS:
        src = os.path.join(game_dir, rel)
        dst = os.path.join(bdir, rel.replace("/", "__"))
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            n += 1
    return n


def do_restore(game_dir):
    bdir = os.path.join(game_dir, BACKUP_DIR)
    if not os.path.isdir(bdir):
        sys.exit("找不到备份目录，无法回滚")
    n = 0
    for _, rel, _, _ in FRUIT_SLOTS:
        src = os.path.join(bdir, rel.replace("/", "__"))
        dst = os.path.join(game_dir, rel)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            n += 1
    log("已回滚 %d 个素材到原始水果" % n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True, help="daxigua 仓库目录")
    ap.add_argument("--sprites", help="贴图所在目录")
    ap.add_argument("--restore", action="store_true", help="回滚为原始水果")
    args = ap.parse_args()

    game = os.path.abspath(args.game)
    if not os.path.exists(os.path.join(game, "index.html")):
        sys.exit("目录不像 daxigua 仓库（未找到 index.html）: %s" % game)

    if args.restore:
        do_restore(game)
        return

    if not args.sprites:
        sys.exit("请用 --sprites 指定贴图目录")
    cats = os.path.abspath(args.sprites)

    # 先校验槽位齐全，避免replace到一半失败
    missing = [rel for _, rel, _, _ in FRUIT_SLOTS
               if not os.path.exists(os.path.join(game, rel))]
    if missing:
        log("以下素材槽位不存在，可能仓库版本不同：")
        for m in missing:
            log("   " + m)
        sys.exit("已中止，未做任何修改")

    imgs = find_cat_images(cats)
    if not imgs:
        sys.exit("贴图目录里没有可用图片: %s" % cats)
    log("找到 %d 张贴图，需要 %d 个槽位" % (len(imgs), len(FRUIT_SLOTS)))

    nb = do_backup(game)
    log("已备份 %d 个原始素材到 %s/\n" % (nb, BACKUP_DIR))

    ok = 0
    for i, (lv, rel, (w, h), origin) in enumerate(FRUIT_SLOTS):
        src = imgs[i % len(imgs)]
        dst = os.path.join(game, rel)
        try:
            with Image.open(src) as im:
                fit(im, w, h).save(dst, "PNG", optimize=True)
            # 立即回读校验，不假设写入成功
            with Image.open(dst) as chk:
                assert chk.size == (w, h), "尺寸不符 %s" % (chk.size,)
                assert chk.mode == "RGBA", "缺少透明通道"
            log("  [OK] lv%-2d %-9s %s <- %s"
                % (lv, "%dx%d" % (w, h), origin, os.path.basename(src)))
            ok += 1
        except Exception as e:
            log("  [FAIL] lv%d %s: %s" % (lv, rel, e))

    log("\n完成 %d/%d" % (ok, len(FRUIT_SLOTS)))
    if ok == len(FRUIT_SLOTS):
        log("启动: cd %s && npx serve" % game)
        log("回滚: python3 apply_native_skin.py --game %s --restore" % args.game)
    else:
        log("存在失败项，建议先回滚后排查")


if __name__ == "__main__":
    main()
