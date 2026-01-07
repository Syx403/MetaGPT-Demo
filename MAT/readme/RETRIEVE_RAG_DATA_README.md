# RetrieveRAGData Action - User Guide

## Overview

The `RetrieveRAGData` action is a powerful component of the MAT (Multi-Agent Trading) framework that retrieves fundamental data from a RAGFlow API and synthesizes it into a structured `FAReport` (Fundamental Analysis Report).

**Purpose**: Automate the extraction and analysis of fundamental financial data for a given stock ticker by leveraging RAG (Retrieval-Augmented Generation) technology.

## Key Features

1. **Targeted Queries**: Performs 4 specific queries to RAGFlow:
   - Revenue Growth (YoY trends)
   - Gross Margin (profit margin analysis)
   - Guidance (management outlook)
   - Key Risks (top risk factors)

2. **LLM Synthesis**: Uses Claude/GPT to distill retrieved chunks into a structured `FAReport`

3. **Audit Trail**: Saves all retrieved data to JSON and Markdown files for debugging

4. **Graceful Fallback**: Returns default values when RAGFlow is not configured

5. **Configurable**: All settings managed through `config/config2.yaml`

---

## Architecture

```
┌─────────────────┐
│  User/Agent     │
└────────┬────────┘
         │
         │ run(ticker="NVDA")
         ▼
┌─────────────────────────────────┐
│  RetrieveRAGData Action         │
│  ┌───────────────────────────┐  │
│  │ 1. Check Configuration    │  │
│  └─────────────┬─────────────┘  │
│                ▼                 │
│  ┌───────────────────────────┐  │
│  │ 2. Send 4 POST Requests   │  │
│  │    to RAGFlow API         │  │
│  │    - Revenue Growth       │  │
│  │    - Gross Margin         │  │
│  │    - Guidance             │  │
│  │    - Key Risks            │  │
│  └─────────────┬─────────────┘  │
│                ▼                 │
│  ┌───────────────────────────┐  │
│  │ 3. Combine All Chunks     │  │
│  └─────────────┬─────────────┘  │
│                ▼                 │
│  ┌───────────────────────────┐  │
│  │ 4. LLM Synthesis          │  │
│  │    (Claude/GPT)           │  │
│  └─────────────┬─────────────┘  │
│                ▼                 │
│  ┌───────────────────────────┐  │
│  │ 5. Return FAReport        │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  FAReport (Structured Output)   │
│  - ticker: str                  │
│  - revenue_growth_yoy: float    │
│  - gross_margin: float          │
│  - fcf_growth: float            │
│  - guidance_sentiment: float    │
│  - key_risks: List[str]         │
│  - is_growth_healthy: bool      │
└─────────────────────────────────┘
```

---

## Configuration

### Step 1: Set Up RAGFlow API

Add the following section to your `config/config2.yaml`:

```yaml
# RAGFlow API for fundamental data retrieval
ragflow:
  endpoint: "http://your-ragflow-ip:9380/api/v1/retrieval"
  api_key: "your-ragflow-api-key-here"
  dataset_id: "your-dataset-id-here"
  top_k: 5  # Number of chunks to retrieve per query
```

**Parameters:**
- `endpoint`: The RAGFlow API endpoint URL (replace `your-ragflow-ip` with your actual IP)
- `api_key`: Your RAGFlow API authentication key
- `dataset_id`: The ID of the dataset containing financial data
- `top_k`: Number of relevant chunks to retrieve per query (default: 5)

### Step 2: Configure Output Directory (Optional)

The default output directory is `MAT/data/rag_results`. To customize:

```yaml
mat:
  rag_output_dir: "MAT/data/rag_results"  # Custom path
```

---

## Usage

### Basic Usage

```python
import asyncio
from MAT.actions.retrieve_rag_data import RetrieveRAGData

async def analyze_ticker():
    # Initialize the action
    action = RetrieveRAGData()
    
    # Retrieve fundamental data for NVDA
    fa_report = await action.run(ticker="NVDA")
    
    # Access the results
    print(f"Ticker: {fa_report.ticker}")
    print(f"Revenue Growth: {fa_report.revenue_growth_yoy:.2%}")
    print(f"Gross Margin: {fa_report.gross_margin:.2%}")
    print(f"FCF Growth: {fa_report.fcf_growth:.2%}")
    print(f"Guidance Sentiment: {fa_report.guidance_sentiment:.2f}")
    print(f"Key Risks: {fa_report.key_risks}")
    print(f"Is Growth Healthy: {fa_report.is_growth_healthy}")

# Run the async function
asyncio.run(analyze_ticker())
```

