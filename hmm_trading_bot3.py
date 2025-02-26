import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
import yfinance as yf
import matplotlib.pyplot as plt
import time
import argparse

def get_stock_data(ticker, start_date, end_date, timeframe='5m'):
    """
    Get stock data with configurable timeframe
    timeframe options: '1m', '5m', '15m', '30m', '1h', '1d', '1wk'
    """
    data = yf.download(ticker, start=start_date, end=end_date, interval=timeframe)
    return data

def get_realtime_data(ticker):
    data = yf.download(ticker, period='1d', interval='1m')
    return data

def add_features(data):
    # Handle potential division by zero and inf values
    data['Close_pct_change'] = data['Close'].pct_change().replace([np.inf, -np.inf], np.nan)
    data['Volume_pct_change'] = data['Volume'].pct_change().replace([np.inf, -np.inf], np.nan)
    data['Rolling_mean_5'] = data['Close'].rolling(window=5).mean()
    data['Rolling_mean_10'] = data['Close'].rolling(window=10).mean()
    data['MACD'] = data['Close'].ewm(span=12, adjust=False).mean() - data['Close'].ewm(span=26, adjust=False).mean()
    data['RSI'] = calculate_rsi(data['Close'])
    data['Bollinger_Upper'], data['Bollinger_Lower'] = calculate_bollinger_bands(data['Close'])
    data['ATR'] = calculate_atr(data)
    
    # Replace deprecated fillna method with ffill() and bfill()
    data = data.ffill().bfill()
    
    # Remove any remaining NaN or inf values
    data = data.replace([np.inf, -np.inf], np.nan).dropna()
    
    data['ATR'] = calculate_atr(data)
    return data

def calculate_rsi(series, period=14): # RSI = Relative Strength Index
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Avoid division by zero
    loss = loss.replace(0, np.nan)
    rs = gain / loss
    rs = rs.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(series, window=20, num_std_dev=2.0):  # increased from 1.5
    rolling_mean = series.rolling(window).mean()
    rolling_std = series.rolling(window).std()
    upper_band = rolling_mean + (rolling_std * num_std_dev)
    lower_band = rolling_mean - (rolling_std * num_std_dev)
    return upper_band, lower_band

def calculate_atr(data, period=14):
    high = data['High'].values.squeeze()
    low = data['Low'].values.squeeze()
    close = data['Close'].values.squeeze()
    
    # Calculate True Range
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    
    # Calculate maximum of the three true ranges
    true_range = np.maximum.reduce([tr1, tr2, tr3])
    
    # Convert to Series with the original index
    true_range = pd.Series(true_range, index=data.index)
    
    # Calculate ATR
    atr = true_range.rolling(window=period).mean()
    return atr

def calculate_stop_loss(entry_price, atr, multiplier=2):
    """
    entry_price: Entry price of the trade
    atr: Current ATR value
    multiplier: ATR multiplier for stop distance
    """
    stop_distance = atr * multiplier
    stop_loss = entry_price - stop_distance  # For long positions
    return stop_loss

def train_hmm(data, n_components=6):
    # Ensure all features are finite
    features = np.column_stack([
        data['Close_pct_change'].values,
        data['Volume_pct_change'].values,
        data['Rolling_mean_5'].values,
        data['Rolling_mean_10'].values,
        data['MACD'].values,
        data['RSI'].values,
        data['Bollinger_Upper'].values,
        data['Bollinger_Lower'].values
    ])
    
    # Remove any rows with non-finite values
    features = features[np.isfinite(features).all(axis=1)]
    
    if len(features) == 0:
        raise ValueError("No valid data points after cleaning")
    
    model = GaussianHMM(
        n_components=n_components, 
        covariance_type="diag", 
        n_iter=2000,
        tol=0.001
    )
    model.fit(features)
    return model

def predict_hmm(model, data):
    features = np.column_stack([data['Close_pct_change'],
                                data['Volume_pct_change'],
                                data['Rolling_mean_5'],
                                data['Rolling_mean_10'],
                                data['MACD'],
                                data['RSI'],
                                data['Bollinger_Upper'],
                                data['Bollinger_Lower']])
    
    hidden_states = model.predict(features)
    
    return hidden_states

