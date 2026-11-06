cask "bongo" do
  arch arm: "arm64", intel: "intel-x86_64"

  version "1.2.0"
  sha256 arm:   "575574f833ddc96c5d60f3bfc26e8df08f9fb307f87f67086ac3af1ae4eed76a",
         intel: "0cc2f4d67a3b89192d15b4728f22e1be0dbe836047b85de048f4a48663f89112"

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
