cask "bongo" do
  arch arm: "arm64", intel: "intel-x86_64"

  version "1.2.0"
  sha256 arm:   "89a1dd4c71d8affe5667e28d0d69d7cf0bd9d5a79be0d87e9a1c0ec41405ea53",
         intel: "688c88fbde6c4650538ec4d7bf20579c96ea8fbd69ef6560871d21c6f34ba34c"

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
