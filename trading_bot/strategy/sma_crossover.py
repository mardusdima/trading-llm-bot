import pandas as pd
from trading_bot.db.models import Candle
from trading_bot.db.session import get_session
from datetime import timedelta

class SMACrossoverStrategy:
    """
    SMA Crossover (Golden Cross / Death Cross):
    Buy when short SMA crosses above long SMA; sell when it crosses below.
    """
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, price_series: pd.Series):
        short_sma = price_series.rolling(window=self.short_window).mean()
        long_sma = price_series.rolling(window=self.long_window).mean()
        signal = pd.Series(0, index=price_series.index)
        # 1 for buy, -1 for sell, 0 for hold
        signal[(short_sma > long_sma) & (short_sma.shift(1) <= long_sma.shift(1))] = 1  # Bull crossover
        signal[(short_sma < long_sma) & (short_sma.shift(1) >= long_sma.shift(1))] = -1 # Bear crossover
        return signal

    def get_signal_from_db(self, symbol, exchange, timeframe='1m', lookback=250):
        with get_session() as session:
            q = (session
                .query(Candle)
                .filter_by(symbol=symbol, exchange=exchange, timeframe=timeframe)
                .order_by(Candle.timestamp.desc())
                .limit(lookback)
            )
            candles = q.all()
            if not candles or len(candles) < self.long_window:
                return 0  # Not enough data, can't generate signal
            # Reverse for correct chronological order
            candles = list(reversed(candles))
            closes = pd.Series([c.close for c in candles], index=[c.timestamp for c in candles])
            signals = self.generate_signals(closes)
            return signals.iloc[-1]  # -1/0/+1

def run_sma_strategy(symbol, exchange, timeframe='1m', lookback=250):
    strategy = SMACrossoverStrategy()
    signal = strategy.get_signal_from_db(symbol, exchange, timeframe, lookback)
    if signal == 1:
        print(f"SMA crossover signal for {symbol}@{exchange}: BUY")
    elif signal == -1:
        print(f"SMA crossover signal for {symbol}@{exchange}: SELL")
    else:
        print(f"SMA crossover signal for {symbol}@{exchange}: HOLD")
    return signal
