# Free Wine HotS: native Ultra FPS check

On 19 October 2026, the free Waypoint Wine runtime produced **119.96 FPS
average, 116.13 FPS 1% low and one missed 120 Hz refresh in 25 seconds** at
**3456 × 2234, Ultra**. The longest frame interval was **16.667 ms**.
The final measurement has valid foreground coverage and one onscreen Metal
layer. It does **not** establish uninterrupted 120 FPS or whole-match stability.

## Final measurement

| Metric | Result |
|---|---:|
| Fixed sample duration | 25.000 s |
| Presented frames inside the window | 2,999 |
| Average FPS | 119.96 |
| 1% low FPS | 116.1281 |
| Median / p99 frame interval | 8.333333 / 8.333375 ms |
| Longest frame interval | 16.666625 ms |
| Intervals longer than 12.5 ms | 1 |
| Intervals longer than 25 / 33.3 / 50 ms | 0 / 0 / 0 |
| Intervals within 8.333 ± 0.2 ms | 99.9667% |
| Onscreen Metal layers / drawable size | 1 / 3456 × 2234 |
| Foreground samples / foreign activations | 102 / 0 |
| Largest foreground-sampler gap | 251.65 ms |

Data: [final metrics](../results/free-wine-2026-10-19/final-v3.json),
[frame intervals](../results/free-wine-2026-10-19/final-v3.csv),
[conditions and input hashes](../results/free-wine-2026-10-19/conditions.json).
The interval CSV contains 3,000 complete intervals intersecting the window,
including its boundaries. Its one long interval has zero-based data index
2,731, excluding the header.
The frame count counts presentations inside the window, so these totals differ.
The 1% low is the reciprocal of the mean of the worst 30 intervals, rather
than the reciprocal of a single percentile.

The diagnostic's strict numeric rule requires at least 20 seconds, average
119.5–120.5 FPS, 1% low ≥115 FPS, p99 ≤9 ms, maximum ≤12.5 ms and at least
99.9% of intervals within 8.333 ±0.2 ms. This run **fails the maximum-interval
condition**. It meets the numeric bounds in the older
[repository target](../configs/target.json), whose maximum is 25 ms, but that
target also requires three demanding fight sections. Only one section has a
valid single-layer measurement, and it fails the strict rule. Whether its
06:48–07:13 window counts as a demanding fight section is not established by
the before/after images; the three-section target remains unconfirmed.

## Scene and conditions

The machine was an M5 Max MacBook Pro with 18 CPU cores, 40 GPU cores and
128 GB memory, running macOS 27.0.1. The internal display retained its normal
1728 × 1117 point desktop, 3456 × 2234 pixels at 120 Hz. AC power and Automatic
power mode were used. Thermal state was nominal after the run; this is not a
continuous temperature or power trace.

The signed and notarized Waypoint Windows preview uses the clean runtime build
from [5b77f2d](https://github.com/wowlocal/waypoint-launcher/commit/5b77f2d),
with launcher revision
[2fc2e81](https://github.com/wowlocal/waypoint-launcher/commit/2fc2e81).
It uses Wine built from CodeWeavers' CrossOver 26.3 LGPL source release,
public DXMT 0.80, MSync and Metal pacing at 120 Hz. DXMT reports an AMD adapter
ID (`1002:6810`), which can affect game defaults or code paths. Game VSync is
disabled and the in-game FPS cap is zero; DXMT supplies
the 120 Hz cap. The overall Ultra preset remains 3, with the game's preset
subsettings preserved, including model and physics quality 2. There is no
resolution reduction, upscaling or frame generation. No installed CrossOver
binaries, D3DMetal or paid license were used.

The replay was warmed by playing beyond the test section, returned to game
clock 06:45 and played at Normal speed. The camera followed a living Kerrigan
during a three-hero lane push; enemy-hero combat is visible in the later image. The fixed
sample covers approximately 06:48–07:13. Screenshots outside the timed window
showed the same fullscreen viewport, an intact portrait/statistics bar and live
combat by 07:16. Screenshots and the replay remain private because they contain
player identifiers. Screenshots cannot rule out transient artifacts between
captures. No screen capture or heavy Instruments session ran in the final window.

This is one warmed replay section. It does not cover a cold shader cache,
every map, a full match, sustained thermal behavior, voice chat or the complete
interactive Install → Play flow. The benchmark used WaypointCore launch and
cleanup APIs; the preview's manual Play/focus behavior remains a separate check.

## Measurement checks

The [v3 recorder](../tools/frame-probe/README.md) attaches a presented handler
to each acquired Metal drawable. Statistics use `MTLDrawable.presentedTime`,
the actual onscreen host time, rather than callback arrival time. Zero-time
drawables are excluded. Across the whole process, 29,335 acquisitions and
29,331 handler reservations were recorded, with no uncommitted records.
The four acquisitions without handler records cannot be timed from this format;
they cannot be assigned to shutdown with certainty. There were 20,896 zero-time
records across loading/seeking/playback, with none acquired or called back
inside the fixed sample. The final sample has no simultaneous display-swap
trace to independently resolve the observed 16.667 ms gap.
Layer identity and dimensions are checked for the
sample and its crossing boundary frames. Analysis runs after the owned game
process exits and rejects interior uncommitted records.

Before collecting frames, the controller exclusively wrote an anchor identifying
the game PID and completion of the replay Play command. The sample was fixed at anchor
+3 through +28 seconds. It was not selected after inspecting frame times.
The read-only foreground observer ran its main loop, sampled the observed
frontmost PID every 250 ms and logged activation notifications. The qualifier
rejects foreign activation, missing coverage or gaps above 350 ms. Native arm64
and Rosetta mach clocks were independently converted to host nanoseconds.
These are trusted local measurements, not an attestation system against an
operator forging input files. The recorder adds a callback per drawable;
its overhead is not claimed to be zero.

A separate 25-second, noncombat calibration matched all **3,000** recorder
timestamps to all **3,000** macOS Frame Lifetimes display swaps in both
directions, with a maximum absolute difference of **167.25 ns**, without a fitted
offset or clock rate. That calibration used v2 of the recorder. The actual
presentation-time API is unchanged in v3; v3 adds layer identity and acquisition
counts. This validates the timing mechanism, but is not a simultaneous display
swap crosscheck of the final combat sample. See the
[calibration summary](../results/free-wine-2026-10-19/calibration-v2.json).

Two earlier warmed combat samples each reported 120.00 FPS and no missed
refreshes. They used v2, which did not identify layers, so their aggregate
results are **preliminary**, not final single-layer acceptance. Their summaries
are retained as [sample 1](../results/free-wine-2026-10-19/preliminary-v2-1.json)
and [sample 2](../results/free-wine-2026-10-19/preliminary-v2-2.json).
A separate heavy Metal trace reported 119.97 FPS with a 16.67 ms maximum;
it was diagnostic and is excluded from acceptance. The final result above
retains its missed refresh rather than selecting a cleaner preliminary run.

Claude Opus 5.5 at xhigh reviewed the measurement plan, recorder, qualifier and
final report. The report review verified the calculations; its wording findings
about source provenance and the unproven fight classification were incorporated.
Review findings led to a real main-loop foreground sampler, explicit activation
checks, independent clock conversion, committed-record checks, layer identity
and validation of boundary frames. All 13 regression tests pass, including two
60 FPS layers that must not be accepted as one 120 FPS stream and a missed
boundary frame that must remain in the statistics. The game was closed through
its owned PID after capture; session cleanup completed and the ticket probe
reported `missing-token`. The original Battle.net and stable Waypoint remained
running.
