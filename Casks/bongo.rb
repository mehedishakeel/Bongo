cask "bongo" do
  arch arm: "arm64", intel: "intel-x86_64"

  version "1.2.0"
  sha256 arm:   "ac28a687c09ba93f15420154634232fbf8f2dcd48de1bd9e730032a745b7f665",
         intel: "974f3fadae5ae7feb1cfdc6358d0b9e6cd49b47315f8a716d89aa3aaaa7a383b"

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
