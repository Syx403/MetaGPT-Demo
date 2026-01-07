# CalculateTechnicals Action - User Guide

## Overview

The `CalculateTechnicals` action is a core component of the MAT (Multi-Agent Trading) framework that retrieves stock price data and calculates technical indicators to generate trading signals based on mean reversion strategies.

**Purpose**: Automate technical analysis with flexible time-alignment to support both real-time trading and historical backtesting.

## Key Features

1. **Flexible Time Windows**:
   - Real-time: Last 60 days (default)
   - Historical: Custom date ranges (e.g., 2022-01-01 to 2022-12-31)
   - Time-aligned with fundamental data for consistent analysis

2. **Technical Indicators** (calculated using `pandas_ta`):
   - RSI (Relative Strength Index, 14-period)
   - Bollinger Bands (20-period, 2 std deviations)
   - SMA (Simple Moving Average, 200-period)
   - ATR (Average True Range, 14-period)

3. **Mean Reversion Strategy**:
   - STRONG_BUY: RSI < 30 AND Close < Lower BB
   - BUY: RSI < 40 AND Close < Lower BB
   - NEUTRAL: No extreme conditions
   - SELL: RSI > 60 AND Close > Upper BB
   - STRONG_SELL: RSI > 70 AND Close > Upper BB

4. **Data Persistence**: Saves results to JSON, CSV, and Markdown for audit

---

## Architecture

```
┌─────────────────┐
│  User/Agent     │
└────────┬────────┘
         │
         │ run(ticker, start_date, end_date)
         ▼
┌─────────────────────────────────┐
│  CalculateTechnicals Action     │
│  ┌───────────────────────────┐  │
│  │ 1. Determine Time Window  │  │
│  │    - Custom dates or      │  │
│  │    - Default 60 days      │  │
│  └─────────────┬─────────────┘  │
│                ▼                 │
│  ┌───────────────────────────┐  │
│  │ 2. Download Stock Data    │  │
│  │    using yfinance         │  │
│  └─────────────┬─────────────┘  │
│                ▼                 │
│  ┌───────────────────────────┐  │
│  │ 3. Calculate Indicators   │  │
│  │    using pandas_ta        │  │
│  │    - RSI(14)              │  │
│  │    - BB(20, 2)            │  │
│  │    - SMA(200)             │  │
│  │    - ATR(14)              │  │
│  └─────────────┬─────────────┘  │
│                ▼                 │
│  ┌───────────────────────────┐  │
│  │ 4. Apply Mean Reversion   │  │
│  │    Logic                  │  │
│  └─────────────┬─────────────┘  │
│                ▼                 │
│  ┌───────────────────────────┐  │
│  │ 5. Return TAReport        │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  TAReport (Structured Output)   │
│  - ticker: str                  │
│  - rsi_14: float                │
│  - bb_lower_touch: bool         │
│  - price_to_ma200_dist: float   │
│  - volatility_atr: float        │
│  - technical_signal: enum       │
└─────────────────────────────────┘
```

---

## Configuration

### Step 1: Install Dependencies

```bash
pip install yfinance pandas_ta
```

### Step 2: Configure Settings (Optional)

Add to your `config/config2.yaml`:

```yaml
# Technical Analysis Settings
technicals:
  default_period: 60  # Default period in days for real-time
  rsi_period: 14      # RSI period
  bb_period: 20       # Bollinger Bands period
  bb_std: 2.0         # Bollinger Bands std deviation
  sma_period: 200     # SMA period
  atr_period: 14      # ATR period
  
  # Mean reversion thresholds
  mean_reversion_thresholds:
    rsi_oversold_strong: 30.0   # STRONG_BUY
    rsi_oversold: 40.0          # BUY
    rsi_overbought: 60.0        # SELL
    rsi_overbought_strong: 70.0 # STRONG_SELL

# MAT Framework
mat:
  technical_output_dir: "MAT/data/technical_results"
```

---

## Usage

### Basic Usage - Real-time Analysis

