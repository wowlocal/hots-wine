#!/usr/bin/env python3
"""Export private v3 probe timings after existing fixed-window qualification.

nextDrawable's recorded timestamp is AFTER it returns. These timings cannot
separate time blocked inside nextDrawable from CPU, GPU, or compositor delays.
No source binary, paths, drawable IDs, or authentication data are exported.
"""
import argparse
import bisect
import csv
import json
import math
import os
from pathlib import Path
import statistics
import struct
import sys

HEADER = struct.Struct('<8sIIQQIIQdII')
RECORD = struct.Struct('<dQQQIIQQ')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def percentile(values, fraction):
    values = sorted(values)
    position = fraction * (len(values) - 1)
    low, high = math.floor(position), math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--qualification', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--presentation-clock-hz', type=int, required=True,
                        help='Independently measured native display clock; 24000000 on this test Mac')
    args = parser.parse_args()
    require(args.presentation_clock_hz > 0, 'Invalid display clock')
    require(args.output.suffix == '.json', 'Output must end in .json')
    qualified = json.loads(args.qualification.read_text())
    pid = qualified['pid']
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError('Game must exit before reading the recording')
    start, end = qualified['fixed_host_ns_window']
    require(qualified['onscreen_layer_count'] == 1 and
            set(qualified['drawable_sizes']) == {'3456x2234'}, 'Unqualified drawable geometry')
    require(end - start == 25_000_000_000, 'Expected the qualified fixed 25-second window')
    with args.binary.open('rb') as file:
        magic, version, size, capacity, count, numer, denom, _, _, observed_pid, _ = HEADER.unpack(file.read(HEADER.size))
        require(magic == b'HOTSMTL1' and version == 3 and size == RECORD.size,
                'Expected probe v3')
        require(observed_pid == pid and count <= capacity and numer > 0 and denom > 0,
                'Wrong producer or corrupt header')
        require(qualified['timebase'] == f'{numer}/{denom}', 'Qualification timebase differs')
        require(qualified['handled_drawables'] == count, 'Qualification does not match this recording')
        file.seek(4096)
        data = file.read(size * count)
    require(len(data) == size * count, 'Truncated recording')
    rows, uncommitted, unpresented = [], [], []
    for index, record in enumerate(RECORD.iter_unpack(data)):
        shown, callback, _, acquired, width, height, layer, committed = record
        if committed != index + 1:
            uncommitted.append(index)
            continue
        if shown <= 0:
            unpresented.append((acquired * numer / denom, layer))
            continue
        require(math.isfinite(shown), 'Invalid presentation timestamp')
        rows.append((shown * 1e9, acquired * numer / denom,
                     callback * numer / denom, width, height, layer))
    selected_layers = {r[5] for r in rows if start <= r[0] < end}
    require(len(selected_layers) == 1 and 0 not in selected_layers, 'Expected one onscreen layer')
    rows = sorted(r for r in rows if r[5] in selected_layers)
    times = [r[0] for r in rows]
    require(all(y > x for x, y in zip(times, times[1:])), 'Duplicate display timestamps')
    left, right = bisect.bisect_right(times, start) - 1, bisect.bisect_left(times, end)
    require(left >= 0 and right < len(rows), 'Missing window boundary frames')
    selected = [r for r in rows if start <= r[0] < end]
    if uncommitted:
        require(uncommitted == list(range(uncommitted[0], count)) and
                len(uncommitted) <= 8 and times[-1] > end + 1e9,
                'Uncommitted records are not a harmless final suffix')
    require(len(selected) == qualified['frame_count'] and
            all(r[3:5] == (3456, 2234) for r in rows[left:right + 1]),
            'Qualification and recording disagree')
    require(all(r[0] >= r[1] and r[2] >= r[0] - 250 for r in rows[left:right + 1]),
            'Acquisition, presentation and callback clocks are inconsistent')
    grid_error = max(abs(r[0] / 1e9 * args.presentation_clock_hz -
                         round(r[0] / 1e9 * args.presentation_clock_hz))
                     for r in rows[left:right + 1])
    require(grid_error < .05, 'Presentation timestamps do not lie on the specified native clock')
    pairs = list(zip(rows[left:right], rows[left + 1:right + 1]))
    intervals = [(b[0] - a[0]) / 1e6 for a, b in pairs]
    ticks = [round(value * args.presentation_clock_hz / 1000) for value in intervals]
    long_count = sum(tick * 80 > args.presentation_clock_hz for tick in ticks)
    acquisitions = [(b[1] - a[1]) / 1e6 for a, b in pairs]
    latencies = [(r[0] - r[1]) / 1e6 for r in selected]
    callbacks = [(r[2] - r[0]) / 1e6 for r in selected]
    worst = sorted(intervals)[-max(1, math.ceil(len(intervals) * .01)):]
    require(abs(1000 / statistics.mean(worst) - qualified['one_percent_low_fps']) < .001,
            'Presentation intervals do not reproduce qualification')
    result = {
        'sample_seconds': 25, 'frame_count': len(selected), 'average_fps': len(selected) / 25,
        'one_percent_low_fps': 1000 / statistics.mean(worst),
        'p99_ms': percentile(intervals, .99), 'max_ms': max(intervals),
        'presentation_intervals_over_12_5_ms': long_count,
        'fps_per_second': [sum(start + i * 1e9 <= r[0] < start + (i + 1) * 1e9
                               for r in selected) for i in range(25)],
        'shown_drawable_acquisition_gaps_over_12_5_ms': sum(x > 12.5 for x in acquisitions),
        'acquisition_reordering_count': sum(x < 0 for x in acquisitions),
        'post_next_drawable_to_present_ms': dict(min=min(latencies), median=statistics.median(latencies),
                                               p99=percentile(latencies, .99), max=max(latencies)),
        'callback_after_present_p99_ms': percentile(callbacks, .99),
        'presentation_clock_hz': args.presentation_clock_hz,
        'max_presentation_clock_grid_error_ticks': grid_error,
        'uncommitted_final_records_excluded': len(uncommitted),
        'observed_unpresented_records_in_acquisition_span': sum(
            rows[left][1] <= acquired <= rows[right][1] and layer in selected_layers
            for acquired, layer in unpresented),
        'interval_histogram_nominal_120_periods': {
            'at_most_1_5': sum(tick * 240 <= 3 * args.presentation_clock_hz for tick in ticks),
            'over_1_5_at_most_2_5': sum(3 * args.presentation_clock_hz < tick * 240 <=
                                       5 * args.presentation_clock_hz for tick in ticks),
            'over_2_5_at_most_3_5': sum(5 * args.presentation_clock_hz < tick * 240 <=
                                       7 * args.presentation_clock_hz for tick in ticks),
            'over_3_5': sum(tick * 240 > 7 * args.presentation_clock_hz for tick in ticks),
        },
        'interval_policy': 'Complete presentation intervals intersecting the fixed window, including boundaries',
        'limitation': 'Post-nextDrawable gaps are between shown drawables, not all acquisitions; no CPU/GPU/compositor cause attribution. Histogram uses a nominal 120 Hz period, not a verified fixed refresh rate.',
    }
    require(not args.output.exists() and not args.output.with_suffix('.csv').exists(),
            'Output already exists')
    with args.output.open('x') as file:
        file.write(json.dumps(result, indent=2) + '\n')
    with args.output.with_suffix('.csv').open('x', newline='') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerow(['interval_end_seconds', 'presentation_interval_ms',
                         'shown_drawable_acquisition_gap_ms', 'post_next_drawable_to_present_ms',
                         'callback_after_present_ms', 'end_inside_fixed_window'])
        for previous, current in pairs:
            writer.writerow([f'{(current[0] - start) / 1e9:.9f}',
                             f'{(current[0] - previous[0]) / 1e6:.6f}',
                             f'{(current[1] - previous[1]) / 1e6:.6f}',
                             f'{(current[0] - current[1]) / 1e6:.6f}',
                             f'{(current[2] - current[0]) / 1e6:.6f}',
                             int(start <= current[0] < end)])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except OSError as error:
        sys.exit(f'Diagnostic file/process access failed ({type(error).__name__})')
    except (KeyError, struct.error):
        sys.exit('Invalid diagnostic metadata or recording')
    except ValueError as error:
        sys.exit(str(error))
