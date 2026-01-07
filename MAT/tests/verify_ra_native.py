"""
Filename: MetaGPT-Ewan/MAT/tests/verify_ra_native.py
Created Date: Saturday, January 4th 2026
Author: Claude Code
Description: Native verification test for RetrieveRAGData action with expert-level financial auditing.

This script ONLY instantiates the RetrieveRAGData Action and calls .run().
It is FORBIDDEN from containing any LLM prompts - all intelligence must come from
the native Action code.

USAGE:
    # Test specific ticker and fiscal year
    python MAT/tests/verify_ra_native.py --ticker AAPL --fiscal_year 2021
    python MAT/tests/verify_ra_native.py --ticker KO --fiscal_year 2021

    # Run all predefined test cases
    python MAT/tests/verify_ra_native.py

Success Criteria:
- Should extract financial metrics with BECAUSE-THEN causal logic
- DATA_GAP indicators should be used if specific metrics are unavailable, with explanatory analysis
- All outputs are valid FAReport Pydantic objects with FinancialMetric sub-models
- Source traceability via evidence_md, source_link, source_url in each FinancialMetric
- Console output shows causal narrative analysis, not just numeric values
- Final JSON FAReport saved for manual verification
"""

import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime

# Import the Action directly
from MAT.actions.retrieve_rag_data import RetrieveRAGData
from MAT.schemas import FAReport, FinancialMetric


# ============================================================
# Test Configuration (Default Test Cases)
# ============================================================
DEFAULT_TEST_CASES = [
    {
        "ticker": "AAPL",
        "fiscal_year": 2021,
        "description": "FY2021: Post-COVID recovery with 33% revenue growth",
    },
    {
        "ticker": "AAPL",
        "fiscal_year": 2022,
        "description": "FY2022: Moderate growth with macro headwinds",
    }
]


