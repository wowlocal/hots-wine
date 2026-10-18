# Heroes of the Storm through Wine on Apple Silicon

Measured CrossOver configuration work for an M5 Max MacBook Pro (40 GPU cores, 128 GB memory).

Target: **3456 × 2234, Ultra, stable 120 FPS**, with native rendering and no generated frames. Acceptance criteria are in [configs/target.json](configs/target.json).

## Current status

The Windows game and Battle.net work in a dedicated CrossOver 26.3 bottle. The target has **not** passed validation. Earlier reduced-quality, half-resolution and static-base samples do not establish target performance.

Native 3456 × 2234 rendering is now confirmed by the Metal HUD. The replay helper corrects the cropped window caused by enabling Retina reporting while the authenticated Wine desktop remains open. The game-generated Ultra preset is retained. Target performance is still being verified.

DXVK's tested native VSync profile is rejected: it fails the frame-time target and corrupts the spectator hero-portrait bar. The normal-game launcher refuses that known-bad profile. A paused scene between captures is deliberate while Instruments processes its trace, which can take several minutes; it must not be mistaken for a game hang. Visual correctness is a separate prerequisite for accepting performance results.

| Tested configuration | Average FPS | 1% low FPS | p99 (ms) | Worst frame (ms) | Outcome |
|---|---:|---:|---:|---:|---|
| DXMT Metal120, three fights | 119.87–120.00 | 108.00–120.00 | 8.33 | 16.67 | One of three passes |
| DXMT VSync120, three fights | 119.78–120.00 | 101.25–120.00 | 8.33 | 16.67 | One of three passes |
| D3DMetal VSync, warmed first fight | 117.63 | 60.00 | 16.67 | 16.67 | Fails |
| DXVK VSync, warmed first fight | 119.71 | 96.72 | 8.33 | 20.83 | Fails; portrait corruption |
| Upstream DXMT0.80, warmed first fight | 119.55 | 87.57 | 8.33 | 16.67 | Fails; worse pacing |

All rows use native3456×2234 and the engine-generated Ultra preset. D3DMetal/DXVK used temporary native1× host scaling; the DXMT rows used the original Retina desktop geometry. These are tested configuration bundles, not an isolated measurement of one backend variable. Exact summaries are under `results/`. Bundled DXMT remains the selected baseline; a final isolated mouse-lag setting test is in progress. See [visual validation](docs/visual-validation.md).

## Local layout

- Bottle: `~/Library/Application Support/CrossOver/Bottles/Heroes of the Storm`
- Private backups and raw captures: `~/Library/Application Support/CrossOver/HotS-Setup`
- Game settings: the bottle's isolated `drive_c/users/crossover/Documents/Heroes of the Storm/Variables.txt`

This repository contains our scripts, configuration targets, and sanitized measurement summaries. It does not contain game files, licenses, account identifiers, replays, registry exports, or raw screen/trace captures.

## Tools

`tools/replay-control` contains a small, one-shot Windows helper built with Clang and lld-link. It controls the local replay window, without hooks, networking, or persistence. See its source before using it.

`scripts/analyze-presented-frames.py` reads Instruments XML exports. Use the `displayed-surfaces-interval` schema for actual display swaps. Metal presented-handler callbacks can be coalesced and are diagnostic only.

`scripts/benchmark-replay.py` is an early launch/capture helper. It does not yet enforce Ultra, native resolution, foreground logging, or the full acceptance protocol. Its output alone cannot prove success.

`scripts/launch-profile.py PROFILE --game` opens the normal game through its Switcher using the existing session; omitting `--game` opens the local benchmark replay. The normal-game path is pending live verification. It preserves the current function-key preference. Restart operations now verify the game's working directory belongs to this bottle and accept updated game build numbers. They never stop Battle.net or wineserver.

`scripts/play-game.py PROFILE` keeps the original macOS scaling and uses the bottle's configured Retina reporting. The optional `--native-display` is for backend comparisons: it temporarily switches to native1× and restores the display/registry backup on game exit. Its process-exit monitor uses macOS kernel notifications, without a polling loop. This wrapper is pending a live normal-game launch/exit check.

The optional `dxmt-v080-metal120` candidate uses an isolated, pinned [upstream DXMT0.80 release](https://github.com/3Shain/dxmt/releases/tag/v0.80). `setup-dxmt-overlay.py` verifies a locally downloaded archive and stages private runtime links; it never edits the installed application. A D3D11 device probe confirmed all four upstream runtime modules loaded successfully. Its first native Ultra fight and warmed repeat rendered correctly, but the repeat regressed to119.55FPS average and87.57FPS1%low. It is not selected. CrossOver's compatibility database prepends its selected backend path, so `WINEDLLPATH` alone did not select the new runtime; the private `CX_ROOT` overlay did.

## Measurement protocol

1. Verify render-target dimensions, preset definitions, and effective graphics variables.
2. Use identical replay times and camera paths across backends.
3. Separate loading, seeking, warm-up, and steady playback.
4. Log foreground state throughout the measurement.
5. Measure displayed-frame intervals and investigate capture overhead.
6. Repeat warm runs and validate at least three demanding fight sections.
7. Preserve the best measured configuration and report limitations explicitly.
