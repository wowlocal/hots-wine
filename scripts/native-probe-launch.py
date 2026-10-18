#!/usr/bin/env python3
"""Run under CrossOver --ux-app to inherit its configured environment.

This uses a private, signed profiling loader and leaves installed binaries intact.
Pass a Unix PE path so the loader creates the initial Wine process correctly.
"""
import os
from pathlib import Path
import sys

base = Path.home() / 'Library/Application Support/CrossOver/HotS-Setup'
repo = Path(__file__).resolve().parent.parent
loader = base / 'profiling-loader/wineloader'
os.environ['DYLD_INSERT_LIBRARIES'] = str(repo / 'tools/frame-probe/frame-probe.dylib')
os.environ.pop('WINELOADERNOEXEC', None)
os.environ['HOTS_FRAME_PROBE_DIRECT'] = '1'
os.execv(str(loader), [str(loader), *sys.argv[1:]])
