from trading_bot.portfolio.tracker import PortfolioTracker

def test_portfolio_tracker_methods():
    tracker = PortfolioTracker()
    assert hasattr(tracker, "update_positions")
    assert hasattr(tracker, "calculate_pnl")
