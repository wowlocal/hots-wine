#!/usr/bin/env python3
"""Stage the pinned official DXMT archive without editing the installed app."""
import argparse,hashlib,json,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=Path.home()/'Library/Application Support/CrossOver/HotS-Setup'
CX=Path('/Applications/CrossOver.app/Contents/SharedSupport/CrossOver')
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=BASE/'downloads/dxmt-v0.80-builtin.tar.gz');a=p.parse_args()
expected=json.loads((ROOT/'results/runtime-audit.json').read_text())['archive_sha256']
if hashlib.sha256(a.archive.read_bytes()).hexdigest()!=expected:raise SystemExit('Archive hash differs from the pinned official release')
unpacked=BASE/'runtimes/dxmt-v0.80'
if not (unpacked/'v0.80').is_dir():
    unpacked.mkdir(parents=True,exist_ok=True)
    with tarfile.open(a.archive)as archive:
        for item in archive.getmembers():
            if not (unpacked/item.name).resolve().is_relative_to(unpacked.resolve()):raise SystemExit('Unsafe archive path')
        archive.extractall(unpacked,filter='data')
overlay=BASE/'runtimes/cx-dxmt-v0.80';overlay.mkdir(exist_ok=True)
def link(source,target):
    if target.is_symlink():
        if target.resolve()!=source.resolve():raise SystemExit(f'Unexpected existing link: {target.name}')
    elif target.exists():raise SystemExit(f'Unexpected existing file: {target.name}')
    else:target.symlink_to(source,target_is_directory=source.is_dir())
for source in CX.iterdir():
    if source.name!='lib':link(source,overlay/source.name)
(overlay/'lib').mkdir(exist_ok=True)
for source in (CX/'lib').iterdir():
    if source.name!='dxmt':link(source,overlay/'lib'/source.name)
link(unpacked/'v0.80',overlay/'lib/dxmt')
print('Pinned DXMT0.80 overlay ready; installed CrossOver unchanged.')
