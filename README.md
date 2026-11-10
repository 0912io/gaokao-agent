# Gaokao Agent

**Multi-Agent Collaborative Decision Framework for College Admission**

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A council of 10 specialized AI agents analyzes college admission options using weighted voting, veto power, and multi-source data cross-validation.

## Architecture

```
User Profile (score/rank/subjects)
       │
   ┌───▼──── PreCheck ────┐
   │  4-element validation │
   └───┬──────────────────┘
       │
   ┌───▼──── State Machine ────┐
   │  6-stage enforcement       │
   └───┬───────────────────────┘
       │
   ┌───▼──── Council ──────────┐
   │  10 agents × parallel     │
   │  Weighted voting + veto    │
   └───┬───────────────────────┘
       │
   ┌───▼──── PostCheck ────────┐
   │  Source/yr/safety checks   │
   └───┬───────────────────────┘
       │
   ┌───▼──── Output ───────────┐
   │  Reach / Match / Safety    │
   │  + Risk warnings           │
   └────────────────────────────┘
```

## Quick Start

```bash
# Install
pip install -e .

# Run demo (uses built-in fictional data, no setup needed)
gaokao-agent demo
```

## Usage

### CLI

```bash
# Demo mode
gaokao-agent demo

# Full mode
gaokao-agent run --province XX --score 500 --rank 80000 --subjects 物理,化学,生物

# List all agents
gaokao-agent list-agents
```

### Python API

```python
from gaokao_agent import GaokaoAgent
from gaokao_agent.config import Profile

agent = GaokaoAgent()
result = agent.run(Profile(
    province="XX", score=500, rank=80000,
    subjects=["物理", "化学", "生物"],
))

for rec in result.recommendations:
    print(f"[{rec['consensus']}] {rec['school_id']}")
```

## Council Agents

| Agent | Role | Weight | Veto |
|-------|------|:------:|:----:|
| **strategist** | Elite university path specialist | 4.5 | |
| **detective** | Information asymmetry detector | 4.5 | |
| **arbitrageur** | Game theory / competitor blind spots | 4.0 | |
| **trend_analyst** | New institution & enrollment tracker | 3.0 | |
| **industry_matcher** | City-industry fit analysis | 2.0 | |
| **safety_auditor** | Safety & risk auditor | 2.0 | ✅ |
| **verifier** | Rank data & charter checker | 2.0 | ✅ |
| **quality_filter** | Major quality & 2030 outlook | 2.0 | ✅ |
| **fallback** | Worst-case scenario planner | 1.0 | |
| **synthesizer** | Multi-perspective summary | 1.0 | |

### Voting Rules

- **Weighted voting**: Output from high-weight agents counts more
- **Veto override**: Any veto agent rejecting a school → `high_risk`
- **Confidence tiers**: `strategy` > `trend` > `data` (discounts applied based on output type)

## Customization

### Add a custom agent

```python
from gaokao_agent.council.base import BaseAgent

class MyAgent(BaseAgent):
    name = "my_analyst"
    weight = 3.0

    def analyze(self, school, profile):
        return {
            "verdict": "match",
            "confidence": 0.8,
            "reasons": ["Custom analysis result."],
            "warnings": [],
        }

agent = GaokaoAgent()
agent.council.add(MyAgent())
```

### Connect a custom data source

```python
from gaokao_agent.data.source import DataSource

class MyDataSource(DataSource):
    def get_schools(self, profile):
        return [{"id": "001", "name": "我的大学", ...}]

agent = GaokaoAgent()
agent.data_source = MyDataSource()
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Project Structure

```
gaokao-agent/
├── src/gaokao_agent/
│   ├── __init__.py      # Public API (GaokaoAgent)
│   ├── _version.py      # Package version
│   ├── cli.py           # Command-line interface
│   ├── config.py        # Profile and Settings
│   ├── engine/          # Pipeline + state machine + policy engine
│   ├── council/         # Agent base + council + 10 personas
│   ├── data/            # Data source interface, demo schools, cross-validator
│   └── guards/          # Pre/post execution validators
├── examples/            # Usage examples
├── tests/               # pytest suite
├── pyproject.toml
├── README.md
└── LICENSE
```

## License

CC BY-NC 4.0 — Free for non-commercial use with attribution.

**You may:**
- Share, copy, and redistribute
- Adapt, remix, and build upon

**You must:**
- Give appropriate credit
- NOT use for commercial purposes without permission

For commercial licensing: contact the author.
