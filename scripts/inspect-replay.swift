import Foundation
import CoreGraphics
import Vision

// Read-only screenshot/OCR for the replay clock and seek state. Use outside samples.
guard CommandLine.arguments.count==3,let pid=Int(CommandLine.arguments[1]) else {exit(2)}
let windows=CGWindowListCopyWindowInfo(.optionAll,0) as? [[String:Any]] ?? []
guard let w=windows.first(where:{($0[kCGWindowOwnerPID as String] as? Int)==pid && ($0[kCGWindowName as String] as? String)=="Heroes of the Storm"}),let id=w[kCGWindowNumber as String] as? Int else {exit(3)}
let path=CommandLine.arguments[2];let capture=Process();capture.executableURL=URL(fileURLWithPath:"/usr/sbin/screencapture");capture.arguments=["-x","-l\(id)",path];try capture.run();capture.waitUntilExit();guard capture.terminationStatus==0 else {exit(4)}
func recognize(_ region:CGRect)->[String] {
    let request=VNRecognizeTextRequest();request.recognitionLevel = .accurate;request.usesLanguageCorrection=false;request.regionOfInterest=region
    try? VNImageRequestHandler(url:URL(fileURLWithPath:path)).perform([request])
    return request.results?.compactMap{$0.topCandidates(1).first?.string} ?? []
}
let clock=recognize(CGRect(x:0.44,y:0.84,width:0.12,height:0.06)).filter {
    $0.range(of:"^-?[0-9]+:[0-9]{2}$",options:.regularExpression) != nil
}
let data:[String:Any] = ["wall":Date().timeIntervalSince1970,"window_id":id,"bounds":w[kCGWindowBounds as String]!,"clock":clock,"state":recognize(CGRect(x:0.40,y:0.60,width:0.20,height:0.10))]
print(String(data:try! JSONSerialization.data(withJSONObject:data,options:[.sortedKeys]),encoding:.utf8)!)
