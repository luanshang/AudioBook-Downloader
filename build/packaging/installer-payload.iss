; 有声书下载器 静默载荷安装包（被 Tauri 引导器嵌入并静默调用）
; 编译：ISCC.exe installer-payload.iss
; 产物：build\installer\payload.exe

#define MyAppName "有声书下载器"
#define MyAppSlug "AudioBook Downloader"
#ifndef MyAppVersion
#define MyAppVersion "0.0.1"
#endif
#define MyAppInstallDir "有声书下载器"
#define MyAppPublisher "AudioBook Downloader"
#define MyAppExeName "有声书下载器.exe"
#define MyAppIcon "installer_icon.ico"
#define PortableDir "..\output\有声书下载器_便携版"

[Setup]
AppId={{B8A4E1F3-9C2D-4E5A-B7F1-3D8A9C4B2E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} Ver {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppInstallDir}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\installer
OutputBaseFilename=payload
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
; 便携版目录包含大量 Qt/PySide 文件，关闭压缩块限制以提高兼容性
DiskSpanning=no
; 静默载荷：隐藏 Inno 自己的向导界面，由外层 Tauri 引导器展示进度
ShowLanguageDialog=no
DisableDirPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes
DisableWelcomePage=yes
UsePreviousAppDir=no
AppendDefaultDirName=no
CreateUninstallRegKey=no
Uninstallable=no
CloseApplications=no
RestartApplications=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
Source: "{#PortableDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"

[Code]
procedure InitializeWizard;
begin
  WizardForm.Caption := '{#MyAppName} 安装向导';
  WizardForm.WelcomeLabel1.Caption := '欢迎安装 {#MyAppName}';
  WizardForm.WelcomeLabel2.Caption := '安装向导将把 {#MyAppName} 安装到本机。' + #13#10 +
    '点击“下一步”继续。';
end;
