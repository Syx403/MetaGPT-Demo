from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- 1. Signal & Event Enums ---

class SignalIntensity(Enum):
    """Standardized signals for trading decisions."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

class MarketEvent(Enum):
    """Categories of market-moving events."""
    EARNINGS_CALL = "EARNINGS_CALL"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"
    REGULATORY_ACTION = "REGULATORY_ACTION"
    ANALYST_UPGRADE = "ANALYST_UPGRADE"
    MACRO_ECONOMIC = "MACRO_ECONOMIC"
    NONE = "NONE"

# --- 2. Agent Output Protocols ---

class FinancialMetric(BaseModel):
    """
    Sub-model for evidence-based financial metrics with full traceability.

    Supports "Data + Context + Source" paradigm where every metric includes:
    - The extracted value (or DATA_GAP indicator)
    - Qualitative analysis with BECAUSE-THEN causal logic
    - Full Markdown-cleaned text of the source chunk for manual verification
    - Clickable RAGFlow preview URL for jumping to exact PDF page
    - Metadata tracking page numbers and relevance scores
    """
    value: Optional[str] = Field(
        None,
        description="Extracted metric value (e.g., '33% YoY', '$100B', 'Increased by 15%'). Use 'DATA_GAP' if data is unavailable."
    )
    analysis: str = Field(
        default="No analysis available",
        description="Qualitative causal explanation using BECAUSE-THEN logic. Must explain WHY the metric changed and WHAT impact it had. Example: 'Revenue grew 33% BECAUSE iPhone sales surged post-COVID recovery, WHICH THEN drove record quarterly performance despite supply chain headwinds.'"
    )
    evidence_md: str = Field(
        default="No evidence available",
        description="The full Markdown-cleaned text of the Top 1 retrieved chunk (HTML tables converted to Markdown). Enables manual verification of the LLM's extraction."
    )
    source_link: str = Field(
        default="No source link available",
        description="Direct reference to source: [Document Name] | [Chunk ID]. Enables jumping to exact PDF location."
    )
    source_url: str = Field(
        default="No source URL available",
        description="Clickable RAGFlow preview URL to jump directly to the chunk's PDF page. Format: http://{base_ip}/chunk/parsed/chunks?id={dataset_id}&doc_id={doc_id}&page=1"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata tracking page_num, relevance_score, and other chunk attributes for audit purposes."
    )

class FAReport(BaseModel):
    """
    Protocol for Research Analyst (RA) - Financial Auditor Module.

    This schema provides evidence-based fundamental analysis with ZERO LLM-generated
    numeric signals. All analysis is descriptive with full source traceability.
    RA acts as a "Financial Auditor" providing expert evidence, not investment signals.
    """
    ticker: str

    # Core Financial Performance Metrics (Evidence-Based)
    revenue_performance: FinancialMetric = Field(
        default_factory=FinancialMetric,
        description="Revenue analysis with YoY growth, segment drivers, and causal explanation"
    )

    profitability_audit: FinancialMetric = Field(
        default_factory=FinancialMetric,
        description="Profitability metrics (gross margin, operating margin, net income) with trend analysis and causal reasoning"
    )

    cash_flow_stability: FinancialMetric = Field(
        default_factory=FinancialMetric,
        description="Free cash flow and cash generation analysis with sustainability assessment"
    )

    # Qualitative Evidence Fields
    management_guidance_audit: str = Field(
        default="No guidance analysis available",
        description="Qualitative audit of management guidance, forward outlook, and strategic commentary. Must identify tone (optimistic/cautious/mixed) with specific evidence from earnings calls or filings."
    )

    key_risks_evidence: List[str] = Field(
        default_factory=list,
        description="Top 3-5 risk factors extracted from filings/earnings with specific evidence. Each risk should include: (1) Risk description, (2) Potential impact, (3) Source reference."
    )

    # Note: source_citations removed - source integrity now handled within each FinancialMetric
    # via evidence_md, source_link, source_url, and metadata fields

class TAReport(BaseModel):
    """
    Protocol for Technical Analyst (TA) - Pure Evidence-Based Module.

    This schema captures multi-period technical structure with ZERO LLM-generated
    numeric signals. All numbers are API-derived; all analysis is descriptive.
    TA provides structural evidence about trend alignment across multiple timeframes.
    """
    ticker: str

    # Core technical metrics - API-derived only
    rsi_14: Optional[float] = Field(50.0, description="Relative Strength Index over 14 periods (yfinance)")
    bb_lower_touch: bool = Field(default=False, description="Whether price touched/broke the lower Bollinger Band")
    volatility_atr: Optional[float] = Field(0.0, description="Average True Range for volatility measurement (yfinance)")

    # Multi-Period Moving Average Distances - API-derived only
    price_to_ma20_dist: Optional[float] = Field(0.0, description="Distance percentage from 20-day MA (short-term trend)")
    price_to_ma50_dist: Optional[float] = Field(0.0, description="Distance percentage from 50-day MA (medium-term trend)")
    price_to_ma200_dist: Optional[float] = Field(0.0, description="Distance percentage from 200-day MA (long-term trend)")

    # Pure Descriptive Evidence - NO numeric scores
    market_regime: str = Field(
        default="Neutral Consolidation",
        description="Long-form structural description analyzing interplay between short (MA20), medium (MA50), and long-term (MA200) trends. Must identify mean reversion risks when price significantly deviates from MAs."
    )

    indicator_tension_analysis: str = Field(
        default="No tension analysis available",
        description="Qualitative analysis of conflicts/alignment between momentum (RSI/BB) and multi-period trend structure (MA20/MA50/MA200)"
    )

    dead_cat_vs_value: str = Field(
        default="Insufficient data for categorization",
        description="Explicit categorization as 'Dead Cat Bounce Risk' or 'Value Entry Opportunity' with multi-period trend reasoning"
    )

    pivot_zones: Dict[str, float] = Field(
        default_factory=dict,
        description="Critical support/resistance levels from API data (e.g., {'ma200_level': 149.0, 'ma50_level': 135.0, 'local_support': 125.0})"
    )

class SAReport(BaseModel):
    """
    Protocol for Sentiment Analyst (SA) - Pure Descriptive Evidence Module (Basic Mode).

    This schema captures qualitative causal narratives with ZERO LLM-generated numeric
    sentiment scores. All analysis is descriptive and anchored in news search results.
    SA provides deep causal chain analysis and structural evidence about market expectations.
    """
    ticker: str

    # Core descriptive fields
    impactful_events: List[MarketEvent] = Field(default_factory=list, description="List of detected major market events")
    top_keywords: List[str] = Field(default_factory=list, description="Key terms extracted from news search")
    news_summary: str = Field(default="No news summary available", description="Narrative summary of news landscape")

    # Pure Qualitative Evidence - NO numeric scores
    qualitative_sentiment_assessment: str = Field(
        default="No sentiment assessment available",
        description="Descriptive assessment of overall market sentiment toward the stock based on news tone, without numeric scoring"
    )

    sentiment_matrix: Dict[str, str] = Field(
        default_factory=dict,
        description="Qualitative audits for each dimension (e.g., {'Product_Demand': 'Strong iPhone sales momentum...', 'Macro_Environment': 'Headwinds from inflation...', 'Management_Confidence': 'Cautious guidance...', 'Competitive_Position': 'Market share gains in...'})"
    )

    causal_narrative: str = Field(
        default="No causal analysis available",
        description="Synthesized narrative using explicit BECAUSE-THEN logic connecting segment drivers to performance causally"
    )

    expectation_gap: str = Field(
        default="No expectation analysis available",
        description="Qualitative analysis of 'Actual Performance vs. Market Expectations' - describes beats, misses, or inline results with market reaction context"
    )

    paradoxes_or_tensions: str = Field(
        default="None identified",
        description="Anomalies like 'Good News, Price Drop' or 'Revenue Beat, Weak Guidance' with causal explanation of the contradiction"
    )

# --- 3. Final Strategy & Decision ---

class StrategyDecision(BaseModel):
    """Protocol for Alpha Strategist (AS) final output."""
    ticker: str
    final_action: SignalIntensity
    confidence_score: float = Field(ge=0, le=100)
    logic_chain: List[str] = Field(description="Step-by-step reasoning for the decision")
    risk_notes: str = Field(description="Risk management constraints for RiskMgr")
    suggested_module: str = Field(description="The name of the execution module from Scheme A")
    decision_summary: str = Field(default="No summary provided", description="High-level 2-3 sentence summary of decision rationale")
    conflict_report: str = Field(default="No conflicts detected", description="Summary of conflicts detected and how they were resolved")

# --- 4. Shared Global State ---

class TradingState(BaseModel):
    """Global context maintained in the Environment."""
    current_ticker: str
    fa_data: Optional[FAReport] = None
    ta_data: Optional[TAReport] = None
    sa_data: Optional[SAReport] = None
    final_decision: Optional[StrategyDecision] = None

# --- Updated Schemas for Scheme C (Dynamic Inquiry) ---

class InvestigationRequest(BaseModel):
    """Protocol for AS to request a deep dive investigation."""
    ticker: str
    target_agent: str = "SA"
    context_issue: str = Field(description="The specific conflicting issue to investigate")
    current_retry: int = Field(default=0, description="Current number of retries")
    max_retries: int = Field(default=1, description="Max retries allowed based on importance")
    importance_level: int = Field(default=1, description="1 for Normal, 2 for High Importance")

class InvestigationReport(BaseModel):
    """
    Protocol for SA to provide deep dive results (Advanced Mode) - Pure Descriptive Evidence.

    This schema captures conflict resolution analysis with ZERO LLM-generated numeric scores.
    All sentiment assessment is qualitative. Focuses on explicit risk classification and
    evidence gap identification for strategic decision-making.
    """
    ticker: str

    # Core investigation fields - Pure descriptive
    detailed_findings: str = Field(description="Qualitative results of the deep investigation with causal analysis")
    is_ambiguity_resolved: bool = Field(description="Whether the conflict is cleared based on evidence")

    # Qualitative sentiment assessment - NO numeric score
    qualitative_sentiment_revision: str = Field(
        default="No sentiment revision available",
        description="Descriptive assessment of how the investigation changes the sentiment outlook (e.g., 'More negative due to...', 'Confirms positive outlook because...', 'Neutral - insufficient evidence')"
    )

    # Expert-Evidence Fields
    risk_classification: str = Field(
        default="MANAGEABLE_NOISE",
        description="Categorical classification: 'FUNDAMENTAL_THREAT', 'MANAGEABLE_NOISE', or 'INSUFFICIENT_DATA' based on structural impact analysis"
    )

    evidence_gaps: List[str] = Field(
        default_factory=list,
        description="Explicitly list unresolved ambiguities or missing data points that prevent full conflict resolution (e.g., ['Lack of specific revenue impact figures', 'No clarity on management mitigation timeline'])"
    )

    # Additional investigation metadata
    key_evidence: List[str] = Field(
        default_factory=list,
        description="Key evidence points that support the investigation findings"
    )

    confidence_level: str = Field(
        default="MEDIUM",
        description="Categorical confidence assessment: 'HIGH', 'MEDIUM', or 'LOW' based on evidence quality and completeness"
    )