import Cocoa
import WebKit

// MARK: - Window Controller (Singleton)

class WelcomeWindowController {
    static let shared = WelcomeWindowController()

    private var window: NSWindow?

    func showWindow() {
        if let window = window {
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }

        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1040, height: 760),
            styleMask: [.titled, .closable, .miniaturizable],
            backing: .buffered,
            defer: false
        )
        window.title = "Bongo"
        window.titlebarAppearsTransparent = true
        window.backgroundColor = .windowBackgroundColor
        window.isReleasedWhenClosed = false
        window.isRestorable = false
        window.contentView = WelcomeTabView()
        window.center()

        self.window = window
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}

// MARK: - Tabbed Container

/// A compact sidebar row with an inset selection pill, accent marker, and hover
/// feedback. Building this as a control avoids AppKit's oversized button bezel.
final class SidebarNavigationButton: NSControl {
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
            marker.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 6),
            marker.centerYAnchor.constraint(equalTo: centerYAnchor),
            marker.widthAnchor.constraint(equalToConstant: 3),
            marker.heightAnchor.constraint(equalToConstant: 18),
            iconView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 17),
            iconView.centerYAnchor.constraint(equalTo: centerYAnchor),
            iconView.widthAnchor.constraint(equalToConstant: 16),
            iconView.heightAnchor.constraint(equalToConstant: 16),
            titleLabel.leadingAnchor.constraint(equalTo: iconView.trailingAnchor, constant: 9),
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

    override func mouseDown(with event: NSEvent) {
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.08
            animator().alphaValue = 0.72
        }
    }

    override func mouseUp(with event: NSEvent) {
        animator().alphaValue = 1
        if bounds.contains(convert(event.locationInWindow, from: nil)) {
            _ = sendAction(action, to: target)
        }
    }

    override func accessibilityPerformPress() -> Bool {
        _ = sendAction(action, to: target)
        return true
    }

    override func hitTest(_ point: NSPoint) -> NSView? {
        bounds.contains(point) ? self : nil
    }

    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        updateAppearance()
    }

    private func updateAppearance() {
        effectiveAppearance.performAsCurrentDrawingAppearance {
            let tint = WelcomeUI.accent
            layer?.backgroundColor = isActive
                ? tint.withAlphaComponent(0.11).cgColor
                : (isHovered ? NSColor.labelColor.withAlphaComponent(0.055).cgColor : NSColor.clear.cgColor)
            marker.layer?.backgroundColor = isActive ? tint.cgColor : NSColor.clear.cgColor
            iconView.contentTintColor = isActive ? tint : .secondaryLabelColor
            titleLabel.textColor = isActive ? .labelColor : .secondaryLabelColor
            titleLabel.font = .systemFont(ofSize: 13.5, weight: isActive ? .semibold : .medium)
            setAccessibilityValue(isActive ? "Selected" : "")
        }
    }
}

class WelcomeTabView: NSView {
    private let tabView = NSTabView()
    private var buttons: [SidebarNavigationButton] = []
    private let heading = NSTextField(labelWithString: "Welcome home")
    private let subtitle = NSTextField(labelWithString: "A little closer to your language.")
    private let titles = ["Welcome home", "Keyboard guide", "Make it yours"]
    private let subtitles = ["A little closer to your language.", "Find the right keys for every word.", "Your words. Your way of typing."]

