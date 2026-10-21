cask "bongo" do
  arch arm: "arm64", intel: "intel-x86_64"

  version "1.1.0"
  sha256 arm:   "1232a06564b02e9a6bae51df6524aa37a6010d1694bc927e3fdc9d795974d545",
         intel: "ab6929a587524b1b6e1e0724e3b5491e3152a79be24faf017b6c64338c9eff6e"

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
