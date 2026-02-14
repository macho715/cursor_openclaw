import pytest

from src.queue.state_machine import (
    QueueState,
    TransitionError,
    validate_transition,
    ALLOWED_TRANSITIONS,
)


def test_allowed_transitions_only():
    # all allowed transitions should pass
    for src, dsts in ALLOWED_TRANSITIONS.items():
        for dst in dsts:
            validate_transition(src, dst)

    # all disallowed transitions should fail
    all_states = list(QueueState)
    for src in all_states:
        for dst in all_states:
            if dst in ALLOWED_TRANSITIONS.get(src, set()):
                continue
            if src == dst:
                # self-transition is disallowed everywhere
                with pytest.raises(TransitionError):
                    validate_transition(src, dst)
            else:
                with pytest.raises(TransitionError):
                    validate_transition(src, dst)
