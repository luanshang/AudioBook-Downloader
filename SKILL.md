---
name: reqable-capture
description: 使用 Reqable 对本项目及授权服务进行 HTTP/HTTPS/WebSocket 抓包、分析、导出和复现。
---

# Reqable 抓包 Skill

## 目的与授权边界

本 Skill 用于调试本项目的网络请求、定位接口参数、验证登录状态以及排查下载失败。只对自己拥有或明确获准测试的设备、账号、应用和服务抓包。抓包内容可能包含 Cookie、Token、设备标识、签名参数、音频地址和个人信息，必须按敏感数据处理。

不得使用抓包结果绕过付费、访问控制、数字版权保护或他人账号权限；不得把真实 Token、Cookie、密码、私钥或完整抓包文件提交到 Git、Issue、聊天记录或公开网盘。

## 项目相关背景

本项目是 PySide6/QML 有声书下载器，涉及：

- 懒人听书：Web/小程序接口通常位于 `m.lrts.me`，移动 App 接口通常位于 `gzapi.mting.info`。
- 喜马拉雅：专辑解析、音频地址和登录请求可能来自多个域名。
- 起点：搜索、书籍详情和章节请求可能依赖登录 Cookie。
- 本项目的 App 登录可能需要 `token`、`imei`、`lrid`、`sc` 等签名或设备参数。只记录确认需要的字段，不要把完整认证 JSON 写入源码。

## 抓包前准备

1. **确认目标和问题**
   - 明确要观察的动作：登录、搜索、打开专辑、加载章节、播放、下载或刷新。
   - 记录复现步骤、时间、客户端版本、设备/系统、是否登录和预期结果。
   - 先确定需要的最小范围：域名、HTTP 方法、状态码、请求头、查询参数、请求体或响应字段。

2. **安装并检查 Reqable**
   - 从 Reqable 官方渠道安装桌面端或移动端客户端。
   - 启动 Reqable，确认设备已连接、捕获功能处于开启状态。
   - 不要同时开启多个会改写系统代理的抓包工具；ProxyPin、Charles、Fiddler 与 Reqable 同时运行可能造成代理链冲突。
   - 关闭无关应用或使用过滤器，减少账号、支付、消息等非目标流量进入捕获记录。

3. **备份和隔离**
   - 使用专门的测试账号和测试设备，避免使用主账号。
   - 捕获前关闭自动同步、云剪贴板和不必要的浏览器标签页。
   - 需要提交日志时，只保留脱敏后的请求结构和必要字段。

## 配置系统代理

1. 在 Reqable 中开启系统代理，或在目标设备的 Wi-Fi/网络设置中手动填写 Reqable 显示的代理地址和端口。
2. 确认设备与电脑在同一网络；Windows 防火墙需要允许 Reqable 接收局域网连接。
3. 浏览器打开一个普通 HTTPS 网站测试代理是否生效。
4. 抓包结束后关闭系统代理或恢复原代理设置。代理未关闭可能导致其他程序无法联网。
5. 如果项目运行在本机，检查 `127.0.0.1` 流量是否被系统代理绕过；如果目标是手机，确认手机流量确实经过电脑地址而不是移动数据直连。

## HTTPS 证书安装与注意事项

HTTPS 请求默认加密，必须在测试设备上安装 Reqable CA 证书才能查看内容。

### 桌面系统

1. 在 Reqable 的证书/HTTPS 设置中生成或安装本机 CA。
2. 按 Reqable 指引将 CA 安装到系统或浏览器的“受信任的根证书颁发机构”。
3. 只在专用测试环境安装。完成抓包后删除证书或恢复测试环境快照。
4. 浏览器访问一个 HTTPS 网站，确认请求可以解密且没有证书警告。

### Android/iOS

