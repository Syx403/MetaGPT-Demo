"""
Filename: MetaGPT-Ewan/MAT/roles/research_analyst.py
Created Date: Wednesday, January 1st 2026
Author: Ewan Su
Description: Research Analyst (RA) role for fundamental analysis using RAGFlow data.

This role wraps the RetrieveRAGData action to perform fundamental analysis
and publishes FAReport when it observes a StartAnalysis message.
"""

from typing import Optional

from metagpt.schema import Message
from metagpt.logs import logger

from .base_agent import BaseInvestmentAgent
from ..actions.retrieve_rag_data import RetrieveRAGData
from ..actions_module import StartAnalysis, PublishFAReport
from ..schemas import FAReport


class ResearchAnalyst(BaseInvestmentAgent):
    """
    Research Analyst (RA) - Fundamental Analysis Expert.
    
    This role is responsible for:
    1. Observing StartAnalysis messages for a specific ticker
    2. Retrieving fundamental data from RAGFlow API
    3. Generating FAReport with financial metrics (revenue growth, margins, risks)
    4. Publishing the FAReport for other agents to observe
    
    The RA uses the RetrieveRAGData action which queries RAGFlow for:
    - Revenue Growth (YoY trends)
    - Gross Margin (profit margins)
    - Guidance (management outlook)
    - Key Risks (top risk factors)
    
    Example:
        ra = ResearchAnalyst()
        ra.set_ticker("AAPL")
        # Observes StartAnalysis message
        # Generates and publishes FAReport
    """
    
    # Optional: Configuration for time-aligned historical analysis
    analysis_start_date: Optional[str] = None
    analysis_end_date: Optional[str] = None
    
    def __init__(
        self,
        name: str = "ResearchAnalyst",
        profile: str = "Research Analyst",
        goal: str = "Conduct fundamental analysis and identify growth potential",
        constraints: str = "Focus on quantitative metrics from RAGFlow data",
        analysis_start_date: Optional[str] = None,
        analysis_end_date: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Research Analyst role.
        
        Args:
            name: Role name (default: "ResearchAnalyst")
            profile: Role profile description
            goal: Primary objective of this role
            constraints: Behavioral constraints for the role
            analysis_start_date: Optional start date for historical analysis (YYYY-MM-DD)
            analysis_end_date: Optional end date for historical analysis (YYYY-MM-DD)
            **kwargs: Additional arguments passed to BaseInvestmentAgent
        """
        super().__init__(
            name=name,
            profile=profile,
            goal=goal,
            constraints=constraints,
            **kwargs
        )
        
        # Store time window for potential time-aligned analysis
        self.analysis_start_date = analysis_start_date
        self.analysis_end_date = analysis_end_date
        
        # Initialize the RetrieveRAGData action
        self.retrieve_rag_action = RetrieveRAGData()
        
        # Set up the role to observe StartAnalysis messages and take PublishFAReport action
        self.set_actions([PublishFAReport])
        self._watch([StartAnalysis])
        
        logger.info(f"📊 {self.profile} initialized and watching for StartAnalysis messages")
    
    async def _act(self) -> Message:
        """
        Execute fundamental analysis and publish FAReport.
        
        This method is called when a StartAnalysis message is observed.
        It will:
        1. Extract the ticker from the current trading state
        2. Call RetrieveRAGData action to get fundamental data
        3. Wrap the FAReport into a Message
        4. Publish the message for other agents to observe
        
        Returns:
            Message containing the FAReport
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 {self.profile} starting fundamental analysis")
        logger.info(f"{'='*80}")
        
        # Get the ticker from the trading state or from the current ticker
        ticker = self._current_ticker or self.env.trading_state.current_ticker
        
        if not ticker:
            logger.error("❌ No ticker specified for analysis")
            # Return a default FAReport with qualitative schema
            default_report = FAReport(ticker="UNKNOWN")
            return self.publish_message(default_report, PublishFAReport)
        
        logger.info(f"🎯 Analyzing ticker: {ticker}")

        # Extract fiscal year from system_reference_date if available
        fiscal_year = None
        if self.system_reference_date:
            try:
                fiscal_year = int(self.system_reference_date.split('-')[0])
                logger.info(f"📅 Target fiscal year: {fiscal_year} (from system_reference_date)")
            except (ValueError, IndexError):
                logger.warning(f"⚠️ Could not extract fiscal year from {self.system_reference_date}")
        elif hasattr(self, 'analysis_start_date') and self.analysis_start_date:
            try:
                fiscal_year = int(self.analysis_start_date.split('-')[0])
                logger.info(f"📅 Target fiscal year: {fiscal_year} (from analysis_start_date)")
            except (ValueError, IndexError):
                logger.warning(f"⚠️ Could not extract fiscal year from {self.analysis_start_date}")
        
        try:
            # Execute the RetrieveRAGData action
            # Pass fiscal_year to focus on specific year's data
            fa_report = await self.retrieve_rag_action.run(
                ticker=ticker,
                fiscal_year=fiscal_year
            )
            
            # Log the analysis results with qualitative evidence
            logger.info(f"\n📈 Fundamental Analysis Results for {ticker}:")
            logger.info(f"   Revenue Performance: {fa_report.revenue_performance.value}")
            logger.info(f"   Profitability Audit: {fa_report.profitability_audit.value}")
            logger.info(f"   Cash Flow Stability: {fa_report.cash_flow_stability.value}")
            logger.info(f"   Management Guidance: {fa_report.management_guidance_audit[:100]}...")
            logger.info(f"   Key Risks: {len(fa_report.key_risks_evidence)} identified")
            
            # Update the environment's trading state with FA data
            if self.env.trading_state:
                self.env.trading_state.fa_data = fa_report
                logger.info(f"✅ Updated trading state with FA data")
            
            # Publish the FAReport as a message
            message = self.publish_message(fa_report, PublishFAReport)
            
            logger.info(f"📤 {self.profile} published FAReport for {ticker}")
            logger.info(f"{'='*80}\n")
            
            return message
            
        except Exception as e:
            logger.error(f"❌ {self.profile} failed to complete analysis: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            
            # Return a default FAReport on error
            from ..schemas import FinancialMetric
            error_report = FAReport(
                ticker=ticker,
                revenue_performance=FinancialMetric(value="DATA_GAP", analysis=f"Analysis failed: {str(e)}"),
                profitability_audit=FinancialMetric(value="DATA_GAP", analysis="Data unavailable due to error"),
                cash_flow_stability=FinancialMetric(value="DATA_GAP", analysis="Data unavailable due to error"),
                management_guidance_audit=f"Analysis failed: {str(e)}",
                key_risks_evidence=[f"Analysis failed: {str(e)}"]
            )
            return self.publish_message(error_report, PublishFAReport)
    
    def _is_message_relevant(self, message: Message) -> bool:
        """
        Determine if a message is relevant to this Research Analyst.
        
        The RA should respond to:
        1. StartAnalysis messages for the current ticker
        2. Messages that explicitly mention the current ticker
        
        Args:
            message: The message to check for relevance
            
        Returns:
            True if the message is relevant, False otherwise
        """
        # Check if it's a StartAnalysis message
        if message.cause_by == StartAnalysis:
            logger.debug(f"📩 {self.profile} received StartAnalysis message")
            return True
        
        # Use the parent class's default filtering logic for other messages
        return super()._is_message_relevant(message)
    
    def set_time_window(self, start_date: str, end_date: str):
        """
        Set time window for time-aligned historical analysis.
        
        This is useful when you want to analyze fundamental data from a specific
        period (e.g., 2022 to match with historical technical analysis).
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        self.analysis_start_date = start_date
        self.analysis_end_date = end_date
        logger.info(f"📅 {self.profile} time window set: {start_date} to {end_date}")

