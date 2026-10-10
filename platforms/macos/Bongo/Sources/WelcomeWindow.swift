import Cocoa
import CoreText
import WebKit

// MARK: - Window Controller (Singleton)

class WelcomeWindowController {
    static let shared = WelcomeWindowController()

    private var window: NSWindow?
    private var tabView: WelcomeTabView?

    func showWindow(tabIndex: Int = 0) {
        if let window = window, let tabView = tabView {
            tabView.selectTab(tabIndex)
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }

        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 920, height: 640),
            styleMask: [.titled, .closable, .miniaturizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.title = "Bongo"
        window.titlebarAppearsTransparent = true
        window.titleVisibility = .hidden
        window.backgroundColor = .windowBackgroundColor
        window.isReleasedWhenClosed = false
        window.isRestorable = false
        window.isMovableByWindowBackground = true
        window.minSize = NSSize(width: 840, height: 580)

        let contentView = WelcomeTabView()
        window.contentView = contentView
        window.center()

        self.window = window
        self.tabView = contentView

        contentView.selectTab(tabIndex)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}

// MARK: - Sidebar Navigation Button

final class SidebarNavigationButton: NSButton {
    private let iconView = NSImageView()
    private let titleLabel = NSTextField(labelWithString: "")
    private let marker = NSView()
    private var trackingAreaRef: NSTrackingArea?
    private var isHovered = false

    var isActive = false {
        didSet { updateAppearance() }
    }

    init(title: String, symbol: String, target: AnyObject?, action: Selector?) {
        super.init(frame: .zero)
        self.target = target
        self.action = action
        self.title = ""
        isBordered = false
        setButtonType(.momentaryChange)
        focusRingType = .none
        wantsLayer = true
        layer?.cornerRadius = 8
        layer?.cornerCurve = .continuous
        translatesAutoresizingMaskIntoConstraints = false

        iconView.image = NSImage(systemSymbolName: symbol, accessibilityDescription: nil)
        iconView.imageScaling = .scaleProportionallyDown
        iconView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(iconView)

        titleLabel.stringValue = title
        titleLabel.font = .systemFont(ofSize: 13.5, weight: .medium)
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        addSubview(titleLabel)

        marker.wantsLayer = true
        marker.layer?.cornerRadius = 1.5
        marker.translatesAutoresizingMaskIntoConstraints = false
        addSubview(marker)

        setAccessibilityElement(true)
        setAccessibilityRole(.button)
        setAccessibilityLabel(title)

        NSLayoutConstraint.activate([
            marker.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 5),
            marker.centerYAnchor.constraint(equalTo: centerYAnchor),
            marker.widthAnchor.constraint(equalToConstant: 3),
            marker.heightAnchor.constraint(equalToConstant: 18),

            iconView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            iconView.centerYAnchor.constraint(equalTo: centerYAnchor),
            iconView.widthAnchor.constraint(equalToConstant: 16),
            iconView.heightAnchor.constraint(equalToConstant: 16),

            titleLabel.leadingAnchor.constraint(equalTo: iconView.trailingAnchor, constant: 10),
            titleLabel.centerYAnchor.constraint(equalTo: centerYAnchor),
            titleLabel.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -12),
        ])
        updateAppearance()
    }

    required init?(coder: NSCoder) { fatalError() }

    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let trackingAreaRef { removeTrackingArea(trackingAreaRef) }
        let area = NSTrackingArea(
            rect: bounds,
            options: [.activeInKeyWindow, .mouseEnteredAndExited, .inVisibleRect],
            owner: self,
            userInfo: nil)
        addTrackingArea(area)
        trackingAreaRef = area
    }

    override func mouseEntered(with event: NSEvent) {
        isHovered = true
        updateAppearance()
    }

    override func mouseExited(with event: NSEvent) {
        isHovered = false
        updateAppearance()
    }

    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }

    override func accessibilityPerformPress() -> Bool {
        _ = sendAction(action, to: target)
        return true
    }

    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        updateAppearance()
    }

    private func updateAppearance() {
        effectiveAppearance.performAsCurrentDrawingAppearance {
            let tint = WelcomeUI.accent
            if isActive {
                layer?.backgroundColor = tint.withAlphaComponent(0.14).cgColor
                marker.layer?.backgroundColor = tint.cgColor
                iconView.contentTintColor = tint
                titleLabel.textColor = .labelColor
                titleLabel.font = .systemFont(ofSize: 13.5, weight: .semibold)
            } else if isHovered {
                layer?.backgroundColor = NSColor.labelColor.withAlphaComponent(0.06).cgColor
                marker.layer?.backgroundColor = NSColor.clear.cgColor
                iconView.contentTintColor = .labelColor
                titleLabel.textColor = .labelColor
                titleLabel.font = .systemFont(ofSize: 13.5, weight: .medium)
            } else {
                layer?.backgroundColor = NSColor.clear.cgColor
                marker.layer?.backgroundColor = NSColor.clear.cgColor
                iconView.contentTintColor = .secondaryLabelColor
                titleLabel.textColor = .secondaryLabelColor
                titleLabel.font = .systemFont(ofSize: 13.5, weight: .medium)
            }
            setAccessibilityValue(isActive ? "Selected" : "")
        }
    }
}

// MARK: - Welcome Tab View (Modern Split Layout)

final class FlippedVisualEffectView: NSVisualEffectView {
    override var isFlipped: Bool { true }
}

class WelcomeTabView: NSView {
    override var isFlipped: Bool { true }

    private let tabView = NSTabView()
    private var buttons: [SidebarNavigationButton] = []
    private let heading = NSTextField(labelWithString: "Getting Started")
    private let subtitle = NSTextField(labelWithString: "Everything you need to begin typing in Bangla.")
    private let titles = ["Getting Started", "Bongo Layout", "Settings", "Fonts"]
    private let subtitles = [
        "Everything you need to begin typing in Bangla.",
        "The complete phonetic key map at a glance.",
        "Choose how Bongo behaves while you type.",
        "Make the suggestion popup comfortable to read.",
    ]

    override init(frame: NSRect) {
        super.init(frame: frame)
        setupLayout()
    }

    required init?(coder: NSCoder) { fatalError() }

    override func draw(_ dirtyRect: NSRect) {
        NSColor.windowBackgroundColor.setFill()
        dirtyRect.fill()
        super.draw(dirtyRect)
    }

