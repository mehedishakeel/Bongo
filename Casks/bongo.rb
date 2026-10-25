cask "bongo" do
  arch arm: "arm64", intel: "intel-x86_64"

  version "1.1.0"
  sha256 arm:   "9f930f383724da7e3b65d10cc99dcb09fd83ffda4e918f7f3e4689605abbf2e3",
         intel: "eda5a6d675970cec946f7af25f7be65a99518516e94b3fc39d036c49c9e9211a"

  url "https://github.com/mehedishakeel/Bongo/releases/download/v#{version}/Bongo-#{version}-macos-#{arch}.dmg"
  name "Bongo"
  desc "Native Bangla Phonetic Keyboard for macOS"
  homepage "https://getbongo.app/"

  livecheck do
    url :url
    strategy :github_latest
  end

  auto_updates true
  depends_on macos: :ventura

  app "Bongo.app"

  zap trash: [
    "~/Library/Application Support/Bongo",
    "~/Library/Caches/org.bongo.Bongo",
    "~/Library/Caches/org.bongo.inputmethod.Bongo",
    "~/Library/Preferences/org.bongo.Bongo.plist",
    "~/Library/Preferences/org.bongo.inputmethod.Bongo.plist",
  ]
end
