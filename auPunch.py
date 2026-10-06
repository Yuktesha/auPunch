#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auPunch - Audacity 3.x ➔ 2.4.2++ 滾動流水線批次抽脂轉換器
“Punch your Audacity 3.x projects down to 2.4.2 & FLAC with zero hassle.”
“auPunch: Heavyweight project conversion, lightweight files.”
“一拳重擊 SQLite 肥胖怪獸，一鍵回歸 2.4.2 輕快殿堂！”

Part of ATGprjs MVlab Ecosystem
"""

import os
import sys
import time
import json
import shutil
import argparse
import subprocess
from pathlib import Path
import re

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from aup3_converter import Aup3Converter
from i18n import detect_language, get_text

BANNER = r"""
“Punch your Audacity 3.x projects down to Native Ardour DAW & FLAC with zero hassle.”
======================================================================
                     /PPPPPPP                                /hh      
                    | PP__  PP                              | hh      
  /aaaaaa  /uu   /uu| PP  \ PP /uu   /uu /nnnnnnn   /ccccccc| hhhhhhh 
 |____  aa| uu  | uu| PPPPPPP/| uu  | uu| nn__  nn /cc_____/| hh__  hh
  /aaaaaaa| uu  | uu| PP____/ | uu  | uu| nn  \ nn| cc      | hh  \ hh
 /aa__  aa| uu  | uu| PP      | uu  | uu| nn  | nn| cc      | hh  | hh
|  aaaaaaa|  uuuuuu/| PP      |  uuuuuu/| nn  | nn|  ccccccc| hh  | hh
 \_______/ \______/ |__/       \______/ |__/  |__/ \_______/|__/  |__/
