# Visual checks before accepting a profile

Settings and FPS counters do not establish correct rendering. The DXVK native VSync run retained the Ultra variables but failed to draw the spectator hero portraits. The underlying world showed through the top bar. The same replay moment rendered correctly with bundled DXMT and upstream DXMT0.80.

For each new renderer configuration, inspect a private screenshot after loading, after warm-up and seeking, and after the measured fight. Check the complete viewport, hero portraits, stat/talent bar, terrain, models, effects and shadows. Match the selected replay player and fight composition to the reference. A profile with visible corruption cannot pass acceptance, regardless of its frame counters.

Read-only screenshots and OCR run outside the timed recording interval. They remain private because they contain player information. New profiles stop at the prepared screenshot checkpoint for visual inspection before capture starts.

The replay deliberately pauses when a capture ends. Instruments can take several minutes to process the trace. The stationary scene during that wait is expected and must be announced clearly; rendering faults are investigated separately.
