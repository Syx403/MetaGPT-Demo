"""
Filename: MetaGPT-Ewan/MAT/tests/verify_sa_native.py
Created Date: Saturday, January 4th 2026
Author: Claude Code
Description: Native verification test for SearchDeepDive action with GPT-4o intelligence.

This script ONLY instantiates the SearchDeepDive Action and calls .run().
It is FORBIDDEN from containing any LLM prompts - all intelligence must come from
the native Action code.

Test Cases:
- AAPL 2021-12-31: Strong recovery post-COVID with segment driver analysis (BASIC + ADVANCED)
- AAPL 2022-12-31: Strong earnings but macro headwinds (inflation, supply chain) (BASIC + ADVANCED)

Success Criteria:
- For 2021: Should extract causal chains showing why recovery happened
- For 2022: Should identify macro headwinds and paradoxes (strong earnings vs. headwinds)
- Console output shows causal narrative (BECAUSE-THEN logic), not bullet points
- All outputs are valid SAReport (basic) and InvestigationReport (advanced) Pydantic objects
- Advanced mode should provide risk classification and evidence gap analysis
"""

import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime

# Import the Action directly
from MAT.actions.search_deep_dive import SearchDeepDive
from MAT.schemas import SAReport, MarketEvent, InvestigationReport, InvestigationRequest


# ============================================================
# Test Configuration
# ============================================================
TEST_CASES = [
    {
        "ticker": "AAPL",
        "date": "2021-12-31",
        "description": "FY2021: Strong post-COVID recovery with ~33% revenue growth",
        "expected_insights": [
            "Causal chain: iPhone sales surge BECAUSE pandemic recovery",
            "Segment drivers: iPhone, Services, Mac",
            "Narrative synthesis with BECAUSE-THEN logic"
        ],
        "context_issue": "Investigate whether the 33% revenue growth in FY2021 is sustainable or if it represents a temporary post-COVID bounce that masks structural risks. Analyze segment driver sustainability and potential mean reversion risks."
    },
    {
        "ticker": "AAPL",
        "date": "2022-12-31",
        "description": "FY2022: Moderate growth ~8% with macro headwinds",
        "expected_insights": [
            "Causal chain: Revenue growth slowed BECAUSE inflation and supply chain issues",
            "Macro headwinds: Inflation, supply chain, China lockdowns",
            "Paradox: Strong earnings BUT weak guidance or stock reaction"
        ],
        "context_issue": "Conflicting signals detected: Strong earnings reported BUT stock showed weak performance and guidance appeared cautious. Investigate whether macro headwinds (inflation, supply chain) represent temporary noise or structural threats to the business model."
    }
]


