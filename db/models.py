"""
db/models.py — SQLAlchemy models for Stocky AI.
Supports both Supabase (Postgres) and local SQLite fallback.
Owner: Person 2
"""
import ssl as _ssl
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, Date, DateTime, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import DATABASE_URL

# SSL context for asyncpg — Supabase pooler uses TLS but doesn't need hostname validation
_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE


def _make_engine():
    """Create async engine — works for both Supabase and SQLite."""
    url = DATABASE_URL

    # Ensure correct async driver prefix
    if "postgresql" in url and "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    elif "sqlite" in url and "aiosqlite" not in url:
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///")

    kwargs = {}
    if "postgresql" in url:
        # Supabase connection pool settings
        kwargs = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "connect_args": {"ssl": _ssl_ctx, "statement_cache_size": 0},
        }

    return create_async_engine(url, echo=False, **kwargs)


engine = _make_engine()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Inventory(Base):
    __tablename__ = "inventory"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    commodity       = Column(String, nullable=False)
    quantity_kg     = Column(Float, nullable=False)
    entry_date      = Column(Date, nullable=False)
    shelf_life_days = Column(Integer, default=7)
    cost_per_kg     = Column(Float, nullable=True)
    supplier_id     = Column(Integer, nullable=True)
    notes           = Column(Text, nullable=True)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String, nullable=False)
    phone       = Column(String, nullable=True)
    language    = Column(String, default="malay")
    reliability = Column(Float, default=5.0)


class SupplierPrice(Base):
    __tablename__ = "supplier_prices"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id  = Column(Integer, nullable=False)
    commodity    = Column(String, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    quantity_kg  = Column(Float, nullable=True)
    quoted_date  = Column(Date, nullable=False)
    source       = Column(String, default="direct")


class Trade(Base):
    __tablename__ = "trades"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    trade_type   = Column(String, nullable=False)
    commodity    = Column(String, nullable=False)
    quantity_kg  = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    counterparty = Column(String, nullable=True)
    trade_date   = Column(Date, nullable=False)
    notes        = Column(Text, nullable=True)


class Receivable(Base):
    __tablename__ = "receivables"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    buyer_name = Column(String, nullable=False)
    commodity  = Column(String, nullable=True)
    amount_rm  = Column(Float, nullable=False)
    due_date   = Column(Date, nullable=True)
    paid       = Column(Boolean, default=False)
    paid_date  = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FamaBenchmark(Base):
    __tablename__ = "fama_benchmarks"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    commodity    = Column(String, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    week_date    = Column(Date, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id     = Column(BigInteger, primary_key=True)   # Telegram user_id — BigInteger avoids int32 overflow
    name        = Column(String, nullable=True)
    language    = Column(String, default="English")
    commodities = Column(Text, nullable=True)          # JSON array e.g. '["tomato","bayam"]'
    city        = Column(String, default="Kuala Lumpur")
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LoanOffer(Base):
    __tablename__ = "loan_offers"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(BigInteger, nullable=False)
    amount_rm  = Column(Float, nullable=False)
    score      = Column(Integer, nullable=False)
    status     = Column(String, default="pending")   # pending | applied | disbursed | declined
    offered_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    """Create all tables if they don't exist. Safe to call repeatedly."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables ready.")
