"""
Filename: MetaGPT-Ewan/MAT/actions/synthesize_strategy.py
Created Date: Tuesday, January 7th 2026
Author: Claude Code
Description: Alpha Strategist (AS) decision engine with conflict detection and strategy synthesis.

This module implements two core actions:
1. AnalyzeConflict - Detects conflicts between TA/RA/SA reports
2. SynthesizeDecision - Makes final trading decisions based on all evidence

Key Design Principles:
- Precise metric extraction using exact parameter names
- Direct value injection into LLM prompts (NO markdown dossier)
- Pure local operation (no external API calls)
- Schema-compliant output (StrategyDecision Pydantic model)
"""

from typing import Dict, Any, Optional
from pathlib import Path

from metagpt.actions import Action
from metagpt.logs import logger
from pydantic import Field

from ..schemas import (
    FAReport, TAReport, SAReport, InvestigationReport,
    StrategyDecision, SignalIntensity
)


class AnalyzeConflict(Action):
    """
    Detect conflicts between TA/RA/SA reports to trigger deep dive investigations.

    This action analyzes multi-agent reports for contradictions, tensions, or ambiguities
    that require additional investigation before making a final trading decision.

    Examples of conflicts:
    - TA shows oversold (value opportunity) but RA shows deteriorating fundamentals
    - SA reports strong earnings beat but stock price dropped (paradox)
    - RA shows strong growth but TA shows MA(200) resistance (dead cat bounce risk)
    """

    name: str = "AnalyzeConflict"

    def _extract_metrics_to_context(
        self,
        ra: FAReport,
        ta: TAReport,
        sa: SAReport,
        sa_adv: Optional[InvestigationReport] = None
    ) -> Dict[str, Any]:
        """
        Extract specific indicators from Pydantic models into a flat dictionary.

        This method creates a context dictionary with exact parameter names that will be
        injected directly into LLM prompts using .format(**context).

        Args:
            ra: Research Analyst (Financial Auditor) report
            ta: Technical Analyst report
            sa: Sentiment Analyst report (basic mode)
            sa_adv: Optional Sentiment Analyst advanced report (investigation mode)

        Returns:
            Dictionary with exact parameter names for prompt injection
        """
        context = {
            # TA Metrics
            "ta_market_regime": ta.market_regime,
            "ta_indicator_tension": ta.indicator_tension_analysis,
            "ta_dead_cat_vs_value": ta.dead_cat_vs_value,

            # RA Metrics
            "ra_revenue_value": ra.revenue_performance.value,
            "ra_revenue_analysis": ra.revenue_performance.analysis,
            "ra_profit_value": ra.profitability_audit.value,
            "ra_profit_analysis": ra.profitability_audit.analysis,
            "ra_cash_value": ra.cash_flow_stability.value,
            "ra_cash_analysis": ra.cash_flow_stability.analysis,
            "ra_guidance": ra.management_guidance_audit,
            "ra_risks": ra.key_risks_evidence,

            # SA Metrics
            "sa_news_summary": sa.news_summary,
            "sa_sentiment_assessment": sa.qualitative_sentiment_assessment,
            "sa_product_demand": sa.sentiment_matrix.get("Product_Demand", "Not available"),
            "sa_macro_env": sa.sentiment_matrix.get("Macro_Environment", "Not available"),
            "sa_mgmt_conf": sa.sentiment_matrix.get("Management_Confidence", "Not available"),
            "sa_comp_pos": sa.sentiment_matrix.get("Competitive_Position", "Not available"),
            "sa_causal_narrative": sa.causal_narrative,
            "sa_expectation_gap": sa.expectation_gap,
            "sa_tensions": sa.paradoxes_or_tensions,
        }

        # SA-Advanced Metrics (if investigation was triggered)
        if sa_adv is not None:
            context.update({
                "sa_adv_findings": sa_adv.detailed_findings,
                "sa_adv_resolved": sa_adv.is_ambiguity_resolved,
                "sa_adv_risk_class": sa_adv.risk_classification,
                "sa_adv_revision": sa_adv.qualitative_sentiment_revision,
                "sa_adv_gaps": sa_adv.evidence_gaps,
                "sa_adv_evidence": sa_adv.key_evidence,
                "sa_adv_confidence": sa_adv.confidence_level,
            })
        else:
            # Provide defaults if advanced mode not used
            context.update({
                "sa_adv_findings": "N/A - Advanced investigation not triggered",
                "sa_adv_resolved": False,
                "sa_adv_risk_class": "N/A",
                "sa_adv_revision": "N/A",
                "sa_adv_gaps": [],
                "sa_adv_evidence": [],
                "sa_adv_confidence": "N/A",
            })

        return context

    async def run(
        self,
        ticker: str,
        ra: FAReport,
        ta: TAReport,
        sa: SAReport
    ) -> Dict[str, Any]:
        """
        Analyze multi-agent reports for conflicts requiring investigation.

        Args:
            ticker: Stock ticker symbol
            ra: Research Analyst report
            ta: Technical Analyst report
            sa: Sentiment Analyst report (basic mode)

        Returns:
            Dictionary with:
            - has_conflict: bool indicating if conflict detected
            - context_issue: str describing the conflict (if detected)
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 ANALYZING CONFLICTS for {ticker}")
        logger.info(f"{'='*80}")

        # Step 1: Extract metrics into flat context dictionary
        context = self._extract_metrics_to_context(ra, ta, sa)
        context["ticker"] = ticker

        # Step 2: Build conflict analysis prompt with placeholders
        prompt = """
