"""Tests for CrossValidator as a standalone helper."""

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaokao_agent.data.cross_validator import CrossValidator


def _source(name, rank, score, year):
    return {"name": name, "rank": rank, "score": score, "year": year}


def test_validate_rank_bands():
    """Rank deviation is PASS under 5%, WARN from 5% to 10%, else REJECT."""
    validator = CrossValidator()
    api = _source("api", 100000, 520, 2025)

    ok, deviation, message = validator.validate_rank(
        _source("excel", 100000, 520, 2025), api,
    )
    assert (ok, deviation, message) == (
        True, 0.0, "PASS: excel(100000) vs api(100000) = 0.0%",
    )

    ok, deviation, message = validator.validate_rank(
        _source("excel", 104000, 520, 2025), api,
    )
    assert ok is True
    assert deviation == 0.04
    assert message == "PASS: excel(104000) vs api(100000) = 4.0%"

    ok, deviation, message = validator.validate_rank(
        _source("excel", 105000, 521, 2025), api,
    )
    assert ok is True
    assert deviation == 0.05
    assert message == "WARN: excel(105000) vs api(100000) = 5.0% (>5%)"

    ok, deviation, message = validator.validate_rank(
        _source("excel", 109000, 522, 2024), api,
    )
    assert ok is True
    assert deviation == 0.09
    assert message == "WARN: excel(109000) vs api(100000) = 9.0% (>5%)"

    ok, deviation, message = validator.validate_rank(
        _source("excel", 110000, 530, 2025), api,
    )
    assert ok is False
    assert deviation == 0.1
    assert message == "REJECT: excel(110000) vs api(100000) = 10.0% (>10%)"


def test_validate_rank_uses_the_second_source_as_baseline():
    """The same pair can warn or reject depending on which rank is source_b."""
    validator = CrossValidator()
    lower = _source("excel", 100000, 520, 2025)
    higher = _source("api", 110000, 518, 2025)

    ok, deviation, message = validator.validate_rank(lower, higher)
    assert ok is True
    assert deviation == abs(100000 - 110000) / 110000
    assert message.startswith("WARN")

    ok, deviation, message = validator.validate_rank(higher, lower)
    assert ok is False
    assert deviation == 0.1
    assert message.startswith("REJECT")


def test_validate_rank_missing_data():
    """A missing or zero rank is rejected instead of compared."""
    validator = CrossValidator()
    present = {"name": "api", "rank": 100000, "score": 520, "year": 2025}

    ok, deviation, message = validator.validate_rank(
        {"name": "excel", "score": 520, "year": 2025}, present,
    )
    assert ok is False
    assert deviation == 1.0
    assert message == "Missing rank data: excel=0, api=100000"

    ok, deviation, message = validator.validate_rank(
        {"name": "excel", "rank": 0, "score": 520, "year": 2025}, present,
    )
    assert (ok, deviation) == (False, 1.0)
    assert message == "Missing rank data: excel=0, api=100000"


def test_validate_score_bands():
    """Score gaps are PASS through 3, WARN through 8, otherwise REJECT."""
    validator = CrossValidator()

    assert validator.validate_score(
        _source("excel", 100000, 520, 2025),
        _source("api", 100000, 520, 2025),
    ) == (True, 0, "PASS: excel(520) vs api(520) = 0分")

    assert validator.validate_score(
        _source("excel", 100000, 520, 2025),
        _source("api", 101000, 523, 2024),
    ) == (True, 3, "PASS: excel(520) vs api(523) = 3分")

    assert validator.validate_score(
        _source("excel", 100000, 520, 2025),
        _source("api", 100000, 524, 2025),
    ) == (True, 4, "WARN: excel(520) vs api(524) = 4分 (>3分)")

    assert validator.validate_score(
        _source("excel", 100000, 520, 2025),
        _source("api", 100000, 528, 2025),
    ) == (True, 8, "WARN: excel(520) vs api(528) = 8分 (>3分)")

    assert validator.validate_score(
        _source("excel", 100000, 520, 2025),
        _source("api", 100000, 529, 2025),
    ) == (False, 9, "REJECT: excel(520) vs api(529) = 9分 (>8分)")


def test_validate_school_across_sources():
    """School checks compare rank pairs and keep the {name, rank, score, year} rows."""
    validator = CrossValidator()
    excel = _source("excel", 100000, 520, 2024)
    api = _source("api", 100000, 521, 2025)

    agreed = validator.validate_school([excel, api])
    assert agreed == {
        "valid": True,
        "used": [excel, api],
        "excluded": [],
        "warnings": [],
    }

    warned_api = _source("api", 106000, 524, 2025)
    warned = validator.validate_school([excel, warned_api])
    _, _, warn_message = validator.validate_rank(excel, warned_api)
    assert warn_message.startswith("WARN")
    assert warned == {
        "valid": True,
        "used": [excel, warned_api],
        "excluded": [],
        "warnings": [warn_message],
    }

    rejected_api = _source("api", 120000, 500, 2025)
    rejected = validator.validate_school([excel, rejected_api])
    _, _, reject_message = validator.validate_rank(excel, rejected_api)
    assert rejected == {
        "valid": False,
        "used": [],
        "excluded": [{"reason": reject_message, "source": rejected_api}],
        "warnings": [],
    }

    # Rank agreement keeps both rows. Score disagreement is reported only
    # by validate_score; validate_school does not compare scores.
    low = _source("excel", 100000, 500, 2025)
    high = _source("api", 100000, 530, 2025)
    assert validator.validate_score(low, high) == (
        False, 30, "REJECT: excel(500) vs api(530) = 30分 (>8分)",
    )
    score_split = validator.validate_school([low, high])
    assert score_split["valid"] is True
    assert score_split["used"] == [low, high]
    assert score_split["excluded"] == []
    assert score_split["warnings"] == []

    web = _source("web", 120000, 490, 2024)
    close_api = _source("api", 101000, 521, 2025)
    mixed = validator.validate_school([excel, close_api, web])
    assert mixed["valid"] is True
    assert mixed["used"] == [excel, close_api]
    assert mixed["warnings"] == []
    assert len(mixed["excluded"]) == 2
    assert all(item["source"] is web for item in mixed["excluded"])
    assert all(item["reason"].startswith("REJECT") for item in mixed["excluded"])

    assert validator.validate_school([]) == {
        "valid": False,
        "used": [],
        "excluded": [],
        "warnings": [],
    }
    assert validator.validate_school([excel]) == {
        "valid": False,
        "used": [],
        "excluded": [],
        "warnings": [],
    }


if __name__ == "__main__":
    test_validate_rank_bands()
    test_validate_rank_uses_the_second_source_as_baseline()
    test_validate_rank_missing_data()
    test_validate_score_bands()
    test_validate_school_across_sources()
    print("All cross-validator tests passed!")
