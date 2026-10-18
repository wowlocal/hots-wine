#!/usr/bin/env python3
"""Cross-check global swaps against game presentation times using trace clock metadata."""
import argparse,bisect,json
from fractions import Fraction
from pathlib import Path
import xml.etree.ElementTree as E

p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--pid',required=True,type=int);p.add_argument('--output',type=Path);a=p.parse_args()
def rows(name):
    root=E.parse(a.folder/name).getroot();defs={e.attrib['id']:e for e in root.iter()if'id'in e.attrib}
    def resolve(e):return defs[e.attrib['ref']]if'ref'in e.attrib else e
    return [[resolve(e)for e in row]for row in root.iter('row')],resolve
info,res=rows('time-info.xml');epoch=int(info[0][1].text);num,den=[int(res(x).text)for x in info[0][3]]
data,res=rows('app-presented.xml');app=[]
for row in data:
    if row[2].text!='2' or not any(e.tag=='pid' and e.text==str(a.pid)for e in row[-1].iter()):continue
    raw=int(row[3].text)
    # Instruments interpreted an absolute ns value as mach ticks, then subtracted
    # the run epoch. Undo both transformations, without fitting an arbitrary offset.
    app.append(float(Fraction(raw*den,num)+epoch-Fraction(epoch*num,den)))
app=sorted(set(app));raw,_=rows('presented.xml');swaps=sorted(set(int(row[0].text)for row in raw))
if not app or not swaps:raise SystemExit('Missing presentation or display events')
lo=max(app[0],swaps[0])+250_000_000;hi=min(app[-1],swaps[-1])-250_000_000
app=[x for x in app if lo<=x<=hi];swaps=[x for x in swaps if lo<=x<=hi]
def nearest(x,series):
    i=bisect.bisect_left(series,x);return min(abs(x-y)for y in series[max(0,i-1):i+1])
errors=[nearest(x,swaps)for x in app];reverse=[nearest(x,app)for x in swaps]
result=dict(valid=bool(errors and reverse)and max(errors)<=250 and max(reverse)<=250,
            application_presentations=len(app),display_swaps=len(swaps),
            max_app_to_swap_error_ns=max(errors,default=None),max_swap_to_app_error_ns=max(reverse,default=None),
            timebase=f'{num}/{den}',boundary_trim_seconds=.25,
            method='Absolute trace epoch correction; no fitted phase or rate')
if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(0 if result['valid']else 1)
