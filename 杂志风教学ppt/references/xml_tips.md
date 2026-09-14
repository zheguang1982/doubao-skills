# 飞书Slides XML - 高频写法与错误修复

## 基础结构

单页XML文件只包含 `<slide>` 元素，不需要 `<?xml?>` 声明和 `<presentation>` 包裹：

```xml
<slide xmlns="https://www.larkoffice.com/sml/2.0">
  <style>
    <fill><fillColor color="rgb(255, 248, 240)"/></fill>
  </style>
  <data>
    <!-- 页面元素 -->
  </data>
  <note>
    <content textType="body" fontSize="14"><p>教师备注话术</p></content>
  </note>
</slide>
```

## 高频元素写法

### 文本框
```xml
<shape type="text" topLeftX="40" topLeftY="60" width="400" height="42">
  <content textType="title" fontSize="28" bold="true" color="rgb(107, 68, 35)"
           textAlign="left" verticalAlign="middle" lineSpacing="multiple:1.5"
           letterSpacing="2" wrap="false">
    <p>标题文字</p>
  </content>
</shape>
```

要点：
- 颜色用 `color` 属性，不是 `fontColor`
- 字号必须显式设置 `fontSize`
- 行间距 `lineSpacing="multiple:1.5"`，不能写 `lineSpacing="1.5"`
- 短标签/单行文字用 `wrap="false"` 并留够宽度
- 内联局部样式用 `<span>`，如 `<span bold="true" color="rgb(200,100,60)">重点</span>`

### 圆角矩形（卡片/标签）
```xml
<shape type="round-rect" topLeftX="40" topLeftY="115" width="420" height="200" presetHandlers="14">
  <fill><fillColor color="rgba(245, 215, 110, 0.2)"/></fill>
  <border color="rgb(245, 215, 110)" width="2"/>
</shape>
```

要点：
- `presetHandlers` 是圆角半径(px)，不是比例
- `round-rect` 默认圆角16，`rect` 默认圆角0
- 半透明填充用 `rgba(R,G,B,0.2)` 营造贴纸感

### 圆形（节点/标签）
```xml
<shape type="ellipse" topLeftX="60" topLeftY="120" width="44" height="44">
  <fill><fillColor color="rgb(245, 215, 110)"/></fill>
</shape>
```

### 图片
```xml
<img src="file_token_here" topLeftX="520" topLeftY="100" width="400" height="300">
  <crop type="rect" presetHandlers="16"/>
  <border color="rgb(255,255,255)" width="4"/>
</img>
```

要点：
- `src` 填 `+media-upload` 返回的 `file_token`，禁止http外链
- `width:height` 对齐原图比例可避免裁剪
- 圆角图片用 `<crop type="rect" presetHandlers="16"/>`
- 圆形头像用 `<crop type="ellipse"/>` 且 `width==height`

### 线条
```xml
<line startX="80" startY="180" endX="880" endY="180">
  <border color="rgb(245, 215, 110)" width="3" dashArray="dash"/>
</line>
```

要点：
- 用 `startX/startY/endX/endY`，不是 `x1/y1/x2/y2`
- 虚线用 `dashArray="dash"`，默认 `solid`

## 常见lint错误修复

### 1. text shape overflows its background container
**原因**：文本框与背景矩形的x/width完全相同，lint认为文字溢出容器。
**修复**：
- 文本框宽度比背景小4-8px，x坐标偏移2-4px居中
- 或移除背景矩形，改用线条分隔
- 表格场景：表头不要用独立rect做背景，直接用加粗彩色文字+底部分隔线

### 2. line crosses shape
**原因**：时间线/连接线穿过了节点圆圈或其他形状。
**修复**：
- 将线条移到节点下方（节点y范围之外）
- 或将线条拆分为节点之间的短段，避开节点区域
- 时间线典型布局：节点在y=164（高32，到196），线在y=200

### 3. shape covers text
**原因**：后写的大矩形覆盖了先写的文本框（XML中后写的在上层）。
**修复**：
- 调整元素顺序：被覆盖的文本写在覆盖形状之后
- 或调整y坐标，使两个元素不重叠
- 底部大卡片与上方对话气泡之间至少留5px间隙

### 4. 添加时 3350002 not found
**原因**：图片file_token拼写错误（末尾大小写敏感，如`...knSe`误写为`...kns`）。
**修复**：核对 `image_tokens.json` 中的准确token，逐字符比对。

### 5. 添加时 invalid param / 3350001
**原因**：XML格式错误，常见为特殊字符未转义、标签未闭合、属性值格式错误。
**修复**：
- 检查 `&` `<` `>` 是否转义为 `&amp;` `&lt;` `&gt;`
- 用xml_lint先校验本地文件
- 检查color格式是否正确（`rgb(R,G,B)` 或 `rgba(R,G,B,A)`）

## 命令速查

```bash
# 创建空白幻灯片
lark-cli slides +create --title "标题"

# 上传图片
lark-cli slides +media-upload --file ./pic.png --presentation <id>

# 添加页面
lark-cli slides +add-slide --presentation <id> --slide "@slides/slide-01.xml"

# 回读全文
lark-cli slides +xml-get --presentation <id> --output ./full.xml

# 截图
lark-cli slides +screenshot --presentation <id> --slide-id <sid> --output-dir ./shots

# 导出PPTX
lark-cli drive +export --token <id> --doc-type slides --file-extension pptx --output-dir ./export

# 静态校验
python <ppt_skill>/scripts/xml_lint.py --input slide.xml
```
