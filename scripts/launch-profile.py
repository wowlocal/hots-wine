#!/usr/bin/env python3
"""Launch a native Ultra replay in the existing authenticated bottle.

Only this bottle's game can be stopped. Battle.net and wineserver stay running.
All backups and paths containing account information remain outside the repo.
"""
import argparse,datetime,json,os,re,shlex,signal,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=Path.home()/'Library/Application Support/CrossOver/HotS-Setup'
BOTTLE=BASE.parent/'Bottles/Heroes of the Storm'
DOCS=BOTTLE/'drive_c/users/crossover/Documents/Heroes of the Storm'
WINE='/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine'
GAME=BOTTLE/'drive_c/Program Files (x86)/Heroes of the Storm'
def pids():
    found=[]
    for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
        parts=line.strip().split(None,1)
        if len(parts)!=2 or not re.match(r'^C:\\Program Files \(x86\)\\Heroes of the Storm\\Versions\\Base\d+\\HeroesOfTheStorm_x64\.exe(?:\s|$)',parts[1]):continue
        pid=int(parts[0])
        opened=subprocess.run(['lsof','-a','-p',str(pid),'-d','cwd','-Fn'],capture_output=True,text=True)
        if f'n{GAME}/Support64' in opened.stdout.splitlines():found.append(pid)
    return found
def helper(arg):
    subprocess.run([WINE,'--bottle','Heroes of the Storm','--no-gui','--debugmsg','-all','--cx-app',r'Y:\Library\Application Support\CrossOver\HotS-Setup\replay-control-build\replay-control.exe',arg],check=True)

def main():
    profiles=json.loads((ROOT/'configs/profiles.json').read_text())
    p=argparse.ArgumentParser();p.add_argument('profile',choices=profiles);p.add_argument('--replace-game',action='store_true');p.add_argument('--prepare-replay',action='store_true');p.add_argument('--hud',action='store_true');p.add_argument('--game',action='store_true',help='Open the normal game instead of the benchmark replay')
    a=p.parse_args();profile=profiles[a.profile]
    if a.game and a.prepare_replay:p.error('--game cannot prepare a replay')
    if a.game and profile.get('rejected_for_play'):raise SystemExit(profile['rejected_for_play'])
    if 'runtime_overlay' in profile:
        overlay=BASE/'runtimes'/profile['runtime_overlay'];runtime=overlay/'lib/dxmt'
        required=['x86_64-windows/d3d11.dll','x86_64-windows/dxgi.dll','x86_64-windows/winemetal.dll','x86_64-unix/winemetal.so']
        if not all((runtime/name).is_file()for name in required):raise SystemExit('Prepare the pinned private runtime overlay before launching this profile')
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
    function_keys=values.get('enablefunctionkeys','false')
    values.update(json.loads((ROOT/'configs/ultra.json').read_text())['settings'])
    values.update(frameratecap=str(profile['game_cap']),lastDeviceId=str(profile.get('last_device_id',26640)),enablefunctionkeys=function_keys if a.game else 'true')
    values['displaymode']=str(profile.get('display_mode',1))
    values.update(windowwidth='3456',windowheight='2234',windowx='0',windowy='0')
    # An absent key in the original baseline meant the engine default. Do not
    # inherit an explicit value left by a different experimental profile.
    if 'reduce_mouse_lag' in profile:values['reducemouselagenabled']='true' if profile['reduce_mouse_lag'] else 'false'
    else:values.pop('reducemouselagenabled',None)
    values['vsync']='true' if profile.get('vsync',False) else 'false'
    variables.write_text(''.join(f'{k}={v}\n' for k,v in sorted(values.items())))
    replay_args=[]
    if not a.game:
        replay=next(DOCS.rglob('*16.02.25 Cursed Hollow.StormReplay'))
        replay_args=['C:\\'+str(replay.relative_to(BOTTLE/'drive_c')).replace('/','\\')]
    env={'CX_GRAPHICS_BACKEND':profile['backend'],'WINEMSYNC':str(profile['msync']),'WINE_SIMULATE_WRITECOPY':'1','MTL_HUD_ENABLED':'1' if a.hud else '0',**profile['env']}
    if 'runtime_overlay' in profile:
        cx=Path(WINE).parents[1]
        env.update(CX_ROOT=str(overlay),WINEDLLPATH=':'.join(str(x)for x in [runtime/'x86_64-windows',runtime,cx/'lib/wine/x86_64-windows',cx/'lib/wine/i386-windows',cx/'lib/wine']),WINEDLLOVERRIDES='d3d11,dxgi,d3d10core,winemetal=b',DXMT_LOG_LEVEL='error')
    log=(out/'wine.log').open('w')
    command=[WINE,'--bottle','Heroes of the Storm','--no-gui','--debugmsg','-all','--no-wait','--env',shlex.join(f'{k}={v}' for k,v in env.items()),'--cx-app',r'C:\Program Files (x86)\Heroes of the Storm\Support64\HeroesSwitcher_x64.exe',*replay_args,'-sso=1','-launch','-uid','heroes']
    subprocess.Popen(command,stdout=log,stderr=log,start_new_session=True)
    until=time.monotonic()+45
    while not pids() and time.monotonic()<until:time.sleep(.5)
    game=pids()
    if len(game)!=1:raise SystemExit('Game startup did not produce one expected process. Inspect private launch logs.')
    (out/'launch.json').write_text(json.dumps({'profile':a.profile,'env':env,'pid':game[0],'mode':'game' if a.game else 'replay'},indent=2)+'\n')
    print(f'Game PID {game[0]}; profile {a.profile}; private logs {out}',flush=True)
    if a.prepare_replay:
        # Map startup can replace the window. Refresh after initial loading,
        # then require a running world clock before considering it prepared.
        time.sleep(60)
        until=time.monotonic()+180
        while time.monotonic()<until:
            try:
                subprocess.run([str(BASE/'replay-control-native'),str(game[0]),'activate'],check=True,stdout=subprocess.DEVNULL)
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
