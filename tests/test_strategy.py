import pandas as pd
from trading_bot.strategy.sma_crossover import SMACrossoverStrategy

def test_sma_crossover_signal_shape():
    strategy = SMACrossoverStrategy(short_window=2, long_window=3)
    data = pd.Series([1, 2, 3, 4, 5])
    signal = strategy.generate_signal(data)
    assert len(signal) == len(data)
