#!/usr/bin/env python3
"""Capture a prepared, paused replay; does not launch or change graphics settings."""
import argparse,json,subprocess,time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('pid',type=int);p.add_argument('label');p.add_argument('--seconds',type=int,default=40);p.add_argument('--instrument',default='Metal Application');p.add_argument('--schema',default='ca-client-presented-handler');p.add_argument('--hold-center',action='store_true')
a=p.parse_args();base=Path.home()/'Library/Application Support/CrossOver/HotS-Setup'
out=base/'benchmarks'/a.label;out.mkdir(exist_ok=False)
docs=base.parent/'Bottles/Heroes of the Storm/drive_c/users/crossover/Documents/Heroes of the Storm'
actual=dict(l.split('=',1) for l in (docs/'Variables.txt').read_text().splitlines() if '=' in l)
expected=json.loads((Path(__file__).resolve().parents[1]/'configs/ultra.json').read_text())['settings']
errors={k:[actual.get(k),v] for k,v in expected.items() if actual.get(k)!=v and k not in ['enablefunctionkeys','frameratecap','vsync']}
if errors:raise SystemExit(f'Ultra/native settings mismatch: {errors}')
(out/'Variables.before.txt').write_bytes((docs/'Variables.txt').read_bytes())
log=(out/'xctrace.log').open('w')
focus=subprocess.Popen([str(base/'focus-monitor'),str(a.pid),str(a.seconds+20),str(out/'focus.jsonl')],stdout=log,stderr=log)
time.sleep(2)
record=subprocess.Popen(['xcrun','xctrace','record','--instrument',a.instrument,'--attach',str(a.pid),'--time-limit',f'{a.seconds}s','--no-prompt','--output',str(out/'metal.trace')],stdout=log,stderr=log)
until=time.monotonic()+30
while 'Ctrl-C to stop' not in (out/'xctrace.log').read_text():
    if record.poll() is not None or time.monotonic()>until:raise SystemExit('Recorder did not become ready; replay left paused')
    time.sleep(.2)
time.sleep(1)
camera=None
if a.hold_center:
    camera=subprocess.Popen([str(base/'replay-control-native'),str(a.pid),'hold-center',str(a.seconds)],stdout=log,stderr=log)
    time.sleep(1.5)
before=time.time()
result=subprocess.run([str(base/'replay-control-native'),str(a.pid),'pause'],text=True,capture_output=True,check=True)
after=time.time()
metadata={'pid':a.pid,'trace_pid':record.pid,'seconds':a.seconds,'camera':'held Space on original replay player' if a.hold_center else 'prepared camera','play_command_wall_before':before,'play_command_wall_after':after,'play_output':result.stdout.strip(),'ultra_config_matches':True,'requires_screenshot_resolution_verification':True,'acceptance_valid':False}
(out/'capture.json').write_text(json.dumps(metadata,indent=2)+'\n');print(out,flush=True)
record.wait();focus.wait();log.close()
if record.returncode:raise SystemExit(record.returncode)
subprocess.run(['xcrun','xctrace','export','--input',str(out/'metal.trace'),'--xpath',f'/trace-toc/run/data/table[@schema="{a.schema}"]','--output',str(out/'presented.xml')],check=True)
mode=['--actual-presentation-time'] if a.schema=='ca-client-presented-handler' else []
if a.schema=='display-surface-swap':mode+=['--foreground-log',str(out/'focus.jsonl')]
subprocess.run(['python3',str(Path(__file__).with_name('analyze-presented-frames.py')),str(out/'presented.xml'),'--pid',str(a.pid),'--stage','steady-replay-after-warm-seek',*mode,'--trim-start','7','--trim-end','1','--output',str(out/'metrics.json')],check=True)
