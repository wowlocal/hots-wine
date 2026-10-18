#!/usr/bin/env python3
"""Launch a replay with Wine and collect Metal frame logs; no UI automation."""
import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import time

BASE = Path(os.environ.get('HOTS_SETUP_DIR', str(Path.home() / 'Library/Application Support/CrossOver/HotS-Setup')))
BOTTLE = BASE.parent / 'Bottles/Heroes of the Storm'
GAME = BOTTLE / 'drive_c/Program Files (x86)/Heroes of the Storm'
DOCUMENTS = BOTTLE / 'drive_c/users/crossover/Documents/Heroes of the Storm'
WINE = '/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine'


def game_pids():
    result = []
    for line in subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True).splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[1].startswith(r'C:\Program Files (x86)\Heroes of the Storm\Versions\Base98348\HeroesOfTheStorm_x64.exe'):
            result.append(int(parts[0]))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('backend', choices=['dxvk', 'dxmt', 'd3dmetal'])
    parser.add_argument('--seconds', type=int, default=150)
    parser.add_argument('--label', default='test')
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--trace-seconds', type=int, default=0)
    parser.add_argument('--trace-delay', type=int, default=45)
    args = parser.parse_args()
    if game_pids():
        raise SystemExit('A Windows game process is already running; leaving it untouched.')
    exe = GAME / 'Versions/Base98348/HeroesOfTheStorm_x64.exe'
    if not exe.is_file():
        raise SystemExit('Windows executable is not installed yet.')
    replay = args.replay or max(DOCUMENTS.rglob('*.StormReplay'), key=lambda p: p.stat().st_mtime)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    folder = BASE / 'benchmarks' / f'{stamp}-{args.backend}-{args.label}'
    folder.mkdir(parents=True)
    (folder / 'Variables.before.txt').write_bytes((DOCUMENTS / 'Variables.txt').read_bytes())
    info = dict(backend=args.backend, duration_requested=args.seconds, replay=str(replay),
                start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                msync=True, ui_automation=False, game_pids=[])
    (folder / 'run.json').write_text(json.dumps(info, indent=2))
    with (folder / 'metal.ndjson').open('w') as metal, (folder / 'wine.log').open('w') as wine_log:
        log = subprocess.Popen(['/usr/bin/log', 'stream', '--style', 'ndjson', '--level', 'debug',
                                '--predicate', 'eventMessage CONTAINS "metal-HUD"'],
                               stdout=metal, stderr=metal)
        env_string = (f'CX_GRAPHICS_BACKEND={args.backend} WINEMSYNC=1 WINE_SIMULATE_WRITECOPY=1 OS_ACTIVITY_DT_MODE=1 '
                      'MTL_HUD_ENABLED=1 MTL_HUD_LOG_ENABLED=1 MTL_HUD_LOG_SHADER_ENABLED=1 '
                      f'DXVK_LOG_PATH="{folder}" DXVK_LOG_LEVEL=info')
        win_replay = 'C:\\' + str(replay.relative_to(BOTTLE / 'drive_c')).replace('/', '\\')
        command = [WINE, '--bottle', 'Heroes of the Storm', '--no-gui', '--debugmsg', '-all',
                   '--no-wait', '--workdir', str(GAME / 'Support64'), '--env', env_string, '--cx-app',
                   r'C:\Program Files (x86)\Heroes of the Storm\Support64\HeroesSwitcher_x64.exe',
                   win_replay]
        subprocess.Popen(command, stdout=wine_log, stderr=wine_log, start_new_session=True)
        print('Benchmark directory:', folder, flush=True)
        started = time.monotonic()
        seen = set()
        trace = None
        trace_file = None
        while time.monotonic() - started < args.seconds:
            pids = game_pids()
            seen.update(pids)
            if args.trace_seconds and not trace and pids and time.monotonic() - started >= args.trace_delay:
                trace_file = (folder / 'xctrace.log').open('w')
                trace = subprocess.Popen(['xcrun', 'xctrace', 'record', '--template', 'Metal System Trace',
                                          '--time-limit', f'{args.trace_seconds}s', '--attach', str(pids[0]),
                                          '--no-prompt', '--output', str(folder / 'metal.trace')],
                                         stdout=trace_file, stderr=trace_file)
            if seen and not pids:
                print('Game process exited.', flush=True)
                break
            if not seen and time.monotonic() - started > 45:
                print('No game process detected after 45 seconds.', flush=True)
                break
            time.sleep(1)
        for pid in game_pids():
            if pid in seen:
                os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        for pid in game_pids():
            if pid in seen:
                os.kill(pid, signal.SIGKILL)
        if trace:
            trace.wait(timeout=120)
            trace_file.close()
        log.terminate()
        log.wait(timeout=10)
    info.update(game_pids=sorted(seen), elapsed=time.monotonic() - started,
                end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (folder / 'run.json').write_text(json.dumps(info, indent=2))
    if (DOCUMENTS / 'Variables.txt').exists():
        (folder / 'Variables.after.txt').write_bytes((DOCUMENTS / 'Variables.txt').read_bytes())
    print(json.dumps(info, indent=2), flush=True)


if __name__ == '__main__':
    main()
