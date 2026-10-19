import AppKit
import Foundation

// Read-only sampling. Run the main loop so NSWorkspace's cached app state
// receives activation notifications; Thread.sleep alone leaves it stale.
let args = CommandLine.arguments
guard args.count == 4, let expected = Int32(args[1]),
      let seconds = Double(args[2]), seconds > 0, seconds <= 1800 else { exit(2) }
let descriptor = open(args[3], O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600)
guard descriptor >= 0 else { exit(3) }
let file = FileHandle(fileDescriptor: descriptor, closeOnDealloc: true)
let end = ProcessInfo.processInfo.systemUptime + seconds
let activity = ProcessInfo.processInfo.beginActivity(options: .latencyCritical,
                                                     reason: "Recording game foreground transitions")
var timebase = mach_timebase_info_data_t()
mach_timebase_info(&timebase)
func emit(_ kind: String, observed: pid_t) {
    let mach = mach_absolute_time()
    let row: [String: Any] = ["kind": kind, "mach": mach,
                             "host_ns": mach * UInt64(timebase.numer) / UInt64(timebase.denom),
                             "timebase_numer": timebase.numer, "timebase_denom": timebase.denom,
                             "wall": Date().timeIntervalSince1970,
                             "expected_pid": expected, "frontmost_pid": observed,
                             "active": observed == expected]
    do {
            let data = try JSONSerialization.data(withJSONObject: row, options: .sortedKeys)
            try file.write(contentsOf: data)
            try file.write(contentsOf: Data([10]))
    } catch { exit(3) }
}
let observer = NSWorkspace.shared.notificationCenter.addObserver(
    forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: .main
) { notification in
    let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication
    emit("activation", observed: app?.processIdentifier ?? -1)
}
let timer = DispatchSource.makeTimerSource(queue: .main)
timer.schedule(deadline: .now(), repeating: .milliseconds(250), leeway: .milliseconds(5))
timer.setEventHandler {
    let observed = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1
    emit("sample", observed: observed)
    if ProcessInfo.processInfo.systemUptime >= end {
        timer.cancel(); try? file.close(); exit(0)
    }
}
timer.activate()
RunLoop.main.run()
