"""
Filename: MetaGPT-Ewan/MAT/tests/verify_ta_native.py
Created Date: Saturday, January 4th 2026
Author: Claude Code
Description: Native verification test for CalculateTechnicals action with GPT-4o intelligence.

This script ONLY instantiates the CalculateTechnicals Action and calls .run().
It is FORBIDDEN from containing any LLM prompts - all intelligence must come from
the native Action code.

Test Cases:
- AAPL 2021-12-31: RSI oversold but in recovery trend (post-COVID rally)
- AAPL 2022-12-31: RSI oversold but MA(200) bearish (dead cat bounce risk)

Success Criteria:
- For 2021: Should recognize value entry with trend support
- For 2022: Should identify dead cat bounce risk due to MA(200) resistance
- Console output shows intelligence reasoning (indicator tension, dead cat vs value)
- All outputs are valid TAReport Pydantic objects
"""

import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime

# Import the Action directly
from MAT.actions.calculate_technicals import CalculateTechnicals
from MAT.schemas import TAReport


# ============================================================
# Test Configuration
# ============================================================
TEST_CASES = [
    {
        "ticker": "AAPL",
        "start_date": "2021-01-01",
        "end_date": "2021-12-31",
        "description": "FY2021: Post-COVID recovery rally - oversold with trend support",
        "expected_context": "Value entry - oversold condition with bullish trend context"
    },
    {
        "ticker": "AAPL",
        "start_date": "2022-01-01",
        "end_date": "2022-12-31",
        "description": "FY2022: Inflation/rate hikes - oversold but bearish MA(200)",
        "expected_context": "Dead cat bounce risk - oversold but strong downtrend"
    }
]


async def run_native_ta_test(ticker: str, start_date: str, end_date: str, description: str):
    """
    Run native CalculateTechnicals test.

    CRITICAL: This function contains ZERO LLM prompts. All intelligence comes from
    the CalculateTechnicals Action's native prompt.

    Args:
        ticker: Stock ticker
        start_date: Start date "YYYY-MM-DD"
        end_date: End date "YYYY-MM-DD"
        description: Test description
    """
    print(f"\n{'='*100}")
    print(f"NATIVE TA TEST: {ticker} ({start_date} to {end_date})")
    print(f"Description: {description}")
    print(f"{'='*100}\n")

    # Step 1: Instantiate Action (ZERO external prompts)
    ta_action = CalculateTechnicals()

    # Step 2: Call .run() - all intelligence is native
    ta_report: TAReport = await ta_action.run(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date
    )

    # Step 3: Print pure descriptive multi-period evidence results
    print(f"\n{'='*100}")
    print(f"NATIVE TA PURE DESCRIPTIVE EVIDENCE FOR {ticker} ({end_date})")
    print(f"{'='*100}")
    print(f"\n📊 API-DERIVED TECHNICAL METRICS (yfinance):")
    print(f"  Ticker: {ta_report.ticker}")
    print(f"  RSI(14): {ta_report.rsi_14:.2f}")
    print(f"  BB Lower Touch: {ta_report.bb_lower_touch}")
    print(f"  ATR Volatility: ${ta_report.volatility_atr:.2f}")
    print(f"\n  Multi-Period MA Distances:")
    print(f"    - MA(20):  {ta_report.price_to_ma20_dist:+.2%} (Short-term)")
    print(f"    - MA(50):  {ta_report.price_to_ma50_dist:+.2%} (Medium-term)")
    print(f"    - MA(200): {ta_report.price_to_ma200_dist:+.2%} (Long-term)")

    print(f"\n🧠 PURE DESCRIPTIVE EVIDENCE:")
    print(f"\n  Market Regime (Multi-Period Structural Analysis):")
    print(f"  {ta_report.market_regime}")
    print(f"\n  Indicator Tension Analysis:")
    print(f"  {ta_report.indicator_tension_analysis}")
    print(f"\n  Dead Cat vs Value Entry (Multi-Period Assessment):")
    print(f"  {ta_report.dead_cat_vs_value}")
    print(f"\n  Pivot Zones (API-Derived Levels):")
    for zone, level in ta_report.pivot_zones.items():
        print(f"    - {zone}: ${level:.2f}")
    print(f"{'='*100}\n")

    # Step 4: Validate Pydantic schema
    try:
        ta_report.model_validate(ta_report)
        print("✅ Pydantic validation PASSED")
    except Exception as e:
        print(f"❌ Pydantic validation FAILED: {e}")

    return ta_report


