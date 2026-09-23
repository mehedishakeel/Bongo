#!/usr/bin/env python3
from pathlib import Path
import zipfile
root = Path(__file__).resolve().parents[1]
version = (root / 'platforms/linux/version.txt').read_text().strip()
out = root / f'dist/Bongo-{version}-source.zip'
out.parent.mkdir(exist_ok=True)
excluded = {'.git', 'upstream', '.toolchains', '.cache', 'dist', 'build', 'target', '__pycache__', '.DS_Store'}
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, strict_timestamps=False) as z:
    for f in sorted(root.rglob('*')):
        rel = f.relative_to(root)
        if rel.parts[0] in excluded or any(part in {'.git', '__pycache__', '.DS_Store'} for part in rel.parts) or (rel.parts[0] == 'platforms' and any(part in {'build', 'target'} for part in rel.parts)):
            continue
        if f.is_file():
            z.write(f, Path('Bongo') / rel)
print(out)
