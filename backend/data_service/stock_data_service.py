from typing import Dict, Optional
import pandas as pd
from datetime import datetime
import yfinance as yf
from .base import BaseDataService
from ..config import Config

class StockDataService(BaseDataService):
    """Data service for stock market data using Yahoo Finance"""
    
    def __init__(self):
        self.sp500 = yf.Ticker(Config.SP500_SYMBOL)
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1h'
    ) -> pd.DataFrame:
        """
        Fetch historical data for a stock symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date for historical data
            end_date: End date for historical data
            timeframe: Time interval for candlesticks
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            print(f"\nFetching historical data for {symbol}")
            print(f"Time range: {start_date} to {end_date}")
            
            # For periods longer than 730 days, use daily data
            days_difference = (end_date - start_date).days
            if days_difference > 730:
                print(f"Using daily data for {symbol} due to time range > 730 days")
                interval = '1d'
            else:
                # Convert timeframe to yfinance interval format
                interval_map = {
                    '1m': '1m',
                    '5m': '5m',
                    '15m': '15m',
                    '1h': '1h',
                    '4h': '4h',
                    '1d': '1d'
                }
                interval = interval_map.get(timeframe, '1d')  # Default to daily if invalid timeframe
            
            print(f"Using interval: {interval}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            if df.empty:
                print(f"No data available for {symbol} in the specified time range")
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            print(f"Retrieved {len(df)} data points for {symbol}")
            
            # Rename columns to match our standard format
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Convert index to timestamp column and handle timezone
            df.index = df.index.tz_localize(None)  # Remove timezone info
            df.index.name = 'timestamp'
            df = df.reset_index()
            
            # Drop unnecessary columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Ensure all required columns exist
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'volume':
                        df[col] = 0
                    else:
                        raise Exception(f"Missing required column: {col}")
            
            print(f"Successfully processed data for {symbol}")
            return df[required_columns]
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info['regularMarketPrice']
        except Exception as e:
            raise Exception(f"Error fetching current price: {str(e)}")
    
    def get_orderbook(self, symbol: str, limit: int = 10) -> Dict:
        """
        Get current orderbook for a symbol
        Note: Yahoo Finance doesn't provide orderbook data,
        so this is a placeholder that returns empty lists
        """
        return {
            'bids': [],
            'asks': []
        }
    
    def get_sp500_components(self) -> list:
        """Get list of S&P 500 components"""
        try:
            # This is a placeholder - in a real implementation,
            # you would want to fetch the actual S&P 500 components
            # from a reliable source
            return []
        except Exception as e:
            raise Exception(f"Error fetching S&P 500 components: {str(e)}")
    
    def get_market_status(self) -> str:
        """Get current market status (open/closed)"""
        try:
            return "OPEN" if self.sp500.info['regularMarketPrice'] else "CLOSED"
        except Exception as e:
            raise Exception(f"Error fetching market status: {str(e)}") 