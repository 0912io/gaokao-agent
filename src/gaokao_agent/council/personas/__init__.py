from .strategist import StrategistAgent
from .detective import DetectiveAgent
from .trend_analyst import TrendAnalystAgent
from .arbitrageur import ArbitrageurAgent
from .safety_auditor import SafetyAuditorAgent
from .verifier import VerifierAgent
from .quality_filter import QualityFilterAgent
from .industry_matcher import IndustryMatcherAgent
from .fallback import FallbackAgent
from .synthesizer import SynthesizerAgent

# Convenience: all agents in recommended council order
ALL_AGENTS = [
    StrategistAgent,
    DetectiveAgent,
    TrendAnalystAgent,
    ArbitrageurAgent,
    SafetyAuditorAgent,
    VerifierAgent,
    QualityFilterAgent,
    IndustryMatcherAgent,
    FallbackAgent,
    SynthesizerAgent,
]

__all__ = [
    "StrategistAgent", "DetectiveAgent", "TrendAnalystAgent",
    "ArbitrageurAgent", "SafetyAuditorAgent", "VerifierAgent",
    "QualityFilterAgent", "IndustryMatcherAgent",
    "FallbackAgent", "SynthesizerAgent", "ALL_AGENTS",
]
