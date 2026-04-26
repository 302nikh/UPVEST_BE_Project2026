"""
Tests for TradingModeManager
=============================
Tests mode switching, capital allocation, and prerequisite checks.
"""

import pytest
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_mode_manager import TradingModeManager


@pytest.fixture
def mode_mgr(tmp_path, monkeypatch):
    """Create a TradingModeManager using a temp config file."""
    config_file = tmp_path / "trading_mode.json"
    monkeypatch.setattr("trading_mode_manager.CONFIG_FILE", config_file)
    return TradingModeManager()


class TestDefaultState:
    """Tests for initial/default state."""

    def test_default_mode_is_paper(self, mode_mgr):
        """Default mode should be paper trading."""
        assert mode_mgr.get_mode() == "paper"

    def test_default_capital_is_100(self, mode_mgr):
        """Default capital allocation should be 100%."""
        assert mode_mgr.get_capital_allocation() == 100.0


class TestCapitalAllocation:
    """Tests for capital allocation setting."""

    def test_set_valid_capital(self, mode_mgr):
        """Setting a valid percentage should succeed."""
        success, msg = mode_mgr.set_capital_allocation(75.0)
        assert success
        assert mode_mgr.get_capital_allocation() == 75.0

    def test_set_minimum_capital(self, mode_mgr):
        """10% should be the minimum allowed."""
        success, _ = mode_mgr.set_capital_allocation(10.0)
        assert success

    def test_set_maximum_capital(self, mode_mgr):
        """100% should be the maximum allowed."""
        success, _ = mode_mgr.set_capital_allocation(100.0)
        assert success

    def test_below_minimum_rejected(self, mode_mgr):
        """Below 10% should be rejected."""
        success, msg = mode_mgr.set_capital_allocation(5.0)
        assert not success
        assert "10" in msg or "between" in msg.lower()

    def test_above_maximum_rejected(self, mode_mgr):
        """Above 100% should be rejected."""
        success, msg = mode_mgr.set_capital_allocation(110.0)
        assert not success


class TestModeSwitching:
    """Tests for mode switching logic."""

    def test_switch_to_paper_always_works(self, mode_mgr):
        """Switching to paper should always succeed."""
        success, msg = mode_mgr.set_mode("paper", confirmed=True)
        assert success
        assert mode_mgr.get_mode() == "paper"

    def test_switch_to_live_without_confirmation_fails(self, mode_mgr):
        """Switching to live without confirmed=True should fail."""
        success, msg = mode_mgr.set_mode("live", confirmed=False)
        assert not success
        assert "confirm" in msg.lower() or "confirmation" in msg.lower()

    def test_invalid_mode_rejected(self, mode_mgr):
        """Invalid mode strings should be rejected."""
        success, msg = mode_mgr.set_mode("sandbox")
        assert not success

    def test_same_mode_returns_true(self, mode_mgr):
        """Switching to the same mode should return success."""
        success, msg = mode_mgr.set_mode("paper", confirmed=True)
        assert success

    def test_live_requires_token(self, monkeypatch, tmp_path):
        """Switching to live without token should fail when prerequisites not met."""
        config_file = tmp_path / "trading_mode.json"
        monkeypatch.setattr("trading_mode_manager.CONFIG_FILE", config_file)

        mgr = TradingModeManager()
        # Patch can_switch_to_live to simulate missing token
        monkeypatch.setattr(mgr, "can_switch_to_live",
                            lambda: (False, "No Upstox access token. Please connect your Demat account first."))

        success, msg = mgr.set_mode("live", confirmed=True)
        assert not success
        assert "token" in msg.lower() or "connect" in msg.lower() or "auth" in msg.lower()


class TestEmergencyReset:
    """Tests for emergency reset."""

    def test_reset_to_paper(self, mode_mgr):
        """Emergency reset should always go to paper mode."""
        mode_mgr.reset_to_paper()
        assert mode_mgr.get_mode() == "paper"


class TestStatusOutput:
    """Tests for get_status() output."""

    def test_status_has_required_keys(self, mode_mgr):
        """Status should contain all required keys."""
        status = mode_mgr.get_status()
        assert "mode" in status
        assert "capital_allocation_pct" in status
        assert "can_switch_to_live" in status

    def test_status_mode_matches_get_mode(self, mode_mgr):
        """Status mode should match get_mode()."""
        status = mode_mgr.get_status()
        assert status["mode"] == mode_mgr.get_mode()
