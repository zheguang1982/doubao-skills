---
name: 杂志风教学PPT
description: 将教学设计或已有课件改造为"儿童文学杂志风"全图形教学PPT。适用于：用户提供教学设计文档、已有PPT/PPTX课件、课文课题，要求生成或改造成杂志排版风格、图文融合、带教师备注话术的课堂演示课件。触发关键词：杂志风、儿童文学杂志、全图形课件、杂志排版、栏目式课件、图文融合PPT。
---

# 杂志风教学PPT

将教学设计或已有课件转化为清新活泼的杂志排版风格课件，适合小学/初中课堂。核心特征：栏目式结构、色块标签、对话气泡、页码、全图文融合页、每页附教师话术备注。

## 工作流程（六步闭环）

### 第一步：探查与解析

1. **定位原文件**：在桌面或用户指定路径找到 .pptx 文件。
2. **解析PPTX**：PPTX本质是ZIP包，用Python `zipfile` + `xml.etree.ElementTree` 解析，无需安装python-pptx。运行 `scripts/parse_pptx.py <pptx路径> <输出目录>`，提取：
   - 每页所有文本（含shape和pic中的文字）
   - 演讲者备注（notesSlides）
   - 所有媒体文件（ppt/media/）
   - 每页图片与文本的对应关系（通过rels文件关联）
3. **查看关键素材**：用Read工具查看原课件中的吉祥物、田字格、装饰元素、场景插图，确定哪些需要保留原样、哪些需要重绘。

### 第二步：结构重组与视觉系统

**栏目式结构（灵活适配教学需求）**：

课件架构必须根据实际教学场景动态调整，不固定页数和栏目组合：

- **课时适配**：第一课时通常含字词学习；第二课时可直接跳过字词乐园，从课文探秘或复习导入开始。
- **探究活动递进**：课堂探究环节可设2-3个有逻辑递进的活动（如：整体感知→局部品析→写法迁移），每个活动独立成页或合并呈现。
- **栏目取舍**：根据课文特点和教学目标，可增删栏目。如自读课文可省略字词乐园，习作指导课可强化互动角/小练笔。

**教学目标呈现规则（核心素养导向）**：

若课件中包含教学目标页，**禁止使用"知识与技能、过程与方法、情感态度与价值观"三维目标框架**，必须从学科核心素养角度拆解呈现。以语文为例，对应四个维度：

| 核心素养维度 | 内涵说明 | 目标表述示例 |
|-------------|---------|------------|
| 文化自信 | 认同中华文化、传承文化基因、开阔文化视野 | 感受桂花雨承载的思乡情怀，增强对中华民俗文化的认同 |
| 语言运用 | 字词积累、阅读理解、表达交流、语感培养 | 积累"姿态、迷人、糕饼"等词语，能有感情地朗读课文 |
| 思维能力 | 直觉思维、形象思维、逻辑思维、创造性思维 | 梳理"摇花乐"的场景脉络，体会作者由事及情的写作思路 |
| 审美创造 | 感受美、欣赏美、评价美、创造美 | 品味文中清新质朴的语言，体会散文的意境美和人情美 |

其他学科参照对应课程标准的核心素养框架（如数学：数学抽象、逻辑推理、数学建模、直观想象、数学运算、数据分析；英语：语言能力、文化意识、思维品质、学习能力）。目标表述须具体可测，避免空泛套话。版式上采用四宫格卡片或纵向列表，每个维度配对应色标标签。

**典型五段栏目**（按需选用，非强制）：

| 栏目 | 典型页面 | 版式建议 |
|------|---------|---------|
| 趣味导入 | 单元导语、作者名片、情境创设 | 对话气泡、档案卡片 |
| 字词乐园 | 词语认读、生字田字格、书写指导 | 贴纸卡片、田字格网格 |
| 课文探秘 | 内容思维导图、段落赏析、关键词品析、情景想象、探究活动1/2/3 | 思维导图、对比双栏、动作链、时间线、信息图 |
| 思维拓展 | 重点句讨论、写作手法图解、资料链接 | 左右对比、流程图、讨论区 |
| 互动角/小练笔 | 拓展阅读、课堂练习、小练笔 | 美食铺、选择题贴纸、填空卡 |

加上**封面**（年级册别·单元+主标题+主视觉图）和**封底**（总结+下期预告），**不设目录页**，总页数根据教学需要灵活确定（通常14-19页）。

**视觉系统**（儿童文学杂志风）：
- 背景：米黄 `rgb(255, 248, 240)`
- 主色：桂花黄 `rgb(245, 215, 110)`
- 辅色：暖粉橘 `rgb(240, 168, 138)`、薄荷绿 `rgb(168, 216, 185)`、淡紫 `rgb(201, 182, 228)`
- 文字：深棕 `rgb(107, 68, 35)`
- 杂志元素：栏目标签（圆角矩形+文字）、页码（右下角）、对话气泡、动作链圆点、时间线、装饰枝叶
- 画布：960×540

### 第三步：素材准备

