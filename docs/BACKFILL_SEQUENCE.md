# Prioritized Backfill Sequence

**Purpose:** Step-by-step guide for loading historical data into the ABRI system, ordered to maximize functionality at each stage.

**Philosophy:** Get the dashboard functional with automated data first, then progressively enhance with manual data. Each phase produces a working (if incomplete) system.

---

## Overview

| Phase | Focus | Effort | Outcome |
|-------|-------|--------|---------|
| **Phase 0** | Infrastructure setup | 1-2 hours | Database ready, dashboard deployed |
| **Phase 1** | Automated data (5 years) | 2-4 hours | Market structure + credit panels functional |
| **Phase 2** | Recent GPU pricing | 1-2 hours | GPU economics panel functional |
| **Phase 3** | Hyperscaler financials (current) | 4-6 hours | Hyperscaler panel functional, partial ABRI |
| **Phase 4** | Historical hyperscaler data | 8-12 hours | Full ABRI calculation possible |
| **Phase 5** | Deal flow baseline | 4-8 hours | Deal flow panel functional, complete ABRI |
| **Phase 6** | Calibration & validation | 2-4 hours | Thresholds calibrated, system validated |

**Total Estimated Effort:** 22-38 hours spread over 2-4 weeks

---

## Phase 0: Infrastructure Setup

**Duration:** 1-2 hours  
**Prerequisites:** GitHub account, Supabase account, FRED API key, Gmail account

### Step 0.1: Create Supabase Project

1. Navigate to https://supabase.com and sign in
2. Click "New Project"
3. Configure:
   - **Name:** `ai-infra-risk-index`
   - **Database Password:** Generate strong password, save securely
   - **Region:** Choose closest to you
   - **Plan:** Free tier
4. Wait for project provisioning (~2 minutes)
5. Navigate to Project Settings → Database
6. Copy the connection string (URI format)
7. Replace `[YOUR-PASSWORD]` with your database password

### Step 0.2: Create GitHub Repository

1. Create new repository: `ai-infra-risk-index`
2. Initialize with README
3. Set visibility: Public (required for Streamlit Cloud)

### Step 0.3: Obtain API Keys

**FRED API Key:**
1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Create account or sign in
3. Request API key
4. Save key securely

**Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication if not already enabled
3. Navigate to App Passwords
4. Generate new app password for "Mail"
5. Save the 16-character password

### Step 0.4: Configure Repository Secrets

In GitHub repository → Settings → Secrets and variables → Actions:

| Secret Name | Value |
|-------------|-------|
| `DATABASE_URL` | Your Supabase connection string |
| `FRED_API_KEY` | Your FRED API key |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | Your Gmail App Password |
| `ALERT_RECIPIENT` | Email for alerts (can be same as SMTP_USER) |

### Step 0.5: Initialize Database Schema

Run locally or via GitHub Actions:

```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/ai-infra-risk-index.git
cd ai-infra-risk-index

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export DATABASE_URL="your-supabase-connection-string"

# Initialize schema
python scripts/init_db.py
```

### Step 0.6: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Connect GitHub account
3. Select repository: `ai-infra-risk-index`
4. Set main file: `dashboard/app.py`
5. Configure secrets (copy from .env)
6. Deploy

**Phase 0 Checkpoint:** ✅ Empty dashboard accessible at your Streamlit URL

---

## Phase 1: Automated Data Backfill (5 Years)

**Duration:** 2-4 hours  
**Prerequisites:** Phase 0 complete

This phase loads all data that can be collected automatically.

### Step 1.1: Equity Prices (5 Years)

