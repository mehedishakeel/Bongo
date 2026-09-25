# Validate Bongo

Run repository checks from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Run the Linux Rust engine tests serially because its upstream tests temporarily
change process-wide environment variables:

```sh
cd platforms/linux/src/engine/riti
cargo test --locked -- --test-threads=1
```

GitHub Actions repeats these checks, runs the macOS InputMethodKit integration
suite on Apple Silicon, and builds the Debian package on each push and pull
request.

## Release checks

Automated tests cover macOS phonetic output, candidates, learned choices,
punctuation, emoji settings, typing modes, editing, composition handoff, and
corrupt-data recovery. They do not establish compatibility with every real app.

Before a release, create artifacts on each matching OS and test installation,
uninstallation, input-source registration, real-app typing, update prompts, and
restart behavior. Sign and notarize macOS builds and Authenticode-sign Windows
builds when those channels are ready.