    private func setupLayout() {
        wantsLayer = true

        // Translucent macOS Sidebar
        let sidebar = FlippedVisualEffectView()
        sidebar.material = .sidebar
        sidebar.blendingMode = .withinWindow
        sidebar.state = .active
        sidebar.translatesAutoresizingMaskIntoConstraints = false
        addSubview(sidebar)

        // Sidebar Header: App Icon & Brand
        var iconImage: NSImage?
        if let resPath = Bundle.main.path(forResource: "AppIcon", ofType: "icns") {
            iconImage = NSImage(contentsOfFile: resPath)
        }
        if iconImage == nil {
            iconImage = Bundle.main.image(forResource: "AppIcon")
        }
        if iconImage == nil {
            iconImage = NSImage(contentsOfFile: "platforms/macos/Bongo/Resources/AppIcon.icns")
        }
        if iconImage == nil, let appIcon = NSImage(named: NSImage.applicationIconName), appIcon.isValid {
            iconImage = appIcon
        }
        let brandIcon = NSImageView(image: iconImage ?? NSApp.applicationIconImage)
        brandIcon.imageScaling = .scaleProportionallyUpOrDown
        brandIcon.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(brandIcon)

        let brand = NSTextField(labelWithString: "Bongo")
        brand.font = .systemFont(ofSize: 22, weight: .bold)
        brand.textColor = WelcomeUI.accent
        brand.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(brand)

        // Navigation Menu
        let nav = NSStackView()
        nav.orientation = .vertical
        nav.alignment = .leading
        nav.spacing = 6
        nav.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(nav)

        let labels = ["Getting Started", "Bongo Layout", "Settings", "Fonts"]
        let symbols = ["sparkles", "keyboard.fill", "slider.horizontal.3", "textformat"]
        for i in 0..<labels.count {
            let button = SidebarNavigationButton(
                title: labels[i], symbol: symbols[i], target: self, action: #selector(navigate(_:)))
            button.tag = i
            nav.addArrangedSubview(button)
            button.widthAnchor.constraint(equalTo: nav.widthAnchor).isActive = true
            button.heightAnchor.constraint(equalToConstant: 36).isActive = true
            buttons.append(button)
        }

        let versionString = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        let version = NSTextField(labelWithString: "v\(versionString) · arm64")
        version.font = .monospacedSystemFont(ofSize: 10.5, weight: .regular)
        version.textColor = .tertiaryLabelColor
        version.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(version)

        let authorLabel = NSTextField(labelWithString: "Developed by Mehedi Shakeel")
        authorLabel.font = .systemFont(ofSize: 10.5, weight: .medium)
        authorLabel.textColor = .tertiaryLabelColor
        authorLabel.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(authorLabel)

        // Content Area Header
        heading.font = .systemFont(ofSize: 26, weight: .bold)
        heading.translatesAutoresizingMaskIntoConstraints = false
        addSubview(heading)

        subtitle.font = .systemFont(ofSize: 13)
        subtitle.textColor = .secondaryLabelColor
        subtitle.translatesAutoresizingMaskIntoConstraints = false
        addSubview(subtitle)

        // Content Tabs
        tabView.tabViewType = .noTabsNoBorder
        tabView.wantsLayer = true
        tabView.translatesAutoresizingMaskIntoConstraints = false

        for (index, view) in [GettingStartedView(), LayoutWebView(), SettingsView(), FontsView()].enumerated() {
            let item = NSTabViewItem(identifier: index)
            item.view = view
            tabView.addTabViewItem(item)
        }
        addSubview(tabView)

        NSLayoutConstraint.activate([
            sidebar.leadingAnchor.constraint(equalTo: leadingAnchor),
            sidebar.topAnchor.constraint(equalTo: topAnchor),
            sidebar.bottomAnchor.constraint(equalTo: bottomAnchor),
            sidebar.widthAnchor.constraint(equalToConstant: 216),

            brandIcon.leadingAnchor.constraint(equalTo: sidebar.leadingAnchor, constant: 20),
            brandIcon.topAnchor.constraint(equalTo: sidebar.topAnchor, constant: 36),
            brandIcon.widthAnchor.constraint(equalToConstant: 34),
            brandIcon.heightAnchor.constraint(equalToConstant: 34),

            brand.leadingAnchor.constraint(equalTo: brandIcon.trailingAnchor, constant: 10),
            brand.centerYAnchor.constraint(equalTo: brandIcon.centerYAnchor),

            nav.leadingAnchor.constraint(equalTo: sidebar.leadingAnchor, constant: 14),
            nav.trailingAnchor.constraint(equalTo: sidebar.trailingAnchor, constant: -14),
            nav.topAnchor.constraint(equalTo: brandIcon.bottomAnchor, constant: 28),

            version.leadingAnchor.constraint(equalTo: sidebar.leadingAnchor, constant: 20),
            version.bottomAnchor.constraint(equalTo: authorLabel.topAnchor, constant: -4),

            authorLabel.leadingAnchor.constraint(equalTo: version.leadingAnchor),
            authorLabel.bottomAnchor.constraint(equalTo: sidebar.bottomAnchor, constant: -18),

            heading.leadingAnchor.constraint(equalTo: sidebar.trailingAnchor, constant: 32),
            heading.topAnchor.constraint(equalTo: topAnchor, constant: 32),

            subtitle.leadingAnchor.constraint(equalTo: heading.leadingAnchor),
            subtitle.topAnchor.constraint(equalTo: heading.bottomAnchor, constant: 6),

            tabView.leadingAnchor.constraint(equalTo: sidebar.trailingAnchor),
            tabView.trailingAnchor.constraint(equalTo: trailingAnchor),
            tabView.topAnchor.constraint(equalTo: subtitle.bottomAnchor, constant: 16),
            tabView.bottomAnchor.constraint(equalTo: bottomAnchor),
        ])

        selectTab(0)
    }

    @objc private func navigate(_ sender: SidebarNavigationButton) { selectTab(sender.tag) }

    func selectTab(_ index: Int) {
        guard titles.indices.contains(index), index < tabView.numberOfTabViewItems else { return }
        tabView.selectTabViewItem(at: index)
        heading.stringValue = titles[index]
        subtitle.stringValue = subtitles[index]
        for (i, button) in buttons.enumerated() {
            button.isActive = (i == index)
        }
    }
}

// MARK: - Shared Welcome UI Helpers

enum WelcomeUI {
    static let pageInset: CGFloat = 32
    static let accent: NSColor = NSColor(name: nil) { appearance in
        let isDark = appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
        return isDark
            ? NSColor(srgbRed: 129/255, green: 140/255, blue: 248/255, alpha: 1.0)
            : NSColor(srgbRed: 79/255, green: 70/255, blue: 229/255, alpha: 1.0)
    }

    static func sectionHeader(_ text: String) -> NSTextField {
        let label = NSTextField(labelWithString: "")
        let attr = NSMutableAttributedString(string: text.uppercased())
        attr.addAttributes(
            [
                .font: NSFont.systemFont(ofSize: 11, weight: .bold),
                .foregroundColor: NSColor.secondaryLabelColor,
                .kern: 0.6,
            ],
            range: NSRange(location: 0, length: attr.length))
        label.attributedStringValue = attr
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }

    static func keyChip(_ text: String) -> NSView {
        let chip = RoundedTintView(
            cornerRadius: 5,
            fill: { NSColor.labelColor.withAlphaComponent(0.07) },
            border: { NSColor.separatorColor.withAlphaComponent(0.4) })
        let label = NSTextField(labelWithString: text)
        label.font = NSFont.monospacedSystemFont(ofSize: 11.5, weight: .semibold)
        label.textColor = .labelColor
        label.translatesAutoresizingMaskIntoConstraints = false
        chip.addSubview(label)
        NSLayoutConstraint.activate([
            label.leadingAnchor.constraint(equalTo: chip.leadingAnchor, constant: 7),
            label.trailingAnchor.constraint(equalTo: chip.trailingAnchor, constant: -7),
            label.topAnchor.constraint(equalTo: chip.topAnchor, constant: 2),
            label.bottomAnchor.constraint(equalTo: chip.bottomAnchor, constant: -2),
        ])
        return chip
    }
}

class RoundedTintView: NSView {
    override var isFlipped: Bool { true }
    private let fillColor: () -> NSColor
    private let borderColor: (() -> NSColor)?

    init(cornerRadius: CGFloat, borderWidth: CGFloat = 0.5,
         fill: @escaping () -> NSColor, border: (() -> NSColor)? = nil) {
        self.fillColor = fill
        self.borderColor = border
        super.init(frame: .zero)
        wantsLayer = true
        layer?.cornerRadius = cornerRadius
        layer?.cornerCurve = .continuous
        layer?.borderWidth = border == nil ? 0 : borderWidth
        translatesAutoresizingMaskIntoConstraints = false
        applyColors()
    }
    required init?(coder: NSCoder) { fatalError() }

    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        applyColors()
    }

    func refreshColors() { applyColors() }

    private func applyColors() {
        effectiveAppearance.performAsCurrentDrawingAppearance { [self] in
            layer?.backgroundColor = fillColor().cgColor
            if let borderColor { layer?.borderColor = borderColor().cgColor }
        }
    }
}

final class CardContainer: RoundedTintView {
    init(content: NSView, insets: NSEdgeInsets = NSEdgeInsets(top: 14, left: 18, bottom: 14, right: 18)) {
        super.init(
            cornerRadius: 12,
            borderWidth: 0.5,
            fill: { NSColor.controlBackgroundColor.withAlphaComponent(0.6) },
            border: { NSColor.separatorColor.withAlphaComponent(0.35) })
        content.translatesAutoresizingMaskIntoConstraints = false
        addSubview(content)
        NSLayoutConstraint.activate([
            content.topAnchor.constraint(equalTo: topAnchor, constant: insets.top),
            content.leadingAnchor.constraint(equalTo: leadingAnchor, constant: insets.left),
            content.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -insets.right),
            content.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -insets.bottom),
        ])
    }
    required init?(coder: NSCoder) { fatalError() }
}

final class PillBadge: NSView {
    override var isFlipped: Bool { true }

    init(text: String, color: NSColor = WelcomeUI.accent) {
        super.init(frame: .zero)
        wantsLayer = true
        layer?.cornerRadius = 10
        layer?.cornerCurve = .continuous
        layer?.backgroundColor = color.withAlphaComponent(0.14).cgColor
        translatesAutoresizingMaskIntoConstraints = false

        let label = NSTextField(labelWithString: text)
        label.font = NSFont.systemFont(ofSize: 10.5, weight: .bold)
        label.textColor = color
        label.translatesAutoresizingMaskIntoConstraints = false
        addSubview(label)

        NSLayoutConstraint.activate([
            label.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 8),
            label.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8),
            label.topAnchor.constraint(equalTo: topAnchor, constant: 2),
            label.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -2),
        ])
    }
    required init?(coder: NSCoder) { fatalError() }
}

// MARK: - Getting Started Tab

final class GettingStartedView: NSView {
    override var isFlipped: Bool { true }

    override init(frame: NSRect) {
        super.init(frame: frame)
        setupUI()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setupUI() {
        let stack = NSStackView()
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 14
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 12),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: WelcomeUI.pageInset),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -WelcomeUI.pageInset),
        ])

        // Step 1 Card: Enable in Settings
        let s1Title = NSTextField(labelWithString: "1. Enable Bongo in Keyboard Settings")
        s1Title.font = .systemFont(ofSize: 14, weight: .semibold)
        let s1Desc = NSTextField(wrappingLabelWithString:
            "Open macOS System Settings → Keyboard → Input Sources → Edit, click +, and add Bongo under Bengali.")
        s1Desc.font = .systemFont(ofSize: 12.5)
        s1Desc.textColor = .secondaryLabelColor

        let openSettingsBtn = NSButton(title: "Open Keyboard Settings…", target: self, action: #selector(openKeyboardSettings))
        openSettingsBtn.bezelStyle = .rounded
        openSettingsBtn.image = NSImage(systemSymbolName: "arrow.up.forward.app", accessibilityDescription: nil)
        openSettingsBtn.imagePosition = .imageTrailing

        let s1Stack = NSStackView(views: [s1Title, s1Desc, openSettingsBtn])
        s1Stack.orientation = .vertical
        s1Stack.alignment = .leading
        s1Stack.spacing = 8
        let s1Card = CardContainer(content: s1Stack)
        stack.addArrangedSubview(s1Card)
        s1Card.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true

        // Step 2 Card: Switch Languages
        let s2Title = NSTextField(labelWithString: "2. Switch Keyboards Quickly")
        s2Title.font = .systemFont(ofSize: 14, weight: .semibold)
        let s2Desc = NSTextField(wrappingLabelWithString:
            "Press the Globe (🌐) key or Control-Space anytime to toggle between English and Bongo.")
        s2Desc.font = .systemFont(ofSize: 12.5)
        s2Desc.textColor = .secondaryLabelColor

        let shortcutChip1 = WelcomeUI.keyChip("🌐 Globe")
        let shortcutChip2 = WelcomeUI.keyChip("⌃ Control + Space")
        let chips = NSStackView(views: [shortcutChip1, shortcutChip2])
        chips.orientation = .horizontal
        chips.spacing = 8

        let s2Stack = NSStackView(views: [s2Title, s2Desc, chips])
        s2Stack.orientation = .vertical
        s2Stack.alignment = .leading
        s2Stack.spacing = 8
        let s2Card = CardContainer(content: s2Stack)
        stack.addArrangedSubview(s2Card)
        s2Card.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true

        // Step 3 Card: Phonetic Typing
        let s3Title = NSTextField(labelWithString: "3. Type Natural Phonetic Bangla")
        s3Title.font = .systemFont(ofSize: 14, weight: .semibold)
        let s3Desc = NSTextField(wrappingLabelWithString:
            "Type English letters phonetically according to how words sound. For example, ami becomes আমি, bangla becomes বাংলা, and dhonnobad becomes ধন্যবাদ.")
        s3Desc.font = .systemFont(ofSize: 12.5)
        s3Desc.textColor = .secondaryLabelColor

        let s3Stack = NSStackView(views: [s3Title, s3Desc])
        s3Stack.orientation = .vertical
        s3Stack.alignment = .leading
        s3Stack.spacing = 6
        let s3Card = CardContainer(content: s3Stack)
        stack.addArrangedSubview(s3Card)
        s3Card.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true

        // Playground Card
        let playTitle = NSTextField(labelWithString: "Interactive Typing Playground")
        playTitle.font = .systemFont(ofSize: 14, weight: .semibold)
        let playDesc = NSTextField(wrappingLabelWithString:
            "Select Bongo from the menu bar and try typing right inside this field:")
        playDesc.font = .systemFont(ofSize: 12)
        playDesc.textColor = .secondaryLabelColor

        let testField = NSTextField()
        testField.placeholderString = "Switch to Bongo and type here (e.g. ami banglay gan gai)..."
        testField.font = .systemFont(ofSize: 14)
        testField.focusRingType = .exterior

        let playStack = NSStackView(views: [playTitle, playDesc, testField])
        playStack.orientation = .vertical
        playStack.alignment = .leading
        playStack.spacing = 8
        let playCard = CardContainer(content: playStack)
        stack.addArrangedSubview(playCard)
        playCard.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        testField.widthAnchor.constraint(equalTo: playStack.widthAnchor).isActive = true
    }

    @objc private func openKeyboardSettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.Keyboard-Settings.extension") {
            NSWorkspace.shared.open(url)
        }
    }
}

