# Bongo — upstream attribution

Bongo is an independent derivative project, not an official release or endorsement
from OmicronLab, Abdur Rahim, or the OpenBangla team. Avro Phonetic remains the name
of the typing method. Original source headers and licenses remain in place.

| Component | Source | License / use |
|---|---|---|
| Avro Keyboard | https://github.com/omicronlab/Avro-Keyboard | MPL-1.1; Windows keyboard foundation, © OmicronLab; original developer Mehdi Hasan Khan |
| Lekho | https://github.com/ARahim3/Lekho | MPL-2.0; Swift InputMethodKit implementation and icon-generation foundation, by Abdur Rahim |
| OpenBangla Keyboard | https://github.com/OpenBangla/OpenBangla-Keyboard | GPL-3.0-or-later; Linux IBus and Qt application, original authors retained in source |
| riti | https://github.com/OpenBangla/riti | MPL-2.0; phonetic engines on Linux and macOS |

Exact source revisions are recorded in `upstream.lock.json`. The two riti revisions
are deliberately different: each native adapter uses its compatible upstream API.
Mac transitive Rust dependencies and versions are recorded in Cargo.lock. Windows
third-party dependencies (including DISQLite3) are not all supplied by upstream;
consult the retained upstream Readme.txt before building or redistributing them.

Bongo modifications: independent product IDs, settings paths, runtime names,
Bongo branding and original icon, Bongo-owned GitHub release checks, manual macOS
DMG packaging, pinned dependencies, release documentation and verification tests.

Distribute the corresponding Bongo source archive alongside binary releases.
Keep licenses and original author notices. The Windows source contains additional
third-party licenses, which remain applicable; this document does not replace them.

OmicronLab's jsAvroPhonetic was reviewed but is not used in the native binaries.

The macOS dependency sources are bundled in vendor/rust, with dependency
licenses and author metadata also collected under licenses/rust.