```python
# scripts/backfill.py (excerpt)

from datetime import date, timedelta
from collectors.equity import fetch_daily_prices
from storage.db import get_session
from storage.models import EquityPrice

TICKERS = [
    # Mag7
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    # Indices
    "SPY", "QQQ", "XLK",
    # Leveraged ETFs
    "TQQQ", "SOXL", "TECL",
    # AI pure-plays (if trading)
    "CRWV", "AI", "PLTR"
]

def backfill_equity(start_date: date, end_date: date):
    """Backfill equity prices for all tickers."""
    print(f"Backfilling equity data from {start_date} to {end_date}")
    
    for ticker in TICKERS:
        print(f"  Fetching {ticker}...")
        try:
            data = fetch_daily_prices([ticker], start_date, end_date)
            
            with get_session() as session:
                for point in data:
                    session.merge(EquityPrice(
                        date=point.date,
                        ticker=point.ticker,
                        close=point.close,
                        volume=point.volume,
                        market_cap=point.market_cap
                    ))
            
            print(f"    ✅ {len(data)} records")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Rate limiting
        time.sleep(1)

# Run backfill
if __name__ == "__main__":
    end_date = date.today()
    start_date = end_date - timedelta(days=365 * 5)  # 5 years
    backfill_equity(start_date, end_date)
```

**Expected Output:**
- ~15 tickers × ~1,260 trading days = ~19,000 records
- Database size: ~5-10 MB
- Time: ~30-60 minutes (with rate limiting)

### Step 1.2: Credit Spreads (5 Years)

```python
def backfill_credit(start_date: date, end_date: date):
    """Backfill credit spread data from FRED."""
    from collectors.credit import fetch_credit_spreads
    
    print(f"Backfilling credit data from {start_date} to {end_date}")
    
    data = fetch_credit_spreads(start_date, end_date)
    
    with get_session() as session:
        for point in data:
            session.merge(CreditSpread(
                date=point.date,
                hy_oas=point.hy_oas,
                ig_bbb_oas=point.ig_bbb_oas,
                hy_ig_diff=point.hy_ig_diff,
                treasury_10y=point.treasury_10y
            ))
    
    print(f"  ✅ {len(data)} records")
```

**Expected Output:**
- ~1,260 trading days of data
- Time: ~5 minutes

### Step 1.3: Compute Market Metrics (5 Years)

After equity data is loaded, compute derived metrics:

```python
def backfill_market_metrics(start_date: date, end_date: date):
    """Compute market metrics from equity data."""
    from analytics.correlation import compute_market_metrics
    
    print(f"Computing market metrics from {start_date} to {end_date}")
    
    # Need 60 days of data before we can compute correlations
    compute_start = start_date + timedelta(days=60)
    
    current = compute_start
    while current <= end_date:
        try:
            metrics = compute_market_metrics(as_of_date=current)
            
            with get_session() as session:
                session.merge(MarketMetric(
                    date=current,
                    mag7_weight=metrics.mag7_weight,
                    tech_weight=metrics.tech_weight,
                    nvda_spy_corr=metrics.nvda_spy_corr,
                    mag7_spy_corr=metrics.mag7_spy_corr
                ))
        except Exception as e:
            print(f"  ⚠️ {current}: {e}")
        
        current += timedelta(days=1)
    
    print(f"  ✅ Metrics computed")
```

**Expected Output:**
- ~1,200 days of computed metrics
- Time: ~15-30 minutes

### Phase 1 Checkpoint

At this point, your dashboard should show:
- ✅ **Market Structure panel:** Mag7 concentration, correlations over 5 years
- ✅ **Credit Stress panel:** Spread history over 5 years
- ⏸️ **GPU Economics panel:** Empty (Phase 2)
- ⏸️ **Hyperscaler Health panel:** Empty (Phase 3)
- ⏸️ **Deal Flow panel:** Empty (Phase 5)
- ⏸️ **ABRI Score:** Partial calculation possible (2 of 7 components)

---

## Phase 2: GPU Pricing Data

**Duration:** 1-2 hours  
**Prerequisites:** Phase 1 complete

GPU pricing data is collected manually. Start with recent data to make the panel functional.

### Step 2.1: Collect Current GPU Pricing

Visit each source and record current pricing:

| Source | URL | Login Required |
|--------|-----|----------------|
| vast.ai | https://vast.ai/console/create/ | Yes |
| Lambda Labs | https://lambdalabs.com/service/gpu-cloud | No |
| RunPod | https://www.runpod.io/gpu-instance/pricing | No |
| CoreWeave | https://www.coreweave.com/pricing | No |

Record prices for:
- H100-80GB (primary benchmark)
- H200 (if available)
- A100-80GB
- A100-40GB
- L40S

### Step 2.2: Enter Current Data via Dashboard

1. Navigate to your dashboard
2. Go to "Manual Entry" page
3. Enter today's GPU pricing
4. Save entries

### Step 2.3: Research Historical GPU Pricing

Historical GPU pricing requires research. Key data points:

| Date | Event | H100 Price Reference |
|------|-------|---------------------|
| Q1 2023 | H100 launch, scarcity | ~$4-8/hr (anecdotal) |
| Q3 2023 | Peak scarcity | ~$8/hr |
| Q1 2024 | Supply improving | ~$3-5/hr |
| Q3 2024 | Oversupply emerging | ~$1.50-2.50/hr |
| Q4 2024 | Current | Check current sources |

**Sources for Historical Research:**
- SemiAnalysis articles (some free)
- Twitter/X threads from ML practitioners
- Hacker News discussions
- Lambda Labs blog posts
- Archived pricing pages (Wayback Machine)

### Step 2.4: Enter Historical Data Points

Enter at minimum one data point per quarter since H100 launch:
- Q2 2023
- Q3 2023
- Q4 2023
- Q1 2024
- Q2 2024
- Q3 2024
- Q4 2024

**Note:** Exact historical prices are difficult to verify. Document your sources and use best estimates. The trend matters more than precision.

### Phase 2 Checkpoint

- ✅ **GPU Economics panel:** Shows current pricing, partial history
- ⏸️ **ABRI Score:** 3 of 7 components (concentration, correlation, GPU deflation)

---

## Phase 3: Current Hyperscaler Financials

**Duration:** 4-6 hours  
**Prerequisites:** Phase 2 complete

Focus on the most recent quarter for each hyperscaler to make the panel functional.

### Step 3.1: Identify Latest Filings

As of December 2024, the most recent filings are approximately:

| Company | Ticker | Latest Filing | Fiscal Period |
|---------|--------|---------------|---------------|
| Microsoft | MSFT | 10-Q | Q1 FY2025 (Jul-Sep 2024) |
| Alphabet | GOOGL | 10-Q | Q3 2024 |
| Amazon | AMZN | 10-Q | Q3 2024 |
| Meta | META | 10-Q | Q3 2024 |
| NVIDIA | NVDA | 10-Q | Q3 FY2025 (Aug-Oct 2024) |

### Step 3.2: Download Filings

Use the SEC EDGAR links from Appendix A of the Technical Specification, or run:

```bash
python -m collectors.sec_edgar --download-latest --tickers MSFT,GOOGL,AMZN,META,NVDA
```

### Step 3.3: Extract Data for Each Company

For each company, extract:

| Metric | Location | Notes |
|--------|----------|-------|
| Capex | Cash Flow Statement | "Additions to property and equipment" or similar |
| Operating Cash Flow | Cash Flow Statement | "Net cash from operations" |
| Total Debt | Balance Sheet | Long-term + current portion |
| Total Equity | Balance Sheet | "Total stockholders' equity" |
| Depreciation | Income Statement or CF | "Depreciation and amortization" |
| AI Revenue | Segment disclosure / Earnings call | Requires estimation |

### Step 3.4: AI Revenue Estimation Guidelines

AI revenue is not consistently disclosed. Use these estimation approaches:

**Microsoft:**
- Azure revenue is disclosed
- Estimate AI portion as 15-25% of Azure based on management commentary
- Track Copilot mentions in earnings calls

**Alphabet:**
- Google Cloud revenue is disclosed
- Estimate AI portion as 20-30% based on AI feature mentions
- Track Gemini/AI mentions in earnings calls

**Amazon:**
- AWS revenue is disclosed
- Estimate AI portion as 10-20% (more conservative, less AI-specific messaging)
- Track Bedrock/AI mentions