// MARK: - Keyboard Guide (WKWebView for proper Bengali rendering)

class LayoutWebView: NSView {
    override var isFlipped: Bool { true }
    private var webView: WKWebView!

    override init(frame: NSRect) {
        super.init(frame: frame)
        setupWebView()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setupWebView() {
        let config = WKWebViewConfiguration()
        webView = WKWebView(frame: .zero, configuration: config)
        webView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(webView)

        NSLayoutConstraint.activate([
            webView.topAnchor.constraint(equalTo: topAnchor),
            webView.leadingAnchor.constraint(equalTo: leadingAnchor),
            webView.trailingAnchor.constraint(equalTo: trailingAnchor),
            webView.bottomAnchor.constraint(equalTo: bottomAnchor),
        ])

        webView.loadHTMLString(layoutHTML(), baseURL: nil)
    }

    private func layoutHTML() -> String {
        return """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            :root {
                --accent: #007aff;
                --text: #1d1d1f;
                --text-secondary: #86868b;
                --page-bg: #ffffff;
                --card-bg: rgba(0, 0, 0, 0.025);
                --card-border: rgba(0, 0, 0, 0.08);
                --row-border: rgba(0, 0, 0, 0.05);
                --key-bg: rgba(0, 0, 0, 0.05);
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --accent: #2997ff;
                    --text: #f5f5f7;
                    --text-secondary: #a1a1a6;
                    --page-bg: #1e1e1e;
                    --card-bg: rgba(255, 255, 255, 0.04);
                    --card-border: rgba(255, 255, 255, 0.10);
                    --row-border: rgba(255, 255, 255, 0.06);
                    --key-bg: rgba(255, 255, 255, 0.08);
                }
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro", "Helvetica Neue", sans-serif;
                padding: 20px 32px 40px 32px;
                background: var(--page-bg);
                color-scheme: light dark;
                color: var(--text);
                -webkit-font-smoothing: antialiased;
            }
            .search-box {
                margin-bottom: 20px;
            }
            .search-box input {
                width: 100%;
                padding: 10px 14px;
                border-radius: 9px;
                border: 1px solid var(--card-border);
                background: var(--card-bg);
                color: var(--text);
                font-size: 13px;
                outline: none;
                transition: border 0.15s ease;
            }
            .search-box input:focus {
                border-color: var(--accent);
            }
            .section-title {
                color: var(--text-secondary);
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.6px;
                text-transform: uppercase;
                margin: 20px 0 8px 2px;
            }
            .section-title:first-of-type { margin-top: 0; }
            table {
                width: 100%;
                table-layout: fixed;
                border-collapse: separate;
                border-spacing: 0;
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 12px;
                overflow: hidden;
            }
            td {
                padding: 8px 10px;
                border-bottom: 1px solid var(--row-border);
                vertical-align: middle;
                font-size: 13px;
            }
            tr:last-child td { border-bottom: none; }
            .bn {
                font-size: 16px;
                font-weight: 500;
                color: var(--text);
                width: 36px;
                text-align: center;
                font-family: "Bangla Sangam MN", "Kohinoor Bangla", -apple-system, sans-serif;
            }
            .key {
                font-size: 12px;
                font-weight: 600;
                color: var(--accent);
                font-family: "SF Mono", Menlo, monospace;
            }
            .key-badge {
                display: inline-block;
                padding: 2px 7px;
                border-radius: 4px;
                background: var(--key-bg);
            }
            .sep { width: 14px; }
        </style>
        <script>
        function filterKeys() {
            var q = document.getElementById('search').value.toLowerCase().trim();
            var rows = document.querySelectorAll('table tr');
            rows.forEach(function(row) {
                if (!q) { row.style.display = ''; return; }
                var text = row.innerText.toLowerCase();
                row.style.display = text.indexOf(q) !== -1 ? '' : 'none';
            });
        }
        </script>
        </head>
        <body>

        <div class="search-box">
            <input type="text" id="search" onkeyup="filterKeys()" placeholder="Quick filter keys (e.g. k, sh, a, Z)...">
        </div>

        <div class="section-title">Consonants · ব্যঞ্জনবর্ণ</div>
        <table>
        <tr>
            <td class="bn">\u{0995}</td><td class="key"><span class="key-badge">k</span></td><td class="sep"></td>
            <td class="bn">\u{099F}</td><td class="key"><span class="key-badge">T</span></td><td class="sep"></td>
            <td class="bn">\u{09AA}</td><td class="key"><span class="key-badge">p</span></td><td class="sep"></td>
            <td class="bn">\u{09B8}</td><td class="key"><span class="key-badge">s</span></td>
        </tr>
        <tr>
            <td class="bn">\u{0996}</td><td class="key"><span class="key-badge">kh</span></td><td class="sep"></td>
            <td class="bn">\u{09A0}</td><td class="key"><span class="key-badge">Th</span></td><td class="sep"></td>
            <td class="bn">\u{09AB}</td><td class="key"><span class="key-badge">ph, f</span></td><td class="sep"></td>
            <td class="bn">\u{09B9}</td><td class="key"><span class="key-badge">h</span></td>
        </tr>
        <tr>
            <td class="bn">\u{0997}</td><td class="key"><span class="key-badge">g</span></td><td class="sep"></td>
            <td class="bn">\u{09A1}</td><td class="key"><span class="key-badge">D</span></td><td class="sep"></td>
            <td class="bn">\u{09AC}</td><td class="key"><span class="key-badge">b</span></td><td class="sep"></td>
            <td class="bn">\u{09DC}</td><td class="key"><span class="key-badge">R</span></td>
        </tr>
        <tr>
            <td class="bn">\u{0998}</td><td class="key"><span class="key-badge">gh</span></td><td class="sep"></td>
            <td class="bn">\u{09A2}</td><td class="key"><span class="key-badge">Dh</span></td><td class="sep"></td>
            <td class="bn">\u{09AD}</td><td class="key"><span class="key-badge">bh, v</span></td><td class="sep"></td>
            <td class="bn">\u{09DD}</td><td class="key"><span class="key-badge">Rh</span></td>
        </tr>
        <tr>
            <td class="bn">\u{0999}</td><td class="key"><span class="key-badge">Ng</span></td><td class="sep"></td>
            <td class="bn">\u{09A3}</td><td class="key"><span class="key-badge">N</span></td><td class="sep"></td>
            <td class="bn">\u{09AE}</td><td class="key"><span class="key-badge">m</span></td><td class="sep"></td>
            <td class="bn">\u{09DF}</td><td class="key"><span class="key-badge">y, Y</span></td>
        </tr>
        <tr>
            <td class="bn">\u{099A}</td><td class="key"><span class="key-badge">c</span></td><td class="sep"></td>
            <td class="bn">\u{09A4}</td><td class="key"><span class="key-badge">t</span></td><td class="sep"></td>
            <td class="bn">\u{09AF}</td><td class="key"><span class="key-badge">z</span></td><td class="sep"></td>
            <td class="bn">\u{09B6}</td><td class="key"><span class="key-badge">sh, S</span></td>
        </tr>
        <tr>
            <td class="bn">\u{099B}</td><td class="key"><span class="key-badge">ch</span></td><td class="sep"></td>
            <td class="bn">\u{09A5}</td><td class="key"><span class="key-badge">th</span></td><td class="sep"></td>
            <td class="bn">\u{09B0}</td><td class="key"><span class="key-badge">r</span></td><td class="sep"></td>
            <td class="bn">\u{09B7}</td><td class="key"><span class="key-badge">Sh</span></td>
        </tr>
        <tr>
            <td class="bn">\u{099C}</td><td class="key"><span class="key-badge">j</span></td><td class="sep"></td>
            <td class="bn">\u{09A6}</td><td class="key"><span class="key-badge">d</span></td><td class="sep"></td>
            <td class="bn">\u{09B2}</td><td class="key"><span class="key-badge">l</span></td><td class="sep"></td>
            <td class="bn">\u{0982}</td><td class="key"><span class="key-badge">ng</span></td>
        </tr>
        <tr>
            <td class="bn">\u{099D}</td><td class="key"><span class="key-badge">jh</span></td><td class="sep"></td>
            <td class="bn">\u{09A7}</td><td class="key"><span class="key-badge">dh</span></td><td class="sep"></td>
            <td class="bn">\u{0983}</td><td class="key"><span class="key-badge">:</span></td><td class="sep"></td>
            <td class="bn">\u{0981}</td><td class="key"><span class="key-badge">^</span></td>
        </tr>
        <tr>
            <td class="bn">\u{099E}</td><td class="key"><span class="key-badge">NG</span></td><td class="sep"></td>
            <td class="bn">\u{09A8}</td><td class="key"><span class="key-badge">n</span></td><td class="sep"></td>
            <td class="bn">\u{09CE}</td><td class="key"><span class="key-badge">t``</span></td><td class="sep"></td>
            <td class="bn"></td><td class="key"></td>
        </tr>
        </table>

        <div class="section-title">Vowels · স্বরবর্ণ</div>
        <table>
        <tr>
            <td class="bn">\u{0985}</td><td class="key"><span class="key-badge">o</span></td><td class="sep"></td>
            <td class="bn">\u{0987} / \u{0995}\u{09BF}</td><td class="key"><span class="key-badge">i</span></td><td class="sep"></td>
            <td class="bn">\u{0989} / \u{0995}\u{09C1}</td><td class="key"><span class="key-badge">u</span></td>
        </tr>
        <tr>
            <td class="bn">\u{0986} / \u{0995}\u{09BE}</td><td class="key"><span class="key-badge">a</span></td><td class="sep"></td>
            <td class="bn">\u{0988} / \u{0995}\u{09C0}</td><td class="key"><span class="key-badge">I</span></td><td class="sep"></td>
            <td class="bn">\u{098A} / \u{0995}\u{09C2}</td><td class="key"><span class="key-badge">U</span></td>
        </tr>
        <tr>
            <td class="bn">\u{098B} / \u{0995}\u{09C3}</td><td class="key"><span class="key-badge">rri</span></td><td class="sep"></td>
            <td class="bn">\u{098F} / \u{0995}\u{09C7}</td><td class="key"><span class="key-badge">e</span></td><td class="sep"></td>
            <td class="bn">\u{0993} / \u{0995}\u{09CB}</td><td class="key"><span class="key-badge">O</span></td>
        </tr>
        <tr>
            <td class="bn">\u{0990} / \u{0995}\u{09C8}</td><td class="key"><span class="key-badge">OI</span></td><td class="sep"></td>
            <td class="bn">\u{0994} / \u{0995}\u{09CC}</td><td class="key"><span class="key-badge">OU</span></td><td class="sep"></td>
            <td class="bn"></td><td class="key"></td>
        </tr>
        </table>

        <div class="section-title">Special & Modifiers · বিশেষ</div>
        <table>
        <tr>
            <td class="bn">\u{09CD} হসন্ত</td><td class="key"><span class="key-badge">,,</span></td><td class="sep"></td>
            <td class="bn">\u{09AC}-ফলা</td><td class="key"><span class="key-badge">w</span></td><td class="sep"></td>
            <td class="bn">\u{09B0}েফ</td><td class="key"><span class="key-badge">rr (v)</span></td>
        </tr>
        <tr>
            <td class="bn">\u{09BC} নুক্তা</td><td class="key"><span class="key-badge">..</span></td><td class="sep"></td>
            <td class="bn">\u{09AF}-ফলা</td><td class="key"><span class="key-badge">y, Z</span></td><td class="sep"></td>
            <td class="bn">\u{0964} দাঁড়ি</td><td class="key"><span class="key-badge">.</span></td>
        </tr>
        <tr>
            <td class="bn">ZWJ</td><td class="key"><span class="key-badge">`</span></td><td class="sep"></td>
            <td class="bn">\u{09B0}-ফলা</td><td class="key"><span class="key-badge">r</span></td><td class="sep"></td>
            <td class="bn">\u{09F3} টাকা</td><td class="key"><span class="key-badge">$</span></td>
        </tr>
        <tr>
            <td class="bn">ZWNJ</td><td class="key"><span class="key-badge">~</span></td><td class="sep"></td>
            <td class="bn"></td><td class="key"></td><td class="sep"></td>
            <td class="bn"></td><td class="key"></td>
        </tr>
        </table>

        <div class="section-title">Numbers · সংখ্যা</div>
        <table>
        <tr>
            <td class="bn">\u{09E6}</td><td class="key"><span class="key-badge">0</span></td><td class="sep"></td>
            <td class="bn">\u{09E7}</td><td class="key"><span class="key-badge">1</span></td><td class="sep"></td>
            <td class="bn">\u{09E8}</td><td class="key"><span class="key-badge">2</span></td><td class="sep"></td>
            <td class="bn">\u{09E9}</td><td class="key"><span class="key-badge">3</span></td><td class="sep"></td>
            <td class="bn">\u{09EA}</td><td class="key"><span class="key-badge">4</span></td>
        </tr>
        <tr>
            <td class="bn">\u{09EB}</td><td class="key"><span class="key-badge">5</span></td><td class="sep"></td>
            <td class="bn">\u{09EC}</td><td class="key"><span class="key-badge">6</span></td><td class="sep"></td>
            <td class="bn">\u{09ED}</td><td class="key"><span class="key-badge">7</span></td><td class="sep"></td>
            <td class="bn">\u{09EE}</td><td class="key"><span class="key-badge">8</span></td><td class="sep"></td>
            <td class="bn">\u{09EF}</td><td class="key"><span class="key-badge">9</span></td>
        </tr>
        </table>

        </body>
        </html>
        """
    }
}

// MARK: - Settings Tab

final class ModeCard: NSView {
    override var isFlipped: Bool { true }
    let mode: BongoInputController.TypingMode
    var onSelect: (() -> Void)?
    var isSelected: Bool = false { didSet { updateSelection() } }