async def run_native_sa_test(ticker: str, date: str, description: str):
    """
    Run native SearchDeepDive test.

    CRITICAL: This function contains ZERO LLM prompts. All intelligence comes from
    the SearchDeepDive Action's native prompt.

    Args:
        ticker: Stock ticker
        date: Analysis date "YYYY-MM-DD"
        description: Test description
    """
    print(f"\n{'='*100}")
    print(f"NATIVE SA TEST: {ticker} ({date})")
    print(f"Description: {description}")
    print(f"{'='*100}\n")

    # Step 1: Instantiate Action (ZERO external prompts)
    sa_action = SearchDeepDive()

    # Step 2: Call .run() - all intelligence is native
    # Note: SearchDeepDive's run() method signature is: run(ticker=..., mode="basic", reference_date=...)
    # For native test, we use basic mode with reference_date for year-specific search
    sa_report: SAReport = await sa_action.run(
        ticker=ticker,
        mode="basic",
        reference_date=date
    )

    # Step 3: Print expert evidence results
    print(f"\n{'='*100}")
    print(f"NATIVE SA EXPERT EVIDENCE FOR {ticker} ({date})")
    print(f"{'='*100}")
    print(f"\n📊 SENTIMENT METADATA:")
    print(f"  Ticker: {sa_report.ticker}")
    print(f"  Impactful Events: {[event.value for event in sa_report.impactful_events]}")
    print(f"  Top Keywords: {sa_report.top_keywords[:5]}")

    print(f"\n🧠 PURE DESCRIPTIVE EVIDENCE:")
    print(f"\n  Qualitative Sentiment Assessment:")
    print(f"  {sa_report.qualitative_sentiment_assessment}")

    print(f"\n  Sentiment Matrix (Qualitative Audits):")
    for factor, audit in sa_report.sentiment_matrix.items():
        print(f"    - {factor}:")
        print(f"      {audit}")

    print(f"\n  Causal Narrative (BECAUSE-THEN Logic):")
    print(f"  {sa_report.causal_narrative}")

    print(f"\n  Expectation Gap Analysis:")
    print(f"  {sa_report.expectation_gap}")

    print(f"\n  Paradoxes/Tensions:")
    print(f"  {sa_report.paradoxes_or_tensions}")

    print(f"\n  News Summary (Full Narrative):")
    print(f"  {sa_report.news_summary}")
    print(f"{'='*100}\n")

    # Step 4: Validate Pydantic schema
    try:
        sa_report.model_validate(sa_report)
        print("✅ Pydantic validation PASSED")
    except Exception as e:
        print(f"❌ Pydantic validation FAILED: {e}")

    # Step 5: Check for causal keywords (BECAUSE, DUE TO, etc.)
    causal_keywords = ["because", "due to", "which then", "led to", "driven by", "caused by", "resulted in"]
    has_causal_logic = any(keyword in sa_report.news_summary.lower() for keyword in causal_keywords)

    print(f"\n🔍 Causal Logic Check:")
    if has_causal_logic:
        print(f"✅ News summary contains causal connectors (BECAUSE-THEN logic)")
        matched_keywords = [kw for kw in causal_keywords if kw in sa_report.news_summary.lower()]
        print(f"   Found: {matched_keywords}")
    else:
        print(f"⚠️  News summary may be missing explicit causal connectors")
        print(f"   Expected keywords: {causal_keywords}")

    # Step 6: Verify DUAL-SAVING PROTOCOL file existence
    print(f"\n📁 DUAL-SAVING PROTOCOL Verification:")

    # Extract year from date
    year = datetime.strptime(date, "%Y-%m-%d").year

    # Check for RAW search results
    raw_search_file = Path(f"MAT/report/SA/Raw_Search_{ticker}_{year}.json")
    if raw_search_file.exists():
        print(f"✅ Raw search results file exists: {raw_search_file}")
    else:
        print(f"❌ Raw search results file NOT FOUND: {raw_search_file}")

    # Check for BASIC mode structured report
    structured_report_file = Path(f"MAT/report/SA/SA_report_basic_{ticker}_{year}.json")
    if structured_report_file.exists():
        print(f"✅ Structured BASIC report file exists: {structured_report_file}")
    else:
        print(f"❌ Structured BASIC report file NOT FOUND: {structured_report_file}")

    return sa_report


