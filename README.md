# Heroes of the Storm through Wine on Apple Silicon

Measured CrossOver configuration work for an M5 Max MacBook Pro (40 GPU cores, 128 GB memory).

Target: **3456 × 2234, Ultra, stable 120 FPS**, with native rendering and no generated frames. Acceptance criteria are in [configs/target.json](configs/target.json).

## Current status

The Windows game and Battle.net work in a dedicated CrossOver 26.3 bottle. The target has **not** passed validation. Earlier reduced-quality, half-resolution and static-base samples do not establish target performance.

Native 3456 × 2234 rendering is now confirmed by the Metal HUD. The replay helper corrects the cropped window caused by enabling Retina reporting while the authenticated Wine desktop remains open. The game-generated Ultra preset is retained. Target performance is still being verified.

## Local layout

- Bottle: `~/Library/Application Support/CrossOver/Bottles/Heroes of the Storm`
- Private backups and raw captures: `~/Library/Application Support/CrossOver/HotS-Setup`
- Game settings: the bottle's isolated `drive_c/users/crossover/Documents/Heroes of the Storm/Variables.txt`

This repository contains our scripts, configuration targets, and sanitized measurement summaries. It does not contain game files, licenses, account identifiers, replays, registry exports, or raw screen/trace captures.

## Tools

`tools/replay-control` contains a small, one-shot Windows helper built with Clang and lld-link. It controls the local replay window, without hooks, networking, or persistence. See its source before using it.

`scripts/analyze-presented-frames.py` reads Instruments XML exports. Use the `displayed-surfaces-interval` schema for actual display swaps. Metal presented-handler callbacks can be coalesced and are diagnostic only.

`scripts/benchmark-replay.py` is an early launch/capture helper. It does not yet enforce Ultra, native resolution, foreground logging, or the full acceptance protocol. Its output alone cannot prove success.

## Measurement protocol

1. Verify render-target dimensions, preset definitions, and effective graphics variables.
2. Use identical replay times and camera paths across backends.
3. Separate loading, seeking, warm-up, and steady playback.
4. Log foreground state throughout the measurement.
5. Measure displayed-frame intervals and investigate capture overhead.
6. Repeat warm runs and validate at least three demanding fight sections.
7. Preserve the best measured configuration and report limitations explicitly.
