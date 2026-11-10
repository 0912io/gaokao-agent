"""
Gaokao Agent — Multi-Agent Collaborative Decision Framework for College Admission.

Features:
    - 10 specialized agent personas with weighted voting and veto power
    - 6-stage execution pipeline with state machine enforcement
    - Pluggable data source for school records
    - CLI and Python API interfaces

Example:
    >>> from gaokao_agent import GaokaoAgent
    >>> from gaokao_agent.config import Profile
    >>>
    >>> agent = GaokaoAgent()
    >>> result = agent.run(Profile(
    ...     province="XX", score=500, rank=80000,
    ...     subjects=["物理", "化学", "生物"]
    ... ))
    >>> print(result.recommendations)
"""

from ._version import __version__
from .config import Profile, Settings
from .engine.pipeline import Pipeline

__all__ = ["GaokaoAgent", "Profile", "Settings", "Pipeline", "__version__"]


class GaokaoAgent:
    """Main entry point for the Gaokao Agent framework.

    Orchestrates the council of expert agents, data pipeline, and
    state machine to produce college admission recommendations.
    """

    def __init__(self, settings=None):
        self.settings = settings or Settings()
        self.pipeline = Pipeline(self.settings)
        self._data_source = None

    @property
    def data_source(self):
        if self._data_source is None:
            from .data.demo_source import DemoDataSource
            self._data_source = DemoDataSource()
        return self._data_source

    @data_source.setter
    def data_source(self, source):
        self._data_source = source

    @property
    def council(self):
        return self.pipeline.council

    def run(self, profile=None, **kwargs):
        """Run the full agent pipeline and return recommendations.

        Args:
            profile: A Profile object with student information.
            **kwargs: If profile is None, kwargs are passed to Profile().

        Returns:
            A PipelineResult with recommendations, risks, and metadata.
        """
        if profile is None:
            profile = Profile(**kwargs)
        return self.pipeline.run(profile, self.data_source)
