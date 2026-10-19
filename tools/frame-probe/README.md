# Local Metal frame recorder

This developer diagnostic observes `CAMetalLayer.nextDrawable` and attaches
`MTLDrawable.addPresentedHandler`. It records `presentedTime`, the actual
onscreen host time; zero means the drawable was not shown. It does not alter
game files or the installed Wine engine, and is not bundled with Waypoint.

The current format is **v3**: a 72-byte header, records beginning at offset
4096, and 56-byte records. Each record includes drawable dimensions, the
Metal layer identity and a committed sequence number. The header records the
producer PID, its own mach timebase, acquired drawables and invoked handlers.
Read the file after the game exits. Uncommitted interior records are rejected.

The diagnostic launcher supplies an absolute `HOTS_FRAME_LOG_DIR` and loads
the x86_64 dylib with `DYLD_INSERT_LIBRARIES`. The directory must already
exist and be private. A process creates its own `frames-PID.bin` only when it
first acquires a drawable; helpers cannot truncate the game's log. Existing
files and symlinks are rejected. No CrossOver executable or license is used.
The Wine loader must permit diagnostic library loading. Normal Waypoint
launches do not enable this recorder.

Use `scripts/observe-game-focus.swift` for read-only foreground sampling.
It runs the main loop, records activation notifications as well as 250 ms
samples, and normalizes its own mach ticks to host nanoseconds. A sleeping
loop can leave `NSWorkspace.frontmostApplication` stale. On this Mac, native
arm64 ticks use 125/3 while Wine under Rosetta reports 1/1.

The replay controller creates an exclusive anchor JSON before the sample:

```json
{"pid": 12345, "play_command_after_host_ns": 123456789000000}
```

The controller and local files are trusted measurement inputs, not an
attestation system against an operator forging a dataset. Choose the window
before viewing results. The qualifier derives the fixed window from anchor
+3 seconds through +28 seconds, and cannot select a different window by CLI.

```sh
python3 scripts/qualify-probe-fps.py /private/frames-12345.bin \
  --pid 12345 --anchor /private/anchor.json --focus /private/focus.jsonl \
  --output /private/metrics.json
python3 scripts/test-probe-qualification.py
```

The qualifier requires one onscreen layer and 3456×2234 drawables, including
the boundary frames used in interval statistics. It checks foreground
coverage, observed PID, activation events and sampler gaps. FPS uses actual
presentation timestamps within the fixed window; complete crossing intervals
retain boundary stalls. The numeric 120 Hz rule is reported in the JSON.

For a simultaneous Frame Lifetimes calibration, export `display-surface-swap`
and `time-info` XML tables and add `--swaps FILE --time-info FILE`. Both
directions must match within 250 ns on the named display, using the trace's
own absolute mach epoch and timebase, without fitting a phase or rate.
Verify the fullscreen viewport, playback speed and visible combat separately.

The older `analyze-metal-probe.py` reads historical v1 files. v2 aggregate
measurements did not identify layers and are preliminary. Use the v3
qualifier for new runs. The observer adds a callback per drawable; no claim
of zero overhead or universal performance across maps is made.
