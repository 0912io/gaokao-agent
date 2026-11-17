"""Tests for StateMachine transitions, four elements, and web floors."""

from gaokao_agent.engine.state_machine import (
    VALID_STATES,
    VALID_TRANSITIONS,
    StateMachine,
)


# The legal graph the pipeline and standalone helpers share.
LEGAL = {
    "INITIAL": ["CONSTRAINTS_COLLECTED"],
    "CONSTRAINTS_COLLECTED": ["DATA_ACQUIRED"],
    "DATA_ACQUIRED": ["DELIBERATED", "DATA_ACQUIRED"],
    "DELIBERATED": ["PLAN_GENERATED", "DATA_ACQUIRED"],
    "PLAN_GENERATED": ["OUTPUT_DELIVERED", "PLAN_GENERATED"],
    "OUTPUT_DELIVERED": ["INITIAL", "CONSTRAINTS_COLLECTED"],
}

_PATH = {
    "INITIAL": [],
    "CONSTRAINTS_COLLECTED": ["CONSTRAINTS_COLLECTED"],
    "DATA_ACQUIRED": ["CONSTRAINTS_COLLECTED", "DATA_ACQUIRED"],
    "DELIBERATED": ["CONSTRAINTS_COLLECTED", "DATA_ACQUIRED", "DELIBERATED"],
    "PLAN_GENERATED": [
        "CONSTRAINTS_COLLECTED", "DATA_ACQUIRED", "DELIBERATED",
        "PLAN_GENERATED",
    ],
    "OUTPUT_DELIVERED": [
        "CONSTRAINTS_COLLECTED", "DATA_ACQUIRED", "DELIBERATED",
        "PLAN_GENERATED", "OUTPUT_DELIVERED",
    ],
}

DEFAULT_GATES = {
    "memory_loaded": False,
    "mcp_called": False,
    "sop_finished": False,
    "citation_added": False,
    "websearch_count": 0,
    "webfetch_count": 0,
    "cross_validation_done": False,
    "data_freshness_checked": False,
}

FOUR_FLAGS = [
    "province_confirmed", "score_confirmed",
    "rank_confirmed", "track_confirmed",
]


def _at(phase):
    """Walk the forward path until ``phase``."""
    machine = StateMachine()
    for step in _PATH[phase]:
        ok, _message = machine.transition(step)
        assert ok is True
    assert machine.current_phase() == phase
    return machine


def test_transition_table_is_the_six_phase_graph():
    """Published states and edges stay the six-phase graph."""
    assert list(VALID_STATES) == list(LEGAL)
    assert VALID_TRANSITIONS == LEGAL


def test_legal_transitions_advance_and_record_history():
    """Every allowed edge moves the phase and appends one history step."""
    for start, targets in LEGAL.items():
        for target in targets:
            machine = _at(start)
            before = len(machine.state["phase_history"])
            ok, message = machine.transition(target)
            assert ok is True
            assert message == f"{start} -> {target}"
            assert machine.current_phase() == target
            assert len(machine.state["phase_history"]) == before + 1
            step = machine.state["phase_history"][-1]
            assert step["from"] == start
            assert step["to"] == target
            assert isinstance(step["timestamp"], str) and step["timestamp"]


def test_illegal_transitions_leave_phase_and_history_unchanged():
    """A disallowed edge, including an unknown name, does not move."""
    for start, targets in LEGAL.items():
        machine = _at(start)
        history = list(machine.state["phase_history"])
        for target in VALID_STATES:
            if target in targets:
                continue
            ok, message = machine.transition(target)
            assert ok is False
            assert message == f"Illegal transition: {start} -> {target}"
            assert machine.current_phase() == start
            assert machine.state["phase_history"] == history

        ok, message = machine.transition("NO_SUCH_PHASE")
        assert ok is False
        assert message == "Invalid state: NO_SUCH_PHASE"
        assert machine.current_phase() == start
        assert machine.state["phase_history"] == history


