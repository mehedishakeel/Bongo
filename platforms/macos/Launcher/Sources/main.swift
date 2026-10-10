import Cocoa
import Carbon

private let inputMethodIdentifier = "org.bongo.inputmethod.Bongo"

final class LauncherDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        guard let embedded = embeddedInputMethod() else {
            showError("Bongo is incomplete", "The embedded keyboard is missing. Download Bongo again from the official GitHub Releases page.")
            return
        }

        let installed = installedInputMethod()
        let targetURL: URL

        if let installed, !isOlder(installed, than: embedded) {
            targetURL = installed
        } else {
            do {
                targetURL = try installInputMethod(from: embedded)
            } catch {
                showError("The keyboard could not be installed", error.localizedDescription)
                return
            }
        }

        registerInputMethod(at: targetURL)
        openInputMethod(targetURL)
    }

    private func embeddedInputMethod() -> URL? {
        let url = Bundle.main.bundleURL
            .appendingPathComponent("Contents/Library/Input Methods/Bongo Input Method.app")
        return validInputMethod(at: url, allowEmbedded: true) ? url : nil
    }

    private func installedInputMethod() -> URL? {
        let home = FileManager.default.homeDirectoryForCurrentUser
        let candidates = [
            home.appendingPathComponent("Library/Input Methods/Bongo.app"),
            home.appendingPathComponent("Library/Input Methods/Bongo Input Method.app"),
            URL(fileURLWithPath: "/Library/Input Methods/Bongo.app"),
            URL(fileURLWithPath: "/Library/Input Methods/Bongo Input Method.app"),
        ]
        return candidates.first(where: { validInputMethod(at: $0, allowEmbedded: false) })
    }

    private func validInputMethod(at url: URL, allowEmbedded: Bool) -> Bool {
        if !allowEmbedded && url.path.contains("/Contents/Library/Input Methods") {
            return false
        }
        return FileManager.default.fileExists(atPath: url.path) && Bundle(url: url)?.bundleIdentifier == inputMethodIdentifier
    }

    private func isOlder(_ installed: URL, than embedded: URL) -> Bool {
        let installedVersion = Bundle(url: installed)?.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
        let embeddedVersion = Bundle(url: embedded)?.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
        let versionOrder = installedVersion.compare(embeddedVersion, options: .numeric)
        if versionOrder != .orderedSame { return versionOrder == .orderedAscending }
        let installedBuild = Bundle(url: installed)?.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "0"
        let embeddedBuild = Bundle(url: embedded)?.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "0"
        return installedBuild.compare(embeddedBuild, options: .numeric) == .orderedAscending
    }

    private func installInputMethod(from source: URL) throws -> URL {
        let manager = FileManager.default
        let directory = manager.homeDirectoryForCurrentUser.appendingPathComponent("Library/Input Methods", isDirectory: true)
        try manager.createDirectory(at: directory, withIntermediateDirectories: true)
        let destination = directory.appendingPathComponent("Bongo.app", isDirectory: true)
        let temporary = directory.appendingPathComponent(".Bongo-install-\(UUID().uuidString).app", isDirectory: true)

        // Terminate any running instance before replacing files
        let runningApps = NSRunningApplication.runningApplications(withBundleIdentifier: inputMethodIdentifier)
        for app in runningApps {
            app.terminate()
        }

        do {
            try manager.copyItem(at: source, to: temporary)
            if manager.fileExists(atPath: destination.path) {
                _ = try manager.replaceItemAt(destination, withItemAt: temporary)
            } else {
                try manager.moveItem(at: temporary, to: destination)
            }
            return destination
        } catch {
            try? manager.removeItem(at: temporary)
            throw error
        }
    }

    private func registerInputMethod(at url: URL) {
        _ = LSRegisterURL(url as CFURL, true)
        _ = TISRegisterInputSource(url as CFURL)

        if let list = TISCreateInputSourceList(nil, true)?.takeRetainedValue() as? [TISInputSource] {
            for source in list {
                let idPtr = TISGetInputSourceProperty(source, kTISPropertyInputSourceID)
                let sId = idPtr != nil ? Unmanaged<CFString>.fromOpaque(idPtr!).takeUnretainedValue() as String : ""
                if sId == inputMethodIdentifier {
                    _ = TISEnableInputSource(source)
                }
            }
        }

        // Ensure Bongo is added to AppleEnabledInputSources in com.apple.HIToolbox
        let key = "AppleEnabledInputSources" as CFString
        let domain = "com.apple.HIToolbox" as CFString
        if let existing = CFPreferencesCopyAppValue(key, domain) as? [[String: Any]] {
            let alreadyPresent = existing.contains { ($0["Bundle ID"] as? String) == inputMethodIdentifier }
            if !alreadyPresent {
                var updated = existing
                updated.append([
                    "Bundle ID": inputMethodIdentifier,
                    "InputSourceKind": "Keyboard Input Method"
                ])
                CFPreferencesSetAppValue(key, updated as CFArray, domain)
                CFPreferencesAppSynchronize(domain)
            }
        }
    }

    private func openInputMethod(_ url: URL) {
        let configuration = NSWorkspace.OpenConfiguration()
        configuration.activates = true
        configuration.addsToRecentItems = false
        configuration.arguments = ["--show-settings"]
        NSWorkspace.shared.openApplication(at: url, configuration: configuration) { _, error in
            DispatchQueue.main.async {
                if let error {
                    self.showError("Bongo could not open", error.localizedDescription)
                } else {
                    NSApp.terminate(nil)
                }
            }
        }
    }

    private func showError(_ title: String, _ message: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.addButton(withTitle: "Close")
        alert.runModal()
        NSApp.terminate(nil)
    }
}

let delegate = LauncherDelegate()
NSApplication.shared.delegate = delegate
withExtendedLifetime(delegate) {
    NSApplication.shared.run()
}
