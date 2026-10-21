
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

Base = declarative_base()
ENGINE_URL = "sqlite:///kai_syndicate.db"
engine = create_engine(ENGINE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DBPosition(Base):
    __tablename__ = "positions"
    position_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    match_name = Column(String, index=True)
    league = Column(String)
    market = Column(String)
    odds_placed = Column(Float)
    odds_fair_model = Column(Float)
    expected_value_ev = Column(Float)
    stake_usd = Column(Float)
    status = Column(String, default="PENDING")
    odds_closing = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DBLedgerEntry(Base):
    __tablename__ = "ledger"
    entry_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    transaction_type = Column(String)
    amount = Column(Float)
    available_cash = Column(Float)
    net_worth = Column(Float)
    reference_id = Column(String, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)
