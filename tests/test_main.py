from tasker.__main__ import main


def test_help_exits_zero():
    assert main(["tasker", "--help"]) == 0