    private let radio = NSImageView()
    private let titleLabel = NSTextField(labelWithString: "")
    private let descLabel = NSTextField(wrappingLabelWithString: "")

    init(mode: BongoInputController.TypingMode, title: String, description: String, recommended: Bool) {
        self.mode = mode
        super.init(frame: .zero)
        wantsLayer = true
        layer?.cornerRadius = 10
        layer?.cornerCurve = .continuous
        layer?.borderWidth = 1
        translatesAutoresizingMaskIntoConstraints = false

        radio.translatesAutoresizingMaskIntoConstraints = false
        radio.imageScaling = .scaleProportionallyUpOrDown

        titleLabel.stringValue = title
        titleLabel.font = NSFont.systemFont(ofSize: 13.5, weight: .semibold)
        titleLabel.translatesAutoresizingMaskIntoConstraints = false

        descLabel.stringValue = description
        descLabel.font = NSFont.systemFont(ofSize: 12)
        descLabel.textColor = .secondaryLabelColor
        descLabel.translatesAutoresizingMaskIntoConstraints = false

        let titleRow = NSStackView(views: [titleLabel])
        titleRow.orientation = .horizontal
        titleRow.spacing = 8
        titleRow.alignment = .centerY
        if recommended { titleRow.addArrangedSubview(PillBadge(text: "Recommended")) }
        titleRow.translatesAutoresizingMaskIntoConstraints = false

        addSubview(radio)
        addSubview(titleRow)
        addSubview(descLabel)

        NSLayoutConstraint.activate([
            radio.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            radio.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            radio.widthAnchor.constraint(equalToConstant: 16),
            radio.heightAnchor.constraint(equalToConstant: 16),

            titleRow.leadingAnchor.constraint(equalTo: radio.trailingAnchor, constant: 12),
            titleRow.topAnchor.constraint(equalTo: topAnchor, constant: 12),
            titleRow.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -16),

            descLabel.leadingAnchor.constraint(equalTo: titleRow.leadingAnchor),
            descLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            descLabel.topAnchor.constraint(equalTo: titleRow.bottomAnchor, constant: 3),
            descLabel.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -12),
        ])

