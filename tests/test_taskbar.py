from tasker.shell.taskbar import apply_taskbar_icon, force_iconic_representation


def test_taskbar_helpers_reject_null_hwnd(tmp_path):
    ico = tmp_path / "x.ico"
    ico.write_bytes(b"0")
    assert force_iconic_representation(0) is False
    assert apply_taskbar_icon(0, ico) is False
