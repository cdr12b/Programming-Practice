import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import seaborn as sns  # Ensure seaborn is imported
from datetime import datetime, timedelta

class MarketTrendAnalyzer:
    """
    A comprehensive market trend analyzer that combines statistical analysis
    with visual representations of market trends.
    """
    
    def __init__(self, data, price_column='price', date_column='date'):
        """Initialize with market data"""
        self.df = data.copy()
        self.price_column = price_column
        self.date_column = date_column
        self.prepare_data()
        
    def prepare_data(self):
        """Prepare and clean the data for analysis"""
        self.df[self.date_column] = pd.to_datetime(self.df[self.date_column])
        self.df = self.df.sort_values(self.date_column)
        self.df.set_index(self.date_column, inplace=True)
        
    def calculate_indicators(self):
        """Calculate all technical indicators and statistics"""
        # Moving averages
        self.df['MA20'] = self.df[self.price_column].rolling(window=20).mean()
        self.df['MA50'] = self.df[self.price_column].rolling(window=50).mean()
        
        # Momentum indicators
        self.df['ROC'] = self.df[self.price_column].pct_change(periods=20) * 100
        self.df['RSI'] = self._calculate_rsi()
        
        # Volatility
        self.df['Volatility'] = self.df[self.price_column].rolling(window=20).std()
        
        return self.df
    
    def _calculate_rsi(self, periods=14):
        """Calculate Relative Strength Index"""
        delta = self.df[self.price_column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def analyze_trends(self):
        """Perform comprehensive trend analysis"""
        self.calculate_indicators()
        
        # Basic statistics
        stats_result = {
            'basic_stats': {
                'mean': self.df[self.price_column].mean(),
                'std': self.df[self.price_column].std(),
                'min': self.df[self.price_column].min(),
                'max': self.df[self.price_column].max(),
                'current_price': self.df[self.price_column].iloc[-1],
                'price_change': self.df[self.price_column].pct_change().iloc[-1] * 100
            }
        }
        
        # Linear trend analysis
        x = np.arange(len(self.df))
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            x, self.df[self.price_column].values
        )
        
        stats_result['trend_analysis'] = {
            'slope': slope,
            'r_squared': r_value**2,
            'p_value': p_value,
            'trend_direction': 'upward' if slope > 0 else 'downward'
        }
        
        # Stationarity test
        adf_result = adfuller(self.df[self.price_column].dropna())
        stats_result['stationarity'] = {
            'test_statistic': adf_result[0],
            'p_value': adf_result[1],
            'is_stationary': adf_result[1] < 0.05
        }
        
        return stats_result
    
    def plot_all_trends(self, figsize=(15, 20)):
        """Generate comprehensive visualization of all trends"""
        self.calculate_indicators()
        
        fig, axes = plt.subplots(4, 1, figsize=figsize)
        fig.suptitle('Market Trend Analysis Dashboard', fontsize=16)
        
        # 1. Price and Moving Averages
        ax1 = axes[0]
        ax1.plot(self.df.index, self.df[self.price_column], label='Price', color='blue')
        ax1.plot(self.df.index, self.df['MA20'], label='20-day MA', color='orange')
        ax1.plot(self.df.index, self.df['MA50'], label='50-day MA', color='red')
        ax1.set_title('Price and Moving Averages')
        ax1.legend()
        ax1.grid(True)
        
        # 2. RSI
        ax2 = axes[1]
        ax2.plot(self.df.index, self.df['RSI'], color='purple')
        ax2.axhline(y=70, color='r', linestyle='--')
        ax2.axhline(y=30, color='g', linestyle='--')
        ax2.set_title('Relative Strength Index (RSI)')
        ax2.grid(True)
        
        # 3. Rate of Change
        ax3 = axes[2]
        ax3.plot(self.df.index, self.df['ROC'], color='green')
        ax3.axhline(y=0, color='black', linestyle='-')
        ax3.set_title('Rate of Change (ROC)')
        ax3.grid(True)
        
        # 4. Volatility
        ax4 = axes[3]
        ax4.plot(self.df.index, self.df['Volatility'], color='red')
        ax4.set_title('Volatility (20-day Rolling Standard Deviation)')
        ax4.grid(True)
        
        plt.tight_layout()
        return fig
    
    def generate_report(self):
        """Generate a comprehensive analysis report"""
        analysis = self.analyze_trends()
        
        report = f"""
Market Trend Analysis Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. Current Market Status
-------------------------
Current Price: ${analysis['basic_stats']['current_price']:.2f}
24h Change: {analysis['basic_stats']['price_change']:.2f}%
Average Price: ${analysis['basic_stats']['mean']:.2f}
Price Range: ${analysis['basic_stats']['min']:.2f} - ${analysis['basic_stats']['max']:.2f}

2. Trend Analysis
-------------------------
Overall Trend: {analysis['trend_analysis']['trend_direction'].upper()}
Trend Strength (R²): {analysis['trend_analysis']['r_squared']:.3f}
Statistical Significance: {'High' if analysis['trend_analysis']['p_value'] < 0.05 else 'Low'}

3. Market Stability
-------------------------
Volatility (Std Dev): ${analysis['basic_stats']['std']:.2f}
Market State: {'Stationary' if analysis['stationarity']['is_stationary'] else 'Non-stationary'}
ADF Test P-value: {analysis['stationarity']['p_value']:.4f}

4. Technical Indicators (Latest Values)
-------------------------
RSI: {self.df['RSI'].iloc[-1]:.2f}
ROC (20-day): {self.df['ROC'].iloc[-1]:.2f}%
20-day MA: ${self.df['MA20'].iloc[-1]:.2f}
50-day MA: ${self.df['MA50'].iloc[-1]:.2f}

5. Market Signals
-------------------------
RSI Signal: {'Overbought' if self.df['RSI'].iloc[-1] > 70 else 'Oversold' if self.df['RSI'].iloc[-1] < 30 else 'Neutral'}
MA Signal: {'Bullish' if self.df['MA20'].iloc[-1] > self.df['MA50'].iloc[-1] else 'Bearish'}
"""
        return report

# Example usage
def demonstrate_analysis():
    # Generate sample data
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    np.random.seed(42)
    prices = np.random.normal(loc=100, scale=10, size=len(dates))
    prices = np.cumsum(prices) + 1000  # Create a random walk with drift
    
    # Create sample DataFrame
    df = pd.DataFrame({
        'date': dates,
        'price': prices
    })
    
    # Create analyzer instance
    analyzer = MarketTrendAnalyzer(df)
    
    # Generate and display analysis
    print("Generating analysis for sample market data...")
    print("\n" + "="*50 + "\n")
    
    # Print report
    print(analyzer.generate_report())
    
    # Use seaborn for styling if available
    try:
        sns.set()  # Use seaborn for styling
    except ImportError:
        plt.style.use('ggplot')  # Fallback style
    
    # Create and show plots
    fig = analyzer.plot_all_trends()
    print("Plotting trends...")  # Debugging step
    plt.show()
    print("Plots displayed.")  # Debugging step

if __name__ == "__main__":
    demonstrate_analysis()