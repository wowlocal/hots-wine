#!/usr/bin/env python3
"""Summarize the four public ABBA launches; verify rounded interval CSVs offline."""
import argparse
import csv
import json
import math
from pathlib import Path
import statistics


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    conditions = json.loads((args.results / 'conditions.json').read_text())
    clock_hz = conditions['collection']['native_mach_clock_hz']
    require(type(clock_hz) is int and clock_hz > 0 and clock_hz % 80 == 0,
            'Unsupported native clock for threshold reconstruction')
    rows = []
    for launch, flag in enumerate([1, 0, 0, 1], 1):
        directory = args.results / f'arm-{launch:02d}-msync-{flag}'
        for seconds in [405, 795, 885]:
            data = json.loads((directory / f'{seconds}.json').read_text())
            expected_clock = f'{seconds // 60:02d}:{seconds % 60:02d}'
            require(data['msync'] == flag and data['prepared_hud_clock'] == expected_clock,
                    'Wrong mode or replay section')
            require(data['sample_seconds'] == 25 and data['onscreen_layer_count'] == 1
                    and set(data['drawable_sizes']) == {'3456x2234'}
                    and sum(data['drawable_sizes'].values()) == data['frame_count'],
                    'Unexpected sample or native drawable')
            require(data['replay_progression_valid'] and data['paused_after_clock_stable']
                    and data['foreground']['max_gap_ms'] <= 350, 'Invalid replay/focus evidence')
            require(data.get('camera_helper_exit_status') == 0
                    or data.get('camera_endpoints_verified') is True, 'Missing camera evidence')
            with (directory / f'{seconds}.csv').open() as file:
                records = list(csv.DictReader(file))
            require([int(r['frame']) for r in records] == list(range(len(records))),
                    'Non-sequential interval rows')
            intervals = [float(r['interval_ms']) for r in records]
            require(intervals and all(math.isfinite(x) and x > 0 for x in intervals),
                    'Invalid frame intervals')
            require(len(intervals) in [data['frame_count'], data['frame_count'] + 1],
                    'Interval count does not match selected frame count')
            require(25000 - .01 <= sum(intervals) <= 25000 + 2 * max(intervals) + .01,
                    'Complete boundary intervals do not cover about 25 seconds')
            ticks = [round(x * clock_hz / 1000) for x in intervals]
            require(max(abs(x * clock_hz / 1000 - tick)
                        for x, tick in zip(intervals, ticks)) < .025,
                    'Intervals do not fit the measured native clock within CSV rounding')
            ordered = sorted(intervals)
            tail = ordered[-max(1, math.ceil(len(ordered) * .01)):]
            position = .99 * (len(ordered) - 1)
            lo, hi = math.floor(position), math.ceil(position)
            p99 = ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)
            for key, observed in [('one_percent_low_fps', 1000 / statistics.mean(tail)),
                                  ('p99_ms', p99), ('max_ms', max(intervals))]:
                require(abs(data[key] - observed) < .001, f'CSV mismatch: {key}')
            require(abs(data['average_fps'] - data['frame_count'] / 25) < 1e-9,
                    'Frame count/FPS mismatch')
            rows.append(dict(launch=launch, msync=flag, prepared_clock=expected_clock,
                             sample_seconds=data['sample_seconds'], frame_count=data['frame_count'],
                             average_fps=data['average_fps'],
                             one_percent_low_fps=data['one_percent_low_fps'],
                             p99_ms=data['p99_ms'], max_ms=data['max_ms'],
                             intervals_over_12_5_ms=sum(tick > clock_hz // 80 for tick in ticks),
                             intervals_over_25_ms=sum(tick > clock_hz // 40 for tick in ticks),
                             legacy_float_threshold_counts=dict(
                                 over_12_5_ms=data['missed_refresh_intervals'],
                                 over_25_ms=data['frames_over_25_ms']),
                             numeric_120_pass=data['numeric_120_pass']))
    groups = []
    for flag in [1, 0]:
        selected = [row for row in rows if row['msync'] == flag]
        groups.append(dict(msync=flag, independent_launches=len({x['launch'] for x in selected}),
                           windows=len(selected), sample_seconds=sum(x['sample_seconds'] for x in selected),
                           average_fps=sum(x['frame_count'] for x in selected) / sum(x['sample_seconds'] for x in selected),
                           average_fps_range=[min(x['average_fps'] for x in selected),
                                              max(x['average_fps'] for x in selected)],
                           one_percent_low_fps_range=[min(x['one_percent_low_fps'] for x in selected),
                                                      max(x['one_percent_low_fps'] for x in selected)],
                           worst_interval_ms=max(x['max_ms'] for x in selected),
                           intervals_over_12_5_ms=sum(x['intervals_over_12_5_ms'] for x in selected),
                           intervals_over_25_ms=sum(x['intervals_over_25_ms'] for x in selected),
                           strict_pass_windows=sum(x['numeric_120_pass'] for x in selected)))
    result = dict(protocol='ABBA, three fixed 25-second windows per launch, Metal cap120',
                  inference_limit='Two independent launches per mode; sections within a launch are not independent replicates. Descriptive comparison, no significance claim or uncapped headroom measurement.',
                  refresh_limit='Intervals >12.5ms are timing events; display mode was preserved, so they do not establish missed physical refreshes under variable refresh.',
                  csv_validation='1%low,p99,max recomputed from rounded CSV; count/duration checked. Threshold counts reconstructed on the measured native Mach clock to remove float artifacts at exact thresholds.',
                  native_mach_clock_hz=clock_hz,
                  groups=groups, rows=rows)
    with args.output.open('x') as file:
        file.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(groups, indent=2))


if __name__ == '__main__':
    main()
