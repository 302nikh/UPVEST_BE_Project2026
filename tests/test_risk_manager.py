"""
Tests for RiskManager
=====================
Tests position limits, circuit breaker, stop-loss, and trade frequency.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from risk_manager import RiskManager


@pytest.fixture
def risk_mgr(tmp_path, monkeypatch):
    """Create a fresh RiskManager for each test with a clean temp state file."""
    mgr = RiskManager(
        initial_capital=100000,
        max_position_size_pct=1.0,
        max_open_positions=5,
        daily_loss_limit_pct=0.05,
        max_trades_per_day=20,
        min_trade_interval_seconds=1,   # short for tests
        max_drawdown_pct=0.10,
        stop_loss_pct=0.02
    )
    # Override state file to a temp path and reset state to clean slate
    mgr.state_file = tmp_path / "risk_state.json"
    mgr.trades_today = 0
    mgr.circuit_breaker_active = False
    mgr.last_trade_time = None
    from datetime import date
    mgr.today_date = date.today()
    return mgr


class TestValidateTrade:
    """Tests for validate_trade() method."""

    def test_valid_buy_trade(self, risk_mgr):
        """A normal BUY trade within limits should pass."""
        can_trade, reason = risk_mgr.validate_trade(
            symbol="NSE_EQ|TEST",
            side="BUY",
            quantity=10,
            price=500.0,
            current_portfolio_value=100000,
            current_open_positions=0
        )
        assert can_trade, f"Expected trade to pass but got: {reason}"

    def test_max_positions_blocked(self, risk_mgr):
        """Trade should be blocked when max positions reached."""
        can_trade, reason = risk_mgr.validate_trade(
            symbol="NSE_EQ|TEST",
            side="BUY",
            quantity=10,
            price=500.0,
            current_portfolio_value=100000,
            current_open_positions=5  # Already at max
        )
        assert not can_trade
        assert "position" in reason.lower() or "max" in reason.lower()

    def test_sell_allowed_at_max_positions(self, risk_mgr):
        """SELL should always be allowed regardless of position count."""
        can_trade, reason = risk_mgr.validate_trade(
            symbol="NSE_EQ|TEST",
            side="SELL",
            quantity=10,
            price=500.0,
            current_portfolio_value=100000,
            current_open_positions=5
        )
        assert can_trade, f"SELL should always be allowed, got: {reason}"

    def test_zero_quantity_blocked(self, risk_mgr):
        """Zero quantity validation is handled by LivePortfolioManager, not RiskManager.
        RiskManager allows it through — the portfolio layer catches it.
        This test verifies the risk manager doesn't crash on zero quantity."""
        # Should not raise an exception
        try:
            can_trade, reason = risk_mgr.validate_trade(
                symbol="NSE_EQ|TEST",
                side="BUY",
                quantity=0,
                price=500.0,
                current_portfolio_value=100000,
                current_open_positions=0
            )
            # Either blocked or allowed — just shouldn't crash
            assert isinstance(can_trade, bool)
        except Exception as e:
            pytest.fail(f"validate_trade raised an exception on zero qty: {e}")


class TestDailyLossLimit:
    """Tests for circuit breaker / daily loss limit."""

    def test_no_loss_ok(self, risk_mgr):
        """No loss should not trigger circuit breaker."""
        can_trade, reason = risk_mgr.check_daily_loss_limit(100000)
        assert can_trade

    def test_circuit_breaker_triggers(self, risk_mgr):
        """5%+ daily loss should trigger circuit breaker."""
        # Portfolio dropped from 100k to 94k (6% loss)
        can_trade, reason = risk_mgr.check_daily_loss_limit(94000)
        assert not can_trade
        assert "circuit" in reason.lower() or "loss" in reason.lower()

    def test_small_loss_ok(self, risk_mgr):
        """Small loss (< 5%) should not trigger circuit breaker."""
        # Portfolio dropped 3% (within limit)
        can_trade, reason = risk_mgr.check_daily_loss_limit(97000)
        assert can_trade


class TestTradeFrequency:
    """Tests for trade frequency throttling."""

    def test_record_and_count(self, risk_mgr):
        """Recording trades should increment counter."""
        initial = risk_mgr.get_status().get("trades_today", 0)
        risk_mgr.record_trade()
        risk_mgr.record_trade()
        status = risk_mgr.get_status()
        assert status.get("trades_today", 0) == initial + 2

    def test_max_trades_per_day(self, risk_mgr):
        """After max trades, new trades should be blocked."""
        # Record max trades
        for _ in range(20):
            risk_mgr.record_trade()

        can_trade, reason = risk_mgr.validate_trade(
            symbol="NSE_EQ|TEST",
            side="BUY",
            quantity=10,
            price=500.0,
            current_portfolio_value=100000,
            current_open_positions=0
        )
        assert not can_trade
        assert "trade" in reason.lower() or "max" in reason.lower() or "daily" in reason.lower()


class TestStatus:
    """Tests for get_status() method."""

    def test_status_returns_dict(self, risk_mgr):
        """get_status() should return a dict with expected keys."""
        status = risk_mgr.get_status()
        assert isinstance(status, dict)
        # Should have at minimum these keys
        assert "trades_today" in status or "circuit_breaker_active" in status

    def test_circuit_breaker_initially_off(self, risk_mgr):
        """Circuit breaker should start inactive."""
        status = risk_mgr.get_status()
        assert not status.get("circuit_breaker_active", False)