1. **生成水彩插图**：用 `image_gen` 生成儿童水彩/彩铅风格插图，典型需求：
   - 封面主视觉（课文情境+人物）
   - 关键场景图（如摇桂花、赏桂花）
   - 特写图（如花枝、美食）
   - 装饰边框
   - Prompt要点：`儿童水彩插画风格` + 场景描述 + `柔和明亮配色` + `水彩晕染质感` + `无文字`
2. **保留原素材**：田字格、特定卡通角色、吉祥物等必须与原素材"长相一致"，直接从原PPTX的media目录提取使用。
3. **下载与上传**：
   - 生成的图片用 `urllib.request.urlretrieve` 下载到工作目录
   - 用 `lark-cli slides +media-upload --file ./xxx.png --presentation <id>` 上传获取 `file_token`
   - 所有token记录到 `image_tokens.json`，避免拼写错误（token末尾大小写敏感）

### 第四步：逐页制作

**前置准备**：
1. 读取 `ppt` skill 的 `SKILL.md` 和 `references/xml/xml-schema-quick-ref.md`
2. Windows环境必须读取 `references/workflow/windows-compat.md`
3. 创建空白幻灯片：`lark-cli slides +create --title "标题"`，记录 `xml_presentation_id` 和 `url`
4. 开工通知：用 `present_files` 交付在线链接

**逐页闭环**（一页一页来，不要批量）：
1. 写单页XML到 `slides/slide-NN.xml`，只包含单个 `<slide>` 元素，不要 `<?xml?>` 声明和 `<presentation>` 包裹
2. 静态校验：`python <ppt_skill路径>/scripts/xml_lint.py --input slides/slide-NN.xml`，`error_count` 必须为0
3. 写入：`lark-cli slides +add-slide --presentation <id> --slide "@slides/slide-NN.xml"`
4. 记录返回的 `slide_id`

**XML关键规则**：
- 文本颜色用 `<content color="...">`，不是 `fontColor`
- 字号必须显式设置 `fontSize`，不要依赖默认值
- 行间距用 `lineSpacing="multiple:1.5"` 格式
- 图片 `src` 填 `file_token`，禁止http外链
- 图片 `width:height` 对齐原图比例可避免裁剪
- 全篇禁止emoji，语义图标用IconPark
- `&` `<` `>` 必须转义为 `&amp;` `&lt;` `&gt;`

**常见lint错误与修复**：
- `text shape overflows its background container`：文本框与背景矩形同宽同位置时触发。将文本框宽度缩小4-8px并居中，或移除背景矩形改用线条分隔。
- `line crosses shape`：时间线/连接线穿过节点圆圈。将线移到节点下方，或移除线条。
- `shape covers text`：底部大矩形覆盖了上方的对话气泡。调整y坐标留出间隙。
- 添加时 `3350002 not found`：图片file_token拼写错误（末尾大小写），核对 `image_tokens.json`。

**教师备注**：每页 `<slide>` 末尾加 `<note><content textType="body" fontSize="14"><p>3-5句可直接照读的课堂话术</p></content></note>`。

### 第五步：全文校验与视觉验证

1. **回读全文**：`lark-cli slides +xml-get --presentation <id> --output ./full_readback.xml`
2. **全文lint**：对回读文件跑 `xml_lint.py`，`error_count` 必须为0（逐页干净不等于全文干净）
3. **截图验证**：`lark-cli slides +screenshot --presentation <id> --slide-id <sid> --output-dir ./screenshots`，用Read查看关键页（封面、思维导图页、场景页）确认排版无溢出、图片正常显示
4. **问题修复**：局部问题用 `+replace-slide`，整页重做用 `+update-slide`

### 第六步：导出与交付

1. **导出PPTX**（Windows/Mac本地模式必须）：`lark-cli drive +export --token <xml_presentation_id> --doc-type slides --file-extension pptx --output-dir ./export`
2. **交付**：用 `present_files` 同时交付：
   - 本地PPTX文件路径（用户可直接下载打开）
   - 飞书在线幻灯片链接（可继续协同编辑）
3. **交付说明**：列出页数、栏目结构、视觉特点、备注话术情况。

## Windows平台注意事项

- Bash工具实际是PowerShell，禁止 `&&`、`heredoc`、`$(...)`、jq等Unix工具
- `lark-cli` 路径只接受CWD内相对路径，先 `cd` 到工作目录
- `--params`/`--data` 禁止命令行内联JSON，先Write到 .json 文件再用 `@file.json`
- `python -c` 中禁止双引号转义，复杂逻辑写成 .py 文件执行
- lark-cli的stderr输出会被PS包成NativeCommandError，不代表真报错，看内容判断

## 脚本说明

- `scripts/parse_pptx.py`：解析PPTX提取文本、备注、媒体文件、图文关系。用法：`python parse_pptx.py <pptx路径> <输出目录>`
- `scripts/upload_images.py`：批量上传图片并记录file_token。修改脚本内 `PRES_ID` 和 `images` 字典后运行。

## 参考文档

- `references/design_system.md`：完整视觉规范、配色色值、杂志元素尺寸参考、典型页面版式模板
- `references/xml_tips.md`：飞书Slides XML高频写法速查、常见错误修复清单
