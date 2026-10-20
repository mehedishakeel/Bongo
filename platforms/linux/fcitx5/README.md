# Bongo for fcitx5

Native fcitx5 frontend for Bongo's Rust Avro phonetic engine.

## Build

```bash
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build/fcitx5
```

## Install

The addon must be installed system-wide:

```bash
sudo cmake --install build/fcitx5
```

Then add **Bongo** in `fcitx5-configtool` and switch to it with `Ctrl+Space`.
The candidate font follows the fcitx5 theme; Bongo's `candidate_font` setting
is used by the IBus frontend only.