You are the Senior Strategy Auditor. You are in the AUDIT PHASE of the investment workflow. Your mission is to detect "Logical Friction" by cross-examining qualitative and quantitative evidence across three dimensions (RA, TA, SA).

=== AUDIT CONTEXT ===
TICKER: {ticker}

=== INPUT DOSSIERS (STRATEGIC PARAMETERS) ===
### 1. Fundamental Evidence (RA)
- Revenue: {ra_revenue_value} | Analysis: {ra_revenue_analysis}
- Profitability: {ra_profit_value} | Analysis: {ra_profit_analysis}
- Cash Flow: {ra_cash_value} | Analysis: {ra_cash_analysis}
- Guidance: {ra_guidance}
- Risks Identified: {ra_risks}

### 2. Technical Structure (TA)
- Market Regime: {ta_market_regime}
- Indicator Tension: {ta_indicator_tension}
- Structural Categorization: {ta_dead_cat_vs_value}

### 3. Sentiment Expectation (SA)
- News Summary: {sa_news_summary} | Assessment: {sa_sentiment_assessment}
- Narrative Matrix: Demand:{sa_product_demand} | Macro:{sa_macro_env} | Mgmt:{sa_mgmt_conf} | Comp:{sa_comp_pos}
- Causal Logic: {sa_causal_narrative}
- Expectation Gap: {sa_expectation_gap} | Paradoxes/Tensions: {sa_tensions}

=== YOUR LOGICAL AUDIT TASK ===
Identify STRUCTURAL CONFLICTS using the following audit rules. You MUST trigger "has_conflict: true" if any friction is detected:

1. **Growth-Sentiment Paradox**: Check if {ra_revenue_analysis} claims strong organic growth while {sa_expectation_gap} or {sa_tensions} reveals market punishment (e.g., "Good news, Price drop") or significant concerns in {sa_macro_env}.
2. **Mean Reversion vs. Narrative FOMO**: If {ta_market_regime} shows price is significantly overextended from long-term averages (suggesting mean reversion risk) and {ta_indicator_tension} indicates exhaustion (high RSI), but {sa_news_summary} reports pure bullish sentiment without acknowledging structural resistance.
3. **Structure-Risk Collision (The Value Trap)**: If {ta_dead_cat_vs_value} suggests a "Value Entry Opportunity" but {ra_risks} identifies a structural fundamental threat or {ra_cash_analysis} shows fragile stability.
4. **Strategic Mismatch**: If {ra_guidance} conflicts with the evidence in {sa_mgmt_conf} or {sa_comp_pos} regarding competitive moat and actual market confidence.

