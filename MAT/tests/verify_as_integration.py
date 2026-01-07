"""
Filename: MetaGPT-Ewan/MAT/tests/verify_as_integration.py
Created Date: Tuesday, January 7th 2026
Author: Claude Code
Description: Static integration test for Alpha Strategist (AS) decision engine.

This script performs evidence audit and workflow simulation using pre-generated reports.
It verifies the AS engine's ability to:
1. Extract precise metrics from JSON reports
2. Detect conflicts between multi-agent reports
3. Synthesize final trading decisions with proper schema compliance

USAGE:
    # Test with default ticker and fiscal year (KO 2021)
    python MAT/tests/verify_as_integration.py

    # Test with specific ticker and fiscal year
    python MAT/tests/verify_as_integration.py --ticker AAPL --fiscal_year 2022

CRITICAL REQUIREMENTS:
- Pure local operation (NO RAG, yfinance, or News API calls)
- Automatic report discovery from MAT/report/ directories
- Evidence audit logging BEFORE LLM calls
- Schema-compliant output (StrategyDecision)
"""

import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime

# Import Actions
from MAT.actions.synthesize_strategy import AnalyzeConflict, SynthesizeDecision

# Import Schemas
from MAT.schemas import FAReport, TAReport, SAReport, InvestigationReport, StrategyDecision


def discover_reports(ticker: str, fiscal_year: int) -> dict:
    """
    Automatically discover pre-generated reports for the specified ticker and fiscal year.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "KO")
        fiscal_year: Fiscal year (e.g., 2021, 2022)

    Returns:
        Dictionary with file paths:
        {
            "ra_report": Path,
            "ta_report": Path,
            "sa_basic_report": Path,
            "sa_advanced_report": Path or None
        }
    """
    print(f"\n{'='*100}")
    print(f"DISCOVERING REPORTS FOR {ticker} (FY{fiscal_year})")
    print(f"{'='*100}\n")

    reports = {
        "ra_report": Path(f"MAT/report/RA/RA_report_{ticker}_{fiscal_year}.json"),
        "ta_report": Path(f"MAT/report/TA/TA_report_{ticker}_{fiscal_year}.json"),
        "sa_basic_report": Path(f"MAT/report/SA/SA_report_basic_{ticker}_{fiscal_year}.json"),
        "sa_advanced_report": Path(f"MAT/report/SA/SA_report_advanced_{ticker}_{fiscal_year}.json")
    }

    # Check which reports exist
    for report_name, report_path in reports.items():
        if report_path.exists():
            print(f"✅ Found: {report_path}")
        else:
            if report_name == "sa_advanced_report":
                print(f"⚠️  Not Found (Optional): {report_path}")
                reports[report_name] = None
            else:
                print(f"❌ Missing Required Report: {report_path}")
                raise FileNotFoundError(f"Required report not found: {report_path}")

    print(f"\n{'='*100}\n")
    return reports


