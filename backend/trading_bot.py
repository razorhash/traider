from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging
from .data_service.crypto_data_service import CryptoDataService
from .data_service.stock_data_service import StockDataService
from .strategies.market_analyzer import MarketAnalyzer
from .strategies.mean_reversion import MeanReversionStrategy
from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingBot:
    """Main trading bot class that coordinates all components"""
    
    def __init__(self):
        # Initialize services
        self.crypto_service = CryptoDataService()
        self.stock_service = StockDataService()
        self.market_analyzer = MarketAnalyzer()
        self.strategy = MeanReversionStrategy()
        
        # Initialize configurations
        self.config = Config.TRADING
        self.market_config = Config.MARKET
        self.quiet_market_config = Config.QUIET_MARKET
        self.backtest_config = Config.BACKTEST
        
        # Initialize portfolio
        self.portfolio = {
            'cash': Config.BACKTEST.INITIAL_CAPITAL,
            'positions': {}
        }
        
        self.trade_history = []
    
    def update_portfolio(
        self,
        action: str,
        symbol: str,
        price: float,
        size: float,
        timestamp: datetime
    ):
        """Update portfolio based on trade execution"""
        trade_value = price * size
        commission = trade_value * Config.BACKTEST.COMMISSION_RATE
        
        if action == 'BUY':
            self.portfolio['cash'] -= (trade_value + commission)
            self.portfolio['positions'][symbol] = {
                'size': size,
                'entry_price': price
            }
        elif action == 'SELL':
            self.portfolio['cash'] += (trade_value - commission)
            if symbol in self.portfolio['positions']:
                del self.portfolio['positions'][symbol]
        
        # Record trade
        self.trade_history.append({
            'timestamp': timestamp,
            'action': action,
            'symbol': symbol,
            'price': price,
            'size': size,
            'value': trade_value,
            'commission': commission,
            'portfolio_value': self.get_portfolio_value()
        })
    
    def get_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        total_value = self.portfolio['cash']
        
        for symbol, position in self.portfolio['positions'].items():
            try:
                current_price = self.crypto_service.get_current_price(symbol)
                position_value = position['size'] * current_price
                total_value += position_value
            except Exception as e:
                logger.error(f"Error getting price for {symbol}: {str(e)}")
        
        return total_value
    
    def run_trading_cycle(self, symbol: str):
        """Run one trading cycle for a symbol"""
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            data = self.crypto_service.get_historical_data(
                symbol,
                start_date,
                end_date
            )
            
            # Get current position for the symbol
            current_position = self.portfolio['positions'].get(symbol)
            
            # Analyze market and get trading signals
            portfolio_value = self.get_portfolio_value()
            analysis = self.strategy.analyze(
                data,
                portfolio_value,
                current_position
            )
            
            # Execute trading signals
            if analysis['action'] == 'ENTER':
                if analysis['signal'] == 'LONG':
                    self.update_portfolio(
                        'BUY',
                        symbol,
                        analysis['price'],
                        analysis['size'],
                        data.index[-1]
                    )
                    logger.info(f"Entered LONG position in {symbol}")
                elif analysis['signal'] == 'SHORT':
                    # Implement short selling logic if supported
                    pass
            
            elif analysis['action'] == 'EXIT':
                if current_position:
                    self.update_portfolio(
                        'SELL',
                        symbol,
                        analysis['price'],
                        current_position['size'],
                        data.index[-1]
                    )
                    logger.info(f"Exited position in {symbol}: {analysis['reason']}")
            
        except Exception as e:
            logger.error(f"Error in trading cycle for {symbol}: {str(e)}")
    
    def run(self):
        """Main trading loop"""
        logger.info("Starting trading bot...")
        
        while True:
            try:
                # Get tradeable symbols
                candidates = self.crypto_service.get_available_pairs()
                
                # Filter symbols based on market conditions
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                filtered_symbols = self.market_analyzer.filter_stocks(
                    candidates,
                    start_date,
                    end_date
                )
                
                # Trade filtered symbols
                for symbol in filtered_symbols:
                    self.run_trading_cycle(symbol)
                
                # Log portfolio status
                logger.info(f"Portfolio value: {self.get_portfolio_value()}")
                
            except Exception as e:
                logger.error(f"Error in main trading loop: {str(e)}")
            
            # Sleep for 1 hour before next cycle
            time.sleep(3600) 