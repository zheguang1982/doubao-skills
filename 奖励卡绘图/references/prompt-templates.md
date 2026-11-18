# 提示词模板与版式参数

所有模板按 **1:1、1440×1440** 写。换尺寸时按比例缩放。

## 1. 版式几何（1:1）

```
┌──────────────────────────────┐  y=0
│        留白 ≥ 120px          │
│                              │
│        ┌────────────┐        │  插画区
│        │  单主体     │        │  y=120 ~ 800
│        │ 头顶留白15% │        │  主体宽 35–55%
│        └────────────┘        │
│                              │
├──────────────────────────────┤  y≈835  (58%)
│      ███ 奖励项目（朱红）      │  字号 96–110px
│                              │
│      金句第一行（墨黑）        │  字号 58–66px
│      金句第二行               │  行距 1.15
│                              │
│ 姓名·日期        印章          │  y≈1270 ~ 1350
└──────────────────────────────┘  y=1440
```

- 外边距：左右各 86px（6%）
- 插画底边不超过 y=800，**不得压到文字区**
- 奖励项目与金句之间留 24–32px
- 印章 90–110px 见方，右下距边 86px
- 姓名日期 34–38px，左下距边 86px，灰墨 #6E6E6E

### L1 经典式（默认）
上 58% 插画，下 42% 文字。主体居中略偏下。

### L2 楹联式
左侧 30% 宽竖排：奖励项目（竖排，朱红，最大）＋金句（竖排，墨黑，较小）；右下 55% 区域放小画，主体缩小到画面宽 30%。

### L3 徽章式
中央一圈枯笔圆环（直径约画面宽 55%）包住主体；环外下方一行短句；印章压在圆环右下边上。

## 2. A 模式主提示词（模型直接写字）

> 顺序：主体 → 动作 → 构图 → 媒介 → 色彩光影 → 材质细节 → 文字 → 背景 → 后期参数

### 2.1 可直接套用的中文模板

```
一张竖方形的中国水墨淡彩手绘奖励卡，宣纸白底（#FBF8F1），带极淡纸纤维颗粒。
画面中心偏下画{主体描述}，2.5头身Q版比例，光头三根毛，招风大耳配青绿色小圆耳环，
穿{袍子颜色}宽袍大袖。闭眼弯成一条弧线，嘴角上扬，不画鼻子，两颊各有一团胭脂腮红。
线条是焦墨枯笔，中锋，起笔重收笔枯，允许断笔飞白和毛边；上色只有3种低饱和水彩，
色块不填满轮廓，边缘留水痕。背景完全空白，只有{0–1个符号道具}。无投影、无渐变、无高光。
画面下部是手写毛笔行楷文字：最上方朱红色大字“{奖励项目}”，
下面墨黑色两行“{金句第一行}”“{金句第二行}”，字号依次变小，字略歪，字距松。
右下角一枚朱红色方形印章，刻“{印章文字}”，边缘斑驳。左下角小字“{姓名} · {日期}”。
整体留白超过60%，像随手画在纸上的一张小卡。画面中没有任何二维码、logo、水印、署名。
```

### 2.2 英文压缩版（模型吃英文时用）

```
Chinese ink-and-wash watercolor reward card, warm rice-paper white background (#FBF8F1) with faint fiber grain.
Single {subject} at 2.5-head chibi proportion, bald head with three strands, oversized ears with small teal hoop earrings,
loose {color} robe, eyes as one closed curve, no nose, two rouge blush patches on both cheeks.
Dry brush sumi ink outlines, heavy start and frayed tail, broken strokes and feibai, no clean vector line.
Only 3 muted watercolor washes, not filling the outlines, soft bloom edges.
58% of the canvas empty and blank, no scenery, at most one small prop.
Lower part: handwritten brush calligraphy — vermilion“{reward}”on top, then two ink-black lines“{line1}”and“{line2}”,
slight jitter, wide letter spacing. Vermilion square seal at bottom right reading“{seal}”.
Tiny gray“(name) · (date)”at bottom left. No QR code, no logo, no watermark, no signature.
Flat even scan-like lighting, no shadow, no gradient, no gloss, 1:1.
```

## 3. B 模式主提示词（无字，留白交给脚本）

关键改动：把整块文字区描述为「完全空白」，并禁止任何字符。