def generate_signals(hidden_states, data, risk_level='moderate'):
    signals = pd.Series(hidden_states, index=data.index).diff().fillna(0)
    common_idx = signals.index.intersection(data.index)
    signals = signals.loc[common_idx]
    data = data.loc[common_idx]
    
    close_series = data["Close"].squeeze()
    boll_lower = data["Bollinger_Lower"].squeeze()
    boll_upper = data["Bollinger_Upper"].squeeze()
    
    # Add trend confirmation
    macd = data["MACD"].squeeze()
    rsi = data["RSI"].squeeze()
    
    # Modified risk parameters for balanced signals
    risk_params = {
        'conservative': {
            'bollinger_margin': 1.002,  # 0.2% margin
            'rsi_oversold': 35,         # Less extreme oversold
            'rsi_overbought': 65,       # Less extreme overbought
            'macd_threshold': 0.3,      # Reduced threshold
            'volume_threshold': 1.05     # 5% above average volume
        },
        'moderate': {
            'bollinger_margin': 1.003,  # 0.3% margin
            'rsi_oversold': 40,         # Moderate oversold
            'rsi_overbought': 60,       # Moderate overbought
            'macd_threshold': 0.2,      # Lower threshold
            'volume_threshold': 1.03     # 3% above average volume
        },
        'aggressive': {
            'bollinger_margin': 1.005,  # 0.5% margin
            'rsi_oversold': 45,         # Light oversold
            'rsi_overbought': 55,       # Light overbought
            'macd_threshold': 0.1,      # Minimal threshold
            'volume_threshold': 1.01     # 1% above average volume
        }
    }
    
    params = risk_params[risk_level]
    
    # Add volume confirmation
    volume = data["Volume"].squeeze()
    volume_ma = volume.rolling(window=20).mean()
    volume_condition = volume > (volume_ma * params['volume_threshold'])
    
    # More balanced conditions for buy/sell signals
    condition_buy = (
        (close_series < boll_lower * (1 + params['bollinger_margin'])) &
        (macd < 0) &  # MACD below zero line
        (rsi < params['rsi_oversold']) &
        volume_condition
    )
    
    condition_sell = (
        (close_series > boll_upper * (1 - params['bollinger_margin'])) &
        (macd > 0) &  # MACD above zero line
        (rsi > params['rsi_overbought']) &
        volume_condition
    )
    
    # Add ATR-based filters
    atr = data['ATR'].squeeze()
    avg_atr = atr.rolling(window=20).mean()
    
    # Only trade when volatility is favorable
    volatility_condition = (
        (atr > avg_atr * 0.8) &  # Enough volatility to trade
        (atr < avg_atr * 2.0)    # Not too volatile
    )
    
    condition_buy = (
        condition_buy &
        volatility_condition
    )
    
    condition_sell = (
        condition_sell &
        volatility_condition
    )
    
    # Equal thresholds for buy and sell signals
    buy_signals = signals[(signals != 0) & (condition_buy)].index
    sell_signals = signals[(signals != 0) & (condition_sell)].index

    return buy_signals, sell_signals

def calculate_position_size(balance, atr, risk_per_trade=0.02):
    """
    balance: Current account balance
    atr: Current ATR value
    risk_per_trade: Maximum risk per trade (default 2%)
    """
    risk_amount = balance * risk_per_trade
    position_size = risk_amount / atr
    return position_size

def backtest(data, buy_signals, sell_signals, strategy_config):
    initial_balance = 1000.0
    balance = initial_balance
    position = 0.0
    trades = []
    daily_trades = 0
    last_trade_date = None

    for buy_ts, sell_ts in zip(buy_signals, sell_signals):
        # Get prices first
        buy_pos = data.index.get_loc(buy_ts)
        sell_pos = data.index.get_loc(sell_ts)
        
        if buy_pos >= len(data) or sell_pos >= len(data):
            break

        buy_price = float(data['Close'].iloc[buy_pos].iloc[0])
        sell_price = float(data['Close'].iloc[sell_pos].iloc[0])

        # Check daily trade limit
        if last_trade_date != buy_ts.date():
            daily_trades = 0
        if daily_trades >= strategy_config['max_trades_per_day']:
            continue
            
        # Calculate position size based on risk
        position_size = calculate_position_size(
            balance=balance,
            atr=data['ATR'].iloc[buy_pos],
            risk_per_trade=strategy_config['stop_loss_pct']
        )
        stop_loss = buy_price * (1 - strategy_config['stop_loss_pct'])
        take_profit = buy_price * (1 + strategy_config['take_profit_pct'])
        
        # Check maximum portfolio loss
        if balance < initial_balance * (1 - strategy_config['max_loss_pct']):
            break

        if not np.isnan(buy_price) and not np.isnan(sell_price):
            position = balance / buy_price
            balance = 0
            trades.append((data.index[buy_pos], 'Buy', buy_price))

            balance = position * sell_price
            position = 0
            trades.append((data.index[sell_pos], 'Sell', sell_price))
            
            # Update trade tracking
            last_trade_date = buy_ts.date()
            daily_trades += 1

    if not data.empty:
        final_balance = float(balance + position * float(data['Close'].iloc[-1].iloc[0]))
    else:
        final_balance = float(balance)

    profit = final_balance - initial_balance
    return final_balance, profit, trades

