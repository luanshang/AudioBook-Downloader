# 有声书下载器

基于 PySide6 + QML FluentUI 的多平台有声内容检索、试听与下载工具。

[English README](README_EN.md)

> 请仅在拥有合法授权的范围内使用本项目。下载内容的版权归原权利人所有，使用者应遵守相关法律法规、平台规则和版权要求。

## 功能

- **懒人听书**：搜索专辑、加载章节、试听、按选中/范围/全部批量下载。
- **喜马拉雅**：通过专辑 URL 或 ID 解析专辑和音频。
- **起点畅听**：搜索书籍、加载章节并试听。
- 本地搜索和详情缓存，支持刷新强制重新请求。
- 下载根目录下按专辑名自动创建子目录。
- FluentUI 深色/浅色主题、日志查看、版权与免责声明页面。

## 运行环境

- Windows 10/11（其他平台需要自行验证）
- Python 3.10+
- PySide6、requests、qasync、keyboard、qrcode、Pillow
- 音频格式转换需要 `ffmpeg.exe`：从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下载后放入 `app/resources/`，或将其所在目录加入 PATH

## 开发运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uv run python main.py
```

如果修改了 QML 资源，重新生成资源文件：

```bash
.venv\Scripts\pyside6-rcc.exe app/qml/resource.qrc -o app/qml/app_qml_rc.py
```

## 登录与本地认证文件

- Web/小程序登录通过内置登录页或 Cookie 完成。
- 懒人听书 App 模式需要从授权的测试设备抓取认证参数，在“用户登录”中粘贴 JSON。
- 起点和其他平台的 Cookie 只保存在本机设置中。
- 认证参数、Cookie、Token、设备标识和临时音频地址均属于敏感信息，不要提交到 GitHub。

示例文件：[examples/lrts_app_auth.example.json](examples/lrts_app_auth.example.json)。复制示例后，在本地创建 `lrts_app_auth.json` 并填写自己的授权参数；真实文件已加入忽略规则。

## 抓包调试

授权会话诊断、HTTPS 证书、Reqable 过滤、脱敏和故障排查请参阅 [Skill/authorized-session-diagnostics/README.md](Skill/authorized-session-diagnostics/README.md)。不得利用抓包绕过付费、访问控制或数字版权保护。

## 项目结构

```text
app/bridge/       Python 与 QML 的桥接层
app/core/         平台 API、下载器、转换器
app/qml/          FluentUI 页面和资源
examples/         可公开提交的配置示例
_archive/         历史资料，不代表当前实现
_tools/           打包和安装工具
```

## 打包

便携版（PyInstaller，依赖库与 exe 同目录）：

```bash
uv run python build/scripts/build_release.py
```

一键产出便携版 ZIP + EXE 安装包 + MSI：

```bash
uv run python build/packaging/build_all.py
```

产物输出到 `build/output/`，同时生成 `.sha256` 校验文件和更新清单 `latest.json`。

### 下载与合并（分卷压缩包）

便携版 ZIP 超过 Gitee 单文件 100MB 限制，Release 中拆分为多卷（`*.part01`、`*.part02`…）。请下载**全部分卷**后按顺序合并：

```bash
# 合并所有分卷（Windows 可用 copy 命令）
copy /b "AudioBook Downloader-v0.0.1-portable.zip.part01" + "AudioBook Downloader-v0.0.1-portable.zip.part02" + "AudioBook Downloader-v0.0.1-portable.zip.part03" "AudioBook Downloader-v0.0.1-portable.zip"
```

```bash
# 或使用 7-Zip / WinRAR 的“解压分卷”功能直接解压 .part01
```

合并后用 `.sha256` 校验完整性：

```bash
certutil -hashfile "AudioBook Downloader-v0.0.1-portable.zip" SHA256
```

## 许可证与免责声明

本仓库中的代码、依赖和归档资料分别受其对应许可证约束。使用第三方平台服务时请遵守其服务条款。项目不保证第三方接口持续可用，也不对用户下载、保存、传播或使用内容产生的后果负责。
