from tasker.ipc import SingleInstance, server_name


def test_server_name_uses_namespace(monkeypatch):
    monkeypatch.setenv("TASKER_IPC_NAMESPACE", "pytest-one")
    assert "pytest-one" in server_name()


def test_second_instance_cannot_become_server(qapp, monkeypatch, tmp_path):
    monkeypatch.setenv("TASKER_IPC_NAMESPACE", f"pytest-{tmp_path.name}")
    first = SingleInstance()
    assert first.become_server(lambda: None)
    second = SingleInstance()
    assert second.become_server(lambda: None) is False
    assert second.ping_existing() is True
    qapp.processEvents()
    qapp.processEvents()
