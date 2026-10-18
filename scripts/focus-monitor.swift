import AppKit
import Foundation
import ApplicationServices

// Authorized foreground activation and read-only focus sampling. No keyboard/mouse input.
guard CommandLine.arguments.count == 4,
      let pid = Int32(CommandLine.arguments[1]),
      let seconds = Double(CommandLine.arguments[2]) else {
    fatalError("usage: focus-monitor PID SECONDS OUTPUT.jsonl")
}
let output = CommandLine.arguments[3]
FileManager.default.createFile(atPath: output, contents: nil)
let file = FileHandle(forWritingAtPath: output)!
let app = NSRunningApplication(processIdentifier: pid)!
_ = AXUIElementSetAttributeValue(AXUIElementCreateApplication(pid), kAXFrontmostAttribute as CFString, kCFBooleanTrue)
_ = app.activate(options: [.activateAllWindows])
Thread.sleep(forTimeInterval: 1)
let until = ProcessInfo.processInfo.systemUptime + seconds
repeat {
    let actual = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1
    let entry: [String: Any] = ["wall": Date().timeIntervalSince1970,
                              "uptime": ProcessInfo.processInfo.systemUptime,
                              "expected_pid": pid, "frontmost_pid": actual,
                              "active": actual == pid]
    let data = try! JSONSerialization.data(withJSONObject: entry, options: [.sortedKeys])
    file.write(data); file.write(Data([10]))
    Thread.sleep(forTimeInterval: 0.25)
} while ProcessInfo.processInfo.systemUptime < until
try! file.close()
