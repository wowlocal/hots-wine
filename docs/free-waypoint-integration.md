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
- [3cddb77](https://github.com/wowlocal/waypoint-launcher/commit/3cddb77): reviewed cache repair, process ownership and host compatibility fixes.
- [a8d49c0](https://github.com/wowlocal/waypoint-launcher/commit/a8d49c0): pinned source build, relocatable dependencies, signing, license notices and build instructions.
- [5b77f2d](https://github.com/wowlocal/waypoint-launcher/commit/5b77f2d): deterministic startup-patch application with an exact post-patch source hash.
- [2fc2e81](https://github.com/wowlocal/waypoint-launcher/commit/2fc2e81): reveal the Wine game after Play while Waypoint still owns focus.

Claude Opus 5.5 with xhigh effort reviewed each major stage. Follow-up reviews
found and corrected cancellation, false Wine exit status, process handoff,
runtime upgrade and cache recovery problems. The HotS-only source patch also
received a separate locking/reentrancy review. Final packaging review caught
BSD `patch` guessing the reverse direction during a dry run. Full builds now
extract pristine Wine, apply the patch noninteractively with `-f`, and verify
the resulting `class.c` hash. Stage-only packaging rejects changed input pins
or source hashes before modifying the source tree. Both rejection cases and
successful stage-only packaging were exercised.

## Local qualification, 19 October 2026

On the M5 Max test Mac, a freshly prepared private prefix launched HotS and
logged in using the native macOS HotS ticket. The stripped, relocated runtime
also reached the logged-in main menu through the production WaypointCore API.
The loaded-module audit found no modules from `CrossOver.app`; D3D11, DXGI,
Wine and Metal bridge modules came from Waypoint's own cache. All 138 automated
tests pass, including native install regressions and cache corruption repair.

The first high-DPI test found that full-window Retina size alone did not prove
native rendering. Preparation now writes and reads back the per-game DPI
setting through the acknowledged helper. The signed free engine subsequently
rendered the menu and replay at **3456 × 2234**, confirmed by the Metal HUD and
game settings, with the **Ultra** overall preset. The replay world and hero
portraits/statistics bar were visually intact. This checks rendering and login;
voice chat and the complete interactive Install → Play flow remain untested.

The qualified runtime was built from clean commit `5b77f2d`. Its patched
`dlls/win32u/class.c` SHA-256 is
`673524e6c36ab1d506ab59e602a67a41024f1a84eea11f7ef20fc89f2bbee6e1`.
The final local preview contains the launcher at `2fc2e81`, signed with
Developer ID team `H8QG3CBM96`. Apple accepted notarization submission
`4806d7e7-4eb0-4e92-b60d-222c91d0a721`; stapling, strict signature verification
and Gatekeeper assessment passed.

There is **no valid FPS acceptance result for this free engine yet**. The
CLI-started replay stayed behind the terminal; foreground monitoring rejected
that measurement. Its FPS cannot establish gameplay performance. Earlier
CrossOver results do not carry over, and solid 120 FPS at native resolution
and Ultra is not claimed. The new launcher reveals the game only while the
user is still in Waypoint; that activation path compiles but still needs an
actual user Play check.

The staged runtime is approximately **314 MB** before compression; the signed
preview app archive is approximately **96 MiB**. Players require Apple silicon,
**macOS 15+** and Rosetta, with no paid tool or development tools. Wine itself
targets 14.6, but public DXMT's Metal bridge requires 15. The native-only
Waypoint build retains its macOS 14 minimum.

Before any public binary release, complete corresponding LGPL dependency sources
and build scripts must accompany the download. This work currently produces a
local development preview, not a stable public release. The installed stable
Waypoint app is unchanged.

On the development Mac the preview is at:

```text
/Users/mike/src/tries/2026-10-04-battle-net/build/Waypoint-Windows-Preview.app
```

When another Waypoint instance is already running, open this exact build with
`open -n` and its path. The independent Windows game is registered at
`~/Games/Heroes of the Storm (Windows)`. Launch it from the preview's normal
HotS row with the Windows edition selected. The older command launcher in this
repository still uses CrossOver and is not the free entry point.
