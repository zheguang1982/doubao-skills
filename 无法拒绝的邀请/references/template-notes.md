# 模板实现笔记 (template-notes)

`assets/template.html` 是定稿产物源模板：单文件、零外部依赖（花朵用内联 SVG data-URI，字体用系统字体栈）。**修改模板前先读本文**，尤其涉及逃逸按钮和锚点时。

## 锚点约定

所有可替换内容都是 `__UPPER_CASE__` 形式的锚点，由 `build_invite.py` 逐一替换并校验。锚点全集见脚本内 `ANCHORS` 常量，含：

- 文本类：`__BRAND__` `__SLOGAN__` `__INVITE_LINE__` `__GUEST__` `__EVENT_NAME__` `__SIGNATURE__` `__ROLE_LABEL__` `__INVITE_TITLE__`
- 组合类（脚本按 `session` 是否留空拼好）：`__KICKER_LINE__`（屏1标签，`主办 · 场次`，session 空则只有主办）、`__SCREEN4_TITLE__`（屏4标题，session 空则为"想参加什么？"）、`__SESSION_ROW__`（票根场次行，session 空则为空串，整行不渲染）
- 日期类（脚本拼好）：`__EVENT_DATE_LINE__` `__EVENT_MONTH_HEAD__` `__EVENT_DAY__` `__EVENT_WEEK_FULL__`
- 内容类：`__TOPICS__`

`__INVITE_TITLE__` 是屏1顶部大标题 + 页面 `<title>` 的共用锚点，默认「讲座邀请函」，由 `invite_title` 配置覆盖。

**改模板守则：**
- 新增可替换内容 → 添加新锚点，并同步加入脚本 `ANCHORS` 与 `replacements`
- 删除锚点 → 同步从脚本 `ANCHORS` 移除，否则脚本会因模板缺锚点而报错（这是有意的护栏）
- 锚点不要复用（如 `__GUEST__` 只出现一处语义），避免替换错位

## 逃逸按钮（核心记忆点）

`#no-btn`「拒绝」按钮的行为有非显而易见的处理：

1. **定位切换**：初始为 `position:relative`（静态流内），第一次逃逸时改为 `position:absolute` 并 `translate()` 到卡片内随机位置，避免影响「愿意」按钮布局。
2. **逃逸触发**：同时监听 `mouseover` 和 `touchstart`（passive），桌面悬停即逃、移动端一碰就逃。
3. **位移约束**：随机落点与按钮原位保持 ≥90px 距离（`Math.hypot` 判定），否则重抽，最多 30 次，防止"躲得太近等于没躲"。
4. **最小位移与动画**：每次逃逸带 0.35s 弹性过渡；`fleeing` 计数达到 5 次后改为 toast 提醒"点右边答应"，避免无限恶作剧影响体验。
5. **答应后处理**：`accept()` 会 `display:none` 掉拒绝按钮并让「愿意」按钮撑满整行。

## 屏幕流程

五屏（`#screen-1` ~ `#screen-5`）单向推进，靠 `.active` 类切换：

1. **邀约询问**：口号 + 邀请语 + 嘉宾/主题/时间 + 愿意/拒绝
2. **答应反馈**：🎉 确认赴约
3. **确认日期**：大日期卡（月/日/星期，由脚本按日历算好）
4. **选择环节**：`topics` 选项卡，可多选（事件委托在 `#topic-list` 上，点整行切换 checkbox）
5. **生成邀请函**：票根样式，含所勾选方向 chips；未勾选直接进屏5时自动全选

## 花朵飘落

- 花瓣为内联 SVG data-URI（避免外部图片引用），14 片先铺场，之后每 1.6s 追加一片。
- 每片花瓣用 CSS 自定义属性 `--dx / --rot / --o` 随机横向漂移、旋转与透明度，动画结束后从 DOM 移除。

## 其他

- `.btn:active{transform:scale(.96)}` 提供按压反馈；`user-select:none` 防长按选中文字。
- 屏5 `#chosen-topics` 由 JS 填充，不属于锚点。
- 若调整视觉、布局、交互逻辑（不由配置控制）：直接改模板后，跑一次生成脚本验证锚点仍全部命中、无残留。
