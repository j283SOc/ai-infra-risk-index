# AI Infrastructure Risk Index (ABRI)

A monitoring framework for tracking indicators of speculative excess in AI infrastructure investment. The system synthesizes publicly available data into a composite risk index and presents findings via an interactive dashboard with automated alerting.

## Overview

The AI Bubble Risk Index (ABRI) monitors seven key indicators:

| Component | Weight | Description |
|-----------|--------|-------------|
| **Concentration** | 15% | Mag7 market cap as % of S&P 500 |
| **Correlation** | 10% | NVDA-SPY 60-day rolling correlation |
| **Credit Stress** | 15% | High Yield - Investment Grade spread differential |
| **GPU Deflation** | 15% | H100 rental price collapse indicator |
| **Capex Intensity** | 15% | Hyperscaler capex/operating cash flow ratio |
| **Revenue Gap** | 10% | AI capex vs AI revenue disconnect |
| **Deal Flow** | 20% | AI infrastructure financing acceleration |

## Project Status

🚧 **Under Development** - See [Technical Specification](docs/TECHNICAL_SPECIFICATION.md) for full details.

## Quick Start

### Prerequisites

- Python 3.11+
- Supabase account (free tier)
- FRED API key (free)
- Gmail account with App Password

### Installation

```bash
# Clone repository
git clone https://github.com/j283SOc/ai-infra-risk-index.git
cd ai-infra-risk-index

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

### Initialize Database

```bash
export DATABASE_URL="your-supabase-connection-string"
python scripts/init_db.py
```

### Run Dashboard Locally

```bash
streamlit run dashboard/app.py
```

## Documentation

- [Technical Specification](docs/TECHNICAL_SPECIFICATION.md) - Complete system architecture and API design
- [Backfill Sequence](docs/BACKFILL_SEQUENCE.md) - Step-by-step data loading guide

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Data Collectors   │────▶│   Supabase (DB)     │
│   (GitHub Actions)  │     │   (PostgreSQL)      │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                                       ▼
┌─────────────────────┐     ┌─────────────────────┐
│   ABRI Calculator   │────▶│   Streamlit Cloud   │
│   (Analytics)       │     │   (Dashboard)       │
└─────────────────────┘     └─────────────────────┘
```

## Data Sources

| Source | Automation | Update Frequency |
|--------|------------|------------------|
| Yahoo Finance | Full | Daily |
| FRED | Full | Daily |
| SEC EDGAR | Semi-auto | Quarterly |
| GPU Pricing | Manual | Weekly |
| Deal Flow | Manual | Ongoing |

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

This is a personal project. Issues and suggestions welcome.