```
...（前半段与 A 模式相同）...
画面下部 42% 必须是完全空白的宣纸，不要写任何字、不要画印章、不要画线条装饰。
不要二维码、不要 logo、不要水印、不要日期、不要名字、不要任何字符。
```

负面词追加：`any text, letters, chinese characters, calligraphy, seal, stamp, signature, qr code`

生成后用 `scripts/render_card_text.py` 叠字。

## 4. 负面提示词（统一使用）

**短版（默认）**

```
photo, realistic, 3d render, cgi, gradient background, glossy, highlight, drop shadow,
neon, oversaturated, thick vector outline, cel shading, smooth digital line, cluttered background,
full scenery, texture overlay, sticker border, frame ornament, qr code, watermark, signature,
logo, emoji, deformed face, extra limbs, six fingers, realistic anatomy, blurry text, garbled characters
```

**加长版（画面反复失控时）** 在短版后追加：

```
multiple subjects, crowd, busy composition, high detail, sharp focus everywhere, soft airbrush shading,
anime eyes with sparkles, manga screentone, western cartoon style, children's book 3d, plastic skin,
flat vector flat design, ui elements, ribbons, stars, confetti, ornate gold frame
```

## 5. 参数建议

| 项 | 值 |
|---|---|
| 模型 | `seedream_5.0_pro`（不可用时降级 `seedream_5.5`） |
| 尺寸 | 1440×1440（1:1），打印用可到 2048×2048 |
| 张数 | 每次 1 张，逐张验字 |
| 风格强度 | 高；风格词占 prompt 一半以上 |
| 主体数量 | 1 个（最多加 1 只小动物） |
| 参考图锚定 | 2–3 张，权重中；只用其线条与设色 |

## 6. 风格锚定（可选，风格漂移时用）

1. 从 `assets/anchors.json` 取 2–3 张锚点的 `cdn_url`（本地有文件时也可先 `FileBatchUpload` 拿 URL）。
2. 用 `image_edit`，`image_reference_url_list` 放 2–3 张锚点，prompt 写：
   `保持参考图的焦墨枯笔线条、宣纸白底大留白、低饱和淡彩与胭脂腮红；换成{新主体}；不要复制参考图里的二维码、署名、日期字与原有文案；1:1。`
3. 锚定只做「风格脚手架」，出图后仍需验字验图。产物对照 `assets/anchors.json` 里的 `target_look` 样张判断是否达标。

## 7. 文字出错时的修复片段

| 问题 | 追加到 prompt |
|---|---|
| 字糊成一团 | `每个汉字笔画清晰分开，字与字之间有明显空隙，不要连笔，不要艺术字变形` |
| 字错／缺字 | 转 B 模式（首选）；或把字数压到 6 字内，字号写大 |
| 字太多挤在一起 | `只写{N}个字，其余位置保持空白` |
| 出现二维码 | `右下角只放一枚朱红印章，不要二维码，不要署名` |
| 字体像电脑字 | `毛笔手写，笔锋有粗细变化，字略歪不齐，不是印刷体` |

## 8. 验收表（逐条打勾，缺一不可）

| # | 检查项 | 判定 |
|---|---|---|
| 1 | 每一个汉字都正确、可读、无多余笔画 | 逐字读 |
| 2 | 奖励项目是朱红、全卡最大字号 | 目视 |
| 3 | 金句 ≤2 行，墨黑，手写感 | 目视 |
| 4 | 有一枚朱红印章，位于右下 | 目视 |
| 5 | 两颊有胭脂腮红 | 目视 |
| 6 | 不画鼻子，五官极简 | 目视 |
| 7 | 线条有枯笔飞白，不是均匀描边 | 放大看 |
| 8 | 留白 ≥55%，无背景场景 | 目视 |
| 9 | 无投影、无渐变、无高光、无 3D 感 | 目视 |
| 10 | 无二维码、logo、水印、署名、emoji | 目视 |
| 11 | 主体五官/手指正常，无多手多指 | 放大看 |
| 12 | 1:1 方图，文字不压插画 | 目视 |

任一条不过：先按第 7 节修 prompt；文字类问题直接转 B 模式。

## 9. 批量出卡（同系列统一风格）

1. 先定「母版 prompt」：固定主体类型、袍色、版式、印章。
2. 只替换 `{奖励项目}`、`{金句}`、`{姓名}`、`{日期}`。
3. 统一走 B 模式：无字插画批量出，脚本批量叠字（脚本可循环调用）。
4. 全部出完后统一验一遍字号与落款位置。
