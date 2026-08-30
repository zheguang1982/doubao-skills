---
name: 智慧中小学教材下载
description: 从「国家中小学智慧教育平台」(basic.smartedu.cn) 批量下载电子教材 PDF。当用户要求下载该平台的电子课本/教材（如"下载智慧中小学平台的小学语文教材""下载统编版语文电子课本"），或提供 basic.smartedu.cn 的 tchMaterial 详情页/目录页链接要求下载时使用。支持按 学段/学科/版别/年级/册次 筛选、单本或整批下载，无需登录。
---

# Smartedu Textbook Downloader

从国家中小学智慧教育平台下载电子教材 PDF 的免登录方案：平台把全部电子课本清单发布在公开 JSON 上，每本教材的 PDF 直链存放在私有 CDN，只需携带占位鉴权头即可下载。

## 工作流

### 1. 确定要下载的书

三种入口，对应不同输入：

| 用户给了什么 | 用什么命令 |
|---|---|
| 单本详情页 URL（含 `contentId`） | `detail <URL>` |
| 目录页 URL（含 `defaultTag`，如 `tchMaterial?defaultTag=...`） | `batch <URL>`（自动解码标签） |
| 口头描述（如"小学语文统编版1-6年级上下册"） | 先用 `list` 确认，再 `batch --filter` |

### 2. 列出/确认教材

```bash
python scripts/download_tchmaterial.py list --filter "小学/语文/统编版" --grade 一年级 --semester 上册
```

- `--filter`：按标签名筛选，用 `/` 分隔（学段/学科/版别…），顺序不限。
- `--grade`（年级）/ `--semester`（册次）：可进一步收窄。
- 输出每本的 学段|学科|版别|年级|册次|contentId|标题。**批量下载前先 list 确认匹配数量，避免误下。**

### 3. 下载

单本：

```bash
python scripts/download_tchmaterial.py detail "https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=<ID>&catalogType=tchMaterial&subCatalog=tchMaterial" -o ./books --verify
```

整批（按筛选条件）：

```bash
python scripts/download_tchmaterial.py batch --filter "小学/语文/统编版" -o ./books --skip-existing
```

整批（直接给目录页 URL，自动解析 defaultTag 标签）：

```bash
python scripts/download_tchmaterial.py batch "https://basic.smartedu.cn/tchMaterial?defaultTag=..." -o ./books
```

- 文件名自动生成：`{学科}{年级}{册次}.pdf`（如 `语文一年级上册.pdf`），无标签时回退到书名。
- `--skip-existing`：跳过已存在的文件，适合断点续传/重复任务。
- `--verify`（仅 detail）：用 pymupdf 校验页数与首页文字（未安装 pymupdf 则自动跳过）。

### 4. 验证与交付

- 每本下载后脚本已校验 `%PDF` 魔数与大小（与平台元数据 `ti_size` 比对）。
- 交付前建议抽样用 pymupdf 打开确认页数与首页标题，再通过 `present_files` 交付给用户。
- 向用户说明版权：仅限个人教学/学习参考，勿商用或二次分发。

## 常见故障

| 现象 | 处理 |
|---|---|
| `HTTP 400 InvalidArgument` | 该资源鉴权较严，占位头不过；需真实登录凭据（见 `references/api.md` 第 6 节）。 |
| `list` 无结果 | 放宽 `--filter`；确认平台确有该学段/学科/版别的电子教材。 |
| 中文/特殊字符报错 | 脚本已自动对 URL path 做 UTF-8 百分号编码，无需手工处理。 |

## 资源

- `scripts/download_tchmaterial.py`：主脚本（detail / list / batch 三个子命令）。
- `references/api.md`：完整接口文档（请求头、教材清单结构、标签维度、元数据解析、defaultTag 解码、真实登录签名方法）。
