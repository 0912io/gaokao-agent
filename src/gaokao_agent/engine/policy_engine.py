"""L1 Policy Engine — keyword-based routing and response validation."""

import re


class PolicyEngine:
    """Routes queries to agents and validates response compliance."""

    def __init__(self, routes: dict = None, rules: dict = None):
        self.routes = routes or self._default_routes()
        self.rules = rules or self._default_rules()

    @staticmethod
    def _default_routes():
        return {
            "gaokao-full": {
                "keywords": ["高考", "志愿", "择校", "录取", "分数线", "冲稳保"],
                "require_all": False,
                "action": "full_pipeline"
            },
            "gaokao-jianlou": {
                "keywords": ["捡漏", "低分", "征集志愿", "压线", "冷门"],
                "require_all": False,
                "action": "jianlou_pipeline"
            },
            "gaokao-info": {
                "keywords": ["批次", "一分一段", "招生计划"],
                "require_all": False,
                "action": "info_only"
            },
        }

    @staticmethod
    def _default_rules():
        return {
            "min_websearch": 2,
            "min_webfetch": 2,
            "year_pattern": re.compile(r"20\d{2}年"),
            "url_pattern": re.compile(r"https?://"),
            "gaokao_pattern": re.compile(
                r"大学|学院|录取|投档|分数线|位次|批次|志愿"
            ),
            "score_pattern": re.compile(r"\d{3}分"),
        }

    def route(self, query: str) -> dict:
        """Route a query to the appropriate pipeline action."""
        for route_id, config in self.routes.items():
            keywords = config.get("keywords", [])
            require_all = config.get("require_all", False)
            if not keywords:
                continue
            matches = [kw for kw in keywords if kw in query]
            if require_all and len(matches) == len(keywords):
                return {"id": route_id, **config}
            if not require_all and len(matches) > 0:
                return {"id": route_id, **config}
        return {"id": "fallback", "action": None}

    def is_gaokao_query(self, text: str) -> bool:
        """Check if text contains gaokao-related keywords."""
        route = self.route(text)
        return route["id"] not in (None, "fallback")

    def validate_response(
        self, text: str, four_ok: bool, gates_ok: bool, web_ok: bool
    ) -> tuple:
        """Validate output compliance. Returns (valid, violations)."""
        violations = []
        rules = self.rules

        if not four_ok:
            violations.append("four_elements_missing")
        if not gates_ok:
            violations.append("exec_gates_failed")
        if not web_ok:
            violations.append("web_search_insufficient")

        # Check year annotation when scores are present
        if rules["score_pattern"].search(text):
            if not rules["year_pattern"].search(text):
                violations.append("year_not_labeled")

        # Check URL presence for recommendations
        if rules["gaokao_pattern"].search(text):
            if not rules["url_pattern"].search(text):
                violations.append("source_url_missing")

        return (len(violations) == 0, violations)
