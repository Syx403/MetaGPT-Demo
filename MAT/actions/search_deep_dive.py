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
    output_dir: Path = Field(default=Path("MAT/data/search_results"))
    
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
        
        # Get output directory from config
        self.output_dir = config.get_search_output_dir()
        
        # Log initialization status
        if self.tavily_api_key:
            logger.info(f"🔍 SearchDeepDive initialized (search_depth={self.search_depth})")
        else:
            logger.warning("⚠️ SearchDeepDive: Tavily API key not configured in config/config2.yaml")
    
    async def run(
        self,
        investigation_request: InvestigationRequest,
        llm_callback: Optional[Any] = None
    ) -> InvestigationReport:
        """
        Execute deep dive search and analysis.
        
        Args:
            investigation_request: The InvestigationRequest from Alpha Strategist
            llm_callback: Optional callback for LLM analysis (default: use self._aask)
            
        Returns:
            InvestigationReport with detailed findings and revised sentiment
        """
        ticker = investigation_request.ticker
        context_issue = investigation_request.context_issue
        importance_level = investigation_request.importance_level
        current_retry = investigation_request.current_retry
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 SEARCH DEEP DIVE ACTION: {ticker}")
        logger.info(f"{'='*80}")
        logger.info(f"📋 Context Issue: {context_issue[:150]}...")
        logger.info(f"📊 Importance Level: {importance_level} (1=Normal, 2=High)")
        logger.info(f"🔄 Retry: {current_retry + 1}/{investigation_request.max_retries}")
        
        try:
            # Step 1: Build intelligent search query
            search_query = self._build_investigation_query(ticker, context_issue)
            logger.info(f"🔎 Engineered Query: '{search_query}'")
            
            # Step 2: Execute Tavily search
            search_results = await self._execute_tavily_search(
                query=search_query,
                max_results=15 if importance_level == 2 else 10
            )
            
            # Step 3: Save search results for audit/debugging
            self._save_search_results(ticker, current_retry + 1, search_results)
            
            if not search_results:
                logger.warning("⚠️ No search results found")
                return InvestigationReport(
                    ticker=ticker,
                    detailed_findings="Deep dive search returned no results. Unable to clarify the conflict.",
                    revised_sentiment_score=0.0,
                    is_ambiguity_resolved=False
                )
            
            # Step 4: Analyze with LLM for risk assessment
            report = await self._analyze_search_results(
                ticker=ticker,
                context_issue=context_issue,
                search_results=search_results,
                importance_level=importance_level,
                llm_callback=llm_callback
            )
            
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ DEEP DIVE COMPLETE for {ticker}")
            logger.info(f"📊 Revised Sentiment: {report.revised_sentiment_score:.2f}")
            logger.info(f"✅ Ambiguity Resolved: {report.is_ambiguity_resolved}")
            logger.info(f"📝 Findings: {report.detailed_findings[:100]}...")
            logger.info(f"{'='*80}\n")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ SearchDeepDive failed: {e}")
            return InvestigationReport(
                ticker=ticker,
                detailed_findings=f"Investigation failed due to error: {str(e)}",
                revised_sentiment_score=0.0,
                is_ambiguity_resolved=False
            )
    
    def _build_investigation_query(self, ticker: str, context_issue: str) -> str:
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
        
        # Build the query
        query_parts = [
            company_name,
            ticker.upper(),
            " ".join(key_terms[:5]),  # Top 5 key terms
            " ".join(analytical_keywords[:3])  # Add 3 analytical keywords
        ]
        
        query = " ".join(query_parts)
        
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
            
            # Process search results
            for item in response.get("results", []):
                result = {
                    "title": item.get("title", "No Title"),
                    "content": item.get("content", "")[:1000],  # Snippet content
                    "url": item.get("url", ""),
                    "score": item.get("score", 0.0),
                    "raw_content": item.get("raw_content", "")[:3000] if self.include_raw_content else ""
                }
                results.append(result)
            
            logger.info(f"✅ Tavily returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Tavily search failed: {e}")
            return []
    
    def _save_search_results(
        self,
        ticker: str,
        round_num: int,
        results: List[Dict]
    ):
        """
        Save search results to files for audit and debugging.
        
        Args:
            ticker: Stock ticker symbol
            round_num: Investigation round number
            results: Search results to save
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON file
        json_path = self.output_dir / f"{ticker}_round{round_num}_{timestamp}.json"
        
        # Markdown file for human reading
        md_path = self.output_dir / f"{ticker}_round{round_num}_{timestamp}.md"
        
        try:
            # Save JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # Save Markdown
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Tavily Deep Dive Results: {ticker}\n\n")
                f.write(f"**Investigation Round:** {round_num}\n")
                f.write(f"**Timestamp:** {timestamp}\n")
                f.write(f"**Search Depth:** {self.search_depth}\n")
                f.write(f"**Total Results:** {len(results)}\n\n")
                f.write("---\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"## Result {i}: {result.get('title', 'No Title')}\n\n")
                    f.write(f"**URL:** {result.get('url', 'N/A')}\n")
                    f.write(f"**Relevance Score:** {result.get('score', 'N/A')}\n\n")
                    f.write(f"**Content Snippet:**\n")
                    f.write(f"```\n{result.get('content', 'No content')}\n```\n\n")
                    
                    if result.get('raw_content'):
                        f.write(f"**Full Content (truncated):**\n")
                        f.write(f"```\n{result.get('raw_content', '')[:1500]}...\n```\n\n")
                    
                    f.write("---\n\n")
            
            logger.info(f"📁 Search results saved:")
            logger.info(f"   JSON: {json_path}")
            logger.info(f"   MD:   {md_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to save search results: {e}")
    
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
        
        # Build strict analysis prompt
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

=== YOUR TASK ===
STRICT INSTRUCTION: Determine if this news represents:
A) FUNDAMENTAL THREAT - A structural, long-term risk that materially affects the company's business model, competitive position, or financial health
B) MANAGEABLE NOISE - A temporary, isolated incident that does not fundamentally alter the investment thesis

You MUST analyze:
1. Is the risk CLARIFIED by the search results? What specific information resolves the ambiguity?
2. What is the SPECIFIC IMPACT on the company? (Revenue, margins, reputation, regulatory)
3. Is this issue TEMPORARY (short-term noise) or STRUCTURAL (fundamental threat)?
4. Based on the evidence, what should the REVISED SENTIMENT be?

CRITICAL: Be objective and evidence-based. If the search results do not provide sufficient clarity, state that ambiguity remains.

=== OUTPUT FORMAT (STRICT JSON) ===
{{
    "risk_classification": "FUNDAMENTAL_THREAT" or "MANAGEABLE_NOISE" or "INSUFFICIENT_DATA",
    "detailed_findings": "<3-4 sentences explaining what the investigation revealed, the specific impact, and whether the risk is temporary or structural>",
    "revised_sentiment_score": <float between -1 (very negative) and +1 (very positive)>,
    "is_ambiguity_resolved": <true if conflict is now clear, false if uncertainty remains>,
    "key_evidence": ["<evidence point 1>", "<evidence point 2>", "<evidence point 3>"],
    "confidence_level": "HIGH" or "MEDIUM" or "LOW"
}}

Provide ONLY the JSON output. No additional text, markdown, or explanations.
"""
        
        try:
            # Call LLM
            if llm_callback:
                response = await llm_callback(prompt)
            else:
                response = await self._aask(prompt)
            
            # Parse LLM response
            parsed = self._parse_llm_response(response)
            
            # Log the analysis
            logger.info(f"📊 LLM Analysis Results:")
            logger.info(f"   - Risk Classification: {parsed.get('risk_classification', 'UNKNOWN')}")
            logger.info(f"   - Confidence: {parsed.get('confidence_level', 'UNKNOWN')}")
            logger.info(f"   - Key Evidence: {parsed.get('key_evidence', [])[:2]}")
            
            # Create InvestigationReport
            report = InvestigationReport(
                ticker=ticker,
                detailed_findings=parsed["detailed_findings"],
                revised_sentiment_score=parsed["revised_sentiment_score"],
                is_ambiguity_resolved=parsed["is_ambiguity_resolved"]
            )
            
            return report
            
        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {e}")
            return InvestigationReport(
                ticker=ticker,
                detailed_findings=f"LLM analysis failed: {str(e)}. Unable to assess risk.",
                revised_sentiment_score=0.0,
                is_ambiguity_resolved=False
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
            
            # Validate and normalize fields
            return {
                "risk_classification": data.get("risk_classification", "INSUFFICIENT_DATA"),
                "detailed_findings": data.get("detailed_findings", "Analysis parsing failed"),
                "revised_sentiment_score": self._clamp(float(data.get("revised_sentiment_score", 0.0)), -1.0, 1.0),
                "is_ambiguity_resolved": bool(data.get("is_ambiguity_resolved", False)),
                "key_evidence": data.get("key_evidence", []),
                "confidence_level": data.get("confidence_level", "LOW")
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            return {
                "risk_classification": "PARSE_ERROR",
                "detailed_findings": f"Failed to parse LLM response: {str(e)}",
                "revised_sentiment_score": 0.0,
                "is_ambiguity_resolved": False,
                "key_evidence": [],
                "confidence_level": "LOW"
            }
    
    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp a value between min and max."""
        return max(min_val, min(max_val, value))