### Using with Custom LLM Callback

```python
async def custom_llm_callback(prompt: str) -> str:
    """Custom LLM function using your own model."""
    # Your LLM logic here
    response = your_llm_model.generate(prompt)
    return response

async def analyze_with_custom_llm():
    action = RetrieveRAGData()
    
    # Pass custom LLM callback
    fa_report = await action.run(
        ticker="AAPL",
        llm_callback=custom_llm_callback
    )
    
    return fa_report
```

### Integration with Research Analyst Agent

```python
from MAT.roles.base_agent import BaseAgent
from MAT.actions.retrieve_rag_data import RetrieveRAGData
from MAT.schemas import FAReport

class ResearchAnalyst(BaseAgent):
    """Research Analyst agent using RAGFlow for fundamental analysis."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add RetrieveRAGData to actions
        self.set_actions([RetrieveRAGData])
    
    async def analyze_fundamentals(self, ticker: str) -> FAReport:
        """Perform fundamental analysis using RAG data."""
        action = RetrieveRAGData()
        fa_report = await action.run(ticker=ticker)
        
        # Log results
        self._log_analysis_results(fa_report)
        
        return fa_report
    
    def _log_analysis_results(self, report: FAReport):
        """Log the analysis results."""
        self.logger.info(f"📊 Fundamental Analysis for {report.ticker}")
        self.logger.info(f"   Revenue Growth: {report.revenue_growth_yoy:.2%}")
        self.logger.info(f"   Gross Margin: {report.gross_margin:.2%}")
        self.logger.info(f"   Growth Healthy: {report.is_growth_healthy}")
```

---

## FAReport Schema

The action returns a structured `FAReport` object with the following fields:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `ticker` | `str` | Stock ticker symbol | - |
| `revenue_growth_yoy` | `float` | Year-over-year revenue growth rate | Decimal (e.g., 0.15 = 15%) |
| `gross_margin` | `float` | Gross profit margin | Decimal (e.g., 0.65 = 65%) |
| `fcf_growth` | `float` | Free cash flow growth rate | Decimal (e.g., 0.10 = 10%) |
| `guidance_sentiment` | `float` | Management guidance sentiment score | Range: -1 (very negative) to +1 (very positive) |
| `key_risks` | `List[str]` | Top 3-5 risk factors | Maximum 5 items |
| `is_growth_healthy` | `bool` | Whether fundamentals meet health thresholds | `True` or `False` |

### Growth Health Thresholds

A company is considered to have "healthy growth" if:
- Revenue growth > 10% YoY
- Gross margin > 40%
- Positive FCF growth
- Guidance sentiment >= 0 (neutral or positive)

---

## Testing

### Run Test Script

```bash
# Test single ticker
python MAT/test_script/test_retrieve_rag_data.py --mode single

# Test multiple tickers
python MAT/test_script/test_retrieve_rag_data.py --mode multiple
```

### Expected Output

```
================================================================================
🧪 Testing RetrieveRAGData Action
================================================================================
============================================================
📋 MAT Configuration Status
============================================================
Project Root: /path/to/MetaGPT-Ewan
Config File: /path/to/MetaGPT-Ewan/config/config2.yaml
OpenAI API: ✅ Configured
Tavily API: ✅ Configured
RAGFlow API: ✅ Configured
...
============================================================

================================================================================
📚 RETRIEVE RAG DATA ACTION: NVDA
================================================================================
🔍 Performing 4 targeted queries to RAGFlow...
📋 Query [Revenue Growth]: What is the year-over-year revenue growth rate...
   ✅ Retrieved 5 chunks
📋 Query [Gross Margin]: What is the gross profit margin...
   ✅ Retrieved 5 chunks
📋 Query [Guidance]: What is the management guidance...
   ✅ Retrieved 5 chunks
📋 Query [Key Risks]: What are the top 3-5 key risk factors...
   ✅ Retrieved 5 chunks
✅ Total chunks retrieved: 20
📁 RAG results saved:
   JSON: MAT/data/rag_results/NVDA_rag_20251229_123456.json
   MD:   MAT/data/rag_results/NVDA_rag_20251229_123456.md
✅ FAReport synthesized successfully

================================================================================
✅ RAG DATA RETRIEVAL COMPLETE for NVDA
📊 Revenue Growth YoY: 25.50%
📊 Gross Margin: 72.30%
📊 FCF Growth: 18.20%
📊 Guidance Sentiment: 0.75
📊 Key Risks: 3 identified
📊 Growth Healthy: True
================================================================================
```

