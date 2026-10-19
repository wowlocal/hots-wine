#!/usr/bin/env python3
"""Offline Metal presentedTime metrics with monotonic foreground validation.

Read only after the game exits. A calibration capture can additionally compare
the probe to Frame Lifetimes' display swaps without fitting clocks or offsets.
"""
import argparse
import bisect
from collections import Counter
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import statistics
import struct
import xml.etree.ElementTree as ET

HEADER = struct.Struct('<8sIIQQIIQdII')
RECORD = struct.Struct('<dQQQIIQQ')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def foreground(path, pid, start, end):
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    require(rows and all(y['host_ns'] > x['host_ns'] for x, y in zip(rows, rows[1:])), 'Invalid monotonic focus log')
    samples = [x for x in rows if x['kind'] == 'sample']
    clocks = [x['host_ns'] for x in samples]
    left = bisect.bisect_right(clocks, start) - 1
    right = bisect.bisect_left(clocks, end)
    require(left >= 0 and right < len(samples), 'Focus log does not cover fixed window')
    samples = samples[left:right + 1]
    gap = max((y['host_ns'] - x['host_ns']) / 1e6 for x, y in zip(samples, samples[1:]))
    require(gap <= 350, 'Foreground sampler gap exceeded 350 ms')
    events = [x for x in rows if x['kind'] == 'activation' and start <= x['host_ns'] <= end]
    require(all(x['frontmost_pid'] == pid and x['expected_pid'] == pid and x['active']
                for x in samples + events), 'Lost game foreground')
    return dict(samples=len(samples), activation_events=len(events), max_gap_ms=gap)


class Table:
    def __init__(self, path, name):
        root = ET.parse(path).getroot()
        schemas = root.findall('.//schema')
        require(len(schemas) == 1 and schemas[0].get('name') == name, 'Wrong XML schema')
        self.columns = {c.findtext('mnemonic'): (i, c.findtext('engineering-type'))
                        for i, c in enumerate(schemas[0].findall('col'))}
        self.defs = {e.get('id'): e for e in root.iter() if e.get('id')}
        self.rows = list(root.iter('row'))

    def resolve(self, element):
        while element.get('ref'):
            element = self.defs[element.get('ref')]
        return element

    def value(self, row, name, kind):
        index, observed = self.columns[name]
        require(observed == kind, f'Wrong XML type for {name}')
        return self.resolve(row[index])