=== DECISION RULES ===
- If NO major conflicts: has_conflict = false, context_issue = "No significant conflicts detected"
- If conflicts detected: has_conflict = true, context_issue = "<Detailed description citing specific parameters. E.g., 'RA revenue analysis vs SA expectation gap discrepancy'>"

=== OUTPUT FORMAT (STRICT JSON) ===
{{
  "has_conflict": boolean,
  "context_issue": "string"
}}

CRITICAL: Output ONLY the JSON. No markdown code blocks, no explanations.
"""
        # Step 3: Inject context values into prompt
        formatted_prompt = prompt.format(**context)

        try:
            # Step 4: Call LLM
            response = await self._aask(formatted_prompt)

            # Step 5: Parse JSON response
            from MAT.roles.base_agent import BaseInvestmentAgent
            result = BaseInvestmentAgent.parse_json_robustly(response)

            has_conflict = result.get("has_conflict", False)
            context_issue = result.get("context_issue", "No conflicts detected")

            logger.info(f"\n📊 Conflict Analysis Result:")
            logger.info(f"   Has Conflict: {has_conflict}")
            logger.info(f"   Context Issue: {context_issue}")
            logger.info(f"{'='*80}\n")

            return {
                "has_conflict": has_conflict,
                "context_issue": context_issue
            }

        except Exception as e:
            logger.error(f"❌ Conflict analysis failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())

            # Return safe default (no conflict detected)
            return {
                "has_conflict": False,
                "context_issue": f"Conflict analysis failed: {str(e)}"
            }


class SynthesizeDecision(Action):
    """
    Make final trading decision based on all available evidence.

    This action synthesizes TA/RA/SA reports (and optional SA-Advanced investigation)
    into a final StrategyDecision with trading signals, confidence scores, and risk notes.

    Output Schema: StrategyDecision
    - ticker: Stock symbol
    - final_action: SignalIntensity (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
    - confidence_score: 0-100
    - logic_chain: List of reasoning steps
    - risk_notes: Risk management constraints
    - suggested_module: Execution module name
    - decision_summary: High-level summary of decision
    - conflict_report: Summary of conflicts and resolutions
    """

    name: str = "SynthesizeDecision"

    def _extract_metrics_to_context(
        self,
        ra: FAReport,
        ta: TAReport,
        sa: SAReport,
        sa_adv: Optional[InvestigationReport] = None
    ) -> Dict[str, Any]:
        """
        Extract specific indicators from Pydantic models into a flat dictionary.

        (Same implementation as AnalyzeConflict for consistency)
        """
        context = {
            # TA Metrics
            "ta_market_regime": ta.market_regime,
            "ta_indicator_tension": ta.indicator_tension_analysis,
            "ta_dead_cat_vs_value": ta.dead_cat_vs_value,

            # RA Metrics
            "ra_revenue_value": ra.revenue_performance.value,
            "ra_revenue_analysis": ra.revenue_performance.analysis,
            "ra_profit_value": ra.profitability_audit.value,
            "ra_profit_analysis": ra.profitability_audit.analysis,
            "ra_cash_value": ra.cash_flow_stability.value,
            "ra_cash_analysis": ra.cash_flow_stability.analysis,
            "ra_guidance": ra.management_guidance_audit,
            "ra_risks": ra.key_risks_evidence,

            # SA Metrics
            "sa_news_summary": sa.news_summary,
            "sa_sentiment_assessment": sa.qualitative_sentiment_assessment,
            "sa_product_demand": sa.sentiment_matrix.get("Product_Demand", "Not available"),
            "sa_macro_env": sa.sentiment_matrix.get("Macro_Environment", "Not available"),
            "sa_mgmt_conf": sa.sentiment_matrix.get("Management_Confidence", "Not available"),
            "sa_comp_pos": sa.sentiment_matrix.get("Competitive_Position", "Not available"),
            "sa_causal_narrative": sa.causal_narrative,
            "sa_expectation_gap": sa.expectation_gap,
            "sa_tensions": sa.paradoxes_or_tensions,
        }

        # SA-Advanced Metrics (if investigation was triggered)
        if sa_adv is not None:
            context.update({
                "sa_adv_findings": sa_adv.detailed_findings,
                "sa_adv_resolved": sa_adv.is_ambiguity_resolved,
                "sa_adv_risk_class": sa_adv.risk_classification,
                "sa_adv_revision": sa_adv.qualitative_sentiment_revision,
                "sa_adv_gaps": sa_adv.evidence_gaps,
                "sa_adv_evidence": sa_adv.key_evidence,
                "sa_adv_confidence": sa_adv.confidence_level,
            })
        else:
            # Provide defaults if advanced mode not used
            context.update({
                "sa_adv_findings": "N/A - Advanced investigation not triggered",
                "sa_adv_resolved": False,
                "sa_adv_risk_class": "N/A",
                "sa_adv_revision": "N/A",
                "sa_adv_gaps": [],
                "sa_adv_evidence": [],
                "sa_adv_confidence": "N/A",
            })

        return context

    async def run(
        self,
        ticker: str,
        ra: FAReport,
        ta: TAReport,
        sa: SAReport,
        sa_adv: Optional[InvestigationReport] = None,
        conflict_issue: Optional[str] = None
    ) -> StrategyDecision:
        """
        Synthesize final trading decision from all evidence.

        Args:
            ticker: Stock ticker symbol
            ra: Research Analyst report
            ta: Technical Analyst report
            sa: Sentiment Analyst report (basic mode)
            sa_adv: Optional advanced investigation report
            conflict_issue: Optional conflict description from AnalyzeConflict

        Returns:
            StrategyDecision Pydantic object with final trading signal
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🎯 SYNTHESIZING DECISION for {ticker}")
        logger.info(f"{'='*80}")

        # Step 1: Extract metrics into flat context dictionary
        context = self._extract_metrics_to_context(ra, ta, sa, sa_adv)
        context["ticker"] = ticker
        context["conflict_issue"] = conflict_issue or "No conflicts detected"

        # Step 2: Build decision synthesis prompt with placeholders
        prompt = """
You are the Chief Strategy Auditor. You are in the SYNTHESIS PHASE. Your task is to provide the final "Safe-First" investment decision by resolving all evidence conflicts and assigning a definitive signal.

=== FINAL AUDIT CONTEXT ===
TICKER: {ticker}
Conflict Analysis: {conflict_issue}

=== CONSOLIDATED PARAMETERS ===
1. [RA Data]: {ra_revenue_value}, {ra_revenue_analysis}, {ra_profit_analysis}, {ra_cash_analysis}, {ra_guidance}, {ra_risks}
2. [TA Data]: {ta_market_regime}, {ta_indicator_tension}, {ta_dead_cat_vs_value}
3. [SA Data]: {sa_news_summary}, {sa_causal_narrative}, {sa_expectation_gap}, {sa_macro_env}, {sa_comp_pos}
4. [SA-Advanced Investigation]: 
   - Resolved: {sa_adv_resolved} | Findings: {sa_adv_findings}
   - Risk Class: {sa_adv_risk_class} | Revision: {sa_adv_revision}
   - Confidence: {sa_adv_confidence} | Evidence: {sa_adv_evidence} | Gaps: {sa_adv_gaps}

=== YOUR DECISION SYNTHESIS TASK ===
Apply the "Safe-First" Strategic Filter to determine the final action:

1. **The Investigation Override**: If a conflict was previously identified, you MUST prioritize {sa_adv_resolved} and {sa_adv_evidence}. If {sa_adv_resolved} is FALSE, or {sa_adv_confidence} is LOW, or {sa_adv_risk_class} is "FUNDAMENTAL_THREAT", you MUST default to "NEUTRAL".
2. **Quality of Growth Audit**: Justify the action using {ra_revenue_analysis} and {ra_profit_analysis}. Ensure {sa_causal_narrative} and {sa_comp_pos} support long-term sustainability.
3. **Technical Execution**: Validate entry timing via {ta_market_regime} and {ta_dead_cat_vs_value}. Ensure {ta_indicator_tension} does not show extreme momentum exhaustion.

=== SIGNAL GUIDELINES ===
- **STRONG_BUY**: RA, TA, and SA are all bullish; fundamentals strong; technical shows structural value support.
- **BUY**: Majority bullish; fundamentals solid; technical shows reasonable opportunity; conflicts resolved via {sa_adv_evidence}.
- **NEUTRAL**: Mixed signals; {sa_adv_resolved} is false; critical {sa_adv_gaps} exist; or high risk in {sa_adv_risk_class}.
- **SELL**: Majority bearish; fundamentals weakening; technical shows structural resistance.
- **STRONG_SELL**: All agents bearish; fundamentals deteriorating; technical indicates "Dead Cat Bounce" risk.

=== OUTPUT FORMAT (STRICT JSON) ===
{{
  "ticker": "{ticker}",
  "final_action": "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL",
  "confidence_score": <float 0-100 based on report consistency and {sa_adv_confidence}>,
  "logic_chain": [
    "Step 1: Metric Check (Using {ra_revenue_value})",
    "Step 2: Analysis Cross-Check (RA analysis vs SA narrative)",
    "Step 3: Technical Structure Check (Using {ta_market_regime})",
    "Step 4: Conflict Resolution (Based on {sa_adv_risk_class} and {sa_adv_evidence})"
  ],
  "risk_notes": "<Actionable risk points using {ra_risks} and {sa_adv_gaps}>",
  "suggested_module": "mean_reversion_engine" | "trend_following_engine" | "hold_module",
  "decision_summary": "<2-3 sentence executive summary using {ra_revenue_analysis}, {ta_market_regime}, and {sa_adv_revision}>",
  "conflict_report": "<Summary of detected friction and how {sa_adv_findings} resolved it.>"
}}

CRITICAL: Output ONLY the JSON. No markdown code blocks, no explanations.
"""
        # Step 3: Inject context values into prompt
        formatted_prompt = prompt.format(**context)

        try:
            # Step 4: Call LLM
            response = await self._aask(formatted_prompt)

            # Step 5: Parse JSON response
            from MAT.roles.base_agent import BaseInvestmentAgent
            result = BaseInvestmentAgent.parse_json_robustly(response)

            # Step 6: Validate and create StrategyDecision
            strategy_decision = StrategyDecision(
                ticker=result.get("ticker", ticker),
                final_action=SignalIntensity[result.get("final_action", "HOLD")],
                confidence_score=float(result.get("confidence_score", 50.0)),
                logic_chain=result.get("logic_chain", ["No logic chain provided"]),
                risk_notes=result.get("risk_notes", "No risk notes provided"),
                suggested_module=result.get("suggested_module", "hold_module"),
                decision_summary=result.get("decision_summary", "No summary provided"),
                conflict_report=result.get("conflict_report", "No conflicts detected")
            )

            logger.info(f"\n🎯 Final Decision:")
            logger.info(f"   Signal: {strategy_decision.final_action.value}")
            logger.info(f"   Confidence: {strategy_decision.confidence_score:.1f}%")
            logger.info(f"   Module: {strategy_decision.suggested_module}")
            logger.info(f"   Summary: {strategy_decision.decision_summary}")
            logger.info(f"{'='*80}\n")

            return strategy_decision

        except Exception as e:
            logger.error(f"❌ Decision synthesis failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())

            # Return safe default HOLD decision
            return StrategyDecision(
                ticker=ticker,
                final_action=SignalIntensity.HOLD,
                confidence_score=0.0,
                logic_chain=[f"Decision synthesis failed: {str(e)}"],
                risk_notes="Unable to generate decision due to errors",
                suggested_module="hold_module",
                decision_summary=f"Decision failed: {str(e)}",
                conflict_report="Unable to analyze conflicts due to errors"
            )
