cask "bongo" do
  arch arm: "arm64", intel: "intel-x86_64"

  version "1.1.0"
  sha256 arm:   "e665524a77f47fd5c88cacdd0a8d2ec1c9cfadbfb68b7fba212f787a8e5c6d64",
         intel: "0fa7551e74b140511510a3080fab592210ce61ec7cd64c5ed7850e70cc8e9fe6"

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