        addGestureRecognizer(NSClickGestureRecognizer(target: self, action: #selector(clicked)))
        updateSelection()
    }
    required init?(coder: NSCoder) { fatalError() }

    @objc private func clicked() { onSelect?() }

    private func updateSelection() {
        let symbol = isSelected ? "largecircle.fill.circle" : "circle"
        radio.image = NSImage(systemSymbolName: symbol, accessibilityDescription: nil)
        radio.contentTintColor = isSelected ? WelcomeUI.accent : .tertiaryLabelColor
        applyColors()
    }

    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        applyColors()
    }

    private func applyColors() {
        effectiveAppearance.performAsCurrentDrawingAppearance { [self] in
            if isSelected {
                layer?.borderColor = WelcomeUI.accent.cgColor
                layer?.backgroundColor = WelcomeUI.accent.withAlphaComponent(0.12).cgColor
            } else {
                layer?.borderColor = NSColor.separatorColor.withAlphaComponent(0.35).cgColor
                layer?.backgroundColor = NSColor.controlBackgroundColor.withAlphaComponent(0.5).cgColor
            }
        }
    }
}

class SettingsView: NSView {
    override var isFlipped: Bool { true }
    private var cards: [ModeCard] = []
    private let emojiSwitch = NSSwitch()
    private let emojiTitle = NSTextField(labelWithString: "Show emoji in suggestions")

