"""
Tests for LivePortfolioManager
================================
Tests using mocked Upstox API responses to avoid real network calls.
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock the token loader before importing LivePortfolioManager
MOCK_TOKEN = {"access_token": "test_access_token_12345"}


def mock_load_token():
    return MOCK_TOKEN


@pytest.fixture
def portfolio(monkeypatch):
    """Create LivePortfolioManager with mocked token loader."""
    monkeypatch.setattr("standalone_login_auth.load_token_from_file", mock_load_token)
    from live_portfolio_manager import LivePortfolioManager
    mgr = LivePortfolioManager(capital_allocation_pct=100.0)
    return mgr


@pytest.fixture
def portfolio_75pct(monkeypatch):
    """Create LivePortfolioManager with 75% capital allocation."""
    monkeypatch.setattr("standalone_login_auth.load_token_from_file", mock_load_token)
    from live_portfolio_manager import LivePortfolioManager
    return LivePortfolioManager(capital_allocation_pct=75.0)


class TestGetBalance:
    """Tests for get_balance()."""

    def test_balance_applies_allocation_pct(self, portfolio_75pct):
        """Balance should be reduced by capital allocation percentage."""
        mock_response = {
            "status": "success",
            "data": {
                "equity": {
                    "available_margin": 100000.0,
                    "used_margin": 0.0
                }
            }
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            balance = portfolio_75pct.get_balance()
            # 75% of 100000 = 75000
            assert balance == pytest.approx(75000.0, rel=0.01)

    def test_balance_returns_zero_on_api_failure(self, portfolio):
        """Should return 0 when API call fails."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.json.return_value = {}

            balance = portfolio.get_balance()
            assert balance == 0.0

    def test_balance_returns_zero_on_exception(self, portfolio):
        """Should return 0 on network exception."""
        with patch("requests.get", side_effect=Exception("Network error")):
            balance = portfolio.get_balance()
            assert balance == 0.0


class TestGetPositions:
    """Tests for get_positions()."""

    def test_returns_positions_list(self, portfolio):
        """Should return a list of positions."""
        mock_response = {
            "status": "success",
            "data": [
                {"instrument_token": "NSE_EQ|TEST", "quantity": 10, "last_price": 500.0}
            ]
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            positions = portfolio.get_positions()
            assert isinstance(positions, list)
            assert len(positions) == 1

    def test_returns_empty_list_on_failure(self, portfolio):
        """Should return empty list on API failure."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 401
            mock_get.return_value.json.return_value = {}

            positions = portfolio.get_positions()
            assert positions == []


class TestExecuteBuy:
    """Tests for execute_buy()."""

    def test_successful_buy(self, portfolio):
        """Successful buy should return (True, message)."""
        mock_response = {
            "status": "success",
            "data": {"order_id": "ORD123456"}
        }
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = mock_response

            success, msg = portfolio.execute_buy(
                symbol="NSE_EQ|TEST",
                qty=10,
                price=500.0,
                stock_name="Test Stock"
            )
            assert success
            assert "ORD123456" in msg or "BUY" in msg

    def test_failed_buy_returns_false(self, portfolio):
        """Failed buy should return (False, error message)."""
        mock_response = {
            "status": "error",
            "errors": [{"message": "Insufficient funds"}]
        }
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = mock_response

            success, msg = portfolio.execute_buy(
                symbol="NSE_EQ|TEST",
                qty=10,
                price=500.0
            )
            assert not success

    def test_zero_quantity_rejected(self, portfolio):
        """Zero quantity should be rejected without API call."""
        with patch("requests.post") as mock_post:
            success, msg = portfolio.execute_buy(
                symbol="NSE_EQ|TEST",
                qty=0,
                price=500.0
            )
            assert not success
            mock_post.assert_not_called()

    def test_buy_on_network_error(self, portfolio):
        """Network error should return (False, error message)."""
        with patch("requests.post", side_effect=Exception("Connection refused")):
            success, msg = portfolio.execute_buy(
                symbol="NSE_EQ|TEST",
                qty=5,
                price=500.0
            )
            assert not success


class TestExecuteSell:
    """Tests for execute_sell()."""

    def test_successful_sell(self, portfolio):
        """Successful sell should return (True, message)."""
        mock_response = {
            "status": "success",
            "data": {"order_id": "ORD789012"}
        }
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = mock_response

            success, msg = portfolio.execute_sell(
                symbol="NSE_EQ|TEST",
                qty=5,
                price=550.0,
                stock_name="Test Stock"
            )
            assert success

    def test_zero_quantity_rejected(self, portfolio):
        """Zero quantity should be rejected."""
        success, msg = portfolio.execute_sell(
            symbol="NSE_EQ|TEST",
            qty=0,
            price=500.0
        )
        assert not success


class TestCapitalAllocation:
    """Tests for capital allocation percentage."""

    def test_allocation_clamped_to_10_min(self, monkeypatch):
        """Capital allocation below 10% should be clamped to 10%."""
        monkeypatch.setattr("standalone_login_auth.load_token_from_file", mock_load_token)
        from live_portfolio_manager import LivePortfolioManager
        mgr = LivePortfolioManager(capital_allocation_pct=5.0)
        assert mgr.capital_allocation_pct == 10.0

    def test_allocation_clamped_to_100_max(self, monkeypatch):
        """Capital allocation above 100% should be clamped to 100%."""
        monkeypatch.setattr("standalone_login_auth.load_token_from_file", mock_load_token)
        from live_portfolio_manager import LivePortfolioManager
        mgr = LivePortfolioManager(capital_allocation_pct=150.0)
        assert mgr.capital_allocation_pct == 100.0
