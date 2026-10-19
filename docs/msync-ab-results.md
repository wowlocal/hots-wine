# HotS MSync comparison, 2026-10-19

**Retain MSync enabled for this tested setup. It helps overall, but does not
eliminate stutter or establish uninterrupted 120 FPS.**

Four independent launches ran in **on → off → off → on** order, with three
25-second replay windows per launch: 300 seconds total, 150 per mode.
Both launches with MSync had higher overall average FPS than either launch
without it. However, the final enabled launch also had a bad 13:15 section.

| Mode | Average FPS across 150 s | Intervals >12.5 ms | Windows passing the strict 120 rule |
|---|---:|---:|---:|
| MSync enabled | 119.18 | 118 | 1/6 |
| MSync disabled | 113.47 | 971 | 0/6 |

These are descriptive results from **two independent launches per mode**.
The three sections within a launch are dependent observations. This is one
ABBA block, without a statistical significance or universal causal claim.
The long-interval count is roughly eight times lower with MSync over equal
sample durations. Per-launch counts were 2 and 116 with MSync, versus 384 and
587 without it; 110 of the 118 enabled-mode events came from the final 13:15
window. It counts timing events, not the number of lost physical refreshes.

Each section below is **average FPS / 1% low FPS**. The 1% low is the reciprocal
of the mean of the slowest 1% of complete presentation intervals.

| Launch | MSync | 06:45 | 13:15 | 14:45 | Launch average FPS |
|---|---|---:|---:|---:|---:|
| 1 | enabled | 119.96 / 116.13 | 120.00 / 120.00 | 119.88 / 109.09 | 119.95 |
| 2 | disabled | 116.24 / 60.00 | 109.00 / 58.95 | 119.32 / 76.60 | 114.85 |
| 3 | disabled | 104.96 / 58.91 | 118.64 / 60.00 | 112.68 / 57.52 | 112.09 |
| 4 | enabled | 119.96 / 116.13 | 115.52 / 58.49 | 119.76 / 100.00 | 118.41 |

Five of six windows without MSync had 1% lows of 57.52–60 FPS; the other was
76.60 FPS. Enabling it again improved the first and third sections relative to
the preceding disabled launch, but did **not** restore the second:
its final 1% low was 58.49 FPS. MSync is therefore not a complete explanation
for the stutter. The longest individual interval was also higher with MSync:
29.17 ms versus 25.00 ms. The conclusion concerns the overall average and
frequency of long intervals, rather than every individual metric.

All 12 samples passed the existing native-drawable, single-onscreen-layer,
monotonic-window and continuous-foreground checks. The replay advanced by
30–31 HUD seconds per capture and was stably paused afterwards. Settings were
**3456×2234, game-generated Ultra, VSync off, game cap disabled, DXMT Metal cap
120**, on an M5 Max with 18 CPU cores, 40 GPU cores and 128 GB RAM. The runtime
was the free Wine engine used by Waypoint 0.6.0, with DXMT 0.80.

The same baseline prefix was cloned to the same private pathname for every
launch. Its wineserver was stopped and awaited between modes. MSync was set
consistently for all clients. ESync was forced off. FSync was unset in the
game environment and forced off for server bootstrap and control helpers.
This differs from the protocol's explicit FSync=0 instruction for every client;
it was the same in both arms. Enabled launches
acknowledged MSync startup; disabled launches did not bootstrap it. Production
preferences and the game executable had unchanged before/after hashes.

Every launch warmed the replay from the pregame countdown through at least
15:10, following Kerrigan, and preflighted all three exact section positions.
Screenshots, OCR and seeking occurred outside timed samples. The calibrated
v3 Metal presentedTime recorder was parsed after game exit. Before every
launch, AC power and no recorded thermal/performance warnings were observed;
there was no continuous temperature or frequency telemetry.

Display mode and Retina scaling were preserved; variable refresh was not
independently disabled. The 120 cap masks uncapped throughput. This is not a
full-match or cold-cache qualification. The first two enabled samples did not
retain the camera helper exit status; their start/end images were manually
checked for the same centered Kerrigan. Later samples require helper exit 0.

A discarded pilot and a valid observation from an incomplete earlier launch
are retained separately. The incomplete block stopped because coarse timeline
seeking could not reach 13:15; its 119.76 FPS average, 100 FPS 1% low and 25 ms
worst interval were not hidden or reused as paired data. An unfocused startup
and an early readiness check during Authentication collected no timed samples.

The [protocol](msync-ab-protocol.md), [complete summary](../results/msync-ab-2026-10-19/summary.json),
[conditions and artifact hashes](../results/msync-ab-2026-10-19/conditions.json),
and per-section JSON/CSV files are committed. Raw replay, screenshots, focus
logs, binary recordings and prefix/auth data remain private. The
[summary script](../scripts/summarize-msync-results.py) independently recomputes
1% lows, p99 and maximum intervals from the rounded public CSVs. Threshold
counts are reconstructed on the measured 24 MHz native Mach clock: two raw
disabled-mode intervals reported as 25.000000125 ms are exactly 25 ms at native
clock precision and do not count as >25 ms. Original collector summaries are
retained, including their legacy float-threshold counters. This correction does
not change the >12.5 ms counts, FPS, lows or conclusions.

Waypoint already defaults to MSync enabled for HotS, so no production setting
change was needed. All owned test games exited, private tickets were cleared,
disposable prefix clones were removed and the Windows launch lease was released.

Claude Opus 5.5 at xhigh reviewed the protocol, replay controls, summary code
and result table. Its feedback led to explicit progression/camera checks,
launch-level reporting and the corrected threshold counters.
[Review provenance](../results/msync-ab-2026-10-19/review.json) records the actual
model and response hashes.