1. 在目标设备浏览器访问 Reqable 提供的证书安装地址，或使用 Reqable 的设备引导流程。
2. Android 新版本中，普通应用可能不信任用户安装的 CA；不要为了绕过限制而修改生产设备或使用未知来源证书。
3. iOS 安装后还需要在“关于本机 → 证书信任设置”启用完整信任。
4. 某些应用启用了证书固定（certificate pinning），此时只能看到连接失败或握手信息。不要对无授权应用绕过固定；应改用开发构建、测试后端或服务方提供的调试配置。
5. 抓包结束后卸载 Reqable CA，并关闭系统代理。

### 证书失败的诊断

- `CERTIFICATE_VERIFY_FAILED`：检查 CA 是否安装、是否过期、设备时间是否正确。
- `handshake_failure`：可能是 TLS 版本、代理链或证书固定问题。
- 浏览器能抓到、App 抓不到：检查 App 是否使用独立网络栈、QUIC/HTTP3、证书固定或 VPN。
- 只看到 CONNECT：说明隧道建立但 HTTPS 解密未成功，先检查 CA 和 HTTPS 捕获开关。

## 开始捕获

1. 在 Reqable 中清空旧记录，避免把历史 Token 混入分析。
2. 开启 Live Capture/实时捕获。
3. 先执行一次无关操作确认记录在增长，再执行最小复现步骤。
4. 每一步只做一个动作并等待请求完成，例如：
   - 打开登录页；
   - 完成扫码或提交 Cookie；
   - 点击检测登录状态；
   - 搜索一个唯一关键词；
   - 打开一个专辑；
   - 加载第一页章节；
   - 点击试听或批量下载。
5. 通过 Host、URL、Method、Status Code 和关键词过滤。优先过滤域名，不要只按“api”或“data”等宽泛关键词。
6. 复现完成后立即停止捕获，再分析已保留记录。

## 分析单条请求

按以下顺序记录，不要盲目复制全部内容：

1. **请求基本信息**：方法、完整 URL、协议版本、状态码、耗时和重定向链。
2. **查询参数**：参数名、是否必需、是否变化、是否疑似时间戳或签名。
3. **请求头**：只保留与复现有关的头，例如 `Content-Type`、`User-Agent`、`Referer`、`Origin`、必要的 `Authorization`。Cookie、Token、设备 ID 必须脱敏。
4. **请求体**：区分 JSON、表单、multipart、二进制；记录字段类型和最小有效样例。
5. **响应**：状态码、Content-Type、错误码、分页字段、音频地址字段和鉴权失败信息。
6. **时序关系**：登录请求、刷新 Token、详情请求、分页请求和播放/下载地址请求之间的依赖。
7. **变化字段**：连续执行两次相同动作，比较时间戳、随机数、nonce、签名和设备参数，不能仅凭字段名判断签名算法。

建议建立如下记录表：

| 动作 | 方法 | 主机 | 路径 | 必要参数 | 响应关键字段 | 是否依赖登录 |
|---|---|---|---|---|---|---|
| 搜索 | GET/POST | 脱敏后的主机 | 脱敏路径 | keyword、page | album/list | 否/是 |
| 专辑详情 | GET/POST | 脱敏后的主机 | 脱敏路径 | albumId | tracks | 是 |
| 音频地址 | GET/POST | 脱敏后的主机 | 脱敏路径 | section、token | url/path | 是 |

## 导出、重放与代码接入

1. 只对经过脱敏的单条请求执行“复制 cURL/导出”。
2. 导出的 cURL 先在文本编辑器中删除：
   - `Cookie`、`Authorization`、`Set-Cookie`；
   - `token`、`access_token`、`refresh_token`、`sign`、`sc`、`imei` 等真实值；
   - 个人账号、手机号、设备序列号和完整音频 URL。
3. 用占位符替换，例如 `<TEST_TOKEN>`、`<ALBUM_ID>`，并在本地通过环境变量或设置注入真实值。
4. 用 Reqable Compose 或 cURL 重放时，先使用 GET/只读接口；确认不会重复下单、提交登录、消耗下载次数或改变服务端数据。
5. 对比原始请求与重放请求的状态码、响应体和关键字段。若结果不同，按 Cookie、签名时效、Referer/Origin、User-Agent、请求体编码和 IP/设备绑定逐项排查。
6. 不要把抓包导出的 cURL 原样放进 README、测试代码或提交记录。

