import pytest
from paper_trading_config import PaperTradingConfig
import paper_trading_orders
from paper_portfolio_manager import PaperPortfolioManager
from run_live_paper_bot import auto_manage_positions

class DummyFetcher:
    def __init__(self, price):
        self.price = price
    def get_current_price(self, ticker):
        return self.price, None


def setup_portfolio(entry_price, qty, stock_name="TEST"):
    portfolio = PaperPortfolioManager(initial_capital=1000.0)
    # reset any existing positions
    portfolio.reset_portfolio()
    portfolio.positions = {"SYM": {"qty": qty, "avg_price": entry_price, "stock_name": stock_name}}
    portfolio.cash = portfolio.initial_capital - entry_price * qty
    paper_trading_orders.paper_portfolio = portfolio
    return portfolio


def test_auto_sell_on_loss(monkeypatch):
    # configure zero threshold to sell immediately on any negative
    PaperTradingConfig.STOP_LOSS_PCT = 0.0

    portfolio = setup_portfolio(entry_price=100, qty=1)
    # simulate price drop below entry
    monkeypatch.setattr('run_live_paper_bot.get_market_data', lambda symbol, interval, days: (99, None))

    # call monitor and observe position zeroed
    auto_manage_positions()
    assert 'SYM' not in portfolio.positions
    assert len(portfolio.trade_history) > 0
    # last trade should be a SELL
    assert portfolio.trade_history[-1]['side'] == 'SELL'


def test_auto_sell_on_profit(monkeypatch):
    PaperTradingConfig.PROFIT_TARGET_PCT = 0.0
    portfolio = setup_portfolio(entry_price=100, qty=1)
    monkeypatch.setattr('run_live_paper_bot.get_market_data', lambda symbol, interval, days: (101, None))
    auto_manage_positions()
    assert 'SYM' not in portfolio.positions
    assert portfolio.trade_history[-1]['side'] == 'SELL'
