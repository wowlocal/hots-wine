# Heroes of the Storm through Wine on Apple Silicon

Wine configuration and performance measurements for an M5 Max MacBook Pro (40 GPU cores, 128 GB memory).

Target: **3456 × 2234, Ultra, stable 120 FPS**, with native rendering and no generated frames. Acceptance criteria are in [configs/target.json](configs/target.json).

Free native-launch integration ships in [Waypoint 0.5.0](https://github.com/wowlocal/waypoint-launcher/releases/tag/v0.5.0),
using source-built Wine and public DXMT, without a CrossOver license. The signed,
notarized app is approximately **3.8 MiB** compressed; Windows support downloads
on the first Windows HotS Play (**90 MiB**) and stays cached. See the
[implementation and qualification checkpoints](docs/free-waypoint-integration.md).
Its [foreground native Ultra measurement](docs/free-wine-fps.md) reports
**119.96 FPS average, 116.13 FPS 1% low and one missed refresh in 25 seconds**.
Uninterrupted 120 FPS remains unconfirmed. The historical CrossOver measurements
below describe the older runtime.

The newer [MSync comparison](docs/msync-ab-results.md) uses the free runtime from
Waypoint 0.6.0: four launches in on/off/off/on order, three sections each.
MSync enabled averaged **119.18 FPS**, versus **113.47 FPS** disabled, with fewer
long frame intervals. One enabled-mode section still had a **58.49 FPS 1% low**;
retain MSync enabled, but uninterrupted 120 FPS remains unconfirmed.

The [stutter tracing report](docs/stutter-trace-results.md) retains an initial
94.44 FPS pass and later smooth controls. A targeted trace independently
matches every displayed frame and localizes an isolated hitch to a gap in
new-frame requests; the cause of the frequent early stutter remains unresolved.

## Historical CrossOver status

The Windows game and Battle.net work in a dedicated CrossOver 26.3 bottle. Performance testing has finished. The target has **not** passed validation. Earlier reduced-quality, half-resolution and static-base samples do not establish target performance.

Native 3456 × 2234 rendering is now confirmed by the Metal HUD. The replay helper corrects the cropped window caused by enabling Retina reporting while the authenticated Wine desktop remains open. The game-generated Ultra preset is retained. The best measured profile is bundled DXMT with Metal pacing at120; occasional missed refreshes prevent the strict1%low target.

DXVK's tested native VSync profile is rejected: it fails the frame-time target and corrupts the spectator hero-portrait bar. The normal-game launcher refuses that known-bad profile. A paused scene between captures is deliberate while Instruments processes its trace, which can take several minutes; it must not be mistaken for a game hang. Visual correctness is a separate prerequisite for accepting performance results.

| Tested configuration | Average FPS | 1% low FPS | p99 (ms) | Worst frame (ms) | Outcome |
|---|---:|---:|---:|---:|---|
| DXMT Metal120, three fights | 119.87–120.00 | 108.00–120.00 | 8.33 | 16.67 | One of three passes |
| DXMT VSync120, three fights | 119.78–120.00 | 101.25–120.00 | 8.33 | 16.67 | One of three passes |
| D3DMetal VSync, warmed first fight | 117.63 | 60.00 | 16.67 | 16.67 | Fails |
| DXVK VSync, warmed first fight | 119.71 | 96.72 | 8.33 | 20.83 | Fails; portrait corruption |
| Upstream DXMT0.80, warmed first fight | 119.55 | 87.57 | 8.33 | 16.67 | Fails; worse pacing |
| Bundled DXMT, mouse-lag reduction disabled | 119.59 | 90.00 | 8.33 | 20.83 | Fails; final candidate rejected |

All rows use native3456×2234 and the engine-generated Ultra preset. D3DMetal/DXVK used temporary native1× host scaling; the DXMT rows used the original Retina desktop geometry. These are tested configuration bundles, not an isolated measurement of one backend variable. Exact summaries are under `results/`. Bundled DXMT `dxmt-metal120` remains selected in [configs/recommended.json](configs/recommended.json). Disabling mouse-lag reduction did not improve the final sample. See the [measured outcome](docs/measured-outcome.md). See [visual validation](docs/visual-validation.md).

## Play with the selected profile

On this Mac, open `~/Applications/Play Heroes of the Storm.command`. The versioned entry is [Play Heroes of the Storm.command](Play%20Heroes%20of%20the%20Storm.command). It opens the normal game with `dxmt-metal120`, hides the diagnostic HUD and retains normal desktop scaling. The local compiled helpers are already installed under HotS-Setup. The launcher does not start a replay, profiler or matchmaking.

## Local layout

- Bottle: `~/Library/Application Support/CrossOver/Bottles/Heroes of the Storm`
- Private backups and raw captures: `~/Library/Application Support/CrossOver/HotS-Setup`
- Game settings: the bottle's isolated `drive_c/users/crossover/Documents/Heroes of the Storm/Variables.txt`

This repository contains our scripts, configuration targets, and sanitized measurement summaries. It does not contain game files, licenses, account identifiers, replays, registry exports, or raw screen/trace captures.

## Tools

`tools/replay-control` contains a small, one-shot Windows helper built with Clang and lld-link. It controls the local replay window, without hooks, networking, or persistence. See its source before using it.

`scripts/analyze-presented-frames.py` reads Instruments XML exports. Use the `displayed-surfaces-interval` schema for actual display swaps. Metal presented-handler callbacks can be coalesced and are diagnostic only.

`scripts/benchmark-replay.py` is an early launch/capture helper. It does not yet enforce Ultra, native resolution, foreground logging, or the full acceptance protocol. Its output alone cannot prove success.

`scripts/launch-profile.py PROFILE --game` opens the normal game through its Switcher using the existing session; omitting `--game` opens the local benchmark replay. The normal-game path was verified to reach the authenticated main menu without joining a match. It preserves the current function-key preference. Restart operations now verify the game's working directory belongs to this bottle and accept updated game build numbers. They never stop Battle.net or wineserver.

`scripts/play-game.py PROFILE` keeps the original macOS scaling and uses the bottle's configured Retina reporting. The optional `--native-display` is for backend comparisons: it temporarily switches to native1× and restores the display/registry backup on game exit. Its process-exit monitor uses macOS kernel notifications, without a polling loop. The default launch, native client/desktop geometry, full pointer range, retained Ultra settings and process-exit monitor were checked live. The test game was then closed while Battle.net stayed authenticated. The optional display-switch branch was not part of that final check.

The optional `dxmt-v080-metal120` candidate uses an isolated, pinned [upstream DXMT0.80 release](https://github.com/3Shain/dxmt/releases/tag/v0.80). `setup-dxmt-overlay.py` verifies a locally downloaded archive and stages private runtime links; it never edits the installed application. A D3D11 device probe confirmed all four upstream runtime modules loaded successfully. Its first native Ultra fight and warmed repeat rendered correctly, but the repeat regressed to119.55FPS average and87.57FPS1%low. It is not selected. CrossOver's compatibility database prepends its selected backend path, so `WINEDLLPATH` alone did not select the new runtime; the private `CX_ROOT` overlay did.

## Measurement protocol

1. Verify render-target dimensions, preset definitions, and effective graphics variables.
2. Use identical replay times and camera paths across backends.
3. Separate loading, seeking, warm-up, and steady playback.
4. Log foreground state throughout the measurement.
5. Measure displayed-frame intervals and investigate capture overhead.
6. Repeat warm runs and validate at least three demanding fight sections.
7. Preserve the best measured configuration and report limitations explicitly.
