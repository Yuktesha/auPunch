#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ardour Session Exporter (auPunch 次世代 Ardour 專案算繪核心)
Part of ATGprjs MVlab Ecosystem

將 Audacity 專案軌道、片段與音訊無縫轉換為原生 Ardour 專業 DAW 會話工程檔案（.ardour）。
支援：
- 完整時間軸 samplecnt_t 樣本級精準對齊（包含 clip offset 與 non-destructive 智慧裁剪手柄）
- 單聲道 (Mono) / 立體聲 (Stereo) 軌道與片段智能辨識及自動合併
- 完整標準 Ardour 目錄階層：<ProjectName>/<ProjectName>.ardour + interchange/<ProjectName>/audiofiles/
- 軌道音量 (Gain)、聲相 (Pan)、靜音 (Mute)、獨奏 (Solo) 完整對映
- 音量包絡線 (<Envelope>) 支援
- 無損高效 FLAC 壓縮音檔儲存
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

class IdGenerator:
    """Ardour 全域唯一 ID 計數器"""
    def __init__(self, start_id: int = 100):
        self.current = start_id

    def next_id(self) -> int:
        val = self.current
        self.current += 1
        return val


class ArdourExporter:
    def __init__(self, project_name: str, sample_rate: int = 48000, ardour_version: int = 7002):
        self.project_name = project_name
        self.sample_rate = sample_rate
        self.ardour_version = int(ardour_version)
        self.id_gen = IdGenerator(start_id=100)

    def generate_ardour_xml(self, tracks_data: List[Dict[str, Any]], session_end_samples: int = 0) -> str:
        """
        建立標準 Ardour Session XML 字串。
        tracks_data:
            [
                {
                    "name": "Vocal",
                    "channels": 2, # 1 or 2
                    "gain": 1.0,
                    "pan": 0.0, # -1.0 (L) ~ 1.0 (R)
                    "mute": False,
                    "solo": False,
                    "clips": [
                        {
                            "name": "Vocal 1",
                            "audio_filename": "Vocal_0.flac",
                            "channels": 2,
                            "position": 0, # samples
                            "length": 2959508, # samples
                            "start": 0, # samples
                            "envelope": [...] # optional list of (t_sec, val)
                        }
                    ]
                }
            ]
        """
        # 計算總工程樣本數長度
        max_end = session_end_samples
        for tr in tracks_data:
            for c in tr.get("clips", []):
                clip_end = c.get("position", 0) + c.get("length", 0)
                if clip_end > max_end:
                    max_end = clip_end

        # 根節點
        root = ET.Element("Session")
        root.set("version", str(self.ardour_version))
        root.set("name", self.project_name)
        root.set("sample-rate", str(self.sample_rate))
        root.set("end-is-free", "yes")
        root.set("event-counter", "1")
        root.set("vca-counter", "1")

        # ProgramVersion
        pv = ET.SubElement(root, "ProgramVersion")
        pv.set("created-with", "auPunch 1.0")
        pv.set("modified-with", "Ardour")

        # MIDIPorts
        midi_ports = ET.SubElement(root, "MIDIPorts")
        for p_name, p_dir in [
            ("MIDI Clock in", "input"), ("MIDI Clock out", "output"),
            ("MIDI control in", "input"), ("MIDI control out", "output"),
            ("MMC in", "input"), ("MMC out", "output"),
            ("MTC in", "input"), ("MTC out", "output"),
            ("Scene in", "input"), ("Scene out", "output"),
        ]:
            p = ET.SubElement(midi_ports, "Port")
            p.set("name", p_name)
            p.set("direction", p_dir)

        # Config
        config = ET.SubElement(root, "Config")
        config_opts = [
            ("destructive-xfade-msecs", "2"),
            ("use-region-fades", "1"),
            ("use-transport-fades", "1"),
            ("use-monitor-fades", "1"),
            ("native-file-data-format", "0"),
            ("native-file-header-format", "1"),
            ("auto-play", "0"),
            ("auto-return", "0"),
            ("auto-input", "1"),
            ("punch-in", "0"),
            ("punch-out", "0"),
            ("subframes-per-frame", "100"),
            ("timecode-format", "8"),
            ("raid-path", ""),
            ("audio-search-path", ""),
            ("midi-search-path", ""),
            ("track-name-number", "0"),
            ("track-name-take", "0"),
            ("take-name", "Take1"),
            ("jack-time-master", "1"),
            ("use-video-sync", "0"),
            ("video-pullup", "0"),
            ("external-sync", "0"),
            ("insert-merge-policy", "1"),
            ("timecode-offset", "0"),
            ("timecode-offset-negative", "1"),
            ("slave-timecode-offset", " 00:00:00:00"),
            ("timecode-generator-offset", " 00:00:00:00"),
            ("glue-new-markers-to-bars-and-beats", "0"),
            ("midi-copy-is-fork", "0"),
            ("glue-new-regions-to-bars-and-beats", "0"),
            ("realtime-export", "0"),
            ("use-video-file-fps", "0"),
            ("videotimeline-pullup", "1"),
            ("wave-amplitude-zoom", "0"),
            ("wave-zoom-factor", "2"),
            ("show-summary", "1"),
            ("show-group-tabs", "1"),
            ("show-region-fades", "1"),
            ("show-busses-on-meterbridge", "0"),
            ("show-master-on-meterbridge", "1"),
            ("show-midi-on-meterbridge", "1"),
            ("show-rec-on-meterbridge", "1"),
            ("show-mute-on-meterbridge", "0"),
            ("show-solo-on-meterbridge", "0"),
            ("show-monitor-on-meterbridge", "0"),
            ("show-name-on-meterbridge", "1"),
            ("meterbridge-label-height", "0"),
        ]
        for k, v in config_opts:
            opt = ET.SubElement(config, "Option")
            opt.set("name", k)
            opt.set("value", v)

        # Metadata
        ET.SubElement(root, "Metadata")

        # Sources
        sources_elem = ET.SubElement(root, "Sources")

        # 註冊所有音檔 Source
        # 音檔名稱 -> [source_id_ch0, source_id_ch1]
        file_to_source_ids = {}
        for tr in tracks_data:
            for c in tr.get("clips", []):
                af = c.get("audio_filename")
                n_chans = c.get("channels", 2)
                if af and af not in file_to_source_ids:
                    s_ids = []
                    for ch_idx in range(n_chans):
                        s_id = self.id_gen.next_id()
                        s_ids.append(s_id)
                        s_node = ET.SubElement(sources_elem, "Source")
                        s_node.set("id", str(s_id))
                        s_node.set("name", af)
                        s_node.set("type", "audio")
                        s_node.set("flags", "0")
                        s_node.set("channel", str(ch_idx))
                    file_to_source_ids[af] = s_ids

        # Regions (全域未放入軌道之片段放此，這裡保持乾淨為空容器)
        ET.SubElement(root, "Regions")

        # Locations (工程起訖範圍)
        locations_elem = ET.SubElement(root, "Locations")
        loc = ET.SubElement(locations_elem, "Location")
        loc.set("id", str(self.id_gen.next_id()))
        loc.set("name", "session")
        loc.set("start", "0")
        loc.set("end", str(max_end))
        loc.set("flags", "IsSessionRange")
        loc.set("locked", "no")
        loc.set("position-lock-style", "AudioTime")

        # Bundles & VCAManager
        ET.SubElement(root, "Bundles")
        ET.SubElement(root, "VCAManager")

        # Routes (Master Bus + 各音軌)
        routes_elem = ET.SubElement(root, "Routes")

        # ── 1. Master Bus ──
        master_id = self.id_gen.next_id()
        master_route = ET.SubElement(routes_elem, "Route")
        master_route.set("id", str(master_id))
        master_route.set("name", "Master")
        master_route.set("default-type", "audio")
        master_route.set("strict-io", "0")
        master_route.set("active", "yes")
        master_route.set("denormal-protection", "no")
        master_route.set("meter-point", "MeterPostFader")
        master_route.set("meter-type", "MeterK20")

        pres = ET.SubElement(master_route, "PresentationInfo")
        pres.set("order", "0")
        pres.set("flags", "MasterOut")
        pres.set("color", "3303371519")

        c_solo = ET.SubElement(master_route, "Controllable")
        c_solo.set("name", "solo")
        c_solo.set("id", str(self.id_gen.next_id()))
        c_solo.set("flags", "Toggle,RealTime")
        c_solo.set("value", "0.000000000000")
        c_solo.set("self-solo", "no")
        c_solo.set("soloed-by-upstream", "0")
        c_solo.set("soloed-by-downstream", "0")

        c_iso = ET.SubElement(master_route, "Controllable")
        c_iso.set("name", "solo-iso")
        c_iso.set("id", str(self.id_gen.next_id()))
        c_iso.set("flags", "Toggle,RealTime")
        c_iso.set("value", "0.000000000000")
        c_iso.set("solo-isolated", "no")

        c_safe = ET.SubElement(master_route, "Controllable")
        c_safe.set("name", "solo-safe")
        c_safe.set("id", str(self.id_gen.next_id()))
        c_safe.set("flags", "Toggle")
        c_safe.set("value", "0.000000000000")
        c_safe.set("solo-safe", "no")

        # Master Input IO (各音軌輸出匯入此處)
        m_in_io = ET.SubElement(master_route, "IO")
        m_in_io.set("name", "Master")
        m_in_io.set("id", str(self.id_gen.next_id()))
        m_in_io.set("direction", "Input")
        m_in_io.set("default-type", "audio")
        m_in_io.set("user-latency", "0")

        m_in_p1 = ET.SubElement(m_in_io, "Port")
        m_in_p1.set("type", "audio")
        m_in_p1.set("name", "Master/audio_in 1")

        m_in_p2 = ET.SubElement(m_in_io, "Port")
        m_in_p2.set("type", "audio")
        m_in_p2.set("name", "Master/audio_in 2")

        # Master Output IO (輸出至系統播放設備)
        m_out_io = ET.SubElement(master_route, "IO")
        m_out_io.set("name", "Master")
        m_out_io.set("id", str(self.id_gen.next_id()))
        m_out_io.set("direction", "Output")
        m_out_io.set("default-type", "audio")
        m_out_io.set("user-latency", "0")

        m_out_p1 = ET.SubElement(m_out_io, "Port")
        m_out_p1.set("type", "audio")
        m_out_p1.set("name", "Master/audio_out 1")
        conn1 = ET.SubElement(m_out_p1, "Connection")
        conn1.set("other", "system:playback_1")

        m_out_p2 = ET.SubElement(m_out_io, "Port")
        m_out_p2.set("type", "audio")
        m_out_p2.set("name", "Master/audio_out 2")
        conn2 = ET.SubElement(m_out_p2, "Connection")
        conn2.set("other", "system:playback_2")

        mm = ET.SubElement(master_route, "MuteMaster")
        mm.set("mute-point", "PostFader,Listen,Main")
        mm.set("muted", "no")

        c_mute = ET.SubElement(master_route, "Controllable")
        c_mute.set("name", "mute")
        c_mute.set("id", str(self.id_gen.next_id()))
        c_mute.set("flags", "Toggle,RealTime")
        c_mute.set("value", "0.000000000000")

        c_phase = ET.SubElement(master_route, "Controllable")
        c_phase.set("name", "phase")
        c_phase.set("id", str(self.id_gen.next_id()))
        c_phase.set("flags", "Toggle")
        c_phase.set("value", "0.000000000000")
        c_phase.set("phase-invert", "00")

        # Master Pannable
        pan_node = ET.SubElement(master_route, "Pannable")
        p_az = ET.SubElement(pan_node, "Controllable")
        p_az.set("name", "pan-azimuth")
        p_az.set("id", str(self.id_gen.next_id()))
        p_az.set("flags", "")
        p_az.set("value", "0.500000000000")

        p_w = ET.SubElement(pan_node, "Controllable")
        p_w.set("name", "pan-width")
        p_w.set("id", str(self.id_gen.next_id()))
        p_w.set("flags", "")
        p_w.set("value", "1.000000000000")

        p_el = ET.SubElement(pan_node, "Controllable")
        p_el.set("name", "pan-elevation")
        p_el.set("id", str(self.id_gen.next_id()))
        p_el.set("flags", "")
        p_el.set("value", "0.000000000000")

        p_fb = ET.SubElement(pan_node, "Controllable")
        p_fb.set("name", "pan-frontback")
        p_fb.set("id", str(self.id_gen.next_id()))
        p_fb.set("flags", "")
        p_fb.set("value", "0.000000000000")

        p_lfe = ET.SubElement(pan_node, "Controllable")
        p_lfe.set("name", "pan-lfe")
        p_lfe.set("id", str(self.id_gen.next_id()))
        p_lfe.set("flags", "")
        p_lfe.set("value", "0.000000000000")
        ET.SubElement(pan_node, "Automation")

        # Master Processors (Trim, Meter, Amp, Main-Outs)
        proc_trim = ET.SubElement(master_route, "Processor")
        proc_trim.set("id", str(self.id_gen.next_id()))
        proc_trim.set("name", "Amp")
        proc_trim.set("active", "yes")
        proc_trim.set("user-latency", "0")
        proc_trim.set("type", "trim")
        c_trim = ET.SubElement(proc_trim, "Controllable")
        c_trim.set("name", "trimcontrol")
        c_trim.set("id", str(self.id_gen.next_id()))
        c_trim.set("flags", "")
        c_trim.set("value", "1.000000000000")

        proc_amp = ET.SubElement(master_route, "Processor")
        proc_amp.set("id", str(self.id_gen.next_id()))
        proc_amp.set("name", "Amp")
        proc_amp.set("active", "yes")
        proc_amp.set("user-latency", "0")
        proc_amp.set("type", "amp")
        c_gain = ET.SubElement(proc_amp, "Controllable")
        c_gain.set("name", "gaincontrol")
        c_gain.set("id", str(self.id_gen.next_id()))
        c_gain.set("flags", "")
        c_gain.set("value", "1.000000000000")

        proc_meter = ET.SubElement(master_route, "Processor")
        proc_meter.set("id", str(self.id_gen.next_id()))
        proc_meter.set("name", "meter-Master")
        proc_meter.set("active", "yes")
        proc_meter.set("user-latency", "0")
        proc_meter.set("type", "meter")

        proc_main = ET.SubElement(master_route, "Processor")
        proc_main.set("id", str(self.id_gen.next_id()))
        proc_main.set("name", "Master")
        proc_main.set("active", "yes")
        proc_main.set("user-latency", "0")
        proc_main.set("own-input", "yes")
        proc_main.set("own-output", "no")
        proc_main.set("output", "Master")
        proc_main.set("type", "main-outs")
        proc_main.set("role", "Main")
        ET.SubElement(proc_main, "PannerShell", bypassed="no", user_panner="", linked_to_route="yes")
        # 主輸出亦包含 Panning
        proc_main.append(pan_node)

        ET.SubElement(master_route, "Slavable")

        # ── 2. 各音軌 (Audio Tracks) ──
        playlists_elem = ET.SubElement(root, "Playlists")
        
        # 軌道色票 (自動輪替美觀配色)
        palette = [
            "3672483583", "3229019391", "2188568063", "3849498623",
            "2863311615", "4152336383", "1932735231", "3435973887"
        ]

        for tr_idx, tr in enumerate(tracks_data, 1):
            t_name = tr.get("name", f"Track {tr_idx}")
            t_chans = tr.get("channels", 2)
            t_gain = float(tr.get("gain", 1.0))
            t_pan = float(tr.get("pan", 0.0)) # -1.0 ~ 1.0
            # 轉換為 Ardour pan-azimuth: 0.0 (L) ~ 1.0 (R), 0.5 為中間
            t_pan_azimuth = max(0.0, min(1.0, (t_pan + 1.0) / 2.0))
            t_mute = tr.get("mute", False)
            t_solo = tr.get("solo", False)
            clips = tr.get("clips", [])

            route_id = self.id_gen.next_id()
            playlist_id = self.id_gen.next_id()
            diskstream_id = self.id_gen.next_id()
            playlist_name = f"{t_name}.1"

            tr_route = ET.SubElement(routes_elem, "Route")
            tr_route.set("id", str(route_id))
            tr_route.set("name", t_name)
            tr_route.set("default-type", "audio")
            tr_route.set("strict-io", "1")
            tr_route.set("active", "yes")
            tr_route.set("denormal-protection", "no")
            tr_route.set("meter-point", "MeterInput")
            tr_route.set("meter-type", "MeterPeak")
            tr_route.set("saved-meter-point", "MeterPostFader")
            tr_route.set("mode", "Normal")

            pres_tr = ET.SubElement(tr_route, "PresentationInfo")
            pres_tr.set("order", str(tr_idx))
            pres_tr.set("flags", "AudioTrack,OrderSet")
            pres_tr.set("color", palette[(tr_idx - 1) % len(palette)])

            # Solo controls
            c_s = ET.SubElement(tr_route, "Controllable")
            c_s.set("name", "solo")
            c_s.set("id", str(self.id_gen.next_id()))
            c_s.set("flags", "Toggle,RealTime")
            c_s.set("value", "1.000000000000" if t_solo else "0.000000000000")
            c_s.set("self-solo", "no")
            c_s.set("soloed-by-upstream", "0")
            c_s.set("soloed-by-downstream", "0")

            c_si = ET.SubElement(tr_route, "Controllable")
            c_si.set("name", "solo-iso")
            c_si.set("id", str(self.id_gen.next_id()))
            c_si.set("flags", "Toggle,RealTime")
            c_si.set("value", "0.000000000000")
            c_si.set("solo-isolated", "no")

            c_ss = ET.SubElement(tr_route, "Controllable")
            c_ss.set("name", "solo-safe")
            c_ss.set("id", str(self.id_gen.next_id()))
            c_ss.set("flags", "Toggle")
            c_ss.set("value", "0.000000000000")
            c_ss.set("solo-safe", "no")

            # Input IO
            tr_in_io = ET.SubElement(tr_route, "IO")
            tr_in_io.set("name", t_name)
            tr_in_io.set("id", str(self.id_gen.next_id()))
            tr_in_io.set("direction", "Input")
            tr_in_io.set("default-type", "audio")
            tr_in_io.set("user-latency", "0")
            for ch in range(1, t_chans + 1):
                p_in = ET.SubElement(tr_in_io, "Port")
                p_in.set("type", "audio")
                p_in.set("name", f"{t_name}/audio_in {ch}")

            # Output IO (連接至 Master)
            tr_out_io = ET.SubElement(tr_route, "IO")
            tr_out_io.set("name", t_name)
            tr_out_io.set("id", str(self.id_gen.next_id()))
            tr_out_io.set("direction", "Output")
            tr_out_io.set("default-type", "audio")
            tr_out_io.set("user-latency", "0")

            p_out1 = ET.SubElement(tr_out_io, "Port")
            p_out1.set("type", "audio")
            p_out1.set("name", f"{t_name}/audio_out 1")
            c_m1 = ET.SubElement(p_out1, "Connection")
            c_m1.set("other", "Master/audio_in 1")

            p_out2 = ET.SubElement(tr_out_io, "Port")
            p_out2.set("type", "audio")
            p_out2.set("name", f"{t_name}/audio_out 2")
            c_m2 = ET.SubElement(p_out2, "Connection")
            c_m2.set("other", "Master/audio_in 2")

            # Mute
            mm_tr = ET.SubElement(tr_route, "MuteMaster")
            mm_tr.set("mute-point", "PostFader,Listen,Main")
            mm_tr.set("muted", "yes" if t_mute else "no")

            c_tmute = ET.SubElement(tr_route, "Controllable")
            c_tmute.set("name", "mute")
            c_tmute.set("id", str(self.id_gen.next_id()))
            c_tmute.set("flags", "Toggle,RealTime")
            c_tmute.set("value", "1.000000000000" if t_mute else "0.000000000000")

            c_tphase = ET.SubElement(tr_route, "Controllable")
            c_tphase.set("name", "phase")
            c_tphase.set("id", str(self.id_gen.next_id()))
            c_tphase.set("flags", "Toggle")
            c_tphase.set("value", "0.000000000000")
            c_tphase.set("phase-invert", "0" if t_chans == 1 else "00")

            # Panning
            pan_tr = ET.SubElement(tr_route, "Pannable")
            p_taz = ET.SubElement(pan_tr, "Controllable")
            p_taz.set("name", "pan-azimuth")
            p_taz.set("id", str(self.id_gen.next_id()))
            p_taz.set("flags", "")
            p_taz.set("value", f"{t_pan_azimuth:.12f}")

            p_tw = ET.SubElement(pan_tr, "Controllable")
            p_tw.set("name", "pan-width")
            p_tw.set("id", str(self.id_gen.next_id()))
            p_tw.set("flags", "")
            p_tw.set("value", "1.000000000000" if t_chans == 2 else "0.000000000000")

            p_tel = ET.SubElement(pan_tr, "Controllable")
            p_tel.set("name", "pan-elevation")
            p_tel.set("id", str(self.id_gen.next_id()))
            p_tel.set("flags", "")
            p_tel.set("value", "0.000000000000")

            p_tfb = ET.SubElement(pan_tr, "Controllable")
            p_tfb.set("name", "pan-frontback")
            p_tfb.set("id", str(self.id_gen.next_id()))
            p_tfb.set("flags", "")
            p_tfb.set("value", "0.000000000000")

            p_tlfe = ET.SubElement(pan_tr, "Controllable")
            p_tlfe.set("name", "pan-lfe")
            p_tlfe.set("id", str(self.id_gen.next_id()))
            p_tlfe.set("flags", "")
            p_tlfe.set("value", "0.000000000000")
            ET.SubElement(pan_tr, "Automation")

            # Processors (Trim, Meter, Amp, Main-Outs)
            proc_ttrim = ET.SubElement(tr_route, "Processor")
            proc_ttrim.set("id", str(self.id_gen.next_id()))
            proc_ttrim.set("name", "Amp")
            proc_ttrim.set("active", "yes")
            proc_ttrim.set("user-latency", "0")
            proc_ttrim.set("type", "trim")
            c_ttrim = ET.SubElement(proc_ttrim, "Controllable")
            c_ttrim.set("name", "trimcontrol")
            c_ttrim.set("id", str(self.id_gen.next_id()))
            c_ttrim.set("flags", "")
            c_ttrim.set("value", "1.000000000000")

            proc_tmeter = ET.SubElement(tr_route, "Processor")
            proc_tmeter.set("id", str(self.id_gen.next_id()))
            proc_tmeter.set("name", f"meter-{t_name}")
            proc_tmeter.set("active", "yes")
            proc_tmeter.set("user-latency", "0")
            proc_tmeter.set("type", "meter")

            proc_tamp = ET.SubElement(tr_route, "Processor")
            proc_tamp.set("id", str(self.id_gen.next_id()))
            proc_tamp.set("name", "Amp")
            proc_tamp.set("active", "yes")
            proc_tamp.set("user-latency", "0")
            proc_tamp.set("type", "amp")
            c_tgain = ET.SubElement(proc_tamp, "Controllable")
            c_tgain.set("name", "gaincontrol")
            c_tgain.set("id", str(self.id_gen.next_id()))
            c_tgain.set("flags", "")
            c_tgain.set("value", f"{t_gain:.12f}")

            proc_tmain = ET.SubElement(tr_route, "Processor")
            proc_tmain.set("id", str(self.id_gen.next_id()))
            proc_tmain.set("name", t_name)
            proc_tmain.set("active", "yes")
            proc_tmain.set("user-latency", "0")
            proc_tmain.set("own-input", "yes")
            proc_tmain.set("own-output", "no")
            proc_tmain.set("output", t_name)
            proc_tmain.set("type", "main-outs")
            proc_tmain.set("role", "Main")
            ET.SubElement(proc_tmain, "PannerShell", bypassed="no", user_panner="", linked_to_route="yes")
            proc_tmain.append(pan_tr)

            ET.SubElement(tr_route, "Slavable")

            c_mon = ET.SubElement(tr_route, "Controllable")
            c_mon.set("name", "monitoring")
            c_mon.set("id", str(self.id_gen.next_id()))
            c_mon.set("flags", "RealTime")
            c_mon.set("value", "0.000000000000")
            c_mon.set("monitoring", "")

            c_rs = ET.SubElement(tr_route, "Controllable")
            c_rs.set("name", "recsafe")
            c_rs.set("id", str(self.id_gen.next_id()))
            c_rs.set("flags", "Toggle,RealTime")
            c_rs.set("value", "0.000000000000")

            c_re = ET.SubElement(tr_route, "Controllable")
            c_re.set("name", "recenable")
            c_re.set("id", str(self.id_gen.next_id()))
            c_re.set("flags", "Toggle,RealTime")
            c_re.set("value", "0.000000000000")

            # Diskstream
            ds = ET.SubElement(tr_route, "Diskstream")
            ds.set("flags", "Recordable")
            ds.set("playlist", playlist_name)
            ds.set("name", t_name)
            ds.set("id", str(diskstream_id))
            ds.set("speed", "1.000000")
            ds.set("capture-alignment", "Automatic")
            ds.set("record-safe", "no")
            ds.set("channels", str(t_chans))

            # ── 3. Playlist 與 Clips (Regions) ──
            pl = ET.SubElement(playlists_elem, "Playlist")
            pl.set("id", str(playlist_id))
            pl.set("name", playlist_name)
            pl.set("type", "audio")
            pl.set("orig-track-id", str(route_id))
            pl.set("frozen", "no")

            for c_idx, c in enumerate(clips):
                c_name = c.get("name", f"{t_name} {c_idx+1}")
                af = c.get("audio_filename")
                s_ids = file_to_source_ids.get(af, [])
                c_chans = c.get("channels", 2)
                pos = int(c.get("position", 0))
                length = int(c.get("length", 0))
                start = int(c.get("start", 0))

                reg_id = self.id_gen.next_id()
                reg = ET.SubElement(pl, "Region")
                reg.set("id", str(reg_id))
                reg.set("name", c_name)
                reg.set("muted", "0")
                reg.set("opaque", "1")
                reg.set("locked", "0")
                reg.set("automatic", "0")
                reg.set("whole-file", "0")
                reg.set("start", str(start))
                reg.set("length", str(length))
                reg.set("position", str(pos))
                reg.set("sync-position", "0")
                reg.set("layering-index", "0")
                reg.set("channels", str(c_chans))

                # 關聯 Source IDs
                if s_ids:
                    reg.set("source-0", str(s_ids[0]))
                    reg.set("master-source-0", str(s_ids[0]))
                    if c_chans > 1 and len(s_ids) > 1:
                        reg.set("source-1", str(s_ids[1]))
                        reg.set("master-source-1", str(s_ids[1]))

                # 音量包絡線 (Envelope)
                env_points = c.get("envelope", [])
                env_node = ET.SubElement(reg, "Envelope")
                if env_points and len(env_points) > 0:
                    auto_list = ET.SubElement(env_node, "AutomationList")
                    auto_list.set("automation-id", "gain")
                    auto_list.set("id", str(self.id_gen.next_id()))
                    auto_list.set("interpolation-style", "Linear")
                    auto_list.set("state", "Touch")
                    events_node = ET.SubElement(auto_list, "events")
                    
                    event_lines = []
                    for pt_t, pt_val in env_points:
                        # pt_t 為秒數或相對 offset，轉換為 region 內樣本時間
                        sample_when = int(round(pt_t * self.sample_rate))
                        event_lines.append(f"{sample_when} {pt_val:.6f}")
                    
                    content_node = ET.SubElement(events_node, "foo")
                    content_node.text = "\n" + "\n".join(event_lines) + "\n"
                else:
                    env_node.set("default", "yes")

                fade_in = ET.SubElement(reg, "FadeIn")
                fade_in.set("default", "yes")

                fade_out = ET.SubElement(reg, "FadeOut")
                fade_out.set("default", "yes")

        # 其他必要子節點
        ET.SubElement(root, "UnusedPlaylists")
        ET.SubElement(root, "RouteGroups")

        click_elem = ET.SubElement(root, "Click")
        c_io = ET.SubElement(click_elem, "IO")
        c_io.set("name", "Click")
        c_io.set("id", str(self.id_gen.next_id()))
        c_io.set("direction", "Output")
        c_io.set("default-type", "audio")
        c_io.set("user-latency", "0")
        cp1 = ET.SubElement(c_io, "Port", type="audio", name="Click/audio_out 1")
        ET.SubElement(cp1, "Connection", other="system:playback_1")
        cp2 = ET.SubElement(c_io, "Port", type="audio", name="Click/audio_out 2")
        ET.SubElement(cp2, "Connection", other="system:playback_2")

        c_proc = ET.SubElement(click_elem, "Processor", id=str(self.id_gen.next_id()), name="Amp", active="yes", user_latency="0", type="amp")
        ET.SubElement(c_proc, "Controllable", name="gaincontrol", id=str(self.id_gen.next_id()), flags="", value="1.000000000000")

        # LTC In/Out
        ltc_in = ET.SubElement(root, "LTC-In")
        ltc_in_io = ET.SubElement(ltc_in, "IO", name="LTC In", id=str(self.id_gen.next_id()), direction="Input", default_type="audio", user_latency="0")
        ET.SubElement(ltc_in_io, "Port", type="audio", name="LTC-in")

        ltc_out = ET.SubElement(root, "LTC-Out")
        ltc_out_io = ET.SubElement(ltc_out, "IO", name="LTC Out", id=str(self.id_gen.next_id()), direction="Output", default_type="audio", user_latency="0")
        ET.SubElement(ltc_out_io, "Port", type="audio", name="LTC-out")

        # Speakers
        spk = ET.SubElement(root, "Speakers")
        ET.SubElement(spk, "Speaker", azimuth="240", elevation="0", distance="1")
        ET.SubElement(spk, "Speaker", azimuth="120", elevation="0", distance="1")

        # TempoMap
        tm = ET.SubElement(root, "TempoMap")
        ET.SubElement(tm, "Tempo", pulse="0.000000", frame="0", beats_per_minute="120.000000", note_type="4.000000", movable="no", active="yes", tempo_type="Ramp", lock_style="AudioTime", locked_to_meter="no")
        ET.SubElement(tm, "Meter", pulse="0.000000", bbt="1|1|0", beat="0.000000", note_type="4.000000", frame="0", lock_style="AudioTime", divisions_per_bar="4.000000", movable="no")

        # ControlProtocols
        cp = ET.SubElement(root, "ControlProtocols")
        for proto in ["Mackie", "Open Sound Control (OSC)", "PreSonus FaderPort", "Generic MIDI"]:
            ET.SubElement(cp, "Protocol", name=proto, active="no")

        # Extra
        extra = ET.SubElement(root, "Extra")
        ET.SubElement(extra, "Videomonitor", active="no")

        # 更新 id-counter
        root.set("id-counter", str(self.id_gen.current + 50))

        # 縮排格式化
        ET.indent(root, space="  ", level=0)
        xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        return xml_bytes.decode("utf-8")

    def export_session(self, output_dir: Path, tracks_data: List[Dict[str, Any]], session_end_samples: int = 0) -> Path:
        """
        建立標準 Ardour Session 目錄與 .ardour 工程檔。
        目錄結構：
        output_dir/
            <ProjectName>/
                <ProjectName>.ardour
                interchange/
                    <ProjectName>/
                        audiofiles/
        """
        output_dir = Path(output_dir).resolve()
        session_dir = output_dir / self.project_name
        audiofiles_dir = session_dir / "interchange" / self.project_name / "audiofiles"

        audiofiles_dir.mkdir(parents=True, exist_ok=True)

        ardour_xml_content = self.generate_ardour_xml(tracks_data, session_end_samples=session_end_samples)
        session_file = session_dir / f"{self.project_name}.ardour"

        with open(session_file, "w", encoding="utf-8") as f:
            f.write(ardour_xml_content)

        return session_file
