from datetime import datetime
import os
from backend.backtesting_bot import BacktestingBot

def main():
    # Get dates from environment variables
    start_date = datetime.strptime(os.getenv('START_DATE', '2023-01-01'), '%Y-%m-%d')
    end_date = datetime.strptime(os.getenv('END_DATE', '2023-12-31'), '%Y-%m-%d')
    
    bot = BacktestingBot(start_date, end_date)
    symbol = "BTC/USDT"  # Default symbol
    
    try:
        bot.run_backtest(symbol)
        results = bot.get_results()
        print(f"Backtesting completed for {symbol}")
        print(f"Final portfolio value: {results['values'][-1] if results['values'] else 'N/A'}")
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
        raise e

if __name__ == '__main__':
    main() 