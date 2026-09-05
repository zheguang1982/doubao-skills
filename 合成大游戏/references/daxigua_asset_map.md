# liyupi/daxigua 素材映射与已知陷阱

本文件是替换原版 Cocos 游戏素材时的权威依据。所有映射经**逐张打开图片视觉核验**得出，不是按尺寸推测。

## 目录
- [仓库获取](#仓库获取)
- [10 个水果槽位映射表](#10-个水果槽位映射表)
- [必须排除的同尺寸干扰项](#必须排除的同尺寸干扰项)
- [非水果素材尺寸](#非水果素材尺寸)
- [代码级事实](#代码级事实)
- [已验证的坑](#已验证的坑)

## 仓库获取

```bash
git clone https://github.com/liyupi/daxigua.git
```

Cocos Creator 构建产物，纯静态，起个 HTTP 服务即可运行（`npx serve` / `python3 -m http.server`）。1400+ star，可商用。

## 10 个水果槽位映射表

**关键事实：仓库实际只有 10 个水果贴图，没有独立的樱桃图。** 网上流传的"11 级"说法不适用于这个仓库。

素材是 UUID 文件名，Cocos 按 UUID 索引资源，因此**只能同名同后缀覆盖，不能改名或新增**。

| level | 相对路径 | 尺寸 | 原始水果 |
|---|---|---|---|
| 0 | `res/raw-assets/0c/0cbb3dbb-2a85-42a5-be21-9839611e5af7.png` | 80×80 | 葡萄 |
| 1 | `res/raw-assets/d0/d0c676e4-0956-4a03-90af-fee028cfabe4.png` | 108×108 | 橘子 |
| 2 | `res/raw-assets/74/74237057-2880-4e1f-8a78-6d8ef00a1f5f.png` | 119×119 | 柠檬 |
| 3 | `res/raw-assets/13/132ded82-3e39-4e2e-bc34-fc934870f84c.png` | 153×152 | 猕猴桃 |
| 4 | `res/raw-assets/03/03c33f55-5932-4ff7-896b-814ba3a8edb8.png` | 183×183 | 西红柿 |
| 5 | `res/raw-assets/66/665a0ec9-6c43-4858-974c-025514f2a0e7.png` | 193×193 | 桃 |
| 6 | `res/raw-assets/84/84bc9d40-83d0-480c-b46a-3ef59e603e14.png` | 258×258 | 菠萝 |
| 7 | `res/raw-assets/5f/5fa0264d-acbf-4a7b-8923-c106ec3b9215.png` | 308×308 | 椰子 |
| 8 | `res/raw-assets/56/564ba620-6a55-4cbe-a5a6-6fa3edd80151.png` | 308×309 | 半个西瓜 |
| 9 | `res/raw-assets/50/5035266c-8df3-4236-8d82-a375e97a0d9c.png` | 408×408 | 大西瓜 |

**308×308 是椰子，308×309 是半个西瓜——只差 1px。** 认错会让合成顺序错乱。

## 必须排除的同尺寸干扰项

只按尺寸匹配一定会误伤这些：

| 路径 | 尺寸 | 实际是 | 易误认为 |
|---|---|---|---|
| `res/raw-assets/47/4756311b-4364-4160-bc7e-299876f49770.png` | 216×216 | 签到领福利按钮 | 菠萝 |
| `res/raw-assets/8c/8c52a851-9969-4702-9997-0a2ca9f43773.png` | 216×216 | 签到领福利按钮 | 菠萝 |
| `res/raw-assets/55/55076d53-f1fd-40fd-97fc-3a14ca11a10a.png` | 92×92 | 首页房子按钮 | 樱桃 |
| `res/raw-assets/b0/b0dd9862-1b33-4857-87f3-0d45f325f63b.png` | 89×89 | 灰圆 | 小水果 |
| `res/raw-assets/b3/b31f518e-342c-453f-8246-0e061947e3e6.png` | 89×89 | 鼠标手势光标 | 小水果 |
| `res/raw-assets/c1/c15f3ea5-f9a0-4e70-b5b3-565ede11df1c.png` | 89×89 | 鼠标手势光标 | 小水果 |
| `res/raw-assets/a7/a7de1099-ffab-450b-8db5-54b51514fd54.png` | 163×163 | 播放键 | 水果 |
| `res/raw-assets/9e/9ed91ad5-dc75-48f7-b1dd-30dc29048969.png` | 224×224 | 白圈 | 水果 |
| `res/raw-assets/53/53e8e9ea-a7ad-4d7d-ba2f-2068f3e65ef6.png` | 256×256 | 星光特效 | 水果 |

`scripts/apply_native_skin.py` 已内置排除逻辑，不会误伤。

## 非水果素材尺寸

需要做完整主题皮肤时参考：

| 用途 | 尺寸 | 备注 |
|---|---|---|
| 游戏背景 | 720×1280 RGB | |
| 顶部横幅 | 720×139 | |
| 顶部叠加层 | 720×127 RGBA | |
| 广告横幅（大） | 1090×100 | |
| 广告横幅（小） | 760×100 | |
| 警戒线 | 711×8 | 高度仅 8px，极易被拉变形 |
| 按钮（宽） | 690×60 | |
| 按钮（次） | 660×60 | |
| 结算面板 | 523×500 | |
| 分享图 | 418×208 | **`res/share.jpg` 是 JPG，换成 PNG 会加载失败** |
| 合成星光 | 38×40 ×10 张 | 序列帧，必须整套替换否则闪烁 |
| 果汁飞溅 | 24×41 ×10 张 | 序列帧，同上 |

## 代码级事实

- 水果名数组在 `src/project.js`：
  `this.fruitS = ["PuTaoS","YingTaoS","JuZiS","NingMengS","MiHouTaoS","XiHongShiS","TaoS","BoLuoS","YeZiS","XiGuaS"]`
  注释写明"水果下标 0-9（0 为葡萄，9 为半个西瓜）"。
- `src/project.js` 是 binary-ish 大文件（22 万字符），`grep` 常失效，用 Python 读取。
- 魔改配置全在 `src/extraSettings.js`：`extraScore` / `wuDi` / `firstFruit(0-10)` / `reverseLevelUp` / `setFruits.startFruits` / `fruitQTan` / `fruitSlowDown` / `clickChangeFruit` / `adLink` / 网页标题 / `selectModal`。
- `src/settings.js` 的 rawAssets 段里**没有**水果图片条目，别去那里找映射。

## 已验证的坑

1. **广告源导致首屏卡死**
   `index.html` 第 76–77 行硬编码两个 `rmcdn.2mdn.net` 广告视频源，实测返回 **502**。删掉这两行 `<source>` 后加载明显顺畅。每次起服务前先处理。

2. **prefab 里搜不到 UUID 明文**
   `res/import/` 下的 prefab JSON 用的是压缩 UUID，搜索水果贴图 UUID 无命中，**无法从代码拿到权威映射**。这就是本文件的映射只能靠逐张视觉识别的原因。

3. **无 GPU 环境跑不起来**
   Cocos WebGL 初始化在无 GPU 沙箱里极慢，页面会长时间停在 95–99% 进不去主画面。**未改动的原始仓库也是同样表现**，不是替换导致的。此时改用静态校验（尺寸、透明通道、HTTP 200）确认素材正确性，不要反复等渲染。
