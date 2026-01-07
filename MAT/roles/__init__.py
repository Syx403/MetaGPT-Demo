"""
Filename: MetaGPT-Ewan/MAT/roles/__init__.py
Created Date: Friday, December 26th 2025
Author: Ewan Su
Description: Package initialization for investment agent roles.
"""

from .base_agent import BaseInvestmentAgent
from .research_analyst import ResearchAnalyst
from .technical_analyst import TechnicalAnalyst
from .sentiment_analyst import SentimentAnalyst
from .alpha_strategist import AlphaStrategist

__all__ = [
    "BaseInvestmentAgent",
    "ResearchAnalyst",
    "TechnicalAnalyst",
    "SentimentAnalyst",
    "AlphaStrategist"
]

