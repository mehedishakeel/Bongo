import Cocoa

// MARK: - Font Settings

enum BongoFontSettings {
    static let familyKey = "BongoCandidateFontFamily"
    static let sizeKey = "BongoCandidateFontSize"

    static var familyName: String? {
        get { UserDefaults.standard.string(forKey: familyKey) }
        set {
            if let newValue, !newValue.isEmpty {
                UserDefaults.standard.set(newValue, forKey: familyKey)
            } else {
                UserDefaults.standard.removeObject(forKey: familyKey)
            }
        }
    }

    static var size: CGFloat {
        get {
            let value = UserDefaults.standard.double(forKey: sizeKey)
            return value >= 12 && value <= 32 ? CGFloat(value) : 16
        }
        set { UserDefaults.standard.set(Double(newValue), forKey: sizeKey) }
    }

    static func font(ofSize fontSize: CGFloat = size) -> NSFont {
        if let familyName, let resolved = resolveFont(family: familyName, size: fontSize) {
            return resolved
        }
        return .systemFont(ofSize: fontSize, weight: .regular)
    }

    static func resolveFont(family: String, size: CGFloat) -> NSFont? {
        if let members = NSFontManager.shared.availableMembers(ofFontFamily: family) {
            let preferred = members.first { member in
                guard let style = member[1] as? String else { return false }
                return style.caseInsensitiveCompare("Regular") == .orderedSame
            } ?? members.first
            if let preferred, let psName = preferred[0] as? String,
               let font = NSFont(name: psName, size: size) {
                return font
            }
        }
        if let font = NSFontManager.shared.font(withFamily: family, traits: [], weight: 5, size: size) {
            return font
        }
        return NSFont(name: family, size: size)
    }
}

// MARK: - CandidatePanel Controller

class CandidatePanel {
    private var panel: NSPanel?
    private var contentView: CandidateView?

    /// Called when user clicks a candidate. Parameter is the candidate index.
    var onCandidateSelected: ((Int) -> Void)?

    func show(candidates: [String], auxiliaryText: String, selectedIndex: Int, cursorRect: NSRect) {
        if panel == nil {
            createPanel()
        }

        guard let panel = panel, let contentView = contentView else { return }

        contentView.update(candidates: candidates, auxiliaryText: auxiliaryText, selectedIndex: selectedIndex)

        // Size the panel to fit content
        let size = contentView.idealSize()
        panel.setContentSize(size)

        // Position below cursor with modern macOS screen clamping
        var origin = cursorRect.origin
        origin.y -= size.height + 6

        let cursorPoint = NSPoint(x: cursorRect.midX, y: cursorRect.midY)
        let screen = NSScreen.screens.first(where: { $0.frame.contains(cursorPoint) }) ?? NSScreen.main

        if let screen = screen {
            let sf = screen.visibleFrame

            // Horizontal: keep panel fully on screen
            origin.x = max(sf.minX + 8, min(origin.x, sf.maxX - size.width - 8))

            // Vertical: prefer below cursor; flip above if not enough room
            if origin.y < sf.minY {
                origin.y = cursorRect.maxY + 6
            }
            if origin.y + size.height > sf.maxY {
                origin.y = sf.maxY - size.height - 8
            }
            if origin.y < sf.minY {
                origin.y = sf.minY + 8
            }
        }

        panel.setFrameOrigin(origin)
        panel.orderFront(nil)
    }

    func hide() {
        panel?.orderOut(nil)
    }

    func selectCandidate(at index: Int) {
        contentView?.setSelectedIndex(index)
    }

    private func createPanel() {
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 280, height: 200),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: true
        )
        panel.level = .popUpMenu
        panel.isFloatingPanel = true
        panel.hidesOnDeactivate = false
        panel.hasShadow = true
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]

        let container = NSVisualEffectView()
        container.material = .hudWindow
        container.blendingMode = .withinWindow
        container.state = .active
        container.wantsLayer = true
        container.layer?.cornerRadius = 11
        container.layer?.cornerCurve = .continuous
        container.layer?.borderWidth = 0.5
        container.layer?.borderColor = NSColor.separatorColor.withAlphaComponent(0.35).cgColor
        container.layer?.masksToBounds = true

        let contentView = CandidateView()
        contentView.translatesAutoresizingMaskIntoConstraints = false
        contentView.onCandidateClicked = { [weak self] index in
            self?.onCandidateSelected?(index)
        }
        container.addSubview(contentView)

        NSLayoutConstraint.activate([
            contentView.topAnchor.constraint(equalTo: container.topAnchor),
            contentView.bottomAnchor.constraint(equalTo: container.bottomAnchor),
            contentView.leadingAnchor.constraint(equalTo: container.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: container.trailingAnchor),
        ])

        panel.contentView = container
        self.panel = panel
        self.contentView = contentView
    }
}

// MARK: - CandidateView (Vibrant Modern macOS HUD)

