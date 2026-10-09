# -*- coding: utf-8 -*-
"""有声书下载器安装向导。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_NAME = "有声书下载器"
APP_VERSION = "2.0.0"
EXE_NAME = "有声书下载器.exe"


def default_install_dir() -> str:
    local = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(local, "Programs", APP_NAME)


def source_dir() -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "app")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")


def create_shortcut(exe_path: str, work_dir: str) -> None:
    ps = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$sc = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\\{APP_NAME}.lnk'); "
        f"$sc.TargetPath = '{exe_path}'; "
        f"$sc.WorkingDirectory = '{work_dir}'; "
        f"$sc.IconLocation = '{exe_path},0'; "
        "$sc.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def do_install(target: str, make_shortcut: bool, progress=None) -> str | None:
    src = source_dir()
    if not os.path.isdir(src):
        return f"未找到程序数据目录：{src}"

    try:
        os.makedirs(target, exist_ok=True)
        entries = list(Path(src).iterdir())
        total = max(len(entries), 1)
        for index, entry in enumerate(entries, 1):
            destination = Path(target) / entry.name
            if entry.is_dir():
                shutil.copytree(entry, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(entry, destination)
            if progress:
                progress(index / total * 100, f"正在复制：{entry.name}")

        exe_path = os.path.join(target, EXE_NAME)
        if not os.path.isfile(exe_path):
            return f"安装后未找到主程序：{exe_path}"
        if make_shortcut:
            create_shortcut(exe_path, target)
        with open(os.path.join(target, "VERSION.txt"), "w", encoding="utf-8") as handle:
            handle.write(f"{APP_NAME} v{APP_VERSION}\n")
    except OSError as exc:
        return str(exc)
    return None


def run_silent() -> int:
    target = default_install_dir()
    error = do_install(target, True)
    if error:
        print(f"安装失败：{error}", file=sys.stderr)
        return 1
    print(f"安装完成: {target}")
    return 0


class InstallerWizard:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION} 安装")
        self.root.geometry("620x390")
        self.root.resizable(False, False)
        self.target = tk.StringVar(value=default_install_dir())
        self.make_shortcut = tk.BooleanVar(value=True)
        self.launch_after = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="准备安装")
        self.progress = tk.DoubleVar(value=0)
        self.pages: list[tk.Frame] = []
        self.current_page = 0
        self._build_pages()
        self._show_page(0)

    def _build_pages(self) -> None:
        self.container = ttk.Frame(self.root, padding=24)
        self.container.pack(fill="both", expand=True)
        self.page_welcome = ttk.Frame(self.container)
        ttk.Label(self.page_welcome, text=f"欢迎安装 {APP_NAME}", font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(20, 16))
        ttk.Label(
            self.page_welcome,
            text=f"版本 {APP_VERSION}\n\n安装向导将把程序安装到本机，并可创建桌面快捷方式。\n点击“下一步”继续。",
            justify="left",
        ).pack(anchor="w")

        self.page_path = ttk.Frame(self.container)
        ttk.Label(self.page_path, text="选择安装位置", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(12, 18))
        ttk.Label(self.page_path, text="请选择程序安装目录：").pack(anchor="w")
        path_row = ttk.Frame(self.page_path)
        path_row.pack(fill="x", pady=12)
        ttk.Entry(path_row, textvariable=self.target).pack(side="left", fill="x", expand=True)
        ttk.Button(path_row, text="浏览...", command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(self.page_path, text="创建桌面快捷方式", variable=self.make_shortcut).pack(anchor="w", pady=8)
        ttk.Label(self.page_path, text="已有同名文件时将覆盖更新程序文件。", foreground="#666").pack(anchor="w", pady=(12, 0))

        self.page_progress = ttk.Frame(self.container)
        ttk.Label(self.page_progress, text="正在安装", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(12, 18))
        ttk.Label(self.page_progress, textvariable=self.status).pack(anchor="w", pady=(10, 8))
        ttk.Progressbar(self.page_progress, variable=self.progress, maximum=100).pack(fill="x", pady=8)

        self.page_finish = ttk.Frame(self.container)
        ttk.Label(self.page_finish, text="安装完成", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(12, 18))
        ttk.Label(self.page_finish, text=f"{APP_NAME} 已成功安装到：").pack(anchor="w")
        ttk.Label(self.page_finish, textvariable=self.target, wraplength=550).pack(anchor="w", pady=(8, 18))
        ttk.Checkbutton(self.page_finish, text="立即启动程序", variable=self.launch_after).pack(anchor="w")

        self.pages = [self.page_welcome, self.page_path, self.page_progress, self.page_finish]
        footer = ttk.Frame(self.root, padding=(24, 10, 24, 18))
        footer.pack(fill="x")
        self.back_button = ttk.Button(footer, text="上一步", command=self._back)
        self.back_button.pack(side="left")
        self.next_button = ttk.Button(footer, text="下一步", command=self._next)
        self.next_button.pack(side="right")
        self.cancel_button = ttk.Button(footer, text="取消", command=self.root.destroy)
        self.cancel_button.pack(side="right", padx=(0, 8))

    def _show_page(self, index: int) -> None:
        for page in self.pages:
            page.pack_forget()
        self.pages[index].pack(fill="both", expand=True)
        self.current_page = index
        self.back_button.configure(state="normal" if index == 1 else "disabled")
        self.cancel_button.configure(state="disabled" if index >= 2 else "normal")
        self.next_button.configure(text="完成" if index == 3 else "下一步", state="normal")
        if index == 0:
            self.back_button.configure(state="disabled")
        if index == 2:
            self.next_button.configure(state="disabled")

    def _browse(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.target.get(), title="选择安装目录")
        if selected:
            self.target.set(selected)

    def _back(self) -> None:
        if self.current_page == 1:
            self._show_page(0)

    def _next(self) -> None:
        if self.current_page == 0:
            self._show_page(1)
        elif self.current_page == 1:
            if not self.target.get().strip():
                messagebox.showerror("安装错误", "请选择安装目录。")
                return
            self._start_install()
        elif self.current_page == 3:
            if self.launch_after.get():
                subprocess.Popen([os.path.join(self.target.get(), EXE_NAME)], cwd=self.target.get())
            self.root.destroy()

    def _start_install(self) -> None:
        self._show_page(2)
        self.root.after(100, self._install_worker)

    def _install_worker(self) -> None:
        def progress(value, text):
            self.root.after(0, lambda: (self.progress.set(value), self.status.set(text)))

        def worker():
            error = do_install(self.target.get(), self.make_shortcut.get(), progress)
            self.root.after(0, lambda: self._install_done(error))

        threading.Thread(target=worker, daemon=True).start()

    def _install_done(self, error: str | None) -> None:
        if error:
            messagebox.showerror("安装失败", error)
            self._show_page(1)
            return
        self.progress.set(100)
        self._show_page(3)


def main() -> int:
    if os.environ.get("LRTS_SETUP_SILENT") == "1":
        return run_silent()
    root = tk.Tk()
    try:
        ttk.Style(root).theme_use("vista")
    except tk.TclError:
        pass
    InstallerWizard(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