---

## Troubleshooting

### Issue: "RAGFlow not configured"

**Solution**: Ensure you have added the `ragflow` section to `config/config2.yaml`:

```yaml
ragflow:
  endpoint: "http://your-ragflow-ip:9380/api/v1/retrieval"
  api_key: "your-api-key"
  dataset_id: "your-dataset-id"
  top_k: 5
```

### Issue: "aiohttp not installed"

**Solution**: Install the required dependency:

```bash
pip install aiohttp
```

### Issue: RAGFlow API returns 401 Unauthorized

**Solution**: 
1. Verify your API key is correct
2. Check if the API key has expired
3. Ensure the Authorization header format is correct (`Bearer <api_key>`)

### Issue: RAGFlow API returns 404 Not Found

**Solution**:
1. Verify the endpoint URL is correct
2. Check if the dataset_id exists
3. Test the endpoint with a tool like `curl`:

```bash
curl -X POST "http://your-ragflow-ip:9380/api/v1/retrieval" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "dataset_id": "your-dataset-id", "top_k": 5}'
```

### Issue: LLM returns default values

**Solution**:
1. Check if RAGFlow returned any chunks (look at saved files in `MAT/data/rag_results/`)
2. Verify the LLM is properly configured in `config/config2.yaml`
3. Check the logs for LLM parsing errors

---

## Output Files

The action saves all retrieved data for audit and debugging:

### JSON File Format

```json
[
  {
    "content": "NVIDIA reported revenue growth of 25.5% YoY...",
    "score": 0.92,
    "metadata": {...},
    "query_category": "Revenue Growth"
  },
  ...
]
```

### Markdown File Format

```markdown
# RAGFlow Retrieval Results: NVDA

**Timestamp:** 20251229_123456
**Total Chunks:** 20

---

## Revenue Growth (5 chunks)

### Chunk 1

**Score:** 0.92

**Content:**
```
NVIDIA reported revenue growth of 25.5% YoY...
```

**Metadata:** {...}

---
...
```

---

## API Reference

### RetrieveRAGData.run()

```python
async def run(
    ticker: str,
    llm_callback: Optional[Any] = None
) -> FAReport
```

**Parameters:**
- `ticker` (str): Stock ticker symbol (e.g., "AAPL", "NVDA", "TSLA")
- `llm_callback` (Optional[Callable]): Custom LLM function for synthesis. If None, uses default `self._aask()`

**Returns:**
- `FAReport`: Structured fundamental analysis report

**Raises:**
- No exceptions are raised; errors are logged and default report is returned

---

## Best Practices

1. **Always Configure RAGFlow**: Ensure RAGFlow is properly configured before use
2. **Check Output Files**: Review saved JSON/Markdown files to verify data quality
3. **Monitor API Quota**: RAGFlow may have API rate limits
4. **Customize Queries**: Modify `_retrieve_all_queries()` if you need different data
5. **Validate Results**: Cross-check synthesized data with actual financial reports

---

## Advanced Customization

### Custom Query Categories

You can extend the action to include additional query categories:

```python
queries = [
    # Standard queries
    {"category": "Revenue Growth", "question": "..."},
    {"category": "Gross Margin", "question": "..."},
    {"category": "Guidance", "question": "..."},
    {"category": "Key Risks", "question": "..."},
    
    # Custom queries
    {"category": "R&D Spending", "question": f"What is the R&D spending for {ticker}?"},
    {"category": "Market Share", "question": f"What is the market share of {ticker}?"}
]
```

### Custom LLM Prompt

Modify the `_synthesize_fa_report()` method to customize the LLM prompt for your specific needs.

---

## Related Actions

- **SearchDeepDive**: Performs deep web search for sentiment analysis
- **PublishFAReport**: Publishes the FAReport to the environment
- **ResearchAnalyst**: Agent that uses RetrieveRAGData for fundamental analysis

---

## License

Part of the MAT (Multi-Agent Trading) framework by Ewan Su.

---

## Contact & Support

For issues, questions, or contributions, please refer to the main MAT documentation or create an issue in the repository.