def load_reports(report_paths: dict) -> dict:
    """
    Load JSON reports into Pydantic models.

    Args:
        report_paths: Dictionary with file paths from discover_reports()

    Returns:
        Dictionary with loaded Pydantic objects:
        {
            "ra": FAReport,
            "ta": TAReport,
            "sa": SAReport,
            "sa_adv": InvestigationReport or None
        }
    """
    print(f"{'='*100}")
    print(f"LOADING REPORTS INTO PYDANTIC MODELS")
    print(f"{'='*100}\n")

    # Load RA Report
    with open(report_paths["ra_report"], 'r', encoding='utf-8') as f:
        ra_data = json.load(f)
        ra_report = FAReport(**ra_data)
        print(f"✅ RA Report loaded: {ra_report.ticker}")

    # Load TA Report
    with open(report_paths["ta_report"], 'r', encoding='utf-8') as f:
        ta_data = json.load(f)
        ta_report = TAReport(**ta_data)
        print(f"✅ TA Report loaded: {ta_report.ticker}")

    # Load SA Basic Report
    with open(report_paths["sa_basic_report"], 'r', encoding='utf-8') as f:
        sa_data = json.load(f)

        # Fix MarketEvent enum serialization issue (if present)
        # SearchDeepDive may save "MarketEvent.EARNINGS_CALL" instead of "EARNINGS_CALL"
        if "impactful_events" in sa_data:
            fixed_events = []
            for event in sa_data["impactful_events"]:
                if isinstance(event, str) and event.startswith("MarketEvent."):
                    # Extract enum value: "MarketEvent.EARNINGS_CALL" -> "EARNINGS_CALL"
                    fixed_events.append(event.split(".")[-1])
                else:
                    fixed_events.append(event)
            sa_data["impactful_events"] = fixed_events

        sa_report = SAReport(**sa_data)
        print(f"✅ SA Basic Report loaded: {sa_report.ticker}")

    # Load SA Advanced Report (if exists)
    sa_adv_report = None
    if report_paths["sa_advanced_report"] and report_paths["sa_advanced_report"].exists():
        with open(report_paths["sa_advanced_report"], 'r', encoding='utf-8') as f:
            sa_adv_data = json.load(f)
            sa_adv_report = InvestigationReport(**sa_adv_data)
            print(f"✅ SA Advanced Report loaded: {sa_adv_report.ticker}")
    else:
        print(f"⚠️  SA Advanced Report not available (will skip advanced mode)")

    print(f"\n{'='*100}\n")

    return {
        "ra": ra_report,
        "ta": ta_report,
        "sa": sa_report,
        "sa_adv": sa_adv_report
    }


