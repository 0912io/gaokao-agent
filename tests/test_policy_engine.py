"""Tests for PolicyEngine as a standalone helper."""

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaokao_agent.engine.policy_engine import PolicyEngine


COMPLIANT_TEXT = "2024年某大学录取分数线520分，来源 https://example.edu/admit"


def _web_ok(engine, websearch_count, webfetch_count):
    """Map search counters onto the flag validate_response accepts."""
    rules = engine.rules
    return (
        websearch_count >= rules["min_websearch"]
        and webfetch_count >= rules["min_webfetch"]
    )


def test_route_free_text_queries():
    """Free-text queries match the first route that contains a keyword."""
    engine = PolicyEngine()

    full = engine.route("陕西考生怎么填高考志愿")
    assert full["id"] == "gaokao-full"
    assert full["action"] == "full_pipeline"
    assert "高考" in full["keywords"]

    jianlou = engine.route("冷门专业还有没有捡漏机会")
    assert jianlou["id"] == "gaokao-jianlou"
    assert jianlou["action"] == "jianlou_pipeline"

    info = engine.route("今年的招生计划公布了吗")
    assert info["id"] == "gaokao-info"
    assert info["action"] == "info_only"

    assert engine.route("只说冲稳保")["id"] == "gaokao-full"
    assert engine.route("只说压线")["id"] == "gaokao-jianlou"
    assert engine.route("只说一分一段")["id"] == "gaokao-info"

    assert engine.route("今天午饭吃什么") == {"id": "fallback", "action": None}
    assert engine.route("") == {"id": "fallback", "action": None}


def test_route_checks_earlier_routes_first():
    """A query that hits two routes keeps the earlier one."""
    engine = PolicyEngine()
    routed = engine.route("高考招生计划")
    assert routed["id"] == "gaokao-full"
    assert routed["action"] == "full_pipeline"


def test_custom_routes_honor_require_all():
    """Injected routes skip empty keyword lists and honor require_all."""
    engine = PolicyEngine(routes={
        "blank": {"keywords": [], "require_all": False, "action": "blank"},
        "both": {
            "keywords": ["高考", "位次"],
            "require_all": True,
            "action": "both",
        },
        "either": {
            "keywords": ["高考", "天气"],
            "require_all": False,
            "action": "either",
        },
    })
    assert engine.route("高考位次查询")["id"] == "both"
    assert engine.route("只谈高考")["id"] == "either"
    assert engine.route("今天天气不错")["id"] == "either"
    assert engine.route("无关的句子") == {"id": "fallback", "action": None}


def test_is_gaokao_query():
    """A routed query is in scope; fallback text is not."""
    engine = PolicyEngine()
    assert engine.is_gaokao_query("想问录取分数线") is True
    assert engine.is_gaokao_query("冷门") is True
    assert engine.is_gaokao_query("批次") is True
    assert engine.is_gaokao_query("hello") is False
    assert engine.is_gaokao_query("") is False


def test_validate_response_year_source_url_and_search_counters():
    """Check year labels, source URLs, and the search-counter minimums."""
    engine = PolicyEngine()
    assert engine.rules["min_websearch"] == 2
    assert engine.rules["min_webfetch"] == 2

    ok, violations = engine.validate_response(
        COMPLIANT_TEXT, True, True, _web_ok(engine, 2, 2),
    )
    assert ok is True
    assert violations == []

    ok, violations = engine.validate_response(
        COMPLIANT_TEXT, True, True, _web_ok(engine, 1, 2),
    )
    assert ok is False
    assert violations == ["web_search_insufficient"]

    ok, violations = engine.validate_response(
        COMPLIANT_TEXT, True, True, _web_ok(engine, 2, 1),
    )
    assert violations == ["web_search_insufficient"]

    ok, violations = engine.validate_response(
        "某大学录取分数线520分，来源 https://example.edu/admit",
        True, True, True,
    )
    assert violations == ["year_not_labeled"]

    ok, violations = engine.validate_response(
        "2024年某大学录取分数线520分",
        True, True, True,
    )
    assert violations == ["source_url_missing"]

    ok, violations = engine.validate_response(
        "2024年学院投档位次见 http://example.edu/plan ，分数线为500分",
        True, True, True,
    )
    assert ok is True
    assert violations == []

    ok, violations = engine.validate_response(
        "2024 大学录取520分 www.example.edu",
        True, True, True,
    )
    assert violations == ["year_not_labeled", "source_url_missing"]

    ok, violations = engine.validate_response(
        "这段文字没有院校和分数", True, True, True,
    )
    assert ok is True
    assert violations == []

    ok, violations = engine.validate_response(
        "2024年记录为520分", True, True, True,
    )
    assert ok is True

    ok, violations = engine.validate_response(
        "大学简介见 https://example.edu/about", True, True, True,
    )
    assert ok is True

    ok, violations = engine.validate_response(
        "某大学录取520分", False, False, False,
    )
    assert ok is False
    assert violations == [
        "four_elements_missing",
        "exec_gates_failed",
        "web_search_insufficient",
        "year_not_labeled",
        "source_url_missing",
    ]


if __name__ == "__main__":
    test_route_free_text_queries()
    test_route_checks_earlier_routes_first()
    test_custom_routes_honor_require_all()
    test_is_gaokao_query()
    test_validate_response_year_source_url_and_search_counters()
    print("All policy engine tests passed!")