======================================================================
“auPunch: Heavyweight project conversion, lightweight files.”
"""

def print_localized_help(lang=None):
    if lang is None:
        lang = detect_language()
    t = lambda k: get_text(k, lang)

    print(BANNER)
    print(f"{t('subtitle')}\n")
    print(f"{t('desc')}\n")
    print(f"📖 {t('usage')}:")
    print("    python auPunch.py [options]\n")
    print(f"⚙️  {t('options')}:")
    print(f"    -s, --source <path>     {t('opt_source')}")
    print(f"    -o, --output <dir>      {t('opt_output')}")
    print(f"    --wav                   {t('opt_wav')}")
    print(f"    --limit <N>             {t('opt_limit')}")
    print(f"    --edit                  {t('opt_edit')}")
    print(f"    -g, --gui, -G, --GUI    {t('opt_gui')}")
    print(f"    -h, --help, --?         {t('opt_help')}\n")
    print(f"💡 {t('examples')}:")
    print(f"    1. {t('ex1')}:")
    print('       python auPunch.py --source "C:\\MyProjects" --output "C:\\MyProjects_slim"\n')
    print(f"    2. {t('ex2')}:")
    print('       python auPunch.py --source "C:\\audacity_projects.7z" --output "C:\\slim_out"\n')
    print(f"    3. {t('ex3')}:")
    print('       python auPunch.py --source "C:\\MyProjects\\Song.aup3" --output "C:\\MyProjects_slim"\n')
    print(f"    4. {t('ex4')}:")
    print('       python auPunch.py --gui\n')
    print("-" * 70)
    print("A Solid GUI Studio X MVlab")

class AuPunchRunner:
    def __init__(self, source_path, output_dir, scratch_dir=None, seven_zip=r"C:\scoop\shims\7z.exe", use_wav=False):
        self.source_path = Path(source_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.use_wav = use_wav
        
        base_dir = Path(__file__).resolve().parent
        if scratch_dir is None:
            self.scratch_dir = base_dir / "_scratch"
        else:
            self.scratch_dir = Path(scratch_dir).resolve()
            
        self.seven_zip = str(seven_zip)
        self.converter = Aup3Converter()
        
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.is_archive = self.source_path.is_file() and self.source_path.suffix.lower() in ['.7z', '.zip']

    def scan_sources(self):
        projects = []
        if self.is_archive:
            print(f"[*] 正在掃描壓縮封包: {self.source_path.name} ...")
            cmd = [self.seven_zip, "l", "-sccUTF-8", str(self.source_path)]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+[.A-Za-z]+\s+(\d+)\s+(?:\d+\s+)?(.*\.aup3)$')
            for line in proc.stdout.splitlines():
                line_str = line.strip()
                m = pattern.match(line_str)
                if m:
                    size_int = int(m.group(1))
                    filename = m.group(2).strip()
                    projects.append({
                        "type": "archive",
                        "archive_name": filename,
                        "base_name": Path(filename).stem,
                        "size": size_int
                    })
        elif self.source_path.is_dir():
            print(f"[*] 正在掃描本機母體目錄: {self.source_path} ...")
            for f in self.source_path.glob("*.aup3"):
                if f.is_file():
                    projects.append({
                        "type": "local",
                        "path": f,
                        "base_name": f.stem,
                        "size": f.stat().st_size
                    })
            projects.sort(key=lambda x: x['base_name'])
        elif self.source_path.is_file() and self.source_path.suffix.lower() == '.aup3':
            projects.append({
                "type": "local",
                "path": self.source_path,
                "base_name": self.source_path.stem,
                "size": self.source_path.stat().st_size
            })
        else:
            raise FileNotFoundError(f"找不到指定的來源檔案或目錄: {self.source_path}")

        return projects

    def run(self, limit=None):
        print(BANNER)
        projects = self.scan_sources()
        total_count = len(projects)
        print(f"[+] 掃描完畢！共找到 {total_count} 個 Audacity 專案。")
        
        total_orig_bytes = sum(p['size'] for p in projects)
        audio_fmt_str = "標準未壓縮 WAV (最高相容性)" if self.use_wav else "預設無損高效 FLAC (極限壓縮，體積砍 70%~96%)"
        source_mode_str = f"7z 壓縮檔滾動串流 ({self.source_path.name})" if self.is_archive else f"本地母體目錄直接抽脂 ({self.source_path})"
        print(f"[+] 來源模式: {source_mode_str}")
        print(f"[+] 目標格式: 原生 Ardour DAW 會話工程 (.ardour)")
        print(f"[+] 專案總計未壓縮體積約: {total_orig_bytes / (1024**3):.2f} GB")
        print(f"[+] 音訊壓縮格式: {audio_fmt_str}")
        print(f"[+] 輸出目標目錄: {self.output_dir}")
        if self.is_archive:
            print(f"[+] 暫存緩衝區: {self.scratch_dir} (轉完單檔立即銷毀，零磁碟膨脹壓力)")
        print("-" * 80)

        if limit:
            projects = projects[:limit]
            print(f"[*] 限制模式：僅處理前 {limit} 個專案。\n")

        success_count = 0
        skipped_count = 0
        failed_count = 0
        
        total_saved_bytes = 0
        total_final_bytes = 0
        start_time = time.time()
        
        log_file = self.output_dir / "conversion_summary.json"
        history = {}
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                history = {}

        for idx, p in enumerate(projects, 1):
            base_name = p['base_name']
            orig_size_mb = p['size'] / (1024*1024)
            
            proj_out_dir = self.output_dir / base_name
            target_file = proj_out_dir / f"{base_name}.ardour"
            target_media = proj_out_dir / "interchange" / base_name / "audiofiles"
            
            if target_file.exists() and target_media.exists() and any(target_media.iterdir()):
                print(f"[{idx:03d}/{len(projects):03d}] ⏭️ [跳過 - 已存在] {base_name}")
                skipped_count += 1
                continue

            print(f"\n[{idx:03d}/{len(projects):03d}] 🥊 auPunch 正在重擊: {base_name} ({orig_size_mb:.1f} MB)")
            
            target_aup3_to_convert = None
            need_cleanup_scratch = False

            if p['type'] == 'archive':
                clean_scratch_file = self.scratch_dir / f"{base_name}.aup3"
                if clean_scratch_file.exists():
                    clean_scratch_file.unlink()

                print(f"    ├─ [1/3] 自 7z 提取單一專案至暫存區...")
                extract_cmd = [
                    self.seven_zip, "e", "-sccUTF-8",
                    str(self.source_path),
                    f"-o{self.scratch_dir}",
                    p['archive_name'],
                    "-y"
                ]
                t0 = time.time()
                ext_res = subprocess.run(extract_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                extracted_files = list(self.scratch_dir.glob("*.aup3"))
                if not extracted_files:
                    print(f"    └─ [!] 錯誤：解壓縮失敗: {ext_res.stderr or ext_res.stdout}")
                    failed_count += 1
                    continue
                    
                target_aup3_to_convert = extracted_files[0]
                need_cleanup_scratch = True
                ext_duration = time.time() - t0
                print(f"    ├─ 提取完成 (耗時 {ext_duration:.1f} 秒)")
            else:
                target_aup3_to_convert = p['path']

            fmt_label = "WAV" if self.use_wav else "FLAC"
            step_label = "2/3" if self.is_archive else "1/2"
            print(f"    ├─ [{step_label}] 執行抽脂並轉換至 Ardour DAW 會話工程 ({fmt_label})...")
            t1 = time.time()
            try:
                res = self.converter.convert(target_aup3_to_convert, self.output_dir, use_wav=self.use_wav)
                conv_duration = time.time() - t1
                
                saved_mb = res['saved_size'] / (1024*1024)
                final_mb = res['final_size'] / (1024*1024)
                total_saved_bytes += res['saved_size']
                total_final_bytes += res['final_size']
                
                print(f"    ├─ 🥊 重擊成功！(耗時 {conv_duration:.1f} 秒)")
                print(f"    ├─ 瘦身效益: {orig_size_mb:.1f} MB ➔ {final_mb:.1f} MB (砍掉 {saved_mb:.1f} MB，瘦身 -{res['saved_percent']}%)")
                
                history[base_name] = res
                success_count += 1
                
            except Exception as e:
                print(f"    ├─ [!] 轉換失敗: {e}")
                failed_count += 1
            finally:
                if need_cleanup_scratch:
                    print(f"    └─ [3/3] 銷毀暫存檔釋放空間... 完成")
                    for f in self.scratch_dir.glob("*"):
                        try:
                            if f.is_file():
                                f.unlink()
                            elif f.is_dir():
                                shutil.rmtree(f)
                        except Exception:
                            pass
                else:
                    print(f"    └─ [2/2] 專案儲存完畢。")

            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        total_duration = time.time() - start_time
        print("\n" + "=" * 80)
        print("🥊 auPunch 批次抽脂轉換流水線執行完畢！")
        print(f"    - 總計處理: {len(projects)} 個專案")
        print(f"    - 轉換成功: {success_count} 個")
        print(f"    - 略過已存在: {skipped_count} 個")
        print(f"    - 失敗/異常: {failed_count} 個")
        print(f"    - 累計瘦身節省空間: {total_saved_bytes / (1024**3):.2f} GB")
        print(f"    - 產出檔案總計大小: {total_final_bytes / (1024**3):.2f} GB")
        print(f"    - 總耗時: {total_duration / 60:.1f} 分鐘")
        print(f"    - 成果目錄: {self.output_dir}")
        print("=" * 80)

def main():
    # 1. 檢查是否無參數，或請求說明 (等同 --? 或 --help)
    help_flags = {'-h', '--help', '-?', '--?', '/?', '/h'}
    args_lower = [a.lower() for a in sys.argv[1:]]

    if len(sys.argv) == 1 or any(flag in args_lower for flag in help_flags):
        print_localized_help()
        sys.exit(0)

    # 2. 檢查是否啟動 GUI
    gui_flags = {'-g', '--gui', '-gui', '--g'}
    if any(flag in args_lower for flag in gui_flags):
        from gui import launch_gui
        # Extract optional default source/output if provided
        default_dir = r"C:\_Suno\Old_Suno\audacity project"
        default_out = r"C:\_Suno\Old_Suno\audacity_projects_slim"
        launch_gui(source=default_dir if os.path.exists(default_dir) else "", output=default_out)
        sys.exit(0)

    # 3. 命令列模式解析
    default_dir = r"C:\_Suno\Old_Suno\audacity project"
    default_7z = r"C:\_MyData\_Workfiles_\Download\Suno\audacity project.7z"
    if os.path.exists(default_dir):
        default_source = default_dir
        default_out = r"C:\_Suno\Old_Suno\audacity_projects_slim"
    else:
        default_source = default_7z
        default_out = r"C:\_MyData\_Workfiles_\Download\Suno\audacity_projects_slim"

    parser = argparse.ArgumentParser(description="auPunch: Punch your Audacity 3.x projects into Native Ardour DAW Sessions & FLAC (MVlab)", add_help=False)
    parser.add_argument("--source", "-s", default=default_source, help="Source path (.7z archive, directory containing .aup3 files, or single .aup3)")
    parser.add_argument("--output", "-o", default=default_out, help="Output destination directory")
    parser.add_argument("--scratch", default=None, help="Scratch directory for single file archive extraction")
    parser.add_argument("--wav", action="store_true", help="Output uncompressed WAV instead of default FLAC")
    parser.add_argument("--limit", type=int, help="Limit processing to first N projects")
    parser.add_argument("--edit", "-e", action="store_true", help="Automatically open project folder when finished")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch Graphical User Interface")

    args = parser.parse_args()
    runner = AuPunchRunner(args.source, args.output, scratch_dir=args.scratch, use_wav=args.wav)
    runner.run(limit=args.limit)

    if args.edit:
        print(f"\n[*] 正在開啟成果目錄: {args.output} ...")
        try:
            os.startfile(args.output)
        except Exception:
            pass

if __name__ == '__main__':
    main()
