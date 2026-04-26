import os
import sys
import json
import pytest
from pathlib import Path

# ensure project root on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading_config import PaperTradingConfig
from paper_portfolio_manager import PaperPortfolioManager
import paper_trading_orders
from trading_execution_ai import place_order_ai, PAPER_TRADING_AVAILABLE

import backend_api
from backend_api import app, _load_creds, _save_creds, CREDS_FILE, ACCESS_TOKEN_FILE
from auth_manager import AuthManager
from fastapi.testclient import TestClient

client = TestClient(app)


def test_paper_module_imports_and_globals(tmp_path):
    # paper trading module should expose necessary names
    assert hasattr(paper_trading_orders, "place_order_ai")
    assert PAPER_TRADING_AVAILABLE is True
    # global portfolio can be set externally; ensure we don't load persistent file
    paper_trading_orders.paper_portfolio = PaperPortfolioManager(
        initial_capital=1000,
        balance_file=tmp_path / 'balance.json'
    )
    assert paper_trading_orders.paper_portfolio.cash == 1000


def test_place_order_ai_routes_correctly(monkeypatch):
    # make sure when PAPER_TRADING_MODE is true the wrapper calls the paper module
    PaperTradingConfig.PAPER_TRADING_MODE = True

    called = {}
    def fake_paper(sym, side, qty, price, **kwargs):
        called['sym'] = sym
        called['side'] = side
        called['qty'] = qty
        called['price'] = price
        called['kwargs'] = kwargs
        return True

    monkeypatch.setattr(paper_trading_orders, 'place_order_ai', fake_paper)

    result = place_order_ai('TESTSYM', 'BUY', 5, 100.0, strategy='foo', stock_name='Foo', interval='day')
    assert result is True
    assert called['sym'] == 'TESTSYM'
    assert called['side'] == 'BUY'
    assert called['qty'] == 5
    # other kwargs should propagate
    assert 'strategy' in called['kwargs'] and called['kwargs']['strategy'] == 'foo'

    # toggling back to live (should simply return None since live behavior returns nothing)
    PaperTradingConfig.PAPER_TRADING_MODE = False
    # monkeypatch live behavior to make sure it is called
    monkeypatch.setattr('trading_execution_ai.requests', pytest.raises)  # cause error if attempted
    # should not raise since qty>0 but live code may attempt network - we won't call it here further


