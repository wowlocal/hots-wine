#!/usr/bin/env python3
"""Warm a prepared paused replay using scoped playback keys and read-only OCR."""
import argparse,json,re,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('pid',type=int);p.add_argument('--target',type=int,default=900);p.add_argument('--speed-steps',type=int,default=4);a=p.parse_args()
base=Path.home()/'Library/Application Support/CrossOver/HotS-Setup';control=base/'replay-control-native'
def key(command):subprocess.run([str(control),str(a.pid),command],check=True,stdout=subprocess.DEVNULL)
def inspect():return json.loads(subprocess.check_output([str(base/'inspect-replay'),str(a.pid),str(base/'warmup-current.png')],text=True))
key('center')
first=inspect()['clock'];time.sleep(2);second=inspect()['clock']
if not first or not second:raise SystemExit('Clock is not visible; warm-up cancelled before changing playback')
for _ in range(a.speed_steps):key('faster')
if first==second:key('pause')
stop=base/f'warm-center-{a.pid}.stop';stop.unlink(missing_ok=True)
camera=subprocess.Popen([str(control),str(a.pid),'hold-center','180',str(stop)],stdout=subprocess.DEVNULL)
end=time.monotonic()+300
try:
    while time.monotonic()<end:
        result=json.loads(subprocess.check_output([str(base/'inspect-replay'),str(a.pid),str(base/'warmup-current.png')],text=True))
        print(json.dumps({'wall':result['wall'],'clock':result['clock'],'state':result['state']}),flush=True)
        clock=next((re.fullmatch(r'(-?)(\d+):(\d\d)',s) for s in result['clock'] if re.fullmatch(r'(-?)(\d+):(\d\d)',s)),None)
        if clock and not clock[1] and int(clock[2])*60+int(clock[3])>=a.target:break
        time.sleep(3)
    else:raise RuntimeError('Warm-up timeout; verify the paused replay before continuing')
finally:
    key('pause')
    for _ in range(a.speed_steps):key('slower')
    stop.write_text('stop\n');camera.wait(timeout=3)
print('Warm-up completed; replay paused at normal speed.',flush=True)
