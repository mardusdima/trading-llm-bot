import pytest
from trading_bot.risk.manager import RiskManager

def test_risk_manager_initialization():
    """Test RiskManager initializes with default values"""
    rm = RiskManager()
    assert rm.max_position_size > 0
    assert rm.max_drawdown_pct > 0
    assert rm.stop_loss_pct > 0

def test_check_position_limit():
    """Test position limit checking"""
    rm = RiskManager()
    # Test within limit
    assert rm.check_position_limit("BTC/USDT", 1.0, 100.0, {}) == True
    # Test exceeds limit
    assert rm.check_position_limit("BTC/USDT", 100.0, 100.0, {}) == False

def test_check_stop_loss():
    """Test stop-loss calculation"""
    rm = RiskManager()
    # check_stop_loss returns True if loss is within acceptable range (NOT triggered)
    # Test stop-loss NOT triggered (loss within limit)
    assert rm.check_stop_loss(100.0, 99.0, "buy") == True  # 1% loss < 2% stop, acceptable
    # Test stop-loss triggered (loss exceeds limit)
    assert rm.check_stop_loss(100.0, 97.0, "buy") == False  # 3% loss > 2% stop, triggered

def test_check_max_drawdown():
    """Test max drawdown checking"""
    rm = RiskManager()
    # Test within drawdown limit
    assert rm.check_max_drawdown(9500.0, 10000.0) == True  # 5% drawdown < 10% max
    # Test exceeds drawdown limit
    assert rm.check_max_drawdown(8500.0, 10000.0) == False  # 15% drawdown > 10% max

def test_validate_trade():
    """Test comprehensive trade validation"""
    rm = RiskManager()
    positions = {}
    portfolio_value = 10000.0
    peak_value = 10000.0
    
    # Valid trade
    is_valid, reason = rm.validate_trade(
        "BTC/USDT", "buy", 1.0, 100.0, positions, portfolio_value, peak_value
    )
    assert is_valid == True
    
    # Trade exceeds position limit
    is_valid, reason = rm.validate_trade(
        "BTC/USDT", "buy", 100.0, 100.0, positions, portfolio_value, peak_value
    )
    assert is_valid == False
    assert "exceeds limit" in reason.lower()

def test_evaluate_position():
    """Test position evaluation for stop-loss"""
    rm = RiskManager()
    position = {
        'entry_price': 100.0,
        'current_price': 97.0,
        'side': 'buy'
    }
    # Should trigger stop-loss
    assert rm.evaluate_position(position) == True

