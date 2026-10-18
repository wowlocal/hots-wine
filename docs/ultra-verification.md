# Ultra verification

Build 98348 ships a GPU classification table inside the local CASC data. Its AMD `1002:6810` entry is labelled Ultra. A temporary DXMT adapter-ID override triggered the game's own graphics auto-detection after clearing graphics overrides.

The game generated `GraphicsOptionOverallQualityVer7[21]=3` and the category values saved in `configs/ultra.json`, including texture/shader/shadow/lighting/post-processing/terrain level3. Effects, models, physics, and portraits use the category values chosen by that preset. Reflections and SSAO are0 in the game-generated preset; these are not settings lowered by the benchmark.

The override changes reported adapter metadata, not the physical GPU. It is used to obtain a trustworthy preset rather than guessing undocumented values. Subsequent measurements must verify that the saved preset persists with the backend's normal identity, as well as checking actual drawable dimensions.

The saved config requests3456×2234. Requested variables alone do not prove rendering resolution; the native window and Metal drawable must also be verified.
