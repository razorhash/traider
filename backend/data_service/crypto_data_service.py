from typing import Dict, Optional
import pandas as pd
from datetime import datetime
import ccxt
from .base import BaseDataService
from ..config import Config
import time

class CryptoDataService(BaseDataService):
    """Data service for cryptocurrency data using CCXT"""
    
    def __init__(self, exchange_id: str = Config.CRYPTO_EXCHANGE):
        self.exchange_id = exchange_id
        self.exchange_class = getattr(ccxt, exchange_id)
        self.exchange = self.exchange_class({
            'enableRateLimit': True,
        })
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1h'
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a given symbol and timeframe
        """
        try:
            print(f"Fetching data for {symbol} from {start_date} to {end_date}")
            
            # Convert dates to timestamps in milliseconds
            since = int(start_date.timestamp() * 1000)
            until = int(end_date.timestamp() * 1000)
            
            all_ohlcv = []
            current_since = since
            
            # Fetch data in chunks until we reach the end date
            while current_since < until:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    since=current_since,
                    limit=1000  # Maximum number of candles per request
                )
                
                if not ohlcv:
                    break
                    
                all_ohlcv.extend(ohlcv)
                
                # Update the since timestamp for the next iteration
                current_since = ohlcv[-1][0] + 1
                
                # Add a small delay to avoid rate limits
                time.sleep(self.exchange.rateLimit / 1000)
            
            if not all_ohlcv:
                raise Exception(f"No data available for {symbol} in the specified time range")
            
            # Convert to DataFrame
            df = pd.DataFrame(
                all_ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp from milliseconds to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Sort by timestamp and remove duplicates
            df = df.sort_values('timestamp')
            df = df.drop_duplicates(subset=['timestamp'])
            
            # Filter to the exact date range
            df = df[
                (df['timestamp'] >= pd.to_datetime(start_date)) & 
                (df['timestamp'] <= pd.to_datetime(end_date))
            ]
            
            if len(df) < 2:
                raise Exception(f"Not enough data points for {symbol} in the specified time range")
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            raise Exception(f"Error fetching current price: {str(e)}")
    
    def get_orderbook(self, symbol: str, limit: int = 10) -> Dict:
        """Get current orderbook for a symbol"""
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return {
                'bids': orderbook['bids'][:limit],
                'asks': orderbook['asks'][:limit]
            }
        except Exception as e:
            raise Exception(f"Error fetching orderbook: {str(e)}")
    
    def get_available_pairs(self) -> list:
        """Get list of available trading pairs"""
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            raise Exception(f"Error fetching available pairs: {str(e)}")
    
    def get_exchange_info(self) -> Dict:
        """Get exchange information including trading limits and precision"""
        try:
            return self.exchange.load_markets()
        except Exception as e:
            raise Exception(f"Error fetching exchange info: {str(e)}") 