def print_evidence_audit(reports: dict, ticker: str, fiscal_year: int):
    """
    Print all extracted indicators for manual inspection BEFORE calling LLM.

    This function provides full visibility into the metrics that will be injected
    into the LLM prompts, enabling manual verification of data extraction correctness.

    Args:
        reports: Dictionary with loaded Pydantic objects
        ticker: Stock ticker symbol
        fiscal_year: Fiscal year
    """
    print(f"\n{'='*100}")
    print(f"EVIDENCE AUDIT: EXTRACTED INDICATORS FOR {ticker} (FY{fiscal_year})")
    print(f"{'='*100}\n")

    ra = reports["ra"]
    ta = reports["ta"]
    sa = reports["sa"]
    sa_adv = reports.get("sa_adv")

    # TA Metrics
    print(f"📊 TECHNICAL ANALYSIS (TA) METRICS:")
    print(f"   - ta_market_regime: {ta.market_regime}")
    print(f"   - ta_indicator_tension: {ta.indicator_tension_analysis}")
    print(f"   - ta_dead_cat_vs_value: {ta.dead_cat_vs_value}")
    print()

    # RA Metrics
    print(f"💰 RESEARCH ANALYST (RA) METRICS:")
    print(f"   - ra_revenue_value: {ra.revenue_performance.value}")
    print(f"   - ra_revenue_analysis: {ra.revenue_performance.analysis[:100]}...")
    print(f"   - ra_profit_value: {ra.profitability_audit.value}")
    print(f"   - ra_profit_analysis: {ra.profitability_audit.analysis[:100]}...")
    print(f"   - ra_cash_value: {ra.cash_flow_stability.value}")
    print(f"   - ra_cash_analysis: {ra.cash_flow_stability.analysis[:100]}...")
    print(f"   - ra_guidance: {ra.management_guidance_audit[:100]}...")
    print(f"   - ra_risks: {len(ra.key_risks_evidence)} risks identified")

    # Display full ra_risks content (strip metadata after second "|")
    if ra.key_risks_evidence:
        for i, risk in enumerate(ra.key_risks_evidence, 1):
            # Parse risk string and keep only first two parts (title | impact)
            risk_parts = risk.split("|")
            if len(risk_parts) >= 2:
                risk_display = f"{risk_parts[0].strip()} | {risk_parts[1].strip()}"
            else:
                risk_display = risk
            print(f"      {i}. {risk_display[:120]}..." if len(risk_display) > 120 else f"      {i}. {risk_display}")
    print()

    # SA Metrics
    print(f"📰 SENTIMENT ANALYST (SA) METRICS:")
    print(f"   - sa_news_summary: {sa.news_summary[:100]}...")
    print(f"   - sa_sentiment_assessment: {sa.qualitative_sentiment_assessment[:100]}...")
    print(f"   - sa_product_demand: {sa.sentiment_matrix.get('Product_Demand', 'N/A')[:80]}...")
    print(f"   - sa_macro_env: {sa.sentiment_matrix.get('Macro_Environment', 'N/A')[:80]}...")
    print(f"   - sa_mgmt_conf: {sa.sentiment_matrix.get('Management_Confidence', 'N/A')[:80]}...")
    print(f"   - sa_comp_pos: {sa.sentiment_matrix.get('Competitive_Position', 'N/A')[:80]}...")
    print(f"   - sa_causal_narrative: {sa.causal_narrative[:100]}...")
    print(f"   - sa_expectation_gap: {sa.expectation_gap[:100]}...")
    print(f"   - sa_tensions: {sa.paradoxes_or_tensions[:100]}...")
    print()

    # SA-Advanced Metrics
    if sa_adv:
        print(f"🔍 SENTIMENT ANALYST ADVANCED (SA-ADV) METRICS:")
        print(f"   - sa_adv_findings: {sa_adv.detailed_findings[:100]}...")
        print(f"   - sa_adv_resolved: {sa_adv.is_ambiguity_resolved}")
        print(f"   - sa_adv_risk_class: {sa_adv.risk_classification}")
        print(f"   - sa_adv_revision: {sa_adv.qualitative_sentiment_revision[:100]}...")
        print(f"   - sa_adv_confidence: {sa_adv.confidence_level}")
        print(f"   - sa_adv_gaps: {len(sa_adv.evidence_gaps)} evidence gaps")

        # Display full sa_adv_gaps content
        if sa_adv.evidence_gaps:
            for i, gap in enumerate(sa_adv.evidence_gaps, 1):
                gap_display = gap[:120] + "..." if len(gap) > 120 else gap
                print(f"      {i}. {gap_display}")

        # Display full sa_adv_evidence content
        print(f"   - sa_adv_evidence: {len(sa_adv.key_evidence)} key evidence items")
        if sa_adv.key_evidence:
            for i, evidence in enumerate(sa_adv.key_evidence, 1):
                evidence_display = evidence[:120] + "..." if len(evidence) > 120 else evidence
                print(f"      {i}. {evidence_display}")
        print()
    else:
        print(f"🔍 SENTIMENT ANALYST ADVANCED (SA-ADV) METRICS:")
        print(f"   - N/A - Advanced investigation not triggered")
        print()

    print(f"{'='*100}\n")


