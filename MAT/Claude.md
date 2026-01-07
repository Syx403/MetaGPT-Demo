* **Test-Driven Development** : After any logic change, you must automatically run tests until they pass. If tests fail, diagnose and fix the code autonomously.

# MAT: Project Guidelines & Standards

## 1. Core Architecture Values

- **MetaGPT Pub-Sub Framework**: All communication must go through the `InvestmentEnvironment` using the Publish-Subscribe pattern.
- **Schema Sovereignty**: Every agent MUST use the Pydantic models defined in `schemas.py` for input/output. No raw strings or dictionaries for inter-agent reports.
- **Decoupled Roles**: Agents must inherit from `BaseInvestmentAgent`. They observe messages from the environment and publish results back to it.

## 2. Standardized Data Flow

- **Trigger**: The `InvestmentEnvironment` initializes and broadcasts the target `Ticker`.
- **Parallel Analysis**:
  - **Research Analyst (RA)**: Observes Ticker -> Queries RAGFlow -> Publishes `FAReport`.
  - **Technical Analyst (TA)**: Observes Ticker -> Computes via yfinance/pandas-ta -> Publishes `TAReport`.
  - **Sentiment Analyst (SA)**: Observes Ticker -> Searches via Tavily -> Publishes `SAReport`.
- **Reactive Decision**:
  - **Alpha Strategist (AS)**: Observes all reports -> Implements **Scheme C (Active Inquiry)** logic -> Publishes final `StrategyDecision`.

## 3. Hard Bans (Prohibited Actions)

- **No Summary MDs**: Do not generate post-execution summary markdown files unless explicitly requested.
- **No Direct Calls**: Agents are strictly forbidden from calling other agents' methods directly. Use `publish_message` only.
- **Language Lock**: All dialogue, code comments, and documentation must be in **English**.
- **Schema Stability**: Do not modify `schemas.py` without explicit confirmation.

## 4. Engineering Standards

- **File Header Requirement**: Every new or modified file must include:
  ```python
  """
  Filename: MetaGPT-Ewan/MAT/<path>/<filename>.py
  Created Date: <Date>
  Author: Ewan Su
  Description: <Brief description>
  """
  ```

* **Test-Driven Development** : Automatically run tests after logic changes. Diagnose and fix code autonomously if tests fail.
* **One-Click Testing** : Always provide a single command (e.g., `pytest` or a script) for manual verification.

## 4. Environment Context

* **Stock Market** : Focused on the US Stock Market.
* **Tech Stack** : MetaGPT, RAGFlow API, yfinance, pandas-ta, Tavily API.
