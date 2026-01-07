"""
Filename: MetaGPT-Ewan/MAT/actions/search_deep_dive.py
Created Date: Sunday, December 29th 2025
Author: Ewan Su
Description: SearchDeepDive action using Tavily API for targeted investigation.

This action is triggered by InvestigationRequest from Alpha Strategist.
It performs advanced web search to clarify conflicts between signals.

Configuration:
    API keys are loaded from config/config2.yaml file.
    Set your Tavily API key in the config file to enable this action.
"""

import re
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from metagpt.actions import Action
from metagpt.logs import logger
from pydantic import Field

from ..schemas import InvestigationRequest, InvestigationReport
from ..config_loader import get_config


# Company name mapping for better search queries
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "GOOGL": "Google Alphabet",
    "GOOG": "Google Alphabet",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "NVDA": "Nvidia",
    "META": "Meta Facebook",
    "TSLA": "Tesla",
    "AMD": "AMD Advanced Micro Devices",
    "INTC": "Intel",
    "NFLX": "Netflix",
    "DIS": "Disney",
    "CRM": "Salesforce",
    "ORCL": "Oracle",
    "IBM": "IBM",
    "CSCO": "Cisco",
    "QCOM": "Qualcomm",
    "TXN": "Texas Instruments",
    "ADBE": "Adobe",
    "PYPL": "PayPal",
    "SQ": "Block Square",
    "SHOP": "Shopify",
    "UBER": "Uber",
    "LYFT": "Lyft",
    "ABNB": "Airbnb",
    "COIN": "Coinbase",
    "PLTR": "Palantir",
    "SNOW": "Snowflake",
    "ZM": "Zoom",
    "DOCU": "DocuSign",
    # Add more as needed
}


