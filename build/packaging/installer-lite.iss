; 有声书下载器 精简版安装包（标准 Inno 向导，不定制化）
; 编译：ISCC.exe installer-lite.iss
; 产物：build\output\AudioBook Downloader-v0.0.1-lite-setup.exe

#define MyAppName "有声书下载器"
#define MyAppSlug "AudioBook Downloader"
#ifndef MyAppVersion
#define MyAppVersion "0.0.1"
#endif
#define MyAppInstallDir "有声书下载器"
#define MyAppPublisher "AudioBook Downloader"
#define MyAppExeName "有声书下载器.exe"
#define MyAppIcon "installer_icon.ico"
#define SlimDir "..\output\精简版_noUPX"

[Setup]
AppId={{9C5A8F1E-4B2D-4A6F-BB33-7E3D5A1C9B42}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} Ver {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppInstallDir}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\output
OutputBaseFilename={#MyAppSlug}-v{#MyAppVersion}-lite-setup
Compression=lzma2/ultra
SolidCompression=yes
LZMADictionarySize=524288
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
DiskSpanning=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
Source: "{#SlimDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent runascurrentuser
