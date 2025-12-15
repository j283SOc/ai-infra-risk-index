# AI Infrastructure Bubble Monitoring Framework
## Technical Specification Document

**Version:** 1.0.0  
**Status:** Draft  
**Last Updated:** December 2024  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Database Schema](#3-database-schema)
4. [Module Specifications](#4-module-specifications)
5. [Data Sources & Collection Strategies](#5-data-sources--collection-strategies)
6. [ABRI Calculation Methodology](#6-abri-calculation-methodology)
7. [Alerting & Notification System](#7-alerting--notification-system)
8. [Deployment Configuration](#8-deployment-configuration)
9. [Development Workflow](#9-development-workflow)
10. [Future Upgrade Path](#10-future-upgrade-path)
11. [Appendices](#11-appendices)

---

## 1. Executive Summary

### 1.1 Purpose

This document specifies the technical implementation of a monitoring framework designed to track indicators of speculative excess in AI infrastructure investment. The system synthesizes publicly available data into a composite risk index (ABRI — AI Bubble Risk Index) and presents findings via an interactive dashboard with automated alerting.

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Transparency** | Open-source methodology; all calculations reproducible |
| **Low Cost** | $0/month operational cost using free-tier services |
| **Maintainability** | Semi-automated data collection with clear manual intervention points |
| **Extensibility** | Modular architecture supporting future enhancements |
| **Auditability** | Source links preserved for all data points |

### 1.3 Constraints & Limitations

- **Public repository requirement:** Streamlit Community Cloud requires public code
- **Rate limits:** Free APIs impose request limits (documented per source)
- **Data freshness:** Some metrics update quarterly; dashboard reflects collection timestamps
- **SQLite concurrency:** Single-writer limitation acceptable for personal use
- **Calibration uncertainty:** AI-specific metrics have limited historical depth (<3 years)

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GITHUB REPOSITORY                              │
│                         (Public, source of truth)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   /collectors   │  │   /analytics    │  │   /dashboard    │             │
│  │                 │  │                 │  │                 │             │
│  │  equity.py      │  │  correlation.py │  │  app.py         │             │
│  │  credit.py      │  │  abri.py        │  │  components/    │             │
│  │  gpu_pricing.py │  │  signals.py     │  │  pages/         │             │
│  │  sec_edgar.py   │  │                 │  │                 │             │
│  │  news.py        │  │                 │  │                 │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                            │
│                                ▼                                            │
│                    ┌─────────────────────┐                                  │
│                    │    /data            │                                  │
│                    │                     │                                  │
│                    │  manual/            │                                  │
│                    │    templates/       │  ← Extraction templates          │
│                    │    pending/         │  ← Pending manual entries        │
│                    └─────────────────────┘                                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           /.github/workflows                                │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  daily.yml      │  │  weekly.yml     │  │  quarterly.yml  │             │
│  │                 │  │                 │  │                 │             │
│  │  • Equity data  │  │  • Email report │  │  • 10-K/Q       │             │
│  │  • Credit data  │  │  • Full refresh │  │    reminder     │             │
│  │  • News scan    │  │  • ABRI calc    │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
           │                                              │
           │                                              │
           ▼                                              ▼
┌─────────────────────┐                      ┌─────────────────────┐
│      SUPABASE       │                      │     STREAMLIT       │
│    (PostgreSQL)     │◄────────────────────►│   COMMUNITY CLOUD   │
│                     │                      │                     │
│  • Time-series data │                      │  • Dashboard UI     │
│  • ABRI history     │                      │  • Manual input     │
│  • Alert log        │                      │    prompts          │
│  • Deal tracker     │                      │  • Source links     │
└─────────────────────┘                      └─────────────────────┘
           │                                              │
           │                                              │
           ▼                                              ▼
┌─────────────────────┐                      ┌─────────────────────┐
│    EXTERNAL APIs    │                      │    EMAIL (SMTP)     │
│                     │                      │                     │
│  • Yahoo Finance    │                      │  Weekly summaries   │
│  • FRED             │                      │  Threshold alerts   │
│  • SEC EDGAR        │                      │                     │
└─────────────────────┘                      └─────────────────────┘
```

### 2.2 Directory Structure

```
ai-infra-risk-index/
├── .github/
│   └── workflows/
│       ├── daily.yml           # Daily data collection
│       ├── weekly.yml          # Weekly report generation
│       └── quarterly.yml       # Quarterly filing reminder
├── collectors/
│   ├── __init__.py
│   ├── equity.py               # Stock prices, market cap, correlations
│   ├── credit.py               # FRED spreads, bond yields
│   ├── gpu_pricing.py          # GPU rental rate tracking (manual)
│   ├── sec_edgar.py            # 10-K/10-Q filing downloader
│   └── news.py                 # RSS aggregation
├── analytics/
│   ├── __init__.py
│   ├── correlation.py          # Rolling correlation calculations
│   ├── abri.py                 # Composite index computation
│   └── signals.py              # Threshold detection, alerting logic
├── dashboard/
│   ├── app.py                  # Streamlit entry point
│   ├── components/
│   │   ├── __init__.py
│   │   ├── charts.py           # Reusable chart components
│   │   ├── metrics.py          # KPI display cards
│   │   ├── tables.py           # Data tables
│   │   └── manual_input.py     # Manual data entry forms
│   └── pages/
│       ├── 1_Market_Structure.py
│       ├── 2_Credit_Stress.py
│       ├── 3_GPU_Economics.py
│       ├── 4_Hyperscaler_Health.py
│       ├── 5_Deal_Flow.py
│       ├── 6_News_Feed.py
│       └── 7_Manual_Entry.py   # Manual data entry page
├── alerts/
│   ├── __init__.py
│   ├── engine.py               # Alert evaluation
│   └── email.py                # SMTP delivery
├── storage/
│   ├── __init__.py
│   ├── db.py                   # Supabase connection management
│   ├── models.py               # SQLAlchemy ORM models
│   └── queries.py              # Common database queries
├── data/
│   ├── templates/              # Extraction templates for manual entry
│   │   ├── hyperscaler_template.json
│   │   ├── gpu_pricing_template.json
│   │   └── deal_template.json
│   └── pending/                # Queued manual entry tasks
│       └── .gitkeep
├── templates/
│   ├── email_weekly.html       # Weekly report template
│   └── email_alert.html        # Threshold alert template
├── scripts/
│   ├── init_db.py              # Database initialization
│   ├── backfill.py             # Historical data loading
│   └── generate_pending.py     # Generate pending manual entry tasks
├── tests/
│   ├── __init__.py
│   ├── test_collectors.py
│   ├── test_analytics.py
│   └── test_alerts.py
├── docs/
│   ├── METHODOLOGY.md          # ABRI calculation explanation
│   ├── DATA_DICTIONARY.md      # Field definitions
│   ├── MANUAL_PROCEDURES.md    # Semi-automated workflow guides
│   └── BACKFILL_SEQUENCE.md    # Prioritized backfill instructions
├── .env.example                # Environment variable template
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── README.md
└── TECHNICAL_SPECIFICATION.md  # This document
```

### 2.3 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Language** | Python 3.11+ | Ecosystem maturity, library availability |
| **Database** | Supabase (PostgreSQL) | Managed hosting, free tier sufficient, proper concurrent access |
| **ORM** | SQLAlchemy 2.0 | Type hints, PostgreSQL-native features |
| **Dashboard** | Streamlit 1.29+ | Rapid development, free hosting |
| **Charts** | Plotly | Interactive, Streamlit-native integration |
| **Scheduling** | GitHub Actions | Free, reliable, no infrastructure |
| **Email** | smtplib + Gmail | Zero cost, sufficient for low volume |
| **HTTP** | httpx | Modern async-capable client |
| **Data Processing** | pandas, numpy | Industry standard |

#### 2.3.1 Supabase Free Tier Specifications

| Resource | Limit | Expected Usage |
|----------|-------|----------------|
| Database storage | 500 MB | ~50-150 MB |
| Bandwidth | 5 GB/month | <1 GB/month |
| API requests | Unlimited | Low volume |
| Inactivity pause | After 7 days | Prevented by daily GitHub Actions |

**Cost:** $0/month under normal operation. Upgrade path to Pro ($25/month) if storage exceeds 500MB or guaranteed uptime required.

---

## 3. Database Schema

### 3.1 Entity-Relationship Overview

```
┌─────────────────────┐       ┌─────────────────────┐
│   equity_prices     │       │   market_metrics    │
├─────────────────────┤       ├─────────────────────┤
│ PK date             │       │ PK date             │
│ PK ticker           │       │    mag7_weight      │
│    close            │       │    tech_weight      │
│    volume           │       │    nvda_spy_corr    │
│    market_cap       │       │    mag7_spy_corr    │
│    collected_at     │       │    collected_at     │
└─────────────────────┘       └─────────────────────┘

┌─────────────────────┐       ┌─────────────────────┐
│   credit_spreads    │       │   gpu_pricing       │
├─────────────────────┤       ├─────────────────────┤
│ PK date             │       │ PK date             │
│    hy_oas           │       │ PK gpu_model        │
│    ig_bbb_oas       │       │ PK source           │
│    hy_ig_diff       │       │    price_per_hour   │
│    treasury_10y     │       │    notes            │
│    collected_at     │       │    collected_at     │
└─────────────────────┘       └─────────────────────┘

┌─────────────────────┐       ┌─────────────────────┐
│ hyperscaler_metrics │       │   deal_tracker      │
├─────────────────────┤       ├─────────────────────┤
│ PK fiscal_period    │       │ PK deal_id          │
│ PK ticker           │       │    announced_date   │
│    capex            │       │    company          │
│    operating_cf     │       │    amount_usd       │
│    capex_ocf_ratio  │       │    structure_type   │
│    ai_revenue       │       │    counterparty     │
│    ai_revenue_growth│       │    is_circular      │
│    total_debt       │       │    source_url       │
│    adj_debt_equity  │       │    notes            │
│    dso              │       │    entered_at       │
│    source_url       │       └─────────────────────┘
│    entered_at       │
└─────────────────────┘       ┌─────────────────────┐
                              │   abri_history      │
┌─────────────────────┐       ├─────────────────────┤
│   news_items        │       │ PK date             │
├─────────────────────┤       │    concentration    │
│ PK item_id          │       │    correlation      │
│    published_date   │       │    credit_stress    │
│    title            │       │    gpu_deflation    │
│    source           │       │    capex_intensity  │
│    url              │       │    revenue_gap      │
│    summary          │       │    deal_flow        │
│    relevance_score  │       │    composite_score  │
│    collected_at     │       │    calculated_at    │
└─────────────────────┘       └─────────────────────┘

┌─────────────────────┐       ┌─────────────────────┐
│   alert_log         │       │   collection_log    │
├─────────────────────┤       ├─────────────────────┤
│ PK alert_id         │       │ PK log_id           │
│    triggered_at     │       │    collection_type  │
│    metric_name      │       │    started_at       │
│    threshold        │       │    completed_at     │
│    actual_value     │       │    status           │
│    alert_type       │       │    records_added    │
│    sent_at          │       │    error_message    │
│    acknowledged     │       └─────────────────────┘
└─────────────────────┘
```

### 3.2 DDL Statements

```sql
-- Core market data
CREATE TABLE equity_prices (
    date DATE NOT NULL,
    ticker TEXT NOT NULL,
    close REAL NOT NULL,
    volume INTEGER,
    market_cap REAL,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, ticker)
);

CREATE INDEX idx_equity_ticker_date ON equity_prices(ticker, date DESC);

CREATE TABLE market_metrics (
    date DATE PRIMARY KEY,
    mag7_weight REAL,           -- Mag7 % of S&P 500
    tech_weight REAL,           -- Tech sector % of S&P 500
    nvda_spy_corr REAL,         -- 60-day rolling correlation
    mag7_spy_corr REAL,         -- 60-day rolling correlation of equal-weight Mag7
    leveraged_etf_aum REAL,     -- Combined AUM of TQQQ, SOXL, etc.
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Credit market data
CREATE TABLE credit_spreads (
    date DATE PRIMARY KEY,
    hy_oas REAL,                -- High Yield OAS (bps)
    ig_bbb_oas REAL,            -- Investment Grade BBB OAS (bps)
    hy_ig_diff REAL,            -- Computed: hy_oas - ig_bbb_oas
    treasury_10y REAL,          -- 10-year Treasury yield
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- GPU market data (semi-automated)
CREATE TABLE gpu_pricing (
    date DATE NOT NULL,
    gpu_model TEXT NOT NULL,    -- 'H100-80GB', 'H200', 'B200', etc.
    source TEXT NOT NULL,       -- 'vast.ai', 'lambda', 'runpod', etc.
    price_per_hour REAL NOT NULL,
    notes TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, gpu_model, source)
);

CREATE INDEX idx_gpu_model_date ON gpu_pricing(gpu_model, date DESC);

-- Hyperscaler quarterly financials (manual entry)
CREATE TABLE hyperscaler_metrics (
    fiscal_period TEXT NOT NULL,  -- 'Q3 2024', 'FY 2024', etc.
    ticker TEXT NOT NULL,         -- 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA'
    capex REAL,                   -- Capital expenditures ($M)
    operating_cf REAL,            -- Operating cash flow ($M)
    capex_ocf_ratio REAL,         -- Computed: capex / operating_cf
    ai_revenue REAL,              -- AI-attributed revenue where disclosed ($M)
    ai_revenue_growth REAL,       -- QoQ growth rate
    total_debt REAL,              -- Total long-term debt ($M)
    total_equity REAL,            -- Total shareholders' equity ($M)
    adj_debt_equity REAL,         -- Adjusted leverage ratio
    days_sales_outstanding REAL,  -- DSO calculation
    depreciation_expense REAL,    -- For tracking vs capex
    source_url TEXT,              -- Link to 10-K/10-Q
    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (fiscal_period, ticker)
);

-- Deal flow tracking (manual entry)
CREATE TABLE deal_tracker (
    deal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    announced_date DATE NOT NULL,
    company TEXT NOT NULL,
    amount_usd REAL,              -- Deal size in millions
    structure_type TEXT,          -- 'corporate_debt', 'spv', 'sale_leaseback', 'equity'
    counterparty TEXT,
    is_circular INTEGER DEFAULT 0, -- Boolean: involves circular financing
    source_url TEXT,
    notes TEXT,
    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_deal_date ON deal_tracker(announced_date DESC);

-- News aggregation
CREATE TABLE news_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    published_date DATE,
    title TEXT NOT NULL,
    source TEXT,
    url TEXT UNIQUE,
    summary TEXT,
    relevance_score REAL,         -- 0-1 based on keyword matching
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_date ON news_items(published_date DESC);

-- ABRI composite index history
CREATE TABLE abri_history (
    date DATE PRIMARY KEY,
    concentration_score REAL,     -- 0-100, from Mag7 weight
    correlation_score REAL,       -- 0-100, from NVDA-SPY correlation
    credit_stress_score REAL,     -- 0-100, from HY-IG differential
    gpu_deflation_score REAL,     -- 0-100, inverse of H100 pricing
    capex_intensity_score REAL,   -- 0-100, from avg capex/OCF
    revenue_gap_score REAL,       -- 0-100, from capex/revenue ratio
    deal_flow_score REAL,         -- 0-100, from deal acceleration
    composite_score REAL,         -- Weighted average
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert tracking
CREATE TABLE alert_log (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_at TIMESTAMP NOT NULL,
    metric_name TEXT NOT NULL,
    threshold REAL NOT NULL,
    actual_value REAL NOT NULL,
    alert_type TEXT,              -- 'breach_high', 'breach_low', 'trend'
    sent_at TIMESTAMP,
    acknowledged INTEGER DEFAULT 0
);

-- Collection job tracking
CREATE TABLE collection_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_type TEXT NOT NULL, -- 'equity', 'credit', 'gpu', etc.
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT,                   -- 'success', 'partial', 'failed'
    records_added INTEGER DEFAULT 0,
    error_message TEXT
);
```

### 3.3 Schema Versioning Strategy

Given SQLite's limited ALTER TABLE support and the personal-use context, schema changes will be managed via:

1. **Version file:** `data/schema_version.txt` containing current version number
2. **Migration scripts:** `storage/migrations/v001_to_v002.sql` (manual execution)
3. **Backup before migration:** `scripts/backup_db.py` creates timestamped copy

**Future upgrade path:** When moving to PostgreSQL, adopt Alembic for proper migration management.

---

## 4. Module Specifications

### 4.1 Collectors Module

#### 4.1.1 `collectors/equity.py`

**Purpose:** Fetch daily equity prices and compute market structure metrics.

**External Dependencies:**
- `yfinance` — Yahoo Finance API wrapper
- Rate limit: ~2,000 requests/hour (unofficially throttled)

**Public Interface:**

```python
from datetime import date
from typing import Optional
from dataclasses import dataclass

@dataclass
class EquityDataPoint:
    date: date
    ticker: str
    close: float
    volume: int
    market_cap: Optional[float]

@dataclass  
class MarketMetrics:
    date: date
    mag7_weight: float
    tech_weight: float
    nvda_spy_corr: float
    mag7_spy_corr: float
    leveraged_etf_aum: Optional[float]

def fetch_daily_prices(
    tickers: list[str],
    start_date: date,
    end_date: date
) -> list[EquityDataPoint]:
    """
    Fetch closing prices for specified tickers.
    
    Args:
        tickers: List of ticker symbols
        start_date: Inclusive start date
        end_date: Inclusive end date
        
    Returns:
        List of EquityDataPoint objects
        
    Raises:
        CollectionError: If Yahoo Finance API fails
    """
    ...

def compute_market_metrics(
    as_of_date: date,
    lookback_days: int = 60
) -> MarketMetrics:
    """
    Compute concentration and correlation metrics.
    
    Requires equity_prices table to have sufficient history.
    
    Args:
        as_of_date: Calculation date
        lookback_days: Window for rolling correlation
        
    Returns:
        MarketMetrics object with computed values
    """
    ...

def get_spy_constituents_weight(sector: str = "Technology") -> float:
    """
    Fetch current sector weight in S&P 500.
    
    Uses slickcharts.com scraping as backup if yfinance fails.
    """
    ...
```

**Ticker Universe:**

```python
TICKERS = {
    "mag7": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    "hyperscalers": ["MSFT", "GOOGL", "AMZN", "META", "NVDA"],
    "indices": ["SPY", "QQQ", "XLK"],  # S&P 500, Nasdaq 100, Tech Select
    "leveraged_etfs": ["TQQQ", "SOXL", "TECL"],
    "ai_pure_plays": ["CRWV", "AI", "PLTR", "PATH"],  # If trading
}
```

**Error Handling:**

| Error Condition | Handling |
|-----------------|----------|
| API timeout | Retry 3x with exponential backoff |
| Ticker not found | Log warning, skip ticker, continue |
| Rate limit hit | Sleep 60 seconds, retry |
| Weekend/holiday (no data) | Return empty list, log info |

---

#### 4.1.2 `collectors/credit.py`

**Purpose:** Fetch credit spread data from FRED.

**External Dependencies:**
- `fredapi` — Federal Reserve Economic Data API
- Requires free API key (https://fred.stlouisfed.org/docs/api/api_key.html)
- Rate limit: 120 requests/minute

**FRED Series IDs:**

| Metric | Series ID | Description |
|--------|-----------|-------------|
| HY OAS | BAMLH0A0HYM2 | ICE BofA US High Yield Index OAS |
| IG BBB OAS | BAMLC0A4CBBB | ICE BofA BBB US Corporate Index OAS |
| 10Y Treasury | DGS10 | 10-Year Treasury Constant Maturity |

**Public Interface:**

```python
@dataclass
class CreditSpreadData:
    date: date
    hy_oas: float           # basis points
    ig_bbb_oas: float       # basis points
    hy_ig_diff: float       # computed
    treasury_10y: float     # percent

def fetch_credit_spreads(
    start_date: date,
    end_date: date
) -> list[CreditSpreadData]:
    """
    Fetch credit spread time series from FRED.
    
    Args:
        start_date: Inclusive start
        end_date: Inclusive end
        
    Returns:
        List of CreditSpreadData, one per trading day
    """
    ...

def get_historical_percentile(
    metric: str,
    value: float,
    lookback_years: int = 5
) -> float:
    """
    Compute where current value sits in historical distribution.
    
    Args:
        metric: 'hy_oas', 'ig_bbb_oas', or 'hy_ig_diff'
        value: Current value
        lookback_years: Historical window
        
    Returns:
        Percentile (0-100)
    """
    ...
```

---

#### 4.1.3 `collectors/gpu_pricing.py`

**Purpose:** Track GPU rental pricing (semi-automated with manual fallback).

**Data Sources:**

| Source | URL | Automation Status |
|--------|-----|-------------------|
| vast.ai | https://vast.ai/console/create/ | Manual (requires login) |
| Lambda Labs | https://lambdalabs.com/service/gpu-cloud | Scrape-able (pricing page) |
| RunPod | https://www.runpod.io/gpu-instance/pricing | Scrape-able |
| CoreWeave | Published rate cards | Manual lookup |

**Design Decision:** Given the fragility of web scraping for pricing data and the relatively low update frequency needed (weekly), this module provides:

1. **Automated scraping** for Lambda/RunPod where feasible
2. **Manual entry interface** via `scripts/manual_entry.py`
3. **Source links** always preserved for verification

**Public Interface:**

```python
@dataclass
class GPUPricePoint:
    date: date
    gpu_model: str          # 'H100-80GB', 'H200', 'B200'
    source: str             # 'lambda', 'runpod', 'vast.ai', 'manual'
    price_per_hour: float
    notes: Optional[str]

def scrape_lambda_pricing() -> list[GPUPricePoint]:
    """
    Scrape current GPU pricing from Lambda Labs.
    
    Returns:
        List of GPUPricePoint for each available GPU type
        
    Raises:
        ScrapingError: If page structure has changed
    """
    ...

def scrape_runpod_pricing() -> list[GPUPricePoint]:
    """Scrape current GPU pricing from RunPod."""
    ...

def add_manual_price(
    gpu_model: str,
    source: str,
    price_per_hour: float,
    notes: Optional[str] = None
) -> None:
    """
    Add manually collected GPU price to database.
    
    Called via scripts/manual_entry.py CLI.
    """
    ...

def get_gpu_price_series(
    gpu_model: str,
    start_date: date,
    end_date: date
) -> list[GPUPricePoint]:
    """Retrieve historical GPU pricing from database."""
    ...

def get_latest_prices() -> dict[str, GPUPricePoint]:
    """
    Get most recent price for each GPU model.
    
    Returns:
        Dict keyed by gpu_model
    """
    ...
```

**Manual Entry Workflow:**

```bash
# Weekly manual entry for vast.ai (requires manual lookup)
python scripts/manual_entry.py gpu \
    --model H100-80GB \
    --source vast.ai \
    --price 1.25 \
    --notes "Spot pricing as of 2024-12-14"
```

---

#### 4.1.4 `collectors/sec_edgar.py`

**Purpose:** Download and organize SEC filings for hyperscaler financial extraction.

**External Dependencies:**
- `sec-edgar-downloader` — Bulk filing downloads
- Rate limit: 10 requests/second (SEC fair access policy)

**Design Decision:** Full XBRL parsing is brittle and maintenance-intensive. This module focuses on:

1. **Automated filing download** — Reliable, well-supported
2. **Filing organization** — Consistent local file structure
3. **Extraction templates** — Guide manual data entry
4. **Source link preservation** — Every metric links to filing

**Public Interface:**

```python
@dataclass
class FilingMetadata:
    ticker: str
    filing_type: str        # '10-K', '10-Q'
    fiscal_period: str      # 'Q3 2024'
    filing_date: date
    accession_number: str
    local_path: Path
    sec_url: str

def download_latest_filings(
    tickers: list[str],
    filing_types: list[str] = ["10-K", "10-Q"],
    after_date: Optional[date] = None
) -> list[FilingMetadata]:
    """
    Download recent SEC filings for specified tickers.
    
    Files stored in: data/filings/{ticker}/{filing_type}/{accession}/
    
    Args:
        tickers: Company ticker symbols
        filing_types: Types to download
        after_date: Only filings after this date
        
    Returns:
        List of FilingMetadata for downloaded filings
    """
    ...

def get_filing_url(ticker: str, accession_number: str) -> str:
    """Generate SEC EDGAR URL for a filing."""
    ...

def list_available_filings(ticker: str) -> list[FilingMetadata]:
    """List all locally downloaded filings for a ticker."""
    ...

def generate_extraction_template(
    ticker: str,
    fiscal_period: str
) -> dict:
    """
    Generate a template dict for manual data entry.
    
    Returns dict with all expected fields and source locations.
    """
    ...
```

**Extraction Template Format:**

```python
{
    "ticker": "MSFT",
    "fiscal_period": "Q1 FY2025",
    "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000789019...",
    "extraction_guide": {
        "capex": {
            "location": "Cash Flow Statement → 'Additions to property and equipment'",
            "value": None,  # To be filled
            "unit": "millions USD"
        },
        "operating_cf": {
            "location": "Cash Flow Statement → 'Net cash from operations'",
            "value": None,
            "unit": "millions USD"
        },
        "ai_revenue": {
            "location": "Segment Disclosures or Earnings Call → Azure AI / Copilot mentions",
            "value": None,
            "unit": "millions USD",
            "notes": "May require estimation from growth rates"
        },
        # ... additional fields
    }
}
```

---

#### 4.1.5 `collectors/news.py`

**Purpose:** Aggregate relevant news via RSS feeds and keyword filtering.

**RSS Feed Sources:**

| Source | Feed URL | Focus |
|--------|----------|-------|
| Data Center Dynamics | https://www.datacenterdynamics.com/rss/ | DC construction, financing |
| Utility Dive | https://www.utilitydive.com/feeds/news/ | Energy/utility capex |
| The Information | Manual (paywalled) | AI industry deals |
| SEC 8-K RSS | Per-ticker | Material agreements |

**Keyword Relevance Scoring:**

```python
KEYWORDS = {
    "high_relevance": [
        "data center financing", "gpu collateral", "coreweave",
        "hyperscaler capex", "ai infrastructure debt", "nvidia demand"
    ],
    "medium_relevance": [
        "data center", "gpu", "artificial intelligence investment",
        "cloud capex", "ai chip", "compute capacity"
    ],
    "low_relevance": [
        "technology", "cloud", "nvidia", "microsoft azure",
        "google cloud", "aws"
    ]
}

def compute_relevance_score(title: str, summary: str) -> float:
    """
    Score 0-1 based on keyword presence and weight.
    
    High relevance keyword: +0.4
    Medium relevance: +0.2
    Low relevance: +0.1
    Cap at 1.0
    """
    ...
```

**Public Interface:**

```python
@dataclass
class NewsItem:
    published_date: date
    title: str
    source: str
    url: str
    summary: str
    relevance_score: float

def fetch_news_feeds() -> list[NewsItem]:
    """
    Fetch and score items from all configured RSS feeds.
    
    Returns:
        List of NewsItem, deduplicated by URL
    """
    ...

def get_recent_news(
    days: int = 7,
    min_relevance: float = 0.3
) -> list[NewsItem]:
    """
    Retrieve recent news items above relevance threshold.
    """
    ...
```

---

### 4.2 Analytics Module

#### 4.2.1 `analytics/correlation.py`

**Purpose:** Compute rolling correlations for crowded trade detection.

**Public Interface:**

```python
def rolling_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int = 60
) -> pd.Series:
    """
    Compute rolling Pearson correlation.
    
    Args:
        series_a: First return series (indexed by date)
        series_b: Second return series
        window: Rolling window in trading days
        
    Returns:
        Series of correlation values
    """
    ...

def compute_nvda_spy_correlation(
    as_of_date: date,
    window: int = 60
) -> float:
    """
    Compute NVDA-SPY rolling correlation as of given date.
    
    Fetches data from equity_prices table.
    """
    ...

def compute_mag7_spy_correlation(
    as_of_date: date,
    window: int = 60
) -> float:
    """
    Compute equal-weighted Mag7 basket correlation with SPY.
    """
    ...

def is_trade_crowded(
    nvda_spy_corr: float,
    mag7_spy_corr: float,
    threshold: float = 0.85
) -> bool:
    """
    Per Kinlaw paper: trade is crowded when both correlations > threshold.
    """
    return nvda_spy_corr > threshold and mag7_spy_corr > threshold
```

---

#### 4.2.2 `analytics/abri.py`

**Purpose:** Compute the AI Bubble Risk Index composite score.

**ABRI Component Scoring:**

| Component | Weight | Raw Input | Scoring Function |
|-----------|--------|-----------|------------------|
| Concentration | 15% | Mag7 % of SPY | Linear: 40%→0, 60%→100 |
| Correlation | 10% | NVDA-SPY 60d corr | Linear: 0.5→0, 0.95→100 |
| Credit Stress | 15% | HY-IG spread diff | Percentile vs 5yr history |
| GPU Deflation | 15% | H100 $/hr | Inverse: $8→0, $0.50→100 |
| Capex Intensity | 15% | Avg hyperscaler capex/OCF | Linear: 40%→0, 80%→100 |
| Revenue Gap | 10% | Aggregate AI capex / AI revenue | Log scale, calibrated |
| Deal Flow | 20% | 6mo deal volume vs prior 6mo | % change, normalized |

**Note on Revenue Gap Weighting:** Reduced from 15% to 10% due to significant uncertainty in AI revenue attribution across hyperscalers. Disclosure practices vary; Microsoft provides growth rates without absolute figures, Google reports Cloud but not AI specifically, and Meta has minimal AI revenue disclosure. This component's estimates carry wider confidence intervals. Weight redistributed to Deal Flow (increased to 20%) which has more observable, verifiable inputs. This weighting should be revisited as disclosure improves.

**Public Interface:**

```python
@dataclass
class ABRIComponents:
    date: date
    concentration_score: float
    correlation_score: float
    credit_stress_score: float
    gpu_deflation_score: float
    capex_intensity_score: float
    revenue_gap_score: float
    deal_flow_score: float
    composite_score: float

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        ...

def compute_concentration_score(mag7_weight: float) -> float:
    """
    Linear scaling: 40% weight → 0, 60% weight → 100.
    
    Clipped to [0, 100] range.
    """
    return max(0, min(100, (mag7_weight - 0.40) / 0.20 * 100))

def compute_correlation_score(nvda_spy_corr: float) -> float:
    """
    Linear scaling: 0.5 correlation → 0, 0.95 correlation → 100.
    """
    return max(0, min(100, (nvda_spy_corr - 0.50) / 0.45 * 100))

def compute_credit_stress_score(
    hy_ig_diff: float,
    historical_values: pd.Series
) -> float:
    """
    Percentile rank vs 5-year history.
    
    Higher percentile = higher stress = higher score.
    """
    ...

def compute_gpu_deflation_score(h100_price: float) -> float:
    """
    Inverse scaling: $8/hr → 0, $0.50/hr → 100.
    
    Reflects collateral value deterioration.
    """
    return max(0, min(100, (8.0 - h100_price) / 7.5 * 100))

def compute_capex_intensity_score(avg_capex_ocf: float) -> float:
    """
    Linear scaling: 40% ratio → 0, 80% ratio → 100.
    """
    return max(0, min(100, (avg_capex_ocf - 0.40) / 0.40 * 100))

def compute_revenue_gap_score(
    total_ai_capex: float,
    total_ai_revenue: float
) -> float:
    """
    Log-scaled ratio of capex to revenue.
    
    Calibration: ratio of 1.0 → 50, ratio of 3.0 → 100.
    """
    ...

def compute_deal_flow_score(
    recent_6mo_volume: float,
    prior_6mo_volume: float
) -> float:
    """
    Acceleration metric: % change normalized.
    
    0% change → 50, +100% change → 100, -50% change → 25.
    """
    ...

def compute_abri(as_of_date: date) -> ABRIComponents:
    """
    Compute full ABRI as of given date.
    
    Fetches all required inputs from database, computes component
    scores, and returns weighted composite.
    
    Weights:
        concentration: 0.15
        correlation: 0.10
        credit_stress: 0.15
        gpu_deflation: 0.15
        capex_intensity: 0.15
        revenue_gap: 0.15
        deal_flow: 0.15
    """
    ...

def get_abri_interpretation(score: float) -> str:
    """
    Human-readable interpretation of ABRI score.
    
    0-30: Normal investment cycle
    30-50: Elevated speculation
    50-70: Bubble characteristics present
    70-100: Extreme fragility; correction risk elevated
    """
    if score < 30:
        return "Normal investment cycle"
    elif score < 50:
        return "Elevated speculation"
    elif score < 70:
        return "Bubble characteristics present"
    else:
        return "Extreme fragility; correction risk elevated"
```

**Historical Calibration Notes:**

The hybrid backtesting approach requires different handling per component:

| Component | Historical Depth | Calibration Method |
|-----------|------------------|-------------------|
| Concentration | 5+ years | Full backtest; Mag7 data available |
| Correlation | 5+ years | Full backtest; price data available |
| Credit Stress | 5+ years | FRED history; use full window |
| GPU Deflation | ~2 years | Use available H100 data; flag limitation |
| Capex Intensity | 5 years | 10-K/10-Q data available |
| Revenue Gap | ~3 years | AI-specific revenue only since ~2023 |
| Deal Flow | ~3 years | AI infrastructure deals only since ~2022 |

**Calibration Implementation:**

```python
def calibrate_thresholds(
    historical_data: pd.DataFrame,
    component: str
) -> dict:
    """
    Compute calibration statistics for a component.
    
    Returns:
        {
            "min": float,
            "max": float,
            "mean": float,
            "std": float,
            "p25": float,
            "p75": float,
            "data_start": date,
            "data_end": date,
            "n_observations": int
        }
    """
    ...
```

---

#### 4.2.3 `analytics/signals.py`

**Purpose:** Evaluate alert thresholds and generate signals.

**Alert Thresholds:**

```python
ALERT_THRESHOLDS = {
    # ABRI composite
    "abri_composite": {
        "warning": 50,
        "critical": 70,
        "direction": "above"
    },
    
    # Individual components
    "mag7_weight": {
        "warning": 0.50,
        "critical": 0.55,
        "direction": "above"
    },
    "nvda_spy_corr": {
        "warning": 0.85,
        "critical": 0.90,
        "direction": "above"
    },
    "hy_ig_diff": {
        "warning_percentile": 75,
        "critical_percentile": 90,
        "direction": "above"
    },
    "h100_price": {
        "warning": 1.50,
        "critical": 0.75,
        "direction": "below"  # Lower prices = higher risk
    },
    "avg_capex_ocf": {
        "warning": 0.65,
        "critical": 0.75,
        "direction": "above"
    }
}
```

**Public Interface:**

```python
@dataclass
class AlertSignal:
    metric_name: str
    current_value: float
    threshold: float
    alert_type: str         # 'warning', 'critical'
    direction: str          # 'above', 'below'
    message: str

def evaluate_thresholds(
    metrics: dict[str, float]
) -> list[AlertSignal]:
    """
    Evaluate all metrics against configured thresholds.
    
    Args:
        metrics: Dict of metric names to current values
        
    Returns:
        List of AlertSignal for any breached thresholds
    """
    ...

def check_for_alerts() -> list[AlertSignal]:
    """
    Run full alert check using latest data from database.
    
    This is the entry point for scheduled alert evaluation.
    """
    ...

def should_send_alert(signal: AlertSignal) -> bool:
    """
    Determine if alert should be sent based on:
    - Not already sent in last 24 hours for same metric
    - Not acknowledged and still breaching
    """
    ...
```

---

### 4.3 Storage Module

#### 4.3.1 `storage/db.py`

**Purpose:** Supabase/PostgreSQL connection and session management.

```python
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Supabase connection string from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# Supabase uses PostgreSQL; connection string format:
# postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set True for SQL debugging
    pool_pre_ping=True,  # Handle connection drops gracefully
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_session() -> Session:
    """
    Context manager for database sessions.
    
    Usage:
        with get_session() as session:
            session.query(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_database():
    """
    Initialize database schema.
    
    Safe to call multiple times; tables created only if not exist.
    """
    from storage.models import Base
    Base.metadata.create_all(engine)

def check_connection() -> bool:
    """
    Verify database connectivity.
    
    Returns True if connection successful, False otherwise.
    Used for health checks and dashboard status display.
    """
    try:
        with get_session() as session:
            session.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
```

**Supabase Setup Instructions:**

1. Create account at https://supabase.com
2. Create new project (free tier)
3. Navigate to Project Settings → Database
4. Copy the "Connection string" (URI format)
5. Replace `[YOUR-PASSWORD]` with your database password
6. Store as `DATABASE_URL` in environment variables

---

### 4.6 Manual Input Prompt System

**Purpose:** Provide a structured interface for entering manually-sourced data (GPU pricing, hyperscaler financials, deal flow) with clear instructions, source links, and data validation.

#### 4.6.1 Design Philosophy

The manual input system operates on the principle that **human verification adds value**. Rather than attempting fragile automation for data that changes format or requires interpretation, the system:

1. **Prompts** the user with exactly what data is needed
2. **Provides** direct links to source materials
3. **Instructs** with clear, step-by-step guidance on where to find and how to format data
4. **Validates** input before committing to database
5. **Tracks** data freshness and alerts when updates are due

#### 4.6.2 Pending Tasks Queue

The system maintains a queue of pending manual data entry tasks in the database:

```sql
CREATE TABLE pending_manual_tasks (
    task_id SERIAL PRIMARY KEY,
    task_type TEXT NOT NULL,        -- 'gpu_pricing', 'hyperscaler', 'deal'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    priority INTEGER DEFAULT 5,     -- 1=highest, 10=lowest
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'skipped'
    data_payload JSONB,             -- Pre-populated template data
    completed_at TIMESTAMP,
    completed_by TEXT
);
```

#### 4.6.3 Dashboard Manual Entry Page (`dashboard/pages/7_Manual_Entry.py`)

```python
import streamlit as st
from datetime import date, timedelta
from storage.db import get_session
from storage.models import PendingManualTask, GPUPricing, HyperscalerMetrics

st.set_page_config(page_title="Manual Data Entry", page_icon="✏️")
st.title("✏️ Manual Data Entry")

# Display pending tasks
st.subheader("Pending Tasks")
pending_tasks = get_pending_tasks()

if not pending_tasks:
    st.success("✅ No pending manual entry tasks!")
else:
    for task in pending_tasks:
        with st.expander(f"📋 {task.task_type.upper()} — Due: {task.due_date}", expanded=task.priority <= 3):
            render_task_form(task)

def render_task_form(task):
    """Render the appropriate form based on task type."""
    if task.task_type == "gpu_pricing":
        render_gpu_pricing_form(task)
    elif task.task_type == "hyperscaler":
        render_hyperscaler_form(task)
    elif task.task_type == "deal":
        render_deal_form(task)
```

#### 4.6.4 GPU Pricing Entry Form

```python
def render_gpu_pricing_form(task):
    """
    GPU pricing manual entry with source links and instructions.
    """
    st.markdown("### GPU Rental Pricing Update")
    
    # Instructions panel
    with st.container():
        st.info("""
        **Instructions:**
        1. Visit each source link below
        2. Find the **on-demand/spot** price for the specified GPU model
        3. Record the **$/hour** rate (not monthly or reserved pricing)
        4. Note any relevant context (e.g., "community cloud", "secure cloud")
        """)
    
    # Source links with direct navigation
    st.markdown("#### 📎 Source Links")
    
    sources = {
        "vast.ai": {
            "url": "https://vast.ai/console/create/",
            "instructions": "Log in → Select GPU model → Note 'Price' column ($/hr)",
            "requires_login": True
        },
        "Lambda Labs": {
            "url": "https://lambdalabs.com/service/gpu-cloud",
            "instructions": "Scroll to pricing table → Find on-demand rate",
            "requires_login": False
        },
        "RunPod": {
            "url": "https://www.runpod.io/gpu-instance/pricing",
            "instructions": "Select 'On-Demand' tab → Find GPU model → Note hourly rate",
            "requires_login": False
        },
        "CoreWeave": {
            "url": "https://www.coreweave.com/pricing",
            "instructions": "Navigate to GPU instances → Note on-demand pricing",
            "requires_login": False
        }
    }
    
    for source_name, source_info in sources.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"[🔗 {source_name}]({source_info['url']})")
            if source_info['requires_login']:
                st.caption("⚠️ Login required")
        with col2:
            st.caption(source_info['instructions'])
    
    st.markdown("---")
    
    # Data entry form
    st.markdown("#### 📝 Enter Pricing Data")
    
    gpu_models = ["H100-80GB", "H200", "A100-80GB", "A100-40GB", "L40S"]
    
    with st.form(key=f"gpu_form_{task.task_id}"):
        entries = []
        
        for model in gpu_models:
            st.markdown(f"**{model}**")
            cols = st.columns(4)
            
            with cols[0]:
                source = st.selectbox(
                    "Source",
                    options=list(sources.keys()) + ["Other"],
                    key=f"source_{model}_{task.task_id}"
                )
            
            with cols[1]:
                price = st.number_input(
                    "$/hour",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.01,
                    format="%.2f",
                    key=f"price_{model}_{task.task_id}"
                )
            
            with cols[2]:
                available = st.checkbox(
                    "Available",
                    value=True,
                    key=f"avail_{model}_{task.task_id}"
                )
            
            with cols[3]:
                notes = st.text_input(
                    "Notes",
                    placeholder="e.g., spot pricing",
                    key=f"notes_{model}_{task.task_id}"
                )
            
            if price > 0:
                entries.append({
                    "gpu_model": model,
                    "source": source,
                    "price_per_hour": price,
                    "available": available,
                    "notes": notes
                })
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Entries", type="primary")
        with col2:
            skipped = st.form_submit_button("⏭️ Skip This Week")
        
        if submitted and entries:
            save_gpu_pricing_entries(entries)
            mark_task_completed(task.task_id)
            st.success(f"✅ Saved {len(entries)} GPU pricing entries!")
            st.rerun()
        
        if skipped:
            mark_task_skipped(task.task_id)
            st.warning("Task skipped. Will appear again next week.")
            st.rerun()
```

#### 4.6.5 Hyperscaler Financials Entry Form

```python
def render_hyperscaler_form(task):
    """
    Hyperscaler quarterly financials entry with SEC filing links.
    """
    ticker = task.data_payload.get("ticker", "MSFT")
    fiscal_period = task.data_payload.get("fiscal_period", "Q1 2025")
    
    st.markdown(f"### {ticker} — {fiscal_period} Financials")
    
    # Filing information
    filing_info = get_filing_info(ticker, fiscal_period)
    
    st.markdown("#### 📎 Source Documents")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"[📄 SEC 10-Q/10-K Filing]({filing_info['sec_url']})")
        st.caption("Primary source for financial data")
    with col2:
        st.markdown(f"[📊 Earnings Call Transcript]({filing_info['transcript_url']})")
        st.caption("For AI revenue commentary")
    
    # Extraction guide
    with st.expander("📖 Extraction Instructions", expanded=True):
        st.markdown(f"""
        **Where to find each metric in the {ticker} filing:**
        
        | Metric | Location | Notes |
        |--------|----------|-------|
        | **Capex** | Cash Flow Statement → "{filing_info['capex_label']}" | In millions |
        | **Operating Cash Flow** | Cash Flow Statement → "Net cash from operations" | In millions |
        | **Total Debt** | Balance Sheet → Long-term debt + Current portion | Sum both lines |
        | **Total Equity** | Balance Sheet → "Total stockholders' equity" | Single line |
        | **AI Revenue** | {filing_info['ai_revenue_location']} | May require estimation |
        | **Depreciation** | Income Statement or Cash Flow → "Depreciation and amortization" | |
        
        **AI Revenue Estimation Notes:**
        {filing_info['ai_revenue_notes']}
        """)
    
    st.markdown("---")
    
    # Data entry form
    with st.form(key=f"hyperscaler_form_{task.task_id}"):
        st.markdown("#### 📝 Enter Financial Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            capex = st.number_input(
                "Capital Expenditures ($M)",
                min_value=0.0,
                step=100.0,
                help="From cash flow statement"
            )
            
            operating_cf = st.number_input(
                "Operating Cash Flow ($M)",
                min_value=0.0,
                step=100.0,
                help="Net cash from operating activities"
            )
            
            total_debt = st.number_input(
                "Total Debt ($M)",
                min_value=0.0,
                step=100.0,
                help="Long-term + current portion"
            )
        
        with col2:
            total_equity = st.number_input(
                "Total Equity ($M)",
                min_value=0.0,
                step=100.0,
                help="Total stockholders' equity"
            )
            
            ai_revenue = st.number_input(
                "AI-Attributed Revenue ($M)",
                min_value=0.0,
                step=100.0,
                help="Estimate if not explicitly disclosed"
            )
            
            depreciation = st.number_input(
                "Depreciation Expense ($M)",
                min_value=0.0,
                step=100.0
            )
        
        st.markdown("---")
        
        ai_revenue_methodology = st.text_area(
            "AI Revenue Estimation Methodology",
            placeholder="Describe how you estimated AI revenue (e.g., '60% of Azure revenue based on management commentary')",
            help="Required for audit trail"
        )
        
        source_url = st.text_input(
            "SEC Filing URL",
            value=filing_info['sec_url'],
            help="Link to the exact filing used"
        )
        
        # Computed metrics preview
        if capex > 0 and operating_cf > 0:
            st.markdown("#### 📊 Computed Metrics Preview")
            capex_ocf = capex / operating_cf
            debt_equity = total_debt / total_equity if total_equity > 0 else 0
            
            prev_col1, prev_col2 = st.columns(2)
            with prev_col1:
                st.metric("Capex/OCF Ratio", f"{capex_ocf:.1%}")
            with prev_col2:
                st.metric("Debt/Equity Ratio", f"{debt_equity:.2f}x")
        
        submitted = st.form_submit_button("💾 Save Entry", type="primary")
        
        if submitted:
            if not source_url:
                st.error("Source URL is required")
            elif ai_revenue > 0 and not ai_revenue_methodology:
                st.error("AI revenue estimation methodology required when AI revenue is entered")
            else:
                save_hyperscaler_entry(
                    ticker=ticker,
                    fiscal_period=fiscal_period,
                    capex=capex,
                    operating_cf=operating_cf,
                    total_debt=total_debt,
                    total_equity=total_equity,
                    ai_revenue=ai_revenue,
                    depreciation=depreciation,
                    ai_revenue_methodology=ai_revenue_methodology,
                    source_url=source_url
                )
                mark_task_completed(task.task_id)
                st.success(f"✅ Saved {ticker} {fiscal_period} financials!")
                st.rerun()
```

#### 4.6.6 Task Generation Logic

Tasks are generated automatically based on schedules:

```python
# scripts/generate_pending.py

from datetime import date, timedelta
from storage.db import get_session
from storage.models import PendingManualTask

def generate_weekly_gpu_task():
    """Generate weekly GPU pricing update task."""
    with get_session() as session:
        # Check if task already exists for this week
        existing = session.query(PendingManualTask).filter(
            PendingManualTask.task_type == "gpu_pricing",
            PendingManualTask.due_date >= date.today() - timedelta(days=7),
            PendingManualTask.status == "pending"
        ).first()
        
        if not existing:
            task = PendingManualTask(
                task_type="gpu_pricing",
                due_date=date.today() + timedelta(days=7),
                priority=3,
                data_payload={"week_of": str(date.today())}
            )
            session.add(task)
            session.commit()

def generate_quarterly_hyperscaler_tasks():
    """Generate tasks for each hyperscaler after earnings season."""
    tickers = ["MSFT", "GOOGL", "AMZN", "META", "NVDA"]
    
    # Determine current fiscal period based on date
    fiscal_period = get_current_fiscal_period()
    
    with get_session() as session:
        for ticker in tickers:
            existing = session.query(PendingManualTask).filter(
                PendingManualTask.task_type == "hyperscaler",
                PendingManualTask.data_payload["ticker"].astext == ticker,
                PendingManualTask.data_payload["fiscal_period"].astext == fiscal_period
            ).first()
            
            if not existing:
                task = PendingManualTask(
                    task_type="hyperscaler",
                    due_date=get_filing_expected_date(ticker, fiscal_period),
                    priority=2,
                    data_payload={
                        "ticker": ticker,
                        "fiscal_period": fiscal_period
                    }
                )
                session.add(task)
        
        session.commit()
```

#### 4.6.7 Data Freshness Indicators

The dashboard displays freshness indicators for manually-sourced data:

```python
def get_data_freshness_status():
    """
    Returns freshness status for each manual data category.
    
    Status: 'current', 'stale', 'critical'
    """
    with get_session() as session:
        # GPU pricing freshness
        latest_gpu = session.query(GPUPricing).order_by(
            GPUPricing.date.desc()
        ).first()
        
        gpu_age = (date.today() - latest_gpu.date).days if latest_gpu else 999
        
        # Hyperscaler freshness (by ticker)
        hyperscaler_status = {}
        for ticker in ["MSFT", "GOOGL", "AMZN", "META", "NVDA"]:
            latest = session.query(HyperscalerMetrics).filter(
                HyperscalerMetrics.ticker == ticker
            ).order_by(HyperscalerMetrics.entered_at.desc()).first()
            
            if latest:
                age = (date.today() - latest.entered_at.date()).days
                hyperscaler_status[ticker] = "current" if age < 120 else "stale"
            else:
                hyperscaler_status[ticker] = "critical"
        
        return {
            "gpu_pricing": {
                "status": "current" if gpu_age < 10 else "stale" if gpu_age < 21 else "critical",
                "last_update": latest_gpu.date if latest_gpu else None,
                "days_old": gpu_age
            },
            "hyperscaler": hyperscaler_status
        }
```

#### 4.6.8 Freshness Display Component

```python
# dashboard/components/freshness.py

import streamlit as st

def render_data_freshness_sidebar():
    """Render data freshness indicators in sidebar."""
    st.sidebar.markdown("### 📅 Data Freshness")
    
    status = get_data_freshness_status()
    
    # GPU Pricing
    gpu = status["gpu_pricing"]
    icon = "🟢" if gpu["status"] == "current" else "🟡" if gpu["status"] == "stale" else "🔴"
    st.sidebar.markdown(f"{icon} **GPU Pricing:** {gpu['days_old']}d old")
    
    # Hyperscaler data
    st.sidebar.markdown("**Hyperscaler Financials:**")
    for ticker, ticker_status in status["hyperscaler"].items():
        icon = "🟢" if ticker_status == "current" else "🟡" if ticker_status == "stale" else "🔴"
        st.sidebar.markdown(f"  {icon} {ticker}")
    
    # Pending tasks count
    pending_count = get_pending_task_count()
    if pending_count > 0:
        st.sidebar.warning(f"⚠️ {pending_count} pending manual entries")
        if st.sidebar.button("Go to Manual Entry"):
            st.switch_page("pages/7_Manual_Entry.py")
```

---

### 4.7 Alerts Module

#### 4.7.1 `alerts/email.py`

**Purpose:** Email delivery via SMTP.

**Configuration (via environment variables):**

```python
# .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Gmail App Password
ALERT_RECIPIENT=your-email@gmail.com
```

**Gmail App Password Setup:**

1. Enable 2-factor authentication on Google account
2. Go to Security → App passwords
3. Generate password for "Mail" application
4. Use this password (not your regular password) in `.env`

**Public Interface:**

```python
def send_alert_email(
    subject: str,
    body_html: str,
    recipient: Optional[str] = None
) -> bool:
    """
    Send alert email via SMTP.
    
    Args:
        subject: Email subject line
        body_html: HTML body content
        recipient: Override default recipient
        
    Returns:
        True if sent successfully
    """
    ...

def send_weekly_report(
    report_html: str,
    recipient: Optional[str] = None
) -> bool:
    """
    Send weekly summary report.
    """
    ...

def render_alert_email(signals: list[AlertSignal]) -> str:
    """
    Render alert signals into HTML email body.
    
    Uses templates/email_alert.html template.
    """
    ...

def render_weekly_report(
    abri: ABRIComponents,
    week_over_week_changes: dict,
    news_items: list[NewsItem]
) -> str:
    """
    Render weekly report into HTML.
    
    Uses templates/email_weekly.html template.
    """
    ...
```

---

### 4.5 Dashboard Module

#### 4.5.1 `dashboard/app.py`

**Purpose:** Streamlit application entry point.

```python
import streamlit as st
from datetime import date, timedelta

st.set_page_config(
    page_title="AI Infrastructure Bubble Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("AI Bubble Monitor")
st.sidebar.markdown("---")

# Manual refresh button
if st.sidebar.button("🔄 Refresh Data"):
    # Trigger data collection
    from collectors import equity, credit
    # ... refresh logic
    st.sidebar.success("Data refreshed!")

# Last updated timestamp
st.sidebar.caption(f"Last updated: {get_last_collection_time()}")

# Main page: ABRI overview
st.title("AI Infrastructure Bubble Risk Index")

# Current ABRI score with gauge chart
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    current_abri = get_latest_abri()
    st.metric(
        label="ABRI Composite Score",
        value=f"{current_abri.composite_score:.1f}",
        delta=f"{week_over_week_change:.1f} vs last week"
    )
    st.caption(get_abri_interpretation(current_abri.composite_score))

with col2:
    st.metric("Mag7 Concentration", f"{current_abri.concentration_score:.1f}")
    
with col3:
    st.metric("Credit Stress", f"{current_abri.credit_stress_score:.1f}")

# ABRI history chart
st.subheader("ABRI History")
abri_history = get_abri_history(days=365)
fig = create_abri_chart(abri_history)
st.plotly_chart(fig, use_container_width=True)

# Component breakdown
st.subheader("Component Breakdown")
# ... component charts

# Navigation to detail pages handled by Streamlit multipage
```

**Page Structure:**

| Page | Path | Content |
|------|------|---------|
| Overview | `app.py` | ABRI score, history, alerts |
| Market Structure | `pages/1_Market_Structure.py` | Concentration, correlation charts |
| Credit Stress | `pages/2_Credit_Stress.py` | Spread charts, historical percentiles |
| GPU Economics | `pages/3_GPU_Economics.py` | Price trends, manual entry link |
| Hyperscaler Health | `pages/4_Hyperscaler_Health.py` | Quarterly metrics table, filing links |
| Deal Flow | `pages/5_Deal_Flow.py` | Deal tracker, circular financing flags |
| News Feed | `pages/6_News_Feed.py` | Filtered news with relevance scores |

---

## 5. Data Sources & Collection Strategies

### 5.1 Automated Collection Summary

| Data Type | Source | Frequency | Method | Rate Limit |
|-----------|--------|-----------|--------|------------|
| Equity prices | Yahoo Finance | Daily | `yfinance` API | ~2k/hr |
| Market cap | Yahoo Finance | Daily | `yfinance` API | ~2k/hr |
| Credit spreads | FRED | Daily | `fredapi` | 120/min |
| 10Y Treasury | FRED | Daily | `fredapi` | 120/min |
| News feeds | Various RSS | Daily | `feedparser` | N/A |
| SEC filings | EDGAR | On-demand | `sec-edgar-downloader` | 10/sec |

### 5.2 Semi-Automated Collection

| Data Type | Source | Frequency | Method |
|-----------|--------|-----------|--------|
| GPU pricing | vast.ai, Lambda, RunPod | Weekly | Scrape + manual |
| Hyperscaler financials | 10-K/10-Q filings | Quarterly | Download + manual extraction |
| Deal flow | Press releases, 8-Ks | Ongoing | Manual entry |
| Leveraged ETF AUM | ETF.com | Weekly | Manual lookup |

### 5.3 Source Link Requirements

Every manually entered data point must include a source URL. The database schema enforces this via application logic:

```python
def add_hyperscaler_metric(data: dict) -> None:
    if not data.get("source_url"):
        raise ValueError("source_url is required for audit trail")
    # ... insert logic
```

### 5.4 Historical Backfill Strategy

For initial setup, historical data will be loaded via `scripts/backfill.py`:

| Dataset | Historical Depth | Source | Estimated Effort |
|---------|------------------|--------|------------------|
| Equity prices | 5 years | Yahoo Finance | Automated (~30 min) |
| Credit spreads | 5 years | FRED | Automated (~10 min) |
| Market metrics | 5 years | Computed from equity | Automated (~20 min) |
| GPU pricing | 2 years | Manual research | 2-4 hours |
| Hyperscaler financials | 5 years (20 quarters × 5 companies) | SEC EDGAR | 8-16 hours |
| Deal flow | 3 years | Manual research | 4-8 hours |

---

## 6. ABRI Calculation Methodology

### 6.1 Scoring Philosophy

The ABRI is designed as a monitoring tool, not a trading signal. Its value lies in:

1. **Trend detection** — Directional changes matter more than absolute levels
2. **Regime identification** — Distinguishing "normal" from "elevated" from "extreme"
3. **Component attribution** — Understanding which factors are driving risk

### 6.2 Component Definitions

#### 6.2.1 Concentration Score (15%)

**Definition:** Degree to which AI/tech leadership dominates index returns.

**Calculation:**
```
concentration_score = clip((mag7_weight - 0.40) / 0.20 × 100, 0, 100)
```

**Rationale:** The paper cites "asset centrality" as a bubble precondition. Historical Mag7 weight averaged ~25-35% pre-2023; 50%+ indicates extreme concentration.

**Data Requirements:**
- Daily market cap for Mag7 constituents
- Daily SPY market cap (or sum of S&P 500 constituents)

#### 6.2.2 Correlation Score (10%)

**Definition:** Crowded trade indicator per Kinlaw-Kritzman-Turkington methodology.

**Calculation:**
```
correlation_score = clip((nvda_spy_corr - 0.50) / 0.45 × 100, 0, 100)
```

**Rationale:** When a single stock's returns explain broad market moves, positioning is crowded. NVDA is the purest AI exposure; correlation >0.85 signals crowding.

**Data Requirements:**
- 60+ trading days of daily returns for NVDA and SPY
- Rolling window computation

#### 6.2.3 Credit Stress Score (15%)

**Definition:** Credit market's assessment of refinancing risk.

**Calculation:**
```
credit_stress_score = percentile_rank(hy_ig_diff, 5yr_history) × 100
```

**Rationale:** Widening HY-IG differential indicates flight to quality within credit. This preceded both the 2008 crisis and 2020 COVID shock.

**Data Requirements:**
- 5 years of daily HY OAS and IG BBB OAS from FRED

#### 6.2.4 GPU Deflation Score (15%)

**Definition:** Collateral value deterioration for GPU-backed financing.

**Calculation:**
```
gpu_deflation_score = clip((8.0 - h100_price) / 7.5 × 100, 0, 100)
```

**Rationale:** The paper documents H100 rental collapse from $8 to ~$1. GPU-backed loans (CoreWeave, etc.) depend on stable collateral values; deflation triggers margin calls.

**Data Requirements:**
- Weekly H100-80GB spot rental pricing
- Benchmark against $8 peak and $0.50 floor

**Calibration Limitation:** Only ~2 years of H100 data exists. This component relies on the single observed boom/bust cycle.

#### 6.2.5 Capex Intensity Score (15%)

**Definition:** Investment burden relative to cash generation.

**Calculation:**
```
avg_capex_ocf = mean(capex/ocf for each hyperscaler)
capex_intensity_score = clip((avg_capex_ocf - 0.40) / 0.40 × 100, 0, 100)
```

**Rationale:** Capex/OCF >70% sustained indicates investment outpacing cash generation — the Minskyian "speculative finance" threshold.

**Data Requirements:**
- Quarterly capex and operating cash flow for MSFT, GOOGL, AMZN, META, NVDA
- 20 quarters (5 years) for baseline

#### 6.2.6 Revenue Gap Score (15%)

**Definition:** Disconnect between AI investment and AI revenue.

**Calculation:**
```
total_ai_capex = sum of hyperscaler AI-attributed capex
total_ai_revenue = sum of hyperscaler AI-attributed revenue
ratio = total_ai_capex / total_ai_revenue
revenue_gap_score = log_scale(ratio, baseline=1.0, ceiling=3.0)
```

**Rationale:** If capex significantly exceeds revenue, returns depend on future growth — the "Field of Dreams" assumption the paper critiques.

**Data Requirements:**
- AI-attributed capex (estimate: 50-70% of total cloud capex)
- AI-attributed revenue (Azure AI, Google Cloud AI, AWS AI, Meta AI, NVIDIA Data Center)

**Calibration Limitation:** AI revenue disclosure varies by company; requires estimation.

#### 6.2.7 Deal Flow Score (15%)

**Definition:** Acceleration of infrastructure financing.

**Calculation:**
```
recent_6mo = sum of deal volume in trailing 6 months
prior_6mo = sum of deal volume in 6 months before that
pct_change = (recent_6mo - prior_6mo) / prior_6mo
deal_flow_score = 50 + (pct_change × 50)  # Normalized around 50
```

**Rationale:** Accelerating deal flow suggests capital is chasing the trade. Deceleration may signal market saturation or caution.

**Data Requirements:**
- Deal tracker with announced amounts and dates
- 12+ months of history for calculation

### 6.3 Composite Calculation

```python
WEIGHTS = {
    "concentration": 0.15,
    "correlation": 0.10,
    "credit_stress": 0.15,
    "gpu_deflation": 0.15,
    "capex_intensity": 0.15,
    "revenue_gap": 0.10,    # Reduced due to attribution uncertainty
    "deal_flow": 0.20       # Increased; more observable/verifiable
}

def compute_composite(components: ABRIComponents) -> float:
    return (
        WEIGHTS["concentration"] * components.concentration_score +
        WEIGHTS["correlation"] * components.correlation_score +
        WEIGHTS["credit_stress"] * components.credit_stress_score +
        WEIGHTS["gpu_deflation"] * components.gpu_deflation_score +
        WEIGHTS["capex_intensity"] * components.capex_intensity_score +
        WEIGHTS["revenue_gap"] * components.revenue_gap_score +
        WEIGHTS["deal_flow"] * components.deal_flow_score
    )
```

### 6.4 Interpretation Guide

| Score Range | Interpretation | Historical Analog |
|-------------|----------------|-------------------|
| 0-30 | Normal investment cycle | Pre-2021 cloud capex |
| 30-50 | Elevated speculation | 2021 growth stock rally |
| 50-70 | Bubble characteristics present | Late 2021 SPAC/crypto |
| 70-100 | Extreme fragility | Early 2022 pre-crash |

---

## 7. Alerting & Notification System

### 7.1 Alert Types

| Type | Trigger | Action |
|------|---------|--------|
| **Threshold Breach** | Metric crosses warning/critical level | Immediate email |
| **Trend Alert** | 3+ consecutive weeks of deterioration | Weekly email note |
| **Data Staleness** | Collection job fails 2+ consecutive days | Immediate email |

### 7.2 Deduplication Logic

To prevent alert fatigue:

```python
def should_send_alert(signal: AlertSignal) -> bool:
    # Check if same metric alerted in last 24 hours
    recent_alerts = get_alerts_since(
        metric=signal.metric_name,
        hours=24
    )
    if recent_alerts:
        return False
    
    # Check if previously acknowledged and still breaching
    # (Don't re-alert for known issues)
    acknowledged = get_acknowledged_alerts(metric=signal.metric_name)
    if acknowledged and is_still_breaching(signal):
        return False
    
    return True
```

### 7.3 Email Templates

**Alert Email Structure:**

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        .warning { background-color: #fff3cd; }
        .critical { background-color: #f8d7da; }
    </style>
</head>
<body>
    <h2>⚠️ ABRI Alert</h2>
    <p>The following thresholds have been breached:</p>
    
    <table>
        <tr class="{{ alert_type }}">
            <td>{{ metric_name }}</td>
            <td>Current: {{ current_value }}</td>
            <td>Threshold: {{ threshold }}</td>
        </tr>
    </table>
    
    <p>
        <a href="{{ dashboard_url }}">View Dashboard</a>
    </p>
</body>
</html>
```

**Weekly Report Structure:**

```html
<!DOCTYPE html>
<html>
<body>
    <h2>📊 Weekly ABRI Report — {{ week_ending }}</h2>
    
    <h3>Composite Score: {{ abri_score }}</h3>
    <p>{{ interpretation }}</p>
    <p>Week-over-week change: {{ wow_change }}</p>
    
    <h3>Component Summary</h3>
    <table>
        <!-- Component scores with WoW changes -->
    </table>
    
    <h3>Key Developments</h3>
    <ul>
        {% for item in news_items %}
        <li><a href="{{ item.url }}">{{ item.title }}</a> ({{ item.source }})</li>
        {% endfor %}
    </ul>
    
    <p>
        <a href="{{ dashboard_url }}">View Full Dashboard</a>
    </p>
</body>
</html>
```

---

## 8. Deployment Configuration

### 8.1 GitHub Repository Setup

**Repository Settings:**
- Visibility: Public (required for Streamlit Community Cloud)
- Branch protection: Main branch protected; require PR for changes
- Secrets: Configure for GitHub Actions (see below)

**Required Secrets:**

| Secret Name | Purpose |
|-------------|---------|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `FRED_API_KEY` | FRED API access |
| `SMTP_USER` | Gmail address |
| `SMTP_PASSWORD` | Gmail App Password |
| `ALERT_RECIPIENT` | Email for alerts |

**DATABASE_URL Format:**
```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### 8.2 GitHub Actions Workflows

#### 8.2.1 Daily Collection (`daily.yml`)

```yaml
name: Daily Data Collection

on:
  schedule:
    - cron: '0 22 * * 1-5'  # 10 PM UTC, Mon-Fri (after US market close)
  workflow_dispatch:  # Manual trigger

jobs:
  collect:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Run equity collector
        run: python -m collectors.equity
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
          
      - name: Run credit collector
        run: python -m collectors.credit
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
          
      - name: Run news collector
        run: python -m collectors.news
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        
      - name: Compute market metrics
        run: python -m analytics.correlation
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        
      - name: Check alerts
        run: python -m alerts.engine
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          ALERT_RECIPIENT: ${{ secrets.ALERT_RECIPIENT }}
```

**Note:** With Supabase, no git commit step is needed — data is written directly to the hosted database.

#### 8.2.2 Weekly Report (`weekly.yml`)

```yaml
name: Weekly Report

on:
  schedule:
    - cron: '0 14 * * 0'  # 2 PM UTC Sunday
  workflow_dispatch:

jobs:
  report:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Compute ABRI
        run: python -m analytics.abri
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        
      - name: Generate and send report
        run: python -m alerts.email --weekly
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          ALERT_RECIPIENT: ${{ secrets.ALERT_RECIPIENT }}
```

#### 8.2.3 Quarterly Reminder (`quarterly.yml`)

```yaml
name: Quarterly Filing Reminder

on:
  schedule:
    # Roughly aligned with earnings season
    - cron: '0 14 15 1,4,7,10 *'  # 15th of Jan, Apr, Jul, Oct
  workflow_dispatch:

jobs:
  remind:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Download new filings
        run: python -m collectors.sec_edgar --download-latest
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        
      - name: Send reminder email
        run: python -m alerts.email --quarterly-reminder
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          ALERT_RECIPIENT: ${{ secrets.ALERT_RECIPIENT }}
```

### 8.3 Streamlit Community Cloud Deployment

**Setup Steps:**

1. Push repository to GitHub (public)
2. Go to share.streamlit.io
3. Connect GitHub account
4. Select repository and branch (main)
5. Set main file path: `dashboard/app.py`
6. Configure secrets in Streamlit Cloud dashboard:
   - Copy contents of `.env` to Streamlit secrets
7. Deploy

**Streamlit Secrets Configuration:**

In Streamlit Cloud dashboard → Settings → Secrets:

```toml
[database]
url = "postgresql://postgres:YOUR-PASSWORD@db.YOUR-PROJECT-REF.supabase.co:5432/postgres"

[fred]
api_key = "your-fred-api-key"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "your-email@gmail.com"
smtp_password = "your-app-password"
recipient = "your-email@gmail.com"
```

**Access in Code:**

```python
import streamlit as st
import os

# For Streamlit Cloud
database_url = st.secrets["database"]["url"]

# For local development (falls back to environment variable)
database_url = st.secrets.get("database", {}).get("url") or os.environ.get("DATABASE_URL")
```

### 8.4 Local Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/ai-bubble-monitor.git
cd ai-bubble-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python scripts/init_db.py

# Run backfill (optional, for historical data)
python scripts/backfill.py

# Start dashboard locally
streamlit run dashboard/app.py
```

---

## 9. Development Workflow

### 9.1 Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production; deployed to Streamlit Cloud |
| `develop` | Integration branch for features |
| `feature/*` | Individual feature development |
| `hotfix/*` | Urgent fixes to production |

### 9.2 Development Cycle

1. **Feature development:** Create `feature/xyz` branch from `develop`
2. **Local testing:** Run tests, manual dashboard verification
3. **Pull request:** PR to `develop` with description
4. **Code review:** Self-review checklist (see below)
5. **Merge to develop:** Squash merge
6. **Release:** PR from `develop` to `main`
7. **Auto-deploy:** Streamlit Cloud picks up `main` changes

### 9.3 Self-Review Checklist

Before merging any PR:

- [ ] All new functions have docstrings
- [ ] Type hints added for function signatures
- [ ] Unit tests written for new logic
- [ ] Manual entry workflows documented if applicable
- [ ] Source URLs required for any new manual data fields
- [ ] No hardcoded credentials
- [ ] Database migrations documented if schema changed

### 9.4 Testing Strategy

**Unit Tests:**

```python
# tests/test_analytics.py
import pytest
from analytics.abri import compute_concentration_score

def test_concentration_score_minimum():
    """40% weight should score 0."""
    assert compute_concentration_score(0.40) == 0

def test_concentration_score_maximum():
    """60% weight should score 100."""
    assert compute_concentration_score(0.60) == 100

def test_concentration_score_midpoint():
    """50% weight should score 50."""
    assert compute_concentration_score(0.50) == 50

def test_concentration_score_clipping():
    """Values outside range should be clipped."""
    assert compute_concentration_score(0.30) == 0
    assert compute_concentration_score(0.70) == 100
```

**Integration Tests:**

```python
# tests/test_collectors.py
import pytest
from datetime import date, timedelta
from collectors.credit import fetch_credit_spreads

@pytest.mark.integration
def test_fred_connection():
    """Verify FRED API is accessible."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    data = fetch_credit_spreads(start_date, end_date)
    
    assert len(data) > 0
    assert all(d.hy_oas > 0 for d in data)
```

**Running Tests:**

```bash
# Unit tests only
pytest tests/ -m "not integration"

# All tests (requires API keys)
pytest tests/
```

---

## 10. Future Upgrade Path

### 10.1 Cost Tier Progression

| Tier | Monthly Cost | Upgrades |
|------|--------------|----------|
| **Current (Free)** | $0 | SQLite, Streamlit Cloud, GitHub Actions |
| **Tier 1** | ~$10 | Supabase (PostgreSQL), dedicated alerts service |
| **Tier 2** | ~$50 | Railway/Render (always-on), enhanced scraping |
| **Tier 3** | ~$150+ | Multi-user, real-time data feeds, mobile app |

### 10.2 Upgrade Trigger Points

| Trigger | Upgrade Path |
|---------|--------------|
| SQLite file >500MB | Migrate to Supabase PostgreSQL |
| Dashboard sleep annoying | Move to Railway/Render paid tier |
| Need real-time GPU pricing | Add scraping service (ScrapingBee, etc.) |
| Want to share with others | Add authentication (Streamlit native or Auth0) |
| Need mobile access | Build companion mobile app or PWA |

### 10.3 Code Preparation for Upgrades

The current architecture is designed for upgrade paths:

**Database Abstraction:**

```python
# storage/db.py already uses SQLAlchemy
# Switching to PostgreSQL requires only connection string change:

# Current (SQLite)
engine = create_engine(f"sqlite:///{DATABASE_PATH}")

# Future (PostgreSQL)
engine = create_engine(os.environ["DATABASE_URL"])
```

**Configuration Externalization:**

All configuration is externalized to environment variables, enabling platform-agnostic deployment.

**Modular Collection:**

Each collector is independent; adding new data sources doesn't require modifying existing ones.

---

## 11. Appendices

### Appendix A: Hyperscaler Quarterly Data Extraction Guide

This guide details where to find each metric in SEC filings.

#### A.1 Microsoft (MSFT)

**Filing Schedule:** Fiscal year ends June 30; Q1=Jul-Sep, Q2=Oct-Dec, Q3=Jan-Mar, Q4=Apr-Jun

| Metric | Location in 10-Q/10-K |
|--------|----------------------|
| Capex | Cash Flow Statement → "Additions to property and equipment" |
| Operating CF | Cash Flow Statement → "Net cash from operations" |
| AI Revenue | Earnings Call / IR Deck → "Azure and other cloud services" + AI mentions |
| Total Debt | Balance Sheet → "Long-term debt" + "Current portion of long-term debt" |
| Total Equity | Balance Sheet → "Total stockholders' equity" |
| Depreciation | Income Statement → "Depreciation and amortization" |
| DSO | Calculate: (Accounts Receivable ÷ Revenue) × 90 |

**Key Links:**
- SEC Filings: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000789019
- Investor Relations: https://www.microsoft.com/en-us/investor

#### A.2 Alphabet (GOOGL)

**Filing Schedule:** Calendar year; standard quarters

| Metric | Location in 10-Q/10-K |
|--------|----------------------|
| Capex | Cash Flow Statement → "Purchases of property and equipment" |
| Operating CF | Cash Flow Statement → "Net cash provided by operating activities" |
| AI Revenue | Earnings Call → Google Cloud segment + AI mentions |
| Total Debt | Balance Sheet → "Long-term debt" |
| Total Equity | Balance Sheet → "Total stockholders' equity" |

**Key Links:**
- SEC Filings: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001652044
- Investor Relations: https://abc.xyz/investor/

#### A.3 Amazon (AMZN)

**Filing Schedule:** Calendar year; standard quarters

| Metric | Location in 10-Q/10-K |
|--------|----------------------|
| Capex | Cash Flow Statement → "Purchases of property and equipment" |
| Operating CF | Cash Flow Statement → "Net cash provided by operating activities" |
| AI Revenue | Earnings Call → AWS segment + AI/ML service mentions |
| Total Debt | Balance Sheet → "Long-term debt" + notes on finance leases |

**Note:** Amazon has significant finance lease obligations that should be considered alongside debt.

**Key Links:**
- SEC Filings: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001018724
- Investor Relations: https://ir.aboutamazon.com/

#### A.4 Meta (META)

**Filing Schedule:** Calendar year; standard quarters

| Metric | Location in 10-Q/10-K |
|--------|----------------------|
| Capex | Cash Flow Statement → "Purchases of property and equipment" |
| Operating CF | Cash Flow Statement → "Net cash provided by operating activities" |
| AI Revenue | Limited disclosure; estimate from "Reality Labs" and ad efficiency mentions |
| Total Debt | Balance Sheet → "Long-term debt" |

**Key Links:**
- SEC Filings: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001326801
- Investor Relations: https://investor.fb.com/

#### A.5 NVIDIA (NVDA)

**Filing Schedule:** Fiscal year ends January; Q1=Feb-Apr, Q2=May-Jul, Q3=Aug-Oct, Q4=Nov-Jan

| Metric | Location in 10-Q/10-K |
|--------|----------------------|
| Capex | Cash Flow Statement → "Purchases of property and equipment" |
| Operating CF | Cash Flow Statement → "Net cash from operating activities" |
| Data Center Revenue | Segment disclosure → "Data Center" revenue |
| Gross Margin | Income Statement → Gross profit ÷ Revenue |
| Inventory | Balance Sheet → "Inventories" |

**Key Links:**
- SEC Filings: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045810
- Investor Relations: https://investor.nvidia.com/

---

### Appendix B: GPU Pricing Research Sources

**Primary Sources (check weekly):**

| Source | URL | Notes |
|--------|-----|-------|
| vast.ai | https://vast.ai/console/create/ | Requires account; shows real-time spot |
| Lambda Labs | https://lambdalabs.com/service/gpu-cloud | Public pricing page |
| RunPod | https://www.runpod.io/gpu-instance/pricing | Public pricing |
| CoreWeave | https://www.coreweave.com/pricing | Published rate card |
| Paperspace | https://www.paperspace.com/pricing | Gradient pricing |

**Secondary Sources (for context):**

| Source | URL | Notes |
|--------|-----|-------|
| SemiAnalysis | https://www.semianalysis.com/ | Industry analysis (some paywalled) |
| Tom's Hardware | GPU pricing articles | Consumer reference |
| eBay sold listings | H100 secondary market | Physical GPU values |

---

### Appendix C: Deal Flow Research Sources

**Press Release Aggregators:**
- Business Wire: https://www.businesswire.com/
- PR Newswire: https://www.prnewswire.com/
- GlobeNewswire: https://www.globenewswire.com/

**SEC Filings:**
- 8-K filings for material agreements
- Search: https://www.sec.gov/cgi-bin/srch-ia?text=data+center+financing

**Industry News:**
- Data Center Dynamics: https://www.datacenterdynamics.com/
- Data Center Knowledge: https://www.datacenterknowledge.com/
- Utility Dive: https://www.utilitydive.com/

**Deal-Specific Keywords:**
- "data center financing"
- "GPU-backed loan"
- "sale-leaseback data center"
- "compute infrastructure debt"
- "AI infrastructure investment"

---

### Appendix D: FRED Series Reference

| Series ID | Name | Update Frequency |
|-----------|------|------------------|
| BAMLH0A0HYM2 | ICE BofA US High Yield Index Option-Adjusted Spread | Daily |
| BAMLC0A4CBBB | ICE BofA BBB US Corporate Index Option-Adjusted Spread | Daily |
| DGS10 | Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity | Daily |
| SP500 | S&P 500 Index | Daily |
| NASDAQCOM | NASDAQ Composite Index | Daily |

**FRED API Documentation:** https://fred.stlouisfed.org/docs/api/fred/

---

### Appendix E: Environment Variables Reference

```bash
# .env.example

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@db.YOUR-PROJECT-REF.supabase.co:5432/postgres

# FRED API (required for credit data)
FRED_API_KEY=your_fred_api_key_here

# Email Configuration (required for alerts)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
ALERT_RECIPIENT=your-email@gmail.com

# Dashboard Configuration
DASHBOARD_URL=https://your-app.streamlit.app

# Development Settings
DEBUG=false
LOG_LEVEL=INFO
```

**Supabase Connection String Setup:**

1. Log in to https://supabase.com
2. Select your project
3. Navigate to Project Settings → Database
4. Under "Connection string", select "URI"
5. Copy the string and replace `[YOUR-PASSWORD]` with your database password
6. Store as `DATABASE_URL`

---

### Appendix F: Glossary

| Term | Definition |
|------|------------|
| **ABRI** | AI Bubble Risk Index; composite metric defined in this document |
| **Capex** | Capital expenditure; investments in property, plant, equipment |
| **HY OAS** | High Yield Option-Adjusted Spread; credit risk premium for junk bonds |
| **IG** | Investment Grade; bonds rated BBB- or higher |
| **Mag7** | "Magnificent Seven" — AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA |
| **OCF** | Operating Cash Flow; cash generated from business operations |
| **SPV** | Special Purpose Vehicle; off-balance-sheet financing entity |
| **DSO** | Days Sales Outstanding; accounts receivable collection metric |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | December 2024 | — | Initial specification |
| 1.1.0 | December 2024 | — | Updated: Supabase (PostgreSQL) instead of SQLite; Revenue Gap weight reduced to 10%; Deal Flow weight increased to 20%; Added Manual Input Prompt System (Section 4.6); Repository name: ai-infra-risk-index; Thresholds marked provisional |

**Related Documents:**
- `docs/BACKFILL_SEQUENCE.md` — Prioritized data loading sequence
- `docs/METHODOLOGY.md` — ABRI calculation methodology (TBD)
- `docs/DATA_DICTIONARY.md` — Field definitions (TBD)

---

*End of Technical Specification*
