<div align="center">
    <br>
    <table>
        <tr>
            <td valign="center"><a href="README.md"><img src="https://github.com/twitter/twemoji/blob/master/assets/svg/1f1fa-1f1f8.svg" width="16"/>English</a></td>
            <td valign="center"><a href="README_zh-cn.md"><img src="https://em-content.zobj.net/thumbs/120/twitter/351/flag-china_1f1e8-1f1f3.png" width="16"/>简体中文</a></td>
        </tr>
    </table>
    <br>
</div>

# OPlus Tracker

用于查询和解析 OPPO、一加 (OnePlus)、真我 (Realme) 设备 (ColorOS / OxygenOS) 的 OTA / SOTA / OPEX / IOT / 降级更新链接的工具集合。

当前脚本列表：

- `C16_transer.py` → 解析动态下载链接 (ColorOS 16+)
- `tomboy_pro.py` → 核心 OTA 查询工具 (全量 / 增量 / 灰度 / 尝鲜版 / 绕过防查询)
- `opex_query.py` → 专用 OPEX 查询工具 (仅限国区)
- `sota_query.py` → SOTA (Software OTA / 模块化 APK) 查询工具 (目前仅限国区)
- `sota_changelog_query.py` → SOTA (Software OTA / 模块化 APK) 更新日志查询工具 (目前仅限国区)
- `iot_query.py` → 旧版及 IoT 服务器查询工具 (仅限国区)
- `downgrade_query.py` → 查询官方降级包 (仅限国区)
- `realme_edl_query.py` → 查询真我官方 EDL (9008线刷) 包
- `changelog_query.py` → 查询特定版本的更新日志
- `config.py` → 公钥、服务器地址和 API 接口配置文件。

## `C16_transer.py`

### 功能特性

- 解析带有 `downloadCheck?` 的动态链接
- 显示最终下载链接及过期时间

### 依赖项

- `requests`

安装：

```bash
pip install requests
```

### 用法

```bash
python C16_transer.py "https://gauss-componentotacostmanual-cn.allawnfs.com/.../downloadCheck?Expires=1767225599&..."
```

## `tomboy_pro.py`

核心进阶 OTA 查询工具 —— 支持全量包、增量更新、灰度通道、尝鲜版、原神定制版、绕过防查询（2025年10月之后）等功能。

### 主要特性

- 自动补全后缀 (`_11.A` / `_11.C` / `_11.F` / `_11.H` / `_11.J`)
- 模式选项：`manual`, `client_auto`, `server_auto`, `taste`
- 使用 `--anti 1` 绕过 ColorOS 16 受限机型的限制
- 通过 `--components` 获取增量 OTA

### 依赖项

```text
requests
cryptography
```

```bash
pip install -r requirements.txt
```

### 用法

```bash
python tomboy_pro.py <OTA_PREFIX> <REGION> [options]
```

#### 位置参数

- `<OTA_PREFIX>` (OTA前缀) 例如：`PJX110` / `PJX110_11.A` / `PJX110_11.C.36_...`
- `<REGION>` (地区) 可选：`cn` `cn_cmcc` `eu` `in` `sg` `ru` `tr` `th` `gl` `tw` `my` `vn` `id` `sa` `mea` `ph` `la` `br` `roe`

#### 常用标志参数

| 标志 (Flag)     | 含义                                           | 示例 / 备注                        |
| --------------- | ---------------------------------------------- | ---------------------------------- |
| `--model`       | 强制指定机型                                   | `--model PJX110`                   |
| `--gray 1`      | 测试通道（主要用于 Realme，少量 OPlus）        |                                    |
| `--mode taste`  | 通常与 `--anti 1` 一起使用                     |                                    |
| `--genshin 1/2` | 原神定制版（带有 YS / Ovt 后缀）               |                                    |
| `--pre 1`       | 尝鲜版（需要使用 `--guid` 参数）               |                                    |
| `--guid 64hex`  | 64 位字符的设备 GUID                           | 获取尝鲜版/体验版必需              |
| `--components`  | 增量查询（格式：name:fullversion,...）         | `--components System:PJX110_11...` |
| `--anti 1`      | 绕过 ColorOS 16 查询限制（约 2025 年 10 月起） | 通常配合 `--mode taste` 使用       |
| `--nvid 8digit` | 使用自定义 NV 运营商 ID 进行查询               |                                    |
| `--graynew 1`   | 查询不在尝鲜模式但在灰度服务器中的固件         |                                    |

