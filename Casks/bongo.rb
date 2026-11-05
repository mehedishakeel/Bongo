cask "bongo" do
  arch arm: "arm64", intel: "intel-x86_64"

  version "1.2.0"
  sha256 arm:   "e5e4744b42ab4e4fc62f47f684a629186f59bf287d6b64481cf830381dc2bd21",
         intel: "91187711806e0cc947416f5f5be031b86746d982eb5518e5484c0bed577fe751"

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
