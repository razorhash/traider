from typing import Dict, Optional, Tuple
import pandas as pd
from datetime import datetime
from .market_condition import MarketConditionAnalyzer
from ..config import Config

class MeanReversionStrategy:
    """
    Implements the mean reversion trading strategy
    described in Chapter 3
    """
    
    def __init__(self):
        self.market_analyzer = MarketConditionAnalyzer()
        self.config = Config.TRADING
    
    def check_entry_conditions(
        self,
        data: pd.DataFrame,
        market_condition: Dict
    ) -> Optional[Dict]:
        """
        Check if entry conditions are met
        
        Args:
            data: DataFrame with OHLCV data
            market_condition: Dict with market condition analysis
            
        Returns:
            Dict with entry signal if conditions are met, None otherwise
        """
        if not market_condition['is_quiet']:
            print("Market not quiet enough for entry")
            return None
        
        current_price = market_condition['current_price']
        current_rsi = market_condition['current_rsi']
        support_resistance = market_condition['support_resistance']
        
        # Check volume condition
        volume = data['volume'].iloc[-1]
        volume_ma = self.market_analyzer.calculate_volume_ma(data).iloc[-1]
        volume_increase = volume / volume_ma > self.config.VOLUME_INCREASE_THRESHOLD
        
        print(f"""
Entry conditions check:
Current price: {current_price}
Current RSI: {current_rsi}
BB Lower: {support_resistance['bb_lower']}
BB Upper: {support_resistance['bb_upper']}
Support: {support_resistance['support']}
Resistance: {support_resistance['resistance']}
Volume increase: {volume_increase}
""")
        
        # Long entry conditions - more lenient
        long_conditions = [
            current_price <= support_resistance['bb_lower'] * 1.05,  # Allow price further above BB lower
            current_rsi < self.config.RSI_OVERSOLD * 1.2,  # Allow RSI further above oversold
            current_price <= support_resistance['support'] * 1.1,  # Within 10% of support
            volume_increase
        ]
        
        # Short entry conditions - more lenient
        short_conditions = [
            current_price >= support_resistance['bb_upper'] * 0.95,  # Allow price further below BB upper
            current_rsi > self.config.RSI_OVERBOUGHT * 0.8,  # Allow RSI further below overbought
            current_price >= support_resistance['resistance'] * 0.9,  # Within 10% of resistance
            volume_increase
        ]
        
        # Only require 2 out of 4 conditions for entry
        if sum(long_conditions) >= 2:
            print("Long entry conditions met")
            return {
                'signal': 'LONG',
                'price': current_price,
                'target': support_resistance['bb_middle'],
                'stop_loss': current_price * (1 - self.calculate_stop_loss(data))
            }
        
        if sum(short_conditions) >= 2:
            print("Short entry conditions met")
            return {
                'signal': 'SHORT',
                'price': current_price,
                'target': support_resistance['bb_middle'],
                'stop_loss': current_price * (1 + self.calculate_stop_loss(data))
            }
        
        print("No entry conditions met")
        return None
    
    def calculate_stop_loss(self, data: pd.DataFrame) -> float:
        """
        Calculate ATR-based stop loss percentage
        """
        atr = self.market_analyzer.calculate_atr(data).iloc[-1]
        current_price = data['close'].iloc[-1]
        return (atr * self.config.STOP_LOSS_ATR_MULTIPLIER) / current_price
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Calculate position size based on risk management rules
        
        Args:
            portfolio_value: Current portfolio value
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            
        Returns:
            Position size in base currency
        """
        # Risk per trade (1% of portfolio)
        risk_amount = portfolio_value * 0.01
        
        # Calculate position size based on stop loss
        risk_per_unit = abs(entry_price - stop_loss)
        position_size = risk_amount / risk_per_unit
        
        # Limit position size to max allowed
        max_position = portfolio_value * self.config.MAX_POSITION_SIZE
        return min(position_size, max_position)
    
    def check_exit_conditions(
        self,
        position: Dict,
        current_price: float,
        current_rsi: float
    ) -> Optional[str]:
        """
        Check if exit conditions are met
        """
        if position['type'] == 'LONG':
            # Exit long position conditions
            if current_price <= position['stop_loss']:
                return 'STOP_LOSS'
            elif current_price >= position['target']:
                return 'TARGET'
            
        elif position['type'] == 'SHORT':
            # Exit short position conditions
            if current_price >= position['stop_loss']:
                return 'STOP_LOSS'
            elif current_price <= position['target']:
                return 'TARGET'
        
        return None
    
    def analyze(
        self,
        data: pd.DataFrame,
        portfolio_value: float,
        current_position: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze current market conditions and generate trading signals
        """
        try:
            if data.empty:
                return {'action': 'HOLD', 'price': 0}

            current_price = data['close'].iloc[-1]
            default_response = {'action': 'HOLD', 'price': current_price}

            # Check exit conditions first if we have an open position
            if current_position:
                # Get current RSI for exit conditions
                current_rsi = self.market_analyzer.calculate_rsi(data).iloc[-1]
                exit_signal = self.check_exit_conditions(
                    current_position,
                    current_price,
                    current_rsi
                )
                if exit_signal:
                    return {
                        'action': 'EXIT',
                        'signal': current_position['type'],
                        'price': current_price,
                        'reason': exit_signal
                    }

            # Check entry conditions if no position is open
            if not current_position:
                # Get market conditions
                market_condition = self.market_analyzer.analyze_market_condition(data)
                
                # Check entry conditions
                entry_signal = self.check_entry_conditions(data, market_condition)
                if entry_signal:
                    # Calculate position size based on risk management
                    position_size = self.calculate_position_size(
                        portfolio_value,
                        entry_signal['price'],
                        entry_signal['stop_loss']
                    )
                    
                    return {
                        'action': 'ENTER',
                        'signal': entry_signal['signal'],
                        'price': entry_signal['price'],
                        'size': position_size,
                        'target': entry_signal['target'],
                        'stop_loss': entry_signal['stop_loss'],
                        'reason': 'Mean reversion entry conditions met'
                    }

            return default_response

        except Exception as e:
            print(f"Error in strategy analysis: {str(e)}")
            return {'action': 'HOLD', 'price': data['close'].iloc[-1] if not data.empty else 0} 