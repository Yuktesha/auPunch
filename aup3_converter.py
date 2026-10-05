#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audacity AUP3 to 2.4.2++ Converter (AUP3 專案抽脂轉換器 - 次世代多軌與智慧手柄版)
Part of ATGprjs MVlab Ecosystem
“用 2.x 的分離式儲存策略，換取極致輕量；用 3.x 開啟，同時享有非破壞性裁剪手柄。”
"""

import os
import sys
import shutil
import subprocess
import tempfile
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

class Aup3Converter:
    def __init__(self, tool_path=None, ffmpeg_path="ffmpeg"):
        if tool_path is None:
            base_dir = Path(__file__).resolve().parent
            tool_path = base_dir / "tools" / "audacity-project-tools-1.0.5-win64" / "bin" / "audacity-project-tools.exe"
        self.tool_path = str(tool_path)
        self.ffmpeg_path = ffmpeg_path
        if not os.path.exists(self.tool_path):
            raise FileNotFoundError(f"audacity-project-tools.exe not found at: {self.tool_path}")

    def convert(self, aup3_path, output_dir, use_wav=False):
        """
        Convert a single .aup3 file into output_dir/<project_name>/
        Defaults to lossless FLAC for maximum compression unless use_wav is True.
        Preserves individual clips and 3.x non-destructive Smart Clip handles (trimLeft/trimRight).
        """
        aup3_path = Path(aup3_path).resolve()
        if not aup3_path.exists():
            raise FileNotFoundError(f"來源專案檔不存在: {aup3_path}")
            
        proj_base_name = aup3_path.stem
        orig_size = aup3_path.stat().st_size
        
        out_proj_dir = Path(output_dir) / proj_base_name
        out_media_dir = out_proj_dir / "media"
        out_data_dir = out_proj_dir / f"{proj_base_name}_data"
        out_aup_file = out_proj_dir / f"{proj_base_name}.aup"
        
        out_media_dir.mkdir(parents=True, exist_ok=True)
        out_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 避免 Windows 260 字元 MAX_PATH 限制，使用標準暫存目錄並以 proj.aup3 短路徑解包
        temp_work_dir = Path(tempfile.mkdtemp(prefix="aup_"))
        temp_aup3 = temp_work_dir / "proj.aup3"
        shutil.copy2(aup3_path, temp_aup3)
        
        try:
            # 1. 導出專案 XML 結構
            cmd_xml = [self.tool_path, "-extract_project", "proj.aup3"]
            res_xml = subprocess.run(cmd_xml, cwd=str(temp_work_dir), capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            extracted_xml = temp_work_dir / "proj.aup3.project.xml"
            if not extracted_xml.exists():
                raise RuntimeError(f"無法導出專案結構 XML: {res_xml.stderr or res_xml.stdout}")
                
            # 2. 優先嘗試導出各片段獨立音訊 (Clips 模式 - 保持各軌獨立與非破壞性手柄)
            cmd_clips = [self.tool_path, "-extract_clips", "proj.aup3"]
            subprocess.run(cmd_clips, cwd=str(temp_work_dir), capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            # 尋找 clips 目錄 (audacity-project-tools 預設置於 proj_data/clips)
            found_clip_dirs = list(temp_work_dir.glob("**/clips"))
            clips_dir = found_clip_dirs[0] if found_clip_dirs else (temp_work_dir / "clips")
            
            def clip_sort_key(f):
                m = re.match(r'^(\d+)_(.*)_(\d+)_(.*)\.wav$', f.name)
                if m:
                    return (int(m.group(1)), int(m.group(3)))
                return (999999, f.name)
                
            clip_wav_files = sorted(list(clips_dir.glob("*.wav")), key=clip_sort_key) if clips_dir.exists() else []
            
            final_audio_paths = []
            clips_count = 0
            
            if clip_wav_files:
                # ── 模式 A: 多片段獨立萃取 ──
                clip_media_map = {}
                for wav_f in clip_wav_files:
                    if not use_wav:
                        dest_audio_name = f"{wav_f.stem}.flac"
                        final_audio_path = out_media_dir / dest_audio_name
                        cmd_flac = [
                            self.ffmpeg_path, "-i", str(wav_f),
                            "-c:a", "flac", "-compression_level", "8",
                            str(final_audio_path), "-y"
                        ]
                        subprocess.run(cmd_flac, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                        if not final_audio_path.exists():
                            dest_audio_name = wav_f.name
                            final_audio_path = out_media_dir / dest_audio_name
                            shutil.move(str(wav_f), str(final_audio_path))
                    else:
                        dest_audio_name = wav_f.name
                        final_audio_path = out_media_dir / dest_audio_name
                        shutil.move(str(wav_f), str(final_audio_path))
                        
                    final_audio_paths.append(final_audio_path)
                    
                    # 建立精準的 (track_idx, clip_idx) 索引映射 (Audacity 要求 aliasfile 必須為絕對路徑)
                    m = re.match(r'^(\d+)_(.*)_(\d+)_(.*)\.wav$', wav_f.name)
                    abs_p = str(final_audio_path.resolve()).replace('\\', '/')
                    if m:
                        clip_media_map[(int(m.group(1)), int(m.group(3)))] = abs_p
                    clip_media_map[wav_f.name] = abs_p
                
                clips_count = len(clip_wav_files)
                self._transform_xml(extracted_xml, out_aup_file, proj_base_name, clip_media_map=clip_media_map)
            else:
                # ── 模式 B: 回退單一混音音軌導出 (適用於單軌專案或無法分解之專案) ──
                cmd_audio = [self.tool_path, "-extract_as_stereo_track", "proj.aup3"]
                res_audio = subprocess.run(cmd_audio, cwd=str(temp_work_dir), capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                temp_data_dir = temp_work_dir / "proj_data"
                extracted_wav = temp_data_dir / "stereo.wav"
                
                if not extracted_wav.exists():
                    cmd_mono = [self.tool_path, "-extract_as_mono_track", "proj.aup3"]
                    subprocess.run(cmd_mono, cwd=str(temp_work_dir), capture_output=True, text=True)
                    extracted_wav = temp_data_dir / "mono.wav"
                    
                if not extracted_wav.exists():
                    raise RuntimeError(f"無法導出音軌檔案: {res_audio.stderr or res_audio.stdout}")
                    
                if not use_wav:
                    dest_audio_name = f"{proj_base_name}.flac"
                    final_audio_path = out_media_dir / dest_audio_name
                    cmd_flac = [
                        self.ffmpeg_path, "-i", str(extracted_wav),
                        "-c:a", "flac", "-compression_level", "8",
                        str(final_audio_path), "-y"
                    ]
                    subprocess.run(cmd_flac, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    if not final_audio_path.exists():
                        dest_audio_name = f"{proj_base_name}.wav"
                        final_audio_path = out_media_dir / dest_audio_name
                        shutil.move(str(extracted_wav), str(final_audio_path))
                else:
                    dest_audio_name = f"{proj_base_name}.wav"
                    final_audio_path = out_media_dir / dest_audio_name
                    shutil.move(str(extracted_wav), str(final_audio_path))
                    
                final_audio_paths.append(final_audio_path)
                clips_count = 1
                abs_media_path = str(final_audio_path.resolve()).replace('\\', '/')
                self._transform_xml(extracted_xml, out_aup_file, proj_base_name, single_media_rel_path=abs_media_path)
            
            # 計算轉換後總容量
            final_aup_size = out_aup_file.stat().st_size
            final_audio_size = sum(p.stat().st_size for p in final_audio_paths if p.exists())
            final_total_size = final_aup_size + final_audio_size
            saved_size = orig_size - final_total_size
            saved_percent = (saved_size / orig_size * 100.0) if orig_size > 0 else 0.0
            
            return {
                "success": True,
                "project_name": proj_base_name,
                "aup_file": str(out_aup_file),
                "audio_files": [str(p) for p in final_audio_paths],
                "audio_file": str(final_audio_paths[0]) if final_audio_paths else "",
                "format": "wav" if use_wav else "flac",
                "orig_size": orig_size,
                "final_size": final_total_size,
                "saved_size": saved_size,
                "saved_percent": round(saved_percent, 2),
                "clips_count": clips_count
            }
            
        finally:
            if temp_work_dir.exists():
                shutil.rmtree(temp_work_dir, ignore_errors=True)

    def _transform_xml(self, input_xml_path, output_aup_path, proj_name, single_media_rel_path=None, clip_media_map=None):
        """
        改寫專案 XML 為 2.4.2++ 規格（外部音訊連結）。
        - 完整保留 trimLeft 與 trimRight 屬性（在 3.x 開啟時還原非破壞性智慧手柄）。
        - 保持軌道原始 linked 屬性（避免將獨立 Mono 軌道誤關聯為立體聲）。
        - 若提供 clip_media_map，每個 waveclip 獨立映射到專屬的 media 音檔。
        """
        with open(input_xml_path, 'r', encoding='utf-8', errors='replace') as f:
            xml_content = f.read()

        # 自動修正未逸出之 & 符號 (避免如 Sucaritá & Yuktesha 等名稱造成 XML 語法錯誤)
        xml_content = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', xml_content)
        
        root = ET.fromstring(xml_content)
        tree = ET.ElementTree(root)
        
        root.set('version', '1.3.0')
        root.set('audacityversion', '2.4.2')
        root.set('projname', f"{proj_name}_data")
        
        for child in list(root):
            if child.tag == qn('effects'):
                root.remove(child)

        clip_rel_paths = list(clip_media_map.values()) if clip_media_map else []
        clip_idx = 0

        for t_idx, track in enumerate(root.findall(qn('wavetrack'))):
            ch = track.get('channel', '0')
            orig_linked = track.get('linked', None)
            if orig_linked is None:
                track.set('linked', '1' if ch == '0' else '0')
            track.set('sampleformat', '262159')
            
            for c in list(track):
                if c.tag == qn('effects'):
                    track.remove(c)
                    
            for c_idx, clip in enumerate(track.findall(qn('waveclip'))):
                # 僅移除不相容的效果與色彩屬性，嚴格保留 trimLeft 與 trimRight（3.x 智慧手柄）
                for attr in ['centShift', 'pitchAndSpeedPreset', 'rawAudioTempo', 'clipStretchRatio', 'colorindex']:
                    if attr in clip.attrib:
                        del clip.attrib[attr]
                        
                seq = clip.find(qn('sequence'))
                if seq is not None:
                    max_samples = int(seq.get('maxsamples', '524288'))
                    num_samples = int(seq.get('numsamples', '0'))
                    seq.set('sampleformat', '262159')
                    if 'effectivesampleformat' in seq.attrib:
                        del seq.attrib['effectivesampleformat']
                    
                    # 決定此 Clip 指向的音訊檔案路徑 (優先依 (t_idx, c_idx) 精準對齊)
                    if clip_media_map and (t_idx, c_idx) in clip_media_map:
                        cur_media_rel = clip_media_map[(t_idx, c_idx)]
                        is_clip_isolated = True
                    elif clip_rel_paths and clip_idx < len(clip_rel_paths):
                        cur_media_rel = clip_rel_paths[clip_idx]
                        clip_idx += 1
                        is_clip_isolated = True
                    else:
                        cur_media_rel = single_media_rel_path or "media/audio.flac"
                        is_clip_isolated = False

                    for wb in list(seq.findall(qn('waveblock'))):
                        start = int(wb.get('start', '0'))
                        alias_len = min(max_samples, num_samples - start)
                        
                        wb.attrib.clear()
                        wb.set('start', str(start))
                        
                        alias_elem = ET.SubElement(wb, qn('pcmaliasblockfile'))
                        alias_elem.set('aliasfile', cur_media_rel.replace('\\', '/'))
                        alias_elem.set('aliasstart', str(start))
                        alias_elem.set('aliaslen', str(alias_len))
                        alias_elem.set('aliaschannel', '0' if is_clip_isolated else ch)

        with open(output_aup_path, 'wb') as f:
            f.write(b'<?xml version="1.0" standalone="no" ?>\n')
            f.write(b'<!DOCTYPE project PUBLIC "-//audacityproject-1.3.0//DTD//EN" "http://audacity.sourceforge.net/xml/audacityproject-1.3.0.dtd" >\n')
            tree.write(f, encoding='utf-8', xml_declaration=False)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python aup3_converter.py <path_to.aup3> <output_dir> [--wav]")
        sys.exit(1)
        
    use_wav_flag = "--wav" in sys.argv
    converter = Aup3Converter()
    stats = converter.convert(sys.argv[1], sys.argv[2], use_wav=use_wav_flag)
    print("轉換成果:", stats)
