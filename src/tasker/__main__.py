from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication

from tasker.app import TaskerApp, set_app_user_model_id
from tasker.resources import resource_path


def frozen_exe_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(__file__).resolve().parents[2] / "dist" / "Tasker" / "Tasker.exe"


def _launch_target() -> tuple[str, tuple[str, ...]]:
    if getattr(sys, "frozen", False):
        return sys.executable, ()
    frozen = frozen_exe_path()
    if frozen.is_file():
        return str(frozen), ()
    return sys.executable, ("-m", "tasker")


def _shell_integration_disabled() -> bool:
    value = os.environ.get("TASKER_SKIP_SHELL_INTEGRATION", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _install_shell_integration(app: TaskerApp) -> None:
    from tasker.shell.shortcut import create_desktop_shortcut

    exe, args = _launch_target()
    try:
        create_desktop_shortcut(
            exe,
            args=args,
            icon=str(resource_path("assets", "icons", "tasker.ico")),
            overwrite=True,
        )
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if any(arg in {"-h", "--help"} for arg in argv[1:]):
        print("Tasker — local workbench")
        return 0
    set_app_user_model_id()
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    qapp = QApplication.instance() or QApplication(argv)
    app = TaskerApp(qapp)
    app.show_dock()
    if not _shell_integration_disabled():
        QTimer.singleShot(0, lambda: _install_shell_integration(app))
    return qapp.exec()


if __name__ == "__main__":
    raise SystemExit(main())