def plot_signals(data, buy_signals, sell_signals, label):
    plt.plot(data['Close'], label=f'Close Price {label}')
    plt.scatter(data.loc[buy_signals].index, data.loc[buy_signals]['Close'], marker='^', color='g', label=f'Buy Signal {label}', alpha=1)
    plt.scatter(data.loc[sell_signals].index, data.loc[sell_signals]['Close'], marker='v', color='r', label=f'Sell Signal {label}', alpha=1)

def plot_bollinger_debug(data):
    plt.figure(figsize=(10,5))
    plt.plot(data.index, data['Close'], label='Close Price', color='black')
    plt.plot(data.index, data['Bollinger_Lower'], label='Bollinger Lower', color='blue')
    plt.plot(data.index, data['Bollinger_Upper'], label='Bollinger Upper', color='red')
    plt.title('Close Price and Bollinger Bands')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

def trade(strategy_config=None):
    initial_balance = 1000.0
    if strategy_config is None:
        strategy_config = {
            'timeframe': '5m',          # Trading interval
            'risk_level': 'moderate',   # Changed to moderate
            'position_size': 1.0,       # Full position size
            'stop_loss_pct': 0.02,      # 2% stop loss
            'max_trades_per_day': 1000,    # Increased daily trades
            'take_profit_pct': 0.03,    # 3% profit target
            'max_loss_pct': 0.05        # 5% maximum loss
        }
    
    ticker = 'ES=F'
    
    # Calculate dates within the 60-day limit for 5m data
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=45)  # Use 45 days to be safe
    
    try:
        # Get data with specified timeframe
        data = get_stock_data(ticker, start_date, end_date, strategy_config['timeframe'])
        if data.empty:
            raise ValueError("No data received from Yahoo Finance")
            
        data = add_features(data)
        model = train_hmm(data)
        hidden_states = predict_hmm(model, data)

        # Generate buy and sell signals
        buy_signals, sell_signals = generate_signals(hidden_states, data, 
                                                   risk_level=strategy_config['risk_level'])
        
        # Print diagnostics
        print(f"Data range: {data.index[0].strftime('%Y-%m-%d %H:%M')} to {data.index[-1].strftime('%Y-%m-%d %H:%M')}")
        print("Number of buy signals:", len(buy_signals))
        print("Number of sell signals:", len(sell_signals))
        
        final_balance, profit, trades = backtest(data, buy_signals, sell_signals, strategy_config)
        
        '''
        # Print trade history
        print("\nTrade history:")
        for buy, sell in zip(trades[::2], trades[1::2]):
            buy_date = buy[0].strftime('%Y-%m-%d %H:%M')
            sell_date = sell[0].strftime('%Y-%m-%d %H:%M')
            profit_loss = (sell[2] - buy[2]) * (initial_balance / buy[2])
            print(f"Buy:  {buy_date} at ${buy[2]:,.2f}")
            print(f"Sell: {sell_date} at ${sell[2]:,.2f}")
            print(f"Trade P/L: ${profit_loss:,.2f}\n")
        '''

         # Print financial results
        print(f"\nTrading Results:")
        print(f"Initial balance: ${initial_balance:,.2f}")
        print(f"Final balance:   ${final_balance:,.2f}")
        print(f"Total profit:    ${profit:,.2f} ({(profit/initial_balance)*100:.1f}%)")

        return data, buy_signals, sell_signals
        
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='HMM Trading Bot')
    args = parser.parse_args()

    data, buy_signals, sell_signals = trade()

'''
    # Create a figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 7))
    
    # First subplot: Trading signals
    ax1.plot(data['Close'], label='Close Price')
    ax1.scatter(data.loc[buy_signals].index, data.loc[buy_signals]['Close'], 
                marker='^', color='g', label='Buy Signal', alpha=1)
    ax1.scatter(data.loc[sell_signals].index, data.loc[sell_signals]['Close'], 
                marker='v', color='r', label='Sell Signal', alpha=1)
    ax1.set_title('E-mini S&P 500 Futures Price with Buy and Sell Signals')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price')
    ax1.legend()

    # Second subplot: Bollinger Bands
    ax2.plot(data.index, data['Close'], label='Close Price', color='black')
    ax2.plot(data.index, data['Bollinger_Lower'], label='Bollinger Lower', color='blue')
    ax2.plot(data.index, data['Bollinger_Upper'], label='Bollinger Upper', color='red')
    ax2.set_title('Close Price with Bollinger Bands')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Price')
    ax2.legend()

    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.show()
'''
if __name__ == "__main__":
    main()