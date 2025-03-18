from typing import Optional
import pandas as pd
from datetime import datetime, timedelta
from backend.trading_bot import TradingBot
from backend.config import Config
import matplotlib.pyplot as plt
import os

class BacktestingBot(TradingBot):
    """Backtesting bot class for simulating trades using historical data"""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.portfolio['cash'] = Config.BACKTEST.INITIAL_CAPITAL
        self.trade_history = []
        self.daily_results = {
            'dates': [],
            'values': [],
            'btc_prices': [],  # Add BTC price tracking
            'sp500_prices': [],  # Add S&P 500 price tracking
            'btc_normalized': [],  # Add normalized values for comparison
            'sp500_normalized': [],  # Add normalized values for comparison
            'portfolio_normalized': []  # Add normalized portfolio values
        }
        self.trades = []  # List to store detailed trade information
        self.current_trade = None  # To track open positions
        self.config = Config.BACKTEST  # Add config initialization
    
    def select_stocks(self, available_stocks: list) -> list:
        """Prompt user to select stocks from available options"""
        print("Available stocks:")
        for i, stock in enumerate(available_stocks):
            print(f"{i + 1}: {stock}")
        selected_indices = input("Enter the numbers of the stocks you want to trade, separated by commas: ")
        selected_indices = [int(i) - 1 for i in selected_indices.split(',')]
        return [available_stocks[i] for i in selected_indices]

    def record_trade(self, action: str, symbol: str, price: float, size: float, date: datetime):
        """Record trade details"""
        if action == 'BUY':
            self.current_trade = {
                'entry_date': date.strftime('%Y-%m-%d'),
                'entry_price': price,
                'size': size,
                'symbol': symbol,
                'type': 'LONG'  # Add trade type
            }
        elif action == 'SELL' and self.current_trade:
            profit_loss = (price - self.current_trade['entry_price']) * self.current_trade['size']
            profit_loss_percentage = ((price / self.current_trade['entry_price']) - 1) * 100
            
            trade_details = {
                **self.current_trade,
                'exit_date': date.strftime('%Y-%m-%d'),
                'exit_price': price,
                'profit_loss': round(profit_loss, 2),
                'profit_loss_percentage': round(profit_loss_percentage, 2)
            }
            self.trades.append(trade_details)
            self.current_trade = None

    def get_trade_history(self):
        """Get detailed trade history"""
        return {
            'trades': self.trades,
            'summary': self.get_trading_summary()
        }

    def get_trading_summary(self):
        """Calculate and return trading summary statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'profitable_trades': 0,
                'total_profit_loss': 0,
                'win_rate': 0,
                'average_profit_loss': 0,
                'largest_gain': 0,
                'largest_loss': 0
            }

        profitable_trades = len([t for t in self.trades if t['profit_loss'] > 0])
        total_profit_loss = sum(t['profit_loss'] for t in self.trades)
        profits = [t['profit_loss'] for t in self.trades if t['profit_loss'] > 0]
        losses = [t['profit_loss'] for t in self.trades if t['profit_loss'] < 0]

        return {
            'total_trades': len(self.trades),
            'profitable_trades': profitable_trades,
            'total_profit_loss': round(total_profit_loss, 2),
            'win_rate': round((profitable_trades / len(self.trades)) * 100, 2),
            'average_profit_loss': round(total_profit_loss / len(self.trades), 2),
            'largest_gain': round(max(profits) if profits else 0, 2),
            'largest_loss': round(min(losses) if losses else 0, 2)
        }

    def record_daily_value(self, date, portfolio_value, btc_price=None, sp500_price=None):
        """Record daily portfolio value and comparison data"""
        # Add date and portfolio value
        self.daily_results['dates'].append(date.strftime('%Y-%m-%d'))
        self.daily_results['values'].append(portfolio_value)
        
        # Record BTC price if available
        if btc_price is not None:
            self.daily_results['btc_prices'].append(btc_price)
            # Calculate normalized BTC value
            if len(self.daily_results['btc_prices']) == 1:
                self.daily_results['btc_normalized'].append(100)  # Base value
            else:
                initial_btc = self.daily_results['btc_prices'][0]
                normalized_btc = (btc_price / initial_btc) * 100
                self.daily_results['btc_normalized'].append(normalized_btc)
        
        # Record S&P 500 price if available
        if sp500_price is not None:
            self.daily_results['sp500_prices'].append(sp500_price)
            # Calculate normalized S&P 500 value
            if len(self.daily_results['sp500_prices']) == 1:
                self.daily_results['sp500_normalized'].append(100)  # Base value
            else:
                initial_sp500 = self.daily_results['sp500_prices'][0]
                normalized_sp500 = (sp500_price / initial_sp500) * 100
                self.daily_results['sp500_normalized'].append(normalized_sp500)
        
        # Calculate normalized portfolio value
        if len(self.daily_results['values']) == 1:
            self.daily_results['portfolio_normalized'].append(100)  # Base value
        else:
            initial_portfolio = self.daily_results['values'][0]
            normalized_portfolio = (portfolio_value / initial_portfolio) * 100
            self.daily_results['portfolio_normalized'].append(normalized_portfolio)
        
        # Print progress update every 30 days
        if len(self.daily_results['dates']) % 30 == 0:
            print(f"\nProgress update ({date.strftime('%Y-%m-%d')}):")
            print(f"Portfolio Value: ${portfolio_value:,.2f}")
            if btc_price is not None:
                btc_return = (self.daily_results['btc_normalized'][-1] - 100)
                print(f"BTC Return: {btc_return:,.2f}%")
            if sp500_price is not None:
                sp500_return = (self.daily_results['sp500_normalized'][-1] - 100)
                print(f"S&P 500 Return: {sp500_return:,.2f}%")
            portfolio_return = (self.daily_results['portfolio_normalized'][-1] - 100)
            print(f"Strategy Return: {portfolio_return:,.2f}%")

    def get_results(self):
        """Get the backtesting results in the format expected by the API"""
        return self.daily_results

    def get_portfolio_value(self, current_data: pd.DataFrame = None) -> float:
        """Calculate total portfolio value including cash and positions"""
        total_value = self.portfolio['cash']
        
        if current_data is not None and len(current_data) > 0:
            current_price = current_data['close'].iloc[-1]
            
            for symbol, position in self.portfolio['positions'].items():
                try:
                    position_value = position['size'] * current_price
                    total_value += position_value
                except Exception as e:
                    print(f"Error calculating position value for {symbol}: {str(e)}")
        
        return round(total_value, 2)

    def calculate_position_size(self, portfolio_value: float, entry_price: float, risk_amount: float) -> float:
        """
        Calculate position size based on risk management rules
        
        Args:
            portfolio_value: Current portfolio value
            entry_price: Entry price for the trade
            risk_amount: Amount willing to risk on this trade (in quote currency)
            
        Returns:
            Position size in base currency
        """
        # Risk per trade (1% of portfolio)
        max_risk = portfolio_value * self.config.RISK_PER_TRADE
        risk_amount = min(risk_amount, max_risk)
        
        # Calculate base currency amount
        position_size = risk_amount / entry_price
        
        # Limit position size to max allowed (10% of portfolio)
        max_position_value = portfolio_value * self.config.MAX_POSITION_SIZE
        max_position_size = max_position_value / entry_price
        
        return min(position_size, max_position_size)

    def update_portfolio(self, action: str, symbol: str, price: float, size: float, date: datetime, target: float = None, stop_loss: float = None):
        """Update portfolio with trade and record it"""
        try:
            if action == 'BUY':
                # Calculate trade cost including slippage
                slippage = price * self.config.SLIPPAGE
                actual_price = price + slippage
                trade_cost = actual_price * size
                
                # Check if we have enough cash
                if trade_cost > self.portfolio['cash']:
                    print(f"Not enough cash for trade: {trade_cost} > {self.portfolio['cash']}")
                    return
                
                # Update portfolio positions
                self.portfolio['positions'][symbol] = {
                    'size': size,
                    'entry_price': actual_price,
                    'type': 'LONG',
                    'target': target,
                    'stop_loss': stop_loss
                }
                self.portfolio['cash'] -= trade_cost
                print(f"Opened LONG position: {size} {symbol} at {actual_price} (slippage: {slippage})")
                
            elif action == 'SELL':
                if symbol not in self.portfolio['positions']:
                    print(f"No position found for {symbol}")
                    return
                    
                position = self.portfolio['positions'].pop(symbol)
                
                # Calculate actual sale price with slippage
                slippage = price * self.config.SLIPPAGE
                actual_price = price - slippage
                trade_value = actual_price * position['size']
                
                self.portfolio['cash'] += trade_value
                print(f"Closed position: {position['size']} {symbol} at {actual_price} (slippage: {slippage})")
            
            # Record the trade
            self.record_trade(action, symbol, price, size, date)
            
        except Exception as e:
            print(f"Error updating portfolio: {str(e)}")

    def run_backtest(self, symbol: str):
        """Run backtest for a given symbol"""
        try:
            print("Starting backtest...")
            
            # Get historical data for crypto
            data = self.crypto_service.get_historical_data(
                symbol,
                self.start_date,
                self.end_date
            )
            
            if data.empty:
                raise Exception(f"No data available for {symbol}")
            
            # Get BTC/USDT data if we're not already trading it
            btc_data = None
            if symbol != 'BTC/USDT':
                btc_data = self.crypto_service.get_historical_data(
                    'BTC/USDT',
                    self.start_date,
                    self.end_date
                )
            else:
                btc_data = data.copy()
            
            # Get S&P 500 data (force daily timeframe)
            print("Fetching S&P 500 data...")
            sp500_data = self.stock_service.get_historical_data(
                self.config.SP500_SYMBOL,
                self.start_date,
                self.end_date,
                timeframe='1d'  # Force daily timeframe
            )
            
            if sp500_data.empty:
                print("Warning: No S&P 500 data available, will proceed without benchmark comparison")
            else:
                print(f"Successfully loaded S&P 500 data with {len(sp500_data)} data points")
            
            if len(data) < 2:
                raise Exception(f"Not enough data points for {symbol}")
            
            # Set timestamp as index and ensure it's datetime
            if 'timestamp' in data.columns:
                data.set_index('timestamp', inplace=True)
                data.index = pd.to_datetime(data.index)
            else:
                raise Exception(f"Missing timestamp column in data for {symbol}")
            
            # Process BTC data
            if btc_data is not None and not btc_data.empty:
                if 'timestamp' in btc_data.columns:
                    btc_data.set_index('timestamp', inplace=True)
                    btc_data.index = pd.to_datetime(btc_data.index)
                    btc_data = btc_data.resample('D').last()
                    btc_data = btc_data.ffill()
            
            # Process S&P 500 data
            if sp500_data is not None and not sp500_data.empty:
                if 'timestamp' in sp500_data.columns:
                    sp500_data.set_index('timestamp', inplace=True)
                    sp500_data.index = pd.to_datetime(sp500_data.index)
                    sp500_data = sp500_data.resample('D').last()
                    sp500_data = sp500_data.ffill()
                    print(f"Successfully processed S&P 500 data with {len(sp500_data)} data points")
            
            # Ensure data is resampled to daily frequency and handle missing values
            data = data.resample('D').last()
            data = data.ffill()  # Forward fill missing values
            
            if len(data) < 2:
                raise Exception(f"Not enough daily data points for {symbol}")
            
            print("Data processing completed, starting backtest execution...")
            
            # Initialize portfolio tracking with initial capital
            initial_btc = btc_data['close'].iloc[0] if btc_data is not None and not btc_data.empty else None
            initial_sp500 = sp500_data['close'].iloc[0] if sp500_data is not None and not sp500_data.empty else None
            
            print(f"Initial values - Portfolio: ${self.portfolio['cash']}, BTC: ${initial_btc}, S&P 500: ${initial_sp500}")
            
            self.record_daily_value(
                data.index[0],
                self.portfolio['cash'],
                initial_btc,
                initial_sp500
            )
            
            # Run backtest day by day
            for current_date in data.index:
                try:
                    # Get current slice of data
                    current_data = data.loc[:current_date].copy()
                    current_price = current_data['close'].iloc[-1]
                    
                    # Get BTC price for the current date
                    btc_price = None
                    if btc_data is not None and not btc_data.empty and current_date in btc_data.index:
                        btc_price = btc_data.loc[current_date]['close']
                    
                    # Get S&P 500 price for the current date
                    sp500_price = None
                    if sp500_data is not None and not sp500_data.empty and current_date in sp500_data.index:
                        sp500_price = sp500_data.loc[current_date]['close']
                    
                    # Get current position and analyze market
                    current_position = self.portfolio['positions'].get(symbol)
                    portfolio_value = self.get_portfolio_value(current_data)
                    
                    # Get trading signal
                    signal = self.strategy.analyze(
                        current_data,
                        portfolio_value,
                        current_position
                    )
                    
                    # Execute trades based on signal
                    if signal and 'action' in signal:
                        if signal['action'] == 'ENTER' and not current_position:
                            # Calculate position size and execute trade
                            size = signal.get('size', 0)
                            if size > 0:
                                self.update_portfolio(
                                    'BUY',
                                    symbol,
                                    current_price,
                                    size,
                                    current_date,
                                    signal.get('target'),
                                    signal.get('stop_loss')
                                )
                                print(f"Entered LONG position: {size} {symbol} at {current_price}")
                        
                        elif signal['action'] == 'EXIT' and current_position:
                            # Close position
                            self.update_portfolio(
                                'SELL',
                                symbol,
                                current_price,
                                current_position['size'],
                                current_date
                            )
                            print(f"Exited position: {current_position['size']} {symbol} at {current_price}")
                    
                    # Record daily portfolio value and comparison data
                    self.record_daily_value(
                        current_date,
                        portfolio_value,
                        btc_price,
                        sp500_price
                    )
                    
                except Exception as e:
                    print(f"Error processing date {current_date}: {str(e)}")
                    continue
            
            print("\nBacktest completed successfully")
            print(f"Final portfolio value: {self.portfolio['cash']:,.2f}")
            
            # Print performance comparison
            initial_value = self.daily_results['values'][0]
            final_value = self.daily_results['values'][-1]
            portfolio_return = ((final_value / initial_value) - 1) * 100
            
            btc_return = None
            if len(self.daily_results['btc_normalized']) > 0:
                btc_return = self.daily_results['btc_normalized'][-1] - 100
            
            sp500_return = None
            if len(self.daily_results['sp500_normalized']) > 0:
                sp500_return = self.daily_results['sp500_normalized'][-1] - 100
            
            print("\nPerformance Summary:")
            print(f"Strategy Return: {portfolio_return:,.2f}%")
            if btc_return is not None:
                print(f"BTC Return: {btc_return:,.2f}%")
            if sp500_return is not None:
                print(f"S&P 500 Return: {sp500_return:,.2f}%")
            
        except Exception as e:
            print(f"Error in backtest: {str(e)}")
            # Return empty results on error
            self.daily_results = {
                'dates': [],
                'values': [],
                'btc_prices': [],
                'sp500_prices': [],
                'btc_normalized': [],
                'sp500_normalized': [],
                'portfolio_normalized': []
            }
            raise 