#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Generate Bongo's Linux update feed")
parser.add_argument("--repository", required=True, help="GitHub owner/repository")
parser.add_argument("--version", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
version = args.version.lstrip("vV")
base = f"https://github.com/{args.repository}"
manifest = {
    "updates": {
        "linux": {
            "open-url": f"{base}/releases/tag/v{version}",
            "latest-version": version,
            "download-url": f"{base}/releases/tag/v{version}",
            "changelog": f"{base}/releases/tag/v{version}",
        }
    }
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(manifest, indent=2) + "\n")
