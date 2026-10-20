#!/usr/bin/env python3
"""Safely add Bongo to an fcitx5 input-method profile.

The helper edits the line-based profile instead of rewriting it with
configparser. Existing groups, items, comments, and ordering are preserved.

Run this only while fcitx5 is stopped: fcitx5 rewrites the profile when it
exits and would discard the change. Stop it with ``fcitx5-remote -e``,
run the helper, then start fcitx5 again (``fcitx5 -d``). The Bongo
installer performs this stop-configure-restart sequence automatically.
"""

import argparse
import os
import pwd
import re
import shutil
import sys
from pathlib import Path


MINIMAL_PROFILE = """[Groups/0]
Name=Default
Default Layout=us
DefaultIM=bongo

[Groups/0/Items/0]
Name=keyboard-us
Layout=

[Groups/0/Items/1]
Name=bongo
Layout=

[GroupOrder]
0=Default
"""


def manual_steps() -> str:
    return """Add Bongo to fcitx5 manually:

1. Run: fcitx5-configtool
2. Open the Input Method tab.
3. Click "+" and choose Bongo.
4. Apply the change and restart fcitx5:
   fcitx5-remote -r
5. Switch input methods with Ctrl+Space.

If you prefer the profile file, append this item inside the first group:
   [Groups/0/Items/<next-index>]
   Name=bongo
   Layout=
"""


def profile_path(profile: Path | None = None) -> Path:
    if profile is not None:
        return Path(profile)

    if os.geteuid() == 0 and os.environ.get("SUDO_USER"):
        try:
            home = Path(pwd.getpwnam(os.environ["SUDO_USER"]).pw_dir)
        except KeyError:
            home = Path.home()
        return home / ".config" / "fcitx5" / "profile"

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "fcitx5" / "profile"
    return Path.home() / ".config" / "fcitx5" / "profile"


def _sections(lines):
    starts = [
        index
        for index, line in enumerate(lines)
        if line.strip().startswith("[") and line.strip().endswith("]")
    ]
    sections = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        sections.append((lines[start].strip(), start, end))
    return sections


def _first_value(lines, start, end, key):
    prefix = f"{key}="
    for line in lines[start + 1 : end]:
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return None


def _first_group_name(lines, sections):
    for header, start, end in sections:
        if header != "[GroupOrder]":
            continue
        for line in lines[start + 1 : end]:
            match = re.match(r"\s*0\s*=\s*(.+?)\s*$", line)
            if match:
                return match.group(1)
    return None


def _find_group(lines, sections, group_name):
    groups = []
    for position, (header, start, end) in enumerate(sections):
        match = re.fullmatch(r"\[Groups/(\d+)\]", header)
        if match:
            groups.append(
                (int(match.group(1)), position, header, start, end)
            )

    if not groups:
        return None

    if group_name is not None:
        for group in groups:
            if _first_value(lines, group[3], group[4], "Name") == group_name:
                return group
    return groups[0]


def _has_bongo(lines, sections, group_number):
    for header, start, end in sections:
        match = re.fullmatch(r"\[Groups/" + str(group_number) + r"/Items/\d+\]", header)
        if not match:
            continue
        if (_first_value(lines, start, end, "Name") or "").lower() == "bongo":
            return True
    return False


def _item_indices(sections, group_number):
    indices = []
    for header, start, end in sections:
        match = re.fullmatch(
            r"\[Groups/" + str(group_number) + r"/Items/(\d+)\]", header
        )
        if match:
            indices.append(int(match.group(1)))
    return indices


def _insertion_point(lines, sections, group_number, group_start):
    item_positions = []
    for position, (header, start, end) in enumerate(sections):
        if re.fullmatch(
            r"\[Groups/" + str(group_number) + r"/Items/\d+\]", header
        ):
            item_positions.append(position)

    if item_positions:
        last_position = item_positions[-1]
        if last_position + 1 < len(sections):
            return sections[last_position + 1][1]
        return len(lines)

    for header, start, end in sections:
        if start > group_start:
            return start
    return len(lines)


def _chown_to_target(path: Path) -> None:
    if os.geteuid() != 0 or not os.environ.get("SUDO_USER"):
        return
    try:
        target = pwd.getpwnam(os.environ["SUDO_USER"])
    except KeyError:
        return
    try:
        os.chown(path, target.pw_uid, target.pw_gid)
    except OSError:
        pass


def configure_profile(profile: Path) -> bool:
    profile = Path(profile)
    if not profile.exists():
        profile.parent.mkdir(parents=True, exist_ok=True)
        profile.write_text(MINIMAL_PROFILE)
        _chown_to_target(profile)
        return True

    text = profile.read_text()
    lines = text.splitlines(keepends=True)
    if not lines:
        return False

    sections = _sections(lines)
    group_name = _first_group_name(lines, sections)
    group = _find_group(lines, sections, group_name)
    if group is None:
        return False

    group_number, _, _, group_start, _ = group
    if _has_bongo(lines, sections, group_number):
        return True

    indices = _item_indices(sections, group_number)
    next_index = max(indices) + 1 if indices else 0
    insertion = _insertion_point(lines, sections, group_number, group_start)

    block = (
        f"\n[Groups/{group_number}/Items/{next_index}]\n"
        "Name=bongo\n"
        "Layout=\n\n"
    )
    if insertion > 0 and not lines[insertion - 1].endswith("\n"):
        lines[insertion - 1] += "\n"
    lines.insert(insertion, block)

    backup = profile.with_name(profile.name + ".bongo-backup")
    if not backup.exists():
        shutil.copy2(profile, backup)
        _chown_to_target(backup)

    profile.write_text("".join(lines))
    _chown_to_target(profile)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add Bongo to the fcitx5 input-method profile."
    )
    parser.add_argument(
        "--profile",
        type=Path,
        help="profile to edit (default: the current user's fcitx5 profile)",
    )
    parser.add_argument(
        "--print-manual-steps",
        action="store_true",
        help="print manual setup instructions and do not edit anything",
    )
    args = parser.parse_args()

    if args.print_manual_steps:
        print(manual_steps())
        return 0

    target = profile_path(args.profile)
    if not configure_profile(target):
        print(
            f"Could not understand the fcitx5 profile at {target}; "
            "leaving it unchanged.",
            file=sys.stderr,
        )
        print(manual_steps(), file=sys.stderr)
        return 1

    print(f"Bongo is configured in {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