```python
import asyncio
from MAT.actions.calculate_technicals import CalculateTechnicals

async def analyze_realtime():
    # Initialize the action
    action = CalculateTechnicals()
    
    # Get technical analysis for last 60 days
    ta_report = await action.run(ticker="AAPL")
    
    # Access results
    print(f"Ticker: {ta_report.ticker}")
    print(f"RSI(14): {ta_report.rsi_14:.2f}")
    print(f"BB Lower Touch: {ta_report.bb_lower_touch}")
    print(f"Price to MA(200): {ta_report.price_to_ma200_dist:+.2%}")
    print(f"ATR Volatility: ${ta_report.volatility_atr:.2f}")
    print(f"Signal: {ta_report.technical_signal.value}")

asyncio.run(analyze_realtime())
```

### Historical Analysis with Time-Alignment

```python
async def analyze_historical():
    action = CalculateTechnicals()
    
    # Analyze 2022 data (to match RAG fundamental reports)
    ta_report = await action.run(
        ticker="AAPL",
        start_date="2022-01-01",
        end_date="2022-12-31"
    )
    
    print(f"Historical Signal (2022): {ta_report.technical_signal.value}")
    print(f"Historical RSI (2022): {ta_report.rsi_14:.2f}")

asyncio.run(analyze_historical())
```

### Integration with Technical Analyst Agent

```python
from MAT.roles.base_agent import BaseAgent
from MAT.actions.calculate_technicals import CalculateTechnicals
from MAT.schemas import TAReport

class TechnicalAnalyst(BaseAgent):
    """Technical Analyst using mean reversion strategy."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CalculateTechnicals])
    
    async def analyze_technicals(
        self,
        ticker: str,
        start_date: str = None,
        end_date: str = None
    ) -> TAReport:
        """Perform technical analysis."""
        action = CalculateTechnicals()
        
        ta_report = await action.run(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date
        )
        
        # Log analysis
        self.logger.info(f"📈 Technical Analysis for {ta_report.ticker}")
        self.logger.info(f"   Signal: {ta_report.technical_signal.value}")
        self.logger.info(f"   RSI: {ta_report.rsi_14:.2f}")
        
        return ta_report
```

---

## TAReport Schema

| Field | Type | Description | Range/Format |
|-------|------|-------------|--------------|
| `ticker` | `str` | Stock ticker symbol | - |
| `rsi_14` | `float` | RSI over 14 periods | 0.0 to 100.0 |
| `bb_lower_touch` | `bool` | Whether price touched/broke lower BB | True/False |
| `price_to_ma200_dist` | `float` | Distance % from 200-day MA | Decimal (e.g., -0.05 = -5%) |
| `volatility_atr` | `float` | Average True Range for volatility | Positive float (USD) |
| `technical_signal` | `SignalIntensity` | Trading signal | STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL |

---

## Mean Reversion Logic

### Signal Generation Rules

| Signal | Condition | Interpretation |
|--------|-----------|----------------|
| **STRONG_BUY** | RSI < 30 AND Close < BB_Lower | Severely oversold - strong mean reversion opportunity |
| **BUY** | RSI < 40 AND Close < BB_Lower | Oversold - potential mean reversion |
| **NEUTRAL** | No extreme conditions | Wait for better entry/exit points |
| **SELL** | RSI > 60 AND Close > BB_Upper | Overbought - consider taking profits |
| **STRONG_SELL** | RSI > 70 AND Close > BB_Upper | Severely overbought - high risk of correction |

### Why Mean Reversion?

Mean reversion strategies work on the principle that prices tend to return to their average over time. When a stock becomes extremely oversold (low RSI + price below lower Bollinger Band), there's a higher probability of a bounce back (mean reversion).

**Key Advantages**:
- Clear entry/exit signals
- Works well in range-bound markets
- Reduces emotional trading decisions
- ATR provides dynamic stop-loss levels

---

## Time-Alignment for Testing

### Problem: Misaligned Data Sources

When testing with historical fundamental data (e.g., 2022 10-K reports from RAGFlow), you need technical data from the same period for accurate analysis.

### Solution: Flexible Time Windows

