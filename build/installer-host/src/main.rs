#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::fs::{self, File};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
#[cfg(windows)]
use std::os::windows::process::CommandExt as _;
#[cfg(windows)]
use std::os::windows::ffi::OsStrExt;
const DETACHED_PROCESS: u32 = 0x00000008;
#[cfg(windows)]
use windows_sys::Win32::UI::Shell::{ShellExecuteExW, SEE_MASK_NOCLOSEPROCESS, SHELLEXECUTEINFOW};
#[cfg(windows)]
use windows_sys::Win32::System::Threading::{GetExitCodeProcess, WaitForSingleObject};
#[cfg(windows)]
use windows_sys::Win32::Foundation::CloseHandle;
use std::ptr::null_mut;
use tauri::{AppHandle, Emitter, WebviewWindow};

const PRODUCT: &str = "有声书下载器";
const APP_EXE: &str = "有声书下载器.exe";
const VERSION: &str = "0.0.1";

// `scripts/build-installer.mjs` replaces this payload before compiling us.
static PAYLOAD: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/payload.exe"));

type InstallPath = Arc<Mutex<Option<(PathBuf, String)>>>;

fn install_root_for_mode(mode: &str) -> String {
    if mode == "perMachine" {
        std::env::var("PROGRAMFILES").unwrap_or_else(|_| "C:\\Program Files".to_string())
    } else {
        let local_app_data = std::env::var("LOCALAPPDATA").unwrap_or_else(|_| ".".to_string());
        PathBuf::from(local_app_data)
            .join("Programs")
            .to_string_lossy()
            .into_owned()
    }
}

fn installed_exe_path(mode: &str) -> PathBuf {
    PathBuf::from(install_root_for_mode(mode)).join(PRODUCT).join(APP_EXE)
}

#[tauri::command]
fn installer_info(mode: Option<String>) -> serde_json::Value {
    let mode = mode.as_deref().unwrap_or("currentUser");
    let root = install_root_for_mode(mode);
    serde_json::json!({
        "product": PRODUCT,
        "version": VERSION,
        "defaultInstallPath": format!("{}\\{}", root, PRODUCT),
    })
}

#[tauri::command]
fn browse_install_path() -> Option<String> {
    rfd::FileDialog::new()
        .set_title("选择安装目录")
        .pick_folder()
        .map(|path| path.to_string_lossy().into_owned())
}

/// 以管理员权限（触发 UAC 提权）启动 payload，等待其结束，返回退出码。
#[cfg(windows)]
fn run_payload_elevated(temp: &std::path::Path, args: &[String]) -> Result<i32, String> {
    let mut verb: Vec<u16> = "runas\0".encode_utf16().collect();
    // 含空格的参数（如 /DIR=C:\Program Files\…）必须加引号，否则按空格截断
    let joined: String = args
        .iter()
        .map(|a| if a.contains(' ') { format!("\"{a}\"") } else { a.clone() })
        .collect::<Vec<_>>()
        .join(" ");
    let mut cmdline: Vec<u16> = joined.encode_utf16().collect();
    cmdline.push(0);
    let mut file: Vec<u16> = temp.as_os_str().encode_wide().collect();
    file.push(0);
    let mut dir: Vec<u16> = std::env::temp_dir().as_os_str().encode_wide().collect();
    dir.push(0);

    let mut sei: SHELLEXECUTEINFOW = unsafe { std::mem::zeroed() };
    sei.cbSize = std::mem::size_of::<SHELLEXECUTEINFOW>() as u32;
    sei.fMask = SEE_MASK_NOCLOSEPROCESS;
    sei.lpVerb = verb.as_mut_ptr();
    sei.lpFile = file.as_mut_ptr();
    sei.lpParameters = cmdline.as_mut_ptr();
    sei.lpDirectory = dir.as_mut_ptr();
    sei.nShow = 0; // SW_HIDE

    let ok = unsafe { ShellExecuteExW(&mut sei) };
    if ok == 0 {
        let err = std::io::Error::last_os_error();
        return Err(format!("请求管理员权限失败：{}", err));
    }
    let handle = sei.hProcess;
    if handle.is_null() {
        return Ok(-1);
    }
    let mut code: u32 = 0;
    unsafe {
        WaitForSingleObject(handle, 0xFFFFFFFF);
        GetExitCodeProcess(handle, &mut code);
        CloseHandle(handle);
    }
    Ok(code as i32)
}