#### 示例

```bash
# 基础国区查询
python tomboy_pro.py PJX110_11.A cn

# ColorOS 16 绕过防查询
python tomboy_pro.py PLA110_11.A cn --anti 1

# 增量 OTA
python tomboy_pro.py PJX110_11.C.36_1360_20250814 cn --components System:PJX110_11.C.35_...

# 带有 GUID 的尝鲜版查询
python tomboy_pro.py PJX110_11.A cn --pre 1 --guid 0123456789abcdef... (64 chars)

# 自定义 NVID
python tomboy_pro.py RMX3301_11.H sg --nvid 00011011
```

**注意**：获取增量 OTA (Delta) 比较特殊，你可以通过在设备中运行 `getprop | grep ro.oplus.version | sed -E 's/\[ro\.oplus\.version\.([^]]+)\]: \[([^]]+)\]/\1:\2/g' | tr '\n' ',' | sed 's/,$//' | sed 's/base/system_vendor/g'` 来获取组件信息，并确保使用全量 OTA 版本，且需与组件版本保持一致。

## `opex_query.py`

查询 **OPEX**（主要针对 ColorOS 国区变体）的专用工具。

### 用法

```bash
python opex_query.py <FULL_OTA_VERSION> --info <OS_VERSION>,<BRAND>

# 示例
python opex_query.py PJZ110_11.C.84_1840_202601060309 --info 16,oneplus
python opex_query.py RMX5200_11.A.63_... --info 16,realme
```

**注意**：需要完整的 OTA 版本字符串（至少包含 3 个 `_` 分隔段）。

## `sota_query.py`

查询 **SOTA** (Software OTA) —— 主要用于国区 ColorOS 系统级应用更新。

### 用法

```bash
python sota_query.py --brand BRAND --ota-version OTA_VERSION --coloros COLOROS

# 示例
python sota_query.py --brand OnePlus --ota-version PJX110_11.F.15_2150_202602051458 --coloros ColorOS16.0.0
```

**注意**：这 3 个参数都是**必填**项（请参考示例）。

## `sota_changelog_query.py`

查询 **SOTA** (Software OTA) 更新日志 —— 主要用于国区 ColorOS 系统级应用更新。

### 用法

```bash
python sota_query.py --brand BRAND --ota-version OTA_VERSION --coloros COLOROS

# 示例
python sota_query.py --brand OnePlus --ota-version PJX110_11.F.15_2150_202602051458 --coloros ColorOS16.0.0
```

**注意**：用法与 `sota_query.py` 相同，但仅用于查询更新日志。

## `iot_query.py`

使用旧版 **iota.coloros.com** 特殊服务器的查询工具（仅限国区）。  
通常会返回常规通道中不再提供的旧版本或特殊版本。

### 用法

```bash
python iot_query.py <OTA_PREFIX> cn [options]

# 示例
python iot_query.py OWW221 cn
python iot_query.py OWW221_11.A cn --model OWW221
```

**注意**：仅支持 `cn` 区域。返回结果可能已过时。

## `downgrade_query.py` & `downgrade_query_old.py`

从 `downgrade.coloros.com` 查询官方**降级包**（仅限国区）。  
当你需要仍具有官方签名且允许降级的旧版官方固件时非常有用。

### 功能特性

- 使用 AES-256-GCM + RSA-OAEP 加密（与官方降级服务器一致）
- 需要真实的 **DUID**（从拨号盘输入 \*#6776# 获取的 64 位 SHA256 字符串）
- 需要 **PrjNum**（5 位项目代码）
- 返回下载链接、更新日志、版本信息、MD5 和发布时间

### 依赖项

- `requests`
- `cryptography`

安装：

```bash
pip install requests cryptography
```

