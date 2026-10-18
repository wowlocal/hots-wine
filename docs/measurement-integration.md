# Measurement integration status

The baseline Instruments analyzer uses `displayed-surfaces-interval`, filtered by the actual game PID. Presented-handler callback timestamps can be coalesced and must not be treated as displayed-frame timestamps.

Earlier attached and system-wide captures contained periodic stalls near five-second boundaries. Their overhead is not resolved. These captures cannot establish the strict120FPS acceptance target by themselves.

A passive recorder prototype uses Apple's `MTLDrawable.presentedTime` API and stores texture dimensions and timestamps in a memory-mapped local file. The binary analyzer excludes zero-time dropped drawables and deduplicates actual presentation times. It always leaves overall goal completion unproven.

The prototype compiles, but it is **not qualified for gameplay measurements yet**. The installed CrossOver loader's hardened-runtime configuration ignores the DYLD injection variable. A private signed loader permits loading the recorder, but direct core-executable startup exits before gameplay in this bottle. The supported Switcher launch remains the baseline path.

A temporary cached-loader experiment was rolled back; its contents were verified byte-for-byte against the installed original. Installed CrossOver binaries were not edited. Private signing and diagnostic files stay outside the repository.

`focus-monitor.swift` activates the selected game PID and samples the frontmost PID every250ms. A sample with lost foreground focus must be rejected or explicitly labelled invalid.

Reference: [Apple presentedTime](https://developer.apple.com/documentation/metal/mtldrawable/presentedtime) and [presentation handlers](https://developer.apple.com/documentation/metal/mtldrawable/addpresentedhandler(_:)).

The Instruments `at-time` field can recover actual presentation times after correcting its extra mach timebase conversion (125/3 on this Mac). In a simultaneous capture,1765 display-swap timestamps aligned with the deduplicated status2 presentation series; the maximum aligned residual was83ns. Three boundary events differed between the two series. Callback arrival times are still unsuitable. This correction has only been qualified on this Mac and must be checked again on other hardware or Instruments versions.

`scripts/display-timing.swift` is a read-only ScreenCaptureKit diagnostic. It saves timing metadata from a64px display stream, without saving image frames. Its compositor timestamps have not been qualified as actual game display swaps, so its FPS must not be used for acceptance.

A lighter Frame Lifetimes capture exports the raw `display-surface-swap` schema. In the simultaneous reference trace, all1765 game-attributed display-swap timestamps matched raw swaps exactly; only the two capture boundaries differed. The raw schema has no PID ownership. It is therefore only usable with continuous foreground verification and a separately verified game viewport covering the entire display. The analyzer rejects missing or lost foreground logs. Attribution on another desktop layout or with other overlays must be requalified.

`inspect-replay.swift` provides read-only clock/seek-state OCR outside measurement intervals. `hold-center` holds Space during a sample so the original replay player's camera path can be repeated across backends.

A temporary AppInit DPI initializer experiment did not produce a qualified load or viewport fix. Its registry values were removed. It is not part of the working launch configuration. The native display-mode helper stores the original mode privately and can restore it with `display-mode restore`; changes use session scope.
