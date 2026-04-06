from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import os

from data_fetcher import fetch_and_process_stock_data
from database import save_data_to_db
from ml_model import predict_next_7_days

app = FastAPI(title="Stock Data Dashboard API")

# Setup CORS just in case frontend is run separately later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

DEFAULT_COMPANIES = ["INFY.NS", "TCS.NS", "RELIANCE.NS", "AAPL", "MSFT", "GOOGL"]

# TASK 5: Root Endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Stock Data Dashboard. Visit /static/index.html to view the dashboard UI."}

# TASK 6.1: Companies API
@app.get("/companies")
def get_companies():
    return {"companies": DEFAULT_COMPANIES}

# TASK 6.2: Data API
@app.get("/data/{symbol}")
def get_data(symbol: str):
    try:
        # Fetch, clean and add metrics
        df = fetch_and_process_stock_data(symbol)
        if df.empty:
            return {"error": "Invalid symbol or no data available"}
        
        # Save to SQLite db
        save_data_to_db(df, symbol)
        
        # Return last 30 days
        df_last_30 = df.tail(30).copy()
        
        # Format Dates back to string so JSON easily reads them
        df_last_30['Date'] = df_last_30['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Replace NaNs with None for JSON parsing
        df_last_30 = df_last_30.where(pd.notna(df_last_30), None)
        
        return df_last_30.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

# TASK 6.3: Summary API
@app.get("/summary/{symbol}")
def get_summary(symbol: str):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1y")
    if df.empty:
        return {"error": "Could not fetch data for this symbol."}
        
    high_52 = float(df['High'].max())
    low_52 = float(df['Low'].min())
    avg_close = float(df['Close'].mean())
    
    return {
        "symbol": symbol,
        "52_week_high": round(high_52, 2),
        "52_week_low": round(low_52, 2),
        "average_closing_price": round(avg_close, 2)
    }

# TASK 6.4: Compare API
@app.get("/compare")
def compare_stocks(symbol1: str, symbol2: str):
    t1 = yf.Ticker(symbol1).history(period="1d")
    t2 = yf.Ticker(symbol2).history(period="1d")
    
    p1 = float(t1['Close'].iloc[0]) if not t1.empty else None
    p2 = float(t2['Close'].iloc[0]) if not t2.empty else None
    
    return {
        "comparison": {
            symbol1: p1,
            symbol2: p2
        }
    }

# TASK 6.5: Market Movers API
@app.get("/market/movers")
def get_market_movers():
    try:
        data = []
        for sym in DEFAULT_COMPANIES:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                prev_close = float(hist['Close'].iloc[-2])
                curr_close = float(hist['Close'].iloc[-1])
                pct_change = ((curr_close - prev_close) / prev_close) * 100
                data.append({
                    "symbol": sym,
                    "price": round(curr_close, 2),
                    "change_pct": round(pct_change, 2)
                })
        
        # Sort sequentially
        data.sort(key=lambda x: x["change_pct"], reverse=True)
        return {
            "top_gainers": [x for x in data if x["change_pct"] > 0][:3],  # Up to 3 positive
            "top_losers": [x for x in data if x["change_pct"] < 0][::-1][:3], # Up to 3 negative
            "neutral": [x for x in data if x["change_pct"] == 0]
        }
    except Exception as e:
        return {"error": str(e)}

# TASK 8: Predict API
@app.get("/predict/{symbol}")
def predict_stock(symbol: str):
    try:
        df = fetch_and_process_stock_data(symbol)
        prediction = predict_next_7_days(df)
        prediction["symbol"] = symbol
        return prediction
    except Exception as e:
        return {"error": str(e)}

# TASK 9: Correlation API
@app.get("/correlation")
def calculate_correlation(symbol1: str, symbol2: str):
    df1 = fetch_and_process_stock_data(symbol1)
    df2 = fetch_and_process_stock_data(symbol2)
    
    merged = pd.merge(df1[['Date', 'Close']], df2[['Date', 'Close']], on='Date', suffixes=('_1', '_2'))
    
    if len(merged) < 2:
        return {"error": "Not enough common data points."}
        
    correlation = merged['Close_1'].corr(merged['Close_2'])
    
    return {
        "symbol1": symbol1,
        "symbol2": symbol2,
        "correlation": float(correlation)
    }
