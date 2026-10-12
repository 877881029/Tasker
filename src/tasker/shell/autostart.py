from __future__ import annotations

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Tasker"


def launch_command() -> str:
    from tasker.__main__ import _launch_target

    exe, args = _launch_target()
    return " ".join([f'"{exe}"', *args])


def is_enabled(key: str = RUN_KEY, name: str = VALUE_NAME) -> bool:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            value, _kind = winreg.QueryValueEx(handle, name)
        return bool(str(value).strip())
    except OSError:
        return False


def set_enabled(
    enabled: bool,
    command: str | None = None,
    key: str = RUN_KEY,
    name: str = VALUE_NAME,
) -> bool:
    try:
        import winreg

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE
        ) as handle:
            if enabled:
                winreg.SetValueEx(
                    handle, name, 0, winreg.REG_SZ, command or launch_command()
                )
            else:
                try:
                    winreg.DeleteValue(handle, name)
                except FileNotFoundError:
                    pass
    except OSError:
        return False
    return is_enabled(key, name) == enabled
