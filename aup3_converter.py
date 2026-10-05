#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audacity AUP3 to 2.4.2++ Converter (AUP3 專案抽脂轉換器)
Part of ATGprjs MVlab Ecosystem
"""

import os
import sys
import shutil
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
        """
        aup3_path = Path(aup3_path).resolve()
        if not aup3_path.exists():
            raise FileNotFoundError(f"來源專案檔不存在: {aup3_path}")
            
        proj_base_name = aup3_path.stem
        orig_size = aup3_path.stat().st_size
        
        out_proj_dir = Path(output_dir) / proj_base_name
        out_media_dir = out_proj_dir / "media"
        out_aup_file = out_proj_dir / f"{proj_base_name}.aup"
        
        out_media_dir.mkdir(parents=True, exist_ok=True)
        
        temp_work_dir = out_proj_dir / "_temp_extract"
        if temp_work_dir.exists():
            shutil.rmtree(temp_work_dir)
        temp_work_dir.mkdir(parents=True, exist_ok=True)
        
        temp_aup3 = temp_work_dir / aup3_path.name
        shutil.copy2(aup3_path, temp_aup3)
        
        try:
            # 1. 導出專案 XML
            cmd_xml = [self.tool_path, "-extract_project", str(temp_aup3)]
            res_xml = subprocess.run(cmd_xml, cwd=str(temp_work_dir), capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            extracted_xml = temp_work_dir / f"{temp_aup3.name}.project.xml"
            if not extracted_xml.exists():
                raise RuntimeError(f"無法導出專案結構 XML: {res_xml.stderr or res_xml.stdout}")
                
            # 2. 導出立體聲 WAV
            cmd_audio = [self.tool_path, "-extract_as_stereo_track", str(temp_aup3)]
            res_audio = subprocess.run(cmd_audio, cwd=str(temp_work_dir), capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            temp_data_dir = temp_work_dir / f"{proj_base_name}_data"
            extracted_wav = temp_data_dir / "stereo.wav"
            
            if not extracted_wav.exists():
                cmd_mono = [self.tool_path, "-extract_as_mono_track", str(temp_aup3)]
                subprocess.run(cmd_mono, cwd=str(temp_work_dir), capture_output=True, text=True)
                extracted_wav = temp_data_dir / "mono.wav"
                
            if not extracted_wav.exists():
                raise RuntimeError(f"無法導出音軌檔案: {res_audio.stderr or res_audio.stdout}")
                
            # 3. 處理音檔儲存格式 (預設無損高效 FLAC，除非指定 use_wav)
            if not use_wav:
                dest_audio_name = f"{proj_base_name}.flac"
                final_audio_path = out_media_dir / dest_audio_name
                cmd_flac = [
                    self.ffmpeg_path, "-i", str(extracted_wav),
                    "-c:a", "flac", "-compression_level", "8",
                    str(final_audio_path), "-y"
                ]
                flac_res = subprocess.run(cmd_flac, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if not final_audio_path.exists():
                    dest_audio_name = f"{proj_base_name}.wav"
                    final_audio_path = out_media_dir / dest_audio_name
                    shutil.move(str(extracted_wav), str(final_audio_path))
            else:
                dest_audio_name = f"{proj_base_name}.wav"
                final_audio_path = out_media_dir / dest_audio_name
                shutil.move(str(extracted_wav), str(final_audio_path))
                
            media_rel_path = f"media/{dest_audio_name}"
            
            # 4. 改寫 XML 為 2.4.2++ 規格 (外部連結)
            self._transform_xml(extracted_xml, out_aup_file, proj_base_name, media_rel_path)
            
            final_aup_size = out_aup_file.stat().st_size
            final_audio_size = final_audio_path.stat().st_size
            final_total_size = final_aup_size + final_audio_size
            saved_size = orig_size - final_total_size
            saved_percent = (saved_size / orig_size * 100.0) if orig_size > 0 else 0.0
            
            return {
                "success": True,
                "project_name": proj_base_name,
                "aup_file": str(out_aup_file),
                "audio_file": str(final_audio_path),
                "format": "wav" if use_wav else "flac",
                "orig_size": orig_size,
                "final_size": final_total_size,
                "saved_size": saved_size,
                "saved_percent": round(saved_percent, 2)
            }
            
        finally:
            if temp_work_dir.exists():
                shutil.rmtree(temp_work_dir, ignore_errors=True)

    def _transform_xml(self, input_xml_path, output_aup_path, proj_name, media_rel_path):
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

        for track in root.findall(qn('wavetrack')):
            ch = track.get('channel', '0')
            track.set('linked', '1' if ch == '0' else '0')
            track.set('sampleformat', '262159')
            
            for c in list(track):
                if c.tag == qn('effects'):
                    track.remove(c)
                    
            for clip in track.findall(qn('waveclip')):
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
                    
                    for wb in list(seq.findall(qn('waveblock'))):
                        start = int(wb.get('start', '0'))
                        alias_len = min(max_samples, num_samples - start)
                        
                        wb.attrib.clear()
                        wb.set('start', str(start))
                        
                        alias_elem = ET.SubElement(wb, qn('pcmaliasblockfile'))
                        alias_elem.set('aliasfile', media_rel_path.replace('\\', '/'))
                        alias_elem.set('aliasstart', str(start))
                        alias_elem.set('aliaslen', str(alias_len))
                        alias_elem.set('aliaschannel', ch)

        with open(output_aup_path, 'wb') as f:
            f.write(b'<?xml version="1.0" standalone="no" ?>\n')
            f.write(b'<!DOCTYPE project PUBLIC "-//audacityproject-1.3.0//DTD//EN" "http://audacity.sourceforge.net/xml/audacityproject-1.3.0.dtd" >\n')
            tree.write(f, encoding='utf-8', xml_declaration=False)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python aup3_converter.py <path_to.aup3> <output_dir> [--flac]")
        sys.exit(1)
        
    use_flac_flag = "--flac" in sys.argv
    converter = Aup3Converter()
    stats = converter.convert(sys.argv[1], sys.argv[2], use_flac=use_flac_flag)
    print("轉換成果:", stats)
