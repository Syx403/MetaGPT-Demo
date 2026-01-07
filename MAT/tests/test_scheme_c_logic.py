"""
Filename: MetaGPT-Ewan/MAT/tests/test_scheme_c_logic.py
Created Date: Thursday, January 2nd 2026
Author: Ewan Su
Description: Standalone integration test for Scheme C (Active Inquiry) logic loop.

This test verifies the complete handshake process between AlphaStrategist and
SentimentAnalyst when conflicts are detected, without calling real APIs.

Scenario: "2022 Bullish but Ambiguous"
- RA: Bullish (high revenue growth, strong margins)
- TA: Bullish (RSI < 30, oversold at BB lower band)
- SA: Unclear sentiment (0.1) with "CFO Resignation Rumors"
- Expected: AS detects conflict → requests investigation → SA clarifies → AS makes final decision

Usage:
    python MAT/tests/test_scheme_c_logic.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from metagpt.schema import Message
from metagpt.logs import logger

from MAT.environment import InvestmentEnvironment
from MAT.roles.research_analyst import ResearchAnalyst
from MAT.roles.technical_analyst import TechnicalAnalyst
from MAT.roles.sentiment_analyst import SentimentAnalyst
from MAT.roles.alpha_strategist import AlphaStrategist
from MAT.actions import (
    StartAnalysis,
    PublishFAReport,
    PublishTAReport,
    PublishSAReport,
    RequestInvestigation,
    PublishInvestigationReport,
    PublishStrategyDecision
)
from MAT.schemas import (
    FAReport,
    TAReport,
    SAReport,
    InvestigationRequest,
    InvestigationReport,
    StrategyDecision,
    SignalIntensity,
    MarketEvent
)


class MockSentimentAnalyst(SentimentAnalyst):
    """
    Mock SentimentAnalyst that returns pre-defined investigation results
    without calling real APIs.
    """

    def __init__(self, **kwargs):
        # Initialize without Tavily to avoid real API calls
        super().__init__(use_tavily=False, **kwargs)
        self._investigation_response = None

    def set_investigation_response(self, response: InvestigationReport):
        """Set the mock investigation response."""
        self._investigation_response = response

    async def _deep_dive_investigation(self, request_msg: Message) -> Message:
        """
        Override to return mock investigation results instead of real API calls.
        """
        import json

        try:
            request_data = json.loads(request_msg.content)
            investigation_req = InvestigationRequest(**request_data)

            ticker = investigation_req.ticker
            context_issue = investigation_req.context_issue

            logger.info(f"\n{'='*70}")
            logger.info(f"🔍 MOCK DEEP DIVE INVESTIGATION for {ticker}")
            logger.info(f"{'='*70}")
            logger.info(f"📋 Context Issue: {context_issue[:100]}...")
            logger.info(f"📊 Importance Level: {investigation_req.importance_level}")
            logger.info(f"🔄 Retry: {investigation_req.current_retry + 1}/{investigation_req.max_retries}")

            # Return pre-configured mock response
            if self._investigation_response is None:
                # Default mock response if not set
                report = InvestigationReport(
                    ticker=ticker,
                    detailed_findings="CFO resignation is for personal reasons. No financial fraud detected. Succession plan in place with experienced replacement.",
                    revised_sentiment_score=0.4,  # Revised from 0.1 to 0.4 (more positive)
                    is_ambiguity_resolved=True
                )
            else:
                report = self._investigation_response

            logger.info(f"✅ Mock Investigation Complete:")
            logger.info(f"   - Revised Sentiment: {report.revised_sentiment_score:.2f}")
            logger.info(f"   - Ambiguity Resolved: {report.is_ambiguity_resolved}")
            logger.info(f"   - Findings: {report.detailed_findings[:100]}...")
            logger.info(f"{'='*70}\n")

            # Publish investigation report (not async)
            return self.publish_message(
                report=report,
                cause_by=PublishInvestigationReport
            )

        except Exception as e:
            logger.error(f"❌ Mock investigation failed: {e}")
            import traceback
            traceback.print_exc()
            raise


async def test_scheme_c_conflict_resolution():
    """
    Test the complete Scheme C (Active Inquiry) workflow.

    This test validates:
    1. AS detects conflict between bullish FA/TA and unclear SA
    2. AS publishes InvestigationRequest
    3. SA observes request and publishes InvestigationReport
    4. AS observes investigation and makes final decision
    """
    logger.info("\n" + "="*80)
    logger.info("🧪 SCHEME C INTEGRATION TEST: Active Inquiry Logic Loop")
    logger.info("="*80)
    logger.info("Scenario: 2022 Bullish but Ambiguous (AAPL)")
    logger.info("="*80 + "\n")

    # Step 0: Setup environment and agents
    logger.info("📝 Step 0: Setting up Mock Environment")
    logger.info("-" * 70)

    env = InvestmentEnvironment()
    env.set_ticker("AAPL")

    # Create mock sentiment analyst (no real API calls)
    sa = MockSentimentAnalyst()
    sa.set_env(env)
    sa.set_ticker("AAPL")

    # Create alpha strategist
    as_agent = AlphaStrategist()
    as_agent.set_env(env)
    as_agent.set_ticker("AAPL")

    logger.info("✅ Environment initialized with AAPL")
    logger.info(f"✅ Mock SentimentAnalyst ready (no API calls)")
    logger.info(f"✅ AlphaStrategist ready with Scheme C logic\n")

    # Step 1: Publish bullish FA and TA reports
    logger.info("📝 Step 1: Publishing Bullish FA and TA Reports")
    logger.info("-" * 70)

    fa_report = FAReport(
        ticker="AAPL",
        revenue_growth_yoy=0.35,  # 35% growth (very bullish)
        gross_margin=0.42,        # Strong margins
        fcf_growth=0.28,          # Strong cash flow
        guidance_sentiment=0.8,   # Positive guidance
        key_risks=["Supply chain"],
        is_growth_healthy=True    # BULLISH
    )

    ta_report = TAReport(
        ticker="AAPL",
        rsi_14=28.0,              # Oversold (< 30)
        bb_lower_touch=True,      # At lower Bollinger Band
        price_to_ma200_dist=-0.15, # 15% below 200-day MA
        volatility_atr=2.3,
        technical_signal=SignalIntensity.STRONG_BUY  # BULLISH
    )

    # Update environment and publish
    env.update_fa_report(fa_report)
    env.update_ta_report(ta_report)

    fa_msg = Message(content=fa_report.model_dump_json(), cause_by=PublishFAReport)
    ta_msg = Message(content=ta_report.model_dump_json(), cause_by=PublishTAReport)

    env.publish_message(fa_msg)
    env.publish_message(ta_msg)

    logger.info(f"📊 FA Report: revenue_growth={fa_report.revenue_growth_yoy:.1%}, healthy={fa_report.is_growth_healthy}")
    logger.info(f"📈 TA Report: signal={ta_report.technical_signal.value}, RSI={ta_report.rsi_14:.1f}")
    logger.info("✅ Bullish fundamentals and technicals published\n")

    # Step 2: Publish unclear SA report (conflict trigger)
    logger.info("📝 Step 2: Publishing Unclear SA Report (Conflict Trigger)")
    logger.info("-" * 70)

    sa_report = SAReport(
        ticker="AAPL",
        sentiment_score=0.05,     # UNCLEAR (< 0.1 to trigger conflict)
        impactful_events=[MarketEvent.REGULATORY_ACTION],
        top_keywords=["CFO", "resignation", "rumors", "uncertainty"],
        news_summary="CFO Resignation Rumors causing market uncertainty. Details unclear."
    )

    env.update_sa_report(sa_report)
    sa_msg = Message(content=sa_report.model_dump_json(), cause_by=PublishSAReport)
    env.publish_message(sa_msg)

    logger.info(f"📰 SA Report: sentiment={sa_report.sentiment_score:.2f} (UNCLEAR)")
    logger.info(f"📰 Keywords: {sa_report.top_keywords}")
    logger.info(f"📰 Summary: {sa_report.news_summary}")
    logger.info("⚠️  CONFLICT: Bullish FA/TA vs Unclear SA\n")

    # Step 3: Trigger AlphaStrategist to detect conflict
    logger.info("📝 Step 3: AlphaStrategist Detects Conflict")
    logger.info("-" * 70)

    # In MetaGPT, we need to trigger _observe() first, then _act()
    # The _observe() method fills rc.news from the environment
    await as_agent._observe()

    # Now trigger AS._act() to process messages
    as_result = await as_agent._act()

    if as_result is None:
        logger.error("❌ TEST FAILED: AlphaStrategist did not produce any result")
        logger.error("Debug: rc.news is empty or _act() returned None")
        return False

    # Parse the result
    import json
    result_content = json.loads(as_result.content)

    # Check if it's an InvestigationRequest
    if "target_agent" in result_content:
        investigation_req = InvestigationRequest(**result_content)
        logger.info(f"✅ CONFLICT DETECTED!")
        logger.info(f"📤 InvestigationRequest Published:")
        logger.info(f"   - Target: {investigation_req.target_agent}")
        logger.info(f"   - Context: {investigation_req.context_issue[:100]}...")
        logger.info(f"   - Importance: {investigation_req.importance_level} (1=Normal, 2=High)")
        logger.info(f"   - Max Retries: {investigation_req.max_retries}")

        # Verify importance level logic (35% revenue growth should be HIGH)
        assert investigation_req.importance_level == 2, "Expected importance_level=2 for 35% revenue growth"
        assert investigation_req.max_retries == 2, "Expected max_retries=2 for high importance"
        logger.info("✅ Importance level correctly calculated (HIGH)\n")

    else:
        logger.error("❌ TEST FAILED: Expected InvestigationRequest but got StrategyDecision")
        return False

    # Step 4: SentimentAnalyst responds to investigation
    logger.info("📝 Step 4: SentimentAnalyst Responds to Investigation")
    logger.info("-" * 70)

    # Set mock investigation response
    mock_investigation = InvestigationReport(
        ticker="AAPL",
        detailed_findings="Deep dive reveals CFO resignation is for personal reasons (retirement). No financial fraud or mismanagement. Succession plan in place with experienced internal candidate (15 years at company). Board confident in smooth transition.",
        revised_sentiment_score=0.4,  # Revised from 0.1 to 0.4 (more positive after clarification)
        is_ambiguity_resolved=True
    )
    sa.set_investigation_response(mock_investigation)

    # Trigger SA to observe and process the investigation request
    await sa._observe()
    sa_result = await sa._act()

    if sa_result is None:
        logger.error("❌ TEST FAILED: SentimentAnalyst did not respond to investigation")
        return False

    # Parse SA result
    sa_result_content = json.loads(sa_result.content)
    inv_report = InvestigationReport(**sa_result_content)

    logger.info(f"✅ Investigation Response Published:")
    logger.info(f"   - Revised Sentiment: {inv_report.revised_sentiment_score:.2f} (was 0.1)")
    logger.info(f"   - Ambiguity Resolved: {inv_report.is_ambiguity_resolved}")
    logger.info(f"   - Findings: {inv_report.detailed_findings[:150]}...")
    logger.info("✅ Handshake 1→2 Complete: AS → SA → AS\n")

    # Step 5: AlphaStrategist makes final decision
    logger.info("📝 Step 5: AlphaStrategist Makes Final Decision")
    logger.info("-" * 70)

    # The investigation report updates the SA data internally in AS's _process_message
    # We need to trigger AS to observe the InvestigationReport message and process it

    # Trigger AS to observe new messages (it will see the InvestigationReport)
    await as_agent._observe()
    final_result = await as_agent._act()

    if final_result is None:
        logger.error("❌ TEST FAILED: AlphaStrategist did not make final decision")
        return False

    # Parse final result
    final_content = json.loads(final_result.content)

    # Check if it's a StrategyDecision
    if "final_action" in final_content:
        decision = StrategyDecision(**final_content)
        logger.info(f"✅ FINAL DECISION Published:")
        logger.info(f"   - Action: {decision.final_action.value}")
        logger.info(f"   - Confidence: {decision.confidence_score:.1f}%")
        logger.info(f"   - Module: {decision.suggested_module}")
        logger.info(f"   - Logic Chain:")
        for i, step in enumerate(decision.logic_chain, 1):
            logger.info(f"      {i}. {step}")
        logger.info(f"   - Risk Notes: {decision.risk_notes}")

        # Verify final decision makes sense
        # With bullish FA/TA and now resolved SA (0.4), should be BUY or STRONG_BUY
        assert decision.final_action in [SignalIntensity.BUY, SignalIntensity.STRONG_BUY], \
            f"Expected BUY/STRONG_BUY but got {decision.final_action.value}"

        logger.info("✅ Handshake Complete: AS → SA → AS → Final Decision\n")

    else:
        logger.error("❌ TEST FAILED: Expected StrategyDecision but got InvestigationRequest again")
        return False

    # Final verification
    logger.info("="*80)
    logger.info("📊 VERIFICATION SUMMARY")
    logger.info("="*80)
    logger.info("✅ Step 1: Published bullish FA and TA reports")
    logger.info("✅ Step 2: Published unclear SA report (conflict trigger)")
    logger.info("✅ Step 3: AS detected conflict and requested investigation")
    logger.info(f"   - Importance level: {investigation_req.importance_level} (HIGH)")
    logger.info(f"   - Max retries: {investigation_req.max_retries}")
    logger.info("✅ Step 4: SA responded with clarified investigation")
    logger.info(f"   - Revised sentiment: {inv_report.revised_sentiment_score:.2f}")
    logger.info(f"   - Ambiguity resolved: {inv_report.is_ambiguity_resolved}")
    logger.info("✅ Step 5: AS made final decision based on investigation")
    logger.info(f"   - Final action: {decision.final_action.value}")
    logger.info(f"   - Confidence: {decision.confidence_score:.1f}%")
    logger.info("="*80)
    logger.info("🎉 SCHEME C INTEGRATION TEST PASSED!")
    logger.info("="*80 + "\n")

    return True


async def test_scheme_c_no_conflict():
    """
    Test that AS makes direct decision when no conflict exists.

    This validates that AS doesn't unnecessarily request investigations
    when all signals are aligned.
    """
    logger.info("\n" + "="*80)
    logger.info("🧪 SCHEME C TEST: No Conflict Scenario")
    logger.info("="*80)
    logger.info("Scenario: All signals aligned (bullish)")
    logger.info("="*80 + "\n")

    # Setup
    env = InvestmentEnvironment()
    env.set_ticker("MSFT")

    as_agent = AlphaStrategist()
    as_agent.set_env(env)
    as_agent.set_ticker("MSFT")

    # Publish aligned reports (all bullish)
    fa_report = FAReport(
        ticker="MSFT",
        revenue_growth_yoy=0.25,
        gross_margin=0.40,
        fcf_growth=0.20,
        guidance_sentiment=0.7,
        key_risks=["Competition"],
        is_growth_healthy=True
    )

    ta_report = TAReport(
        ticker="MSFT",
        rsi_14=35.0,
        bb_lower_touch=True,
        price_to_ma200_dist=-0.10,
        volatility_atr=2.5,
        technical_signal=SignalIntensity.BUY
    )

    sa_report = SAReport(
        ticker="MSFT",
        sentiment_score=0.6,  # POSITIVE (aligned with FA/TA)
        impactful_events=[MarketEvent.PRODUCT_LAUNCH],
        top_keywords=["growth", "innovation", "expansion"],
        news_summary="Positive news about product launches and market expansion."
    )

    env.update_fa_report(fa_report)
    env.update_ta_report(ta_report)
    env.update_sa_report(sa_report)

    env.publish_message(Message(content=fa_report.model_dump_json(), cause_by=PublishFAReport))
    env.publish_message(Message(content=ta_report.model_dump_json(), cause_by=PublishTAReport))
    env.publish_message(Message(content=sa_report.model_dump_json(), cause_by=PublishSAReport))

    logger.info(f"📊 FA: Bullish (revenue_growth={fa_report.revenue_growth_yoy:.1%})")
    logger.info(f"📈 TA: {ta_report.technical_signal.value}")
    logger.info(f"📰 SA: Positive (sentiment={sa_report.sentiment_score:.2f})")
    logger.info("✅ All signals aligned - no conflict\n")

    # Trigger AS to observe and act
    await as_agent._observe()
    result = await as_agent._act()

    if result is None:
        logger.error("❌ TEST FAILED: AS did not produce result")
        return False

    # Parse result
    import json
    content = json.loads(result.content)

    # Should be StrategyDecision, NOT InvestigationRequest
    if "final_action" in content:
        decision = StrategyDecision(**content)
        logger.info(f"✅ Direct Decision Made (No Investigation Needed):")
        logger.info(f"   - Action: {decision.final_action.value}")
        logger.info(f"   - Confidence: {decision.confidence_score:.1f}%")
        logger.info("✅ TEST PASSED: AS correctly skipped investigation for aligned signals\n")
        return True
    else:
        logger.error("❌ TEST FAILED: AS requested investigation when signals were aligned")
        return False


async def main():
    """Run all Scheme C integration tests."""
    results = {}

    # Test 1: Conflict resolution workflow
    results["Scheme C: Conflict Resolution"] = await test_scheme_c_conflict_resolution()

    # Test 2: No conflict scenario
    results["Scheme C: No Conflict"] = await test_scheme_c_no_conflict()

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")

    logger.info("="*80)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("="*80)

    if passed == total:
        logger.info("\n🎉 ALL SCHEME C TESTS PASSED!")
        logger.info("\nKey Validations:")
        logger.info("✅ Conflict detection logic works correctly")
        logger.info("✅ Importance level calculation based on fundamentals")
        logger.info("✅ AS → SA → AS handshake completes successfully")
        logger.info("✅ Investigation resolves ambiguity")
        logger.info("✅ Final decision incorporates investigation findings")
        logger.info("✅ No unnecessary investigations when signals align")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