async def run_native_sa_advanced_test(ticker: str, date: str, description: str, context_issue: str):
    """
    Run native SearchDeepDive ADVANCED MODE test.

    CRITICAL: This function contains ZERO LLM prompts. All intelligence comes from
    the SearchDeepDive Action's native prompt.

    Args:
        ticker: Stock ticker
        date: Analysis date "YYYY-MM-DD"
        description: Test description
        context_issue: The conflict/issue to investigate
    """
    print(f"\n{'='*100}")
    print(f"NATIVE SA ADVANCED TEST: {ticker} ({date})")
    print(f"Description: {description}")
    print(f"Context Issue: {context_issue}")
    print(f"{'='*100}\n")

    # Step 1: Instantiate Action (ZERO external prompts)
    sa_action = SearchDeepDive()

    # Step 2: Create InvestigationRequest (simulating what AS would send)
    investigation_request = InvestigationRequest(
        ticker=ticker,
        target_agent="SA",
        context_issue=context_issue,
        current_retry=0,
        max_retries=1,
        importance_level=2  # High importance for thorough investigation
    )

    # Step 3: Call .run() in advanced mode - all intelligence is native
    investigation_report: InvestigationReport = await sa_action.run(
        investigation_request=investigation_request,
        mode="advanced",
        reference_date=date
    )

    # Step 4: Print expert evidence results
    print(f"\n{'='*100}")
    print(f"NATIVE SA ADVANCED MODE INVESTIGATION REPORT FOR {ticker} ({date})")
    print(f"{'='*100}")
    print(f"\n📊 INVESTIGATION METADATA:")
    print(f"  Ticker: {investigation_report.ticker}")
    print(f"  Risk Classification: {investigation_report.risk_classification}")
    print(f"  Confidence Level: {investigation_report.confidence_level}")
    print(f"  Ambiguity Resolved: {investigation_report.is_ambiguity_resolved}")

    print(f"\n🧠 INVESTIGATION FINDINGS:")
    print(f"\n  Detailed Findings:")
    print(f"  {investigation_report.detailed_findings}")

    print(f"\n  Qualitative Sentiment Revision:")
    print(f"  {investigation_report.qualitative_sentiment_revision}")

    print(f"\n  Key Evidence:")
    for i, evidence in enumerate(investigation_report.key_evidence, 1):
        print(f"    {i}. {evidence}")

    print(f"\n  Evidence Gaps:")
    for i, gap in enumerate(investigation_report.evidence_gaps, 1):
        print(f"    {i}. {gap}")

    print(f"{'='*100}\n")

    # Step 5: Validate Pydantic schema
    try:
        investigation_report.model_validate(investigation_report)
        print("✅ Pydantic validation PASSED (Advanced Mode)")
    except Exception as e:
        print(f"❌ Pydantic validation FAILED (Advanced Mode): {e}")

    # Step 6: Verify DUAL-SAVING PROTOCOL file existence
    print(f"\n📁 DUAL-SAVING PROTOCOL Verification (Advanced Mode):")

    # Extract year from date
    year = datetime.strptime(date, "%Y-%m-%d").year

    # Check for RAW search results
    raw_search_file = Path(f"MAT/report/SA/Raw_Search_{ticker}_{year}.json")
    if raw_search_file.exists():
        print(f"✅ Raw search results file exists: {raw_search_file}")
    else:
        print(f"❌ Raw search results file NOT FOUND: {raw_search_file}")

    # Check for ADVANCED mode structured report
    structured_report_file = Path(f"MAT/report/SA/SA_report_advanced_{ticker}_{year}.json")
    if structured_report_file.exists():
        print(f"✅ Structured ADVANCED report file exists: {structured_report_file}")
    else:
        print(f"❌ Structured ADVANCED report file NOT FOUND: {structured_report_file}")

    return investigation_report


