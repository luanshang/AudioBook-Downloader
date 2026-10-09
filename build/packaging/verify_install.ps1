$env:LRTS_SETUP_SILENT = "1"
$installer = "E:\AI\Chat\WorkSpace\Software\AudioBook Downloader\_tools\dist\有声书下载器_安装版_v2.0.0.exe"
$p = Start-Process -FilePath $installer -PassThru -Wait
Write-Output "安装器退出码: $($p.ExitCode)"
$appDir = "$env:LOCALAPPDATA\Programs\有声书下载器"
Write-Output "安装目录存在: $(Test-Path $appDir)"
Write-Output "主程序存在: $(Test-Path "$appDir\有声书下载器.exe")"
Write-Output "python313.dll 存在: $(Test-Path "$appDir\_internal\python313.dll")"
Write-Output "_internal 目录存在: $(Test-Path "$appDir\_internal")"
