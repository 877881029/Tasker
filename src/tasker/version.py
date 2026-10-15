from __future__ import annotations

import sys

from tasker.resources import resource_path


def app_version() -> str:
    path = resource_path("VERSION")
    try:
        return path.read_text(encoding="utf-8").strip() or "0.0.0"
    except OSError:
        return "0.0.0"


RELEASES_URL = "https://github.com/877881029/Tasker-releases/releases"
REPO_URL = "https://github.com/877881029/Tasker"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))
