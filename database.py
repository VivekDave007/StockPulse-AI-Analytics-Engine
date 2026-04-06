from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

DATABASE_URL = "sqlite:///./stock_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StockData(Base):
    __tablename__ = "stock_data"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    daily_return = Column(Float, nullable=True)
    ma_7 = Column(Float, nullable=True)
    volatility_7 = Column(Float, nullable=True)

Base.metadata.create_all(bind=engine)

def save_data_to_db(df, symbol):
    db = SessionLocal()
    try:
        # Prevent duplicates or keep it simple: clear old records for this symbol
        db.query(StockData).filter(StockData.symbol == symbol).delete()
        
        records = []
        for _, row in df.iterrows():
            record = StockData(
                symbol=symbol,
                date=row['Date'],
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume'],
                daily_return=row.get('Daily_Return'),
                ma_7=row.get('MA_7'),
                volatility_7=row.get('Volatility_7')
            )
            records.append(record)
        db.bulk_save_objects(records)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