def nearest(value, series):
    i = bisect.bisect_left(series, value)
    return min(abs(value - x) for x in series[max(0, i - 1):i + 1])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary', type=Path)
    p.add_argument('--pid', type=int, required=True)
    p.add_argument('--focus', type=Path, required=True)
    p.add_argument('--anchor', type=Path, required=True,
                   help='Exclusive pre-run file containing pid and play_command_after_host_ns')
    p.add_argument('--swaps', type=Path)
    p.add_argument('--time-info', type=Path)
    p.add_argument('--display', default='Built-In Display')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    anchor = json.loads(a.anchor.read_text())
    require(anchor['pid'] == a.pid, 'Wrong anchor PID')
    require(type(anchor['play_command_after_host_ns']) is int, 'Anchor must contain integer host ns')
    a.start_host_ns = anchor['play_command_after_host_ns'] + 3_000_000_000
    a.end_host_ns = anchor['play_command_after_host_ns'] + 28_000_000_000
    try:
        os.kill(a.pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError('Game must exit before reading the mmap file')
    require(a.start_host_ns < a.end_host_ns, 'Invalid fixed monotonic window')
    with a.binary.open('rb') as f:
        magic, version, size, capacity, count, numer, denom, producer_start_mach, _, pid, _ = HEADER.unpack(f.read(HEADER.size))
        require(magic == b'HOTSMTL1' and version == 3 and size == RECORD.size, 'Unsupported probe format')
        require(pid == a.pid and count <= capacity, 'Wrong PID or overflowing probe')
        acquired_count, = struct.unpack('<Q', f.read(8))
        require(acquired_count >= count, 'Handler count exceeds acquired drawables')
        f.seek(4096)
        data = f.read(count * size)
    require(len(data) == count * size, 'Truncated probe')
    ratio = Fraction(numer, denom)
    require(producer_start_mach * ratio < anchor['play_command_after_host_ns'], 'Anchor predates producer')
    start_ns, end_ns = a.start_host_ns, a.end_host_ns
    times, sizes, pending, layers, presented_rows = [], Counter(), [], set(), []
    for i, (presented, callback, drawable, acquired, width, height, layer, committed) in enumerate(RECORD.iter_unpack(data)):
        if committed != i + 1:
            pending.append(i)
            continue
        if presented <= 0:
            continue
        require(math.isfinite(presented), 'Invalid presentedTime')
        time_ns = presented * 1e9
        times.append(time_ns)
        presented_rows.append((time_ns, layer, width, height))
        if start_ns <= time_ns < end_ns:
            sizes[f'{width}x{height}'] += 1
            layers.add(layer)
    times = sorted(set(times))
    require(times and times[0] < start_ns and times[-1] > end_ns, 'Frames do not cover fixed window')
    if pending:
        # An abrupt exit can cut the final callbacks short. Only a contiguous
        # suffix entirely after the sample can be ignored, never an interior gap.
        require(pending == list(range(pending[0], count)) and len(pending) <= 8
                and times[-1] > end_ns + 1e9, 'Uncommitted interior probe records')
    require(sizes and set(sizes) == {'3456x2234'}, 'Unexpected displayed drawable dimensions')
    require(len(layers) == 1 and 0 not in layers, 'Expected one onscreen Metal layer')
    layer = next(iter(layers))
    layer_rows = sorted(r for r in presented_rows if r[1] == layer)
    times = sorted(set(r[0] for r in layer_rows))
    left = bisect.bisect_right(times, start_ns) - 1
    right = bisect.bisect_left(times, end_ns)
    require(left >= 0 and right < len(times), 'Selected layer does not cover fixed window')
    boundary_times = {times[left], times[right]}
    require(all((r[2], r[3]) == (3456, 2234) for r in layer_rows if r[0] in boundary_times),
            'Unexpected boundary drawable dimensions')
    focus = foreground(a.focus, pid, start_ns, end_ns)
    selected = [t for t in times if start_ns <= t < end_ns]
    intervals = [(y-x)/1e6 for x, y in zip(times, times[1:]) if x < end_ns and y > start_ns]
    require(intervals, 'No frame intervals')
    ordered = sorted(intervals)
    def percentile(q):
        pos = q * (len(ordered)-1); lo = math.floor(pos); hi = math.ceil(pos)
        return ordered[lo] + (ordered[hi]-ordered[lo]) * (pos-lo)
    worst = ordered[-max(1, math.ceil(len(ordered)*.01)):]
    seconds = float(end_ns-start_ns)/1e9
    result = dict(pid=pid, metric='MTLDrawable.presentedTime, actual onscreen host time',
                  fixed_host_ns_window=[start_ns, end_ns], sample_seconds=seconds,
                  timebase=f'{numer}/{denom}', drawable_sizes=dict(sizes), frame_count=len(selected),
                  onscreen_layer_count=len(layers), acquired_drawables=acquired_count,
                  handled_drawables=count,
                  foreground=focus, average_fps=len(selected)/seconds,
                  one_percent_low_fps=1000/statistics.mean(worst),
                  p50_ms=percentile(.5), p95_ms=percentile(.95), p99_ms=percentile(.99), max_ms=max(intervals),
                  missed_refresh_intervals=sum(x > 12.5 for x in intervals),
                  cadence_120_fraction=sum(abs(x-1000/120) <= .2 for x in intervals)/len(intervals),
                  frames_over_25_ms=sum(x > 25 for x in intervals),
                  frames_over_33_3_ms=sum(x > 100/3 for x in intervals),
                  frames_over_50_ms=sum(x > 50 for x in intervals),
                  interval_policy='Complete intervals intersecting a fixed window; includes boundary stalls')
    result['numeric_120_rule'] = '>=20s,119.5..120.5avg,1%low>=115,p99<=9ms,max<=12.5ms,>=99.9% intervals within8.333+/-0.2ms'
    result['numeric_120_pass'] = (seconds >= 20 and 119.5 <= result['average_fps'] <= 120.5
        and result['one_percent_low_fps'] >= 115 and result['p99_ms'] <= 9
        and result['max_ms'] <= 12.5 and result['cadence_120_fraction'] >= .999)
    if a.swaps or a.time_info:
        require(a.swaps and a.time_info, 'Both swap and clock XMLs required')
        info = Table(a.time_info, 'time-info'); require(len(info.rows) == 1, 'Expected one trace clock')
        row = info.rows[0]
        epoch = int(info.value(row, 'mabs-epoch', 'mach-absolute-time').text)
        tb = info.value(row, 'timebase-info', 'mach-timebase-info')
        require(len(tb) == 2, 'Expected numerator and denominator')
        trace_ratio = Fraction(*(int(info.resolve(x).text) for x in tb))
        # Rosetta reports a 1/1 timebase while native arm64 reports 125/3 on
        # this Mac. Normalize each process' ticks separately to host ns.
        swap_table = Table(a.swaps, 'display-surface-swap')
        swaps = sorted(set(int(swap_table.value(row, 'timestamp', 'start-time').text) + epoch*trace_ratio
            for row in swap_table.rows if swap_table.value(row, 'display-name', 'display-name').text == a.display))
        shown = [t for t in swaps if start_ns <= t < end_ns]
        require(shown and swaps[0] < start_ns and swaps[-1] > end_ns, 'Display swaps do not cover fixed window')
        forward = [nearest(t, swaps) for t in selected]; reverse = [nearest(t, times) for t in shown]
        max_forward, max_reverse = float(max(forward)), float(max(reverse))
        result['display_crosscheck'] = dict(valid=max_forward<=250 and max_reverse<=250,
            max_probe_to_swap_error_ns=max_forward, max_swap_to_probe_error_ns=max_reverse,
            probe_frames=len(selected), display_swaps=len(shown), display=a.display,
            method='Absolute mach epoch, both directions, no fitted offset or rate')
        require(result['display_crosscheck']['valid'], 'Display/probe timestamp mismatch')
    with a.output.open('x') as output:
        output.write(json.dumps(result, indent=2)+'\n')
    with a.output.with_suffix('.csv').open('x') as output:
        output.write('frame,interval_ms\n'+''.join(f'{i},{x:.6f}\n' for i,x in enumerate(intervals)))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
