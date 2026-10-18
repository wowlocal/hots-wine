# Measured outcome

Performance experiments stopped after the final bundled-DXMT input-setting comparison. **Genuine3456×2234 and Ultra were verified; stable120FPS was not.** No resolution scaling, quality reduction or generated frames were used.

The selected profile is `dxmt-metal120`: CrossOver26.3 bundled DXMT v0.72-25-gf35d839, MSync on, game frame cap disabled, VSync off, Metal preferred maximum120FPS, AMD adapter metadata for the engine-generated Ultra preset, and the engine default for Reduce Mouse Lag. Normal macOS Retina scaling is retained with Wine RetinaModeY and96DPI. Installed CrossOver binaries were not modified.

| Prepared replay clock | Average FPS | 1% low FPS | p95 / p99 ms | Worst ms | Frames over25ms | Acceptance |
|---|---:|---:|---:|---:|---:|---|
|06:51|120.000|119.999|8.333 /8.333|8.333|0|Pass|
|13:21|119.911|111.724|8.333 /8.333|16.667|0|Fail1%low|
|14:52|119.866|108.000|8.333 /8.333|16.667|0|Fail1%low|

These are three30-second recordings, with the first7seconds and last1second excluded. The selected replay player and held-Space camera path were repeated after shader traversal and cached seeking. Full-display viewport, continuous foreground logs and the native Ultra settings were checked. See the three `results/dxmt-metal120-fight*-nohud.json` summaries.

The acceptance requirement was average≥119FPS,1%low≥115FPS,p99≤9ms and no steady frame over25ms, across all three demanding sections. Two sections missed individual display refreshes. This keeps the average near120 while dropping the worst1% below the requirement. One passing section cannot establish success.

D3DMetal had weaker lows. DXVK both failed pacing and corrupted the spectator portrait bar; its tested profile is blocked by the normal launcher. An isolated upstream DXMT0.80 runtime rendered correctly but its warmed first-fight repeat fell to119.55FPS average and87.57FPS1%low. The final bundled-DXMT test explicitly disabled Reduce Mouse Lag:119.59FPS average,90.00FPS1%low,8.333ms p99 and20.833ms worst frame. It provided no evidence to replace the selected baseline and was not expanded into more tests.

The light Frame Lifetimes swap timestamps were independently matched against game presentation timestamps in a simultaneous native HUD-hidden DXMT capture, within167ns. Heavy Instruments captures caused more misses. Exact residual overhead in the light recordings remains unresolved, as does the root cause of the occasional missed refresh. These results do not prove a hardware limit or guarantee live-match performance on other maps. They establish that the requested strict target did not pass this protocol.

The authenticated Battle.net process was preserved. Benchmark-only function-key and camera-follow preferences were restored. The chosen profile and exact selection evidence are in `configs/recommended.json`; raw traces, screenshots and backups remain private under HotS-Setup.

The convenience launcher at `~/Applications/Play Heroes of the Storm.command` was tested end to end: it reached the authenticated normal-game menu, retained native client/desktop dimensions and Ultra, preserved full pointer movement, and returned successfully after the test game exited. The game is closed; Battle.net remains running. See `results/normal-launch-validation.json`.