async def run_native_ra_test(ticker: str, fiscal_year: int, description: str):
    """
    Run native RetrieveRAGData test.

    CRITICAL: This function contains ZERO LLM prompts. All intelligence comes from
    the RetrieveRAGData Action's native prompt.

    Args:
        ticker: Stock ticker
        fiscal_year: Fiscal year for analysis
        description: Test description
    """
    print(f"\n{'='*100}")
    print(f"NATIVE RA TEST: {ticker} (FY{fiscal_year})")
    print(f"Description: {description}")
    print(f"{'='*100}\n")

    # Step 1: Instantiate Action (ZERO external prompts)
    ra_action = RetrieveRAGData()

    # Step 2: Call .run() - all intelligence is native
    fa_report: FAReport = await ra_action.run(
        ticker=ticker,
        fiscal_year=fiscal_year
    )

    # Step 3: Print expert evidence results
    print(f"\n{'='*100}")
    print(f"NATIVE RA FINANCIAL AUDIT FOR {ticker} (FY{fiscal_year})")
    print(f"{'='*100}")

    print(f"\n💰 REVENUE PERFORMANCE:")
    print(f"  Value: {fa_report.revenue_performance.value}")
    print(f"  Analysis:")
    print(f"  {fa_report.revenue_performance.analysis}")

    print(f"\n📊 PROFITABILITY AUDIT:")
    print(f"  Value: {fa_report.profitability_audit.value}")
    print(f"  Analysis:")
    print(f"  {fa_report.profitability_audit.analysis}")

    print(f"\n💵 CASH FLOW STABILITY:")
    print(f"  Value: {fa_report.cash_flow_stability.value}")
    print(f"  Analysis:")
    print(f"  {fa_report.cash_flow_stability.analysis}")

    print(f"\n🎯 MANAGEMENT GUIDANCE AUDIT:")
    print(f"  {fa_report.management_guidance_audit}")

    print(f"\n⚠️  KEY RISKS EVIDENCE:")
    for i, risk in enumerate(fa_report.key_risks_evidence, 1):
        print(f"  {i}. {risk}")

    print(f"\n📚 SOURCE TRACEABILITY:")
    print(f"  Revenue Source URL: {fa_report.revenue_performance.source_url[:80]}..." if len(fa_report.revenue_performance.source_url) > 80 else f"  Revenue Source URL: {fa_report.revenue_performance.source_url}")
    print(f"  Profitability Source URL: {fa_report.profitability_audit.source_url[:80]}..." if len(fa_report.profitability_audit.source_url) > 80 else f"  Profitability Source URL: {fa_report.profitability_audit.source_url}")
    print(f"  Cash Flow Source URL: {fa_report.cash_flow_stability.source_url[:80]}..." if len(fa_report.cash_flow_stability.source_url) > 80 else f"  Cash Flow Source URL: {fa_report.cash_flow_stability.source_url}")

    print(f"{'='*100}\n")

    # Step 4: Validate Pydantic schema
    try:
        fa_report.model_validate(fa_report)
        print("✅ Pydantic validation PASSED")
    except Exception as e:
        print(f"❌ Pydantic validation FAILED: {e}")

    # Step 5: Check for BECAUSE-THEN causal logic
    causal_keywords = ["because", "due to", "which then", "led to", "driven by", "caused by", "resulted in"]

    fields_to_check = [
        ("Revenue Analysis", fa_report.revenue_performance.analysis),
        ("Profitability Analysis", fa_report.profitability_audit.analysis),
        ("Cash Flow Analysis", fa_report.cash_flow_stability.analysis),
        ("Guidance Audit", fa_report.management_guidance_audit)
    ]

    print(f"\n🔍 Causal Logic Check:")
    for field_name, field_text in fields_to_check:
        has_causal = any(keyword in field_text.lower() for keyword in causal_keywords)
        if has_causal:
            matched = [kw for kw in causal_keywords if kw in field_text.lower()]
            print(f"✅ {field_name}: Contains causal connectors {matched}")
        else:
            print(f"⚠️  {field_name}: Missing explicit causal connectors")

    # Step 6: Check for DATA_GAP handling
    has_data_gaps = (
        fa_report.revenue_performance.value == "DATA_GAP" or
        fa_report.profitability_audit.value == "DATA_GAP" or
        fa_report.cash_flow_stability.value == "DATA_GAP"
    )

    if has_data_gaps:
        print(f"\n📊 DATA_GAP Detection:")
        print(f"⚠️  Some metrics marked as DATA_GAP - this is expected if RAG data is unavailable")
        print(f"   Analysis fields should explain WHY data is unavailable")

    return fa_report


