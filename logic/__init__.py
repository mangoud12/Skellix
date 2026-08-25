"""
logic/__init__.py

Business-logic layer for Skillix.
Exposes the three main logic modules:

    from logic.scoring import compute_assessment_score
    from logic.gaps    import identify_skill_gaps
    from logic.roadmap import generate_roadmap
"""

from .scoring import compute_assessment_score
from .gaps import identify_skill_gaps
from .roadmap import generate_roadmap

__all__ = [
    "compute_assessment_score",
    "identify_skill_gaps",
    "generate_roadmap",
]
