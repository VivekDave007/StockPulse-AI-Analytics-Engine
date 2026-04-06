import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

def predict_next_7_days(df: pd.DataFrame) -> dict:
    # Ensure no NaN values which might occur due to rolling windows
    df_clean = df.dropna(subset=['Close'])
    if len(df_clean) < 7:
        return {"error": "Not enough data points for prediction"}
        
    df_clean = df_clean.sort_values('Date')
    
    # Map dates to an integer (days from the start)
    start_date = df_clean['Date'].iloc[0]
    df_clean['Days'] = (df_clean['Date'] - start_date).dt.days
    
    X = df_clean[['Days']]
    y = df_clean['Close']
    
    # Train Linear Regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict next 7 days
    last_date = df_clean['Date'].iloc[-1]
    last_day_int = df_clean['Days'].iloc[-1]
    
    future_days = []
    future_dates = []
    for i in range(1, 8):
        future_days.append([last_day_int + i])
        future_dates.append((last_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d"))
        
    predictions = model.predict(future_days)
    
    return {
        "dates": future_dates,
        "predicted_close": predictions.tolist()
    }