    override init(frame: NSRect) {
        super.init(frame: frame)
        setupUI()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setupUI() {
        let stack = NSStackView()
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 12),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: WelcomeUI.pageInset),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -WelcomeUI.pageInset),
        ])

        // Typing Mode Section
        let modeHeader = WelcomeUI.sectionHeader("Typing mode")
        stack.addArrangedSubview(modeHeader)

        let current = BongoInputController.currentTypingMode()
        let modes: [(BongoInputController.TypingMode, String, String, Bool)] = [
            (.phoneticFirst, "Phonetic first",
             "Types the exact phonetic spelling by default, showing suggestions underneath for alternatives you can select with arrows or numbers.", true),
            (.smart, "Smart suggestions",
             "Picks the top dictionary-ranked word automatically on Space. Best for fluid fast typing.", false),
            (.phoneticOnly, "Phonetic only",
             "Direct inline phonetic output with no candidate popup or suggestions.", false),
        ]

        let cardStack = NSStackView()
        cardStack.orientation = .vertical
        cardStack.alignment = .leading
        cardStack.spacing = 8
        cardStack.translatesAutoresizingMaskIntoConstraints = false

        for (mode, title, desc, recommended) in modes {
            let card = ModeCard(mode: mode, title: title, description: desc, recommended: recommended)
            card.isSelected = (mode == current)
            card.onSelect = { [weak self, weak card] in
                guard let self, let card else { return }
                self.selectMode(card.mode)
            }
            cardStack.addArrangedSubview(card)
            card.widthAnchor.constraint(equalTo: cardStack.widthAnchor).isActive = true
            cards.append(card)
        }
        stack.addArrangedSubview(cardStack)
        cardStack.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true

        // Preferences Section
        let prefHeader = WelcomeUI.sectionHeader("Preferences")
        stack.addArrangedSubview(prefHeader)

        emojiTitle.font = .systemFont(ofSize: 13, weight: .medium)
        emojiSwitch.state = BongoInputController.currentShowEmoji() ? .on : .off
        emojiSwitch.target = self
        emojiSwitch.action = #selector(emojiToggled)

        let emojiRow = NSStackView(views: [emojiTitle, emojiSwitch])
        emojiRow.orientation = .horizontal
        emojiRow.spacing = 16
        emojiRow.alignment = .centerY

        let prefCard = CardContainer(content: emojiRow)
        stack.addArrangedSubview(prefCard)
        prefCard.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true

        // Updates & System Info
        let sysHeader = WelcomeUI.sectionHeader("Updates & System")
        stack.addArrangedSubview(sysHeader)

        let archLabel = NSTextField(labelWithString: "Native Apple Silicon (arm64)")
        archLabel.font = .systemFont(ofSize: 13, weight: .medium)
        let checkUpdateBtn = NSButton(title: "Check for Updates…", target: self, action: #selector(checkUpdates))
        checkUpdateBtn.bezelStyle = .rounded

        let sysRow = NSStackView(views: [archLabel, checkUpdateBtn])
        sysRow.orientation = .horizontal
        sysRow.spacing = 16
        sysRow.alignment = .centerY

        let sysCard = CardContainer(content: sysRow)
        stack.addArrangedSubview(sysCard)
        sysCard.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
    }

    private func selectMode(_ mode: BongoInputController.TypingMode) {
        UserDefaults.standard.set(mode.rawValue, forKey: BongoInputController.typingModeKey)
        NotificationCenter.default.post(name: .bongoTypingModeChanged, object: nil)
        for card in cards {
            card.isSelected = (card.mode == mode)
        }
    }

    @objc private func emojiToggled() {
        let on = (emojiSwitch.state == .on)
        UserDefaults.standard.set(on, forKey: BongoInputController.showEmojiKey)
        NotificationCenter.default.post(name: .bongoEmojiSettingChanged, object: nil)
    }

    @objc private func checkUpdates() {
        BongoUpdateChecker.shared.check()
    }
}

// MARK: - Fonts Tab

final class FontsView: NSView {
    override var isFlipped: Bool { true }
    private let fontMenu = NSPopUpButton()
    private let sizeMenu = NSPopUpButton()
    private let candidate1 = NSTextField(labelWithString: "1   আমি")
    private let candidate2 = NSTextField(labelWithString: "2   আমার")
    private let candidate3 = NSTextField(labelWithString: "3   আমরা")
    private let previewLabel = NSTextField(labelWithString: "আমি বাংলায় গান গাই  ·  বাংলা আমার অহংকার")

