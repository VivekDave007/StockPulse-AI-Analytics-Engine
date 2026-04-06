import yfinance as yf
import pandas as pd

def fetch_and_process_stock_data(symbol: str) -> pd.DataFrame:
    # TASK 2: Fetch and clean data
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo")
    
    df.reset_index(inplace=True)
    
    # Task 2: Convert date column properly
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    elif 'Datetime' in df.columns:
        df.rename(columns={'Datetime': 'Date'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
        
    # TASK 3: Add metrics
    df['Daily_Return'] = (df['Close'] - df['Open']) / df['Open']
    df['MA_7'] = df['Close'].rolling(window=7).mean()
    df['Volatility_7'] = df['Close'].rolling(window=7).std()
    
    return df