**Meta:**
- No direct AI revenue disclosure
- Consider Advantage+ AI ad spending mentions
- Conservative approach: minimal attribution

**NVIDIA:**
- Data Center segment is ~90% AI-driven
- Use Data Center revenue directly as AI revenue proxy

### Step 3.5: Enter Data via Dashboard

1. Navigate to Manual Entry page
2. Complete the hyperscaler form for each company
3. Document AI revenue estimation methodology
4. Save with source URLs

### Phase 3 Checkpoint

- ✅ **Hyperscaler Health panel:** Shows current quarter metrics
- ⏸️ **ABRI Score:** 5 of 7 components (adds capex intensity, revenue gap)

---

## Phase 4: Historical Hyperscaler Financials

**Duration:** 8-12 hours (spread over multiple sessions)  
**Prerequisites:** Phase 3 complete

Backfill 5 years of quarterly data for full ABRI calibration.

### Step 4.1: Determine Filing Scope

5 years × 4 quarters × 5 companies = **100 quarterly data points**

Prioritization (if time-constrained):
1. **High priority:** Last 3 years (60 data points) — captures AI investment pivot
2. **Medium priority:** Years 4-5 (40 data points) — pre-AI baseline
3. **Lower priority:** Older data if available

### Step 4.2: Batch Processing Strategy

Process by company to maintain context:

**Week 1: NVIDIA** (most important for GPU/AI context)
- FY2020 through FY2025 (20 quarters)
- Pay special attention to Data Center revenue growth

**Week 1-2: Microsoft**
- FY2020 through FY2025 (20 quarters)
- Track Azure growth trajectory

**Week 2: Alphabet**
- 2020 through 2024 (20 quarters)
- Track Google Cloud growth

**Week 2-3: Amazon**
- 2020 through 2024 (20 quarters)
- Track AWS growth

**Week 3: Meta**
- 2020 through 2024 (20 quarters)
- Note: Heavy capex shift to "Reality Labs" then AI

### Step 4.3: Data Entry Tips

- Use browser tabs to have filing and dashboard side-by-side
- Copy/paste SEC filing URL for each entry
- For AI revenue, apply consistent methodology across all quarters
- Document estimation approach in notes field
- Take breaks — data entry fatigue leads to errors

### Step 4.4: Validation Checks

After entering data, run validation:

```python
def validate_hyperscaler_data():
    """Check for data quality issues."""
    with get_session() as session:
        # Check for missing quarters
        for ticker in ["MSFT", "GOOGL", "AMZN", "META", "NVDA"]:
            entries = session.query(HyperscalerMetrics).filter(
                HyperscalerMetrics.ticker == ticker
            ).order_by(HyperscalerMetrics.fiscal_period).all()
            
            print(f"{ticker}: {len(entries)} quarters")
            
            # Check for outliers
            capex_values = [e.capex for e in entries if e.capex]
            if capex_values:
                mean_capex = sum(capex_values) / len(capex_values)
                for e in entries:
                    if e.capex and (e.capex > mean_capex * 3 or e.capex < mean_capex / 3):
                        print(f"  ⚠️ Outlier: {e.fiscal_period} capex={e.capex}")
```

### Phase 4 Checkpoint

- ✅ **Hyperscaler Health panel:** Full 5-year history
- ✅ **ABRI Calibration:** Can compute historical percentiles for capex/revenue metrics
- ⏸️ **ABRI Score:** 6 of 7 components (missing deal flow)

---

## Phase 5: Deal Flow Baseline

**Duration:** 4-8 hours  
**Prerequisites:** Phase 4 complete

Build initial deal tracker with significant AI infrastructure financing deals.

### Step 5.1: Research Major Deals

Key deals to research (non-exhaustive):

**2022:**
- CoreWeave early funding rounds
- Microsoft datacenter expansion announcements

**2023:**
- CoreWeave $2.3B debt facility (April 2023)
- Microsoft datacenter announcements
- Google datacenter investments

