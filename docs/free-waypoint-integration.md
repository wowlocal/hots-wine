# Free Windows HotS in Waypoint

Implementation lives in [Waypoint's `feat/free-windows-hots` branch](https://github.com/wowlocal/waypoint-launcher/tree/feat/free-windows-hots).
The earlier benchmark profiles and command launcher in this repository still
describe CrossOver-based experiments. Their frame-rate measurements do not
qualify the new free engine.

The new engine is compiled from CodeWeavers' published LGPL Wine 26.3 sources,
with public MIT DXMT 0.80 and supplementary FOSS dylibs. It does not use the
installed CrossOver application, its license data, bundled DXMT or D3DMetal.
Wine is a compatibility layer; a Windows VM is not required.

Waypoint keeps one AppKit HotS row with Windows/macOS selection. Windows game
files, CASC records and Documents settings are separate from the native game.
Installation uses Blizzard's Windows CDN manifests. The existing native web
login and saved account select the game ticket. A small Windows helper receives
it through stdin, protects it with Wine DPAPI and starts HeroesSwitcher in the
same server session. Credentials are absent from argv, environment and logs.

The bundled engine is copied into a verified, versioned runtime cache so the
game can outlive an app update. Preparation, startup and cleanup hold a private
prefix lease. Process exit events follow Switcher/Core handoffs. Recovery kills
only Waypoint's own prefix, and does not touch the authenticated CrossOver bottle.

## Implementation checkpoints

- [71668d1](https://github.com/wowlocal/waypoint-launcher/commit/71668d1): platform-qualified installs, safe root claims and a Windows state sidecar.
- [eb6475f](https://github.com/wowlocal/waypoint-launcher/commit/eb6475f): DPAPI ticket bridge, bounded pipe protocol and Wine process detection.
- [2c67a1f](https://github.com/wowlocal/waypoint-launcher/commit/2c67a1f): AppKit integration, private sessions, engine caching, lifecycle and restart cleanup.

Claude Opus 5.5 with xhigh effort reviewed each major stage. Follow-up reviews
found and corrected cancellation, false Wine exit status, process handoff,
runtime upgrade and cache recovery problems. The HotS-only source patch also
received a separate locking/reentrancy review.

## Qualification so far

On the M5 Max test Mac, a freshly prepared private prefix launched HotS and
logged in using the native macOS HotS ticket. The stripped, relocated runtime
also reached the logged-in main menu through the production WaypointCore API.
The loaded-module audit found no modules from `CrossOver.app`; D3D11, DXGI,
Wine and Metal bridge modules came from Waypoint's own cache. All 138 automated
tests pass, including native install regressions and cache corruption repair.

The first high-DPI test found that full-window Retina size alone did not prove
native rendering. Preparation now writes and reads back the per-game DPI
setting through the acknowledged helper. Native render-size qualification and
the Developer ID build smoke test are still in progress at this checkpoint.
No 120 FPS claim is made for this engine yet.

The staged runtime is approximately 335 MB before compression. Players require
Apple silicon, macOS 14.6+ and Rosetta, with no paid tool or development tools.
Before any public binary release, complete corresponding LGPL dependency sources
and build scripts must accompany the download. This work currently produces a
local development preview, not a stable public release.
