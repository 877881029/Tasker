from dataclasses import replace

import pytest

from tasker.shell.status import apply_status
from tasker.store import Store


@pytest.mark.parametrize(
    "start, target, expected",
    [
        ("pending", "urgent", "urgent"),
        ("urgent", "pending", "pending"),
        ("pending", "done", "done"),
        ("urgent", "done", "done"),
        ("pending", "pending", "pending"),
    ],
)
def test_apply_status_reaches_target(tmp_path, start, target, expected):
    store = Store(tmp_path)
    item = store.save(replace(store.create(), state=start, resume_state=start))
    assert apply_status(store, item.id, target).state == expected
    assert store.get(item.id).state == expected


def test_reopening_done_restores_then_switches(tmp_path):
    store = Store(tmp_path)
    item = store.save(replace(store.create(), state="urgent", resume_state="urgent"))
    apply_status(store, item.id, "done")
    assert apply_status(store, item.id, "urgent").state == "urgent"
    apply_status(store, item.id, "done")
    reopened = apply_status(store, item.id, "pending")
    assert reopened.state == "pending"
    assert reopened.resume_state == "pending"
