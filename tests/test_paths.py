from pathlib import Path

from tasker.paths import attachments_dir, data_dir, db_path, tasks_dir


def test_data_dir_uses_tasker_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    assert data_dir() == tmp_path.resolve()
    assert db_path() == tmp_path.resolve() / "tasker.sqlite"
    assert tasks_dir() == tmp_path.resolve() / "tasks"
    assert attachments_dir("abc") == tmp_path.resolve() / "tasks" / "abc"


def test_data_dir_does_not_use_reader_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    assert "Reader" not in str(data_dir())
