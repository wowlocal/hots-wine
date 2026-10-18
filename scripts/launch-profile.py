#!/usr/bin/env python3
"""Launch a native Ultra replay in the existing authenticated bottle.

Only this bottle's game can be stopped. Battle.net and wineserver stay running.
All backups and paths containing account information remain outside the repo.
"""
import argparse,datetime,json,os,shlex,signal,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=Path.home()/'Library/Application Support/CrossOver/HotS-Setup'
BOTTLE=BASE.parent/'Bottles/Heroes of the Storm'
DOCS=BOTTLE/'drive_c/users/crossover/Documents/Heroes of the Storm'
WINE='/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine'
EXE=r'C:\Program Files (x86)\Heroes of the Storm\Versions\Base98348\HeroesOfTheStorm_x64.exe'
def pids():
    return [int(line.split(None,1)[0]) for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines() if line.strip().split(None,1)[-1].startswith(EXE)]
def helper(arg):
    subprocess.run([WINE,'--bottle','Heroes of the Storm','--no-gui','--debugmsg','-all','--cx-app',r'Y:\Library\Application Support\CrossOver\HotS-Setup\replay-control-build\replay-control.exe',arg],check=True)

def main():
    profiles=json.loads((ROOT/'configs/profiles.json').read_text())
    p=argparse.ArgumentParser();p.add_argument('profile',choices=profiles);p.add_argument('--replace-game',action='store_true');p.add_argument('--prepare-replay',action='store_true');p.add_argument('--hud',action='store_true')
    a=p.parse_args();profile=profiles[a.profile]
    running=pids()
    if running and not a.replace_game:raise SystemExit('Game is running. Use --replace-game only for an authorized benchmark restart.')
    for pid in running:os.kill(pid,signal.SIGTERM)
    until=time.monotonic()+5
    while pids() and time.monotonic()<until:time.sleep(.2)
    for pid in pids():
        if pid in running:os.kill(pid,signal.SIGKILL)
    time.sleep(.5)
    out=BASE/'launches'/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+a.profile);out.mkdir(parents=True)
    variables=DOCS/'Variables.txt';(out/'Variables.before.txt').write_bytes(variables.read_bytes())
    values=dict(l.split('=',1) for l in variables.read_text().splitlines() if '=' in l)
    values.update(json.loads((ROOT/'configs/ultra.json').read_text())['settings'])
    values.update(frameratecap=str(profile['game_cap']),lastDeviceId=str(profile.get('last_device_id',26640)),enablefunctionkeys='true')
    values['displaymode']=str(profile.get('display_mode',1))
    values.update(windowwidth='3456',windowheight='2234',windowx='0',windowy='0')
    if 'reduce_mouse_lag' in profile:values['reducemouselagenabled']='true' if profile['reduce_mouse_lag'] else 'false'
    variables.write_text(''.join(f'{k}={v}\n' for k,v in sorted(values.items())))
    replay=next(DOCS.rglob('*16.02.25 Cursed Hollow.StormReplay'))
    replay_win='C:\\'+str(replay.relative_to(BOTTLE/'drive_c')).replace('/','\\')
    env={'CX_GRAPHICS_BACKEND':profile['backend'],'WINEMSYNC':str(profile['msync']),'WINE_SIMULATE_WRITECOPY':'1','MTL_HUD_ENABLED':'1' if a.hud else '0',**profile['env']}
    log=(out/'wine.log').open('w')
    command=[WINE,'--bottle','Heroes of the Storm','--no-gui','--debugmsg','-all','--no-wait','--env',shlex.join(f'{k}={v}' for k,v in env.items()),'--cx-app',r'C:\Program Files (x86)\Heroes of the Storm\Support64\HeroesSwitcher_x64.exe',replay_win,'-sso=1','-launch','-uid','heroes']
    subprocess.Popen(command,stdout=log,stderr=log,start_new_session=True)
    until=time.monotonic()+45
    while not pids() and time.monotonic()<until:time.sleep(.5)
    game=pids()
    if len(game)!=1:raise SystemExit('Game startup did not produce one expected process. Inspect private launch logs.')
    (out/'launch.json').write_text(json.dumps({'profile':a.profile,'env':env,'pid':game[0]},indent=2)+'\n')
    print(f'Game PID {game[0]}; profile {a.profile}; private logs {out}',flush=True)
    if a.prepare_replay:
        # Let parallel asset/shader loading settle before changing the viewport.
        time.sleep(30)
        until=time.monotonic()+180
        quiet_since=None
        while time.monotonic()<until:
            try:
                cpu=float(subprocess.check_output(['ps','-p',str(game[0]),'-o','%cpu='],text=True).strip())
                if cpu>300:quiet_since=None;time.sleep(2);continue
                if quiet_since is None:quiet_since=time.monotonic()
                if time.monotonic()-quiet_since<8:time.sleep(2);continue
                helper('display=1');helper('native=1')
                state=json.loads(subprocess.check_output([str(BASE/'inspect-replay'),str(game[0]),str(out/'loaded.png')],text=True))
                if any(s not in ('00:00','-00:00') for s in state['clock']) and not any('Seeking' in s for s in state['state']):break
            except (subprocess.CalledProcessError,json.JSONDecodeError):pass
            time.sleep(2)
        else:raise SystemExit('Replay clock was not detected; do not send preparation keys while loading.')
        helper('display=1');helper('native=1')
        subprocess.run([str(BASE/'replay-control-native'),str(game[0]),'center'],check=True)
        time.sleep(2)
        def clock():
            return json.loads(subprocess.check_output([str(BASE/'inspect-replay'),str(game[0]),str(out/'prepared.png')],text=True))['clock']
        first=clock();time.sleep(2);second=clock()
        if first!=second:subprocess.run([str(BASE/'replay-control-native'),str(game[0]),'pause'],check=True)
        print('Loaded replay centered and paused; verify viewport and effective settings before measuring.',flush=True)

if __name__=='__main__':main()
