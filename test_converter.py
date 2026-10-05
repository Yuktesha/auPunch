#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test for auPunch multi-clip extraction and Smart Clip handle preservation.
"""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import tempfile
import shutil

from aup3_converter import Aup3Converter, NS, qn

class TestAup3ConverterSmartClips(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.converter = Aup3Converter.__new__(Aup3Converter)

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_xml_transformation_smart_clips_and_clips_mapping(self):
        # Sample XML containing 2 tracks, each with Smart Clip trim attributes
        sample_xml = """<?xml version="1.0" standalone="no" ?>
<!DOCTYPE project PUBLIC "-//audacityproject-1.3.0//DTD//EN" "http://audacity.sourceforge.net/xml/audacityproject-1.3.0.dtd" >
<project xmlns="http://audacity.sourceforge.net/xml/" version="1.3.0" audacityversion="3.7.0" rate="44100" projname="test_proj">
  <wavetrack name="Vocal Track" channel="0" linked="0" rate="44100" sampleformat="262159">
    <waveclip offset="1.5" trimLeft="0.45" trimRight="2.30" name="Vocal Clip 1" colorindex="1" centShift="0">
      <sequence maxsamples="262144" sampleformat="262159" numsamples="524288">
        <waveblock start="0" />
        <waveblock start="262144" />
      </sequence>
      <envelope numpoints="0" />
    </waveclip>
  </wavetrack>
  <wavetrack name="Guitar Track" channel="0" linked="1" rate="44100" sampleformat="262159">
    <waveclip offset="10.0" trimLeft="1.20" trimRight="0.00" name="Guitar Clip 1">
      <sequence maxsamples="262144" sampleformat="262159" numsamples="262144">
        <waveblock start="0" />
      </sequence>
      <envelope numpoints="0" />
    </waveclip>
  </wavetrack>
</project>
"""
        in_xml_path = self.temp_dir / "input.xml"
        out_aup_path = self.temp_dir / "output.aup"
        
        with open(in_xml_path, "w", encoding="utf-8") as f:
            f.write(sample_xml)
            
        clip_media_map = {
            "0_Vocal_0_Clip1.wav": "media/0_Vocal_0_Clip1.flac",
            "1_Guitar_0_Clip1.wav": "media/1_Guitar_0_Clip1.flac"
        }
        
        self.converter._transform_xml(
            in_xml_path,
            out_aup_path,
            "test_proj",
            clip_media_map=clip_media_map
        )
        
        self.assertTrue(out_aup_path.exists())
        
        tree = ET.parse(out_aup_path)
        root = tree.getroot()
        
        # Verify project metadata
        self.assertEqual(root.get("version"), "1.3.0")
        self.assertEqual(root.get("audacityversion"), "2.4.2")
        self.assertEqual(root.get("projname"), "test_proj_data")
        
        tracks = root.findall(qn("wavetrack"))
        self.assertEqual(len(tracks), 2)
        
        # Track 1 check
        tr1 = tracks[0]
        self.assertEqual(tr1.get("linked"), "0") # Preserved mono linked=0
        clip1 = tr1.find(qn("waveclip"))
        self.assertIsNotNone(clip1)
        self.assertEqual(clip1.get("trimLeft"), "0.45") # Smart Clip handle preserved!
        self.assertEqual(clip1.get("trimRight"), "2.30")
        self.assertNotIn("colorindex", clip1.attrib) # Stripped incompatible attr
        self.assertNotIn("centShift", clip1.attrib)
        
        # Blocks in Clip 1
        seq1 = clip1.find(qn("sequence"))
        wbs1 = seq1.findall(qn("waveblock"))
        self.assertEqual(len(wbs1), 2)
        
        alias1_0 = wbs1[0].find(qn("pcmaliasblockfile"))
        self.assertIsNotNone(alias1_0)
        self.assertEqual(alias1_0.get("aliasfile"), "media/0_Vocal_0_Clip1.flac")
        self.assertEqual(alias1_0.get("aliasstart"), "0")
        self.assertEqual(alias1_0.get("aliaschannel"), "0")
        
        alias1_1 = wbs1[1].find(qn("pcmaliasblockfile"))
        self.assertIsNotNone(alias1_1)
        self.assertEqual(alias1_1.get("aliasfile"), "media/0_Vocal_0_Clip1.flac")
        self.assertEqual(alias1_1.get("aliasstart"), "262144")
        
        # Track 2 check
        tr2 = tracks[1]
        self.assertEqual(tr2.get("linked"), "1") # Preserved linked=1
        clip2 = tr2.find(qn("waveclip"))
        self.assertEqual(clip2.get("trimLeft"), "1.20")
        self.assertEqual(clip2.get("trimRight"), "0.00")
        
        seq2 = clip2.find(qn("sequence"))
        wbs2 = seq2.findall(qn("waveblock"))
        self.assertEqual(len(wbs2), 1)
        alias2_0 = wbs2[0].find(qn("pcmaliasblockfile"))
        self.assertIsNotNone(alias2_0)
        self.assertEqual(alias2_0.get("aliasfile"), "media/1_Guitar_0_Clip1.flac")

    def test_xml_transformation_single_track_fallback(self):
        sample_xml = """<?xml version="1.0" standalone="no" ?>
