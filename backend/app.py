from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .live_trading import LiveTrading
from datetime import datetime
from .backtesting_bot import BacktestingBot
import os
from pathlib import Path

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "http://localhost:80", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files - use absolute path
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Store bot instance
bot_instance = None

# Available trading symbols (using CCXT format)
AVAILABLE_SYMBOLS = ["BTC/USDT", "ETH/USDT", "LTC/USDT", "XRP/USDT", "ADA/USDT"]

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the index.html file"""
    index_path = static_dir / "index.html"
    with open(index_path) as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/available-symbols")
async def get_available_symbols():
    """Get available trading symbols"""
    return JSONResponse(content={"symbols": AVAILABLE_SYMBOLS})

@app.get("/backtesting-results")
async def get_backtesting_results(
    symbol: str = Query("BTC/USDT", description="Trading symbol to backtest"),
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format")
):
    """Endpoint to get backtesting results"""
    try:
        global bot_instance
        
        # Use provided dates or fall back to environment variables
        start = datetime.strptime(
            start_date or os.getenv('START_DATE', '2023-01-01'),
            '%Y-%m-%d'
        )
        end = datetime.strptime(
            end_date or os.getenv('END_DATE', '2023-12-31'),
            '%Y-%m-%d'
        )
        
        print(f"Running backtest for {symbol} from {start} to {end}")  # Debug log
        
        # Initialize and run backtest
        bot_instance = BacktestingBot(start, end)
        bot_instance.run_backtest(symbol)
        
        # Get results
        results = bot_instance.get_results()
        return JSONResponse(content=results)
    except Exception as e:
        print(f"Error in backtesting endpoint: {str(e)}")  # Add debug logging
        return JSONResponse(
            content={"error": f"Failed to get backtesting results: {str(e)}"},
            status_code=500
        )

@app.get("/trade-history")
async def get_trade_history():
    """Endpoint to get detailed trade history and summary"""
    try:
        global bot_instance
        if bot_instance is None:
            return JSONResponse(
                content={"error": "No backtest has been run yet"},
                status_code=400
            )
        
        trade_history = bot_instance.get_trade_history()
        return JSONResponse(content=trade_history)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to get trade history: {str(e)}"},
            status_code=500
        )

# Initialize live trading instances
actual_trading = LiveTrading(mode='actual')
virtual_trading = LiveTrading(mode='virtual')

@app.get("/live-trading-results/{mode}")
async def get_live_trading_results(mode: str):
    """Endpoint to get live trading results"""
    if mode == 'actual':
        return JSONResponse(content=actual_trading.get_trading_results())
    elif mode == 'virtual':
        return JSONResponse(content=virtual_trading.get_trading_results())
    else:
        return JSONResponse(content={"error": "Invalid mode"}, status_code=400) 