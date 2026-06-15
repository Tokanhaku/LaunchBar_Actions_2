import Foundation
import CoreServices

let text = Array(CommandLine.arguments.dropFirst())[0]
let detectedLanguage = CFStringTokenizerCopyBestStringLanguage(text as CFString, CFRangeMake(0, text.count))

print("\(detectedLanguage!)")
