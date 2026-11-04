# Bongo AUR Package (`bongo-bin`)

Official Arch User Repository (AUR) package definition for **Bongo** on Arch Linux, Manjaro, EndeavourOS, and Omarchy.

This package installs prebuilt Bongo binaries directly from official GitHub releases for `x86_64` and `aarch64`.

## For Users

### Install via AUR Helper

```bash
# Using yay:
yay -S bongo-bin

# Using paru:
paru -S bongo-bin
```

### Install Manually with makepkg

```bash
git clone https://aur.archlinux.org/bongo-bin.git
cd bongo-bin
makepkg -si
```

---

## For Maintainers: Publishing & Updating on AUR

### Prerequisites

Ensure you have your SSH key configured with your Arch Linux AUR account:
```bash
# Test SSH connection to AUR:
ssh -T aur@aur.archlinux.org
```

### Initial Setup (First Time Publishing)

```bash
git clone ssh://aur@aur.archlinux.org/bongo-bin.git aur-repo
cd aur-repo
cp /path/to/Bongo/platforms/linux/packaging/aur/bongo-bin/* .
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO bongo-bin.install README.md
git commit -m "feat: initial release of bongo-bin"
git push -u origin master
```

### Updating for a New Release

1. Update `pkgver` in `PKGBUILD`.
2. Reset `pkgrel=1`.
3. Regenerate `.SRCINFO`:
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```
4. Test local build:
   ```bash
   makepkg -f
   ```
5. Commit and push:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "chore: bump to v<new_version>"
   git push
   ```
