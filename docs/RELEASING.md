# Releasing Bongo

The official repository is
[mehedishakeel/Bongo](https://github.com/mehedishakeel/Bongo).

Builds default to `mehedishakeel/Bongo`. Set the environment variable
`BONGO_GITHUB_REPOSITORY=owner/repository` only when packaging a fork.
The macOS build writes this repository into the app so **Check for Updates** can
query GitHub Releases. The Linux build uses the `linux.json` attached to the
latest release. Windows includes `platforms/windows/scripts/check-update.ps1`, which queries
the same GitHub Releases API.

For a release:

1. Update the versions in `platforms/macos/Bongo/Resources/Info.plist`,
   `platforms/linux/version.txt`, the Windows `Bongo.rc`, and the update scripts.
2. Review release notes and generate `linux.json` from the tag and repository
   using `scripts/generate-update-manifest.py`.
3. Create release artifacts with `platforms/macos/scripts/create-dmg.sh`,
   `platforms/linux/scripts/create-deb.sh`, and
   `platforms/windows/scripts/create-exe.ps1` on their
   respective operating systems. Sign and notarize macOS; Authenticode-sign
   Windows. Do not publish the current Windows target until its
   documented legacy dependencies and runtime data are complete.
4. Commit, tag the same version as `vX.Y.Z`, and push the tag.
5. Create a GitHub Release, attach the tested macOS, Linux and Windows artifacts
   that are available, attach `linux.json`, review the release, and publish it.

The updater only announces a newer release and opens its page. Installation stays
under the user's control, which avoids replacing a running input method.