### `downgrade_query.py` 的用法

```bash
python downgrade_query.py <OTA_PREFIX> <PrjNum> <snNum> <DUID> [--debug 0/1]

# 示例
python downgrade_query.py PKX110_11.C 24821 a1b2c3e4 498A44DF1BEC4EB19FBCB3A870FCACB4EC7D424979CC9C517FE7B805A1937746
```

#### 参数限制

- `<OTA_PREFIX>` : 必须包含至少一个 `_`（例如 `PKX110_11.C`）
- `<PrjNum>` : 必须是 5 位数字（例如 `24821`）
- `<snNum>` : 手机的 SN 序列号
- `<DUID>` : 64 位 SHA256 字符串（通过拨号盘代码 \*#6776# 获取）
- `[--debug 0/1]` : 获取官方降级流程的元数据

#### 输出示例

```text
Fetch Info:
• Link: https://...
• Changelog: ...
• Version: ColorOS 15.0 (Android 15)
• Ota Version: PKX110_11.C.12_...
• MD5: abcdef123456...
```

### `downgrade_query_old.py` 的用法

```bash
python downgrade_query.py <OTA_PREFIX> <PrjNum>

# 示例
python downgrade_query.py PKX110_11.C 24821
```

#### 参数限制

- `<OTA_PREFIX>` : 必须包含至少一个 `_`（例如 `PKX110_11.C`）
- `<PrjNum>` : 必须是 5 位数字（例如 `24821`）

#### 输出示例

```text
Fetch Info:
• Link: https://...
• Changelog: ...
• Version: ColorOS 15.0 (Android 15)
• Ota Version: PKX110_11.C.12_...
• MD5: abcdef123456...
```

**注意**：仅适用于支持官方降级的机型/地区。服务器可能会拒绝无效的 DUID 或项目代码。

## `realme_edl_query.py`

使用 REALME 服务器查询 EDL (9008线刷) ROM 的查询工具。

### 用法

```bash
python realme_edl_query.py <VERSION_NAME> <REGION> <DATE>

# 示例
python3 realme_edl_query.py "RMX3888_16.0.3.500(CN01)" CN 202601241320
```

#### 输出示例

```text
Querying for RMX8899_16.0.3.532(CN01)

Fetch Info:
• Link: https://rms11.realme.net/sw/RMX8899domestic_11_16.0.3.532CN01_2026013016580190.zip
```

**注意**：你可以从全量 OTA 版本字符串中获取日期参数，通常是 `_` 分隔的第三部分。

## `changelog_query.py`

查询特定版本的更新日志。

#### 参数限制

- `<OTA_PREFIX>` 例如 `PJD110_11.F.39_2390`
- `<REGION>` 可选：`cn` `cn_cmcc` `eu` `in` `sg` `ru` `tr` `th` `gl` `tw` `my` `vn` `id` `sa` `mea` `ph` `la` `br` `roe`
- `[--pre 0/1]` : 获取测试版 / 测试设备的更新日志

### 用法

```bash
python3 changelog_query.py <OTA_VERSION> <REGION>

# 示例
python3 changelog_query.py PJD110_11.F.39_2390 CN

python3 changelog_query.py PLP110_11.A.40_0400 CN --pre 1
```

**注意**：你可以不使用完整的 OTA 版本号，但至少需要包含两个 `_`（需包含版本号和版本代码）。

### 重要提示 (2025–2026)

- ColorOS 16 引入了强力的防查询限制（约在 2025 年 10 月）。在 `tomboy_pro.py` 中使用 `--anti 1` + `taste` 模式 + 基础版本号（例如 `11.A`）可以在许多机型上绕过此限制。
- 带有 `downloadCheck?` 的动态链接通常在 **10–30 分钟**内过期 —— 获取链接后请立即使用 `C16_transer.py` 进行解析。
- 目前 `opex_query.py`、`sota_query.py`、`iot_query.py` 和 `downgrade_query.py` **仅限国区 (CN-only)** 使用。
- 所有工具在每次请求时都会重新生成加密密钥 / 设备 ID，以减少被服务器端封禁的风险。
