# Free Windows HotS in Waypoint

Implementation is merged into [Waypoint's `main` branch](https://github.com/wowlocal/waypoint-launcher/tree/main)
and ships in [Waypoint 0.5.0, build 69](https://github.com/wowlocal/waypoint-launcher/releases/tag/v0.5.0).
The earlier benchmark profiles and command launcher in this repository still
describe CrossOver-based experiments. Their frame-rate measurements do not
qualify the new free engine.

The new engine compiles Wine from CodeWeavers' CrossOver 26.3 LGPL source release,
with public MIT DXMT 0.80 and supplementary FOSS dylibs. It does not use the
installed CrossOver application, its license data, bundled DXMT or D3DMetal.
Wine is a compatibility layer; a Windows VM is not required.

Waypoint keeps one AppKit HotS row with Windows/macOS selection. Windows game
files, CASC records and Documents settings are separate from the native game.
Installation uses Blizzard's Windows CDN manifests. The existing native web
login and saved account select the game ticket. A small Windows helper receives
it through stdin, protects it with Wine DPAPI and starts HeroesSwitcher in the
same server session. Credentials are absent from argv, environment and logs.

Windows support downloads on the first Windows HotS Play, with progress in the
native game row. The signed app pins its HTTPS URL, size and SHA-256, plus a
manifest of runtime files. A verified, versioned cache reuses the component
offline and lets the game outlive an app update. Corrupt caches are repaired;
cancelled or failed downloads do not become installed runtimes.
Preparation, startup and cleanup hold a private
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
- [8e0a8d5](https://github.com/wowlocal/waypoint-launcher/commit/8e0a8d5): verified, cancellable first-Play component download and cache repair.
- [e3e04be](https://github.com/wowlocal/waypoint-launcher/commit/e3e04be): separately notarized component, corresponding LGPL sources and resumable release publication.
- [3544ac3](https://github.com/wowlocal/waypoint-launcher/commit/3544ac3): source-built current TLS dependencies, immutable component URLs and source-package checks from Opus review.
- [1409b71](https://github.com/wowlocal/waypoint-launcher/commit/1409b71): native progress observation; released app revision.

Claude Opus 5.5 with xhigh effort reviewed each major stage. Follow-up reviews
found and corrected cancellation, false Wine exit status, process handoff,
runtime upgrade and cache recovery problems. The HotS-only source patch also
received a separate locking/reentrancy review. Final packaging review caught
BSD `patch` guessing the reverse direction during a dry run. Full builds now
extract pristine Wine, apply the patch noninteractively with `-f`, and verify
the resulting `class.c` hash. Stage-only packaging rejects changed input pins
or source hashes before modifying the source tree. Both rejection cases and
successful stage-only packaging were exercised.
The final activation revision at `2fc2e81` received another Opus 5.5 xhigh
review, with no blocking correctness finding. Its manual Play and focus cases
remain part of the verification limits below.
Opus also reviewed the on-demand implementation and release packaging. Findings
led to clean dependency builds with recorded binary hashes, current GnuTLS,
content-addressed component URLs that the publisher refuses to overwrite,
full public-object hash checks before activating the update feed, and explicit source/relinking
instructions. Download progress is throttled and its associated values take part
in AppKit observation equality.

## Public release and first-Play check

The 0.5.0 DMG is **4,003,692 bytes (3.8 MiB)**. Windows support is a separate
**94,624,506-byte ZIP (90 MiB)**; normal app updates do not redownload it when the
pinned runtime is unchanged. The app, component wrapper and DMG have Developer ID
signatures, accepted Apple notarization and stapled tickets. Sparkle verifies
the DMG's EdDSA signature. The native app still supports macOS 14; Windows HotS
requires **Apple silicon, macOS 15+ and Rosetta**.

The final production WaypointCore test downloaded the real public component,
verified and installed it, prepared the prefix and reached the authenticated
HotS main menu with the saved native account. Read-only inspection after the
user focused the game confirmed the menu. Loaded GnuTLS, GMP, Nettle/Hogweed,
Wine and Metal bridge libraries came from Waypoint's cache, with no modules
from `CrossOver.app`. After stopping only the owned test game, production
session cleanup completed and the DPAPI helper reported `missing-token`.
Existing Battle.net and stable Waypoint processes were preserved.

All **144 Swift tests pass**, including bounded/cancelled downloads, offline
cache reuse, cache repair, abandoned-transfer cleanup, same-size hash corruption,
manifest mismatch and unsafe descriptor rejection. The whole interactive
Install → Play path, voice chat and a macOS 14 machine remain outside this check.

The release replaces the preview's LGPL dependency binaries with fresh builds
of **GMP 6.3.0, Nettle/Hogweed 3.10.1 and GnuTLS 3.8.13**. Wine and DXMT rendering
code are unchanged from the preview described below. The FPS measurement has
**not** been repeated with this final TLS dependency set; it remains a result
for the earlier preview, rather than release-wide performance qualification.

The release includes the complete corresponding LGPL sources, build recipes,
patches and license notices. Sources are also available at the
[content-addressed source archive](https://storage.yandexcloud.net/macos-releases/waypoint/windows/Waypoint-Windows-d724f342f2bbde317a02add5843bab3384b74bc00656731c1696b4c07771d5b6-sources.tar).
[Runtime build instructions](https://github.com/wowlocal/waypoint-launcher/blob/main/tools/wine-runtime/SOURCE-README.md)
explain how to use a modified local runtime through `windowsRuntimeOverride`.
No CrossOver purchase or license is required.

## Earlier preview qualification, 19 October 2026

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

The free engine now has a valid foreground, single-layer FPS measurement at
native resolution and Ultra: **119.96 FPS average, 116.13 FPS 1% low**, with
**one missed refresh in 25 seconds** and a **16.67 ms** longest interval.
Uninterrupted 120 FPS remains unconfirmed. See the
[measurement report and data](free-wine-fps.md) for the exact scene and limits.
Earlier CrossOver results do not carry over. Initial background captures were
rejected; the final test followed an explicit user focus action and continuous
foreground observation. The new launcher reveals the game only while the
user is still in Waypoint; the manual Play activation path still needs an
actual user check.

The staged runtime is approximately **314 MB** before compression; the signed
preview app archive is approximately **96 MiB**. Players require Apple silicon,
**macOS 15+** and Rosetta, with no paid tool or development tools. Wine itself
targets 14.6, but public DXMT's Metal bridge requires 15. The native-only
Waypoint build retains its macOS 14 minimum.

The installed stable Waypoint instance was not replaced during testing. For
normal use, install the published release or use its Sparkle update, select
Windows in the HotS row and press Play. The independent Windows game is
registered at `~/Games/Heroes of the Storm (Windows)` on the development Mac.
The older command launcher in this repository still uses CrossOver.
