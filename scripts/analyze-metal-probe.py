#!/usr/bin/env python3
"""Analyze actual MTLDrawable.presentedTime values, excluding dropped drawables."""
import argparse
import json
import math
from pathlib import Path
import statistics
import struct

HEADER = struct.Struct('<8sIIQQIIQdII')
RECORD = struct.Struct('<dQQQII')


def percentile(values, p):
    ordered = sorted(values)
    pos = p * (len(ordered) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def analyze(path, start_wall=None, end_wall=None, focus=None):
    with path.open('rb') as f:
        magic, version, size, capacity, count, numer, denom, start_mach, wall, pid, _ = HEADER.unpack(f.read(HEADER.size))
        if magic != b'HOTSMTL1' or version != 1 or size != RECORD.size:
            raise ValueError('Unsupported Metal probe file')
        f.seek(4096)
        data = f.read(min(capacity, count) * size)
    host_scale = numer / denom / 1e9
    wall_offset = wall - start_mach * host_scale
    selected = []
    for presented, callback, drawable, acquired, width, height in RECORD.iter_unpack(data):
        if not width or not height:
            continue
        callback_wall = callback * host_scale + wall_offset
        if start_wall is not None and callback_wall < start_wall:
            continue
        if end_wall is not None and callback_wall > end_wall:
            continue
        selected.append((presented, callback * host_scale, drawable, width, height))
    shown = [r for r in selected if r[0] > 0]
    times = sorted(set(r[0] for r in shown))
    intervals = [(b - a) * 1000 for a, b in zip(times, times[1:]) if b > a]
    if not intervals:
        raise ValueError('No displayed frames in selected interval')
    worst = sorted(intervals)[-max(1, math.ceil(len(intervals) * .01)):]
    callback_delay = [(r[1] - r[0]) * 1000 for r in shown]
    clock_sane = -1 < statistics.median(callback_delay) < 1000
    result = dict(metric='MTLDrawable.presentedTime (actual onscreen host time)',
                  source=path.name, pid=pid, raw_records=count,
                  records_over_capacity=max(0, count - capacity),
                  selected_records=len(selected), dropped_drawables=sum(r[0] == 0 for r in selected),
                  displayed_frames=len(times), sample_seconds=sum(intervals) / 1000,
                  average_fps=1000 / statistics.mean(intervals),
                  one_percent_low_fps=1000 / statistics.mean(worst),
                  p50_ms=percentile(intervals, .5), p95_ms=percentile(intervals, .95),
                  p99_ms=percentile(intervals, .99), max_ms=max(intervals),
                  frames_over_9_ms=sum(x > 9 for x in intervals),
                  frames_over_16_67_ms=sum(x > 16.67 for x in intervals),
                  frames_over_25_ms=sum(x > 25 for x in intervals),
                  callback_delay_median_ms=statistics.median(callback_delay),
                  callback_delay_p99_ms=percentile(callback_delay, .99),
                  clocks_consistent=clock_sane,
                  drawable_sizes=sorted(set((r[3], r[4]) for r in shown)),
                  start_wall=start_wall, end_wall=end_wall)
    if focus:
        entries = [json.loads(line) for line in focus.read_text().splitlines()]
        entries = [r for r in entries if (start_wall is None or r['wall'] >= start_wall)
                   and (end_wall is None or r['wall'] <= end_wall)]
        result['focus_samples'] = len(entries)
        result['foreground_fraction'] = sum(r['active'] for r in entries) / len(entries) if entries else 0
    result['numeric_target_pass'] = (result['average_fps'] >= 119 and
                                    result['one_percent_low_fps'] >= 115 and
                                    result['p99_ms'] <= 9 and result['max_ms'] <= 25)
    result['target_completion_proven'] = False  # Requires full quality, stage, repeat and overhead audit.
    return result, intervals


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', type=Path)
    parser.add_argument('--start-wall', type=float)
    parser.add_argument('--end-wall', type=float)
    parser.add_argument('--focus', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result, intervals = analyze(args.binary, args.start_wall, args.end_wall, args.focus)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        args.output.with_suffix('.csv').write_text('frame,interval_ms\n' + ''.join(
            f'{i},{v:.6f}\n' for i, v in enumerate(intervals, 1)))
    print(json.dumps(result, indent=2))