def test_set_four_elements_confirms_all_four_flags():
    """set_four_elements fills the user record and the four confirmed flags."""
    machine = StateMachine()
    ok, missing = machine.check_four_elements()
    assert ok is False
    assert missing == FOUR_FLAGS

    machine.set_four_elements(
        "陕西", 520, 85000, "physics",
        subjects=["物理", "化学", "生物"],
        gender="男",
    )
    ok, missing = machine.check_four_elements()
    assert ok is True
    assert missing == []
    assert machine.current_phase() == "CONSTRAINTS_COLLECTED"
    user = machine.state["current_user"]
    assert user["province"] == "陕西"
    assert user["score"] == 520
    assert user["rank"] == 85000
    assert user["subject_track"] == "physics"
    assert user["subjects"] == ["物理", "化学", "生物"]
    assert user["gender"] == "男"

    blank = StateMachine()
    blank.set_four_elements("陕西", 520, 85000, "physics")
    assert blank.state["current_user"]["subjects"] == []
    assert blank.state["current_user"]["gender"] == ""
    assert blank.check_four_elements() == (True, [])


def test_check_four_elements_reads_only_the_confirmed_flags():
    """A filled user record does not count until the four flags are set."""
    machine = StateMachine()
    machine.state["current_user"].update({
        "province": "陕西",
        "score": 520,
        "rank": 85000,
        "subject_track": "physics",
        "subjects": ["物理"],
    })
    ok, missing = machine.check_four_elements()
    assert ok is False
    assert missing == FOUR_FLAGS

    machine.state["four_elements"]["province_confirmed"] = True
    machine.state["four_elements"]["score_confirmed"] = True
    ok, missing = machine.check_four_elements()
    assert ok is False
    assert missing == ["rank_confirmed", "track_confirmed"]


def test_default_execution_gates_stay_false():
    """Transitions and set_four_elements leave every default gate untouched."""
    machine = StateMachine()
    assert machine.state["execution_gates"] == DEFAULT_GATES

    machine.set_four_elements(
        "陕西", 520, 85000, "physics", subjects=["物理"],
    )
    assert machine.state["execution_gates"] == DEFAULT_GATES

    for phase in (
        "DATA_ACQUIRED", "DELIBERATED", "PLAN_GENERATED", "OUTPUT_DELIVERED",
    ):
        ok, _message = machine.transition(phase)
        assert ok is True
        assert machine.state["execution_gates"] == DEFAULT_GATES

    passed, failed, warnings = machine.check_gates()
    assert passed is False
    assert failed == ["memory_loaded", "mcp_called", "citation_added"]
    assert warnings == ["data_freshness_checked"]


def test_check_web_minimums_floors():
    """Search count needs at least 2, and search plus fetch needs at least 4."""
    machine = StateMachine()
    ok, stats = machine.check_web_minimums()
    assert ok is False
    assert stats == {
        "websearch_count": 0,
        "webfetch_count": 0,
        "total": 0,
        "websearch_ok": False,
        "total_ok": False,
    }

    cases = [
        # (websearch, webfetch, passed, websearch_ok, total_ok)
        (1, 3, False, False, True),
        (2, 1, False, True, False),
        (2, 0, False, True, False),
        (2, 2, True, True, True),
        (3, 1, True, True, True),
        (4, 0, True, True, True),
    ]
    for websearch, webfetch, passed, search_ok, total_ok in cases:
        gates = machine.state["execution_gates"]
        gates["websearch_count"] = websearch
        gates["webfetch_count"] = webfetch
        ok, stats = machine.check_web_minimums()
        assert ok is passed
        assert stats["websearch_count"] == websearch
        assert stats["webfetch_count"] == webfetch
        assert stats["total"] == websearch + webfetch
        assert stats["websearch_ok"] is search_ok
        assert stats["total_ok"] is total_ok
        assert gates["memory_loaded"] is False
        assert gates["mcp_called"] is False
        assert gates["citation_added"] is False


if __name__ == "__main__":
    test_transition_table_is_the_six_phase_graph()
    test_legal_transitions_advance_and_record_history()
    test_illegal_transitions_leave_phase_and_history_unchanged()
    test_set_four_elements_confirms_all_four_flags()
    test_check_four_elements_reads_only_the_confirmed_flags()
    test_default_execution_gates_stay_false()
    test_check_web_minimums_floors()
    print("All state machine tests passed!")
