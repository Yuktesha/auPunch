#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for ArdourExporter (auPunch)
"""

import unittest
import tempfile
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from ardour_exporter import ArdourExporter

class TestArdourExporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_ardour_"))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_and_export_ardour_session(self):
        exporter = ArdourExporter(project_name="TestSong", sample_rate=48000)

        tracks_data = [
            {
                "name": "Vocals",
                "channels": 2,
                "gain": 0.85,
                "pan": -0.2,
                "mute": False,
                "solo": False,
                "clips": [
                    {
                        "name": "Intro Vocal",
                        "audio_filename": "intro_vocal.flac",
                        "channels": 2,
                        "position": 0,
                        "length": 96000, # 2.0s
                        "start": 0,
                        "envelope": [
                            (0.0, 0.0),
                            (0.5, 1.0),
                            (1.5, 1.0),
                            (2.0, 0.0)
                        ]
                    },
                    {
                        "name": "Chorus Vocal",
                        "audio_filename": "chorus_vocal.flac",
                        "channels": 2,
                        "position": 192000, # 4.0s
                        "length": 144000, # 3.0s
                        "start": 0,
                        "envelope": []
                    }
                ]
            },
            {
                "name": "Guitar",
                "channels": 1,
                "gain": 1.0,
                "pan": 0.5,
                "mute": False,
                "solo": False,
                "clips": [
                    {
                        "name": "Riff",
                        "audio_filename": "guitar_riff.flac",
                        "channels": 1,
                        "position": 48000, # 1.0s
                        "length": 96000,
                        "start": 0,
                        "envelope": []
                    }
                ]
            }
        ]

        session_file = exporter.export_session(self.temp_dir, tracks_data)
        self.assertTrue(session_file.exists())
        self.assertEqual(session_file.name, "TestSong.ardour")

        # 驗證 interchange 音訊資料夾存在
        audiofiles_dir = self.temp_dir / "TestSong" / "interchange" / "TestSong" / "audiofiles"
        self.assertTrue(audiofiles_dir.exists())

        # 解析 XML
        tree = ET.parse(session_file)
        root = tree.getroot()
        self.assertEqual(root.tag, "Session")
        self.assertEqual(root.get("version"), "7002")
        self.assertEqual(root.get("sample-rate"), "48000")
        self.assertEqual(root.get("name"), "TestSong")

        # 驗證 Sources
        sources = root.findall("./Sources/Source")
        # Vocals: 2 stereo files = 2 * 2 = 4 Sources
        # Guitar: 1 mono file = 1 Source
        # Total = 5 Sources
        self.assertEqual(len(sources), 5)
        source_ids = {s.get("id"): s for s in sources}

        # 驗證 Routes (Master + 2 Tracks)
        routes = root.findall("./Routes/Route")
        self.assertEqual(len(routes), 3)
        route_names = [r.get("name") for r in routes]
        self.assertIn("Master", route_names)
        self.assertIn("Vocals", route_names)
        self.assertIn("Guitar", route_names)

        # 驗證 Playlists (2 Tracks)
        playlists = root.findall("./Playlists/Playlist")
        self.assertEqual(len(playlists), 2)
        pl_names = [p.get("name") for p in playlists]
        self.assertIn("Vocals.1", pl_names)
        self.assertIn("Guitar.1", pl_names)

        # 驗證 Vocals Playlist Clips (2 Regions)
        vocal_pl = [p for p in playlists if p.get("name") == "Vocals.1"][0]
        vocal_regions = vocal_pl.findall("Region")
        self.assertEqual(len(vocal_regions), 2)

        reg0 = vocal_regions[0]
        self.assertEqual(reg0.get("name"), "Intro Vocal")
        self.assertEqual(reg0.get("position"), "0")
        self.assertEqual(reg0.get("length"), "96000")
        self.assertEqual(reg0.get("channels"), "2")
        self.assertIn(reg0.get("source-0"), source_ids)
        self.assertIn(reg0.get("source-1"), source_ids)

        # 驗證四點式音量包絡線
        env = reg0.find("Envelope")
        self.assertIsNotNone(env)
        auto_list = env.find("AutomationList")
        self.assertIsNotNone(auto_list)
        events = auto_list.find("events")
        self.assertIsNotNone(events)
        self.assertIn("0 0.000000", events.find("foo").text)
        self.assertIn("96000 0.000000", events.find("foo").text)

        # 驗證 Guitar Playlist Clip (1 Mono Region)
        guitar_pl = [p for p in playlists if p.get("name") == "Guitar.1"][0]
        guitar_regions = guitar_pl.findall("Region")
        self.assertEqual(len(guitar_regions), 1)
        g_reg = guitar_regions[0]
        self.assertEqual(g_reg.get("channels"), "1")
        self.assertIn(g_reg.get("source-0"), source_ids)
        self.assertIsNone(g_reg.get("source-1"))

        # 驗證 Locations 起訖範圍
        locations = root.findall("./Locations/Location")
        self.assertEqual(len(locations), 1)
        loc = locations[0]
        # Vocals chorus ends at 192000 + 144000 = 336000
        self.assertEqual(loc.get("end"), "336000")

if __name__ == "__main__":
    unittest.main()
