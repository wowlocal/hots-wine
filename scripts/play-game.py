#!/usr/bin/env python3
"""Normal-game launcher with native display geometry and restoration on game exit.

No replay controls or match joining. Battle.net and wineserver are left running.
"""
import argparse,datetime,importlib.util,json,re,select,signal,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hots_launch',ROOT/'scripts/launch-profile.py')
launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)
BASE=launch.BASE
KEY=r'HKCU\Software\Wine\Mac Driver'
def reg(*args,check=True):
    return subprocess.run([launch.WINE,'--bottle','Heroes of the Storm','--no-gui','--debugmsg','-all','--cx-app','reg',*args],capture_output=True,text=True,check=check)
def main():
    profiles=json.loads((ROOT/'configs/profiles.json').read_text())
    p=argparse.ArgumentParser();p.add_argument('profile',choices=profiles);a=p.parse_args()
    if profiles[a.profile].get('rejected_for_play'):raise SystemExit(profiles[a.profile]['rejected_for_play'])
    running=launch.pids()
    if running:
        subprocess.run([str(BASE/'replay-control-native'),str(running[0]),'activate'],check=True)
        print('Game already running; current graphics and display settings retained.')
        return
    for name in ['display-mode','replay-control-native']:
        if not (BASE/name).is_file():raise SystemExit(f'Missing locally built helper: {name}')
    state=BASE/'launches'/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-normal-display')
    state.mkdir(parents=True)
    query=reg('query',KEY,'/v','RetinaMode',check=False)
    match=re.search(r'RetinaMode\s+REG_SZ\s+(\S+)',query.stdout)
    if query.returncode and 'unable to find' not in query.stdout.lower():
        raise SystemExit('Could not read the original RetinaMode value; display unchanged.')
    original=match[1] if match else None
    (state/'retina-before.json').write_text(json.dumps({'RetinaMode':original})+'\n')
    backup=state/'display-before.json'
    changed=False
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in [signal.SIGTERM,signal.SIGHUP,signal.SIGINT]:signal.signal(sig,interrupted)
    try:
        subprocess.run([str(BASE/'display-mode'),'native1x',str(backup)],check=True)
        changed=True
        reg('add',KEY,'/v','RetinaMode','/t','REG_SZ','/d','N','/f')
        subprocess.run(['python3',str(ROOT/'scripts/launch-profile.py'),a.profile,'--game'],check=True)
        game=launch.pids()
        if len(game)!=1:raise RuntimeError('Expected one game process after launch')
        pid=game[0]
        watcher=select.kqueue()
        try:watcher.control([select.kevent(pid,filter=select.KQ_FILTER_PROC,flags=select.KQ_EV_ADD,fflags=select.KQ_NOTE_EXIT)],0,0)
        except ProcessLookupError:return
        print('Normal game started. Quit the game to restore macOS display scaling.',flush=True)
        # Allow menu loading to finish before the same one-shot viewport repair
        # used by the replay launcher. No menu or match input is sent.
        exited=bool(watcher.control(None,1,60))
        if not exited:
            subprocess.run([str(BASE/'replay-control-native'),str(pid),'activate'],check=True)
            launch.helper('display=1');launch.helper('native=1')
            print('Native viewport applied; waiting for game exit.',flush=True)
            watcher.control(None,1,None)
        watcher.close()
    finally:
        if changed:
            if original is None:reg('delete',KEY,'/v','RetinaMode','/f',check=False)
            else:reg('add',KEY,'/v','RetinaMode','/t','REG_SZ','/d',original,'/f')
            subprocess.run([str(BASE/'display-mode'),'restore',str(backup)],check=True)
            print('Original macOS display mode and RetinaMode restored.',flush=True)

if __name__=='__main__':main()