## WebSocket、长连接和特殊流量

- 对 WebSocket，先记录握手 URL、`Upgrade`、`Origin`、鉴权头和握手响应，再记录消息方向、时间和消息类型。
- 二进制消息先保存哈希、长度和前几个字节，不要直接把可能包含凭据的完整消息提交。
- HTTP/3、QUIC、DoH、VPN 或应用内自定义加密可能不会以普通 HTTP 记录呈现；先让目标客户端切换到测试环境支持的 HTTP/1.1 或 HTTP/2，再判断是否为抓包工具限制。
- 音频下载通常会产生 30x 重定向、Range 请求或 CDN 请求。分析时区分“获取播放/下载地址的 API”和“真正传输音频的 CDN URL”。

## Reqable Rewrite 和 Script

### Rewrite

Rewrite 适合临时调试，例如修改测试请求中的分页参数、替换测试响应字段或添加调试 Header。

- 只对明确的 Host、路径和方法设置规则。
- 先禁用规则，确认原始行为，再一次只启用一条规则。
- 修改响应时保留 Content-Length、Content-Encoding 等一致性，避免压缩或长度不匹配。
- 抓包完成后关闭全局 Rewrite，并删除临时规则。

### Python Script

Script 适合记录调试信息、对测试响应做结构化检查或自动标记异常。

- 脚本只处理测试流量，避免输出完整 Cookie、Token、密码和音频地址。
- 记录哈希、长度、字段名和状态码，必要时只记录值的前后少量字符。
- 创建或更新 Reqable Script 前，先读取当前版本的 Script Framework 和 Script Template；不要凭记忆编写不符合 Reqable 生命周期的脚本。
- 脚本异常可能影响请求，调试完成后禁用并删除临时脚本。

## 本项目的推荐抓包流程

1. 在项目中打开对应平台页面，确认登录模式和测试账号。
2. 清空 Reqable 捕获记录，打开目标域名过滤。
3. 重新执行一次登录检测，确认登录请求和响应中的会话字段。
4. 搜索一个唯一关键词，记录搜索接口的关键词、分页参数和响应列表结构。
5. 点击一个专辑，记录详情接口、专辑 ID、第一页参数和章节字段。
6. 点击“加载全部”，确认是否产生分页请求以及最后一页条件。
7. 选择一集试听或开始下载，区分获取音频地址的请求和 CDN 文件请求。
8. 对失败请求记录状态码、响应错误码、请求时间和是否换 Token 后恢复。
9. 只把脱敏后的字段结构写入项目文档；真实认证值通过应用设置或本地环境变量提供。
10. 停止捕获、关闭代理、卸载测试 CA，并清理本地临时导出文件。

## Reqable MCP Server

本项目调试时可以通过已配置的 Reqable MCP Server 操作桌面端 Reqable，减少手动复制请求的步骤。MCP 调用仍然只允许用于已授权的测试流量；工具返回的请求头、请求体和响应可能含有真实凭据，禁止原样写入代码或提交 GitHub。

### 可用能力概览

- **资源**：读取 `script_framework` 和 `script_template`，用于编写 Reqable Python Script。
- **实时捕获**：启动/停止 Live Capture，按 URL、Host、方法、状态码、应用或关键词过滤记录，查看单条完整记录。
- **请求复现**：生成单条记录的 cURL，或将记录 Compose 成 Reqable HTTP/WebSocket 标签页。
- **断点**：创建、查看、更新、启用/禁用和删除 Request/Response Breakpoint。
- **Rewrite**：创建、查看、更新、启用/禁用和删除重写规则。
- **Script**：创建、查看、更新、启用/禁用和删除 Python Script 规则。
- **集合**：创建 Collection、Folder 和 API，导入 cURL，生成/更新/删除集合 API。
- **代理**：设置 Reqable 是否覆盖系统代理。

