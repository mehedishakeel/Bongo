cask "bongo" do
  version "1.0"
  sha256 "5bf0aa61b0e82e692e0f5f34c6c31f86bfff3d7209a9d24ed9c96dfcea9a9b2a"

  url "https://github.com/mehedishakeel/Bongo/releases/download/v#{version}/Bongo-#{version}-macos-arm64.dmg"
  name "Bongo"
  desc "Native Bengali phonetic input method (IME) for Apple Silicon"
  homepage "https://getbongo.app/"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on arch: :arm64
  depends_on macos: :ventura

  app "Bongo.app"

  uninstall quit: [
    "com.mehedishakeel.Bongo",
    "com.mehedishakeel.inputmethod.Bongo",
  ]

  zap trash: [
    "~/Library/Application Support/Bongo",
    "~/Library/Caches/com.mehedishakeel.Bongo",
    "~/Library/Preferences/com.mehedishakeel.Bongo.plist",
    "~/Library/Preferences/com.mehedishakeel.inputmethod.Bongo.plist",
  ]

  caveats <<~EOS
    Bongo is a macOS Input Method. To enable it:
      1. Open Bongo once from /Applications
      2. Open System Settings → Keyboard → Input Sources → Edit → +
      3. Select "Bangla" (Bengali) and add "Bongo"
      4. Switch input sources with the Globe key (fn) or Control+Space
  EOS
end
