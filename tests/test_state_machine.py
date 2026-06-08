import pytest

pytest.importorskip("fastapi")

from app.common.state_machine import assert_valid_transition


def test_new_statuses_can_move_into_progress():
    # Kanban "Дальше" from the Новые column must work for every new sub-status.
    for src in ("DETECTED", "PENDING_CONFIRMATION", "ACCEPTED", "TO_DO"):
        assert_valid_transition(src, "IN_PROGRESS")


def test_progress_review_done_chain():
    assert_valid_transition("IN_PROGRESS", "REVIEW")
    assert_valid_transition("REVIEW", "DONE")
    assert_valid_transition("IN_PROGRESS", "DONE")


def test_invalid_transition_rejected():
    with pytest.raises(ValueError):
        assert_valid_transition("DONE", "REVIEW")
    with pytest.raises(ValueError):
        assert_valid_transition("REJECTED", "IN_PROGRESS")
