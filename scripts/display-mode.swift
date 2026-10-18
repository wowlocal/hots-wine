import CoreGraphics
import Foundation

// Session-only display geometry; original mode is retained for restoration.
guard (2...3).contains(CommandLine.arguments.count), ["native1x","restore"].contains(CommandLine.arguments[1]) else {exit(2)}
let display=CGMainDisplayID()
let base=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/CrossOver/HotS-Setup")
let backup=CommandLine.arguments.count==3 ? URL(fileURLWithPath:CommandLine.arguments[2]) : base.appendingPathComponent("display-mode-backup.json")
guard let current=CGDisplayCopyDisplayMode(display),let modes=CGDisplayCopyAllDisplayModes(display,[kCGDisplayShowDuplicateLowResolutionModes:true] as CFDictionary) as? [CGDisplayMode] else {exit(3)}
let mode:CGDisplayMode
if CommandLine.arguments[1]=="native1x" {
    guard current.pixelWidth==3456,current.pixelHeight==2234 else {fputs("Unexpected display; no change made\n",stderr);exit(4)}
    if !FileManager.default.fileExists(atPath:backup.path) {
        let state:[String:Any]=["mode_id":current.ioDisplayModeID,"width":current.width,"height":current.height,"pixel_width":current.pixelWidth,"pixel_height":current.pixelHeight,"refresh_rate":current.refreshRate]
        try JSONSerialization.data(withJSONObject:state,options:[.prettyPrinted,.sortedKeys]).write(to:backup)
    }
    guard let target=modes.first(where:{$0.width==3456 && $0.height==2234 && $0.pixelWidth==3456 && abs($0.refreshRate-120)<0.01}) else {exit(5)}
    mode=target
} else {
    let state=try JSONSerialization.jsonObject(with:Data(contentsOf:backup)) as! [String:Any]
    guard let target=modes.first(where:{$0.ioDisplayModeID==(state["mode_id"] as! NSNumber).uint32Value}) else {exit(6)}
    mode=target
}
var config:CGDisplayConfigRef?
guard CGBeginDisplayConfiguration(&config) == .success else {exit(7)}
guard CGConfigureDisplayWithDisplayMode(config,display,mode,nil) == .success else {CGCancelDisplayConfiguration(config);exit(8)}
guard CGCompleteDisplayConfiguration(config,.forSession) == .success else {exit(9)}
print("Display mode: \(mode.width)x\(mode.height) points, \(mode.pixelWidth)x\(mode.pixelHeight) pixels, \(mode.refreshRate)Hz")
