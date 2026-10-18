# Measurement integration status

The baseline Instruments analyzer uses `displayed-surfaces-interval`, filtered by the actual game PID. Presented-handler callback timestamps can be coalesced and must not be treated as displayed-frame timestamps.

Earlier attached and system-wide captures contained periodic stalls near five-second boundaries. Their overhead is not resolved. These captures cannot establish the strict120FPS acceptance target by themselves.

A passive recorder prototype uses Apple's `MTLDrawable.presentedTime` API and stores texture dimensions and timestamps in a memory-mapped local file. The binary analyzer excludes zero-time dropped drawables and deduplicates actual presentation times. It always leaves overall goal completion unproven.

The prototype compiles, but it is **not qualified for gameplay measurements yet**. The installed CrossOver loader's hardened-runtime configuration ignores the DYLD injection variable. A private signed loader permits loading the recorder, but direct core-executable startup exits before gameplay in this bottle. The supported Switcher launch remains the baseline path.

A temporary cached-loader experiment was rolled back; its contents were verified byte-for-byte against the installed original. Installed CrossOver binaries were not edited. Private signing and diagnostic files stay outside the repository.

`focus-monitor.swift` activates the selected game PID and samples the frontmost PID every250ms. A sample with lost foreground focus must be rejected or explicitly labelled invalid.

Reference: [Apple presentedTime](https://developer.apple.com/documentation/metal/mtldrawable/presentedtime) and [presentation handlers](https://developer.apple.com/documentation/metal/mtldrawable/addpresentedhandler(_:)).
