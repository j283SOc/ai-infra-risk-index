"""
SQLAlchemy ORM models for the AI Infrastructure Risk Index database.

All tables are defined here using SQLAlchemy 2.0 declarative syntax.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Index,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# =============================================================================
# Market Data Tables
# =============================================================================

class EquityPrice(Base):
    """Daily equity prices for tracked tickers."""
    
    __tablename__ = "equity_prices"
    
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(Integer)
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    
    __table_args__ = (
        Index("idx_equity_ticker_date", "ticker", "date"),
    )


class MarketMetric(Base):
    """Computed market structure metrics (concentration, correlation)."""
    
    __tablename__ = "market_metrics"
    
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    mag7_weight: Mapped[Optional[float]] = mapped_column(Float)  # Mag7 % of S&P 500
    tech_weight: Mapped[Optional[float]] = mapped_column(Float)  # Tech sector % of S&P 500
    nvda_spy_corr: Mapped[Optional[float]] = mapped_column(Float)  # 60-day rolling correlation
    mag7_spy_corr: Mapped[Optional[float]] = mapped_column(Float)  # Equal-weight Mag7 correlation
    leveraged_etf_aum: Mapped[Optional[float]] = mapped_column(Float)  # Combined AUM
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


# =============================================================================
# Credit Market Tables
# =============================================================================

class CreditSpread(Base):
    """Daily credit spread data from FRED."""
    
    __tablename__ = "credit_spreads"
    
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    hy_oas: Mapped[Optional[float]] = mapped_column(Float)  # High Yield OAS (bps)
    ig_bbb_oas: Mapped[Optional[float]] = mapped_column(Float)  # Investment Grade BBB OAS (bps)
    hy_ig_diff: Mapped[Optional[float]] = mapped_column(Float)  # Computed: hy_oas - ig_bbb_oas
    treasury_10y: Mapped[Optional[float]] = mapped_column(Float)  # 10-year Treasury yield
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


# =============================================================================
# GPU Market Tables
# =============================================================================

class GPUPricing(Base):
    """GPU rental pricing (semi-automated collection)."""
    
    __tablename__ = "gpu_pricing"
    
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    gpu_model: Mapped[str] = mapped_column(String(50), primary_key=True)  # 'H100-80GB', 'H200', etc.
    source: Mapped[str] = mapped_column(String(50), primary_key=True)  # 'vast.ai', 'lambda', etc.
    price_per_hour: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    
    __table_args__ = (
        Index("idx_gpu_model_date", "gpu_model", "date"),
    )


# =============================================================================
# Hyperscaler Financial Tables
# =============================================================================

class HyperscalerMetric(Base):
    """Quarterly financial metrics for hyperscalers (manual entry)."""
    
    __tablename__ = "hyperscaler_metrics"
    
    fiscal_period: Mapped[str] = mapped_column(String(20), primary_key=True)  # 'Q3 2024', 'FY 2024'
    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)  # 'MSFT', 'GOOGL', etc.
    capex: Mapped[Optional[float]] = mapped_column(Float)  # Capital expenditures ($M)
    operating_cf: Mapped[Optional[float]] = mapped_column(Float)  # Operating cash flow ($M)
    capex_ocf_ratio: Mapped[Optional[float]] = mapped_column(Float)  # Computed: capex / operating_cf
    ai_revenue: Mapped[Optional[float]] = mapped_column(Float)  # AI-attributed revenue ($M)
    ai_revenue_growth: Mapped[Optional[float]] = mapped_column(Float)  # QoQ growth rate
    total_debt: Mapped[Optional[float]] = mapped_column(Float)  # Total long-term debt ($M)
    total_equity: Mapped[Optional[float]] = mapped_column(Float)  # Total shareholders' equity ($M)
    adj_debt_equity: Mapped[Optional[float]] = mapped_column(Float)  # Adjusted leverage ratio
    days_sales_outstanding: Mapped[Optional[float]] = mapped_column(Float)  # DSO
    depreciation_expense: Mapped[Optional[float]] = mapped_column(Float)  # For tracking vs capex
    source_url: Mapped[Optional[str]] = mapped_column(Text)  # Link to 10-K/10-Q
    ai_revenue_methodology: Mapped[Optional[str]] = mapped_column(Text)  # How AI revenue was estimated
    entered_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


# =============================================================================
# Deal Flow Tables
# =============================================================================

class Deal(Base):
    """AI infrastructure financing deals (manual entry)."""
    
    __tablename__ = "deal_tracker"
    
    deal_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    announced_date: Mapped[date] = mapped_column(Date, nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_usd: Mapped[Optional[float]] = mapped_column(Float)  # Deal size in millions
    structure_type: Mapped[Optional[str]] = mapped_column(String(50))  # 'corporate_debt', 'spv', etc.
    counterparty: Mapped[Optional[str]] = mapped_column(String(200))
    is_circular: Mapped[bool] = mapped_column(Boolean, default=False)  # Involves circular financing
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    entered_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    
    __table_args__ = (
        Index("idx_deal_date", "announced_date"),
    )


# =============================================================================
# News Tables
# =============================================================================

class NewsItem(Base):
    """Aggregated news items with relevance scoring."""
    
    __tablename__ = "news_items"
    
    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    published_date: Mapped[Optional[date]] = mapped_column(Date)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    url: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-1
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    
    __table_args__ = (
        Index("idx_news_date", "published_date"),
    )


# =============================================================================
# ABRI Tables
# =============================================================================

class ABRIHistory(Base):
    """Historical ABRI composite index values."""
    
    __tablename__ = "abri_history"
    
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    concentration_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    correlation_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    credit_stress_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    gpu_deflation_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    capex_intensity_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    revenue_gap_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    deal_flow_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    composite_score: Mapped[Optional[float]] = mapped_column(Float)  # Weighted average
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


# =============================================================================
# Alert & Logging Tables
# =============================================================================

class AlertLog(Base):
    """Log of triggered alerts."""
    
    __tablename__ = "alert_log"
    
    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    alert_type: Mapped[Optional[str]] = mapped_column(String(20))  # 'breach_high', 'breach_low', 'trend'
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)


class CollectionLog(Base):
    """Log of data collection job runs."""
    
    __tablename__ = "collection_log"
    
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collection_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'equity', 'credit', etc.
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[Optional[str]] = mapped_column(String(20))  # 'success', 'partial', 'failed'
    records_added: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)


# =============================================================================
# Manual Entry Task Queue
# =============================================================================

class PendingManualTask(Base):
    """Queue of pending manual data entry tasks."""
    
    __tablename__ = "pending_manual_tasks"
    
    task_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'gpu_pricing', 'hyperscaler', 'deal'
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest, 10=lowest
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'in_progress', 'completed', 'skipped'
    data_payload: Mapped[Optional[dict]] = mapped_column(JSONB)  # Pre-populated template data
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_by: Mapped[Optional[str]] = mapped_column(String(100))
