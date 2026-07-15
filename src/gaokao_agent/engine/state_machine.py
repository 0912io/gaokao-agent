"""L1 State Machine — enforces mandatory execution gates for the pipeline.

States: INITIAL → CONSTRAINTS_COLLECTED → DATA_ACQUIRED →
        CROSS_VALIDATED → PLAN_GENERATED → OUTPUT_DELIVERED
"""

import json
from datetime import datetime
from typing import List, Tuple


VALID_STATES = [
    "INITIAL", "CONSTRAINTS_COLLECTED", "DATA_ACQUIRED",
    "CROSS_VALIDATED", "PLAN_GENERATED", "OUTPUT_DELIVERED"
]

VALID_TRANSITIONS = {
    "INITIAL": ["CONSTRAINTS_COLLECTED"],
    "CONSTRAINTS_COLLECTED": ["DATA_ACQUIRED"],
    "DATA_ACQUIRED": ["CROSS_VALIDATED", "DATA_ACQUIRED"],
    "CROSS_VALIDATED": ["PLAN_GENERATED", "DATA_ACQUIRED"],
    "PLAN_GENERATED": ["OUTPUT_DELIVERED", "PLAN_GENERATED"],
    "OUTPUT_DELIVERED": ["INITIAL", "CONSTRAINTS_COLLECTED"],
}


class StateMachine:
    """Tracks and validates pipeline state transitions."""

    def __init__(self):
        self.state = self._default_state()

    def _default_state(self):
        return {
            "schema_version": "1.0",
            "session_id": "",
            "current_phase": "INITIAL",
            "phase_history": [],
            "current_user": {
                "province": "", "score": 0, "rank": 0,
                "subject_track": "", "subjects": [], "gender": "",
                "constraints": {}
            },
            "four_elements": {
                "province_confirmed": False, "score_confirmed": False,
                "rank_confirmed": False, "track_confirmed": False
            },
            "execution_gates": {
                "memory_loaded": False, "mcp_called": False,
                "sop_finished": False, "citation_added": False,
                "websearch_count": 0, "webfetch_count": 0,
                "cross_validation_done": False,
                "data_freshness_checked": False
            },
            "last_recommendations": [],
            "created_at": "", "updated_at": ""
        }

    def current_phase(self) -> str:
        return self.state.get("current_phase", "INITIAL")

    def transition(self, to_state: str) -> Tuple[bool, str]:
        current = self.current_phase()
        if to_state not in VALID_STATES:
            return False, f"Invalid state: {to_state}"
        if to_state not in VALID_TRANSITIONS.get(current, []):
            return False, f"Illegal transition: {current} -> {to_state}"
        self.state["current_phase"] = to_state
        self.state["phase_history"].append({
            "from": current, "to": to_state,
            "timestamp": datetime.now().isoformat()
        })
        return True, f"{current} -> {to_state}"

    def check_four_elements(self) -> Tuple[bool, List[str]]:
        fe = self.state.get("four_elements", {})
        if fe.get("confirmed"):
            missing = [k for k in ["province", "score", "rank", "track"]
                       if not fe.get(k)]
        else:
            missing = [k for k in ["province_confirmed", "score_confirmed",
                                   "rank_confirmed", "track_confirmed"]
                       if not fe.get(k)]
        return (len(missing) == 0, missing)

    def set_four_elements(self, province, score, rank, track,
                          subjects=None, gender=""):
        self.state["current_user"].update({
            "province": province, "score": score,
            "rank": rank, "subject_track": track
        })
        if subjects:
            self.state["current_user"]["subjects"] = subjects
        if gender:
            self.state["current_user"]["gender"] = gender
        self.state["four_elements"] = {
            "province_confirmed": True, "score_confirmed": True,
            "rank_confirmed": True, "track_confirmed": True
        }
        self.transition("CONSTRAINTS_COLLECTED")

    def set_gate(self, gate_name: str, value: bool):
        if gate_name in self.state["execution_gates"]:
            self.state["execution_gates"][gate_name] = value

    def check_gates(self) -> Tuple[bool, List[str], List[str]]:
        gates = self.state.get("execution_gates", {})
        failed = [g for g in ["memory_loaded", "mcp_called", "citation_added"]
                  if not gates.get(g)]
        warnings = [g for g in ["data_freshness_checked"]
                    if not gates.get(g)]
        return (len(failed) == 0, failed, warnings)

    def check_web_minimums(self) -> Tuple[bool, dict]:
        gates = self.state.get("execution_gates", {})
        ws = gates.get("websearch_count", 0)
        wf = gates.get("webfetch_count", 0)
        total = ws + wf
        stats = {"websearch_count": ws, "webfetch_count": wf, "total": total,
                 "websearch_ok": ws >= 2, "total_ok": total >= 4}
        return (stats["websearch_ok"] and stats["total_ok"], stats)

    def check_all(self) -> Tuple[bool, List[str]]:
        """Run all checks. Returns (passed, errors)."""
        errors = []
        four_ok, missing = self.check_four_elements()
        gates_ok, failed, _ = self.check_gates()
        web_ok, stats = self.check_web_minimums()

        if not four_ok:
            errors.append(f"four_elements_missing:{missing}")
        if not gates_ok:
            errors.append(f"gates_failed:{failed}")
        if not web_ok:
            errors.append(f"web_insufficient:{stats}")

        return (len(errors) == 0, errors)

    def to_dict(self):
        return self.state
