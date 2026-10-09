; 有声书下载器 EXE 安装包（Inno Setup 6）
; 编译：ISCC.exe installer.iss
; 产物：_release\有声书下载器_安装版_v2.0.0.exe

#define MyAppName "有声书下载器"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "AudioBook Downloader"
#define MyAppExeName "有声书下载器.exe"
#define MyAppIcon "app\resources\favicon.ico"
#define PortableDir "Release\有声书下载器_便携版"

[Setup]
AppId={{8F1C9E5A-2D4B-4A6F-BB33-7E3D5A1C9B42}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Release
OutputBaseFilename=audiobook-downloader-v{#MyAppVersion}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
; 便携版目录包含大量 Qt/PySide 文件，关闭压缩块限制以提高兼容性
DiskSpanning=no

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
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

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
