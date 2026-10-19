#!/usr/bin/env python3
"""Synthetic rejection cases for the measurement gates, not game FPS tests."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

HEADER = struct.Struct('<8sIIQQIIQdII')
RECORD = struct.Struct('<dQQQIIQQ')
PID = 2147483600  # Deliberately nonexistent on the test Mac.


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.rows = [dict(kind='sample', host_ns=1_000_000_000+i*250_000_000,
                          expected_pid=PID, frontmost_pid=PID, active=True)
                     for i in range(133)]
        self.write_probe()
        (self.root/'anchor.json').write_text(json.dumps(dict(pid=PID,play_command_after_host_ns=2_000_000_000)))

    def tearDown(self):
        self.directory.cleanup()

    def write_probe(self, fps=120, drop=None, size=(3456, 2234), two_layers=False,
                    bad_boundary_size=False, switch_after_end=False):
        records = []
        self.frame_times = []
        for i in range(31*fps+1):
            t = 2+i/fps
            if drop is not None and abs(t-drop) < .000001:
                continue
            n = len(records)
            self.frame_times.append(t)
            frame_size=(1728,1117)if bad_boundary_size and abs(t-30)<.000001 else size
            layer=43 if switch_after_end and t>=30 else 42+(i%2 if two_layers else 0)
            records.append(RECORD.pack(t, int((t+.001)*1e9), i, int((t-.001)*1e9), *frame_size,layer,n+1))
        header = HEADER.pack(b'HOTSMTL1', 3, RECORD.size, 1000000, len(records), 1, 1, 0, 0, PID, 0)+struct.pack('<Q',len(records))
        (self.root/'frames.bin').write_bytes(header+b'\0'*(4096-len(header))+b''.join(records))

    def run_case(self, success=True, optimized=False, extra=()):
        (self.root/'focus.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in sorted(self.rows,key=lambda r:r['host_ns'])))
        command = [sys.executable]+(['-O']if optimized else [])+[
            str(Path(__file__).with_name('qualify-probe-fps.py')),str(self.root/'frames.bin'),
            '--pid',str(PID),'--focus',str(self.root/'focus.jsonl'),
            '--anchor',str(self.root/'anchor.json'),
            '--output',str(self.root/'metrics.json'),*extra]
        r = subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(r.returncode==0,success,r.stderr)
        return json.loads((self.root/'metrics.json').read_text())if success else None

    def test_constant_120_with_rosetta_nanosecond_clock(self):
        result = self.run_case()
        self.assertEqual(result['average_fps'],120)
        self.assertTrue(result['numeric_120_pass'])

    def test_60_fps_does_not_pass_even_without_25ms_stalls(self):
        self.write_probe(fps=60)
        result = self.run_case()
        self.assertFalse(result['numeric_120_pass'])
        self.assertEqual(result['frames_over_25_ms'],0)
        self.assertGreater(result['missed_refresh_intervals'],0)

    def test_two_60fps_layers_cannot_merge_into_fake_120(self):
        self.write_probe(two_layers=True)
        self.run_case(success=False)

    def test_wrong_boundary_size_is_rejected(self):
        self.write_probe(bad_boundary_size=True)
        self.run_case(success=False)

    def test_foreign_layer_cannot_supply_coverage_after_window(self):
        self.write_probe(switch_after_end=True)
        self.run_case(success=False)

    def test_boundary_missed_frame_survives_fixed_window(self):
        self.write_probe(drop=5)
        result = self.run_case()
        self.assertGreater(result['max_ms'],16)
        self.assertFalse(result['numeric_120_pass'])

    def test_false_active_flag_cannot_hide_wrong_observed_pid(self):
        self.rows[20]['frontmost_pid']=123
        self.run_case(success=False,optimized=True)

    def test_activation_between_periodic_samples_is_rejected(self):
        self.rows.append(dict(kind='activation',host_ns=5_125_000_000,expected_pid=PID,
                              frontmost_pid=123,active=False))
        self.run_case(success=False)

    def test_missing_coverage_is_rejected(self):
        self.rows=self.rows[25:]
        self.run_case(success=False)

    def test_sampler_gap_is_rejected(self):
        del self.rows[20:23]
        self.run_case(success=False)

    def test_non_native_drawable_is_rejected(self):
        self.write_probe(size=(1728,1117))
        self.run_case(success=False)

    def write_swaps(self, add_unmatched=False):
        def table(name, columns):
            root=ET.Element('trace-query-result');node=ET.SubElement(root,'node')
            schema=ET.SubElement(node,'schema',name=name)
            for mnemonic,kind in columns:
                col=ET.SubElement(schema,'col');ET.SubElement(col,'mnemonic').text=mnemonic
                ET.SubElement(col,'engineering-type').text=kind
            return root,node
        root,node=table('time-info',[('mabs-epoch','mach-absolute-time'),('timebase-info','mach-timebase-info')])
        row=ET.SubElement(node,'row');ET.SubElement(row,'mach-absolute-time').text='48000000'
        tb=ET.SubElement(row,'mach-timebase-info')
        for value in ['125','3']:ET.SubElement(tb,'mach-timebase-info-field').text=value
        ET.ElementTree(root).write(self.root/'time.xml')
        root,node=table('display-surface-swap',[('timestamp','start-time'),('display-name','display-name')])
        stamps=[round(t*1e9)-2_000_000_000 for t in self.frame_times]
        if add_unmatched:stamps.append(3_001_000_000)
        for stamp in sorted(stamps):
            row=ET.SubElement(node,'row');ET.SubElement(row,'start-time').text=str(stamp)
            ET.SubElement(row,'display-name').text='Built-In Display'
        ET.ElementTree(root).write(self.root/'swaps.xml')
        return ['--swaps',str(self.root/'swaps.xml'),'--time-info',str(self.root/'time.xml')]

    def test_native_trace_and_rosetta_probe_have_different_timebases(self):
        result=self.run_case(extra=self.write_swaps())
        self.assertTrue(result['display_crosscheck']['valid'])

    def test_unmatched_display_swap_is_rejected(self):
        self.run_case(success=False,extra=self.write_swaps(add_unmatched=True))


if __name__=='__main__':
    unittest.main()
