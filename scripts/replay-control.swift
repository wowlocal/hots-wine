import AppKit
import CoreGraphics
import Foundation
import ApplicationServices

// Scoped CLI companion for the Wine replay. No general-purpose UI actions.
guard CommandLine.arguments.count >= 3, let pid = Int32(CommandLine.arguments[1]),
      let app = NSRunningApplication(processIdentifier: pid),
      app.localizedName == "HeroesOfTheStorm_x64.exe" else { fatalError("Expected the Wine HotS PID") }
let command = CommandLine.arguments[2]
guard ["activate", "camera", "center", "pointer-check", "follow", "hold-center", "play-for", "seek", "hud", "timeline", "pause", "faster", "slower", "restart", "back", "next"].contains(command) else { fatalError("Unsupported replay command") }
guard CGPreflightPostEventAccess() else { fatalError("Event posting is unavailable; no input sent") }
let windows = CGWindowListCopyWindowInfo([.optionAll, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
guard let window = windows.first(where: {
    ($0[kCGWindowOwnerPID as String] as? Int) == Int(pid) &&
    ($0[kCGWindowName as String] as? String) == "Heroes of the Storm"
}), let bounds = window[kCGWindowBounds as String] as? [String: CGFloat],
   let x = bounds["X"], let y = bounds["Y"], let width = bounds["Width"], let height = bounds["Height"] else {
    fatalError("Replay window not found")
}
_ = AXUIElementSetAttributeValue(AXUIElementCreateApplication(pid), kAXFrontmostAttribute as CFString, kCFBooleanTrue)
_ = app.activate(options: [.activateAllWindows])
Thread.sleep(forTimeInterval: 1)
func checkFocus() {
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { fatalError("Replay lost focus; input cancelled") }
}
func key(_ code: CGKeyCode, flags: CGEventFlags = []) {
    checkFocus()
    let down = CGEvent(keyboardEventSource: nil, virtualKey: code, keyDown: true)
    down?.flags = flags; down?.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.08)
    let up = CGEvent(keyboardEventSource: nil, virtualKey: code, keyDown: false)
    up?.flags = flags; up?.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.2)
}
if command == "camera" { key(23); key(8) } // Observe player5, then follow player camera.
func movePointer(_ point:CGPoint) {
    checkFocus()
    CGEvent(mouseEventSource:nil,mouseType:.mouseMoved,mouseCursorPosition:point,mouseButton:.left)?.post(tap:.cghidEventTap)
    Thread.sleep(forTimeInterval:0.2)
}
if command == "center" {
    movePointer(CGPoint(x:x+width*0.5,y:y+height*0.5))
    key(23); key(49)
}
if command == "pointer-check" {
    let target=CGPoint(x:x+width*0.9,y:y+height*0.5)
    movePointer(target)
    let actual=CGEvent(source:nil)!.location
    print("Pointer target: \(target.x),\(target.y); actual: \(actual.x),\(actual.y)")
    movePointer(CGPoint(x:x+width*0.5,y:y+height*0.5))
}
if command == "hold-center" {
    guard (4...5).contains(CommandLine.arguments.count), let seconds=Double(CommandLine.arguments[3]), seconds>0,seconds<=180 else {exit(2)}
    let stopFile=CommandLine.arguments.count==5 ? CommandLine.arguments[4] : nil
    checkFocus()
    let down=CGEvent(keyboardEventSource:nil,virtualKey:49,keyDown:true);down?.flags=[];down?.post(tap:.cghidEventTap)
    let end=ProcessInfo.processInfo.systemUptime+seconds
    while ProcessInfo.processInfo.systemUptime<end && NSWorkspace.shared.frontmostApplication?.processIdentifier==pid {
        if let stopFile=stopFile,FileManager.default.fileExists(atPath:stopFile){break}
        Thread.sleep(forTimeInterval:0.1)
    }
    let up=CGEvent(keyboardEventSource:nil,virtualKey:49,keyDown:false);up?.flags=[];up?.post(tap:.cghidEventTap)
}
func chord(_ modifier: CGKeyCode, _ flags: CGEventFlags, _ code: CGKeyCode) {
    let down = CGEvent(keyboardEventSource:nil, virtualKey:modifier, keyDown:true)
    down?.flags=flags;down?.post(tap:.cghidEventTap)
    Thread.sleep(forTimeInterval:0.1)
    key(code, flags:flags)
    let up = CGEvent(keyboardEventSource:nil, virtualKey:modifier, keyDown:false)
    up?.flags=[];up?.post(tap:.cghidEventTap)
}
// HeroesData overrides the Core CameraFollow binding with L.
if command == "follow" { key(23); key(37) }
if command == "hud" { chord(56, .maskShift, 101) }
if command == "timeline" { chord(59, .maskControl, 17) }
if command == "restart" { chord(59, .maskControl, 14) }
if command == "back" || command == "next" {
    let count = CommandLine.arguments.count == 4 ? Int(CommandLine.arguments[3]) ?? 0 : 1
    guard count >= 1 && count <= 100 else { fatalError("Skip count must be1...100") }
    for _ in 0..<count { key(command == "back" ? 11 : 3); Thread.sleep(forTimeInterval:0.8) }
}
if command == "pause" { key(35) }
if command == "play-for" {
    guard CommandLine.arguments.count==4,let seconds=Double(CommandLine.arguments[3]),seconds>=0.5,seconds<=60 else {exit(2)}
    let started=ProcessInfo.processInfo.systemUptime
    key(35)
    Thread.sleep(forTimeInterval:max(0,seconds-(ProcessInfo.processInfo.systemUptime-started)))
    key(35)
}
if command == "faster" { key(24) }
if command == "slower" { key(27) }
if command == "seek" {
    guard CommandLine.arguments.count == 4, let fraction = Double(CommandLine.arguments[3]),
          fraction >= 0, fraction <= 0.95 else { fatalError("seek fraction must be0...0.95") }
    checkFocus()
    let point = CGPoint(x: x + width * (0.785 + 0.195 * fraction), y: y + height * 0.162)
    CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.1)
    checkFocus()
    CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.08)
    CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
}
print("Replay command delivered: \(command), PID \(pid)")
