from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication

from tasker.identity import APP_USER_MODEL_ID
from tasker.paths import data_dir
from tasker.resources import resource_path
from tasker.shell.window import DockWindow
from tasker.store import Store


def set_app_user_model_id() -> None:
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


class TaskerApp:
    def __init__(self, qapp: QApplication) -> None:
        self.qapp = qapp
        self.store = Store(data_dir())
        self.dock = DockWindow(self.store)

    def show_dock(self) -> None:
        self.dock.show()
        self.dock.raise_()
        self.dock.activateWindow()
