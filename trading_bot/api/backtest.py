"""
API endpoints for backtesting
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime
from trading_bot.strategy.backtest import run_backtest, Backtester
from trading_bot.strategy.sma_crossover import SMACrossoverStrategy
from trading_bot.db.models import Candle
from trading_bot.db.session import get_session
from trading_bot.logging.logger import logger

router = APIRouter(prefix="/api/backtest", tags=["Backtesting"])

class BacktestRequest(BaseModel):
    """Request model for running a backtest"""
    symbol: str = Field(..., description="Trading symbol", example="BTC/USDT")
    exchange: str = Field(default="binance", description="Exchange name", example="binance")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)", example="2024-01-01")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)", example="2024-12-31")
    timeframe: str = Field(default="1m", description="Timeframe", example="1m")
    initial_capital: float = Field(default=10000.0, description="Starting capital", example=10000.0)
    strategy: str = Field(default="sma_crossover", description="Strategy name", example="sma_crossover")
    strategy_params: Optional[Dict] = Field(None, description="Strategy parameters", example={"short_window": 50, "long_window": 200})

@router.post("/run")
async def run_backtest_endpoint(request: BacktestRequest):
    """
    Run a backtest on historical data.
    
    Fetches historical candle data from the database and runs a backtest
    using the specified strategy.
    
    **Example Request:**
    ```json
    {
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "timeframe": "1m",
        "initial_capital": 10000.0,
        "strategy": "sma_crossover",
        "strategy_params": {
            "short_window": 50,
            "long_window": 200
        }
    }
    ```
    
    **Response:**
    ```json
    {
        "total_trades": 25,
        "winning_trades": 15,
        "losing_trades": 10,
        "win_rate": 0.6,
        "total_pnl": 1500.50,
        "max_drawdown": 0.05,
        "return_pct": 15.005,
        "sharpe_ratio": 1.2,
        "final_value": 11500.50
    }
    ```
    """
    try:
        # Fetch historical data from database
        with get_session() as session:
            query = session.query(Candle).filter_by(
                symbol=request.symbol,
                exchange=request.exchange,
                timeframe=request.timeframe
            )
            
            if request.start_date:
                start_dt = datetime.fromisoformat(request.start_date)
                query = query.filter(Candle.timestamp >= start_dt)
            
            if request.end_date:
                end_dt = datetime.fromisoformat(request.end_date)
                query = query.filter(Candle.timestamp <= end_dt)
            
            candles = query.order_by(Candle.timestamp.asc()).all()
            
            if len(candles) < 200:  # Need enough data for SMA
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient data: {len(candles)} candles. Need at least 200."
                )
            
            # Convert to DataFrame
            data = pd.DataFrame([{
                'timestamp': c.timestamp,
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close,
                'volume': c.volume
            } for c in candles])
        
        # Select strategy
        strategy_params = request.strategy_params or {}
        if request.strategy == "sma_crossover":
            strategy = SMACrossoverStrategy(**strategy_params)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy}")
        
        # Run backtest
        backtester = Backtester(strategy, initial_capital=request.initial_capital)
        result = backtester.run(data, symbol=request.symbol)
        
        return JSONResponse(content=result.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-data")
async def get_available_backtest_data(
    exchange: str = Query(default="binance", description="Exchange name"),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Get available historical data for backtesting.
    
    Returns a list of symbols and date ranges available in the database.
    """
    try:
        with get_session() as session:
            query = session.query(Candle).filter_by(exchange=exchange)
            if symbol:
                query = query.filter_by(symbol=symbol)
            
            candles = query.order_by(Candle.timestamp.asc()).all()
            
            if not candles:
                return JSONResponse(content={"message": "No data available", "data": []})
            
            # Group by symbol
            symbols_data = {}
            for candle in candles:
                if candle.symbol not in symbols_data:
                    symbols_data[candle.symbol] = {
                        "symbol": candle.symbol,
                        "timeframe": candle.timeframe,
                        "start_date": candle.timestamp.isoformat() if candle.timestamp else None,
                        "end_date": candle.timestamp.isoformat() if candle.timestamp else None,
                        "count": 0
                    }
                symbols_data[candle.symbol]["count"] += 1
                if candle.timestamp:
                    if not symbols_data[candle.symbol]["start_date"] or candle.timestamp < datetime.fromisoformat(symbols_data[candle.symbol]["start_date"]):
                        symbols_data[candle.symbol]["start_date"] = candle.timestamp.isoformat()
                    if not symbols_data[candle.symbol]["end_date"] or candle.timestamp > datetime.fromisoformat(symbols_data[candle.symbol]["end_date"]):
                        symbols_data[candle.symbol]["end_date"] = candle.timestamp.isoformat()
            
            return JSONResponse(content={
                "exchange": exchange,
                "data": list(symbols_data.values())
            })
    except Exception as e:
        logger.error(f"Failed to get available data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

