from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Optional, List
import asyncio
import json
from trading_bot.core.trading_orchestrator import TradingOrchestrator
from trading_bot.db.models import Trade, Ticker, Candle
from trading_bot.db.session import get_session
from trading_bot.logging.logger import logger
from trading_bot.api.backtest import router as backtest_router
from datetime import datetime, timedelta

app = FastAPI(
    title="Trading LLM Bot API",
    version="1.0.0",
    description="""
    A comprehensive trading bot API supporting multiple exchanges (Binance, Coinbase, Alpaca).
    
    ## Features
    
    * **Multi-Exchange Support**: Trade on Binance, Coinbase, and Alpaca
    * **Real-time Data**: WebSocket streams for market data and trades
    * **Portfolio Management**: Track positions, P&L, and portfolio value
    * **Order Management**: Create, cancel, and track orders
    * **Risk Management**: Built-in risk controls and validation
    * **Paper Trading**: Safe testing mode enabled by default
    
    ## Authentication
    
    API keys are configured via environment variables. See configuration documentation.
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include backtest router
app.include_router(backtest_router)

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
    """Request model for executing a trading cycle"""
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USDT, AAPL)", example="BTC/USDT")
    exchange: str = Field(default="binance", description="Exchange name", example="binance")
    timeframe: Optional[str] = Field(default="1m", description="Timeframe for strategy analysis", example="1m")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "timeframe": "1m"
            }
        }

class OrderRequest(BaseModel):
    """Request model for creating an order"""
    symbol: str = Field(..., description="Trading symbol", example="BTC/USDT")
    side: str = Field(..., description="Order side: 'buy' or 'sell'", example="buy")
    amount: float = Field(..., description="Order amount", example=1.0, gt=0)
    price: Optional[float] = Field(None, description="Limit price (None for market orders)", example=100.0)
    exchange: str = Field(default="binance", description="Exchange name", example="binance")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "side": "buy",
                "amount": 1.0,
                "price": 50000.0,
                "exchange": "binance"
            }
        }

class TradeResponse(BaseModel):
    """Response model for trade execution"""
    status: str = Field(..., description="Trade status", example="executed")
    order_id: Optional[str] = Field(None, description="Order ID if executed", example="12345")
    symbol: Optional[str] = Field(None, description="Trading symbol")
    side: Optional[str] = Field(None, description="Order side")
    amount: Optional[float] = Field(None, description="Order amount")
    price: Optional[float] = Field(None, description="Execution price")
    reason: Optional[str] = Field(None, description="Reason for rejection or hold")

class PortfolioSummary(BaseModel):
    """Portfolio summary response model"""
    total_pnl: float = Field(..., description="Total profit and loss")
    realized_pnl: float = Field(..., description="Realized P&L from closed trades")
    unrealized_pnl: float = Field(..., description="Unrealized P&L from open positions")
    portfolio_value: float = Field(..., description="Current portfolio value")
    total_position_value: float = Field(..., description="Total value of open positions")
    cash: float = Field(..., description="Available cash")
    closed_trades_count: int = Field(..., description="Number of closed trades")

@app.get("/ping", tags=["Health"])
def ping():
    """
    Ping endpoint for service health check.
    
    Returns a simple status message to verify the API is running.
    """
    return {"status": "ok", "service": "trading-bot-api"}

@app.get("/health", tags=["Health"])
def health():
    """
    Health check endpoint.
    
    Returns the health status of the API and its components.
    """
    return {"status": "healthy", "components": {"api": "ok"}}

@app.post("/api/trade/execute", response_model=TradeResponse, tags=["Trading"])
async def execute_trade(request: TradeRequest):
    """
    Execute a complete trading cycle for a symbol.
    
    This endpoint runs the full trading pipeline:
    1. Get strategy signal (SMA crossover)
    2. Validate risk parameters
    3. Execute order if approved
    4. Update portfolio
    
    **Example Request:**
    ```json
    {
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "timeframe": "1m"
    }
    ```
    
    **Response Statuses:**
    - `executed`: Order was successfully placed
    - `hold`: No trading signal generated
    - `rejected`: Trade rejected by risk management
    - `error`: An error occurred during execution
    """
    try:
        orchestrator = TradingOrchestrator(exchange_name=request.exchange)
        result = orchestrator.execute_trading_cycle(request.symbol, request.timeframe)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order/create", tags=["Orders"])
async def create_order(request: OrderRequest):
    """
    Create an order directly, bypassing strategy logic.
    
    Use this endpoint to place orders manually without strategy signals.
    Orders are still subject to risk management checks.
    
    **Order Types:**
    - **Market Order**: Set `price` to `null` for immediate execution at market price
    - **Limit Order**: Set `price` to specify maximum/minimum execution price
    
    **Example Market Order:**
    ```json
    {
        "symbol": "BTC/USDT",
        "side": "buy",
        "amount": 1.0,
        "price": null,
        "exchange": "binance"
    }
    ```
    
    **Example Limit Order:**
    ```json
    {
        "symbol": "BTC/USDT",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
        "exchange": "binance"
    }
    ```
    """
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

@app.get("/api/portfolio/summary", response_model=PortfolioSummary, tags=["Portfolio"])
async def get_portfolio_summary(
    exchange: str = Query(default="binance", description="Exchange name", example="binance")
):
    """
    Get comprehensive portfolio summary.
    
    Returns current portfolio state including:
    - Total and realized/unrealized P&L
    - Portfolio value and cash balance
    - Open positions
    - Trade statistics
    
    **Example Response:**
    ```json
    {
        "total_pnl": 150.50,
        "realized_pnl": 100.00,
        "unrealized_pnl": 50.50,
        "portfolio_value": 10150.50,
        "total_position_value": 500.00,
        "cash": 9650.50,
        "closed_trades_count": 5
    }
    ```
    """
    try:
        orchestrator = TradingOrchestrator(exchange_name=exchange)
        summary = orchestrator.get_portfolio_summary()
        return JSONResponse(content=summary)
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades/history", tags=["Trades"])
async def get_trade_history(
    limit: int = Query(default=100, description="Maximum number of trades to return", ge=1, le=1000)
):
    """
    Get historical trade records.
    
    Returns a list of executed trades ordered by timestamp (most recent first).
    
    **Query Parameters:**
    - `limit`: Maximum number of trades to return (1-1000, default: 100)
    
    **Example Response:**
    ```json
    [
        {
            "id": 1,
            "symbol": "BTC/USDT",
            "side": "buy",
            "amount": 1.0,
            "price": 50000.0,
            "timestamp": "2024-01-01T12:00:00Z",
            "status": "filled"
        }
    ]
    ```
    """
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

@app.get("/api/market/ticker/{symbol}", tags=["Market Data"])
async def get_ticker(
    symbol: str = Path(..., description="Trading symbol", example="BTC/USDT"),
    exchange: str = Query(default="binance", description="Exchange name", example="binance")
):
    """
    Get latest ticker price for a symbol.
    
    Returns the most recent market price for the specified symbol.
    
    **Path Parameters:**
    - `symbol`: Trading symbol (e.g., BTC/USDT, AAPL)
    
    **Query Parameters:**
    - `exchange`: Exchange name (binance, coinbase, alpaca)
    
    **Example Response:**
    ```json
    {
        "symbol": "BTC/USDT",
        "price": 50000.0
    }
    ```
    """
    try:
        orchestrator = TradingOrchestrator(exchange_name=exchange)
        price = orchestrator.get_current_price(symbol)
        return JSONResponse(content={"symbol": symbol, "price": price})
    except Exception as e:
        logger.error(f"Failed to get ticker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{order_id}", tags=["Orders"])
async def get_order_status(
    order_id: str = Path(..., description="Order ID (database ID or exchange order ID)", example="123"),
    exchange: str = Query(default="binance", description="Exchange name", example="binance")
):
    """
    Get detailed order status by ID.
    
    Returns comprehensive order information including status, fills, and timestamps.
    
    **Path Parameters:**
    - `order_id`: Order ID (can be database ID or exchange order ID)
    
    **Order Statuses:**
    - `pending`: Order is pending execution
    - `filled`: Order is completely filled
    - `partial`: Order is partially filled
    - `canceled`: Order was canceled
    - `rejected`: Order was rejected
    
    **Example Response:**
    ```json
    {
        "id": 123,
        "exchange_order_id": "ex_order_456",
        "symbol": "BTC/USDT",
        "side": "buy",
        "status": "filled",
        "amount": 1.0,
        "filled_amount": 1.0,
        "price": 50000.0,
        "average_fill_price": 50000.0,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:01Z"
    }
    ```
    """
    try:
        orchestrator = TradingOrchestrator(exchange_name=exchange)
        order_status = orchestrator.execution_engine.get_order_status(order_id)
        if not order_status:
            raise HTTPException(status_code=404, detail="Order not found")
        return JSONResponse(content=order_status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders", tags=["Orders"])
async def list_orders(
    exchange: str = Query(default="binance", description="Exchange name", example="binance"),
    status: Optional[str] = Query(None, description="Filter by order status (pending, filled, canceled, etc.)", example="filled"),
    limit: int = Query(default=100, description="Maximum number of orders to return", ge=1, le=1000)
):
    """
    List orders with optional filtering.
    
    Returns a list of orders with optional filtering by status.
    
    **Query Parameters:**
    - `exchange`: Exchange name (default: binance)
    - `status`: Optional status filter (pending, filled, partial, canceled, rejected)
    - `limit`: Maximum number of orders to return (1-1000, default: 100)
    
    **Example Request:**
    ```
    GET /api/orders?exchange=binance&status=filled&limit=50
    ```
    
    **Example Response:**
    ```json
    [
        {
            "id": 123,
            "exchange_order_id": "ex_order_456",
            "symbol": "BTC/USDT",
            "side": "buy",
            "status": "filled",
            "amount": 1.0,
            "filled_amount": 1.0,
            "price": 50000.0,
            "created_at": "2024-01-01T12:00:00Z"
        }
    ]
    ```
    """
    try:
        from trading_bot.db.models import Order
        with get_session() as session:
            query = session.query(Order).filter_by(exchange=exchange)
            if status:
                query = query.filter_by(status=status)
            orders = query.order_by(Order.created_at.desc()).limit(limit).all()
            return JSONResponse(content=[{
                "id": o.id,
                "exchange_order_id": o.exchange_order_id,
                "symbol": o.symbol,
                "side": o.side,
                "status": o.status,
                "amount": o.amount,
                "filled_amount": o.filled_amount,
                "price": o.price,
                "created_at": o.created_at.isoformat() if o.created_at else None
            } for o in orders])
    except Exception as e:
        logger.error(f"Failed to list orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/market", tags=["WebSocket"])
async def websocket_market(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data streaming.
    
    Streams live ticker data from the database. Clients can optionally send
    an initial message with a symbol filter:
    
    ```json
    {"symbol": "BTC/USDT"}
    ```
    
    **Message Format:**
    ```json
    {
        "type": "ticker",
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "price": 50000.0,
        "bid": 49999.0,
        "ask": 50001.0,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    ```
    
    Heartbeat messages are sent when no new data is available.
    """
    await manager.connect(websocket)
    try:
        # Receive initial message for symbol filter (optional)
        symbol = None
        try:
            initial_msg = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
            symbol = initial_msg.get('symbol')
        except:
            pass  # No initial message, stream all symbols
        
        last_timestamp = datetime.utcnow() - timedelta(minutes=1)
        while True:
            # Fetch latest ticker data from database
            with get_session() as session:
                query = session.query(Ticker).order_by(Ticker.timestamp.desc())
                if symbol:
                    query = query.filter_by(symbol=symbol)
                query = query.filter(Ticker.timestamp > last_timestamp)
                tickers = query.limit(10).all()
                
                if tickers:
                    for ticker in tickers:
                        data = {
                            "type": "ticker",
                            "symbol": ticker.symbol,
                            "exchange": ticker.exchange,
                            "price": ticker.price,
                            "bid": ticker.bid,
                            "ask": ticker.ask,
                            "timestamp": ticker.timestamp.isoformat() if ticker.timestamp else None
                        }
                        await websocket.send_json(data)
                    last_timestamp = tickers[0].timestamp
                else:
                    # Send heartbeat if no new data
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            await asyncio.sleep(5)  # Send update every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.websocket("/ws/trades", tags=["WebSocket"])
async def websocket_trades(websocket: WebSocket):
    """
    WebSocket endpoint for real-time trade updates.
    
    Streams live trade execution events as they occur.
    
    **Message Format:**
    ```json
    {
        "type": "trade_update",
        "id": 123,
        "symbol": "BTC/USDT",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
        "status": "filled",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    ```
    
    Heartbeat messages are sent when no new trades are available.
    """
    await manager.connect(websocket)
    try:
        last_timestamp = datetime.utcnow() - timedelta(minutes=5)
        while True:
            # Fetch latest trades from database
            with get_session() as session:
                trades = (session.query(Trade)
                         .filter(Trade.timestamp > last_timestamp)
                         .order_by(Trade.timestamp.desc())
                         .limit(20)
                         .all())
                
                if trades:
                    for trade in trades:
                        data = {
                            "type": "trade_update",
                            "id": trade.id,
                            "symbol": trade.symbol,
                            "side": trade.side,
                            "amount": trade.amount,
                            "price": trade.price,
                            "status": trade.status,
                            "timestamp": trade.timestamp.isoformat() if trade.timestamp else None
                        }
                        await websocket.send_json(data)
                    last_timestamp = trades[0].timestamp
                else:
                    # Send heartbeat if no new trades
                    await websocket.send_json({
                        "type": "heartbeat",
                        "message": "No new trades",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            await asyncio.sleep(10)  # Check every 10 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