class SearchDeepDive(Action):
    """
    Deep dive search action using Tavily API for targeted investigation.
    
    This action is used by the Sentiment Analyst to investigate conflicts
    detected by the Alpha Strategist. It performs advanced web search
    combining ticker information with the specific context issue.
    
    Key Features:
    1. Intelligent query engineering (ticker + context_issue)
    2. Tavily API with search_depth="advanced"
    3. Full content extraction for comprehensive analysis
    4. LLM-based risk assessment (fundamental threat vs manageable noise)
    5. Returns structured InvestigationReport
    
    Example:
        If ticker="NVDA" and context="CFO resignation", the query becomes:
        "Nvidia NVDA CFO resignation reason analysis official statement"
    """
    
    name: str = "SearchDeepDive"
    
    # Output directory for saving search results
    output_dir: Path = Field(default=Path("MAT/report/SA"))
    
    # Tavily API configuration (loaded from config/config2.yaml)
    tavily_api_key: Optional[str] = Field(default=None)
    search_depth: str = Field(default="advanced")  # Use advanced for investigations
    max_results: int = Field(default=10)
    include_answer: bool = Field(default=True)
    include_raw_content: bool = Field(default=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load configuration from config/config2.yaml
        config = get_config()
        
        # Get Tavily settings from config
        tavily_config = config.get_tavily_config()
        self.tavily_api_key = tavily_config.get("api_key")
        self.search_depth = tavily_config.get("search_depth", "advanced")
        self.max_results = tavily_config.get("max_results", 10)
        self.include_answer = tavily_config.get("include_answer", True)
        self.include_raw_content = tavily_config.get("include_raw_content", True)

        # Note: output_dir uses Field default (MAT/report/SA) unless overridden in config

        # Log initialization status
        if self.tavily_api_key:
            logger.info(f"🔍 SearchDeepDive initialized (search_depth={self.search_depth})")
        else:
            logger.warning("⚠️ SearchDeepDive: Tavily API key not configured in config/config2.yaml")
    
    async def run(
        self,
        investigation_request: Optional[InvestigationRequest] = None,
        ticker: Optional[str] = None,
        mode: str = "basic",
        llm_callback: Optional[Any] = None,
        reference_date: Optional[str] = None
    ):
        """
        Execute search and sentiment analysis in basic or advanced mode.

        This action supports two modes:
        1. **Basic Mode** (mode="basic"):
           - Triggered by Ticker broadcast (StartAnalysis)
           - Uses search_depth="basic" in Tavily
           - Returns SAReport (normal sentiment analysis)

        2. **Advanced Mode** (mode="advanced"):
           - Triggered by InvestigationRequest from Alpha Strategist
           - Uses search_depth="advanced" in Tavily
           - Focuses on specific context_issue
           - Returns InvestigationReport with revised sentiment

        Args:
            investigation_request: The InvestigationRequest from Alpha Strategist (required for advanced mode)
            ticker: Stock ticker symbol (required for basic mode)
            mode: "basic" or "advanced" (default: "basic")
            llm_callback: Optional callback for LLM analysis (default: use self._aask)
            reference_date: Optional reference date for historical search (e.g., "2022-12-31")

        Returns:
            SAReport (basic mode) or InvestigationReport (advanced mode)
        """
        # Auto-detect mode based on investigation_request presence
        if investigation_request is not None:
            mode = "advanced"
            ticker = investigation_request.ticker
            logger.info("🤖 Auto-Detection: investigation_request provided -> switching to ADVANCED mode")

        # Validate inputs based on mode
        if mode == "advanced":
            if investigation_request is None:
                raise ValueError("investigation_request is required for advanced mode")
            ticker = investigation_request.ticker
            context_issue = investigation_request.context_issue
            importance_level = investigation_request.importance_level
            current_retry = investigation_request.current_retry
        elif mode == "basic":
            if ticker is None:
                raise ValueError("ticker is required for basic mode")
            context_issue = None
            importance_level = 1
            current_retry = 0
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'basic' or 'advanced'")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 SEARCH ACTION ({mode.upper()} MODE): {ticker}")
        logger.info(f"{'='*80}")
        if mode == "advanced":
            logger.info(f"📋 Context Issue: {context_issue[:150]}...")
            logger.info(f"📊 Importance Level: {importance_level} (1=Normal, 2=High)")
            logger.info(f"🔄 Retry: {current_retry + 1}/{investigation_request.max_retries}")
        else:
            logger.info(f"📋 Mode: Basic sentiment analysis")
        
        try:
            # Step 1: Build search query based on mode
            if mode == "advanced":
                search_query = self._build_investigation_query(ticker, context_issue, reference_date)
                max_results = 15 if importance_level == 2 else 10
                search_depth = "advanced"
            else:
                # Basic mode: general news sentiment search
                if reference_date:
                    # Extract year and quarter from reference date
                    ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
                    year = ref_dt.year
                    quarter = (ref_dt.month - 1) // 3 + 1
                    search_query = f"{ticker} stock news sentiment Q{quarter} {year}"
                    logger.info(f"🕰️  Time-Travel Mode: Searching for Q{quarter} {year} news")
                else:
                    search_query = f"{ticker} stock news sentiment latest analysis"
                max_results = 5
                search_depth = "basic"

            logger.info(f"🔎 Engineered Query: '{search_query}'")
            logger.info(f"🔎 Search Depth: {search_depth}")

            # Step 2: Execute Tavily search with appropriate depth
            original_depth = self.search_depth
            self.search_depth = search_depth  # Temporarily set search depth
            search_results = await self._execute_tavily_search(
                query=search_query,
                max_results=max_results
            )
            self.search_depth = original_depth  # Restore original depth

            # Step 3: DUAL-SAVING PROTOCOL (Part 1): Save RAW search results immediately
            self._save_raw_search_results(ticker, search_results, reference_date)
            
            if not search_results:
                logger.warning("⚠️ No search results found")
                if mode == "advanced":
                    return InvestigationReport(
                        ticker=ticker,
                        detailed_findings="Deep dive search returned no results. Unable to clarify the conflict.",
                        qualitative_sentiment_revision="Insufficient data - no search results available",
                        is_ambiguity_resolved=False,
                        risk_classification="INSUFFICIENT_DATA",
                        evidence_gaps=["No search results available"],
                        key_evidence=[],
                        confidence_level="LOW"
                    )
                else:
                    # Basic mode: return neutral SAReport
                    from ..schemas import SAReport, MarketEvent
                    return SAReport(
                        ticker=ticker,
                        sentiment_score=0.0,
                        impactful_events=[MarketEvent.NONE],
                        top_keywords=["no-news"],
                        news_summary="No news found for sentiment analysis."
                    )

            # Step 4: Analyze with LLM based on mode
            if mode == "advanced":
                # Advanced mode: return InvestigationReport
                report = await self._analyze_search_results(
                    ticker=ticker,
                    context_issue=context_issue,
                    search_results=search_results,
                    importance_level=importance_level,
                    llm_callback=llm_callback
                )

                # DUAL-SAVING PROTOCOL (Part 2): Save structured InvestigationReport
                self._save_structured_report(ticker, report, reference_date, mode="advanced")

                logger.info(f"\n{'='*80}")
                logger.info(f"✅ DEEP DIVE COMPLETE for {ticker}")
                logger.info(f"📊 Sentiment Revision: {report.qualitative_sentiment_revision}")
                logger.info(f"📊 Risk Classification: {report.risk_classification}")
                logger.info(f"✅ Ambiguity Resolved: {report.is_ambiguity_resolved}")
                logger.info(f"📝 Findings: {report.detailed_findings[:100]}...")
                logger.info(f"{'='*80}\n")

                return report
            else:
                # Basic mode: return SAReport
                report = await self._analyze_basic_sentiment(
                    ticker=ticker,
                    search_results=search_results,
                    llm_callback=llm_callback
                )

                # DUAL-SAVING PROTOCOL (Part 2): Save structured SAReport
                self._save_structured_report(ticker, report, reference_date, mode="basic")

                logger.info(f"\n{'='*80}")
                logger.info(f"✅ BASIC SENTIMENT ANALYSIS COMPLETE for {ticker}")
                logger.info(f"📊 Qualitative Sentiment: {report.qualitative_sentiment_assessment[:100]}...")
                logger.info(f"📝 Events: {[e.value for e in report.impactful_events]}")
                logger.info(f"{'='*80}\n")

                return report

        except Exception as e:
            logger.error(f"❌ Search action failed: {e}")
            if mode == "advanced":
                return InvestigationReport(
                    ticker=ticker,
                    detailed_findings=f"Investigation failed due to error: {str(e)}",
                    qualitative_sentiment_revision="Analysis failed - unable to assess sentiment impact",
                    is_ambiguity_resolved=False,
                    risk_classification="INSUFFICIENT_DATA",
                    evidence_gaps=["Investigation failed due to technical error"],
                    key_evidence=[],
                    confidence_level="LOW"
                )
            else:
                from ..schemas import SAReport, MarketEvent
                return SAReport(
                    ticker=ticker,
                    impactful_events=[MarketEvent.NONE],
                    top_keywords=["error"],
                    news_summary=f"Analysis failed: {str(e)}",
                    qualitative_sentiment_assessment="Analysis failed - unable to assess sentiment"
                )
    
    def _build_investigation_query(self, ticker: str, context_issue: str, reference_date: Optional[str] = None) -> str:
        """
        Build an intelligent search query combining ticker and context issue.

        Query Engineering Strategy:
        1. Include company name (not just ticker) for broader results
        2. Extract key terms from context_issue
        3. Add analytical keywords for deeper insights
        4. Include "official statement" for authoritative sources
        
        Args:
            ticker: Stock ticker symbol (e.g., "NVDA")
            context_issue: The specific conflict/issue to investigate
            
        Returns:
            Optimized search query string
            
        Example:
            Input: ticker="NVDA", context="CFO resignation"
            Output: "Nvidia NVDA CFO resignation reason analysis official statement"
        """
        # Get company name from mapping, or use ticker as fallback
        company_name = TICKER_TO_COMPANY.get(ticker.upper(), ticker)
        
        # Extract key terms from context_issue
        # Remove common words and extract important terms
        key_terms = self._extract_key_terms(context_issue)
        
        # Analytical keywords to add depth to search
        analytical_keywords = ["reason", "analysis", "impact", "official statement"]

        # Add time context if reference_date is provided
        time_context = ""
        if reference_date:
            ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
            year = ref_dt.year
            quarter = (ref_dt.month - 1) // 3 + 1
            time_context = f"Q{quarter} {year}"

        # Build the query
        query_parts = [
            company_name,
            ticker.upper(),
            " ".join(key_terms[:5]),  # Top 5 key terms
            " ".join(analytical_keywords[:3]),  # Add 3 analytical keywords
            time_context  # Add time context if available
        ]

        query = " ".join([p for p in query_parts if p])  # Filter out empty strings
        
        # Limit query length to avoid API issues
        if len(query) > 300:
            query = query[:300]
        
        return query.strip()
    
    def _extract_key_terms(self, context_issue: str) -> List[str]:
        """
        Extract key terms from the context issue for query building.
        
        Args:
            context_issue: The conflict description
            
        Returns:
            List of key terms
        """
        # Common words to filter out
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "and", "but", "or", "nor", "for", "yet", "so", "as", "if", "then",
            "than", "that", "this", "these", "those", "it", "its", "of", "to",
            "in", "on", "at", "by", "with", "from", "into", "onto", "upon",
            "about", "above", "below", "between", "under", "over", "through",
            "during", "before", "after", "while", "because", "although", "though",
            "signal", "bullish", "bearish", "sentiment", "negative", "positive",
            "conflict", "detected", "unclear", "analysis", "analyst"
        }
        
        # Extract words and filter
        words = re.findall(r'\b[a-zA-Z]{3,}\b', context_issue.lower())
        key_terms = [w for w in words if w not in stop_words]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in key_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms
    
    async def _execute_tavily_search(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Execute search using Tavily API.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, content, url, score
        """
        try:
            from tavily import TavilyClient
        except ImportError:
            logger.error("❌ Tavily not installed. Run: pip install tavily-python")
            return []
        
        if not self.tavily_api_key:
            logger.error("❌ Tavily API key not configured!")
            logger.error("   Please set your API key in: config/config2.yaml")
            logger.error("   Under the 'tavily:' section, set 'api_key: your-key-here'")
            return []
        
        try:
            logger.info(f"🌐 Executing Tavily search (depth={self.search_depth})")

            client = TavilyClient(api_key=self.tavily_api_key)

            # Execute search with advanced depth for investigation
            response = client.search(
                query=query,
                search_depth=self.search_depth,  # "advanced" for deep investigations
                max_results=max_results,
                include_answer=self.include_answer,
                include_raw_content=self.include_raw_content,
                include_domains=[],  # No domain restrictions
                exclude_domains=[]   # No domain exclusions
            )

            # Check if response is valid
            if response is None:
                logger.error("❌ Tavily returned None response")
                return []

            # Debug: log response type and keys
            logger.debug(f"Tavily response type: {type(response)}")
            if isinstance(response, dict):
                logger.debug(f"Tavily response keys: {list(response.keys())}")

            # Extract and format results
            results = []

            # Include Tavily's AI-generated answer if available
            if response.get("answer"):
                results.append({
                    "title": "Tavily AI Summary",
                    "content": response["answer"],
                    "url": "AI Generated Summary",
                    "score": 1.0,
                    "raw_content": response.get("answer", "")
                })

            # Process search results - handle case where results might be None
            search_results = response.get("results")
            if search_results is None:
                logger.warning("⚠️ Tavily response has no 'results' field")
                search_results = []

            for item in search_results:
                if item is None:
                    continue

                # Safely extract content and raw_content
                content = item.get("content", "") or ""  # Handle None
                raw_content = item.get("raw_content", "") or ""  # Handle None

                result = {
                    "title": item.get("title", "No Title"),
                    "content": content[:1000],  # Snippet content
                    "url": item.get("url", ""),
                    "score": item.get("score", 0.0),
                    "raw_content": raw_content[:3000] if self.include_raw_content else ""
                }
                results.append(result)
            
            logger.info(f"✅ Tavily returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Tavily search failed: {e}")
            import traceback
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            return []
    
    def _save_raw_search_results(
        self,
        ticker: str,
        results: List[Dict],
        reference_date: Optional[str] = None
    ):
        """
        DUAL-SAVING PROTOCOL (Part 1): Save RAW search results immediately after Tavily search.

        This saves the unprocessed Tavily API response for debugging and audit purposes.

        Args:
            ticker: Stock ticker symbol
            results: Raw search results from Tavily
            reference_date: Optional reference date for filename (format: YYYY-MM-DD)
        """
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Extract year from reference_date or use timestamp
        if reference_date:
            year = datetime.strptime(reference_date, "%Y-%m-%d").year
            filename = f"Raw_Search_{ticker}_{year}.json"
        else:
            filename = f"Raw_Search_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        json_path = self.output_dir / filename

        try:
            # Save raw JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"📁 Raw search results saved: {json_path}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to save raw search results: {e}")

    def _save_structured_report(
        self,
        ticker: str,
        report,  # SAReport or InvestigationReport
        reference_date: Optional[str] = None,
        mode: str = "basic"
    ):
        """
        DUAL-SAVING PROTOCOL (Part 2): Save structured report after LLM analysis.

        This saves the final Pydantic-validated report (SAReport or InvestigationReport)
        for downstream consumption by Alpha Strategist.

        Args:
            ticker: Stock ticker symbol
            report: SAReport (basic mode) or InvestigationReport (advanced mode)
            reference_date: Optional reference date for filename (format: YYYY-MM-DD)
            mode: "basic" or "advanced"
        """
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Extract year from reference_date or use timestamp
        if reference_date:
            year = datetime.strptime(reference_date, "%Y-%m-%d").year
            filename = f"SA_report_{mode}_{ticker}_{year}.json"
        else:
            filename = f"SA_report_{mode}_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        json_path = self.output_dir / filename

        try:
            # Save structured report as JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report.model_dump(), f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📁 Structured {mode.upper()} report saved: {json_path}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to save structured report: {e}")
    
    async def _analyze_search_results(
        self,
        ticker: str,
        context_issue: str,
        search_results: List[Dict],
        importance_level: int,
        llm_callback: Optional[Any] = None
    ) -> InvestigationReport:
        """
        Analyze search results using LLM to determine risk assessment.
        
        The LLM is instructed with a strict prompt to:
        1. Determine if the news represents a FUNDAMENTAL THREAT or MANAGEABLE NOISE
        2. Clarify if the risk is temporary or structural
        3. Provide a revised sentiment score
        4. Determine if the ambiguity is resolved
        
        Args:
            ticker: Stock ticker symbol
            context_issue: The conflict/issue being investigated
            search_results: Tavily search results
            importance_level: 1=Normal, 2=High
            llm_callback: Optional callback for LLM (uses self._aask if None)
            
        Returns:
            InvestigationReport with detailed findings
        """
        # Prepare search content for LLM
        search_content = self._prepare_content_for_llm(search_results)
        
        # Build PURE DESCRIPTIVE investigation prompt (NO numeric scores)
        prompt = f"""
You are a senior financial risk analyst conducting a CRITICAL INVESTIGATION for {ticker} stock.

=== INVESTIGATION CONTEXT ===
TICKER: {ticker}
COMPANY: {TICKER_TO_COMPANY.get(ticker.upper(), ticker)}
IMPORTANCE LEVEL: {importance_level} (1=Normal, 2=High Priority)

DETECTED CONFLICT:
{context_issue}

=== SEARCH RESULTS (FROM TAVILY ADVANCED SEARCH) ===
{search_content}

=== YOUR PURE DESCRIPTIVE INVESTIGATION TASK ===
CRITICAL RULES:
- You are providing QUALITATIVE EVIDENCE ONLY
- DO NOT generate numeric sentiment scores
- ALL sentiment revision must be DESCRIPTIVE (e.g., "More negative due to...", "Confirms positive outlook because...", "Neutral - insufficient evidence")
- Focus on STRUCTURAL IMPACT ANALYSIS and EVIDENCE GAPS

**Critical Analysis Requirements:**

1. **Risk Classification (Categorical):**
   - FUNDAMENTAL_THREAT: Structural, long-term risk materially affecting business model, competitive position, or financial health
   - MANAGEABLE_NOISE: Temporary, isolated incident NOT fundamentally altering investment thesis
   - INSUFFICIENT_DATA: Search results don't provide enough clarity to classify

2. **Conflict Resolution Analysis (Qualitative):**
   - What specific information RESOLVES or CLARIFIES the ambiguity?
   - What is the SPECIFIC IMPACT on the company? (Revenue, margins, reputation, regulatory)
   - Is this issue TEMPORARY (short-term noise) or STRUCTURAL (fundamental threat)?
   - Provide QUALITATIVE sentiment revision: How does this investigation change the sentiment outlook?
   - Example: "Investigation reveals regulatory concerns are more negative than initially assessed. The FDA approval delay will likely extend product launch by 6-9 months, creating negative revenue impact headwinds."

3. **Evidence Gaps (CRITICAL):**
   - Explicitly list UNRESOLVED AMBIGUITIES or MISSING DATA POINTS
   - What questions remain unanswered despite the investigation?
   - What additional information would be needed for full clarity?
   - Example: ["Lack of specific revenue impact figures", "No clarity on management's mitigation timeline", "Unclear regulatory approval status"]

4. **Confidence Assessment (Categorical):**
   - HIGH: Strong evidence, conflict fully resolved, minimal ambiguity
   - MEDIUM: Partial resolution, some evidence gaps remain
   - LOW: Insufficient data, major ambiguities unresolved

=== OUTPUT FORMAT (STRICT JSON) ===
{{
    "risk_classification": "FUNDAMENTAL_THREAT" | "MANAGEABLE_NOISE" | "INSUFFICIENT_DATA",
    "detailed_findings": "<3-4 sentences explaining what investigation revealed, specific impact, and whether risk is temporary or structural>",
    "qualitative_sentiment_revision": "<Descriptive assessment of how investigation changes sentiment outlook (1-2 sentences). Examples: 'More negative due to structural revenue headwinds', 'Confirms positive outlook with manageable risks', 'Neutral - insufficient evidence for clear directional change'. NO numeric scores.>",
    "is_ambiguity_resolved": <true if conflict is now clear, false if uncertainty remains>,
    "evidence_gaps": [
        "<Specific missing data point or unresolved question 1>",
        "<Specific missing data point or unresolved question 2>",
        "<Specific missing data point or unresolved question 3>"
    ],
    "key_evidence": ["<evidence point 1>", "<evidence point 2>", "<evidence point 3>"],
    "confidence_level": "HIGH" | "MEDIUM" | "LOW"
}}

CRITICAL: Explicitly document what you DON'T know (evidence_gaps) as much as what you DO know. This is PURE DESCRIPTIVE EVIDENCE - NO numeric sentiment scores.
"""
        
        try:
            # Call LLM
            if llm_callback:
                response = await llm_callback(prompt)
            else:
                response = await self._aask(prompt)
            
            # Parse LLM response
            parsed = self._parse_llm_response(response)

            # Log the expert evidence analysis
            logger.info(f"📊 Investigation Expert Evidence:")
            logger.info(f"   - Risk Classification: {parsed.get('risk_classification', 'UNKNOWN')}")
            logger.info(f"   - Confidence: {parsed.get('confidence_level', 'UNKNOWN')}")
            logger.info(f"   - Key Evidence: {parsed.get('key_evidence', [])[:2]}")
            logger.info(f"   - Evidence Gaps: {parsed.get('evidence_gaps', [])[:2]}")

            # Create InvestigationReport with pure descriptive evidence fields
            report = InvestigationReport(
                ticker=ticker,
                detailed_findings=parsed["detailed_findings"],
                qualitative_sentiment_revision=parsed.get("qualitative_sentiment_revision", "No sentiment revision available"),
                is_ambiguity_resolved=parsed["is_ambiguity_resolved"],
                risk_classification=parsed.get("risk_classification", "MANAGEABLE_NOISE"),
                evidence_gaps=parsed.get("evidence_gaps", []),
                key_evidence=parsed.get("key_evidence", []),
                confidence_level=parsed.get("confidence_level", "MEDIUM")
            )

            return report

        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {e}")
            return InvestigationReport(
                ticker=ticker,
                detailed_findings=f"LLM analysis failed: {str(e)}. Unable to assess risk.",
                qualitative_sentiment_revision="Investigation failed - unable to assess sentiment impact",
                is_ambiguity_resolved=False,
                risk_classification="INSUFFICIENT_DATA",
                evidence_gaps=["Investigation failed due to technical error", "Unable to retrieve search results or parse LLM response"],
                key_evidence=[],
                confidence_level="LOW"
            )
    
    def _prepare_content_for_llm(self, search_results: List[Dict]) -> str:
        """
        Prepare search results content for LLM analysis.
        
        Args:
            search_results: Tavily search results
            
        Returns:
            Formatted string for LLM prompt
        """
        content_parts = []
        
        for i, result in enumerate(search_results[:8], 1):  # Limit to top 8 for token efficiency
            title = result.get("title", "No Title")
            url = result.get("url", "N/A")
            content = result.get("content", "")
            raw_content = result.get("raw_content", "")
            score = result.get("score", 0.0)
            
            # Use raw_content if available, otherwise use snippet
            main_content = raw_content[:1500] if raw_content else content[:800]
            
            part = f"""
--- RESULT {i} (Relevance: {score:.2f}) ---
Title: {title}
Source: {url}
Content:
{main_content}
"""
            content_parts.append(part)
        
        return "\n".join(content_parts)
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        Parse LLM JSON response with robust error handling.
        
        Args:
            response: LLM response string
            
        Returns:
            Parsed dictionary with analysis data
        """
        try:
            # Try to extract JSON from response
            # Handle markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # Try direct JSON extraction
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = json.loads(response)
            
            # Validate and normalize fields (pure descriptive - no numeric sentiment_score)
            return {
                "risk_classification": data.get("risk_classification", "INSUFFICIENT_DATA"),
                "detailed_findings": data.get("detailed_findings", "Analysis parsing failed"),
                "qualitative_sentiment_revision": data.get("qualitative_sentiment_revision", "No sentiment revision available"),
                "is_ambiguity_resolved": bool(data.get("is_ambiguity_resolved", False)),
                "evidence_gaps": data.get("evidence_gaps", []),
                "key_evidence": data.get("key_evidence", []),
                "confidence_level": data.get("confidence_level", "LOW")
            }

        except Exception as e:
            logger.error(f"❌ Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            return {
                "risk_classification": "PARSE_ERROR",
                "detailed_findings": f"Failed to parse LLM response: {str(e)}",
                "qualitative_sentiment_revision": "Parse error - unable to assess sentiment impact",
                "is_ambiguity_resolved": False,
                "evidence_gaps": ["Failed to parse investigation response"],
                "key_evidence": [],
                "confidence_level": "LOW"
            }
    
    async def _analyze_basic_sentiment(
        self,
        ticker: str,
        search_results: List[Dict],
        llm_callback: Optional[Any] = None
    ):
        """
        Analyze search results for basic sentiment analysis mode.

        The LLM is instructed to:
        1. Provide overall sentiment score from -1 to +1
        2. Identify major market-moving events
        3. Extract key keywords
        4. Write a brief summary

        Args:
            ticker: Stock ticker symbol
            search_results: Tavily search results
            llm_callback: Optional callback for LLM (uses self._aask if None)

        Returns:
            SAReport with sentiment analysis
        """
        from ..schemas import SAReport, MarketEvent

        # Prepare search content for LLM
        search_content = self._prepare_content_for_llm(search_results)

        # Build PURE DESCRIPTIVE sentiment analysis prompt (NO numeric scores)
        prompt = f"""
You are an expert sentiment analyst providing PURE DESCRIPTIVE EVIDENCE for {ticker} stock.

=== NEWS ARTICLES ===
{search_content}

=== YOUR PURE DESCRIPTIVE ANALYSIS TASK ===
CRITICAL RULES:
- You are providing QUALITATIVE CAUSAL ANALYSIS ONLY
- DO NOT generate numeric sentiment scores
- ALL sentiment assessment must be DESCRIPTIVE (e.g., "Broadly positive", "Mixed with bearish undertones", "Decisively negative")
- Focus on CAUSAL STRUCTURES and STRUCTURAL EVIDENCE from news content

**Critical Analysis Requirements:**

1. **Qualitative Sentiment Assessment:**
   - Provide a descriptive overall sentiment assessment (1-2 sentences)
   - Example: "Broadly positive sentiment driven by strong product demand signals, though tempered by macro headwinds and cautious guidance."
   - NO numeric scores - purely qualitative

2. **Sentiment Matrix (Qualitative Audits for Each Dimension):**
   - Break down sentiment into sub-factor QUALITATIVE AUDITS (NOT numeric scores):
     * Product_Demand: Qualitative assessment of customer demand signals from news
     * Macro_Environment: Qualitative assessment of macro headwind/tailwind narratives
     * Management_Confidence: Qualitative assessment of guidance tone and management commentary
     * Competitive_Position: Qualitative assessment of market share and competitive dynamics
   - Example: {{
       "Product_Demand": "Strong iPhone sales momentum indicated by multiple channel checks and bullish analyst commentary. Premium segment showing resilience despite macro concerns.",
       "Macro_Environment": "Headwinds from inflation and supply chain disruptions mentioned across multiple reports. Management cited elevated input costs as margin pressure.",
       "Management_Confidence": "Cautious guidance with management citing 'uncertain macro backdrop.' Forward revenue outlook lowered by 3-5% for next quarter.",
       "Competitive_Position": "Market share gains in services segment noted by analysts. However, smartphone market share faces pressure from competitors in China."
     }}

3. **Causal Narrative (BECAUSE-THEN Logic):**
   - Synthesize a coherent narrative paragraph (3-5 sentences) using explicit BECAUSE-THEN logic
   - Connect segment drivers to overall performance causally
   - Example: "Revenue grew 8% YoY BECAUSE iPhone sales rebounded 10%, WHICH THEN compensated for services growth slowdown. DUE TO inflation pressures, management focused on premium models, WHICH LED TO sustained margins despite volume concerns."
   - This MUST read like a professional analyst's narrative, NOT bullet points

4. **Expectation Gap Analysis (Qualitative):**
   - Describe "Actual Performance vs. Market Expectations" qualitatively
   - Identify beats, misses, or inline results with market reaction context
   - Example: "Revenue beat consensus by 2%, BUT stock fell 3% BECAUSE guidance was cut 5%, revealing investor focus shifted from current quarter to future outlook. Market reaction suggests disappointing forward outlook overshadowed current beat."

5. **Paradoxes and Tensions:**
   - Identify anomalies: "Good News, Price Drop" or "Revenue Beat, Weak Guidance"
   - Explain what these contradictions reveal about business health
   - Example: "Paradox: Strong earnings BUT weak stock reaction. Reflects investor concern that growth is price-driven (unsustainable) rather than volume-driven."

=== OUTPUT FORMAT (STRICT JSON) ===
{{
    "qualitative_sentiment_assessment": "<Descriptive overall sentiment (1-2 sentences). NO numeric scores.>",
    "events": ["EVENT_TYPE_1", "EVENT_TYPE_2"],
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "news_summary": "<Coherent narrative paragraph using BECAUSE-THEN causal logic (3-5 sentences, NOT bullet points)>",
    "sentiment_matrix": {{
        "Product_Demand": "<Qualitative audit of demand signals from news. 1-2 sentences.>",
        "Macro_Environment": "<Qualitative audit of macro headwind/tailwind narratives. 1-2 sentences.>",
        "Management_Confidence": "<Qualitative audit of guidance tone and management commentary. 1-2 sentences.>",
        "Competitive_Position": "<Qualitative audit of market share and competitive dynamics. 1-2 sentences.>"
    }},
    "causal_narrative": "<Deep causal explanation connecting segment drivers to performance with BECAUSE-THEN logic. 2-3 sentences.>",
    "expectation_gap": "<Qualitative analysis of actual vs. expected performance with market reaction. 2-3 sentences.>",
    "paradoxes_or_tensions": "<Contradictions and what they reveal about business health. 1-2 sentences or 'None identified'.>"
}}

**Event Types:** EARNINGS_CALL, PRODUCT_LAUNCH, REGULATORY_ACTION, ANALYST_UPGRADE, MACRO_ECONOMIC, NONE

CRITICAL: This is PURE DESCRIPTIVE EVIDENCE. NO numeric sentiment scores. All sentiment assessment must be qualitative and anchored in news content.
"""

        try:
            # Call LLM
            if llm_callback:
                response = await llm_callback(prompt)
            else:
                response = await self._aask(prompt)

            # Parse LLM response
            parsed = self._parse_basic_sentiment_response(response)

            # Log the pure descriptive evidence analysis
            logger.info(f"📊 Sentiment Descriptive Evidence Analysis:")
            logger.info(f"   - Qualitative Assessment: {parsed.get('qualitative_sentiment_assessment', 'N/A')[:100]}...")
            logger.info(f"   - Events: {parsed['events']}")
            logger.info(f"   - Keywords: {parsed['keywords'][:5]}")
            logger.info(f"   - Sentiment Matrix (Qualitative):")
            for factor, audit in parsed.get('sentiment_matrix', {}).items():
                logger.info(f"     * {factor}: {audit[:80]}...")
            logger.info(f"   - Causal Narrative: {parsed.get('causal_narrative', 'N/A')[:150]}...")
            logger.info(f"   - Expectation Gap: {parsed.get('expectation_gap', 'N/A')[:150]}...")
            logger.info(f"   - Paradoxes/Tensions: {parsed.get('paradoxes_or_tensions', 'None identified')}")
            logger.info(f"   - News Summary: {parsed['summary'][:200]}...")

            # Create SAReport with pure descriptive evidence fields
            report = SAReport(
                ticker=ticker,
                impactful_events=parsed["events"],
                top_keywords=parsed["keywords"],
                news_summary=parsed["summary"],
                qualitative_sentiment_assessment=parsed.get("qualitative_sentiment_assessment", "No sentiment assessment available"),
                sentiment_matrix=parsed.get("sentiment_matrix", {}),
                causal_narrative=parsed.get("causal_narrative", "No causal analysis available"),
                expectation_gap=parsed.get("expectation_gap", "No expectation analysis available"),
                paradoxes_or_tensions=parsed.get("paradoxes_or_tensions", "None identified")
            )

            return report

        except Exception as e:
            logger.error(f"❌ Basic sentiment analysis failed: {e}")
            return SAReport(
                ticker=ticker,
                impactful_events=[MarketEvent.NONE],
                top_keywords=["analysis-error"],
                news_summary=f"Sentiment analysis failed: {str(e)}",
                qualitative_sentiment_assessment="Analysis failed - unable to assess sentiment"
            )

    def _parse_basic_sentiment_response(self, response: str) -> Dict:
        """
        Parse LLM JSON response for basic sentiment analysis.

        Args:
            response: LLM response string

        Returns:
            Parsed dictionary with sentiment data
        """
        from ..schemas import MarketEvent

        try:
            # Try to extract JSON from response
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # Try direct JSON extraction
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = json.loads(response)

            # Parse events
            events = []
            for event_str in data.get("events", []):
                try:
                    events.append(MarketEvent[event_str])
                except KeyError:
                    logger.warning(f"Unknown event type: {event_str}")

            if not events:
                events = [MarketEvent.NONE]

            # Validate and normalize fields (pure descriptive - no numeric sentiment_score)
            return {
                "qualitative_sentiment_assessment": data.get("qualitative_sentiment_assessment", "No sentiment assessment available"),
                "events": events,
                "keywords": data.get("keywords", [])[:5],  # Limit to 5 keywords
                "summary": data.get("news_summary", data.get("summary", "No summary available")),
                "sentiment_matrix": data.get("sentiment_matrix", {}),  # Now expects Dict[str, str] instead of Dict[str, float]
                "causal_narrative": data.get("causal_narrative", "No causal analysis available"),
                "expectation_gap": data.get("expectation_gap", "No expectation analysis available"),
                "paradoxes_or_tensions": data.get("paradoxes_or_tensions", "None identified")
            }

        except Exception as e:
            logger.error(f"❌ Failed to parse basic sentiment response: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            return {
                "qualitative_sentiment_assessment": "Failed to parse sentiment response",
                "events": [MarketEvent.NONE],
                "keywords": [],
                "summary": f"Failed to parse sentiment response: {str(e)}",
                "sentiment_matrix": {},
                "causal_narrative": "No causal analysis available",
                "expectation_gap": "No expectation analysis available",
                "paradoxes_or_tensions": "None identified"
            }

    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp a value between min and max."""
        return max(min_val, min(max_val, value))

