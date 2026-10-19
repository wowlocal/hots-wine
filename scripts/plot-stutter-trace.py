#!/usr/bin/env python3
"""Plot the sanitized one-second frame counts, without opening a GUI."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1] / 'results/stutter-trace-2026-10-19'
groups = [
    ('Launch 1', 'launch-01', [
        ('light-before', 'Initial light measurement', '#0072B2', '-'),
        ('diagnostic', 'Interrupted profiler recording', '#777777', '--'),
        ('diagnostic-api', 'Completed system trace', '#D55E00', '-'),
        ('light-api-after', 'Final light measurement', '#009E73', ':')]),
    ('Launch 2', 'launch-02', [
        ('light-before', 'Light measurement before trace', '#0072B2', '-'),
        ('diagnostic', 'Targeted game trace', '#D55E00', '-'),
        ('light-after', 'Light measurement after trace', '#009E73', ':')]),
]
groups = [g for g in groups if (root / g[1]).exists()]
fig, axes = plt.subplots(len(groups), 1, figsize=(10, 4.5 * len(groups)),
                         squeeze=False, layout='constrained')
for axis, (title, folder, cases) in zip(axes[:, 0], groups):
    for name, label, color, style in cases:
        path = root / folder / (name + '.json')
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        counts = data['fps_per_second']
        assert len(counts) == 25 and sum(counts) == data['frame_count']
        axis.step(range(26), counts + counts[-1:], where='post', color=color,
                  linestyle=style, linewidth=1.8,
                  label=f"{label} ({data['average_fps']:.2f} average)")
    axis.set(title=title, xlim=(0, 25), ylim=(40, 125),
             xlabel='Seconds in the fixed 25-second window',
             ylabel='Frames shown per second')
    axis.set_xticks(range(0, 26, 5))
    axis.set_yticks([40, 60, 80, 100, 120])
    axis.grid(alpha=.2)
    axis.legend(fontsize=8, loc='upper center', bbox_to_anchor=(.5, -.24), ncol=2)
fig.suptitle('HotS replay at 13:15 · MSync enabled · 3456 × 2234 · Ultra')
fig.savefig(root / 'fps-timeline.png', dpi=160,
            metadata={'Software': 'HotS Wine diagnostic'})
fig.savefig(root / 'fps-timeline.svg',
            metadata={'Creator': 'HotS Wine diagnostic', 'Date': None})
svg = root / 'fps-timeline.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
