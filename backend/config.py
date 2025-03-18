from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class MarketConfig:
    # Volatility thresholds
    VOLATILITY_RATIO_MIN: float = 0.6
    VOLATILITY_RATIO_MAX: float = 1.5
    
    # Correlation weights
    HIGH_CORRELATION_THRESHOLD: float = 0.5
    BTC_WEIGHT_HIGH_CORR: float = 0.5
    BTC_WEIGHT_LOW_CORR: float = 0.7
    
    # Rolling windows
    VOLATILITY_WINDOW: int = 30
    CORRELATION_WINDOW: int = 30
    VOLUME_MA_WINDOW: int = 50

@dataclass
class QuietMarketConfig:
    # ATR settings
    ATR_PERIOD: int = 14
    ATR_THRESHOLD: float = 1.2  # ATR must be below this * ATR MA
    ATR_MA_PERIOD: int = 20
    
    # Bollinger Bands settings
    BB_PERIOD: int = 20
    BB_STD: float = 2.0
    BB_WIDTH_THRESHOLD: float = 1.0  # BB width must be below this * BB width MA
    BB_WIDTH_MA_PERIOD: int = 20
    
    # ADX settings
    ADX_PERIOD: int = 14
    ADX_THRESHOLD: float = 30  # ADX must be below this value
    
    # RSI settings
    RSI_PERIOD: int = 14
    RSI_LOWER: float = 35  # RSI must be between these values
    RSI_UPPER: float = 65
    
    # Volume settings
    VOLUME_MA_PERIOD: int = 50
    VOLUME_THRESHOLD: float = 1.5  # Volume must be below this * Volume MA
    
    # Condition requirements
    MIN_CONDITIONS_MET: int = 3  # Number of conditions that must be met out of 5

@dataclass
class TradingConfig:
    # Entry conditions
    RSI_OVERSOLD: float = 35
    RSI_OVERBOUGHT: float = 65
    VOLUME_INCREASE_THRESHOLD: float = 1.05
    
    # Exit conditions
    STOP_LOSS_ATR_MULTIPLIER: float = 2.0
    PROFIT_TARGET_ATR_MULTIPLIER: float = 1.5
    
    # Position sizing
    MAX_POSITION_SIZE: float = 0.1
    RISK_PER_TRADE: float = 0.01
    
    # Risk management
    MAX_DRAWDOWN: float = 0.2
    SLIPPAGE: float = 0.001

@dataclass
class BacktestConfig:
    START_DATE: Optional[datetime] = None
    END_DATE: Optional[datetime] = None
    INITIAL_CAPITAL: float = 100000
    COMMISSION_RATE: float = 0.001
    SP500_SYMBOL: str = "^GSPC"  # S&P 500 Index
    RISK_PER_TRADE: float = 0.01  # Risk 1% per trade
    MAX_POSITION_SIZE: float = 0.1  # Maximum 10% of portfolio per position
    SLIPPAGE: float = 0.001  # 0.1% slippage per trade

class Config:
    # API Keys for Coinbase (load from environment variables)
    COINBASE_LIVE_API_KEY: str = os.getenv('COINBASE_LIVE_API_KEY', '')
    COINBASE_LIVE_API_SECRET: str = os.getenv('COINBASE_LIVE_API_SECRET', '')
    COINBASE_LIVE_PASSPHRASE: str = ''  # No longer used
    
    COINBASE_SANDBOX_API_KEY: str = os.getenv('COINBASE_SANDBOX_API_KEY', '')
    COINBASE_SANDBOX_API_SECRET: str = os.getenv('COINBASE_SANDBOX_API_SECRET', '')
    COINBASE_SANDBOX_PASSPHRASE: str = os.getenv('COINBASE_SANDBOX_PASSPHRASE', '')
    
    # Determine if using sandbox or live
    if os.getenv('TRADING_ENV') == 'live':
        COINBASE_API_KEY = COINBASE_LIVE_API_KEY
        COINBASE_API_SECRET = COINBASE_LIVE_API_SECRET
        COINBASE_API_URL = 'https://api.pro.coinbase.com'
    else:
        COINBASE_API_KEY = COINBASE_SANDBOX_API_KEY
        COINBASE_API_SECRET = COINBASE_SANDBOX_API_SECRET
        COINBASE_PASSPHRASE = COINBASE_SANDBOX_PASSPHRASE
        COINBASE_API_URL = 'https://api-public.sandbox.pro.coinbase.com'
    
    # Market data settings
    CRYPTO_EXCHANGE: str = 'coinbase'
    CRYPTO_SYMBOLS: List[str] = ['BTC/USDT', 'ETH/USDT']
    SP500_SYMBOL: str = '^GSPC'
    
    # Trading pairs
    TRADING_PAIRS: List[str] = ['BTC/USDT', 'ETH/USDT']
    
    # Timeframes
    DEFAULT_TIMEFRAME: str = '1d'
    AVAILABLE_TIMEFRAMES: List[str] = ['1m', '5m', '15m', '1h', '4h', '1d']
    
    # Component configurations
    MARKET = MarketConfig()
    QUIET_MARKET = QuietMarketConfig()
    TRADING = TradingConfig()
    BACKTEST = BacktestConfig()
    
    # Database settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate the configuration settings"""
        if not cls.COINBASE_API_KEY or not cls.COINBASE_API_SECRET:
            raise ValueError("API keys not configured")
        return True 