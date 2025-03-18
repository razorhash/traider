from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

class BaseDataService(ABC):
    """Abstract base class for all data services"""
    
    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1h'
    ) -> pd.DataFrame:
        """
        Fetch historical price data for a given symbol
        
        Returns:
        pd.DataFrame with columns: [timestamp, open, high, low, close, volume]
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        pass
    
    @abstractmethod
    def get_orderbook(self, symbol: str, limit: int = 10) -> Dict:
        """Get current orderbook for a symbol"""
        pass
    
    def calculate_volatility(
        self,
        data: pd.DataFrame,
        window: int = 30
    ) -> pd.Series:
        """Calculate rolling volatility"""
        return data['close'].pct_change().rolling(window=window).std()
    
    def calculate_correlation(
        self,
        data1: pd.DataFrame,
        data2: pd.DataFrame,
        window: int = 30
    ) -> pd.Series:
        """Calculate rolling correlation between two price series"""
        returns1 = data1['close'].pct_change()
        returns2 = data2['close'].pct_change()
        return returns1.rolling(window=window).corr(returns2) 