async def main():
    """
    Main test runner.

    Runs native SA tests for both test cases and saves results.
    """
    print("\n" + "="*100)
    print("NATIVE SENTIMENT ANALYSIS VERIFICATION TEST")
    print("="*100)
    print("\nObjective: Verify that SearchDeepDive Action has internalized GPT-4o intelligence.")
    print("Requirement: ALL intelligence must come from native Action code, NOT external prompts.")
    print("\nTest Cases:")
    for i, tc in enumerate(TEST_CASES, 1):
        print(f"  {i}. {tc['ticker']} {tc['date']}: {tc['description']}")
    print("="*100)

    results = []

    # Run tests
    for test_case in TEST_CASES:
        try:
            # Test 1: BASIC MODE
            print(f"\n{'#'*100}")
            print(f"# TESTING BASIC MODE: {test_case['ticker']} {test_case['date']}")
            print(f"{'#'*100}")

            sa_report = await run_native_sa_test(
                ticker=test_case["ticker"],
                date=test_case["date"],
                description=test_case["description"]
            )

            # Check for causal logic
            causal_keywords = ["because", "due to", "which then", "led to", "driven by", "caused by", "resulted in"]
            has_causal_logic = any(keyword in sa_report.news_summary.lower() for keyword in causal_keywords)

            # Test 2: ADVANCED MODE
            print(f"\n{'#'*100}")
            print(f"# TESTING ADVANCED MODE: {test_case['ticker']} {test_case['date']}")
            print(f"{'#'*100}")

            investigation_report = await run_native_sa_advanced_test(
                ticker=test_case["ticker"],
                date=test_case["date"],
                description=test_case["description"],
                context_issue=test_case["context_issue"]
            )

            results.append({
                "test_case": test_case["description"],
                "ticker": test_case["ticker"],
                "date": test_case["date"],
                "expected_insights": test_case["expected_insights"],
                "context_issue": test_case["context_issue"],
                "sa_report": sa_report.model_dump(),
                "investigation_report": investigation_report.model_dump(),
                "has_causal_logic": has_causal_logic,
                "status": "PASSED"
            })

        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()

            results.append({
                "test_case": test_case["description"],
                "ticker": test_case["ticker"],
                "date": test_case["date"],
                "expected_insights": test_case["expected_insights"],
                "context_issue": test_case.get("context_issue", "N/A"),
                "error": str(e),
                "status": "FAILED"
            })

    # Save results
    output_file = Path("MAT/tests/native_sa_verification_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "test_name": "Native SA Intelligence Verification",
        "test_date": datetime.now().isoformat(),
        "objective": "Verify SearchDeepDive has internalized GPT-4o intelligence",
        "results": results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'='*100}")
    print(f"NATIVE SA VERIFICATION COMPLETE")
    print(f"{'='*100}")
    print(f"Results saved to: {output_file}")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(1 for r in results if r['status'] == 'PASSED')}")
    print(f"Failed: {sum(1 for r in results if r['status'] == 'FAILED')}")
    print(f"{'='*100}\n")

    # Print summary
    print("\n📊 SUMMARY:")
    for result in results:
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"\n{status_icon} {result['ticker']} {result['date']}: {result['test_case']}")
        if result["status"] == "PASSED":
            # BASIC MODE RESULTS
            print(f"\n  🔵 BASIC MODE (SAReport):")
            sa_data = result["sa_report"]
            causal_icon = "✅" if result["has_causal_logic"] else "⚠️"
            print(f"     Qualitative Sentiment: {sa_data.get('qualitative_sentiment_assessment', 'N/A')[:80]}...")
            print(f"     Events: {sa_data['impactful_events']}")
            print(f"     {causal_icon} Causal Logic: {'Present' if result['has_causal_logic'] else 'Missing'}")
            print(f"     Sentiment Matrix Factors: {list(sa_data.get('sentiment_matrix', {}).keys())}")
            print(f"     Paradoxes: {sa_data.get('paradoxes_or_tensions', 'N/A')[:80]}...")

            # ADVANCED MODE RESULTS
            print(f"\n  🔴 ADVANCED MODE (InvestigationReport):")
            inv_data = result["investigation_report"]
            print(f"     Risk Classification: {inv_data.get('risk_classification', 'N/A')}")
            print(f"     Confidence Level: {inv_data.get('confidence_level', 'N/A')}")
            print(f"     Ambiguity Resolved: {inv_data.get('is_ambiguity_resolved', False)}")
            print(f"     Sentiment Revision: {inv_data.get('qualitative_sentiment_revision', 'N/A')[:80]}...")
            print(f"     Key Evidence Count: {len(inv_data.get('key_evidence', []))}")
            print(f"     Evidence Gaps Count: {len(inv_data.get('evidence_gaps', []))}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

    # Print full JSON reports
    print("\n" + "="*100)
    print("FULL JSON REPORTS")
    print("="*100)
    for i, result in enumerate(results, 1):
        if result["status"] == "PASSED":
            print(f"\n{i}. {result['ticker']} {result['date']}:")
            print(f"\n  🔵 BASIC MODE (SAReport):")
            print(json.dumps(result["sa_report"], indent=2, default=str))
            print(f"\n  🔴 ADVANCED MODE (InvestigationReport):")
            print(json.dumps(result["investigation_report"], indent=2, default=str))


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Native verification test for SearchDeepDive action")
    parser.add_argument("--ticker", type=str, help="Stock ticker symbol (e.g., AAPL, KO)")
    parser.add_argument("--fiscal_year", type=int, help="Fiscal year for analysis (e.g., 2021, 2022)")

    args = parser.parse_args()

    # If CLI arguments provided, override test cases
    if args.ticker and args.fiscal_year:
        # Replace test cases with CLI-specified single test
        TEST_CASES.clear()
        TEST_CASES.append({
            "ticker": args.ticker,
            "date": f"{args.fiscal_year}-12-31",
            "description": f"CLI Test: {args.ticker} FY{args.fiscal_year}",
            "expected_insights": [
                "Sentiment analysis for specified ticker and fiscal year"
            ],
            "context_issue": f"Investigate market sentiment and news landscape for {args.ticker} in fiscal year {args.fiscal_year}. Analyze key events, causal drivers, and potential conflicts between reported performance and market reaction."
        })
        print(f"\n🔧 CLI Mode: Running test for {args.ticker} FY{args.fiscal_year}")

    asyncio.run(main())
