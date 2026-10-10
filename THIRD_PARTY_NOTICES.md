# Bongo — upstream attribution

Bongo is an independent derivative project, not an official release or endorsement
from OmicronLab, Abdur Rahim, or the OpenBangla team. The Bongo Phonetic product
label identifies Bongo's compatible presentation of the Avro Phonetic method; it
does not claim authorship of that method. Original source headers and licenses
remain in place.

| Component | Source | License / use |
|---|---|---|
| Avro Keyboard | https://github.com/omicronlab/Avro-Keyboard | Phonetic layout scheme compatibility, © OmicronLab; original developer Mehdi Hasan Khan |
| Lekho | https://github.com/ARahim3/Lekho | MPL-2.0; Swift InputMethodKit implementation and icon-generation foundation, by Abdur Rahim |
| riti | https://github.com/OpenBangla/riti | MPL-2.0; native phonetic conversion engine, by OpenBangla contributors |

Exact source revisions are recorded in `upstream.lock.json`.
Apple Silicon macOS transitive Rust dependencies and versions are recorded in `platforms/macos/engine/Cargo.lock`.

Bongo modifications: independent product IDs, settings paths, runtime names,
Bongo branding and original icon, Bongo-owned GitHub release checks, Apple Silicon
DMG packaging, pinned dependencies, release documentation and verification tests.
The Bongo Phonetic layout-guide artwork is a new Bongo-branded rendering. It does
not include the upstream Avro artwork, logo, OmicronLab URL, or Avro branding.

Distribute the corresponding Bongo source archive alongside binary releases.
Keep licenses and original author notices.

The macOS dependency sources are bundled in vendor/rust, with dependency
licenses and author metadata collected under licenses/rust.