    override init(frame: NSRect) {
        super.init(frame: frame)
        let sidebar = NSVisualEffectView()
        sidebar.material = .sidebar
        sidebar.blendingMode = .withinWindow
        sidebar.state = .active
        sidebar.translatesAutoresizingMaskIntoConstraints = false
        addSubview(sidebar)
        let brandIcon = NSImageView(image: NSApp.applicationIconImage)
        brandIcon.imageScaling = .scaleProportionallyUpOrDown
        brandIcon.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(brandIcon)
        let brand = NSTextField(labelWithString: "Bongo")
        brand.font = .systemFont(ofSize: 25, weight: .bold)
        brand.textColor = WelcomeUI.accent
        brand.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(brand)
        let nav = NSStackView()
        nav.orientation = .vertical
        nav.alignment = .leading
        nav.spacing = 7
        nav.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(nav)
        let labels = ["Overview", "Keyboard guide", "Preferences"]
        let symbols = ["square.grid.2x2", "keyboard", "slider.horizontal.3"]
        for i in 0..<labels.count {
            let button = SidebarNavigationButton(
                title: labels[i], symbol: symbols[i], target: self, action: #selector(navigate(_:)))
            button.tag = i
            nav.addArrangedSubview(button)
            button.widthAnchor.constraint(equalTo: nav.widthAnchor).isActive = true
            button.heightAnchor.constraint(equalToConstant: 38).isActive = true
            buttons.append(button)
        }
        let offline = NSTextField(labelWithString: "●  On-device typing")
        offline.font = .systemFont(ofSize: 11, weight: .medium)
        offline.textColor = WelcomeUI.accent
        offline.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(offline)
        let version = NSTextField(labelWithString: "Bongo  " + (Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? ""))
        version.font = .systemFont(ofSize: 11)
        version.textColor = .secondaryLabelColor
        version.translatesAutoresizingMaskIntoConstraints = false
        sidebar.addSubview(version)
        heading.font = .systemFont(ofSize: 27, weight: .bold)
        subtitle.font = .systemFont(ofSize: 13)
        subtitle.textColor = .secondaryLabelColor
        for v in [heading, subtitle] { v.translatesAutoresizingMaskIntoConstraints = false; addSubview(v) }
        tabView.tabViewType = .noTabsNoBorder
        tabView.translatesAutoresizingMaskIntoConstraints = false
        for (index, view) in [GettingStartedView(), LayoutWebView(), SettingsView()].enumerated() {
            let item = NSTabViewItem(identifier: index)
            item.view = view
            tabView.addTabViewItem(item)
        }
        addSubview(tabView)
        let footer = NSTextField(labelWithString: "Developed by Mehedi Shakeel")
        footer.font = .systemFont(ofSize: 11, weight: .medium)
        footer.textColor = .secondaryLabelColor
        footer.translatesAutoresizingMaskIntoConstraints = false
        addSubview(footer)
        NSLayoutConstraint.activate([
            sidebar.leadingAnchor.constraint(equalTo: leadingAnchor), sidebar.topAnchor.constraint(equalTo: topAnchor),
            sidebar.bottomAnchor.constraint(equalTo: bottomAnchor), sidebar.widthAnchor.constraint(equalToConstant: 218),
            brandIcon.leadingAnchor.constraint(equalTo: sidebar.leadingAnchor, constant: 22), brandIcon.topAnchor.constraint(equalTo: sidebar.topAnchor, constant: 23),
            brandIcon.widthAnchor.constraint(equalToConstant: 38), brandIcon.heightAnchor.constraint(equalToConstant: 38),
            brand.leadingAnchor.constraint(equalTo: brandIcon.trailingAnchor, constant: 9), brand.centerYAnchor.constraint(equalTo: brandIcon.centerYAnchor),
            nav.leadingAnchor.constraint(equalTo: sidebar.leadingAnchor, constant: 20), nav.trailingAnchor.constraint(equalTo: sidebar.trailingAnchor, constant: -20),
            nav.topAnchor.constraint(equalTo: brandIcon.bottomAnchor, constant: 38),
            offline.leadingAnchor.constraint(equalTo: brandIcon.leadingAnchor), offline.bottomAnchor.constraint(equalTo: version.topAnchor, constant: -10),
            version.leadingAnchor.constraint(equalTo: brandIcon.leadingAnchor), version.bottomAnchor.constraint(equalTo: sidebar.bottomAnchor, constant: -24),
            heading.leadingAnchor.constraint(equalTo: sidebar.trailingAnchor, constant: 32), heading.topAnchor.constraint(equalTo: topAnchor, constant: 28),
            subtitle.leadingAnchor.constraint(equalTo: heading.leadingAnchor), subtitle.topAnchor.constraint(equalTo: heading.bottomAnchor, constant: 7),
            tabView.leadingAnchor.constraint(equalTo: sidebar.trailingAnchor), tabView.trailingAnchor.constraint(equalTo: trailingAnchor),
            tabView.topAnchor.constraint(equalTo: subtitle.bottomAnchor, constant: 12), tabView.bottomAnchor.constraint(equalTo: footer.topAnchor, constant: -12),
            footer.centerXAnchor.constraint(equalTo: tabView.centerXAnchor), footer.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -18),
        ])
        refreshNavigation(0)
    }
    required init?(coder: NSCoder) { fatalError() }
    @objc private func navigate(_ sender: SidebarNavigationButton) { refreshNavigation(sender.tag) }
    private func refreshNavigation(_ index: Int) {
        tabView.selectTabViewItem(at: index)
        heading.stringValue = titles[index]
        subtitle.stringValue = subtitles[index]
        for (i, button) in buttons.enumerated() {
            button.isActive = (i == index)
        }
    }
    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        if let index = tabView.selectedTabViewItem.flatMap({ tabView.indexOfTabViewItem($0) }) { refreshNavigation(index) }
    }
}

// MARK: - Updates

final class BongoUpdateChecker: NSObject {
    static let shared = BongoUpdateChecker()

