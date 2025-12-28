"""
Filename: MetaGPT-Ewan/MAT/test_script/test_search_deep_dive.py
Created Date: Sunday, December 29th 2025
Author: Ewan Su
Description: Test and demonstration script for SearchDeepDive action.

Prerequisites:
1. Fill in your API keys in config/config2.yaml:
   - tavily.api_key: Your Tavily API key (get free at https://tavily.com)
   - llm.api_key: Your OpenAI API key
2. Install tavily-python: pip install tavily-python

Usage:
    cd /path/to/MetaGPT-Ewan
    python -m MAT.test_script.test_search_deep_dive
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from metagpt.logs import logger

# Import config loader
from MAT.config_loader import get_config


def setup_logging():
    """Configure logging based on config file."""
    config = get_config()
    log_level = config.get_log_level()
    
    logger.remove()
    logger.add(sys.stderr, level=log_level)


async def test_search_deep_dive():
    """
    Test the SearchDeepDive action with various scenarios.
    """
    from MAT.actions.search_deep_dive import SearchDeepDive
    from MAT.schemas import InvestigationRequest
    
    # Get config and check API key
    config = get_config()
    
    if not config.is_tavily_configured():
        logger.error("❌ Tavily API key not configured!")
        logger.info("")
        logger.info("📝 Please configure your API key in: config/config2.yaml")
        logger.info("   Under the 'tavily:' section, set:")
        logger.info("   api_key: \"your-tavily-api-key-here\"")
        logger.info("")
        logger.info("🔑 Get a free API key at: https://tavily.com")
        return
    
    logger.info("="*80)
    logger.info("🧪 TESTING SEARCH DEEP DIVE ACTION")
    logger.info("="*80)
    
    # Print config status
    config.print_config_status()
    
    # Initialize action (will load API key from config)
    action = SearchDeepDive()
    
    # Test Case 1: NVDA with regulatory concerns
    logger.info("\n" + "="*80)
    logger.info("📋 TEST CASE 1: NVDA - Regulatory Concerns")
    logger.info("="*80)
    
    request1 = InvestigationRequest(
        ticker="NVDA",
        target_agent="SA",
        context_issue="CONFLICT DETECTED: Fundamentals show 35% revenue growth and healthy margins, "
                     "Technicals show BUY signal with RSI=28.5, but Sentiment is NEGATIVE (-0.4) "
                     "due to regulatory concerns and export restrictions to China.",
        current_retry=0,
        max_retries=2,
        importance_level=2  # High importance due to growth
    )
    
    report1 = await action.run(request1)
    
    logger.info(f"\n📊 Result for NVDA:")
    logger.info(f"   Revised Sentiment: {report1.revised_sentiment_score:.2f}")
    logger.info(f"   Ambiguity Resolved: {report1.is_ambiguity_resolved}")
    logger.info(f"   Findings: {report1.detailed_findings}")
    
    # Test Case 2: TSLA with management concerns
    logger.info("\n" + "="*80)
    logger.info("📋 TEST CASE 2: TSLA - Management Focus Concerns")
    logger.info("="*80)
    
    request2 = InvestigationRequest(
        ticker="TSLA",
        target_agent="SA",
        context_issue="CONFLICT DETECTED: Fundamentals show healthy growth metrics, "
                     "Technicals are neutral, but Sentiment is NEGATIVE due to CEO distraction "
                     "with X/Twitter and concerns about management focus on core EV business.",
        current_retry=0,
        max_retries=1,
        importance_level=1  # Normal importance
    )
    
    report2 = await action.run(request2)
    
    logger.info(f"\n📊 Result for TSLA:")
    logger.info(f"   Revised Sentiment: {report2.revised_sentiment_score:.2f}")
    logger.info(f"   Ambiguity Resolved: {report2.is_ambiguity_resolved}")
    logger.info(f"   Findings: {report2.detailed_findings}")
    
    # Test Case 3: AAPL with product cycle concerns
    logger.info("\n" + "="*80)
    logger.info("📋 TEST CASE 3: AAPL - Product Cycle Concerns")
    logger.info("="*80)
    
    request3 = InvestigationRequest(
        ticker="AAPL",
        target_agent="SA",
        context_issue="CONFLICT DETECTED: Fundamentals show stable margins and cash flow, "
                     "Technicals show oversold conditions (RSI=32), but Sentiment is UNCLEAR (0.05) "
                     "due to concerns about iPhone sales in China and AI strategy delay.",
        current_retry=0,
        max_retries=1,
        importance_level=1
    )
    
    report3 = await action.run(request3)
    
    logger.info(f"\n📊 Result for AAPL:")
    logger.info(f"   Revised Sentiment: {report3.revised_sentiment_score:.2f}")
    logger.info(f"   Ambiguity Resolved: {report3.is_ambiguity_resolved}")
    logger.info(f"   Findings: {report3.detailed_findings}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("✅ TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"NVDA: sentiment={report1.revised_sentiment_score:.2f}, resolved={report1.is_ambiguity_resolved}")
    logger.info(f"TSLA: sentiment={report2.revised_sentiment_score:.2f}, resolved={report2.is_ambiguity_resolved}")
    logger.info(f"AAPL: sentiment={report3.revised_sentiment_score:.2f}, resolved={report3.is_ambiguity_resolved}")
    logger.info("="*80)
    logger.info(f"📁 Search results saved to: {action.output_dir.absolute()}")


async def demo_query_engineering():
    """
    Demonstrate the query engineering logic.
    This doesn't require API keys.
    """
    from MAT.actions.search_deep_dive import SearchDeepDive
    
    logger.info("\n" + "="*80)
    logger.info("🔍 QUERY ENGINEERING DEMONSTRATION")
    logger.info("="*80)
    logger.info("This demo shows how search queries are engineered from ticker + context.")
    logger.info("No API key required for this part.\n")
    
    action = SearchDeepDive()
    
    test_cases = [
        ("NVDA", "CFO resignation and management changes"),
        ("TSLA", "CEO distraction with Twitter/X affecting company focus"),
        ("AAPL", "iPhone sales decline in China market"),
        ("AMD", "Data center GPU market share competition with NVIDIA"),
        ("GOOGL", "Antitrust lawsuit and regulatory pressure on advertising"),
    ]
    
    for ticker, context in test_cases:
        query = action._build_investigation_query(ticker, context)
        logger.info(f"\n📌 Ticker: {ticker}")
        logger.info(f"   Context: {context}")
        logger.info(f"   🔎 Generated Query: {query}")
    
    logger.info("\n" + "="*80)


async def check_config():
    """
    Check and display current configuration status.
    """
    config = get_config()
    
    logger.info("")
    logger.info("="*80)
    logger.info("🔧 CONFIGURATION CHECK")
    logger.info("="*80)
    
    config.print_config_status()
    
    if not config.is_tavily_configured():
        logger.warning("")
        logger.warning("⚠️  Tavily API key is not configured!")
        logger.warning("   To run full tests, please edit: config/config2.yaml")
        logger.warning("   And add your Tavily API key under 'tavily:' section")
        logger.warning("")
    
    if not config.is_openai_configured():
        logger.warning("")
        logger.warning("⚠️  OpenAI API key is not configured!")
        logger.warning("   LLM analysis will not work without it.")
        logger.warning("   Please edit: config/config2.yaml")
        logger.warning("   And add your OpenAI API key under 'llm:' section")
        logger.warning("")
    
    return config.is_tavily_configured()


async def main():
    """
    Main entry point for the test script.
    """
    setup_logging()
    
    logger.info("🚀 Starting SearchDeepDive Tests")
    logger.info("")
    
    # Check configuration first
    tavily_ready = await check_config()
    
    # Always show query engineering demo (no API needed)
    await demo_query_engineering()
    
    # Run full tests only if Tavily is configured
    if tavily_ready:
        logger.info("\n✅ Tavily API configured - running full tests...\n")
        await test_search_deep_dive()
    else:
        logger.warning("\n⏭️  Skipping API tests (Tavily not configured)")
        logger.info("")
        logger.info("📝 To enable full tests:")
        logger.info("   1. Open config/config2.yaml")
        logger.info("   2. Set your Tavily API key: tavily.api_key")
        logger.info("   3. Set your OpenAI API key: llm.api_key")
        logger.info("   4. Run this script again")
        logger.info("")


if __name__ == "__main__":
    asyncio.run(main())
