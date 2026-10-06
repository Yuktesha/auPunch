#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audacity AUP3 to Ardour Session Converter (auPunch 次世代 DAW 轉檔核心)
Part of ATGprjs MVlab Ecosystem

“告別 Audacity 歷史包袱，直達 Ardour 專業 DAW 世界！”
- 提取 AUP3 專案結構與多軌獨立音訊片段 (Clips)
- 智慧還原立體聲對軌 (Stereo Pairs) 為原生雙聲道無損 FLAC 音軌
- 毫秒/樣本級精準對齊時間軸（包含 non-destructive 智慧裁剪手柄與起訖點）
- 完整轉移音量 (Gain)、聲相 (Pan)、靜音 (Mute)、獨奏 (Solo) 與音量包絡線 (<Envelope>)
- 輸出標準 Ardour 工程會話目錄：<ProjectName>/<ProjectName>.ardour + interchange/
"""

import os
import sys
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from typing import List, Dict, Any, Optional

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from ardour_exporter import ArdourExporter

NS = 'http://audacity.sourceforge.net/xml/'
ET.register_namespace('', NS)

def qn(tag):
    return f'{{{NS}}}{tag}'

def sanitize_filename(name: str) -> str:
    """清理檔名中的非合法字元"""
    s = re.sub(r'[\\/*?:"<>|]', '_', name).strip()
    return s if s else "audio"

class Aup3Converter:
    def __init__(self, tool_path=None, ffmpeg_path="ffmpeg"):
        if tool_path is None:
            base_dir = Path(__file__).resolve().parent
            tool_path = base_dir / "tools" / "audacity-project-tools-1.0.5-win64" / "bin" / "audacity-project-tools.exe"
        self.tool_path = str(tool_path)
        self.ffmpeg_path = ffmpeg_path
        if not os.path.exists(self.tool_path):
            raise FileNotFoundError(f"audacity-project-tools.exe not found at: {self.tool_path}")

    def convert(self, aup3_path, output_dir, use_wav=False, ardour_version=7002):
        """
        轉換 AUP3 專案檔為原生 Ardour DAW 會話工程目錄。
        """
        return self.convert_to_ardour(aup3_path, output_dir, use_wav=use_wav, ardour_version=ardour_version)

    def convert_to_ardour(self, aup3_path, output_dir, use_wav=False, ardour_version=7002):
        """
        將單一 .aup3 專案轉換為標準 Ardour Session 目錄：
        <output_dir>/<ProjectName>/
            <ProjectName>.ardour
            interchange/<ProjectName>/audiofiles/*.flac (or *.wav)
        """
        aup3_path = Path(aup3_path).resolve()
        if not aup3_path.exists():
            raise FileNotFoundError(f"來源專案檔不存在: {aup3_path}")

        proj_base_name = aup3_path.stem
        orig_size = aup3_path.stat().st_size

        out_proj_dir = Path(output_dir) / proj_base_name
        audiofiles_dir = out_proj_dir / "interchange" / proj_base_name / "audiofiles"
        audiofiles_dir.mkdir(parents=True, exist_ok=True)

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

            # 2. 優先嘗試導出各片段獨立音訊 (Clips 模式)
            cmd_clips = [self.tool_path, "-extract_clips", "proj.aup3"]
            subprocess.run(cmd_clips, cwd=str(temp_work_dir), capture_output=True, text=True, encoding='utf-8', errors='ignore')

            # 尋找 clips 目錄
            found_clip_dirs = list(temp_work_dir.glob("**/clips"))
            clips_dir = found_clip_dirs[0] if found_clip_dirs else (temp_work_dir / "clips")

            # 讀取並解析 Audacity 專案 XML
            with open(extracted_xml, 'r', encoding='utf-8', errors='replace') as f:
                xml_content = f.read()
            # 修正未逸出之 & 符號
            xml_content = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', xml_content)
            root = ET.fromstring(xml_content)

            sample_rate = int(root.get("rate", "44100"))
            raw_tracks = root.findall(qn("wavetrack"))

            # 建立磁碟上現有 clips 的索引映射: (track_idx, clip_idx) -> wav_path
            clip_disk_map = {}
            if clips_dir.exists():
                for wav_f in clips_dir.glob("*.wav"):
                    m = re.match(r'^(\d+)_(.*)_(\d+)_(.*)\.wav$', wav_f.name)
                    if m:
                        t_i = int(m.group(1))
                        c_i = int(m.group(3))
                        clip_disk_map[(t_i, c_i)] = wav_f

            has_extracted_clips = len(clip_disk_map) > 0
            final_audio_paths = []
            ardour_tracks = []
            total_clips_count = 0
            audio_ext = "wav" if use_wav else "flac"

            if has_extracted_clips:
                # ── 模式 A: 完整多軌片段對齊與合併 ──
                # 掃描並配對左右聲道立體聲音軌 (Stereo Pairs)
                t_idx = 0
                while t_idx < len(raw_tracks):
                    tr = raw_tracks[t_idx]
                    t_name = tr.get("name", f"Track {t_idx+1}")
                    ch = tr.get("channel", "0")
                    linked = tr.get("linked", "0")
                    gain = float(tr.get("gain", "1"))
                    pan = float(tr.get("pan", "0"))
                    mute = tr.get("mute", "false").lower() == "true"
                    solo = tr.get("solo", "false").lower() == "true"

                    is_stereo_pair = False
                    next_tr = raw_tracks[t_idx + 1] if t_idx + 1 < len(raw_tracks) else None
                    if next_tr is not None:
                        n_ch = next_tr.get("channel", "0")
                        n_name = next_tr.get("name")
                        if ch == "0" and n_ch == "1" and (n_name == t_name or linked in ["1", "3"]):
                            is_stereo_pair = True

                    clips_0 = tr.findall(qn("waveclip"))
                    clips_1 = next_tr.findall(qn("waveclip")) if is_stereo_pair else []

                    max_c = max(len(clips_0), len(clips_1)) if is_stereo_pair else len(clips_0)
                    track_clips = []

                    for c_idx in range(max_c):
                        clip_elem = clips_0[c_idx] if c_idx < len(clips_0) else clips_1[c_idx]
                        c_name = clip_elem.get("name", f"{t_name} {c_idx+1}")
                        offset = float(clip_elem.get("offset", "0"))
                        trim_l = float(clip_elem.get("trimLeft", "0"))
                        trim_r = float(clip_elem.get("trimRight", "0"))

                        # 取得 sequence sample 數
                        seq = clip_elem.find(qn("sequence"))
                        num_samples = int(seq.get("numsamples", "0")) if seq is not None else 0

                        # 片段在時間軸上的可見起始位置 (Audacity 3 裁剪手柄公式)
                        vis_start_sec = offset + trim_l
                        pos_samples = max(0, int(round(vis_start_sec * sample_rate)))

                        # 片段可見播放長度 (秒數與樣本數)
                        dur_orig_sec = (num_samples / sample_rate) if sample_rate else 0.0
                        dur_trimmed_sec = max(0.0, dur_orig_sec - trim_l - trim_r)
                        len_samples = int(round(dur_trimmed_sec * sample_rate))

                        # 解析包絡線 (Envelope)
                        env_elem = clip_elem.find(qn("envelope"))
                        env_points = []
                        if env_elem is not None:
                            for cp in env_elem.findall(qn("controlpoint")):
                                pt_t = float(cp.get("t", "0"))
                                pt_val = float(cp.get("val", "1"))
                                env_points.append((pt_t, pt_val))

                        # 準備輸出音檔
                        safe_clip_str = sanitize_filename(c_name)
                        dest_audio_name = f"{t_idx}_{c_idx}_{safe_clip_str}.{audio_ext}"
                        dest_audio_path = audiofiles_dir / dest_audio_name

                        wav_ch0 = clip_disk_map.get((t_idx, c_idx))
                        wav_ch1 = clip_disk_map.get((t_idx + 1, c_idx)) if is_stereo_pair else None

                        actual_channels = 1
                        actual_length_samples = len_samples

                        if is_stereo_pair and wav_ch0 and wav_ch1 and wav_ch0.exists() and wav_ch1.exists():
                            # 合併為標準雙聲道立體聲音訊
                            actual_channels = 2
                            if not use_wav:
                                cmd_merge = [
                                    self.ffmpeg_path,
                                    "-i", str(wav_ch0), "-i", str(wav_ch1),
                                    "-filter_complex", "[0:a][1:a]amerge=inputs=2[a]",
                                    "-map", "[a]",
                                    "-c:a", "flac", "-compression_level", "8",
                                    str(dest_audio_path), "-y"
                                ]
                            else:
                                cmd_merge = [
                                    self.ffmpeg_path,
                                    "-i", str(wav_ch0), "-i", str(wav_ch1),
                                    "-filter_complex", "[0:a][1:a]amerge=inputs=2[a]",
                                    "-map", "[a]",
                                    "-c:a", "pcm_s24le",
                                    str(dest_audio_path), "-y"
                                ]
                            subprocess.run(cmd_merge, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                        elif wav_ch0 and wav_ch0.exists():
                            # 單聲道音訊
                            actual_channels = 1
                            if not use_wav:
                                cmd_conv = [
                                    self.ffmpeg_path,
                                    "-i", str(wav_ch0),
                                    "-c:a", "flac", "-compression_level", "8",
                                    str(dest_audio_path), "-y"
                                ]
                            else:
                                cmd_conv = [
                                    self.ffmpeg_path,
                                    "-i", str(wav_ch0),
                                    "-c:a", "pcm_s24le",
                                    str(dest_audio_path), "-y"
                                ]
                            subprocess.run(cmd_conv, capture_output=True, text=True, encoding='utf-8', errors='ignore')

                        if dest_audio_path.exists():
                            final_audio_paths.append(dest_audio_path)
                            total_clips_count += 1

                            track_clips.append({
                                "name": c_name,
                                "audio_filename": dest_audio_name,
                                "channels": actual_channels,
                                "position": pos_samples,
                                "length": actual_length_samples,
                                "start": 0,
                                "envelope": env_points
                            })

                    ardour_tracks.append({
                        "name": t_name,
                        "channels": 2 if is_stereo_pair else 1,
                        "gain": gain,
                        "pan": pan,
                        "mute": mute,
                        "solo": solo,
                        "clips": track_clips
                    })

                    t_idx += 2 if is_stereo_pair else 1

            else:
                # ── 模式 B: 回退單一混音音軌導出 ──
                cmd_audio = [self.tool_path, "-extract_as_stereo_track", "proj.aup3"]
                res_audio = subprocess.run(cmd_audio, cwd=str(temp_work_dir), capture_output=True, text=True, encoding='utf-8', errors='ignore')

                temp_data_dir = temp_work_dir / "proj_data"
                extracted_wav = temp_data_dir / "stereo.wav"
                is_stereo = True

                if not extracted_wav.exists():
                    cmd_mono = [self.tool_path, "-extract_as_mono_track", "proj.aup3"]
                    subprocess.run(cmd_mono, cwd=str(temp_work_dir), capture_output=True, text=True)
                    extracted_wav = temp_data_dir / "mono.wav"
                    is_stereo = False

                if not extracted_wav.exists():
                    raise RuntimeError(f"無法導出音軌檔案: {res_audio.stderr or res_audio.stdout}")

                dest_audio_name = f"{proj_base_name}.{audio_ext}"
                final_audio_path = audiofiles_dir / dest_audio_name

                if not use_wav:
                    cmd_flac = [
                        self.ffmpeg_path, "-i", str(extracted_wav),
                        "-c:a", "flac", "-compression_level", "8",
                        str(final_audio_path), "-y"
                    ]
                    subprocess.run(cmd_flac, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                else:
                    shutil.move(str(extracted_wav), str(final_audio_path))

                final_audio_paths.append(final_audio_path)
                total_clips_count = 1

                # 估算總樣本長度
                stat_size = final_audio_path.stat().st_size
                dur_est_samples = sample_rate * 60 # 預設

                ardour_tracks.append({
                    "name": proj_base_name,
                    "channels": 2 if is_stereo else 1,
                    "gain": 1.0,
                    "pan": 0.0,
                    "mute": False,
                    "solo": False,
                    "clips": [
                        {
                            "name": proj_base_name,
                            "audio_filename": dest_audio_name,
                            "channels": 2 if is_stereo else 1,
                            "position": 0,
                            "length": dur_est_samples,
                            "start": 0,
                            "envelope": []
                        }
                    ]
                })

            # 3. 輸出 Ardour Session XML
            exporter = ArdourExporter(project_name=proj_base_name, sample_rate=sample_rate, ardour_version=ardour_version)
            out_ardour_file = exporter.export_session(output_dir=output_dir, tracks_data=ardour_tracks)

            # 4. 計算統計與壓縮率
            final_ardour_size = out_ardour_file.stat().st_size
            final_audio_size = sum(p.stat().st_size for p in final_audio_paths if p.exists())
            final_total_size = final_ardour_size + final_audio_size
            saved_size = orig_size - final_total_size
            saved_percent = (saved_size / orig_size * 100.0) if orig_size > 0 else 0.0

            return {
                "success": True,
                "project_name": proj_base_name,
                "target": "ardour",
                "ardour_version": ardour_version,
                "session_file": str(out_ardour_file),
                "ardour_file": str(out_ardour_file),
                "session_dir": str(out_proj_dir),
                "audio_files": [str(p) for p in final_audio_paths],
                "format": "wav" if use_wav else "flac",
                "sample_rate": sample_rate,
                "tracks_count": len(ardour_tracks),
                "clips_count": total_clips_count,
                "orig_size": orig_size,
                "final_size": final_total_size,
                "saved_size": saved_size,
                "saved_percent": round(saved_percent, 2)
            }

        finally:
            if temp_work_dir.exists():
                shutil.rmtree(temp_work_dir, ignore_errors=True)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python aup3_converter.py <path_to.aup3> <output_dir> [--wav] [--ardour-version {7002, 3002}]")
        sys.exit(1)

    use_wav_flag = "--wav" in sys.argv
    ardour_ver = 7002
    for arg in sys.argv:
        if arg in ["--legacy", "--3002"]:
            ardour_ver = 3002
        elif arg in ["--modern", "--7002", "--latest"]:
            ardour_ver = 7002

    converter = Aup3Converter()
    stats = converter.convert(sys.argv[1], sys.argv[2], use_wav=use_wav_flag, ardour_version=ardour_ver)
    print("轉換成果:", stats)