```python
# For testing with 2022 RAG reports
ta_report = await action.run(
    ticker="AAPL",
    start_date="2022-01-01",
    end_date="2022-12-31"
)
```

### Example: Aligned Analysis

```python
async def aligned_analysis():
    """Analyze with time-aligned FA and TA data."""
    from MAT.actions.retrieve_rag_data import RetrieveRAGData
    from MAT.actions.calculate_technicals import CalculateTechnicals
    
    ticker = "AAPL"
    
    # Both use 2022 data
    rag_action = RetrieveRAGData()
    ta_action = CalculateTechnicals()
    
    # RAG retrieves 2022 10-K data
    fa_report = await rag_action.run(ticker=ticker)
    
    # TA uses 2022 price data
    ta_report = await ta_action.run(
        ticker=ticker,
        start_date="2022-01-01",
        end_date="2022-12-31"
    )
    
    # Now both reports are from 2022 - aligned!
    print(f"FA (2022): Growth Healthy = {fa_report.is_growth_healthy}")
    print(f"TA (2022): Signal = {ta_report.technical_signal.value}")
```

---

## Testing

### Run Test Script

```bash
# Real-time analysis (last 60 days)
python MAT/test_script/test_calculate_technicals.py --mode realtime

# Historical analysis (2022)
python MAT/test_script/test_calculate_technicals.py --mode historical

# Custom date range
python MAT/test_script/test_calculate_technicals.py --mode custom --start 2022-01-01 --end 2022-12-31 --ticker AAPL

# Compare real-time vs historical
python MAT/test_script/test_calculate_technicals.py --mode comparison
```

### Expected Output

```
================================================================================
📈 CALCULATE TECHNICALS ACTION: AAPL
================================================================================
📅 Time Window: 2022-01-01 to 2022-12-31 (Historical)
🌐 Downloading stock data from Yahoo Finance...
   Downloaded historical data: 2022-01-01 to 2022-12-31
   Data range: 2022-01-03 to 2022-12-30
   Trading days: 251
✅ Downloaded 251 trading days of data
🔢 Calculating technical indicators...
   ✅ RSI(14) calculated
   ✅ Bollinger Bands(20, 2.0) calculated
   ✅ SMA(200) calculated
   ✅ ATR(14) calculated
   📊 Dropped 199 rows with NaN (warm-up period)
   📊 Valid data points: 52

📊 Technical Metrics (as of 2022-12-30):
   Close Price: $129.93
   RSI(14): 45.32
   BB Lower: $128.45, BB Upper: $145.67
   SMA(200): $142.18
   Price to MA(200): -8.62%
   ATR(14): $2.45
   BB Lower Touch: False
   Signal: NEUTRAL

================================================================================
✅ TECHNICAL ANALYSIS COMPLETE for AAPL
📊 RSI(14): 45.32
📊 BB Lower Touch: False
📊 Price to MA(200) Distance: -8.62%
📊 ATR Volatility: $2.45
📊 Technical Signal: NEUTRAL
================================================================================
```

---

## Output Files

The action saves three types of files:

### 1. JSON File - TAReport

```json
{
  "ticker": "AAPL",
  "rsi_14": 45.32,
  "bb_lower_touch": false,
  "price_to_ma200_dist": -0.0862,
  "volatility_atr": 2.45,
  "technical_signal": "NEUTRAL"
}
```

### 2. CSV File - Full Data with Indicators

| Date | Open | High | Low | Close | Volume | RSI | BB_Lower | BB_Upper | SMA_200 | ATR |
|------|------|------|-----|-------|--------|-----|----------|----------|---------|-----|
| 2022-12-30 | 130.15 | 131.50 | 129.50 | 129.93 | 95M | 45.32 | 128.45 | 145.67 | 142.18 | 2.45 |

### 3. Markdown File - Human-Readable Report

