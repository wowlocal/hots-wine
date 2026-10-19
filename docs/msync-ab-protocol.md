# HotS MSync A/B protocol, 2026-10-19

This is an exploratory comparison of MSync on/off on the free Waypoint Wine
runtime, with native 3456×2234 Ultra rendering and a 120 FPS Metal cap. Earlier
benchmarks used MSync on throughout; they cannot establish its benefit.

Use the same private prefix pathname, restoring an APFS clone of an identical
baseline before each launch. Hold Waypoint's global Windows launch lease. Stop
and wait for only that prefix's wineserver between launches. Set WINEMSYNC
consistently for the server, bridge, game and Wine input helper; explicitly
set WINEESYNC=0 and WINEFSYNC=0. Record the actual MSync startup acknowledgement.
Do not launch Windows Battle.net or modify the production prefix.

A discarded pilot validates the control/measurement path and warms shared
shader caches. The first comparison block is on → off → off → on (ABBA).
All launches pause/reset the replay to its beginning, then traverse it to at
least HUD 15:10 before testing, using
8× for the initial traversal and returning to Normal before the end of the game.
Record AC/thermal state and retain a fixed cooldown between launches. Preserve
normal Retina display scaling and the current display mode. Since variable
refresh is not independently disabled, report long presentation intervals as
intervals, rather than claiming physical missed refreshes from a fixed rate.

Preflight all three paused HUD clocks 06:45, 13:15 and 14:45 before collecting
any timed sample in each launch, then prepare them again in collection order.
Timeline clicks are coarse: use cached 10-second skips and timed play/pause
inside the Wine helper for the last few seconds, and confirm the exact clock.
Wait for the replay HUD after authentication; an unreadable clock during
loading is not a failed performance measurement. Select player 3 (Kerrigan),
center the pointer and hold Space to follow her. Verify the selected portrait,
scene, exact paused HUD clock and Normal speed outside the sample. The timer in
the replay panel differs from the HUD timer; use the HUD consistently.
The same camera path and interface must be used in both arms. Do not directly
compare these player-view samples with older spectator-view recordings.

For each section, declare an exclusive anchor file immediately after the play
command. Measure the fixed host-clock interval +3 to +28 seconds. Do not run
screenshots, OCR, a trace profiler or seek controls inside that interval.
Use the existing calibrated v3 MTLDrawable.presentedTime recorder. Analyze only
after the game exits, with the existing strict native-drawable, single-layer,
continuous-foreground and monotonic-window validation. Require a 29–33 second advancement of the HUD clock and a stable paused
clock after recording, so a dropped play command cannot qualify a paused scene.
Keep all failed attempts and reasons; never trim a stall out of a sample. Abort on loss of foreground.

Report each section and independent launch separately: average FPS, 1% low,
p99, worst interval, intervals >12.5/25/50 ms, and strict 120-rule status.
Two launches per arm are a screening block, not a statistical proof of a small
advantage. A setting change requires a repeatable improvement exceeding
launch-to-launch spread; otherwise retain the current default. Claude Opus 5.5
xhigh recommended at least three complete ABBA blocks for a stronger inference.
The 120 cap masks uncapped headroom and no replay establishes whole-match FPS.

Raw screenshots, replay and prefix/registry/auth data stay private. Publish only
sanitized metrics, hashes, protocol deviations and the observed limitations.