    func check() {
        guard let repository = Bundle.main.object(forInfoDictionaryKey: "BongoGitHubRepository") as? String,
              !repository.isEmpty,
              let url = URL(string: "https://api.github.com/repos/\(repository)/releases/latest") else {
            show(title: "Updates are not configured", message: "This local build has no GitHub repository configured. Release builds configure it automatically.")
            return
        }
        var request = URLRequest(url: url)
        request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        request.setValue("Bongo-macOS", forHTTPHeaderField: "User-Agent")
        URLSession.shared.dataTask(with: request) { data, _, error in
            guard error == nil, let data,
                  let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let tag = object["tag_name"] as? String,
                  let page = object["html_url"] as? String else {
                self.show(title: "Couldn’t check for updates", message: "Check your internet connection and try again.")
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

// MARK: - Settings Tab

// MARK: - Shared welcome-window UI

/// Visual helpers shared across the welcome window's tabs.
enum WelcomeUI {
    static let pageInset: CGFloat = 32
    static let accent = NSColor.systemTeal
    static let accentTint: CGFloat = 0.12

    /// Small uppercase section header (macOS grouped-settings style).
    static func sectionHeader(_ text: String) -> NSTextField {
        let label = NSTextField(labelWithString: "")
        let attr = NSMutableAttributedString(string: text.uppercased())
        attr.addAttributes(
            [
                .font: NSFont.systemFont(ofSize: 11, weight: .semibold),
                .foregroundColor: NSColor.secondaryLabelColor,
                .kern: 0.6,
            ],
            range: NSRange(location: 0, length: attr.length))
        label.attributedStringValue = attr
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }

    /// A monospace "key" chip used in the shortcut/layout lists.
    static func keyChip(_ text: String) -> NSView {
        let chip = RoundedTintView(
            cornerRadius: 5,
            fill: { NSColor.labelColor.withAlphaComponent(0.07) },
            border: { NSColor.separatorColor })
        let label = NSTextField(labelWithString: text)
        label.font = NSFont.monospacedSystemFont(ofSize: 11.5, weight: .medium)
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

/// A rounded, layer-backed view whose fill/border colors resolve per-appearance.
/// `fill`/`border` are closures so semantic NSColors are re-resolved on light/dark
/// changes (CGColors don't auto-update).
class RoundedTintView: NSView {
    private let fillColor: () -> NSColor
    private let borderColor: (() -> NSColor)?

    init(cornerRadius: CGFloat, borderWidth: CGFloat = 1,
         fill: @escaping () -> NSColor, border: (() -> NSColor)? = nil) {
        self.fillColor = fill
        self.borderColor = border
        super.init(frame: .zero)
        wantsLayer = true
        layer?.cornerRadius = cornerRadius
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

/// A rounded container that wraps arbitrary content with inset padding.
final class CardContainer: RoundedTintView {
    init(content: NSView, insets: NSEdgeInsets = NSEdgeInsets(top: 12, left: 16, bottom: 12, right: 16)) {
        super.init(
            cornerRadius: 14,
            fill: { .controlBackgroundColor.withAlphaComponent(0.6) },
            border: { .separatorColor })
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

/// Small accent "Recommended"-style badge.
final class PillBadge: RoundedTintView {
    init(text: String) {
        super.init(
            cornerRadius: 7,
            fill: { WelcomeUI.accent.withAlphaComponent(0.15) })
        setContentHuggingPriority(.required, for: .horizontal)
        let label = NSTextField(labelWithString: text)
        label.font = NSFont.systemFont(ofSize: 10, weight: .semibold)
        label.textColor = WelcomeUI.accent
        label.translatesAutoresizingMaskIntoConstraints = false
        addSubview(label)
        NSLayoutConstraint.activate([
            label.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 7),
            label.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -7),
            label.topAnchor.constraint(equalTo: topAnchor, constant: 2),
            label.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -2),
        ])
    }
    required init?(coder: NSCoder) { fatalError() }
}

// MARK: - Settings Tab (selectable mode cards)

/// A selectable typing-mode card: radio indicator + title (+ optional badge) +
/// wrapping description. The whole card is clickable.
final class ModeCard: NSView {
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
        layer?.borderWidth = 1
        translatesAutoresizingMaskIntoConstraints = false

        radio.translatesAutoresizingMaskIntoConstraints = false
        radio.imageScaling = .scaleProportionallyUpOrDown

        titleLabel.stringValue = title
        titleLabel.font = NSFont.systemFont(ofSize: 14, weight: .semibold)
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        titleLabel.setContentHuggingPriority(.required, for: .horizontal)

        descLabel.stringValue = description
        descLabel.font = NSFont.systemFont(ofSize: 13)
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
            radio.topAnchor.constraint(equalTo: topAnchor, constant: 17),
            radio.widthAnchor.constraint(equalToConstant: 16),
            radio.heightAnchor.constraint(equalToConstant: 16),

            titleRow.leadingAnchor.constraint(equalTo: radio.trailingAnchor, constant: 12),
            titleRow.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            titleRow.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -16),

            descLabel.leadingAnchor.constraint(equalTo: titleRow.leadingAnchor),
            descLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            descLabel.topAnchor.constraint(equalTo: titleRow.bottomAnchor, constant: 4),
            descLabel.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16),
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
                layer?.borderColor = NSColor.separatorColor.cgColor
                layer?.backgroundColor = NSColor.controlBackgroundColor.withAlphaComponent(0.55).cgColor
            }
        }
    }
}

class SettingsView: NSView {
    private var cards: [ModeCard] = []
    private let emojiSwitch = NSSwitch()
    private let emojiTitle = NSTextField(labelWithString: "Show emoji in suggestions")

    override init(frame: NSRect) {
        super.init(frame: frame)
        setupUI()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setupUI() {
        let header = WelcomeUI.sectionHeader("Typing mode")

        let intro = NSTextField(wrappingLabelWithString:
            "Choose how Bongo turns what you type into Bangla. You can switch anytime.")
        intro.font = NSFont.systemFont(ofSize: 13)
        intro.textColor = .secondaryLabelColor
        intro.translatesAutoresizingMaskIntoConstraints = false

        let cardStack = NSStackView()
        cardStack.orientation = .vertical
        cardStack.alignment = .leading
        cardStack.spacing = 14
        cardStack.translatesAutoresizingMaskIntoConstraints = false

        let current = BongoInputController.currentTypingMode()
        let modes: [(BongoInputController.TypingMode, String, String, Bool)] = [
            (.smart, "Smart suggestions",
             "Let the dictionary choose a word. Browse suggestions when you want another spelling.",
             false),
            (.phoneticFirst, "Phonetic-first",
             "Your phonetic spelling comes first, with suggestions a keypress away. Bongo remembers your choices.",
             true),
            (.phoneticOnly, "Phonetic-only",
             "Just your keystrokes, translated into Bangla. No suggestions or automatic corrections.",
             false),
        ]
        for (mode, title, desc, recommended) in modes {
            let card = ModeCard(mode: mode, title: title, description: desc, recommended: recommended)
            card.isSelected = (mode == current)
            card.onSelect = { [weak self] in self?.select(mode) }
            cards.append(card)
            cardStack.addArrangedSubview(card)
            card.widthAnchor.constraint(equalTo: cardStack.widthAnchor).isActive = true
        }

        let suggestionsHeader = WelcomeUI.sectionHeader("Suggestions")
        let emojiCard = makeEmojiCard()

        let updatesHeader = WelcomeUI.sectionHeader("Updates")
        let updateCard = makeUpdateCard()
        let content = NSStackView(views: [header, intro, cardStack, suggestionsHeader, emojiCard, updatesHeader, updateCard])
        content.orientation = .vertical
        content.alignment = .leading
        content.spacing = 6
        content.setCustomSpacing(18, after: intro)
        content.setCustomSpacing(26, after: cardStack)
        content.setCustomSpacing(10, after: suggestionsHeader)
        content.setCustomSpacing(22, after: emojiCard)
        content.setCustomSpacing(10, after: updatesHeader)
        content.translatesAutoresizingMaskIntoConstraints = false
        addSubview(content)

        let tip = NSTextField(wrappingLabelWithString:
            "Changes apply immediately to new typing. Any word you were composing when you switch is discarded — just retype it.")
        tip.font = NSFont.systemFont(ofSize: 11)
        tip.textColor = .tertiaryLabelColor
        tip.translatesAutoresizingMaskIntoConstraints = false
        addSubview(tip)

        NSLayoutConstraint.activate([
            content.leadingAnchor.constraint(equalTo: leadingAnchor, constant: WelcomeUI.pageInset),
            content.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -WelcomeUI.pageInset),
            content.topAnchor.constraint(equalTo: topAnchor, constant: 28),
            cardStack.widthAnchor.constraint(equalTo: content.widthAnchor),
            intro.widthAnchor.constraint(equalTo: content.widthAnchor),
            emojiCard.widthAnchor.constraint(equalTo: content.widthAnchor),
            updateCard.widthAnchor.constraint(equalTo: content.widthAnchor),

            tip.leadingAnchor.constraint(equalTo: leadingAnchor, constant: WelcomeUI.pageInset),
            tip.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -WelcomeUI.pageInset),
            tip.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -24),
        ])
    }