```markdown
# Technical Analysis Report: AAPL

**Generated:** 20260101_123456
**Mode:** historical
**Data Range:** 2022-01-03 to 2022-12-30
**Trading Days:** 251

---

## Technical Report Summary

- **Ticker:** AAPL
- **RSI(14):** 45.32
- **BB Lower Touch:** False
- **Price to MA(200) Distance:** -8.62%
- **ATR Volatility:** $2.45
- **Technical Signal:** NEUTRAL

---

## Signal Interpretation

**NEUTRAL** - No extreme conditions. Wait for better entry/exit points.

---

## Recent Price History (Last 10 Days)

| Date | Close | RSI | BB Lower | BB Upper | Signal |
|------|-------|-----|----------|----------|--------|
| 2022-12-30 | $129.93 | 45.3 | $128.45 | $145.67 | NEUTRAL |
...
```

---

## Troubleshooting

### Issue: "yfinance not installed"

**Solution**:
```bash
pip install yfinance
```

### Issue: "pandas_ta not installed"

**Solution**:
```bash
pip install pandas_ta
```

### Issue: "No data returned for ticker"

**Possible Causes**:
1. Invalid ticker symbol
2. Market closed (real-time mode)
3. Historical date range too far back
4. Network connection issues

**Solution**:
```python
# Verify ticker exists
import yfinance as yf
stock = yf.Ticker("AAPL")
print(stock.info)  # Should show company info
```

### Issue: "All data dropped after indicator calculation"

**Cause**: Insufficient data for indicators (need at least 200+ days for SMA(200))

**Solution**:
```python
# Use longer period or adjust indicator settings
ta_report = await action.run(
    ticker="AAPL",
    start_date="2021-01-01",  # Longer period
    end_date="2022-12-31"
)
```

---

## API Reference

### CalculateTechnicals.run()

```python
async def run(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> TAReport
```

**Parameters**:
- `ticker` (str): Stock ticker symbol (e.g., "AAPL", "KO")
- `start_date` (Optional[str]): Start date in "YYYY-MM-DD" format. If None, uses default period.
- `end_date` (Optional[str]): End date in "YYYY-MM-DD" format. If None, uses default period.

**Returns**:
- `TAReport`: Structured technical analysis report

**Example**:
```python
# Real-time
ta_report = await action.run("AAPL")

# Historical
ta_report = await action.run("AAPL", "2022-01-01", "2022-12-31")
```

---

## Best Practices

1. **Time Alignment**: Always align technical analysis period with fundamental data period
2. **Sufficient Data**: Ensure at least 200+ trading days for SMA(200) calculation
3. **Market Hours**: Real-time data only available during market hours (use historical for testing)
4. **Indicator Tuning**: Adjust RSI/BB thresholds based on volatility regime
5. **Risk Management**: Use ATR for dynamic stop-loss placement

---

## Advanced Customization

### Custom Thresholds

```python
# More aggressive mean reversion
action = CalculateTechnicals(
    rsi_oversold_strong=25.0,  # Lower threshold
    rsi_oversold=35.0,
    rsi_overbought=65.0,
    rsi_overbought_strong=75.0
)
```

### Custom Indicator Periods

```python
# Faster indicators for day trading
action = CalculateTechnicals(
    rsi_period=9,      # Faster RSI
    bb_period=10,      # Faster BB
    sma_period=50      # Shorter MA
)
```

---

## Comparison with Other Actions

| Aspect | CalculateTechnicals | RetrieveRAGData | SearchDeepDive |
|--------|-------------------|-----------------|----------------|
| **Purpose** | Technical signals | Fundamental metrics | Sentiment/news |
| **Data Source** | yfinance | RAGFlow API | Tavily API |
| **Output** | `TAReport` | `FAReport` | `InvestigationReport` |
| **Time Sensitivity** | High (price changes) | Low (quarterly reports) | Medium (news cycle) |
| **Agent** | Technical Analyst | Research Analyst | Sentiment Analyst |

---

## Related Actions

- **RetrieveRAGData**: Retrieves fundamental data to complement technical analysis
- **SearchDeepDive**: Provides sentiment context for technical signals
- **PublishTAReport**: Publishes TAReport to the environment

---

## License

Part of the MAT (Multi-Agent Trading) framework by Ewan Su.

---

## Contact & Support

For issues, questions, or contributions, please refer to the main MAT documentation.