**2024:**
- CoreWeave $7.5B debt facility (May 2024)
- CoreWeave IPO filing/withdrawal
- Blackstone datacenter investments
- NVIDIA-backed infrastructure deals

**Sources:**
- SEC 8-K filings for material agreements
- Company press releases
- Data Center Dynamics archives
- Bloomberg/Reuters deal announcements (summaries often free)
- The Information (if subscribed)

### Step 5.2: Deal Entry Template

For each deal, capture:

| Field | Description | Example |
|-------|-------------|---------|
| Announced Date | When publicly announced | 2024-05-15 |
| Company | Primary company | CoreWeave |
| Amount (USD millions) | Deal size | 7500 |
| Structure Type | Deal structure | spv, corporate_debt, sale_leaseback, equity |
| Counterparty | Lender/investor | Blackstone, Magnetar |
| Is Circular | Involves circular financing | Yes if NVIDIA/OpenAI related |
| Source URL | Press release or filing | https://... |
| Notes | Additional context | "Secured by NVIDIA GPUs" |

### Step 5.3: Circular Deal Identification

Flag deals as "circular" if they involve interconnected parties:
- NVIDIA investing in companies that buy NVIDIA GPUs
- OpenAI/Microsoft cross-investments
- Hyperscalers investing in AI startups that consume their cloud services

### Step 5.4: Enter via Dashboard

1. Navigate to Manual Entry page
2. Use deal entry form for each significant deal
3. Prioritize deals >$500M
4. Include source URLs

### Phase 5 Checkpoint

- ✅ **Deal Flow panel:** Shows major deals with circular financing flags
- ✅ **ABRI Score:** All 7 components calculable
- ⏸️ **Calibration:** Thresholds still provisional

---

## Phase 6: Calibration & Validation

**Duration:** 2-4 hours  
**Prerequisites:** Phases 1-5 complete

Calibrate ABRI thresholds and validate system behavior.

### Step 6.1: Compute Historical ABRI

Run ABRI calculation across full historical period:

```python
def compute_historical_abri():
    """Compute ABRI for all dates with sufficient data."""
    from analytics.abri import compute_abri
    from datetime import date, timedelta
    
    # Start from when we have all required data
    # (likely ~3 years back due to AI-specific metrics)
    start_date = date(2022, 1, 1)
    end_date = date.today()
    
    results = []
    current = start_date
    
    while current <= end_date:
        try:
            abri = compute_abri(current)
            results.append(abri)
            
            # Save to database
            with get_session() as session:
                session.merge(ABRIHistory(
                    date=current,
                    concentration_score=abri.concentration_score,
                    correlation_score=abri.correlation_score,
                    credit_stress_score=abri.credit_stress_score,
                    gpu_deflation_score=abri.gpu_deflation_score,
                    capex_intensity_score=abri.capex_intensity_score,
                    revenue_gap_score=abri.revenue_gap_score,
                    deal_flow_score=abri.deal_flow_score,
                    composite_score=abri.composite_score
                ))
        except Exception as e:
            print(f"  ⚠️ {current}: {e}")
        
        current += timedelta(days=7)  # Weekly granularity
    
    return results
```

### Step 6.2: Analyze Distribution

Examine historical ABRI distribution:

```python
import pandas as pd
import numpy as np

def analyze_abri_distribution(results):
    """Analyze historical ABRI for threshold calibration."""
    scores = [r.composite_score for r in results]
    
    print("ABRI Distribution Analysis")
    print("=" * 40)
    print(f"Count: {len(scores)}")
    print(f"Min: {min(scores):.1f}")
    print(f"Max: {max(scores):.1f}")
    print(f"Mean: {np.mean(scores):.1f}")
    print(f"Median: {np.median(scores):.1f}")
    print(f"Std Dev: {np.std(scores):.1f}")
    print()
    print("Percentiles:")
    for p in [10, 25, 50, 75, 90, 95]:
        print(f"  {p}th: {np.percentile(scores, p):.1f}")
```