### MCP 调用顺序

1. 先确认 Reqable 已启动且目标设备/应用已连接。
2. 调用代理设置检查或关闭其他代理工具；需要捕获时再启用系统代理。
3. 用 `capture_live_set_enabled(enabled=true)` 开始捕获。
4. 执行一次最小复现动作，然后用 `capture_live_filter` 按 Host、URL、Method 或 Code 缩小结果。
5. 对过滤出的数字记录 ID 调用 `capture_live_get_by_id` 查看完整请求/响应；不要在聊天中直接转发完整内容。
6. 需要命令行验证时调用 `capture_live_generate_curl`，先脱敏输出再运行。
7. 需要在 Reqable 中继续观察或编辑时调用 `capture_live_compose`。
8. 复现结束后调用 `capture_live_set_enabled(enabled=false)`，并关闭系统代理。

### 捕获与过滤示例

工具参数使用 JSON；示例中的域名和关键词均为占位符：

```json
{"enabled": true}
```

```json
{"filters": [{"type": "host", "hosts": ["api.example.test"]}]}
```

```json
{"filters": [{"type": "method", "methods": ["POST"]}, {"type": "code", "codes": [401, 403]}]}
```

```json
{"filters": [{"type": "keyword", "pattern": "batchGetListenPath", "regex": false, "caseSensitive": false}]}
```

过滤结果只返回记录 ID；必须再调用 `capture_live_get_by_id` 获取详情。多个过滤器是 AND 关系，URL 过滤是精确 URL 匹配。分析本项目时通常先按 Host 过滤，再按方法或路径关键词过滤。

### Reqable MCP 安全规则

- 不要调用 `capture_live_generate_curl` 后把原始结果粘贴到 README、Issue、提交记录或公共聊天。
- 不要把 `capture_live_get_by_id` 返回的 Cookie、Authorization、Token、设备 ID、二维码和临时 CDN URL 转发给不需要的人员。
- 捕获记录 ID 可能在不同会话中复用；每次开始新会话都重新过滤，不要假定旧 ID 仍指向同一请求。
- 捕获完成后必须停止 Live Capture，并恢复系统代理状态。
- 修改 Rewrite/Breakpoint/Script 前先读取配置；创建规则时使用精确 Host、URL 和 HTTP 方法，避免误改全局流量。
- 删除规则前先用 get 接口确认 ID 和匹配范围；调试结束后删除临时规则。

### Breakpoint 调试

适合检查或临时修改单个请求/响应：

1. 用 `capture_breakpoint_create` 指定名称、URL、方法，以及只在 Request 或 Response 断点。
2. 用 `capture_breakpoint_set_enabled` 启用全局断点功能。
3. 命中后在 Reqable 中检查请求或响应；只修改测试数据。
4. 用 `capture_breakpoint_update` 禁用单条规则，或用 `capture_breakpoint_delete` 删除规则。
5. 完成后确认全局断点功能关闭。

断点会暂停请求，可能导致客户端超时；不要在批量下载或生产账号上使用宽泛 URL 断点。

### Rewrite 与 Script 的 MCP 流程

Rewrite 的创建/更新参数必须包含完整 action。先用 `capture_rewrite_get_config` 读取现有配置，创建后用 `capture_rewrite_get_by_id` 核对规则，再按需启用。响应 Body、Content-Encoding、Content-Length 和状态码必须保持一致。

创建或更新 Script **之前必须先读取** Reqable 的 `script_framework` 和 `script_template` 资源，按当前版本生命周期编写代码。脚本只记录状态码、字段名、长度或脱敏摘要，不记录完整凭据。创建后先禁用验证，再限定到单个测试 URL；完成后禁用并删除。

### 从 Live Capture 导入 Collection