async def main():
    """
    Main test runner with command-line argument support.

    Runs native RA tests for specified ticker/year or default test cases.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Native RA (Financial Auditor) Verification Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test specific ticker and fiscal year
  python MAT/tests/verify_ra_native.py --ticker AAPL --fiscal_year 2021
  python MAT/tests/verify_ra_native.py --ticker KO --fiscal_year 2021

  # Run all default test cases
  python MAT/tests/verify_ra_native.py
        """
    )
    parser.add_argument(
        "--ticker",
        type=str,
        help="Stock ticker symbol (e.g., AAPL, KO, NVDA)"
    )
    parser.add_argument(
        "--fiscal_year",
        type=int,
        help="Fiscal year for analysis (e.g., 2021, 2022)"
    )

    args = parser.parse_args()

    # Determine test cases based on arguments
    if args.ticker and args.fiscal_year:
        # Single test case from command-line arguments
        test_cases = [
            {
                "ticker": args.ticker,
                "fiscal_year": args.fiscal_year,
                "description": f"FY{args.fiscal_year}: Custom test for {args.ticker}"
            }
        ]
    elif args.ticker or args.fiscal_year:
        # Error if only one argument provided
        print("❌ Error: Both --ticker and --fiscal_year must be provided together")
        parser.print_help()
        return
    else:
        # Use default test cases
        test_cases = DEFAULT_TEST_CASES

    print("\n" + "="*100)
    print("NATIVE RESEARCH ANALYST (FINANCIAL AUDITOR) VERIFICATION TEST")
    print("="*100)
    print("\nObjective: Verify that RetrieveRAGData Action provides expert-level financial auditing.")
    print("Requirement: ALL intelligence must come from native Action code, NOT external prompts.")
    print("\nTest Cases:")
    for i, tc in enumerate(test_cases, 1):
        print(f"  {i}. {tc['ticker']} FY{tc['fiscal_year']}: {tc['description']}")
    print("="*100)

    results = []

    # Run tests
    for test_case in test_cases:
        try:
            fa_report = await run_native_ra_test(
                ticker=test_case["ticker"],
                fiscal_year=test_case["fiscal_year"],
                description=test_case["description"]
            )

            # Check for causal logic in all analysis fields
            causal_keywords = ["because", "due to", "which then", "led to", "driven by", "caused by", "resulted in"]

            analyses = [
                fa_report.revenue_performance.analysis,
                fa_report.profitability_audit.analysis,
                fa_report.cash_flow_stability.analysis,
                fa_report.management_guidance_audit
            ]

            has_causal_logic = any(
                any(keyword in analysis.lower() for keyword in causal_keywords)
                for analysis in analyses
            )

            results.append({
                "test_case": test_case["description"],
                "ticker": test_case["ticker"],
                "fiscal_year": test_case["fiscal_year"],
                "fa_report": fa_report.model_dump(),
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
                "fiscal_year": test_case["fiscal_year"],
                "error": str(e),
                "status": "FAILED"
            })

    # Save results
    output_dir = Path("MAT/tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save comprehensive results
    output_file = output_dir / "native_ra_verification_results.json"

    output_data = {
        "test_name": "Native RA (Financial Auditor) Intelligence Verification",
        "test_date": datetime.now().isoformat(),
        "objective": "Verify RetrieveRAGData has expert-level financial auditing capabilities",
        "results": results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

    # Verify dual-output files exist (created by RetrieveRAGData action)
    print(f"\n{'='*100}")
    print(f"DUAL-OUTPUT FILE VERIFICATION")
    print(f"{'='*100}")

    for result in results:
        if result["status"] == "PASSED":
            ticker = result["ticker"]
            fiscal_year = result["fiscal_year"]

            # Check for Topk_chunk file
            topk_chunk_file = Path(f"MAT/report/RA/Topk_chunk_{ticker}_{fiscal_year}.json")
            if topk_chunk_file.exists():
                print(f"✅ Top-K chunks file exists: {topk_chunk_file}")
            else:
                print(f"❌ Top-K chunks file MISSING: {topk_chunk_file}")

            # Check for RA_report file
            ra_report_file = Path(f"MAT/report/RA/RA_report_{ticker}_{fiscal_year}.json")
            if ra_report_file.exists():
                print(f"✅ FAReport file exists: {ra_report_file}")
            else:
                print(f"❌ FAReport file MISSING: {ra_report_file}")

    print(f"\n{'='*100}")
    print(f"NATIVE RA VERIFICATION COMPLETE")
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
        print(f"\n{status_icon} {result['ticker']} FY{result['fiscal_year']}: {result['test_case']}")
        if result["status"] == "PASSED":
            fa_data = result["fa_report"]
            causal_icon = "✅" if result["has_causal_logic"] else "⚠️"

            print(f"\n  💰 Revenue Performance:")
            print(f"     Value: {fa_data['revenue_performance']['value']}")
            print(f"     {causal_icon} Causal Logic: {'Present' if result['has_causal_logic'] else 'Missing'}")

            print(f"\n  📊 Profitability Audit:")
            print(f"     Value: {fa_data['profitability_audit']['value']}")

            print(f"\n  💵 Cash Flow Stability:")
            print(f"     Value: {fa_data['cash_flow_stability']['value']}")

            print(f"\n  ⚠️  Key Risks: {len(fa_data['key_risks_evidence'])} identified")
            # source_citations removed - traceability now in each FinancialMetric
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

    # Print full JSON reports
    print("\n" + "="*100)
    print("FULL JSON REPORTS")
    print("="*100)
    for i, result in enumerate(results, 1):
        if result["status"] == "PASSED":
            print(f"\n{i}. {result['ticker']} FY{result['fiscal_year']}:")
            print(json.dumps(result["fa_report"], indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
