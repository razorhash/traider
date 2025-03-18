from typing import Dict, Optional
import pandas as pd
import numpy as np
from ta.volatility import AverageTrueRange, BollingerBands
from ta.trend import ADXIndicator
from ta.momentum import RSIIndicator
from ..config import Config

class MarketConditionAnalyzer:
    """
    Implements the quiet market detection logic
    described in Chapter 2
    """
    
    def __init__(self):
        self.config = Config.QUIET_MARKET
    
    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        atr = AverageTrueRange(
            high=data['high'],
            low=data['low'],
            close=data['close'],
            window=self.config.ATR_PERIOD
        )
        return atr.average_true_range()
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        bb = BollingerBands(
            close=data['close'],
            window=self.config.BB_PERIOD,
            window_dev=self.config.BB_STD
        )
        
        return {
            'upper': bb.bollinger_hband(),
            'middle': bb.bollinger_mavg(),
            'lower': bb.bollinger_lband(),
            'width': bb.bollinger_wband()
        }
    
    def calculate_adx(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average Directional Index"""
        adx = ADXIndicator(
            high=data['high'],
            low=data['low'],
            close=data['close'],
            window=self.config.ADX_PERIOD
        )
        return adx.adx()
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Relative Strength Index"""
        rsi = RSIIndicator(
            close=data['close'],
            window=self.config.RSI_PERIOD
        )
        return rsi.rsi()
    
    def calculate_volume_ma(self, data: pd.DataFrame) -> pd.Series:
        """Calculate volume moving average"""
        return data['volume'].rolling(window=self.config.VOLUME_MA_PERIOD).mean()
    
    def is_quiet_market(self, data: pd.DataFrame) -> bool:
        """
        Determine if the market is currently quiet based on multiple indicators
        """
        # Calculate indicators
        atr = self.calculate_atr(data)
        bb = self.calculate_bollinger_bands(data)
        adx = self.calculate_adx(data)
        rsi = self.calculate_rsi(data)
        volume_ma = self.calculate_volume_ma(data)
        
        # Get current values (most recent data point)
        current_atr = atr.iloc[-1]
        current_bb_width = bb['width'].iloc[-1]
        current_adx = adx.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_volume = data['volume'].iloc[-1]
        current_volume_ma = volume_ma.iloc[-1]
        
        # Calculate ATR condition
        atr_ma = atr.rolling(window=self.config.ATR_MA_PERIOD).mean().iloc[-1]
        atr_condition = current_atr < (self.config.ATR_THRESHOLD * atr_ma)
        print(f"ATR Condition: {atr_condition} (Current: {current_atr:.2f}, Threshold: {self.config.ATR_THRESHOLD * atr_ma:.2f})")
        
        # Calculate BB condition
        bb_width_ma = bb['width'].rolling(window=self.config.BB_WIDTH_MA_PERIOD).mean().iloc[-1]
        bb_condition = current_bb_width < (self.config.BB_WIDTH_THRESHOLD * bb_width_ma)
        print(f"BB Width Condition: {bb_condition} (Current: {current_bb_width:.2f}, Threshold: {self.config.BB_WIDTH_THRESHOLD * bb_width_ma:.2f})")
        
        # Check ADX condition
        adx_condition = current_adx < self.config.ADX_THRESHOLD
        print(f"ADX Condition: {adx_condition} (Current: {current_adx:.2f}, Threshold: {self.config.ADX_THRESHOLD})")
        
        # Check RSI condition
        rsi_condition = (
            self.config.RSI_LOWER <= 
            current_rsi <= 
            self.config.RSI_UPPER
        )
        print(f"RSI Condition: {rsi_condition} (Current: {current_rsi:.2f}, Range: {self.config.RSI_LOWER}-{self.config.RSI_UPPER})")
        
        # Check volume condition
        volume_condition = current_volume < (self.config.VOLUME_THRESHOLD * current_volume_ma)
        print(f"Volume Condition: {volume_condition} (Current: {current_volume:.2f}, Threshold: {self.config.VOLUME_THRESHOLD * current_volume_ma:.2f})")
        
        # Market is considered quiet if required number of conditions are met
        conditions = [
            atr_condition,
            bb_condition,
            adx_condition,
            rsi_condition,
            volume_condition
        ]
        conditions_met = sum(conditions) >= self.config.MIN_CONDITIONS_MET
        
        print(f"At least {self.config.MIN_CONDITIONS_MET} conditions met: {conditions_met}")
        return conditions_met
    
    def get_support_resistance(
        self,
        data: pd.DataFrame,
        lookback_periods: int = 20
    ) -> Dict[str, float]:
        """
        Calculate support and resistance levels
        
        Args:
            data: DataFrame with OHLCV data
            lookback_periods: Number of periods to look back
            
        Returns:
            Dict with support and resistance levels
        """
        recent_data = data.tail(lookback_periods)
        
        support = recent_data['low'].min()
        resistance = recent_data['high'].max()
        
        bb = self.calculate_bollinger_bands(data)
        
        return {
            'support': support,
            'resistance': resistance,
            'bb_lower': bb['lower'].iloc[-1],
            'bb_middle': bb['middle'].iloc[-1],
            'bb_upper': bb['upper'].iloc[-1]
        }
    
    def analyze_market_condition(
        self,
        data: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Comprehensive market condition analysis
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dict with market condition analysis
        """
        is_quiet = self.is_quiet_market(data)
        
        if not is_quiet:
            return {'is_quiet': False}
        
        # If market is quiet, calculate additional metrics
        support_resistance = self.get_support_resistance(data)
        rsi = self.calculate_rsi(data).iloc[-1]
        
        return {
            'is_quiet': True,
            'support_resistance': support_resistance,
            'current_rsi': rsi,
            'current_price': data['close'].iloc[-1]
        } 