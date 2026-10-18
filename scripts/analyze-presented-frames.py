#!/usr/bin/env python3
"""Summarize actual display swaps, or explicitly labelled callback diagnostics."""
import argparse
import json
import math
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('xml', type=Path)
parser.add_argument('--pid', type=int, required=True)
parser.add_argument('--stage', required=True)
parser.add_argument('--output', type=Path)
parser.add_argument('--trim-start', type=float, default=0)
parser.add_argument('--trim-end', type=float, default=0)
args = parser.parse_args()
root = ET.parse(args.xml).getroot()
definitions = {e.attrib['id']: e for e in root.iter() if 'id' in e.attrib}


def resolve(e):
    return definitions[e.attrib['ref']] if 'ref' in e.attrib else e


def walk(e):
    e = resolve(e)
    yield e
    for child in e:
        yield from walk(child)


def pid(e):
    for child in walk(e):
        if child.tag == 'pid':
            return int(child.text)
    return None


frames = []
schema = root.find('.//schema').attrib['name']
display_swaps = schema == 'displayed-surfaces-interval'
if schema not in ('displayed-surfaces-interval', 'ca-client-presented-handler'):
    raise SystemExit(f'Unsupported frame schema: {schema}')
for row in root.iter('row'):
    owner = row[9] if display_swaps else row[-1]
    if pid(owner) != args.pid:
        continue
    timestamp = resolve(row[0])
    frames.append(int(timestamp.text))
frames = sorted(set(frames))
if frames:
    first, last = frames[0], frames[-1]
    frames = [t for t in frames if first + args.trim_start * 1e9 <= t <= last - args.trim_end * 1e9]
intervals = [(b - a) / 1e6 for a, b in zip(frames, frames[1:]) if b > a]
if not intervals:
    raise SystemExit('No matching frame intervals in trace.')
ordered = sorted(intervals)


def percentile(p):
    position = p * (len(ordered) - 1)
    lo = int(position)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


worst = ordered[-max(1, math.ceil(len(ordered) * .01)):]
result = dict(pid=args.pid, stage=args.stage, source=str(args.xml),
              metric=('Displayed surface swap timestamps' if display_swaps else
                      'CAMetalDrawable callback timestamps; includes coalesced callbacks, not display FPS'),
              schema=schema, trim_start_seconds=args.trim_start, trim_end_seconds=args.trim_end,
              frame_count=len(frames), sample_seconds=sum(intervals) / 1000,
              average_fps=1000 / statistics.mean(intervals),
              one_percent_low_fps=1000 / statistics.mean(worst),
              p50_ms=percentile(.5), p95_ms=percentile(.95), p99_ms=percentile(.99),
              max_ms=max(intervals), frames_over_25_ms=sum(x > 25 for x in intervals),
              frames_over_33_3_ms=sum(x > 100 / 3 for x in intervals),
              frames_over_50_ms=sum(x > 50 for x in intervals))
if args.output:
    args.output.write_text(json.dumps(result, indent=2))
    args.output.with_suffix('.csv').write_text('frame,interval_ms\n' + ''.join(
        f'{i},{value:.6f}\n' for i, value in enumerate(intervals, 1)))
print(json.dumps(result, indent=2))
