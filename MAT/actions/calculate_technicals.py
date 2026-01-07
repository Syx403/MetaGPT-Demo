"""
Filename: MetaGPT-Ewan/MAT/actions/calculate_technicals.py
Created Date: Wednesday, January 1st 2026
Author: Ewan Su
Description: CalculateTechnicals action for technical analysis with time-alignment.

This action retrieves historical or real-time stock data using yfinance and
calculates technical indicators (RSI, Bollinger Bands, SMA) using pandas_ta.
It supports flexible time windows to align with fundamental data periods.

Key Features:
- Flexible time window (custom dates or default 60 days)
- Technical indicators: RSI(14), Bollinger Bands(20,2), SMA(200), ATR(14)
- Mean reversion logic for signal generation
- Time-alignment for historical testing

Configuration:
    Settings can be configured in config/config2.yaml under 'technicals' section.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from metagpt.actions import Action
from metagpt.logs import logger
from pydantic import Field

from ..schemas import TAReport
from ..config_loader import get_config


class CalculateTechnicals(Action):
    """
    Calculate technical indicators and generate trading signals using mean reversion logic.
    
    This action retrieves stock price data using yfinance and calculates technical
    indicators using pandas_ta library. It supports flexible time windows for both
    real-time trading and historical backtesting.
    
    Key Features:
    1. Flexible time window (custom start/end dates or default 60 days)
    2. Technical indicators:
       - RSI (Relative Strength Index, 14-period)
       - Bollinger Bands (20-period, 2 std deviations)
       - SMA (Simple Moving Average, 200-period)
       - ATR (Average True Range, 14-period) for volatility
    3. Mean reversion signal logic:
       - STRONG_BUY: RSI < 30 AND Close < Lower Bollinger Band
       - BUY: RSI < 40 AND Close < Lower Bollinger Band
       - NEUTRAL: No strong signals
       - SELL: RSI > 60 AND Close > Upper Bollinger Band
       - STRONG_SELL: RSI > 70 AND Close > Upper Bollinger Band
    4. Time-alignment for historical testing (e.g., 2022 data to match 10-K reports)
    
    Example:
        # Real-time analysis (last 60 days)
        action = CalculateTechnicals()
        ta_report = await action.run(ticker="AAPL")
        
        # Historical analysis (specific period)
        ta_report = await action.run(
            ticker="AAPL",
            start_date="2022-01-01",
            end_date="2022-12-31"
        )
    """
    
    name: str = "CalculateTechnicals"
    
    # Default time window (days)
    default_period: int = Field(default=500, description="Default period in days if dates not specified (increased to support SMA200)")
    
    # Technical indicator parameters
    rsi_period: int = Field(default=14, description="RSI period")
    bb_period: int = Field(default=20, description="Bollinger Bands period")
    bb_std: float = Field(default=2.0, description="Bollinger Bands standard deviation")
    sma_period: int = Field(default=200, description="Simple Moving Average period")
    atr_period: int = Field(default=14, description="Average True Range period")
    
    # Mean reversion thresholds
    rsi_oversold_strong: float = Field(default=30.0, description="RSI threshold for STRONG_BUY")
    rsi_oversold: float = Field(default=40.0, description="RSI threshold for BUY")
    rsi_overbought: float = Field(default=60.0, description="RSI threshold for SELL")
    rsi_overbought_strong: float = Field(default=70.0, description="RSI threshold for STRONG_SELL")
    
    # Output directory for saving technical analysis results
    output_dir: Path = Field(default=Path("MAT/report/TA"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load configuration from config/config2.yaml
        config = get_config()
        
        # Get technical analysis settings from config
        tech_config = config.get_technicals_config()
        self.default_period = tech_config.get("default_period", self.default_period)
        self.rsi_period = tech_config.get("rsi_period", self.rsi_period)
        self.bb_period = tech_config.get("bb_period", self.bb_period)
        self.bb_std = tech_config.get("bb_std", self.bb_std)
        self.sma_period = tech_config.get("sma_period", self.sma_period)
        self.atr_period = tech_config.get("atr_period", self.atr_period)
        
        # Mean reversion thresholds
        thresholds = tech_config.get("mean_reversion_thresholds", {})
        self.rsi_oversold_strong = thresholds.get("rsi_oversold_strong", self.rsi_oversold_strong)
        self.rsi_oversold = thresholds.get("rsi_oversold", self.rsi_oversold)
        self.rsi_overbought = thresholds.get("rsi_overbought", self.rsi_overbought)
        self.rsi_overbought_strong = thresholds.get("rsi_overbought_strong", self.rsi_overbought_strong)

        # Note: output_dir uses Field default (MAT/report/TA) unless overridden in config

        logger.info(f"📈 CalculateTechnicals initialized (RSI={self.rsi_period}, BB={self.bb_period}, SMA={self.sma_period})")
        logger.info(f"📁 Output directory: {self.output_dir}")
    
    async def run(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> TAReport:
        """
        Calculate technical indicators and generate TAReport.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "KO")
            start_date: Optional start date in format "YYYY-MM-DD" (e.g., "2022-01-01")
            end_date: Optional end date in format "YYYY-MM-DD" (e.g., "2022-12-31")
            
        Returns:
            TAReport with technical analysis data and signal
            
        Example:
            # Real-time (last 60 days)
            ta_report = await action.run(ticker="AAPL")
            
            # Historical (2022 data)
            ta_report = await action.run(
                ticker="AAPL",
                start_date="2022-01-01",
                end_date="2022-12-31"
            )
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"📈 CALCULATE TECHNICALS ACTION: {ticker}")
        logger.info(f"{'='*80}")
        
        # Determine time window
        if start_date and end_date:
            logger.info(f"📅 Time Window: {start_date} to {end_date} (Historical)")
            time_mode = "historical"
        else:
            logger.info(f"📅 Time Window: Last {self.default_period} days (Real-time)")
            time_mode = "realtime"
        
        try:
            # Step 1: Download stock data using yfinance
            df = await self._download_stock_data(ticker, start_date, end_date)
            
            if df is None or df.empty:
                logger.warning("⚠️ No stock data retrieved")
                return self._create_default_report(ticker)
            
            logger.info(f"✅ Downloaded {len(df)} trading days of data")
            
            # Step 2: Calculate technical indicators using pandas_ta
            df_with_indicators = await self._calculate_indicators(df, ticker)
            
            if df_with_indicators is None:
                logger.warning("⚠️ Failed to calculate indicators")
                return self._create_default_report(ticker)
            
            # Step 3: Extract latest values for TAReport
            ta_report = await self._generate_ta_report(
                ticker=ticker,
                df=df_with_indicators,
                time_mode=time_mode,
                start_date=start_date,
                end_date=end_date
            )
            
            # Step 4: Save technical analysis results for audit/debugging
            self._save_technical_results(ticker, df_with_indicators, ta_report, time_mode, end_date)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ TECHNICAL ANALYSIS COMPLETE for {ticker}")
            logger.info(f"📊 RSI(14): {ta_report.rsi_14:.2f}")
            logger.info(f"📊 BB Lower Touch: {ta_report.bb_lower_touch}")
            logger.info(f"📊 Price to MA(200) Distance: {ta_report.price_to_ma200_dist:.2%}")
            logger.info(f"📊 ATR Volatility: {ta_report.volatility_atr:.2f}")
            logger.info(f"📊 Market Regime: {ta_report.market_regime}")
            logger.info(f"📊 Pivot Zones: {ta_report.pivot_zones}")
            logger.info(f"{'='*80}\n")
            
            return ta_report
            
        except Exception as e:
            logger.error(f"❌ CalculateTechnicals failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return self._create_default_report(ticker, error_message=str(e))
    
    async def _download_stock_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Download stock data using yfinance.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date "YYYY-MM-DD"
            end_date: Optional end date "YYYY-MM-DD"
            
        Returns:
            pandas DataFrame with OHLCV data, or None if failed
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.error("❌ yfinance not installed. Run: pip install yfinance")
            return None
        
        try:
            logger.info("🌐 Downloading stock data from Yahoo Finance...")
            
            # Use yf.download() which is more stable than Ticker.history()
            if start_date and end_date:
                # Historical period with specific dates
                df = yf.download(
                    ticker, 
                    start=start_date, 
                    end=end_date,
                    progress=False,
                    auto_adjust=True,  # Adjust for splits and dividends
                    threads=False      # Avoid threading issues
                )
                logger.info(f"   Downloaded historical data: {start_date} to {end_date}")
            else:
                # Real-time: last N days
                df = yf.download(
                    ticker,
                    period=f"{self.default_period}d",
                    progress=False,
                    auto_adjust=True,
                    threads=False
                )
                logger.info(f"   Downloaded recent data: last {self.default_period} days")
            
            if df.empty:
                logger.warning(f"⚠️ No data returned for {ticker}")
                logger.warning(f"   This might be due to:")
                logger.warning(f"   1. Network connectivity issues")
                logger.warning(f"   2. Yahoo Finance API temporary unavailability")
                logger.warning(f"   3. Invalid ticker symbol")
                logger.warning(f"   Please try again later or check your internet connection")
                return None
            
            # yf.download returns MultiIndex columns for single ticker, flatten them
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Basic data validation
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                logger.error(f"❌ Missing required columns: {missing_cols}")
                return None
            
            logger.info(f"   Data range: {df.index[0].date()} to {df.index[-1].date()}")
            logger.info(f"   Trading days: {len(df)}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to download stock data: {e}")
            logger.error(f"   This is likely a temporary Yahoo Finance API issue")
            logger.error(f"   Possible solutions:")
            logger.error(f"   1. Wait a few minutes and try again")
            logger.error(f"   2. Check your internet connection")
            logger.error(f"   3. Update yfinance: pip install --upgrade yfinance")
            return None
    
    async def _calculate_indicators(self, df, ticker: str):
        """
        Calculate technical indicators using pandas_ta.

        Indicators:
        - RSI (Relative Strength Index, 14-period)
        - Bollinger Bands (20-period, 2 std)
        - Multi-Period SMAs (20, 50, 200-period) for trend analysis
        - ATR (Average True Range, 14-period)

        Args:
            df: DataFrame with OHLCV data
            ticker: Stock ticker symbol

        Returns:
            DataFrame with added indicator columns, or None if failed
        """
        try:
            import pandas_ta as ta
        except ImportError:
            logger.error("❌ pandas_ta not installed. Run: pip install pandas_ta")
            return None

        try:
            logger.info("🔢 Calculating technical indicators...")

            # Make a copy to avoid modifying original
            df = df.copy()

            # Calculate RSI (Relative Strength Index)
            df['RSI'] = ta.rsi(df['Close'], length=self.rsi_period)
            logger.info(f"   ✅ RSI({self.rsi_period}) calculated")

            # Calculate Bollinger Bands
            bbands = ta.bbands(df['Close'], length=self.bb_period, std=self.bb_std)
            if bbands is not None:
                df['BB_Lower'] = bbands[f'BBL_{self.bb_period}_{self.bb_std}']
                df['BB_Middle'] = bbands[f'BBM_{self.bb_period}_{self.bb_std}']
                df['BB_Upper'] = bbands[f'BBU_{self.bb_period}_{self.bb_std}']
                logger.info(f"   ✅ Bollinger Bands({self.bb_period}, {self.bb_std}) calculated")
            else:
                logger.warning("   ⚠️ Bollinger Bands calculation returned None")
                df['BB_Lower'] = df['Close']
                df['BB_Middle'] = df['Close']
                df['BB_Upper'] = df['Close']

            # Calculate Multi-Period SMAs (Simple Moving Averages) for trend structure
            df['SMA_20'] = ta.sma(df['Close'], length=20)
            logger.info(f"   ✅ SMA(20) calculated - short-term trend")

            df['SMA_50'] = ta.sma(df['Close'], length=50)
            logger.info(f"   ✅ SMA(50) calculated - medium-term trend")

            df['SMA_200'] = ta.sma(df['Close'], length=self.sma_period)
            logger.info(f"   ✅ SMA({self.sma_period}) calculated - long-term trend")

            # Calculate ATR (Average True Range) for volatility
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=self.atr_period)
            logger.info(f"   ✅ ATR({self.atr_period}) calculated")

            # Drop rows with NaN values (initial periods where indicators can't be calculated)
            initial_rows = len(df)
            df = df.dropna()
            dropped_rows = initial_rows - len(df)

            if dropped_rows > 0:
                logger.info(f"   📊 Dropped {dropped_rows} rows with NaN (warm-up period)")

            if df.empty:
                logger.error("❌ All data dropped after indicator calculation (insufficient data)")
                return None

            logger.info(f"   📊 Valid data points: {len(df)}")

            return df

        except Exception as e:
            logger.error(f"❌ Failed to calculate indicators: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    async def _generate_ta_report(
        self,
        ticker: str,
        df,
        time_mode: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> TAReport:
        """
        Generate TAReport from calculated indicators using LLM-based contextual interpretation.

        Extracts the latest values and uses GPT-4o-mini to interpret the technical condition
        and provide a qualitative, logic-based signal instead of hardcoded thresholds.

        Args:
            ticker: Stock ticker symbol
            df: DataFrame with calculated indicators
            time_mode: "realtime" or "historical"
            start_date: Optional start date (for logging)
            end_date: Optional end date (for logging)

        Returns:
            TAReport with technical analysis data and LLM-interpreted signal
        """
        try:
            # Get the latest row (most recent data)
            latest = df.iloc[-1]
            analysis_date = latest.name.date()

            # Extract values
            close_price = float(latest['Close'])
            rsi_14 = float(latest['RSI']) if not latest['RSI'] != latest['RSI'] else 50.0  # NaN check
            bb_lower = float(latest['BB_Lower']) if not latest['BB_Lower'] != latest['BB_Lower'] else close_price
            bb_upper = float(latest['BB_Upper']) if not latest['BB_Upper'] != latest['BB_Upper'] else close_price
            bb_middle = float(latest['BB_Middle']) if not latest['BB_Middle'] != latest['BB_Middle'] else close_price
            sma_20 = float(latest['SMA_20']) if not latest['SMA_20'] != latest['SMA_20'] else close_price
            sma_50 = float(latest['SMA_50']) if not latest['SMA_50'] != latest['SMA_50'] else close_price
            sma_200 = float(latest['SMA_200']) if not latest['SMA_200'] != latest['SMA_200'] else close_price
            atr = float(latest['ATR']) if not latest['ATR'] != latest['ATR'] else 0.0

            # Check if price touched/broke lower Bollinger Band
            bb_lower_touch = close_price <= bb_lower

            # Calculate distance from multi-period MAs (as percentage)
            if sma_20 > 0:
                price_to_ma20_dist = (close_price - sma_20) / sma_20
            else:
                price_to_ma20_dist = 0.0

            if sma_50 > 0:
                price_to_ma50_dist = (close_price - sma_50) / sma_50
            else:
                price_to_ma50_dist = 0.0

            if sma_200 > 0:
                price_to_ma200_dist = (close_price - sma_200) / sma_200
            else:
                price_to_ma200_dist = 0.0

            logger.info(f"\n📊 Technical Metrics (as of {analysis_date}):")
            logger.info(f"   Close Price: ${close_price:.2f}")
            logger.info(f"   RSI(14): {rsi_14:.2f}")
            logger.info(f"   BB Lower: ${bb_lower:.2f}, BB Middle: ${bb_middle:.2f}, BB Upper: ${bb_upper:.2f}")
            logger.info(f"   SMA(20): ${sma_20:.2f}, Distance: {price_to_ma20_dist:+.2%}")
            logger.info(f"   SMA(50): ${sma_50:.2f}, Distance: {price_to_ma50_dist:+.2%}")
            logger.info(f"   SMA(200): ${sma_200:.2f}, Distance: {price_to_ma200_dist:+.2%}")
            logger.info(f"   ATR(14): ${atr:.2f}")
            logger.info(f"   BB Lower Touch: {bb_lower_touch}")

            # Use LLM to generate evidence-based analysis (NO SIGNALS)
            logger.info(f"🤖 Requesting LLM multi-period trend analysis...")
            evidence_data = await self._llm_interpret_technicals(
                ticker=ticker,
                analysis_date=str(analysis_date),
                close_price=close_price,
                rsi=rsi_14,
                bb_lower=bb_lower,
                bb_middle=bb_middle,
                bb_upper=bb_upper,
                sma_20=sma_20,
                sma_50=sma_50,
                sma_200=sma_200,
                price_to_ma20_dist=price_to_ma20_dist,
                price_to_ma50_dist=price_to_ma50_dist,
                price_to_ma200_dist=price_to_ma200_dist,
                atr=atr,
                bb_lower_touch=bb_lower_touch
            )

            logger.info(f"   Market Regime: {evidence_data['market_regime']}")

            # Create TAReport with multi-period evidence fields
            ta_report = TAReport(
                ticker=ticker,
                rsi_14=rsi_14,
                bb_lower_touch=bb_lower_touch,
                price_to_ma20_dist=price_to_ma20_dist,
                price_to_ma50_dist=price_to_ma50_dist,
                price_to_ma200_dist=price_to_ma200_dist,
                volatility_atr=atr,
                market_regime=evidence_data["market_regime"],
                indicator_tension_analysis=evidence_data["indicator_tension_analysis"],
                dead_cat_vs_value=evidence_data["dead_cat_vs_value"],
                pivot_zones=evidence_data["pivot_zones"]
            )

            return ta_report

        except Exception as e:
            logger.error(f"❌ Failed to generate TAReport: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return self._create_default_report(ticker, error_message=f"Report generation failed: {str(e)}")

    async def _llm_interpret_technicals(
        self,
        ticker: str,
        analysis_date: str,
        close_price: float,
        rsi: float,
        bb_lower: float,
        bb_middle: float,
        bb_upper: float,
        sma_20: float,
        sma_50: float,
        sma_200: float,
        price_to_ma20_dist: float,
        price_to_ma50_dist: float,
        price_to_ma200_dist: float,
        atr: float,
        bb_lower_touch: bool
    ) -> Dict[str, any]:
        """
        Use LLM to generate pure descriptive multi-period trend analysis (ZERO numeric signals).

        This method provides expert structural evidence using API-derived metrics only.
        All numbers come from yfinance; all analysis is descriptive and qualitative.

        Args:
            ticker: Stock ticker symbol
            analysis_date: Date of analysis
            close_price: Current close price (yfinance)
            rsi: RSI(14) value (yfinance)
            bb_lower: Lower Bollinger Band (yfinance)
            bb_middle: Middle Bollinger Band (yfinance)
            bb_upper: Upper Bollinger Band (yfinance)
            sma_20: 20-day SMA (yfinance)
            sma_50: 50-day SMA (yfinance)
            sma_200: 200-day SMA (yfinance)
            price_to_ma20_dist: Distance from MA(20) as decimal (yfinance-derived)
            price_to_ma50_dist: Distance from MA(50) as decimal (yfinance-derived)
            price_to_ma200_dist: Distance from MA(200) as decimal (yfinance-derived)
            atr: Average True Range (yfinance)
            bb_lower_touch: Whether price touched lower BB (yfinance-derived)

        Returns:
            Dict with market_regime, indicator_tension_analysis, dead_cat_vs_value, pivot_zones
        """
        try:
            # Build LLM prompt for pure descriptive multi-period analysis
            prompt = f"""You are an expert technical analyst providing PURE DESCRIPTIVE EVIDENCE for {ticker} as of {analysis_date}.

=== API-DERIVED TECHNICAL METRICS (yfinance) ===
- Current Price: ${close_price:.2f}
- RSI(14): {rsi:.2f}

- Bollinger Bands (20-period):
  * Lower Band: ${bb_lower:.2f}
  * Middle Band: ${bb_middle:.2f}
  * Upper Band: ${bb_upper:.2f}
  * Price touched/broke lower BB: {bb_lower_touch}

- Multi-Period Moving Averages:
  * SMA(20):  ${sma_20:.2f}  | Distance: {price_to_ma20_dist:+.2%}  (Short-term trend)
  * SMA(50):  ${sma_50:.2f}  | Distance: {price_to_ma50_dist:+.2%}  (Medium-term trend)
  * SMA(200): ${sma_200:.2f} | Distance: {price_to_ma200_dist:+.2%} (Long-term trend)

- Volatility:
  * ATR(14): ${atr:.2f}

=== YOUR PURE DESCRIPTIVE ANALYSIS TASK ===
CRITICAL RULES:
- You are providing DESCRIPTIVE STRUCTURAL EVIDENCE ONLY
- DO NOT generate any numeric sentiment scores or signals
- ALL numbers in your response must be from the API metrics above
- Focus on QUALITATIVE analysis of trend structure and indicator relationships

**Analysis Requirements:**

1. **Market Regime (Long-Form Structural Description):**
   - Provide a detailed narrative (3-5 sentences) analyzing the interplay between:
     * Short-term trend (price vs MA20)
     * Medium-term trend (price vs MA50)
     * Long-term trend (price vs MA200)
   - CRITICAL: Identify "Mean Reversion Risk" when price significantly deviates from MAs
   - Example for overextension: "Price is +24% above MA(200), +18% above MA(50), and +12% above MA(20), indicating significant overextension across all timeframes. This creates elevated mean reversion risk as price has deviated substantially from structural support levels. The widening gap between price and all MAs suggests potential for pullback to reestablish equilibrium..."
   - Example for downtrend: "Price is -14% below MA(200), -10% below MA(50), and -5% below MA(20), confirming a persistent downtrend across all timeframes. The consistent negative distances indicate structural bearish pressure..."

2. **Indicator Tension Analysis:**
   - Analyze CONFLICT or ALIGNMENT between:
     * Momentum indicators (RSI, BB position)
     * Multi-period trend structure (MA20/MA50/MA200 relationships)
   - Example: "RSI at 37 approaching oversold, creating tension with price -14% below MA(200). Short-term momentum suggests bounce potential, but multi-period trend structure (all MAs in bearish configuration) indicates structural resistance..."

3. **Dead Cat Bounce vs. Value Entry (Multi-Period Assessment):**
   - Use multi-period MA distances to categorize:
     * Dead Cat Bounce Risk: Price significantly below MA20/MA50/MA200 with no bullish crossover signals
     * Value Entry Opportunity: Price near key MAs with structural support alignment
   - Provide reasoning based on API-derived MA distances only

4. **Pivot Zones (API-Derived Levels Only):**
   - Use ONLY the API-provided MA levels and BB levels
   - Example: {{"ma200_level": {sma_200:.2f}, "ma50_level": {sma_50:.2f}, "ma20_level": {sma_20:.2f}, "bb_middle": {bb_middle:.2f}}}

=== OUTPUT FORMAT (STRICT JSON) ===
{{
  "market_regime": "<Long-form structural description (3-5 sentences) analyzing short/medium/long-term trend interplay. MUST identify mean reversion risks when price significantly deviates from MAs. Use API-derived distances only.>",
  "indicator_tension_analysis": "<Qualitative analysis of conflict/alignment between momentum (RSI/BB) and multi-period trend structure (MA20/MA50/MA200). 2-3 sentences.>",
  "dead_cat_vs_value": "<Structural categorization as 'Dead Cat Bounce Risk' or 'Value Entry Opportunity' with multi-period MA distance reasoning. 2-3 sentences. NO trade recommendations.>",
  "pivot_zones": {{
    "ma200_level": {sma_200:.2f},
    "ma50_level": {sma_50:.2f},
    "ma20_level": {sma_20:.2f},
    "bb_middle": {bb_middle:.2f}
  }}
}}

CRITICAL: You are providing PURE DESCRIPTIVE EVIDENCE using API-derived metrics ONLY. No numeric signals, no LLM-generated scores, only qualitative structural analysis."""

            # Get LLM instance from MetaGPT context
            from metagpt.context import Context

            context = Context()
            llm = context.llm()

            logger.info(f"🤖 Sending technical interpretation request to LLM...")
            response = await llm.aask(prompt)

            # Parse JSON response robustly (handles Markdown wrapping)
            from MAT.roles.base_agent import BaseInvestmentAgent
            response_data = BaseInvestmentAgent.parse_json_robustly(response)

            # Log LLM evidence-based analysis
            logger.info(f"\n🧠 LLM Technical Evidence Analysis:")
            logger.info(f"   Market Regime: {response_data.get('market_regime', 'N/A')}")
            logger.info(f"   Indicator Tension: {response_data.get('indicator_tension_analysis', 'N/A')}")
            logger.info(f"   Dead Cat vs Value: {response_data.get('dead_cat_vs_value', 'N/A')}")
            logger.info(f"   Pivot Zones: {response_data.get('pivot_zones', {})}")

            # Return the evidence data (no signal generation)
            return {
                "market_regime": response_data.get('market_regime', 'Neutral Consolidation'),
                "indicator_tension_analysis": response_data.get('indicator_tension_analysis', 'No analysis available'),
                "dead_cat_vs_value": response_data.get('dead_cat_vs_value', 'Insufficient data'),
                "pivot_zones": response_data.get('pivot_zones', {})
            }

        except Exception as e:
            logger.warning(f"⚠️ LLM evidence generation failed: {e}")
            logger.warning(f"   Returning default evidence structure")
            import traceback
            logger.debug(traceback.format_exc())

            # Fallback to default evidence structure with multi-period levels
            return {
                "market_regime": "Analysis Failed",
                "indicator_tension_analysis": f"LLM analysis failed: {str(e)}",
                "dead_cat_vs_value": "Unable to categorize due to analysis failure",
                "pivot_zones": {
                    "ma200_level": sma_200,
                    "ma50_level": sma_50,
                    "ma20_level": sma_20,
                    "bb_middle": bb_middle
                }
            }

    def _save_technical_results(
        self,
        ticker: str,
        df,
        ta_report: TAReport,
        time_mode: str,
        end_date: Optional[str] = None
    ):
        """
        Save technical analysis results to files for audit and debugging.

        Args:
            ticker: Stock ticker symbol
            df: DataFrame with indicators
            ta_report: Generated TAReport
            time_mode: "realtime" or "historical"
            end_date: Optional end date for filename (format: YYYY-MM-DD)
        """
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Extract year from end_date or use timestamp
        if end_date:
            year = datetime.strptime(end_date, "%Y-%m-%d").year
            filename_base = f"TA_report_{ticker}_{year}"
        else:
            filename_base = f"TA_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # JSON file for TAReport
        json_path = self.output_dir / f"{filename_base}.json"

        # CSV file for full data with indicators
        csv_path = self.output_dir / f"{filename_base}_data.csv"

        # Markdown file for human reading
        md_path = self.output_dir / f"{filename_base}.md"
        
        try:
            # Save TAReport as JSON
            report_dict = ta_report.model_dump()

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
            
            # Save full data with indicators as CSV
            df.to_csv(csv_path)
            
            # Save Markdown summary
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Technical Analyst Report: {ticker}\n\n")
                f.write(f"**Report Type:** Technical Analysis (TA)\n")
                f.write(f"**Ticker:** {ticker}\n")
                if end_date:
                    year = datetime.strptime(end_date, "%Y-%m-%d").year
                    f.write(f"**Fiscal Year:** {year}\n")
                f.write(f"**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Data Range:** {df.index[0].date()} to {df.index[-1].date()}\n")
                f.write(f"**Trading Days:** {len(df)}\n")
                f.write(f"**Analysis Mode:** {time_mode}\n\n")
                f.write("---\n\n")
                
                f.write("## Technical Report Summary\n\n")
                f.write(f"- **Ticker:** {ta_report.ticker}\n")
                f.write(f"- **RSI(14):** {ta_report.rsi_14:.2f}\n")
                f.write(f"- **BB Lower Touch:** {ta_report.bb_lower_touch}\n")
                f.write(f"- **Price to MA(200) Distance:** {ta_report.price_to_ma200_dist:+.2%}\n")
                f.write(f"- **ATR Volatility:** ${ta_report.volatility_atr:.2f}\n")
                f.write(f"- **Market Regime:** {ta_report.market_regime}\n\n")

                f.write("---\n\n")

                f.write("## Expert Evidence Analysis\n\n")
                f.write(f"**Indicator Tension Analysis:**\n{ta_report.indicator_tension_analysis}\n\n")
                f.write(f"**Dead Cat vs Value Entry:**\n{ta_report.dead_cat_vs_value}\n\n")
                f.write(f"**Pivot Zones:**\n")
                for zone, level in ta_report.pivot_zones.items():
                    f.write(f"- {zone}: ${level:.2f}\n")
                f.write("\n")

                f.write("---\n\n")

                f.write("## Latest Price Data\n\n")
                latest = df.iloc[-1]
                f.write(f"- **Date:** {latest.name.date()}\n")
                f.write(f"- **Close:** ${latest['Close']:.2f}\n")
                f.write(f"- **High:** ${latest['High']:.2f}\n")
                f.write(f"- **Low:** ${latest['Low']:.2f}\n")
                f.write(f"- **Volume:** {latest['Volume']:,.0f}\n\n")
                
                f.write("---\n\n")
                
                f.write("## Technical Indicators (Latest)\n\n")
                f.write(f"- **RSI(14):** {latest['RSI']:.2f}\n")
                f.write(f"- **BB Lower:** ${latest['BB_Lower']:.2f}\n")
                f.write(f"- **BB Middle:** ${latest['BB_Middle']:.2f}\n")
                f.write(f"- **BB Upper:** ${latest['BB_Upper']:.2f}\n")
                f.write(f"- **SMA(200):** ${latest['SMA_200']:.2f}\n")
                f.write(f"- **ATR(14):** ${latest['ATR']:.2f}\n\n")
                
                f.write("---\n\n")

                f.write("## Recent Price History (Last 10 Days)\n\n")
                f.write("| Date | Close | RSI | BB Lower | BB Upper | SMA(200) |\n")
                f.write("|------|-------|-----|----------|----------|----------|\n")

                for idx in range(max(0, len(df) - 10), len(df)):
                    row = df.iloc[idx]
                    f.write(f"| {row.name.date()} | ${row['Close']:.2f} | {row['RSI']:.1f} | "
                           f"${row['BB_Lower']:.2f} | ${row['BB_Upper']:.2f} | ${row['SMA_200']:.2f} |\n")

                f.write("\n---\n\n")
                f.write(f"Full data saved to: {csv_path.name}\n")
            
            logger.info(f"📁 Technical analysis results saved:")
            logger.info(f"   JSON: {json_path}")
            logger.info(f"   CSV:  {csv_path}")
            logger.info(f"   MD:   {md_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to save technical results: {e}")
    
    def _create_default_report(self, ticker: str, error_message: str = "") -> TAReport:
        """
        Create a default TAReport when calculation fails.

        Args:
            ticker: Stock ticker symbol
            error_message: Optional error message for logging

        Returns:
            TAReport with default/neutral values
        """
        if error_message:
            logger.warning(f"⚠️ Creating default TAReport: {error_message}")

        return TAReport(
            ticker=ticker,
            rsi_14=50.0,  # Neutral RSI
            bb_lower_touch=False,
            price_to_ma20_dist=0.0,
            price_to_ma50_dist=0.0,
            price_to_ma200_dist=0.0,
            volatility_atr=0.0,
            market_regime="Analysis Failed",
            indicator_tension_analysis=f"Unable to perform analysis: {error_message}",
            dead_cat_vs_value="Insufficient data for categorization",
            pivot_zones={}
        )

