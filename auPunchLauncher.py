#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auPunchLauncher - Audacity 智能前導啟動器 (Smart Project Dispatcher)
“Punch your Audacity 3.x projects down to 2.4.2 & FLAC with zero hassle.”

行為邏輯：
1. 若傳入 .aup (2.x 專案) ➔ 直接以 Audacity 前台開啟。
2. 若傳入 .aup3 (3.x 專案) ➔ 自動呼叫 auPunch 極速抽脂轉為 2.4.2++ (預設 FLAC)，完成後直接以前台開啟轉好之 .aup！
3. 若無參數 ➔ 直接啟動 Audacity 編輯器前台介面。

支援本機安裝版與可攜版 Audacity 自動智慧探測。
Part of ATGprjs MVlab Ecosystem
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from aup3_converter import Aup3Converter

BASE_DIR = Path(__file__).resolve().parent

def find_audacity_exe(custom_path=None):
    """
    智慧探測 Audacity 執行檔路徑：
    1. 自訂路徑 (若傳入且存在)
    2. 同層可攜版目錄 (AudacityPortable/audacity.exe 或 Audacity/audacity.exe)
    3. 系統標準安裝路徑 (Program Files, Program Files (x86), LocalAppData)
    4. 系統 PATH 環境變數 (audacity / audacity.exe)
    5. Windows 註冊表 App Paths
    """
    if custom_path:
        cp = Path(custom_path).resolve()
        if cp.is_file():
            return cp

    # 1. 檢查本工具伴隨的可攜版目錄
    portable_candidates = [
        BASE_DIR / "AudacityPortable" / "audacity.exe",
        BASE_DIR / "Audacity" / "audacity.exe",
    ]
    for c in portable_candidates:
        if c.is_file():
            return c

    # 2. 檢查 Windows 標準安裝位置
    if sys.platform == 'win32':
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local_app = os.environ.get("LOCALAPPDATA", "")

        sys_candidates = [
            Path(prog_files) / "Audacity" / "audacity.exe",
            Path(prog_files_x86) / "Audacity" / "audacity.exe",
        ]
        if local_app:
            sys_candidates.append(Path(local_app) / "Programs" / "Audacity" / "audacity.exe")

        for sc in sys_candidates:
            if sc.is_file():
                return sc

        # 3. 檢查 Windows Registry App Paths
        try:
            import winreg
            for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(root_key, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\audacity.exe") as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val and os.path.isfile(val):
                            return Path(val)
                except OSError:
                    pass
        except Exception:
            pass

    # 4. 檢查系統 PATH
    which_exe = shutil.which("audacity.exe") or shutil.which("audacity")
    if which_exe and os.path.isfile(which_exe):
        return Path(which_exe)

    # 5. macOS / Linux
    if sys.platform == 'darwin':
        mac_app = Path("/Applications/Audacity.app/Contents/MacOS/Audacity")
        if mac_app.is_file():
            return mac_app

    return None

def launch_audacity(project_file=None, custom_exe=None):
    """啟動 Audacity 編輯器前台視窗。"""
    audacity_exe = find_audacity_exe(custom_exe)
    if not audacity_exe:
        print("[!] 提示：系統中未偵測到 Audacity 編輯器 (已搜尋可攜版目錄及系統標準安裝路徑)。")
        print("    若需使用 Audacity 編輯專案，可至官網 (https://www.audacityteam.org/) 下載安裝，")
        print("    或在 auPunch 介面中指定 audacity.exe 所在路徑。")
        return False

    cmd = [str(audacity_exe)]
    if project_file:
        cmd.append(str(Path(project_file).resolve()))
        print(f"[*] 正在以前台視窗開啟專案: {Path(project_file).name} ...")
    else:
        print(f"[*] 正在以前台視窗開啟 Audacity ({audacity_exe.name}) ...")

    # 使用 Windows 分離進程啟動 GUI 視窗，確保主控台腳本正常退出
    if sys.platform == 'win32':
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, close_fds=True)
    else:
        subprocess.Popen(cmd)
    return True

def main():
    if len(sys.argv) < 2:
        # 無參數：直接開啟 Audacity
        launch_audacity()
        return

    target_path = Path(sys.argv[1]).resolve()
    if not target_path.exists():
        print(f"[!] 錯誤：指定檔案不存在: {target_path}")
        return

    suffix = target_path.suffix.lower()

    if suffix == '.aup':
        # 2.x 原生專案：直接開啟
        print(f"[+] 偵測到 Audacity 2.x 專案: {target_path.name}")
        launch_audacity(target_path)

    elif suffix == '.aup3':
        # 3.x 膨脹專案：自動抽脂並以 2.4.2 開啟
        print("====================================================================")
        print("   🥊 auPunch 智能前導轉換器")
        print("====================================================================")
        print(f"[*] 偵測到 Audacity 3.x 專案: {target_path.name} ({target_path.stat().st_size / (1024*1024):.1f} MB)")
        print("[*] 正在自動執行無損高效抽脂轉換 (預設 FLAC)...")

        out_dir = target_path.parent / f"{target_path.stem}_slim"
        converter = Aup3Converter()
        
        try:
            res = converter.convert(target_path, out_dir, use_wav=False)
            print("[+] 抽脂轉換成功！")
            print(f"    - 原大小: {res['orig_size'] / (1024*1024):.1f} MB")
            print(f"    - 瘦身後: {res['final_size'] / (1024*1024):.1f} MB (-{res['saved_percent']}%)")
            print(f"    - 專案檔: {res['aup_file']}")
            
            # 開啟轉好的 2.4.2 專案
            launch_audacity(res['aup_file'])
        except Exception as e:
            print(f"[!] 轉換失敗: {e}")
            sys.exit(1)
    else:
        # 其他音訊或檔案，直接交由 Audacity 開啟
        launch_audacity(target_path)

if __name__ == '__main__':
    main()
