"""Bump the Tasker version everywhere it is recorded.

Usage:
    python scripts/bump_version.py            # patch +1 (1.0.25 -> 1.0.26)
    python scripts/bump_version.py 1.1.0      # set an explicit version
    python scripts/bump_version.py --check    # verify VERSION and version_info.txt agree
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
INFO_FILE = ROOT / "version_info.txt"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def next_patch(version: str) -> str:
    match = SEMVER.match(version)
    if match is None:
        raise SystemExit(f"VERSION is not X.Y.Z: {version!r}")
    major, minor, patch = (int(part) for part in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def render_info(text: str, version: str) -> str:
    major, minor, patch = version.split(".")
    tuple_text = f"({major}, {minor}, {patch}, 0)"
    text = re.sub(r"filevers=\([^)]*\)", f"filevers={tuple_text}", text)
    text = re.sub(r"prodvers=\([^)]*\)", f"prodvers={tuple_text}", text)
    text = re.sub(r"StringStruct\('FileVersion', '[^']*'\)", f"StringStruct('FileVersion', '{version}')", text)
    return re.sub(r"StringStruct\('ProductVersion', '[^']*'\)", f"StringStruct('ProductVersion', '{version}')", text)


def info_version(text: str) -> str | None:
    match = re.search(r"StringStruct\('ProductVersion', '([^']*)'\)", text)
    return match.group(1) if match else None


def main(argv: list[str]) -> int:
    info = INFO_FILE.read_text(encoding="utf-8")
    if argv and argv[0] == "--check":
        current = read_version()
        ok = info_version(info) == current and f"filevers=({current.replace('.', ', ')}, 0)" in info
        print(f"VERSION {current}, version_info {info_version(info)}: {'ok' if ok else 'MISMATCH'}")
        return 0 if ok else 1
    target = argv[0] if argv else next_patch(read_version())
    if SEMVER.match(target) is None:
        raise SystemExit(f"Not a X.Y.Z version: {target!r}")
    VERSION_FILE.write_text(target + "\n", encoding="utf-8")
    INFO_FILE.write_text(render_info(info, target), encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