def test_upstox_linking_flow(tmp_path, monkeypatch):
    # redirect the credentials files to temporary location
    monkeypatch.setattr('backend_api.CREDS_FILE', tmp_path / 'creds.json')
    monkeypatch.setattr('backend_api.ACCESS_TOKEN_FILE', tmp_path / 'access_token.json')

    # prepare dummy user and token
    user_id = 42
    token = AuthManager.generate_token(user_id, 'user@example.com', 'User Name')

    # capture calls to update_upstox_link
    calls = []
    def fake_update(uid, email):
        calls.append((uid, email))
        return True
    monkeypatch.setattr('backend_api.update_upstox_link', fake_update)

    # ensure creds file starts empty
    if (tmp_path / 'creds.json').exists():
        (tmp_path / 'creds.json').unlink()

    # hit configure endpoint with JWT header
    resp = client.post('/api/auth/configure', json={
        'api_key': 'foo',
        'api_secret': 'bar',
        'redirect_uri': 'http://localhost/test'
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['success'] is True
    # creds file should contain linking_user_id
    creds = _load_creds()
    assert creds.get('linking_user_id') == user_id

    # simulate callback from Upstox
    class DummyResponse:
        status_code = 200
        def json(self):
            return {'access_token': 'abc123'}
    # backend_api imports requests inside the callback; patch requests.post globally
    import requests
    monkeypatch.setattr(requests, 'post', lambda *args, **kw: DummyResponse())

    # call callback; code param can be arbitrary
    resp2 = client.get('/api/auth/callback?code=XYZ')
    assert resp2.status_code == 200
    # after callback, creds file should NO LONGER have linking_user_id and update_upstox_link should have been called
    creds_after = _load_creds()
    assert 'linking_user_id' not in creds_after
    assert calls == [(user_id, creds_after.get('auth', {}).get('client_id', ''))]

    # hitting auth/status with the same token should now show the account
    status_resp = client.get('/api/auth/status', headers={'Authorization': f'Bearer {token}'})
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data.get('connected') is True
    # `upstox_linked` may be missing when no DB is configured; just ignore if absent


def test_paper_portfolio_buy_and_sell(tmp_path):
    # ensure portfolio persists to temporary file
    bal_file = tmp_path / 'paper_balance.json'
    pm = PaperPortfolioManager(initial_capital=1000.0, balance_file=bal_file)

    # buy 10 units at price 10
    success, msg = pm.execute_buy('SYM', 10, 10.0, stock_name='SymCorp')
    assert success
    assert pm.cash == pytest.approx(900.0)
    assert 'SYM' in pm.positions
    assert pm.positions['SYM']['qty'] == 10

    # sell partial quantity
    success2, msg2 = pm.execute_sell('SYM', 5, 12.0)
    assert success2
    assert pm.cash == pytest.approx(900.0 + 5 * 12.0)
    # qty should reduce
    assert pm.positions['SYM']['qty'] == 5

    # sell remaining
    success3, msg3 = pm.execute_sell('SYM', 5, 15.0)
    assert success3
    assert 'SYM' not in pm.positions
    assert pm.cash > 0


def test_paper_api_endpoints():
    # paper trades endpoint should return success with empty list when no trades
    resp = client.get('/api/paper/trades?limit=5')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('success') is True
    assert isinstance(data.get('trades'), list)

    # portfolio endpoint should return expected keys
    resp2 = client.get('/api/paper/portfolio')
    assert resp2.status_code == 200
    p = resp2.json()
    assert 'success' in p
    assert 'balance' in p
    assert 'open_positions' in p


def test_start_agent_passes_correct_args(monkeypatch):
    # simulate a trading mode manager that returns 'live' and 50% capital
    class DummyMgr:
        def get_mode(self):
            return "live"
        def get_capital_allocation(self):
            return 50.0
    monkeypatch.setattr('backend_api.get_mode_manager', lambda: DummyMgr())

    # intercept subprocess.Popen calls to capture arguments
    captured = {}
    def fake_popen(args, stdout, stderr, cwd):
        captured['args'] = args
        class DummyProc:
            pid = 12345
            def poll(self):
                return 1
            stdout = []
            stderr = []
        return DummyProc()
    monkeypatch.setattr(backend_api.subprocess, 'Popen', fake_popen)

    # call core function directly instead of via HTTP to avoid routing issues
    result = backend_api._start_agent_core()
    assert result['mode'] == 'LIVE' or result['mode'] == 'live' or result['mode'] == 'Live'
    assert result['capital_allocation_pct'] == 50.0

    # ensure the CLI argument was converted correctly to fraction
    assert '--capital' in captured['args']
    idx = captured['args'].index('--capital')
    assert captured['args'][idx+1] == '0.5'


def test_stop_agent_not_running():
    # ensure agent state is stopped
    # send POST to stop endpoint
    resp = client.post('/api/agent/stop')
    assert resp.status_code == 200
    body = resp.json()
    assert body.get('success') is False
    assert 'not currently running' in body.get('message', '').lower()


def test_bot_cli_args():
    """Importing the bot module should parse CLI args from sys.argv."""
    import importlib, sys

    # backup original argv and modules
    orig_argv = sys.argv.copy()
    try:
        sys.argv = ['run_live_paper_bot.py', '--mode', 'paper', '--capital', '0.25']
        # reload the module to re-run the parser logic
        if 'run_live_paper_bot' in sys.modules:
            del sys.modules['run_live_paper_bot']
        botmod = importlib.import_module('run_live_paper_bot')
        # ensure attributes exist
        assert hasattr(botmod, 'args')
        assert botmod.args.mode == 'paper'
        assert abs(botmod.args.capital - 0.25) < 1e-9
    finally:
        sys.argv = orig_argv

