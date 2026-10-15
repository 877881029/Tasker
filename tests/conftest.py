from __future__ import annotations

import os
from pathlib import Path

# A desktop-sized virtual screen: the default offscreen screen is 800x800,
# which is narrower than a dock plus its detail paper.
# QPA arguments are ':'-separated, so a drive-letter path cannot be used.
_SCREEN = Path(os.path.relpath(Path(__file__).with_name("offscreen.json"))).as_posix()
os.environ.setdefault("QT_QPA_PLATFORM", f"offscreen:configfile={_SCREEN}")
os.environ.setdefault("TASKER_SKIP_SHELL_INTEGRATION", "1")
os.environ.setdefault("TASKER_NO_RECYCLE", "1")
