# 国家中小学智慧教育平台 · 电子教材下载 API 参考

本文件记录平台电子教材下载涉及的接口、数据结构和鉴权规则。均为基础 HTTP/JSON，无需登录（部分资源在占位头下可能 400，届时需提供真实登录凭据，见文末）。

## 1. 请求头（占位鉴权，免登录）

所有请求统一携带：

```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36
Referer: https://basic.smartedu.cn/
Origin: https://basic.smartedu.cn
Authorization: Bearer 0
X-ND-AUTH: MAC id="0",nonce="0",mac="0"
```

- `X-ND-AUTH` 是平台 UC SDK 的 MAC 签名头；`id="0",nonce="0",mac="0"` 为匿名占位，官方阅读器对多数教材不校验签名只要求头格式。
- 私有 CDN（`*-ndr-private.ykt.cbern.com.cn`）下载时无需在 URL 上拼 `accessToken`。

## 2. 教材清单（三步取全量）

**a. 版本索引**

```
GET https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/version/data_version.json
```

返回：

```json
{ "urls": "https://s-file-2.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/part_100.json,..." }
```

**b. 分片清单**：逐个 GET `urls` 里的每个 part URL，每个返回一个教材条目数组（约 1000 条/片，共 4 片，全平台约 3800+ 条）。

**c. 条目字段**（关键字段）：

```json
{
  "id": "2e3dc199-9c42-486b-bbee-7731bd0ee227",
  "title": "（根据2022年版课程标准修订）义务教育教科书·语文六年级上册",
  "global_title": { "zh-CN": "..." },
  "tag_list": [
    {"tag_id": "...", "tag_name": "小学",   "tag_dimension_id": "zxxxd"},
    {"tag_id": "...", "tag_name": "语文",   "tag_dimension_id": "zxxxk"},
    {"tag_id": "...", "tag_name": "统编版", "tag_dimension_id": "zxxbb"},
    {"tag_id": "...", "tag_name": "六年级", "tag_dimension_id": "zxxnj"},
    {"tag_id": "...", "tag_name": "上册",   "tag_dimension_id": "zxxcc"}
  ],
  "tag_paths": ["..."],
  "resource_type_code": "assets_document",
  "status": "ONLINE"
}
```

### 标签维度（tag_dimension_id）

| 维度 ID | 含义 | 取值示例 |
|---|---|---|
| `zxxxd` | 学段 | 小学 / 初中 / 高中 |
| `zxxxk` | 学科 | 语文 / 数学 / 英语… |
| `zxxbb` | 版别 | 统编版 / 人教版 / 北师大版… |
| `zxxnj` | 年级 | 一年级 ~ 六年级… |
| `zxxcc` | 册次 | 上册 / 下册 |

筛选时直接匹配 `tag_list` 里的 `tag_name`（按 `tag_dimension_id` 定位维度）即可，无需关心 tag_id。

## 3. 单本元数据（取 PDF 直链）

```
GET https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/resources/tch_material/details/{contentId}.json
```

返回字段（关键）：

```json
{
  "title": "...",
  "ti_items": [
    {
      "ti_is_source_file": true,
      "ti_format": "pdf",
      "ti_size": 20472762,
      "ti_storage": "cs_path:${ref-path}/edu_product/esp/assets/{id}.pkg/xxx.pdf",
      "ti_storages": [
        "https://r1-ndr-private.ykt.cbern.com.cn/edu_product/esp/assets/{id}.pkg/xxx.pdf",
        "https://r2-ndr-private.ykt.cbern.com.cn/...",
        "https://r3-ndr-private.ykt.cbern.com.cn/..."
      ]
    }
  ]
}
```

取直链规则（按优先级）：

1. 遍历 `ti_items`，取 `ti_is_source_file == true` 且 `ti_format == "pdf"` 的项；
2. 若 `ti_storage` 以 `cs_path:${ref-path}` 开头，替换前缀为 `https://r1-ndr-private.ykt.cbern.com.cn`；
3. 否则取 `ti_storages[0]`（非空的第一条）。
4. 兜底：`ti_file_flag == "source"` 且 `ti_format == "pdf"` 的项。

## 4. 下载 PDF

- 直链位于 `r1/r2/r3-ndr-private.ykt.cbern.com.cn`（私有 CDN）。
- **必须**对 URL 的 path 做 UTF-8 百分号编码（中文、`•`、全角括号等不能直接进 HTTP 请求行），query 原样保留。
- 携带第 1 节的请求头 GET。
- 校验：响应体以 `%PDF` 开头；大小与 `ti_size` 一致。

## 5. 目录页 defaultTag 解码

`https://basic.smartedu.cn/tchMaterial?defaultTag={id1}/{id2}/{id3}/{id4}` 中的 defaultTag 是一串 tag_id，用 `/` 分隔（URL 里为 `%2F`）。解码：

```
GET https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/tch_material_tag.json
```

返回 `hierarchies` 树，把 `tag_id` 映射到 `tag_name`，即可得到筛选维度（如 `小学/语文/统编版/一年级`）。

## 6. 常见问题

| 现象 | 原因与处理 |
|---|---|
| `HTTP 400 InvalidArgument` | 该资源鉴权较严，占位头不过。需获取真实登录凭据（见下）。 |
| 元数据无 PDF 项 | 资源可能已下架或非文档类型，换 contentType 分支（课程/精品课等不在本技能范围）。 |
| 下载内容非 `%PDF` | 多为被反代/错误页拦截，检查响应头与状态码。 |
| 部分资源要求真实登录 | 登录 basic.smartedu.cn 后，在浏览器控制台执行取 `localStorage` 中 `ND_UC_AUTH-*` 的 `access_token`/`mac_key`/`diff`，按 URL 现算 HMAC-SHA256 签名生成 `X-ND-AUTH`（签名原文：`{nonce}\n{METHOD}\n{解码后的path}{?query}\n{hostname}\n`）。占位头覆盖不了时采用。 |

## 7. 相关常量参考

- 语文 contentId 示例：六年级上册 `2e3dc199-9c42-486b-bbee-7731bd0ee227`
- 小学/语文/统编版 1-6 年级上下册共 12 本（可在清单中按标签筛出）。
- 平台另有盲校、聋校等特殊教育语文教材（非统编版，tag 不含统编版）。