#[tauri::command]
async fn install_payload(
    app: AppHandle,
    window: WebviewWindow,
    state: tauri::State<'_, InstallPath>,
    path: String,
    mode: String,
) -> Result<(), String> {
    if mode != "currentUser" && mode != "perMachine" {
        return Err("无效的安装范围".to_string());
    }
    let target = PathBuf::from(path.trim());
    if target.as_os_str().is_empty() {
        return Err("请选择安装目录".to_string());
    }
    // 不在此处创建目录：perMachine 需要提权，由提权后的 Inno 载荷创建；
    // currentUser 由 Inno 以当前用户权限创建（%LOCALAPPDATA% 可写）。
    *state.lock().map_err(|_| "安装状态不可用")? = Some((target.clone(), mode.clone()));

    let temp = std::env::temp_dir().join(format!("abk-installer-payload-{}.exe", std::process::id()));
    let mut file = File::create(&temp).map_err(|e| format!("无法准备安装文件：{e}"))?;
    file.write_all(PAYLOAD).map_err(|e| format!("无法写入安装文件：{e}"))?;
    drop(file);

    let emit = |percent: u8, label: &str, detail: &str| {
        let _ = window.emit("installer-progress", serde_json::json!({
            "percent": percent, "label": label, "detail": detail
        }));
    };
    emit(8, "准备安装", "正在检查安装目录…");
    let emit_log = |line: &str| {
        let _ = window.emit("installer-log", serde_json::json!({"line": line}));
    };
    emit_log("正在准备安装文件…");
    emit_log(&format!("安装目录：{}", target.display()));
    emit_log("正在解压安装程序…");

    let common_args = [
        "/VERYSILENT".to_string(),
        "/SUPPRESSMSGBOXES".to_string(),
        "/NORESTART".to_string(),
        (if mode == "perMachine" { "/ALLUSERS" } else { "/CURRENTUSER" }).to_string(),
        format!("/DIR={}", target.display()),
    ];

    let status_code: i32 = if mode == "perMachine" {
        // 所有用户：通过 runas 触发 UAC 提权，让 Inno 以管理员运行
        #[cfg(windows)]
        {
            emit_log("请求管理员权限（UAC）…");
            run_payload_elevated(&temp, &common_args)?
        }
        #[cfg(not(windows))]
        {
            let _ = common_args;
            -1
        }
    } else {
        let mut child = Command::new(&temp)
            .args(&common_args)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("无法启动安装程序：{e}"))?;

        let app1 = app.clone();
        if let Some(stdout) = child.stdout.take() {
            std::thread::spawn(move || {
                for line in BufReader::new(stdout).lines().map_while(Result::ok) {
                    let _ = app1.emit("installer-log", serde_json::json!({"line": line}));
                }
            });
        }
        let app2 = app.clone();
        if let Some(stderr) = child.stderr.take() {
            std::thread::spawn(move || {
                for line in BufReader::new(stderr).lines().map_while(Result::ok) {
                    let _ = app2.emit("installer-log", serde_json::json!({"line": line}));
                }
            });
        }
        child.wait()
            .map_err(|e| format!("安装进程错误：{e}"))?
            .code()
            .unwrap_or(-1)
    };

    let _ = fs::remove_file(&temp);
    if status_code != 0 {
        emit_log("安装失败：安装程序已退出");
        return Err(format!("安装程序退出，代码：{status_code}"));
    }
    emit_log("安装程序已成功完成");
    emit_log("正在更新快捷方式和系统信息…");

    emit(100, "安装完成", "正在准备启动应用…");
    let _ = window.emit("installer-done", ());
    Ok(())
}

#[tauri::command]
fn launch_installed_app(state: tauri::State<'_, InstallPath>, app: AppHandle) -> Result<(), String> {
    let (selected_path, mode) = state.lock().map_err(|_| "安装状态不可用")?.clone()
        .ok_or_else(|| "找不到安装信息".to_string())?;
    let default_exe = installed_exe_path(&mode);
    let selected_exe = selected_path.join(APP_EXE);
    let exe = [selected_exe, default_exe]
        .into_iter()
        .find(|candidate| candidate.exists())
        .ok_or_else(|| format!("找不到已安装的应用：{}", selected_path.display()))?;
    let mut cmd = Command::new(exe);
    #[cfg(windows)]
    cmd.creation_flags(DETACHED_PROCESS);
    cmd.spawn()
        .map_err(|e| format!("无法启动应用：{e}"))?;
    thread::sleep(Duration::from_millis(500));
    app.exit(0);
    Ok(())
}

#[tauri::command]
fn cancel_installer(app: AppHandle) {
    app.exit(0);
}

fn main() {
    // 默认以管理员运行：非管理员时通过 UAC 重启自身
    if !is_admin() {
        match relaunch_as_admin() {
            Ok(()) => return,
            Err(e) => {
                // 用户取消 UAC 或失败：仍以普通权限继续（可装当前用户目录）
                eprintln!("提权失败（以普通权限继续）：{e}");
            }
        }
    }
    let install_path: InstallPath = Arc::new(Mutex::new(None));
    tauri::Builder::default()
        .manage(install_path)
        .invoke_handler(tauri::generate_handler![
            installer_info,
            browse_install_path,
            install_payload,
            launch_installed_app,
            cancel_installer,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run installer");
}

/// 当前进程是否以管理员权限运行。
fn is_admin() -> bool {
    #[cfg(windows)]
    {
        use windows_sys::Win32::UI::Shell::IsUserAnAdmin;
        unsafe { IsUserAnAdmin() != 0 }
    }
    #[cfg(not(windows))]
    {
        true
    }
}

/// 通过 UAC 以管理员权限重启自身（runas 动词），成功返回 Ok(())。
/// 注意：被提权的新实例会再次进入 main()，此时 is_admin() 为真，继续正常流程。
#[cfg(windows)]
fn relaunch_as_admin() -> Result<(), String> {
    use std::os::windows::ffi::OsStrExt;

    let mut verb: Vec<u16> = "runas\0".encode_utf16().collect();
    // 以管理员权限重启自身
    let current = std::env::current_exe().map_err(|e| e.to_string())?;
    let mut file: Vec<u16> = current.as_os_str().encode_wide().collect();
    file.push(0);
    let mut dir: Vec<u16> = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .as_os_str()
        .encode_wide()
        .collect();
    dir.push(0);

    let mut sei: SHELLEXECUTEINFOW = unsafe { std::mem::zeroed() };
    sei.cbSize = std::mem::size_of::<SHELLEXECUTEINFOW>() as u32;
    sei.lpVerb = verb.as_mut_ptr();
    sei.lpFile = file.as_mut_ptr();
    sei.lpParameters = null_mut();
    sei.lpDirectory = dir.as_mut_ptr();
    sei.nShow = 1; // SW_NORMAL

    let ok = unsafe { ShellExecuteExW(&mut sei) };
    if ok == 0 {
        let err = std::io::Error::last_os_error();
        return Err(format!("请求管理员权限失败：{}", err));
    }
    Ok(())
}
