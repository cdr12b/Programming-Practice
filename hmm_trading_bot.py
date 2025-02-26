import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
import yfinance as yf
import matplotlib.pyplot as plt

def get_stock_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

def add_features(data):
    data['Close_pct_change'] = data['Close'].pct_change()
    data['Volume_pct_change'] = data['Volume'].pct_change()
    data['Rolling_mean_5'] = data['Close'].rolling(window=5).mean()
    data['Rolling_mean_10'] = data['Close'].rolling(window=10).mean()
    data['MACD'] = data['Close'].ewm(span=12, adjust=False).mean() - data['Close'].ewm(span=26, adjust=False).mean()
    data['RSI'] = calculate_rsi(data['Close'])
    data.dropna(inplace=True)
    return data

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def train_hmm(data):
    features = np.column_stack([data['Close_pct_change'],
                                data['Volume_pct_change'],
                                data['Rolling_mean_5'],
                                data['Rolling_mean_10'],
                                data['MACD'],
                                data['RSI']])
    
    model = GaussianHMM(n_components=4, covariance_type="diag", n_iter=2000, tol=0.01)
    model.fit(features)
    
    return model

def predict_hmm(model, data):
    features = np.column_stack([data['Close_pct_change'],
                                data['Volume_pct_change'],
                                data['Rolling_mean_5'],
                                data['Rolling_mean_10'],
                                data['MACD'],
                                data['RSI']])
    
    hidden_states = model.predict(features)
    
    return hidden_states

def generate_signals(hidden_states):
    signals = pd.Series(hidden_states).diff().fillna(0)
    buy_signals = signals[signals == 1].index
    sell_signals = signals[signals == -1].index
    
    return buy_signals, sell_signals

def backtest(data, buy_signals, sell_signals):
    """
    Backtests the trading strategy using historical data and generated signals.

    Parameters:
    data (pd.DataFrame): The historical stock data with features.
    buy_signals (pd.Index): The indices of buy signals.
    sell_signals (pd.Index): The indices of sell signals.

    Returns:
    tuple: A tuple containing the final balance, profit, and a list of trades.
    """
    initial_balance = 10000
    balance = initial_balance
    position = 0.0
    trades = []

    for buy_idx, sell_idx in zip(buy_signals, sell_signals):
        if buy_idx >= len(data) or sell_idx >= len(data):
            break
        
        buy_price = int(data['Close'].iloc[buy_idx].iloc[0])
        sell_price = int(data['Close'].iloc[sell_idx].iloc[0])
        if not np.isnan(buy_price) and not np.isnan(sell_price):
            position = balance / buy_price
            balance = 0
            trades.append((data.index[buy_idx], 'Buy', buy_price))
            
            balance = position * sell_price
            position = 0
            trades.append((data.index[sell_idx], 'Sell', sell_price))
    
    if not data.empty:
        final_balance = int(balance + position * data['Close'].iloc[-1].iloc[0])
    else:
        final_balance = int(balance)
    
    profit = final_balance - initial_balance
    return final_balance, profit, trades

def plot_signals(data, buy_signals, sell_signals):
    plt.figure(figsize=(14, 7))
    plt.plot(data['Close'], label='Close Price')
    plt.scatter(data.iloc[buy_signals].index, data.iloc[buy_signals]['Close'], marker='^', color='g', label='Buy Signal', alpha=1)
    plt.scatter(data.iloc[sell_signals].index, data.iloc[sell_signals]['Close'], marker='v', color='r', label='Sell Signal', alpha=1)
    plt.title('E-mini S&P 500 Futures Price with Buy and Sell Signals')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

def main():
    ticker = 'ES=F'
    start_date = '2020-01-01'
    end_date = '2025-02-08'
    initial_balance = 10000

    data = get_stock_data(ticker, start_date, end_date)
    data = add_features(data)
    model = train_hmm(data)
    hidden_states = predict_hmm(model, data)
    buy_signals, sell_signals = generate_signals(hidden_states)
    
    print("Buy signals:")
    for idx in buy_signals:
        print(f"Date: {data.index[idx].strftime('%m/%d/%Y')}")
    
    print("\nSell signals:")
    for idx in sell_signals:
        print(f"Date: {data.index[idx].strftime('%m/%d/%Y')}")
    
    final_balance, profit, trades = backtest(data, buy_signals, sell_signals)
    print(f"\nInitial balance: $10000.00")
    # Print the final balance formatted to 2 decimal places
    print(f"Final balance: ${final_balance:.2f}")
    print(f"Profit: ${profit:.2f}")
    
    print("\nTrade history:")
    for i in range(1, len(trades), 2):
        buy_trade = trades[i-1]
        sell_trade = trades[i]
        profit_loss = (sell_trade[2] - buy_trade[2]) * (initial_balance / buy_trade[2])
        print(f"Buy Date: {buy_trade[0].strftime('%m/%d/%Y')}, Sell Date: {sell_trade[0].strftime('%m/%d/%Y')}, Profit/Loss: ${profit_loss:.2f}")
    
    plot_signals(data, buy_signals, sell_signals)

if __name__ == "__main__":
    main()