"""
Filename: MetaGPT-Ewan/MAT/__init__.py
Created Date: Friday, December 26th 2025
Author: Ewan Su
Description: Multi-Agent Trading (MAT) Framework - Core package initialization.
"""

from .schemas import (
    SignalIntensity,
    MarketEvent,
    FAReport,
    TAReport,
    SAReport,
    StrategyDecision,
    TradingState,
    InvestigationRequest,
    InvestigationReport
)
from .environment import InvestmentEnvironment
from .roles import BaseInvestmentAgent, AlphaStrategist, SentimentAnalyst
# Import action types (message types for pub-sub)
from .actions import (
    StartAnalysis,
    PublishFAReport,
    PublishTAReport,
    PublishSAReport,
    PublishStrategyDecision,
    RequestInvestigation,
    PublishInvestigationReport
)
# Import executable actions from actions directory
from .actions.search_deep_dive import SearchDeepDive
# Import configuration utilities
from .config_loader import MATConfig, get_config

__all__ = [
    # Enums
    "SignalIntensity",
    "MarketEvent",
    # Report Schemas
    "FAReport",
    "TAReport",
    "SAReport",
    "StrategyDecision",
    "TradingState",
    "InvestigationRequest",
    "InvestigationReport",
    # Core Framework
    "InvestmentEnvironment",
    "BaseInvestmentAgent",
    # Concrete Agents (Scheme C)
    "AlphaStrategist",
    "SentimentAnalyst",
    # Actions (Message Types)
    "StartAnalysis",
    "PublishFAReport",
    "PublishTAReport",
    "PublishSAReport",
    "PublishStrategyDecision",
    "RequestInvestigation",
    "PublishInvestigationReport",
    # Actions (Executable)
    "SearchDeepDive",
    # Configuration
    "MATConfig",
    "get_config",
]

__version__ = "0.1.0"