1. 通过 `capture_live_generate_curl` 获取脱敏后的 cURL。
2. 用 `collection_create` 创建测试集合，必要时用 `collection_folder_create` 建立平台或功能目录。
3. 用 `collection_api_create` 导入 cURL，或用 `collection_api_add` 写入结构化 API。
4. 用 `collection_api_get` 检查请求方法、URL、Header、Body 和授权模式。
5. 不要把真实 Cookie/Token 固化在 Collection；优先使用继承配置、环境变量或本地测试值。
6. 分享集合前再次执行脱敏检查。

### 本项目的 MCP 排查配方

- **搜索失败**：过滤目标平台 Host + `GET`/`POST`，查看状态码、关键词参数、分页字段和响应错误码。
- **专辑列表为空**：先抓搜索请求，再抓详情请求；分别核对专辑 ID、第一页参数和响应字段，不要只重放详情请求。
- **批量下载出现“请验证”**：过滤 `batchGetListenPath`，查看 `apiStatus`、`msg`、请求批次大小和认证参数是否变化；停止捕获后脱敏记录错误结构。
- **登录失效**：按时间顺序查看登录检测、Cookie/Token 写入和业务请求，比较状态码及会话字段是否过期。
- **音频播放失败**：区分获取播放地址的 API 与后续 CDN 请求，分别检查重定向、Range、Referer、有效期和响应 Content-Type。

### MCP 调用结束检查

- [ ] 已停止 Live Capture。
- [ ] 已关闭或恢复系统代理。
- [ ] 已禁用并删除临时 Breakpoint、Rewrite、Script。
- [ ] 已清理 Compose 标签页和本地 cURL/HAR 临时文件。
- [ ] 已对所有 MCP 返回内容执行 Cookie、Token、设备信息和 URL 脱敏。


### 没有任何记录

检查系统代理是否开启、设备是否使用正确网络、Reqable 是否有防火墙权限、目标进程是否绕过代理，以及是否误用了 VPN/移动数据。

### 只有部分请求

检查域名过滤、HTTPS 解密、HTTP/3/QUIC、WebSocket 开关和应用是否使用多个 API 域名。不要只盯着主页面域名，登录和 CDN 常常位于不同主机。

### 请求返回 401/403

先检查 Cookie/Token 是否过期，再检查签名时效、设备参数、Referer/Origin、请求体编码和账号权限。不要简单地反复重放真实请求。

### 重放成功但项目失败

比较 URL 编码、JSON 字段类型、Header、重定向处理、压缩方式和超时；确认项目后台任务没有在主线程同步执行，并检查 `logs/app.log` 中的完整 traceback。

### 下载目录或音频地址异常

分别记录“获取地址”响应和实际 CDN 请求。地址可能短时有效、绑定 User-Agent/Referer、需要 Range 请求，或者返回加密格式。不要把临时 CDN URL 当成永久接口。

## 脱敏清单

提交任何截图、HAR、cURL 或日志前逐项检查：

- Cookie、Authorization、Bearer Token、JWT；
- `token`、`access_token`、`refresh_token`、`sign`、`sc`、`imei`、设备 ID；
- 手机号、邮箱、用户 ID、昵称、二维码内容；
- 完整音频 CDN URL、临时签名和下载地址；
- 请求体中的密码、支付信息和个人资料；
- 响应中的 Set-Cookie、私有下载地址和内部错误堆栈。

脱敏后仍需保留方法、域名（必要时替换为 `api.example.test`）、路径结构、参数名、字段类型、状态码和错误码，以便复现问题。

## 完成检查

- [ ] 只抓取已获授权的目标和测试账号。
- [ ] 已清空旧记录并使用最小复现步骤。
- [ ] 已记录请求与响应的结构、时序和关键错误码。
- [ ] 已删除或脱敏所有凭据和临时 URL。
- [ ] 已关闭 Live Capture、系统代理和临时 Rewrite/Script。
- [ ] 已卸载测试设备上的 Reqable CA。
- [ ] 已验证项目代码不包含真实 Token、Cookie 或密码。