    private func makeUpdateCard() -> NSView {
        let title = NSTextField(labelWithString: "Keep Bongo current")
        title.font = .systemFont(ofSize: 14, weight: .semibold)
        let detail = NSTextField(labelWithString: "Check GitHub Releases for a newer build.")
        detail.font = .systemFont(ofSize: 12)
        detail.textColor = .secondaryLabelColor
        let labels = NSStackView(views: [title, detail])
        labels.orientation = .vertical
        labels.alignment = .leading
        labels.spacing = 3
        let button = NSButton(title: "Check for Updates", target: self, action: #selector(checkForUpdates))
        button.bezelStyle = .rounded
        let row = NSStackView(views: [labels, button])
        row.orientation = .horizontal
        row.alignment = .centerY
        row.spacing = 16
        labels.setContentHuggingPriority(.defaultLow, for: .horizontal)
        return CardContainer(content: row)
    }

    @objc private func checkForUpdates() {
        BongoUpdateChecker.shared.check()
    }

    /// "Show emoji in suggestions" row: title + description on the left, switch
    /// on the right.
    private func makeEmojiCard() -> NSView {
        emojiTitle.font = NSFont.systemFont(ofSize: 14, weight: .semibold)

        let desc = NSTextField(wrappingLabelWithString:
            "Emoji like 🔥 show up next to matching words in the suggestion list. Turn this off for words only. Phonetic-only mode never shows emoji.")
        desc.font = NSFont.systemFont(ofSize: 13)
        desc.textColor = .secondaryLabelColor

        let text = NSStackView(views: [emojiTitle, desc])
        text.orientation = .vertical
        text.alignment = .leading
        text.spacing = 4

        emojiSwitch.state = BongoInputController.currentShowEmoji() ? .on : .off
        emojiSwitch.target = self
        emojiSwitch.action = #selector(emojiToggled)
        emojiSwitch.setContentHuggingPriority(.required, for: .horizontal)
        emojiSwitch.setContentCompressionResistancePriority(.required, for: .horizontal)

        let row = NSStackView(views: [text, emojiSwitch])
        row.orientation = .horizontal
        row.alignment = .centerY
        row.spacing = 16

        updateEmojiAvailability(for: BongoInputController.currentTypingMode())
        return CardContainer(
            content: row,
            insets: NSEdgeInsets(top: 14, left: 16, bottom: 14, right: 16))
    }

    /// The toggle has nothing to act on in Phonetic-only mode (no suggestion list).
    private func updateEmojiAvailability(for mode: BongoInputController.TypingMode) {
        let available = mode != .phoneticOnly
        emojiSwitch.isEnabled = available
        emojiTitle.textColor = available ? .labelColor : .tertiaryLabelColor
    }

    @objc private func emojiToggled() {
        UserDefaults.standard.set(emojiSwitch.state == .on, forKey: BongoInputController.showEmojiKey)
        NotificationCenter.default.post(name: .bongoEmojiSettingChanged, object: nil)
    }

    private func select(_ mode: BongoInputController.TypingMode) {
        for card in cards { card.isSelected = (card.mode == mode) }
        updateEmojiAvailability(for: mode)
        UserDefaults.standard.set(mode.rawValue, forKey: BongoInputController.typingModeKey)
        NotificationCenter.default.post(name: .bongoTypingModeChanged, object: nil)
    }
}

// MARK: - Getting Started Tab

class GettingStartedView: NSView {
    override init(frame: NSRect) {
        super.init(frame: frame)
        let page = NSStackView()
        page.orientation = .vertical
        page.alignment = .leading
        page.spacing = 20
        page.translatesAutoresizingMaskIntoConstraints = false
        addSubview(page)

        let hero = RoundedTintView(cornerRadius: 20, fill: { WelcomeUI.accent.withAlphaComponent(0.10) })
        let eyebrow = label("MADE FOR YOUR WORDS", size: 10, weight: .semibold, color: WelcomeUI.accent)
        let headline = label("নিজের ভাষায়, নিজের মতো।", size: 32, weight: .medium)
        let caption = label("Think in Bangla. Type naturally.", size: 15, color: .secondaryLabelColor)
        let example = label("ami banglay likhi   →   আমি বাংলায় লিখি", size: 18, weight: .medium)
        let heroStack = NSStackView(views: [eyebrow, headline, caption, example])
        heroStack.orientation = .vertical
        heroStack.alignment = .leading
        heroStack.spacing = 12
        heroStack.setCustomSpacing(24, after: caption)
        heroStack.translatesAutoresizingMaskIntoConstraints = false
        hero.addSubview(heroStack)
        NSLayoutConstraint.activate([
            heroStack.leadingAnchor.constraint(equalTo: hero.leadingAnchor, constant: 26),
            heroStack.trailingAnchor.constraint(equalTo: hero.trailingAnchor, constant: -26),
            heroStack.topAnchor.constraint(equalTo: hero.topAnchor, constant: 24),
            heroStack.bottomAnchor.constraint(equalTo: hero.bottomAnchor, constant: -24),
        ])
        page.addArrangedSubview(hero)
        hero.widthAnchor.constraint(equalTo: page.widthAnchor).isActive = true

        let setupTitle = label("Ready when you are", size: 16, weight: .semibold)
        let setupBody = label("Add Bongo in Keyboard settings, then use Globe or Control–Space to switch.", size: 13, color: .secondaryLabelColor)
        let setupButton = NSButton(title: "Open Keyboard Settings  ↗", target: self, action: #selector(openKeyboardSettings))
        setupButton.bezelStyle = .rounded
        setupButton.controlSize = .large
        setupButton.contentTintColor = WelcomeUI.accent
        let setup = NSStackView(views: [setupTitle, setupBody, setupButton])
        setup.orientation = .vertical
        setup.alignment = .leading
        setup.spacing = 10
        let card = CardContainer(content: setup, insets: NSEdgeInsets(top: 18, left: 20, bottom: 18, right: 20))
        page.addArrangedSubview(card)
        card.widthAnchor.constraint(equalTo: page.widthAnchor).isActive = true
        page.addArrangedSubview(WelcomeUI.sectionHeader("A few useful shortcuts"))
        let shortcutRows = NSStackView()
        shortcutRows.orientation = .vertical
        shortcutRows.alignment = .leading
        shortcutRows.spacing = 14
        for (key, description) in [
            ("Space", "Finish your word"),
            ("↑  ↓", "Browse suggestions"),
            ("1–9", "Choose a suggestion"),
            ("Esc", "Cancel this word"),
        ] {
            let row = NSStackView(views: [WelcomeUI.keyChip(key), label(description, size: 13)])
            row.orientation = .horizontal
            row.alignment = .centerY
            row.spacing = 12
            shortcutRows.addArrangedSubview(row)
        }
        page.addArrangedSubview(shortcutRows)
        let tip = label("Close this window anytime. Bongo keeps working in your apps.", size: 12, color: .secondaryLabelColor)
        page.addArrangedSubview(tip)
        NSLayoutConstraint.activate([
            page.topAnchor.constraint(equalTo: topAnchor, constant: 18),
            page.leadingAnchor.constraint(equalTo: leadingAnchor, constant: WelcomeUI.pageInset),
            page.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -WelcomeUI.pageInset),
        ])
    }
    required init?(coder: NSCoder) { fatalError() }
    private func label(_ text: String, size: CGFloat, weight: NSFont.Weight = .regular, color: NSColor = .labelColor) -> NSTextField {
        let field = NSTextField(wrappingLabelWithString: text)
        field.font = .systemFont(ofSize: size, weight: weight)
        field.textColor = color
        return field
    }
    @objc private func openKeyboardSettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.Keyboard-Settings.extension") {
            NSWorkspace.shared.open(url)
        }
    }
}