    override init(frame: NSRect) {
        super.init(frame: frame)
        setupUI()
        updatePreview()
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(fontSettingsUpdated),
            name: .bongoFontSettingChanged,
            object: nil
        )
    }
    required init?(coder: NSCoder) { fatalError() }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }

    private func setupUI() {
        let stack = NSStackView()
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 14
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 12),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: WelcomeUI.pageInset),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -WelcomeUI.pageInset),
        ])

        let fontHeader = WelcomeUI.sectionHeader("Candidate popup typography")
        stack.addArrangedSubview(fontHeader)

        configureFontMenu()
        configureSizeMenu()

        let fontColLabel = NSTextField(labelWithString: "Font Family")
        fontColLabel.font = .systemFont(ofSize: 12.5, weight: .medium)
        fontColLabel.textColor = .secondaryLabelColor

        let sizeColLabel = NSTextField(labelWithString: "Size")
        sizeColLabel.font = .systemFont(ofSize: 12.5, weight: .medium)
        sizeColLabel.textColor = .secondaryLabelColor

        let fontStack = NSStackView(views: [fontColLabel, fontMenu])
        fontStack.orientation = .vertical
        fontStack.alignment = .leading
        fontStack.spacing = 5

        let sizeStack = NSStackView(views: [sizeColLabel, sizeMenu])
        sizeStack.orientation = .vertical
        sizeStack.alignment = .leading
        sizeStack.spacing = 5

        let controlRow = NSStackView(views: [fontStack, sizeStack])
        controlRow.orientation = .horizontal
        controlRow.spacing = 16
        fontMenu.widthAnchor.constraint(equalToConstant: 260).isActive = true
        sizeMenu.widthAnchor.constraint(equalToConstant: 120).isActive = true

        let fontCard = CardContainer(content: controlRow)
        stack.addArrangedSubview(fontCard)
        fontCard.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true

        // Preview Section
        let prevHeader = WelcomeUI.sectionHeader("Live candidate preview")
        stack.addArrangedSubview(prevHeader)

        let mockPanel = FlippedVisualEffectView()
        mockPanel.material = .hudWindow
        mockPanel.blendingMode = .withinWindow
        mockPanel.state = .active
        mockPanel.wantsLayer = true
        mockPanel.layer?.cornerRadius = 10
        mockPanel.layer?.cornerCurve = .continuous
        mockPanel.layer?.borderWidth = 0.5
        mockPanel.layer?.borderColor = NSColor.separatorColor.withAlphaComponent(0.35).cgColor
        mockPanel.translatesAutoresizingMaskIntoConstraints = false

        let mockContent = NSStackView()
        mockContent.orientation = .vertical
        mockContent.alignment = .leading
        mockContent.spacing = 6
        mockContent.translatesAutoresizingMaskIntoConstraints = false
        mockPanel.addSubview(mockContent)

        // Mock aux text
        let mockAux = NSTextField(labelWithString: "ami  ·  বাংলা")
        mockAux.font = .monospacedSystemFont(ofSize: 11, weight: .semibold)
        mockAux.textColor = .secondaryLabelColor
        mockContent.addArrangedSubview(mockAux)

        // Mock candidates
        candidate1.textColor = .labelColor
        candidate2.textColor = .secondaryLabelColor
        candidate3.textColor = .secondaryLabelColor

        mockContent.addArrangedSubview(candidate1)
        mockContent.addArrangedSubview(candidate2)
        mockContent.addArrangedSubview(candidate3)

        // Sentence sample inside preview card
        let previewDivider = NSBox()
        previewDivider.boxType = .separator
        previewDivider.translatesAutoresizingMaskIntoConstraints = false
        mockContent.addArrangedSubview(previewDivider)
        previewDivider.widthAnchor.constraint(equalTo: mockContent.widthAnchor).isActive = true

        previewLabel.textColor = .labelColor
        previewLabel.lineBreakMode = .byWordWrapping
        mockContent.addArrangedSubview(previewLabel)

        NSLayoutConstraint.activate([
            mockContent.topAnchor.constraint(equalTo: mockPanel.topAnchor, constant: 12),
            mockContent.bottomAnchor.constraint(equalTo: mockPanel.bottomAnchor, constant: -12),
            mockContent.leadingAnchor.constraint(equalTo: mockPanel.leadingAnchor, constant: 14),
            mockContent.trailingAnchor.constraint(equalTo: mockPanel.trailingAnchor, constant: -14),
        ])

        let previewContainer = CardContainer(content: mockPanel)
        stack.addArrangedSubview(previewContainer)
        previewContainer.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true

        // Font Book Action
        let actionsRow = NSStackView()
        actionsRow.orientation = .horizontal
        actionsRow.spacing = 10

        let refreshBtn = NSButton(title: "Refresh Fonts", target: self, action: #selector(refreshFonts))
        refreshBtn.bezelStyle = .rounded
        actionsRow.addArrangedSubview(refreshBtn)

        let fontBookBtn = NSButton(title: "Open Font Book", target: self, action: #selector(openFontBook))
        fontBookBtn.bezelStyle = .rounded
        actionsRow.addArrangedSubview(fontBookBtn)

        stack.addArrangedSubview(actionsRow)
    }

    private func configureFontMenu() {
        fontMenu.target = self
        fontMenu.action = #selector(fontChanged)
        reloadFonts()
    }

    private func configureSizeMenu() {
        sizeMenu.removeAllItems()
        for s in [14, 16, 18, 20, 22, 24, 28] {
            sizeMenu.addItem(withTitle: "\(s) pt")
            sizeMenu.lastItem?.tag = s
        }
        let currentSize = Int(BongoFontSettings.size)
        sizeMenu.selectItem(withTag: currentSize)
        sizeMenu.target = self
        sizeMenu.action = #selector(sizeChanged)
    }

    private func updatePreview() {
        let currentFont = BongoFontSettings.font()
        candidate1.font = currentFont
        candidate2.font = currentFont
        candidate3.font = currentFont
        previewLabel.font = currentFont
    }

    private func syncMenuSelections() {
        if let current = BongoFontSettings.familyName, !current.isEmpty {
            let idx = fontMenu.indexOfItem(withTitle: current)
            if idx >= 0 {
                fontMenu.selectItem(at: idx)
            } else {
                fontMenu.addItem(withTitle: current)
                fontMenu.lastItem?.representedObject = current
                fontMenu.selectItem(withTitle: current)
            }
        } else {
            fontMenu.selectItem(at: 0)
        }
        sizeMenu.selectItem(withTag: Int(BongoFontSettings.size))
    }

    private func reloadFonts() {
        fontMenu.removeAllItems()
        fontMenu.addItem(withTitle: "System Font (Default)")
        fontMenu.lastItem?.representedObject = nil

        let fonts = NSFontManager.shared.availableFontFamilies
        let banglaFonts = fonts.filter { family in
            guard let font = BongoFontSettings.resolveFont(family: family, size: 14) else { return false }
            return font.coveredCharacterSet.contains(UnicodeScalar(0x0985)!)
        }.sorted { $0.localizedCaseInsensitiveCompare($1) == .orderedAscending }

        for family in banglaFonts {
            fontMenu.addItem(withTitle: family)
            fontMenu.lastItem?.representedObject = family
        }

        syncMenuSelections()
    }

    @objc private func fontChanged() {
        let chosen = fontMenu.selectedItem?.representedObject as? String
        BongoFontSettings.familyName = chosen
        updatePreview()
        NotificationCenter.default.post(name: .bongoFontSettingChanged, object: nil)
    }

    @objc private func sizeChanged() {
        if let tag = sizeMenu.selectedItem?.tag {
            BongoFontSettings.size = CGFloat(tag)
            updatePreview()
            NotificationCenter.default.post(name: .bongoFontSettingChanged, object: nil)
        }
    }

    @objc private func fontSettingsUpdated() {
        updatePreview()
        syncMenuSelections()
    }

    @objc private func refreshFonts() {
        reloadFonts()
        updatePreview()
    }

    @objc private func openFontBook() {
        if let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: "com.apple.FontBook") {
            NSWorkspace.shared.open(url)
        }
    }
}

// MARK: - Updates Checker

final class BongoUpdateChecker: NSObject {
    static let shared = BongoUpdateChecker()

    func check() {
        guard let repository = Bundle.main.object(forInfoDictionaryKey: "BongoGitHubRepository") as? String,
              !repository.isEmpty,
              let url = URL(string: "https://api.github.com/repos/\(repository)/releases?per_page=1") else {
            show(title: "Updates are not configured", message: "This local build has no GitHub repository configured. Release builds configure it automatically.")
            return
        }
        var request = URLRequest(url: url)
        request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        request.setValue("Bongo-macOS", forHTTPHeaderField: "User-Agent")
        URLSession.shared.dataTask(with: request) { data, response, error in
            if (response as? HTTPURLResponse)?.statusCode == 404 {
                let current = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
                self.show(title: "No public release information", message: "Bongo \(current) is installed. The release feed is not public yet.")
                return
            }
            guard error == nil, let data,
                  let releases = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
                self.show(title: "Couldn’t check for updates", message: "Check your internet connection and try again.")
                return
            }
            guard let object = releases.first else {
                let current = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
                self.show(title: "Bongo is up to date", message: "You’re using version \(current). No newer release is published yet.")
                return
            }
            guard let tag = object["tag_name"] as? String,
                  let page = object["html_url"] as? String else {
                self.show(title: "Couldn’t read release information", message: "Open GitHub Releases and check manually.")
                return
            }
            let latest = tag.trimmingCharacters(in: CharacterSet(charactersIn: "vV"))
            let current = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
            if current.compare(latest, options: .numeric) == .orderedAscending {
                DispatchQueue.main.async {
                    let alert = NSAlert()
                    alert.messageText = "Bongo \(latest) is available"
                    alert.informativeText = "Open the release page to download the update for your system."
                    alert.addButton(withTitle: "Open release")
                    alert.addButton(withTitle: "Later")
                    if alert.runModal() == .alertFirstButtonReturn, let releaseURL = URL(string: page) {
                        NSWorkspace.shared.open(releaseURL)
                    }
                }
            } else {
                self.show(title: "Bongo is up to date", message: "You’re using version \(current).")
            }
        }.resume()
    }

    private func show(title: String, message: String) {
        DispatchQueue.main.async {
            let alert = NSAlert()
            alert.messageText = title
            alert.informativeText = message
            alert.addButton(withTitle: "OK")
            alert.runModal()
        }
    }
}
