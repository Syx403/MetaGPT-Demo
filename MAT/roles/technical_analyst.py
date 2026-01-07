"""
Filename: MetaGPT-Ewan/MAT/roles/technical_analyst.py
Created Date: Wednesday, January 1st 2026
Author: Ewan Su
Description: Technical Analyst (TA) role for technical analysis using yfinance and pandas_ta.

This role wraps the CalculateTechnicals action to perform technical analysis
and publishes TAReport when it observes a StartAnalysis message.
"""

from typing import Optional
from datetime import datetime, timedelta

from metagpt.schema import Message
from metagpt.logs import logger

from .base_agent import BaseInvestmentAgent
from ..actions.calculate_technicals import CalculateTechnicals
from ..actions_module import StartAnalysis, PublishTAReport
from ..schemas import TAReport, SignalIntensity


class TechnicalAnalyst(BaseInvestmentAgent):
    """
    Technical Analyst (TA) - Technical Analysis & Mean Reversion Expert.
    
    This role is responsible for:
    1. Observing StartAnalysis messages for a specific ticker
    2. Downloading historical/real-time stock price data
    3. Calculating technical indicators (RSI, Bollinger Bands, SMA, ATR)
    4. Applying mean reversion logic to generate trading signals
    5. Publishing the TAReport for other agents to observe
    
    The TA uses the CalculateTechnicals action which:
    - Downloads data from yfinance
    - Calculates RSI(14), BB(20,2), SMA(200), ATR(14) using pandas_ta
    - Generates signals: STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL
    
    Time-Alignment Support:
    - Real-time mode: Uses last 250 days (default)
    - Historical mode: Uses custom start_date and end_date
    
    Example:
        # Real-time analysis
        ta = TechnicalAnalyst()
        ta.set_ticker("AAPL")
        # Observes StartAnalysis message
        # Generates and publishes TAReport using last 250 days
        
        # Historical analysis (time-aligned with 2022 RAG data)
        ta = TechnicalAnalyst(
            analysis_start_date="2022-01-01",
            analysis_end_date="2022-12-31"
        )
        ta.set_ticker("AAPL")
        # Generates TAReport using 2022 price data
    """
    
    # Time window configuration for time-aligned analysis
    analysis_start_date: Optional[str] = None
    analysis_end_date: Optional[str] = None
    
    def __init__(
        self,
        name: str = "TechnicalAnalyst",
        profile: str = "Technical Analyst",
        goal: str = "Identify mean reversion opportunities through technical analysis",
        constraints: str = "Focus on RSI, Bollinger Bands, and SMA indicators",
        analysis_start_date: Optional[str] = None,
        analysis_end_date: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Technical Analyst role.
        
        Args:
            name: Role name (default: "TechnicalAnalyst")
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
        
        # Store time window for time-aligned analysis
        self.analysis_start_date = analysis_start_date
        self.analysis_end_date = analysis_end_date
        
        # Initialize the CalculateTechnicals action
        self.calculate_technicals_action = CalculateTechnicals()
        
        # Set up the role to observe StartAnalysis messages and take PublishTAReport action
        self.set_actions([PublishTAReport])
        self._watch([StartAnalysis])
        
        # Log time window configuration
        if analysis_start_date and analysis_end_date:
            logger.info(f"📈 {self.profile} initialized (Historical: {analysis_start_date} to {analysis_end_date})")
        else:
            logger.info(f"📈 {self.profile} initialized (Real-time: last 250 days)")
        
        logger.info(f"📈 {self.profile} watching for StartAnalysis messages")
    
    async def _act(self) -> Message:
        """
        Execute technical analysis and publish TAReport.
        
        This method is called when a StartAnalysis message is observed.
        It will:
        1. Extract the ticker from the current trading state
        2. Call CalculateTechnicals action to get technical indicators and signal
        3. Wrap the TAReport into a Message
        4. Publish the message for other agents to observe
        
        The time window used depends on the configuration:
        - If analysis_start_date and analysis_end_date are set: Use historical period
        - Otherwise: Use default real-time period (last 250 days)
        
        Returns:
            Message containing the TAReport
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"📈 {self.profile} starting technical analysis")
        logger.info(f"{'='*80}")
        
        # Get the ticker from the trading state or from the current ticker
        ticker = self._current_ticker or self.env.trading_state.current_ticker
        
        if not ticker:
            logger.error("❌ No ticker specified for analysis")
            # Return a default TAReport with qualitative schema
            default_report = TAReport(ticker="UNKNOWN")
            return self.publish_message(default_report, PublishTAReport)
        
        logger.info(f"🎯 Analyzing ticker: {ticker}")

        # Determine time window from system_reference_date or custom dates
        start_date = self.analysis_start_date
        end_date = self.analysis_end_date

        # If system_reference_date is set, calculate historical window
        if self.system_reference_date and not (start_date and end_date):
            ref_date = datetime.strptime(self.system_reference_date, "%Y-%m-%d")
            # Get 12 months (365 days) of data before the reference date to support SMA(200)
            end_date = self.system_reference_date
            start_date = (ref_date - timedelta(days=365)).strftime("%Y-%m-%d")
            logger.info(f"🕰️  Time-Travel Mode: Reference date = {self.system_reference_date}")
            logger.info(f"📅 Time Window: {start_date} to {end_date} (12 months before reference)")
        elif start_date and end_date:
            logger.info(f"📅 Time Window: {start_date} to {end_date} (Historical)")
        else:
            logger.info(f"📅 Time Window: Last 250 days (Real-time)")

        try:
            # Execute the CalculateTechnicals action
            # Pass the time window if configured for historical analysis
            ta_report = await self.calculate_technicals_action.run(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date
            )
            
            # Log the analysis results with qualitative evidence
            logger.info(f"\n📊 Technical Analysis Results for {ticker}:")
            logger.info(f"   RSI(14): {ta_report.rsi_14:.2f}")
            logger.info(f"   BB Lower Touch: {ta_report.bb_lower_touch}")
            logger.info(f"   Multi-Period MA Distances:")
            logger.info(f"     - MA(20):  {ta_report.price_to_ma20_dist:+.2%}")
            logger.info(f"     - MA(50):  {ta_report.price_to_ma50_dist:+.2%}")
            logger.info(f"     - MA(200): {ta_report.price_to_ma200_dist:+.2%}")
            logger.info(f"   ATR Volatility: ${ta_report.volatility_atr:.2f}")
            logger.info(f"   Market Regime: {ta_report.market_regime[:100]}...")
            
            # Update the environment's trading state with TA data
            if self.env.trading_state:
                self.env.trading_state.ta_data = ta_report
                logger.info(f"✅ Updated trading state with TA data")
            
            # Publish the TAReport as a message
            message = self.publish_message(ta_report, PublishTAReport)
            
            logger.info(f"📤 {self.profile} published TAReport for {ticker}")
            logger.info(f"{'='*80}\n")
            
            return message
            
        except Exception as e:
            logger.error(f"❌ {self.profile} failed to complete analysis: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            
            # Return a default TAReport on error with qualitative schema
            error_report = TAReport(
                ticker=ticker,
                rsi_14=50.0,
                bb_lower_touch=False,
                price_to_ma20_dist=0.0,
                price_to_ma50_dist=0.0,
                price_to_ma200_dist=0.0,
                volatility_atr=0.0,
                market_regime=f"Analysis failed: {str(e)}",
                indicator_tension_analysis="Analysis failed",
                dead_cat_vs_value="Analysis failed"
            )
            return self.publish_message(error_report, PublishTAReport)
    
    def _is_message_relevant(self, message: Message) -> bool:
        """
        Determine if a message is relevant to this Technical Analyst.
        
        The TA should respond to:
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
        
        This is useful when you want to analyze price data from a specific period
        to align with fundamental data (e.g., 2022 to match RAG reports from 2022 10-Ks).
        
        Args:
            start_date: Start date in YYYY-MM-DD format (e.g., "2022-01-01")
            end_date: End date in YYYY-MM-DD format (e.g., "2022-12-31")
        
        Example:
            ta = TechnicalAnalyst()
            ta.set_time_window("2022-01-01", "2022-12-31")
            # Now technical analysis will use 2022 price data
        """
        self.analysis_start_date = start_date
        self.analysis_end_date = end_date
        logger.info(f"📅 {self.profile} time window set: {start_date} to {end_date}")
        logger.info(f"   Technical analysis will use price data from this period")
    
    def use_realtime_mode(self):
        """
        Switch to real-time mode (last 250 days).
        
        This clears any previously set time window and uses the default
        real-time period for technical analysis.
        
        Example:
            ta = TechnicalAnalyst(
                analysis_start_date="2022-01-01",
                analysis_end_date="2022-12-31"
            )
            # Later, switch to real-time
            ta.use_realtime_mode()
        """
        self.analysis_start_date = None
        self.analysis_end_date = None
        logger.info(f"📅 {self.profile} switched to real-time mode (last 250 days)")