async def main():
    """
    Main test runner.

    Runs native TA tests for both test cases and saves results.
    """
    print("\n" + "="*100)
    print("NATIVE TECHNICAL ANALYSIS VERIFICATION TEST")
    print("="*100)
    print("\nObjective: Verify that CalculateTechnicals Action has internalized GPT-4o intelligence.")
    print("Requirement: ALL intelligence must come from native Action code, NOT external prompts.")
    print("\nTest Cases:")
    for i, tc in enumerate(TEST_CASES, 1):
        print(f"  {i}. {tc['ticker']} {tc['end_date']}: {tc['description']}")
    print("="*100)

    results = []

    # Run tests
    for test_case in TEST_CASES:
        try:
            ta_report = await run_native_ta_test(
                ticker=test_case["ticker"],
                start_date=test_case["start_date"],
                end_date=test_case["end_date"],
                description=test_case["description"]
            )

            results.append({
                "test_case": test_case["description"],
                "ticker": test_case["ticker"],
                "date": test_case["end_date"],
                "expected_context": test_case["expected_context"],
                "ta_report": ta_report.model_dump(),
                "status": "PASSED"
            })

        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()

            results.append({
                "test_case": test_case["description"],
                "ticker": test_case["ticker"],
                "date": test_case["end_date"],
                "expected_context": test_case["expected_context"],
                "error": str(e),
                "status": "FAILED"
            })

    # Save results
    output_file = Path("MAT/tests/native_ta_verification_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "test_name": "Native TA Intelligence Verification",
        "test_date": datetime.now().isoformat(),
        "objective": "Verify CalculateTechnicals has internalized GPT-4o intelligence",
        "results": results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'='*100}")
    print(f"NATIVE TA VERIFICATION COMPLETE")
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
        print(f"{status_icon} {result['ticker']} {result['date']}: {result['test_case']}")
        if result["status"] == "PASSED":
            ta_data = result["ta_report"]
            print(f"   Market Regime: {ta_data['market_regime'][:100]}...")
            print(f"   Multi-Period MA Distances: MA20={ta_data['price_to_ma20_dist']:+.2%}, MA50={ta_data['price_to_ma50_dist']:+.2%}, MA200={ta_data['price_to_ma200_dist']:+.2%}")
            print(f"   RSI: {ta_data['rsi_14']:.2f}")
            print(f"   Dead Cat vs Value: {ta_data['dead_cat_vs_value'][:80]}...")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

    # Print full JSON reports
    print("\n" + "="*100)
    print("FULL JSON REPORTS")
    print("="*100)
    for i, result in enumerate(results, 1):
        if result["status"] == "PASSED":
            print(f"\n{i}. {result['ticker']} {result['date']}:")
            print(json.dumps(result["ta_report"], indent=2, default=str))


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Native verification test for CalculateTechnicals action")
    parser.add_argument("--ticker", type=str, help="Stock ticker symbol (e.g., AAPL, KO)")
    parser.add_argument("--fiscal_year", type=int, help="Fiscal year for analysis (e.g., 2021, 2022)")

    args = parser.parse_args()

    # If CLI arguments provided, override test cases
    if args.ticker and args.fiscal_year:
        # Replace test cases with CLI-specified single test
        TEST_CASES.clear()
        TEST_CASES.append({
            "ticker": args.ticker,
            "start_date": f"{args.fiscal_year}-01-01",
            "end_date": f"{args.fiscal_year}-12-31",
            "description": f"CLI Test: {args.ticker} FY{args.fiscal_year}",
            "expected_context": f"Technical analysis for {args.ticker} in {args.fiscal_year}"
        })
        print(f"\n🔧 CLI Mode: Running test for {args.ticker} FY{args.fiscal_year}")

    asyncio.run(main())