async def run_as_workflow(ticker: str, fiscal_year: int):
    """
    Run the complete AS decision workflow.

    Workflow Steps:
    1. Discover pre-generated reports
    2. Load reports into Pydantic models
    3. Print evidence audit (BEFORE LLM calls)
    4. Run AnalyzeConflict action
    5. If conflict detected, verify SA-Advanced report exists
    6. Run SynthesizeDecision action
    7. Print final JSON decision

    Args:
        ticker: Stock ticker symbol
        fiscal_year: Fiscal year for analysis
    """
    print(f"\n{'#'*100}")
    print(f"# ALPHA STRATEGIST (AS) STATIC INTEGRATION TEST")
    print(f"# Ticker: {ticker} | Fiscal Year: {fiscal_year}")
    print(f"{'#'*100}\n")

    # Step 1: Discover reports
    try:
        report_paths = discover_reports(ticker, fiscal_year)
    except FileNotFoundError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print(f"Please run the following tests first to generate required reports:")
        print(f"  - python MAT/tests/verify_ra_native.py --ticker {ticker} --fiscal_year {fiscal_year}")
        print(f"  - python MAT/tests/verify_ta_native.py --ticker {ticker} --fiscal_year {fiscal_year}")
        print(f"  - python MAT/tests/verify_sa_native.py --ticker {ticker} --fiscal_year {fiscal_year}")
        return

    # Step 2: Load reports into Pydantic models
    reports = load_reports(report_paths)

    # Step 3: Evidence Audit (BEFORE LLM calls)
    print_evidence_audit(reports, ticker, fiscal_year)

    # Step 4: Run AnalyzeConflict
    print(f"{'='*100}")
    print(f"STEP 1: CONFLICT ANALYSIS")
    print(f"{'='*100}\n")

    analyze_conflict = AnalyzeConflict()
    conflict_result = await analyze_conflict.run(
        ticker=ticker,
        ra=reports["ra"],
        ta=reports["ta"],
        sa=reports["sa"]
    )

    has_conflict = conflict_result["has_conflict"]
    context_issue = conflict_result["context_issue"]

    print(f"Conflict Detected: {has_conflict}")
    print(f"Context Issue: {context_issue}\n")

    # Step 5: If conflict detected, verify SA-Advanced report exists
    sa_adv_for_synthesis = None
    if has_conflict:
        print(f"⚠️  Conflict detected - checking for SA-Advanced report...")
        if reports["sa_adv"]:
            print(f"✅ SA-Advanced report found - will use for conflict resolution\n")
            sa_adv_for_synthesis = reports["sa_adv"]
        else:
            print(f"❌ WARNING: Conflict detected but SA-Advanced report not available")
            print(f"   Decision synthesis will proceed without advanced investigation\n")

    # Step 6: Run SynthesizeDecision
    print(f"{'='*100}")
    print(f"STEP 2: DECISION SYNTHESIS")
    print(f"{'='*100}\n")

    synthesize_decision = SynthesizeDecision()
    strategy_decision = await synthesize_decision.run(
        ticker=ticker,
        ra=reports["ra"],
        ta=reports["ta"],
        sa=reports["sa"],
        sa_adv=sa_adv_for_synthesis,
        conflict_issue=context_issue if has_conflict else None
    )

    # Step 7: Print final JSON decision
    print(f"\n{'='*100}")
    print(f"FINAL STRATEGY DECISION")
    print(f"{'='*100}\n")

    decision_json = strategy_decision.model_dump_json(indent=2)
    print(decision_json)

    # Save decision to file
    output_dir = Path("MAT/report/AS")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"AS_decision_{ticker}_{fiscal_year}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(decision_json)

    print(f"\n📁 Decision saved to: {output_file}")
    print(f"\n{'='*100}")
    print(f"TEST COMPLETE")
    print(f"{'='*100}\n")

    # Print summary
    print(f"📊 SUMMARY:")
    print(f"   Ticker: {strategy_decision.ticker}")
    print(f"   Signal: {strategy_decision.final_action.value}")
    print(f"   Confidence: {strategy_decision.confidence_score:.1f}%")
    print(f"   Module: {strategy_decision.suggested_module}")
    print(f"   Conflict Detected: {has_conflict}")
    print(f"   Summary: {strategy_decision.decision_summary}")
    print()


def main():
    """
    Main test runner with command-line argument support.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Static integration test for Alpha Strategist (AS) decision engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default ticker and fiscal year (KO 2021)
  python MAT/tests/verify_as_integration.py

  # Test with specific ticker and fiscal year
  python MAT/tests/verify_as_integration.py --ticker AAPL --fiscal_year 2022
  python MAT/tests/verify_as_integration.py --ticker KO --fiscal_year 2021
        """
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="KO",
        help="Stock ticker symbol (default: KO)"
    )
    parser.add_argument(
        "--fiscal_year",
        type=int,
        default=2021,
        help="Fiscal year for analysis (default: 2021)"
    )

    args = parser.parse_args()

    # Run AS workflow
    asyncio.run(run_as_workflow(args.ticker, args.fiscal_year))


if __name__ == "__main__":
    main()
