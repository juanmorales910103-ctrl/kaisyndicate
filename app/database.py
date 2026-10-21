from datetime import datetime, timezone
import os
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/kai_syndicate.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBPosition(Base):
    __tablename__ = "portfolio_positions"
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(String(50), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    match_name = Column(String(150), nullable=False)
    market = Column(String(20), nullable=False)
    odds_provider = Column(Float, nullable=False)
    odds_fair_model = Column(Float, nullable=False)
    expected_value_ev = Column(Float, nullable=False)
    stake = Column(Float, nullable=False)
    status = Column(String(30), default="PENDING")
    net_pnl = Column(Float, default=0.0)

class DBLedgerEntry(Base):
    __tablename__ = "double_entry_ledger"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    position_id = Column(String(50), index=True, nullable=True)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    available_cash = Column(Float, nullable=False)
    net_worth = Column(Float, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
