"""Abstract data source interface."""

from abc import ABC, abstractmethod
from typing import List


class DataSource(ABC):
    """Abstract interface for gaokao data providers.

    Implement this to connect any data source (Excel, API, database).
    """

    @abstractmethod
    def get_schools(self, profile) -> List[dict]:
        """Return matching schools for a student profile.

        Args:
            profile: Profile with province/score/rank/subjects.

        Returns:
            List of school dicts, each with at minimum:
            {
                "id": str,
                "name": str,
                "min_rank": int (or 0 if unknown),
                "majors": List[str],
                "subjects_required": str,
                "label": str (985/211/双一流/...),
                "city": str,
                "city_level": int (1-6),
                "type": str,
                "tuition": int,
                "cleanliness": float (0.0-1.0),
                ... (additional optional fields)
            }
        """
        ...
