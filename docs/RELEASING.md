# Releasing Bongo

The official repository is [mehedishakeel/Bongo](https://github.com/mehedishakeel/Bongo).

Builds default to `mehedishakeel/Bongo`. Set the environment variable `BONGO_GITHUB_REPOSITORY=owner/repository` only when packaging a fork.
The macOS build writes this repository into the app so **Check for Updates** can query GitHub Releases.

For a release:

1. Install prerequisites listed in [BUILDING.md](BUILDING.md).
2. Update the version in `platforms/macos/Bongo/Resources/Info.plist` and `platforms/macos/Launcher/Resources/Info.plist`.
3. Review release notes.
4. Create release artifacts with `./platforms/macos/scripts/create-dmg.sh`. For public releases, sign and notarize with an Apple Developer ID certificate.
5. Commit, tag the release version as `vX.Y.Z`, and push the tag.
6. Create a GitHub Release, attach `platforms/macos/release/Bongo-*-macos-arm64.dmg`, and publish it.

The updater only announces a newer release and opens its page. Installation stays under the user's control.
