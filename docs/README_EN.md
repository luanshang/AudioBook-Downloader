# AudioBook Downloader

A PySide6 + QML FluentUI desktop tool for searching, previewing, and downloading authorized audiobook content from supported platforms.

[中文 README](README.md)

> Use this project only where you have lawful authorization. Copyright belongs to the respective rights holders.

## Features

- **LRTS**: Search albums, load chapters, preview audio, and download selected, ranged, or all chapters.
- **Ximalaya**: Resolve albums from an album URL or ID.
- **Qidian**: Search books, load chapters, and preview audio.
- Local search/detail cache with explicit refresh support.
- Automatic album-named subdirectories under the configured download root.
- FluentUI light/dark themes, logs, and copyright disclaimer pages.

## Requirements

- Windows 10/11 (other platforms are not currently guaranteed)
- Python 3.10+
- PySide6, requests, qasync, keyboard, qrcode, and Pillow
- `ffmpeg.exe` for audio conversion: download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and place it in `app/resources/`, or add its directory to `PATH`

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

After changing QML resources, rebuild them:

```bash
.venv\Scripts\pyside6-rcc.exe app/qml/resource.qrc -o app/qml/app_qml_rc.py
```

## Authentication and secrets

- Web and mini-program login use the built-in login flow or a Cookie.
- LRTS App mode accepts authentication parameters captured from an authorized test device.
- Cookies, tokens, device identifiers, signatures, and temporary audio URLs are sensitive data. Never commit them to GitHub.
- Start from [examples/lrts_app_auth.example.json](examples/lrts_app_auth.example.json). Keep real local credentials in `lrts_app_auth.json`; this filename is ignored by Git.

## Authorized traffic debugging

See [SKILL.md](SKILL.md) for Reqable capture setup, HTTPS certificates, filtering, request replay, redaction, and troubleshooting. Do not use traffic capture to bypass payment, access controls, or digital-rights protection.

## Project layout

```text
app/bridge/       Python/QML bridge
app/core/         Platform APIs, downloader, and converter
app/qml/          FluentUI pages and resources
examples/         Public configuration examples
_archive/         Historical material
_tools/           Packaging and installer tools
```

## Packaging

```bash
pyinstaller lrts.spec --noconfirm --clean
```

## License and disclaimer

Code, dependencies, and archived material may be covered by separate licenses. Follow each platform's terms of service. The project does not guarantee third-party API availability and is not responsible for how users download, store, share, or use content.
