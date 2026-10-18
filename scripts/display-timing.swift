import AppKit
import ScreenCaptureKit
import CoreMedia
import Foundation

// Read-only timing probe. Scales the display capture to64px; saves metadata only.
// Complete display frames are compositor updates, not proof of game attribution.
guard CommandLine.arguments.count == 3, let duration=Double(CommandLine.arguments[1]), duration>0 else {
    fputs("usage: display-timing SECONDS OUTPUT.jsonl\n", stderr); exit(2)
}
let output=CommandLine.arguments[2]
FileManager.default.createFile(atPath:output, contents:nil)
let file=FileHandle(forWritingAtPath:output)!
func write(_ value:[String:Any]) {
    file.write(try! JSONSerialization.data(withJSONObject:value, options:[.sortedKeys]));file.write(Data([10]))
}
var tb=mach_timebase_info_data_t();mach_timebase_info(&tb)
write(["kind":"header","wall":Date().timeIntervalSince1970,"mach":mach_absolute_time(),"numer":tb.numer,"denom":tb.denom,"source":"ScreenCaptureKit displayTime","size":64])
final class Sink:NSObject,SCStreamOutput,SCStreamDelegate {
    func stream(_ stream:SCStream, didOutputSampleBuffer sampleBuffer:CMSampleBuffer, of type:SCStreamOutputType) {
        guard type == .screen, let info=(CMSampleBufferGetSampleAttachmentsArray(sampleBuffer, createIfNecessary:false) as? [[SCStreamFrameInfo:Any]])?.first else {return}
        write(["kind":"frame","status":info[.status] as? Int ?? -1,"display_mach":(info[.displayTime] as? NSNumber)?.uint64Value ?? 0,"callback_mach":mach_absolute_time()])
    }
    func stream(_ stream:SCStream, didStopWithError error:Error) {fputs("\(error)\n",stderr);exit(3)}
}
let sink=Sink()
var retainedStream:SCStream?
SCShareableContent.getExcludingDesktopWindows(true,onScreenWindowsOnly:true) {content,error in
    guard let display=content?.displays.first(where:{$0.displayID==CGMainDisplayID()}) else {fputs("\(String(describing:error))\n",stderr);exit(3)}
    let filter=SCContentFilter(display:display,excludingWindows:[])
    let config=SCStreamConfiguration();config.width=64;config.height=64
    config.minimumFrameInterval=CMTime(value:1,timescale:240);config.queueDepth=8
    config.showsCursor=false;config.capturesAudio=false
    let stream=SCStream(filter:filter,configuration:config,delegate:sink);retainedStream=stream
    do {try stream.addStreamOutput(sink,type:.screen,sampleHandlerQueue:DispatchQueue(label:"hots.display-timing"))} catch {fputs("\(error)\n",stderr);exit(3)}
    stream.startCapture {error in
        if let error=error {fputs("\(error)\n",stderr);exit(3)}
        DispatchQueue.main.asyncAfter(deadline:.now()+duration) {
            stream.stopCapture {_ in try? file.close();exit(0)}
        }
    }
}
RunLoop.main.run()