<!DOCTYPE project PUBLIC "-//audacityproject-1.3.0//DTD//EN" "http://audacity.sourceforge.net/xml/audacityproject-1.3.0.dtd" >
<project xmlns="http://audacity.sourceforge.net/xml/" version="1.3.0" audacityversion="3.7.0" rate="44100" projname="single_proj">
  <wavetrack name="Stereo Track" channel="0" linked="1" rate="44100" sampleformat="262159">
    <waveclip offset="0.0" name="Clip 1">
      <sequence maxsamples="262144" sampleformat="262159" numsamples="262144">
        <waveblock start="0" />
      </sequence>
      <envelope numpoints="0" />
    </waveclip>
  </wavetrack>
  <wavetrack name="Stereo Track" channel="1" linked="0" rate="44100" sampleformat="262159">
    <waveclip offset="0.0" name="Clip 1">
      <sequence maxsamples="262144" sampleformat="262159" numsamples="262144">
        <waveblock start="0" />
      </sequence>
      <envelope numpoints="0" />
    </waveclip>
  </wavetrack>
</project>
"""
        in_xml_path = self.temp_dir / "input_single.xml"
        out_aup_path = self.temp_dir / "output_single.aup"
        with open(in_xml_path, "w", encoding="utf-8") as f:
            f.write(sample_xml)
            
        self.converter._transform_xml(
            in_xml_path,
            out_aup_path,
            "single_proj",
            single_media_rel_path="media/single_proj.flac"
        )
        
        self.assertTrue(out_aup_path.exists())
        tree = ET.parse(out_aup_path)
        root = tree.getroot()
        tracks = root.findall(qn("wavetrack"))
        self.assertEqual(len(tracks), 2)
        
        # Channel 0
        wb0 = tracks[0].find(qn("waveclip")).find(qn("sequence")).find(qn("waveblock"))
        alias0 = wb0.find(qn("pcmaliasblockfile"))
        self.assertEqual(alias0.get("aliasfile"), "media/single_proj.flac")
        self.assertEqual(alias0.get("aliaschannel"), "0")
        
        # Channel 1
        wb1 = tracks[1].find(qn("waveclip")).find(qn("sequence")).find(qn("waveblock"))
        alias1 = wb1.find(qn("pcmaliasblockfile"))
        self.assertEqual(alias1.get("aliasfile"), "media/single_proj.flac")
        self.assertEqual(alias1.get("aliaschannel"), "1")


if __name__ == "__main__":
    unittest.main()
