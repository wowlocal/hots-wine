#!/usr/bin/env python3
"""Align an already warmed, paused replay using cached10s skips and timed playback."""
import argparse,json,math,re,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('pid',type=int);p.add_argument('clock');a=p.parse_args()
minute,second=map(int,a.clock.split(':'));target=minute*60+second
base=Path.home()/'Library/Application Support/CrossOver/HotS-Setup'
def key(command,*args):subprocess.run([str(base/'replay-control-native'),str(a.pid),command,*map(str,args)],check=True,stdout=subprocess.DEVNULL)
def clock():
    d=json.loads(subprocess.check_output([str(base/'inspect-replay'),str(a.pid),str(base/f'section-{a.pid}.png')],text=True))
    for s in d['clock']:
        m=re.fullmatch(r'(\d+):(\d\d)',s)
        if m and not any('Seeking'in x for x in d['state']):return int(m[1])*60+int(m[2])
def stable():
    until=time.monotonic()+90;previous=None;repeats=0
    while time.monotonic()<until:
        current=clock();repeats=repeats+1 if current is not None and current==previous else 0;previous=current
        if repeats>=2:return current
        time.sleep(1)
    raise RuntimeError('Replay clock did not settle; no measurement started')
key('center')
for _ in range(10):
    current=stable();print(f'Prepared clock {current//60:02}:{current%60:02}',flush=True)
    delta=target-current
    if delta==0:break
    if 0<delta<10:key('play-for',delta)
    elif delta>0:key('next',min(100,delta//10))
    else:key('back',min(100,math.ceil(-delta/10)))
else:raise SystemExit('Section could not be aligned exactly; replay remains paused')
print(f'Replay paused at requested clock {a.clock}',flush=True)
