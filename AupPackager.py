#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AupPackager - Audacity 2.4.2 專案封包整理小精靈 (Project Consolidate & Packager)
ATGprjs MVlab 影音實驗室專屬工具
"""

import os
import sys
import shutil
import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import re

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

NS = 'http://audacity.sourceforge.net/xml/'
ET.register_namespace('', NS)

def qn(tag):
    return f'{{{NS}}}{tag}'

BANNER = r"""
================================================================================
   ___             ___             __                               
  /   | __  ______/ _ \____ ______/ /______ _____ ____  _____       
 / /| |/ / / / __  / //_/ __ `/ ___/ //_/ __ `/ __ `/ _ \/ ___/       
/ ___ / /_/ / /_/ /  / / /_/ / /__/ ,< / /_/ / /_/ /  __/ /           
\/  |_\__,_/\__,_/_/   \__,_/\___/_/|_|\__,_/\__, /\___/_/            
                                            /____/                    
  Audacity 2.4.2 專案封包整理小精靈 (MVlab 專業版)
================================================================================
"""

class AupPackager:
    def __init__(self, seven_zip_path=r"C:\scoop\shims\7z.exe"):
        self.seven_zip = seven_zip_path

    def consolidate(self, aup_file_path, move_files=False, compress_format=None, output_archive=None):
        aup_path = Path(aup_file_path).resolve()
        if not aup_path.exists() or aup_path.suffix.lower() != '.aup':
            print(f"[!] 錯誤：請提供正確的 Audacity 2.x 專案檔案 (.aup): {aup_file_path}")
            return None

        proj_dir = aup_path.parent
        media_dir = proj_dir / "media"
        media_dir.mkdir(exist_ok=True)

        print(f"[*] 正在分析專案結構: {aup_path.name}")
        
        with open(aup_path, 'r', encoding='utf-8', errors='replace') as f:
            xml_text = f.read()
        xml_text = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', xml_text)
        
        root = ET.fromstring(xml_text)
        tree = ET.ElementTree(root)

        alias_elements = []
        for elem in root.iter():
            if elem.tag == qn('pcmaliasblockfile') or elem.tag == 'pcmaliasblockfile':
                alias_elements.append(elem)

        print(f"[*] 找到 {len(alias_elements)} 個外部音訊區塊參照。")

        file_mapping = {}
        missing_files = []
        consolidated_count = 0

        for elem in alias_elements:
            raw_path = elem.get('aliasfile', '')
            if not raw_path:
                continue

            normalized_candidate = (proj_dir / raw_path).resolve()
            if normalized_candidate.exists():
                if normalized_candidate.parent == media_dir:
                    continue
                source_file = normalized_candidate
            else:
                source_file = Path(raw_path).resolve()

            if not source_file.exists():
                if raw_path not in missing_files:
                    missing_files.append(raw_path)
                continue

            dest_filename = source_file.name
            dest_path = media_dir / dest_filename

            counter = 1
            while dest_path.exists() and dest_path.resolve() != source_file.resolve() and dest_path.stat().st_size != source_file.stat().st_size:
                dest_filename = f"{source_file.stem}_{counter}{source_file.suffix}"
                dest_path = media_dir / dest_filename
                counter += 1

            if source_file.resolve() != dest_path.resolve() and not dest_path.exists():
                action_str = "移動" if move_files else "複製"
                print(f"    ├─ 正在{action_str}媒材: {source_file.name} ➔ media/")
                if move_files:
                    shutil.move(str(source_file), str(dest_path))
                else:
                    shutil.copy2(str(source_file), str(dest_path))
                consolidated_count += 1

            file_mapping[raw_path] = f"media/{dest_filename}"
            elem.set('aliasfile', f"media/{dest_filename}")

        if missing_files:
            print(f"[!] 警告：發現 {len(missing_files)} 個參照遺失的外部音檔：")
            for mf in missing_files:
                print(f"    - {mf}")

        bak_file = aup_path.with_suffix(".aup.bak")
        shutil.copy2(aup_path, bak_file)

        with open(aup_path, 'wb') as f:
            f.write(b'<?xml version="1.0" standalone="no" ?>\n')
            f.write(b'<!DOCTYPE project PUBLIC "-//audacityproject-1.3.0//DTD//EN" "http://audacity.sourceforge.net/xml/audacityproject-1.3.0.dtd" >\n')
            tree.write(f, encoding='utf-8', xml_declaration=False)

        print(f"[+] 專案統整完成！")
        print(f"    ├─ 備份檔案: {bak_file.name}")
        print(f"    ├─ 統整媒材數: {consolidated_count}")
        print(f"    └─ 媒材目錄: {media_dir}")

        if compress_format:
            fmt = compress_format.lower()
            if fmt not in ['7z', 'zip']:
                fmt = '7z'
            if not output_archive:
                output_archive = proj_dir.parent / f"{aup_path.stem}_package.{fmt}"
            else:
                output_archive = Path(output_archive)

            print(f"[*] 正在打包封裝專案至單一封包檔: {output_archive.name} ...")
            if os.path.exists(self.seven_zip):
                cmd = [
                    self.seven_zip, "a", "-t" + fmt,
                    str(output_archive),
                    str(aup_path),
                    str(media_dir)
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    print(f"[+] 專案封包打包成功: {output_archive} ({output_archive.stat().st_size / (1024*1024):.2f} MB)")
                else:
                    print(f"[!] 封包壓縮失敗: {res.stderr}")
            else:
                print(f"[!] 找不到 7z.exe ({self.seven_zip})，略過壓縮步驟。")

        return True

def main():
    print(BANNER)
    parser = argparse.ArgumentParser(description="Audacity 2.4.2 專案封包整理小精靈 (MVlab)")
    parser.add_argument("aup_path", nargs="?", help="Audacity 2.x 專案檔案路徑 (.aup)")
    parser.add_argument("--move", action="store_true", help="將外部音檔移動而非複製到 media/ (預設為複製)")
    parser.add_argument("--compress", choices=['7z', 'zip'], help="整理完成後自動壓縮成單一封包檔 (7z 或 zip)")
    parser.add_argument("--output", help="自訂壓縮檔輸出路徑")

    args = parser.parse_args()
    if not args.aup_path:
        print("[提示] 請傳入 .aup 專案路徑，例如：")
        print('    python AupPackager.py "C:\\路徑\\專案名稱.aup"')
        print("或直接使用 PowerShell 腳本拖曳執行。\n")
        return

    packager = AupPackager()
    packager.consolidate(args.aup_path, move_files=args.move, compress_format=args.compress, output_archive=args.output)

if __name__ == '__main__':
    main()
