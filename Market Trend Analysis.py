import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller


def analyze_market_trends(data, price_column='price', date_column='date'):
    """
    Comprehensive market trend analysis including multiple technical indicators
    and statistical tests.
    
    Parameters:
    data (pd.DataFrame): DataFrame with date and price columns
    price_column (str): Name of the column containing price data
    date_column (str): Name of the column containing dates
    
    Returns:
    dict: Dictionary containing various trend indicators and analysis results
    """
    # Ensure data is sorted by date
    df = data.sort_values(date_column).copy()
    df[date_column] = pd.to_datetime(df[date_column])
    df.set_index(date_column, inplace=True)
    
    # Calculate basic statistics
    basic_stats = {
        'mean': df[price_column].mean(),
        'std': df[price_column].std(),
        'min': df[price_column].min(),
        'max': df[price_column].max()
    }
    
    # Calculate moving averages
    df['MA20'] = df[price_column].rolling(window=20).mean()
    df['MA50'] = df[price_column].rolling(window=50).mean()
    
    # Calculate momentum indicators
    df['ROC'] = df[price_column].pct_change(periods=20) * 100  # Rate of Change
    df['RSI'] = calculate_rsi(df[price_column])
    
    # Perform trend analysis
    trend_analysis = {
        'linear_trend': calculate_linear_trend(df[price_column]),
        'adf_test': perform_stationarity_test(df[price_column]),
        'volatility': calculate_volatility(df[price_column])
    }
    
    # Decompose time series
    if len(df) >= 2:  # Ensure enough data points
        decomposition = seasonal_decompose(df[price_column], period=min(len(df), 30))
        trend_analysis['seasonal_decomposition'] = {
            'trend': decomposition.trend,
            'seasonal': decomposition.seasonal,
            'residual': decomposition.resid
        }
    
    return {
        'data': df,
        'basic_stats': basic_stats,
        'trend_analysis': trend_analysis
    }

def calculate_rsi(prices, periods=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_linear_trend(prices):
    """Calculate linear trend and related statistics"""
    x = np.arange(len(prices))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, prices)
    
    return {
        'slope': slope,
        'r_squared': r_value**2,
        'p_value': p_value,
        'trend_direction': 'upward' if slope > 0 else 'downward'
    }

def perform_stationarity_test(prices):
    """Perform Augmented Dickey-Fuller test for stationarity"""
    adf_result = adfuller(prices.dropna())
    return {
        'test_statistic': adf_result[0],
        'p_value': adf_result[1],
        'is_stationary': adf_result[1] < 0.05
    }

def calculate_volatility(prices, window=20):
    """Calculate rolling volatility"""
    return prices.rolling(window=window).std()