// MARK: - Keyboard Guide (WKWebView for proper Bengali rendering)

class LayoutWebView: NSView {
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
                    --accent: #087f8c;
                    --text: #1d1d1f;
                    --text-secondary: #8a8a8e;
                    --page-bg: #f7f7f8;
                    --card-bg: rgba(0, 0, 0, 0.025);
                    --card-border: rgba(0, 0, 0, 0.10);
                    --row-border: rgba(0, 0, 0, 0.06);
                }
                @media (prefers-color-scheme: dark) {
                    :root {
                        --accent: #66d9cf;
                        --text: #f2f2f7;
                        --text-secondary: #98989d;
                        --page-bg: #2c242a;
                        --card-bg: rgba(255, 255, 255, 0.05);
                        --card-border: rgba(255, 255, 255, 0.12);
                        --row-border: rgba(255, 255, 255, 0.07);
                    }
                }
                body {
                    font-family: -apple-system, "Helvetica Neue", sans-serif;
                    padding: 18px 32px;
                    background: var(--page-bg);
                    color-scheme: light dark;
                    color: var(--text);
                }
                .section-title {
                    color: var(--text-secondary);
                    font-size: 10.5px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    text-transform: uppercase;
                    margin: 16px 0 5px 2px;
                }
                .section-title:first-child { margin-top: 0; }
                table {
                    width: 100%;
                    table-layout: fixed;
                    border-collapse: separate;
                    border-spacing: 0;
                    background: var(--card-bg);
                    border: 1px solid var(--card-border);
                    border-radius: 14px;
                    overflow: hidden;
                }
                td {
                    padding: 7px 6px;
                    border-bottom: 1px solid var(--row-border);
                    vertical-align: middle;
                    font-size: 12px;
                    line-height: 1.35;
                }
                tr:last-child td { border-bottom: none; }
                .bn {
                    font-size: 15px;
                    font-weight: 500;
                    color: var(--text);
                    width: 34px;
                    text-align: center;
                }
                .key {
                    font-size: 11px;
                    font-weight: 600;
                    color: var(--accent);
                    font-family: "SF Mono", Menlo, monospace;
                }
                .pair { width: 25%; }
                .pair-wide { width: 33.33%; }
                .sep { width: 10px; }
            </style>
            </head>
            <body>

            <div class="section-title">Consonants \u{09AC}\u{09CD}\u{09AF}\u{099E}\u{09CD}\u{099C}\u{09A8}\u{09AC}\u{09B0}\u{09CD}\u{09A3}</div>
            <table>
            <tr>
                <td class="bn pair">\u{0995}</td><td class="key">k</td><td class="sep"></td>
                <td class="bn pair">\u{099F}</td><td class="key">T</td><td class="sep"></td>
                <td class="bn pair">\u{09AA}</td><td class="key">p</td><td class="sep"></td>
                <td class="bn pair">\u{09B8}</td><td class="key">s</td>
            </tr>
            <tr>
                <td class="bn">\u{0996}</td><td class="key">kh</td><td class="sep"></td>
                <td class="bn">\u{09A0}</td><td class="key">Th</td><td class="sep"></td>
                <td class="bn">\u{09AB}</td><td class="key">ph, f</td><td class="sep"></td>
                <td class="bn">\u{09B9}</td><td class="key">h</td>
            </tr>
            <tr>
                <td class="bn">\u{0997}</td><td class="key">g</td><td class="sep"></td>
                <td class="bn">\u{09A1}</td><td class="key">D</td><td class="sep"></td>
                <td class="bn">\u{09AC}</td><td class="key">b</td><td class="sep"></td>
                <td class="bn">\u{09DC}</td><td class="key">R</td>
            </tr>
            <tr>
                <td class="bn">\u{0998}</td><td class="key">gh</td><td class="sep"></td>
                <td class="bn">\u{09A2}</td><td class="key">Dh</td><td class="sep"></td>
                <td class="bn">\u{09AD}</td><td class="key">bh, v</td><td class="sep"></td>
                <td class="bn">\u{09DD}</td><td class="key">Rh</td>
            </tr>
            <tr>
                <td class="bn">\u{0999}</td><td class="key">Ng</td><td class="sep"></td>
                <td class="bn">\u{09A3}</td><td class="key">N</td><td class="sep"></td>
                <td class="bn">\u{09AE}</td><td class="key">m</td><td class="sep"></td>
                <td class="bn">\u{09DF}</td><td class="key">y, Y</td>
            </tr>
            <tr>
                <td class="bn">\u{099A}</td><td class="key">c</td><td class="sep"></td>
                <td class="bn">\u{09A4}</td><td class="key">t</td><td class="sep"></td>
                <td class="bn">\u{09AF}</td><td class="key">z</td><td class="sep"></td>
                <td class="bn">\u{09B6}</td><td class="key">sh, S</td>
            </tr>
            <tr>
                <td class="bn">\u{099B}</td><td class="key">ch</td><td class="sep"></td>
                <td class="bn">\u{09A5}</td><td class="key">th</td><td class="sep"></td>
                <td class="bn">\u{09B0}</td><td class="key">r</td><td class="sep"></td>
                <td class="bn">\u{09B7}</td><td class="key">Sh</td>
            </tr>
            <tr>
                <td class="bn">\u{099C}</td><td class="key">j</td><td class="sep"></td>
                <td class="bn">\u{09A6}</td><td class="key">d</td><td class="sep"></td>
                <td class="bn">\u{09B2}</td><td class="key">l</td><td class="sep"></td>
                <td class="bn">\u{0982}</td><td class="key">ng</td>
            </tr>
            <tr>
                <td class="bn">\u{099D}</td><td class="key">jh</td><td class="sep"></td>
                <td class="bn">\u{09A7}</td><td class="key">dh</td><td class="sep"></td>
                <td class="bn">\u{0983}</td><td class="key">:</td><td class="sep"></td>
                <td class="bn">\u{0981}</td><td class="key">^</td>
            </tr>
            <tr>
                <td class="bn">\u{099E}</td><td class="key">NG</td><td class="sep"></td>
                <td class="bn">\u{09A8}</td><td class="key">n</td><td class="sep"></td>
                <td class="bn">\u{09CE}</td><td class="key">t``</td><td class="sep"></td>
                <td class="bn"></td><td class="key"></td>
            </tr>
            </table>

            <div class="section-title">Vowels \u{09B8}\u{09CD}\u{09AC}\u{09B0}\u{09AC}\u{09B0}\u{09CD}\u{09A3}</div>
            <table>
            <tr>
                <td class="bn pair-wide">\u{0985}</td><td class="key">o</td><td class="sep"></td>
                <td class="bn pair-wide">\u{0987} / \u{0995}\u{09BF}</td><td class="key">i</td><td class="sep"></td>
                <td class="bn pair-wide">\u{0989} / \u{0995}\u{09C1}</td><td class="key">u</td>
            </tr>
            <tr>
                <td class="bn">\u{0986} / \u{0995}\u{09BE}</td><td class="key">a</td><td class="sep"></td>
                <td class="bn">\u{0988} / \u{0995}\u{09C0}</td><td class="key">I</td><td class="sep"></td>
                <td class="bn">\u{098A} / \u{0995}\u{09C2}</td><td class="key">U</td>
            </tr>
            <tr>
                <td class="bn">\u{098B} / \u{0995}\u{09C3}</td><td class="key">rri</td><td class="sep"></td>
                <td class="bn">\u{098F} / \u{0995}\u{09C7}</td><td class="key">e</td><td class="sep"></td>
                <td class="bn">\u{0993} / \u{0995}\u{09CB}</td><td class="key">O</td>
            </tr>
            <tr>
                <td class="bn">\u{0990} / \u{0995}\u{09C8}</td><td class="key">OI</td><td class="sep"></td>
                <td class="bn">\u{0994} / \u{0995}\u{09CC}</td><td class="key">OU</td><td class="sep"></td>
                <td class="bn"></td><td class="key"></td>
            </tr>
            </table>

            <div class="section-title">Special</div>
            <table>
            <tr>
                <td class="bn pair-wide">\u{09CD} \u{09B9}\u{09B8}\u{09A8}\u{09CD}\u{09A4}</td><td class="key">,,</td><td class="sep"></td>
                <td class="bn pair-wide">\u{09AC}-\u{09AB}\u{09B2}\u{09BE}</td><td class="key">w</td><td class="sep"></td>
                <td class="bn pair-wide">\u{09B0}\u{09C7}\u{09AB}</td><td class="key">rr (v)</td>
            </tr>
            <tr>
                <td class="bn">\u{09BC} \u{09A8}\u{09C1}\u{0995}\u{09CD}\u{09A4}\u{09BE}</td><td class="key">..</td><td class="sep"></td>
                <td class="bn">\u{09AF}-\u{09AB}\u{09B2}\u{09BE}</td><td class="key">y, Z</td><td class="sep"></td>
                <td class="bn">\u{0964} \u{09A6}\u{09BE}\u{09DC}\u{09BF}</td><td class="key">.</td>
            </tr>
            <tr>
                <td class="bn">ZWJ</td><td class="key">`</td><td class="sep"></td>
                <td class="bn">\u{09B0}-\u{09AB}\u{09B2}\u{09BE}</td><td class="key">r</td><td class="sep"></td>
                <td class="bn">\u{09F3} \u{099F}\u{09BE}\u{0995}\u{09BE}</td><td class="key">$</td>
            </tr>
            <tr>
                <td class="bn">ZWNJ</td><td class="key">~</td><td class="sep"></td>
                <td class="bn"></td><td class="key"></td><td class="sep"></td>
                <td class="bn"></td><td class="key"></td>
            </tr>
            </table>

            <div class="section-title">Numbers \u{09B8}\u{0982}\u{0996}\u{09CD}\u{09AF}\u{09BE}</div>
            <table>
            <tr>
                <td class="bn">\u{09E6}</td><td class="key">0</td><td class="sep"></td>
                <td class="bn">\u{09E7}</td><td class="key">1</td><td class="sep"></td>
                <td class="bn">\u{09E8}</td><td class="key">2</td><td class="sep"></td>
                <td class="bn">\u{09E9}</td><td class="key">3</td><td class="sep"></td>
                <td class="bn">\u{09EA}</td><td class="key">4</td>
            </tr>
            <tr>
                <td class="bn">\u{09EB}</td><td class="key">5</td><td class="sep"></td>
                <td class="bn">\u{09EC}</td><td class="key">6</td><td class="sep"></td>
                <td class="bn">\u{09ED}</td><td class="key">7</td><td class="sep"></td>
                <td class="bn">\u{09EE}</td><td class="key">8</td><td class="sep"></td>
                <td class="bn">\u{09EF}</td><td class="key">9</td>
            </tr>
            </table>

            </body>
            </html>
            """
    }
}
