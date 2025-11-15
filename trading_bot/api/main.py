from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
from trading_bot.core.trading_orchestrator import TradingOrchestrator
from trading_bot.db.models import Trade, Ticker, Candle
from trading_bot.db.session import get_session
from trading_bot.logging.logger import logger

app = FastAPI(title="Trading LLM Bot", version="1.0.0")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models for request/response
class TradeRequest(BaseModel):
    symbol: str
    exchange: str = "binance"
    timeframe: Optional[str] = "1m"

class OrderRequest(BaseModel):
    symbol: str
    side: str
    amount: float
    price: Optional[float] = None
    exchange: str = "binance"

@app.get("/ping")
def ping():
    return {"status": "ok", "service": "trading-bot-api"}

@app.get("/health")
def health():
    return {"status": "healthy", "components": {"api": "ok"}}

@app.post("/api/trade/execute")
async def execute_trade(request: TradeRequest):
    """Execute a trading cycle for a symbol"""
    try:
        orchestrator = TradingOrchestrator(exchange_name=request.exchange)
        result = orchestrator.execute_trading_cycle(request.symbol, request.timeframe)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order/create")
async def create_order(request: OrderRequest):
    """Create an order directly (bypasses strategy)"""
    try:
        orchestrator = TradingOrchestrator(exchange_name=request.exchange)
        order = orchestrator.execution_engine.send_order(
            symbol=request.symbol,
            side=request.side,
            amount=request.amount,
            price=request.price
        )
        return JSONResponse(content={"status": "success", "order": order})
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/summary")
async def get_portfolio_summary(exchange: str = "binance"):
    """Get portfolio summary"""
    try:
        orchestrator = TradingOrchestrator(exchange_name=exchange)
        summary = orchestrator.get_portfolio_summary()
        return JSONResponse(content=summary)
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades/history")
async def get_trade_history(limit: int = 100):
    """Get trade history"""
    try:
        with get_session() as session:
            trades = session.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
            return JSONResponse(content=[{
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "amount": t.amount,
                "price": t.price,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "status": t.status
            } for t in trades])
    except Exception as e:
        logger.error(f"Failed to get trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/ticker/{symbol}")
async def get_ticker(symbol: str, exchange: str = "binance"):
    """Get latest ticker for a symbol"""
    try:
        orchestrator = TradingOrchestrator(exchange_name=exchange)
        price = orchestrator.get_current_price(symbol)
        return JSONResponse(content={"symbol": symbol, "price": price})
    except Exception as e:
        logger.error(f"Failed to get ticker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    """WebSocket endpoint for real-time market data streaming"""
    await manager.connect(websocket)
    try:
        while True:
            # Send latest ticker data periodically
            # In production, this would stream real-time data from exchanges
            data = {
                "type": "ticker",
                "message": "Market data streaming active",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            await websocket.send_json(data)
            await asyncio.sleep(5)  # Send update every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")

@app.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):
    """WebSocket endpoint for real-time trade updates"""
    await manager.connect(websocket)
    try:
        while True:
            # In production, this would stream real-time trade events
            data = {
                "type": "trade_update",
                "message": "Trade updates streaming active"
            }
            await websocket.send_json(data)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
