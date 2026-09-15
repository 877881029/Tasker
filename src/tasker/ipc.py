from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QLockFile, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "Tasker.SingleInstance.v1"
LOCK_DIR = Path(tempfile.gettempdir()) / "tasker-single-instance-locks"
ACTIVATE = b"ACTIVATE\n"


def server_name() -> str:
    namespace = os.environ.get("TASKER_IPC_NAMESPACE", "").strip()
    if not namespace:
        return SERVER_NAME
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", namespace)
    return f"{SERVER_NAME}.{safe}"


class SingleInstance:
    def __init__(self) -> None:
        self._name = server_name()
        self._server: QLocalServer | None = None
        self._lock: QLockFile | None = None
        self._on_activate: Callable[[], None] | None = None

    def become_server(self, on_activate: Callable[[], None]) -> bool:
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(LOCK_DIR / f"{self._name}.lock"))
        lock.setStaleLockTime(0)
        if not lock.tryLock(0):
            return False
        server = QLocalServer()
        QLocalServer.removeServer(self._name)
        if not server.listen(self._name):
            lock.unlock()
            return False
        self._lock = lock
        self._server = server
        self._on_activate = on_activate
        server.newConnection.connect(self._accept)
        return True

    def ping_existing(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self._name)
        if not socket.waitForConnected(1000):
            return False
        socket.write(ACTIVATE)
        socket.flush()
        socket.waitForBytesWritten(1000)
        app = QCoreApplication.instance()
        if app is not None:
            app.processEvents()
        socket.waitForDisconnected(300)
        socket.disconnectFromServer()
        return True

    def _accept(self) -> None:
        if self._server is None:
            return
        socket = self._server.nextPendingConnection()
        if socket is None:
            return
        QTimer.singleShot(0, lambda sock=socket: self._consume(sock))

    def _consume(self, socket: QLocalSocket) -> None:
        if socket.bytesAvailable() or socket.waitForReadyRead(500):
            self._read(socket)
        else:
            socket.readyRead.connect(lambda sock=socket: self._read(sock))

    def _read(self, socket: QLocalSocket) -> None:
        payload = bytes(socket.readAll())
        socket.close()
        if ACTIVATE.strip() in payload and self._on_activate is not None:
            self._on_activate()
