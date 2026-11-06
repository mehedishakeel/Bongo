cask "bongo" do
  arch arm: "arm64", intel: "intel-x86_64"

  version "1.2.0"
  sha256 arm:   "56b477bbfc3194590ad01229613ec61a993198cfab8507b08468123b72d40d7d",
         intel: "d9660e16037ef0fc9c9fcdc5ef0c43ab43123d05c531c24167c340032e218f40"

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
