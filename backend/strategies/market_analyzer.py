from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..data_service.crypto_data_service import CryptoDataService
from ..data_service.stock_data_service import StockDataService
from ..config import Config

class MarketAnalyzer:
    """
    Implements the volatility-based stock filtering approach
    described in Chapter 1
    """
    
    def __init__(self):
        self.crypto_service = CryptoDataService()
        self.stock_service = StockDataService()
        self.config = Config.MARKET
    
    def get_market_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get historical data for both S&P 500 and Bitcoin
        
        Returns:
            Tuple of (sp500_data, btc_data)
        """
        sp500_data = self.stock_service.get_historical_data(
            Config.SP500_SYMBOL,
            start_date,
            end_date
        )
        
        btc_data = self.crypto_service.get_historical_data(
            'BTC/USDT',
            start_date,
            end_date
        )
        
        return sp500_data, btc_data
    
    def compute_market_volatility(
        self,
        sp500_data: pd.DataFrame,
        btc_data: pd.DataFrame
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Compute rolling volatility for S&P 500 and Bitcoin
        """
        sp500_vol = self.stock_service.calculate_volatility(
            sp500_data,
            window=self.config.VOLATILITY_WINDOW
        )
        
        btc_vol = self.crypto_service.calculate_volatility(
            btc_data,
            window=self.config.VOLATILITY_WINDOW
        )
        
        return sp500_vol, btc_vol
    
    def compute_correlation(
        self,
        sp500_data: pd.DataFrame,
        btc_data: pd.DataFrame
    ) -> float:
        """
        Compute correlation between S&P 500 and Bitcoin
        """
        correlation = self.stock_service.calculate_correlation(
            sp500_data,
            btc_data,
            window=self.config.CORRELATION_WINDOW
        )
        
        # Return the most recent correlation value
        return correlation.iloc[-1]
    
    def get_market_weights(self, correlation: float) -> Tuple[float, float]:
        """
        Determine market weights based on correlation
        
        Returns:
            Tuple of (sp500_weight, btc_weight)
        """
        if correlation > self.config.HIGH_CORRELATION_THRESHOLD:
            # High correlation: 50-50 split
            return 0.5, 0.5
        else:
            # Low correlation: More weight to Bitcoin
            btc_weight = self.config.BTC_WEIGHT_LOW_CORR
            return 1 - btc_weight, btc_weight
    
    def compute_weighted_market_volatility(
        self,
        sp500_vol: pd.Series,
        btc_vol: pd.Series,
        weights: Tuple[float, float]
    ) -> pd.Series:
        """
        Compute weighted market volatility
        """
        sp500_weight, btc_weight = weights
        return sp500_weight * sp500_vol + btc_weight * btc_vol
    
    def compute_volatility_ratio(
        self,
        stock_data: pd.DataFrame,
        market_vol: pd.Series
    ) -> float:
        """
        Compute stock-to-market volatility ratio
        """
        stock_vol = self.stock_service.calculate_volatility(
            stock_data,
            window=self.config.VOLATILITY_WINDOW
        )
        
        # Return the most recent volatility ratio
        return (stock_vol / market_vol).iloc[-1]
    
    def filter_stocks(
        self,
        candidates: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """
        Filter stocks based on volatility ratio
        
        Args:
            candidates: List of stock symbols to analyze
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of filtered stock symbols
        """
        # Get market data
        sp500_data, btc_data = self.get_market_data(start_date, end_date)
        
        # Compute market volatilities
        sp500_vol, btc_vol = self.compute_market_volatility(sp500_data, btc_data)
        
        # Compute correlation and weights
        correlation = self.compute_correlation(sp500_data, btc_data)
        weights = self.get_market_weights(correlation)
        
        # Compute weighted market volatility
        market_vol = self.compute_weighted_market_volatility(
            sp500_vol,
            btc_vol,
            weights
        )
        
        filtered_stocks = []
        volumes = {}
        
        # Filter stocks based on volatility ratio
        for symbol in candidates:
            try:
                stock_data = self.stock_service.get_historical_data(
                    symbol,
                    start_date,
                    end_date
                )
                
                v_ratio = self.compute_volatility_ratio(stock_data, market_vol)
                
                if (self.config.VOLATILITY_RATIO_MIN <= v_ratio <= 
                    self.config.VOLATILITY_RATIO_MAX):
                    filtered_stocks.append(symbol)
                    # Store average 30-day volume
                    volumes[symbol] = stock_data['volume'].tail(30).mean()
                    
            except Exception as e:
                print(f"Error analyzing {symbol}: {str(e)}")
                continue
        
        # If more than 5 stocks passed the filter, select top 5 by volume
        if len(filtered_stocks) > 5:
            filtered_stocks = sorted(
                filtered_stocks,
                key=lambda x: volumes[x],
                reverse=True
            )[:5]
        
        return filtered_stocks 