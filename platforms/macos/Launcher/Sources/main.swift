import Cocoa

private let inputMethodIdentifier = "org.bongo.inputmethod.Bongo"

final class LauncherDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        guard let embedded = embeddedInputMethod() else {
            showError("Bongo is incomplete", "The embedded keyboard is missing. Download Bongo again from the official GitHub Releases page.")
            return
        }

        let installed = installedInputMethod()
        if let installed, !isOlder(installed, than: embedded) {
            openInputMethod(installed)
            return
        }

        let alert = NSAlert()
        alert.messageText = installed == nil ? "Install the Bongo keyboard?" : "Update the Bongo keyboard?"
        alert.informativeText = "Bongo will copy its keyboard to your user Input Methods folder. macOS may require one log out and log in before it appears in Keyboard settings."
        alert.addButton(withTitle: installed == nil ? "Install" : "Update")
        alert.addButton(withTitle: "Not Now")
        guard alert.runModal() == .alertFirstButtonReturn else {
            if let installed { openInputMethod(installed) } else { NSApp.terminate(nil) }
            return
        }

        do {
            let destination = try installInputMethod(from: embedded)
            openInputMethod(destination)
        } catch {
            showError("The keyboard could not be installed", error.localizedDescription)
        }
    }

    private func embeddedInputMethod() -> URL? {
        let url = Bundle.main.bundleURL
            .appendingPathComponent("Contents/Library/Input Methods/Bongo Input Method.app")
        return validInputMethod(at: url) ? url : nil
    }

    private func installedInputMethod() -> URL? {
        let home = FileManager.default.homeDirectoryForCurrentUser
        var candidates = [
            home.appendingPathComponent("Library/Input Methods/Bongo.app"),
            home.appendingPathComponent("Library/Input Methods/Bongo Input Method.app"),
            URL(fileURLWithPath: "/Library/Input Methods/Bongo.app"),
            URL(fileURLWithPath: "/Library/Input Methods/Bongo Input Method.app"),
        ]
        if let registered = NSWorkspace.shared.urlForApplication(withBundleIdentifier: inputMethodIdentifier) {
            candidates.append(registered)
        }
        return candidates.first(where: validInputMethod)
    }

    private func validInputMethod(at url: URL) -> Bool {
        FileManager.default.fileExists(atPath: url.path) && Bundle(url: url)?.bundleIdentifier == inputMethodIdentifier
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