class CandidateView: NSView {
    private var candidates: [String] = []
    private var auxiliaryText: String = ""
    private var selectedIndex: Int = 0
    private var scrollOffset: Int = 0
    private var hoveredIndex: Int?

    var onCandidateClicked: ((Int) -> Void)?

    static let accent: NSColor = NSColor(name: nil) { appearance in
        let isDark = appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
        return isDark
            ? NSColor(srgbRed: 129/255, green: 140/255, blue: 248/255, alpha: 1.0)
            : NSColor(srgbRed: 79/255, green: 70/255, blue: 229/255, alpha: 1.0)
    }

    private let padding: CGFloat = 7
    private var rowHeight: CGFloat { max(27, BongoFontSettings.size + 11) }
    private let auxHeight: CGFloat = 24
    private let maxVisibleCandidates = 9

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
        NotificationCenter.default.addObserver(
            self, selector: #selector(fontSettingChanged),
            name: .bongoFontSettingChanged, object: nil)
    }

    required init?(coder: NSCoder) { fatalError() }

    @objc private func fontSettingChanged() {
        needsDisplay = true
        if let panel = window as? NSPanel { panel.setContentSize(idealSize()) }
    }

    func update(candidates: [String], auxiliaryText: String, selectedIndex: Int) {
        self.candidates = candidates
        self.auxiliaryText = auxiliaryText
        self.selectedIndex = candidates.isEmpty ? 0 : min(selectedIndex, candidates.count - 1)
        adjustScroll()
        needsDisplay = true
    }

    func setSelectedIndex(_ index: Int) {
        self.selectedIndex = candidates.isEmpty ? 0 : min(index, candidates.count - 1)
        adjustScroll()
        needsDisplay = true
    }

    private func adjustScroll() {
        if selectedIndex < scrollOffset {
            scrollOffset = selectedIndex
        } else if selectedIndex >= scrollOffset + maxVisibleCandidates {
            scrollOffset = selectedIndex - maxVisibleCandidates + 1
        }
        scrollOffset = max(0, scrollOffset)
    }

    func idealSize() -> NSSize {
        let totalCount = candidates.count
        let visibleCount = min(totalCount - scrollOffset, maxVisibleCandidates)
        let height = CGFloat(visibleCount) * rowHeight + auxHeight + padding * 2
        let width: CGFloat = 286
        return NSSize(width: width, height: height)
    }

    override func draw(_ dirtyRect: NSRect) {
        let bounds = self.bounds
        let visibleStart = scrollOffset
        let visibleEnd = min(scrollOffset + maxVisibleCandidates, candidates.count)
        let visibleCount = visibleEnd - visibleStart

        // 1. Auxiliary Header Bar (Typed letters + Language Tag)
        let auxRect = NSRect(
            x: padding + 2,
            y: bounds.height - auxHeight - padding + 2,
            width: bounds.width - (padding * 2) - 4,
            height: auxHeight - 4
        )

        // Subtle header divider
        let dividerY = bounds.height - auxHeight - padding + 1
        let dividerPath = NSBezierPath()
        dividerPath.move(to: NSPoint(x: padding + 2, y: dividerY))
        dividerPath.line(to: NSPoint(x: bounds.width - padding - 2, y: dividerY))
        NSColor.separatorColor.withAlphaComponent(0.25).setStroke()
        dividerPath.lineWidth = 0.5
        dividerPath.stroke()

        if !auxiliaryText.isEmpty {
            let auxTextRect = NSRect(x: auxRect.minX + 2, y: auxRect.minY + 1, width: auxRect.width - 50, height: auxRect.height)
            let auxAttrs: [NSAttributedString.Key: Any] = [
                .font: NSFont.monospacedSystemFont(ofSize: 11.5, weight: .semibold),
                .foregroundColor: NSColor.secondaryLabelColor
            ]
            auxiliaryText.draw(in: auxTextRect, withAttributes: auxAttrs)
        }

        // Bongo branding tag on right
        let tagRect = NSRect(x: bounds.width - padding - 54, y: auxRect.minY + 2, width: 50, height: auxRect.height - 2)
        let tagAttrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 10, weight: .medium),
            .foregroundColor: NSColor.tertiaryLabelColor
        ]
        let tagText: String
        if candidates.count > maxVisibleCandidates {
            tagText = "\(selectedIndex + 1)/\(candidates.count)"
        } else {
            tagText = "বাংলা"
        }
        let tagString = NSAttributedString(string: tagText, attributes: tagAttrs)
        let tagSize = tagString.size()
        tagString.draw(at: NSPoint(x: tagRect.maxX - tagSize.width - 2, y: tagRect.minY + (tagRect.height - tagSize.height) / 2))

        // 2. Candidate Rows
        for i in 0..<visibleCount {
            let candidateIndex = scrollOffset + i
            let y = bounds.height - auxHeight - padding - CGFloat(i + 1) * rowHeight + 1
            let rowRect = NSRect(
                x: padding + 2,
                y: y,
                width: bounds.width - (padding * 2) - 4,
                height: rowHeight - 2
            )

            let isSelected = (candidateIndex == selectedIndex)
            let isHovered = (hoveredIndex == candidateIndex)

            // Selection pill
            if isSelected {
                let pillPath = NSBezierPath(roundedRect: rowRect, xRadius: 6, yRadius: 6)
                CandidateView.accent.setFill()
                pillPath.fill()
            } else if isHovered {
                let hoverPath = NSBezierPath(roundedRect: rowRect, xRadius: 6, yRadius: 6)
                NSColor.labelColor.withAlphaComponent(0.06).setFill()
                hoverPath.fill()
            }

            // Keyboard Shortcut Badge ([1], [2]...)
            let badgeWidth: CGFloat = 18
            let badgeHeight: CGFloat = 18
            let badgeRect = NSRect(
                x: rowRect.minX + 6,
                y: rowRect.midY - (badgeHeight / 2),
                width: badgeWidth,
                height: badgeHeight
            )

            if !isSelected {
                let badgePath = NSBezierPath(roundedRect: badgeRect, xRadius: 4, yRadius: 4)
                NSColor.labelColor.withAlphaComponent(0.06).setFill()
                badgePath.fill()
            }

            let numAttrs: [NSAttributedString.Key: Any] = [
                .font: NSFont.monospacedDigitSystemFont(ofSize: 11, weight: .semibold),
                .foregroundColor: isSelected
                    ? NSColor.white
                    : NSColor.secondaryLabelColor
            ]
            let numStr = "\(candidateIndex + 1)"
            let numSize = (numStr as NSString).size(withAttributes: numAttrs)
            let numPoint = NSPoint(
                x: badgeRect.midX - (numSize.width / 2),
                y: badgeRect.midY - (numSize.height / 2)
            )
            numStr.draw(at: numPoint, withAttributes: numAttrs)

            // Candidate Word Text
            let textX = badgeRect.maxX + 9
            let textWidth = rowRect.maxX - textX - 6
            let textRect = NSRect(
                x: textX,
                y: rowRect.minY + 2,
                width: textWidth,
                height: rowHeight - 6
            )

            let candidateFont = BongoFontSettings.font()
            let textAttrs: [NSAttributedString.Key: Any] = [
                .font: candidateFont,
                .foregroundColor: isSelected
                    ? NSColor.white
                    : NSColor.labelColor
            ]
            candidates[candidateIndex].draw(in: textRect, withAttributes: textAttrs)
        }

        // 3. Scroll arrows if needed
        let indicatorColor = NSColor.secondaryLabelColor.withAlphaComponent(0.6)
        if scrollOffset > 0 {
            let arrowRect = NSRect(x: bounds.width - padding - 16, y: bounds.height - auxHeight - padding - 6, width: 8, height: 5)
            drawUpArrow(in: arrowRect, color: indicatorColor)
        }
        if visibleEnd < candidates.count {
            let arrowRect = NSRect(x: bounds.width - padding - 16, y: padding + 3, width: 8, height: 5)
            drawDownArrow(in: arrowRect, color: indicatorColor)
        }
    }

    private func drawUpArrow(in rect: NSRect, color: NSColor) {
        let path = NSBezierPath()
        path.move(to: NSPoint(x: rect.midX, y: rect.maxY))
        path.line(to: NSPoint(x: rect.minX, y: rect.minY))
        path.line(to: NSPoint(x: rect.maxX, y: rect.minY))
        path.close()
        color.setFill()
        path.fill()
    }

    private func drawDownArrow(in rect: NSRect, color: NSColor) {
        let path = NSBezierPath()
        path.move(to: NSPoint(x: rect.midX, y: rect.minY))
        path.line(to: NSPoint(x: rect.minX, y: rect.maxY))
        path.line(to: NSPoint(x: rect.maxX, y: rect.maxY))
        path.close()
        color.setFill()
        path.fill()
    }

    // MARK: - Mouse Interaction

    override func acceptsFirstMouse(for event: NSEvent?) -> Bool {
        return true
    }

    override func mouseDown(with event: NSEvent) {
        let point = convert(event.locationInWindow, from: nil)
        if let index = candidateIndex(at: point) {
            selectedIndex = index
            adjustScroll()
            needsDisplay = true
        }
    }

    override func mouseUp(with event: NSEvent) {
        let point = convert(event.locationInWindow, from: nil)
        if let index = candidateIndex(at: point), index == selectedIndex {
            onCandidateClicked?(index)
        }
    }

    private func candidateIndex(at point: NSPoint) -> Int? {
        let topOfCandidates = bounds.height - auxHeight - padding
        let clickOffset = topOfCandidates - point.y
        guard clickOffset >= 0 else { return nil }

        let rowIndex = Int(clickOffset / rowHeight)
        guard rowIndex < maxVisibleCandidates else { return nil }
        let candidateIndex = scrollOffset + rowIndex
        guard candidateIndex >= 0 && candidateIndex < candidates.count else { return nil }
        return candidateIndex
    }
}