### Step 6.3: Threshold Review

Compare computed thresholds against initial assumptions:

| Level | Initial Threshold | Historical Percentile | Adjustment Needed? |
|-------|-------------------|----------------------|-------------------|
| Normal | 0-30 | Should be ~50th percentile | TBD |
| Elevated | 30-50 | Should be ~75th percentile | TBD |
| Bubble | 50-70 | Should be ~90th percentile | TBD |
| Extreme | 70-100 | Should be >95th percentile | TBD |

### Step 6.4: Document Calibration Decisions

Create `docs/CALIBRATION_LOG.md` documenting:
- Historical distribution statistics
- Threshold adjustments made
- Rationale for changes
- Known limitations (e.g., short GPU pricing history)

### Step 6.5: Alert Threshold Testing

Verify alert thresholds fire appropriately:

```python
def test_alerts_on_historical_data():
    """Backtest alert logic against historical ABRI."""
    from analytics.signals import check_for_alerts
    
    # Load historical ABRI
    with get_session() as session:
        history = session.query(ABRIHistory).order_by(ABRIHistory.date).all()
    
    alert_count = 0
    for entry in history:
        alerts = check_for_alerts(as_of_date=entry.date)
        if alerts:
            alert_count += len(alerts)
            print(f"{entry.date}: {len(alerts)} alerts")
            for a in alerts:
                print(f"  - {a.metric_name}: {a.current_value:.1f} vs {a.threshold:.1f}")
    
    print(f"\nTotal alerts over period: {alert_count}")
    print(f"Average alerts per week: {alert_count / len(history):.2f}")
```

**Target:** 1-3 alerts per month on average. If significantly higher, thresholds may be too sensitive.

### Phase 6 Checkpoint

- ✅ **Full System:** All panels functional with historical data
- ✅ **ABRI:** Calibrated thresholds with documented rationale
- ✅ **Alerts:** Validated against historical data
- ✅ **Ready for Production:** Enable scheduled workflows

---

## Post-Backfill: Enable Automation

After completing all phases:

### Enable GitHub Actions Workflows

1. Verify all secrets are configured
2. Enable the daily workflow
3. Enable the weekly workflow
4. Enable the quarterly reminder workflow

### Set Up Monitoring

1. Check dashboard daily for first week
2. Verify email alerts are delivered
3. Monitor Supabase usage (should stay well under limits)

### Establish Maintenance Routine

**Weekly:**
- Update GPU pricing via Manual Entry page
- Review news feed for deal announcements

**Quarterly:**
- Update hyperscaler financials after earnings
- Review and update deal tracker

**Annually:**
- Review ABRI threshold calibration
- Archive old data if approaching storage limits

---

## Appendix: Time Estimates by Data Source

| Data Source | Records | Automation | One-Time Effort | Ongoing Effort |
|-------------|---------|------------|-----------------|----------------|
| Equity prices | ~19,000 | Full | 1 hour | 0 |
| Credit spreads | ~1,260 | Full | 15 min | 0 |
| Market metrics | ~1,200 | Full (computed) | 30 min | 0 |
| GPU pricing | ~50-100 | Manual | 2 hours | 15 min/week |
| Hyperscaler financials | ~100 | Manual | 12 hours | 2 hours/quarter |
| Deal flow | ~50-100 | Manual | 6 hours | 30 min/month |

---

## Appendix: Troubleshooting Common Issues

### "Connection refused" from Supabase

- Check DATABASE_URL format
- Verify password doesn't contain special characters that need escaping
- Check Supabase project isn't paused (activity within 7 days)

### Yahoo Finance rate limiting

- Add `time.sleep(1)` between requests
- Run backfill during off-peak hours
- Use batch requests where possible

### FRED API errors

- Verify API key is valid
- Check series IDs haven't changed
- FRED has occasional maintenance windows

### Missing historical data

- Some tickers may not have full 5-year history
- ETFs like SOXL have shorter histories
- Document data gaps in calibration notes

---

*End of Backfill Sequence Guide*
