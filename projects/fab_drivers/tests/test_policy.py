"""The command policy is the safety gate. These tests hold it shut."""

import pytest

from fab_drivers.core.policy import CommandPolicy, CommandRefused


def make_policy():
    return CommandPolicy(
        "test device",
        allowed=["J", "K", "B"],
        banned={"g": "Locks other serial ports out, including the tool's own."},
    )


def test_an_allowed_command_passes_through():
    policy = make_policy()
    assert policy.check("J") == "J"


def test_a_banned_command_is_refused_with_its_reason():
    policy = make_policy()
    with pytest.raises(CommandRefused) as caught:
        policy.check("g")
    # The reason matters as much as the refusal. The next person needs to know
    # why, not just that it did not work.
    assert "Locks other serial ports out" in str(caught.value)


def test_an_unlisted_command_is_refused_even_though_nobody_banned_it():
    # This is the important one. A control command nobody thought to ban is
    # still refused, because the allowed list is the whole gate.
    policy = make_policy()
    with pytest.raises(CommandRefused):
        policy.check("A1")


def test_a_command_that_is_both_allowed_and_banned_is_caught_when_built():
    # A driver with a contradictory list is broken. Say so at once, not on the
    # night someone sends the command.
    with pytest.raises(ValueError) as caught:
        CommandPolicy("test", allowed=["J"], banned={"J": "reason"})
    assert "both allowed and banned" in str(caught.value)


def test_is_allowed_answers_without_raising():
    policy = make_policy()
    assert policy.is_allowed("J") is True
    assert policy.is_allowed("g") is False
    assert policy.is_allowed("A1") is False
