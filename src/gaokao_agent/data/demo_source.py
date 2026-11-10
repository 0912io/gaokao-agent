"""Demo data source — fictional schools for testing and demonstration.

Provides 5 fictional schools with complete metadata so the agent
pipeline runs end-to-end without any external data dependencies.
"""

from typing import List

from .demo_schools import DEMO_SCHOOLS as _DEMO_SCHOOLS
from .source import DataSource


class DemoDataSource(DataSource):
    """Built-in demo data source with fictional but realistic schools."""

    DEMO_SCHOOLS = _DEMO_SCHOOLS

    def get_schools(self, profile=None) -> List[dict]:
        """Return all demo schools (profile filtering optional)."""
        return list(self.DEMO_SCHOOLS)
