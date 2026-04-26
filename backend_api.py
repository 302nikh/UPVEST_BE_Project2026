"""
Backend API Server
==================
FastAPI server that exposes REST endpoints for the UPVEST frontend
to communicate with the Python trading backend.

Endpoints:
- /api/status - Server health check
- /api/portfolio - Get current positions and P&L
- /api/trades - Get trade history
- /api/trades/today - Get today's trades
- /api/daily-summary - Get daily P&L summaries
- /api/bot/status - Trading bot status
- /api/bot/start - Start trading bot
- /api/bot/stop - Stop trading bot
- /api/ai/predict - Get AI prediction for a stock

Run with: python backend_api.py
"""


from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pathlib import Path
import threading
import json
import os

# ── Database import (independent of AuthManager) ─────────────────────────────
try:
    from database_manager import (
        get_trades_by_date, get_trades_by_date_range,
        get_daily_summary, get_daily_summaries_by_range,
        initialize_database,
        create_user, get_user_by_email, update_upstox_link
    )
    from datetime import timedelta

    # Wrapper: get_all_trades
    def get_all_trades(limit: int = 50):
        """Get recent trades from database"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            df = get_trades_by_date_range(start_date, end_date)
            if df.empty:
                return []
            records = df.to_dict('records')[-limit:]
            return list(reversed(records))
        except Exception as e:
            print(f"Error getting trades: {e}")
            return []

    # Wrapper: get_daily_summaries
    def get_daily_summaries(limit: int = 30):
        """Get daily summaries from database"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=limit)
            df = get_daily_summaries_by_range(start_date, end_date)
            if df.empty:
                return []
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting summaries: {e}")
            return []

    DB_AVAILABLE = True
    print("[OK] Database module loaded.")
except Exception as e:
    DB_AVAILABLE = False
    print(f"[WARN] Database manager not available: {e}")

# ── AuthManager (separate — needs bcrypt, optional) ───────────────────────────
try:
    from auth_manager import AuthManager
    AUTH_MANAGER_AVAILABLE = True
except Exception as e:
    AUTH_MANAGER_AVAILABLE = False
    # Create a stub so the rest of the code doesn't crash
    class AuthManager:
        @staticmethod
        def verify_token(token): return None
        @staticmethod
        def create_token(payload, expires_delta=None): return ""
    print(f"[WARN] AuthManager not available (bcrypt missing?): {e}")

try:
    from trading_execution import get_pnL_summary, get_available_funds
    from upstox import upstox_positions
    TRADING_AVAILABLE = True
except ImportError:
    TRADING_AVAILABLE = False
    print("[WARN] Trading execution not available")

try:
    from standalone_login_auth import load_token_from_file
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    print("Warning: Auth module not available")

# Trading mode and risk management
try:
    from trading_mode_manager import get_mode_manager
    from risk_manager import RiskManager
    MODE_MANAGER_AVAILABLE = True
except ImportError as e:
    MODE_MANAGER_AVAILABLE = False
    print(f"Warning: Mode manager not available: {e}")

# Agent process management
import subprocess
import psutil

# Global agent process tracker
agent_process = None
agent_start_time = None
agent_mode = "paper"  # paper or live

# Initialize FastAPI app
app = FastAPI(
    title="UPVEST Trading API",
    description="REST API for UPVEST AI Trading Platform",
    version="1.0.0"
)

# Enable CORS for frontend access
# Production: set ALLOWED_ORIGINS env var, e.g. "https://yourdomain.com,https://www.yourdomain.com"
# Development: allow localhost/127.0.0.1 on ANY port (covers Live Server 5500, etc.)
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
_cors_origins = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()] if _allowed_origins_env else []

# Notes:
# - We do NOT rely on "*" because the frontend may run on localhost or 127.0.0.1 (different origins).
# - We do NOT use credentials/cookies for this app’s browser calls, so keep allow_credentials=False.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=None if _cors_origins else r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend files directly from the backend so users can open the app from port 5000
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Global state for agent control
agent_state = {
    "running": False,
    "started_at": None,
    "trades_today": 0,
    "pnl_today": 0.0,
    "last_signal": None,
    "thread": None
}
# Backward-compat alias
bot_state = agent_state


# ============== Pydantic Models ==============

class StatusResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    db_available: bool
    trading_available: bool
    auth_available: bool


class TradeRecord(BaseModel):
    id: Optional[int] = None
    timestamp: str
    symbol: str
    stock_name: str
    strategy: str
    signal: str
    quantity: int
    price: float
    order_id: Optional[str] = None
    status: str
    ai_enabled: bool = False
    confidence: Optional[float] = None
    models_used: Optional[str] = None


class PortfolioResponse(BaseModel):
    balance: float
    total_pnl: float
    open_positions: int
    positions: List[Dict[str, Any]]
    total_invested: Optional[float] = None
    current_value: Optional[float] = None
    total_returns: Optional[float] = None


class DailySummary(BaseModel):
    date: str
    starting_balance: float
    ending_balance: float
    total_pnl: float
    total_trades: int
    mode: str


class BotStatusResponse(BaseModel):
    running: bool
    started_at: Optional[str] = None
    trades_today: int
    pnl_today: float
    last_signal: Optional[str] = None


class PredictionRequest(BaseModel):
    symbol: str
    interval: str = "day"


class PredictionResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float
    predicted_price: Optional[float] = None
    price_change_pct: Optional[float] = None
    models_used: List[str]
    reason: str


# ============== API Endpoints ==============

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Health check endpoint"""
    return StatusResponse(
        status="online",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        db_available=DB_AVAILABLE,
        trading_available=TRADING_AVAILABLE,
        auth_available=AUTH_AVAILABLE
    )


@app.get("/api/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    """Get current portfolio data"""
    if not TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Trading module not available")
    
    try:
        pnl, open_pos = get_pnL_summary()
        balance = get_available_funds()
        
        # Get positions from Upstox (only in live mode)
        positions = []
        try:
            # build credentials exactly as trading_execution does
            from standalone_login_auth import load_token_from_file
            token_info = load_token_from_file()
            creds = {
                "api": {"headers": {"Authorization": f"Bearer {token_info.get('access_token')}",
                                       "accept": "application/json"}},
                "auth": {"client_id": "AUTO_BOT"}
            }
            # upstox_positions() returns the creds dict (not a list directly)
            # — the positions list is stored in creds["api"]["positions"]
            updated_creds = upstox_positions(creds)
            if updated_creds and isinstance(updated_creds, dict):
                positions = updated_creds.get("api", {}).get("positions", []) or []
        except TypeError as e:
            # upstox_positions requires creds; if call failed just log and continue
            print(f"Error fetching positions (missing creds?): {e}")
        except Exception as e:
            print(f"Error fetching positions: {e}")
        
        # Upstox v2 API uses 'last_price' for LTP and 'average_price' for cost basis
        position_value = 0.0
        total_invested = 0.0
        for pos in positions:
            qty = float(pos.get('quantity', 0) or 0)
            ltp = float(
                pos.get('last_price') or pos.get('ltp') or
                pos.get('last_trade_price') or pos.get('close_price') or 0
            )
            avg_price = float(pos.get('average_price') or pos.get('buy_price') or ltp or 0)
            position_value += qty * ltp
            total_invested += qty * avg_price

        current_value = float(balance) + position_value
        # Fallback when no open positions
        if total_invested == 0:
            total_invested = current_value - float(pnl)

        return PortfolioResponse(
            balance=balance,
            total_pnl=pnl,
            open_positions=open_pos,
            positions=positions,
            total_invested=total_invested,
            current_value=current_value,
            total_returns=pnl
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades", response_model=List[TradeRecord])
async def get_trades(limit: int = 50):
    """Get trade history"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        trades = get_all_trades(limit=limit)
        return [TradeRecord(
            id=t.get('id'),
            timestamp=str(t.get('timestamp', '')),
            symbol=t.get('symbol', ''),
            stock_name=t.get('stock_name', ''),
            strategy=t.get('strategy', ''),
            signal=t.get('signal', ''),
            quantity=t.get('quantity', 0),
            price=t.get('price', 0.0),
            order_id=t.get('order_id'),
            status=t.get('status', ''),
            ai_enabled=t.get('ai_enabled', False),
            confidence=t.get('confidence'),
            models_used=t.get('models_used')
        ) for t in trades]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/today", response_model=List[TradeRecord])
async def get_trades_today():
    """Get today's trades"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        today = date.today()
        trades = get_trades_by_date(today)
        return [TradeRecord(
            id=t.get('id'),
            timestamp=str(t.get('timestamp', '')),
            symbol=t.get('symbol', ''),
            stock_name=t.get('stock_name', ''),
            strategy=t.get('strategy', ''),
            signal=t.get('signal', ''),
            quantity=t.get('quantity', 0),
            price=t.get('price', 0.0),
            order_id=t.get('order_id'),
            status=t.get('status', ''),
            ai_enabled=t.get('ai_enabled', False),
            confidence=t.get('confidence'),
            models_used=t.get('models_used')
        ) for t in trades]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/daily-summary", response_model=List[DailySummary])
async def get_daily_summary(days: int = 30):
    """Get daily P&L summaries"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        summaries = get_daily_summaries(limit=days)
        return [DailySummary(
            date=str(s.get('date', '')),
            starting_balance=s.get('starting_balance', 0.0),
            ending_balance=s.get('ending_balance', 0.0),
            total_pnl=s.get('total_pnl', 0.0),
            total_trades=s.get('total_trades', 0),
            mode=s.get('notes', 'Unknown')
        ) for s in summaries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/status", response_model=BotStatusResponse)
async def get_agent_status():
    """Get AI trading agent status — checks both subprocess and PID file."""
    # 1. Check subprocess launched from this session
    is_running = False
    if agent_process and agent_process.poll() is None:
        is_running = True
        agent_state["running"] = True
    else:
        # 2. Check PID file written by terminal-launched bot
        pid_file = Path("data/bot.pid")
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                proc = psutil.Process(pid)
                if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                    is_running = True
                    agent_state["running"] = True
                else:
                    pid_file.unlink(missing_ok=True)
                    agent_state["running"] = False
            except (psutil.NoSuchProcess, ValueError, OSError):
                pid_file.unlink(missing_ok=True)
                agent_state["running"] = False
        else:
            agent_state["running"] = False

    # 3. Pull live trade count from DB if available
    trades_today = agent_state["trades_today"]
    if DB_AVAILABLE:
        try:
            today_trades = get_trades_by_date(date.today())
            trades_today = len(today_trades) if hasattr(today_trades, '__len__') else today_trades.shape[0]
            agent_state["trades_today"] = trades_today
        except Exception:
            pass

    return BotStatusResponse(
        running=is_running,
        started_at=agent_state["started_at"],
        trades_today=trades_today,
        pnl_today=agent_state["pnl_today"],
        last_signal=agent_state["last_signal"]
    )


@app.get("/api/bot/status", response_model=BotStatusResponse)
async def get_bot_status():
    """[Legacy] Get AI trading agent status — use /api/agent/status instead"""
    return await get_agent_status()


def run_trading_agent(mode: str = "paper", capital_pct: float = 100.0):
    """Background task to run the AI trading agent in the correct mode"""
    global agent_state
    try:
        # CRITICAL: Force UTF-8 encoding on stdout/stderr for this thread.
        # Windows consoles default to cp1252 which cannot handle emojis
        # or special characters used throughout the trading codebase.
        import sys, io
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
            )
        if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True
            )

        if mode == "live":
            from live_agent import run_live_agent
            run_live_agent(capital_allocation_pct=capital_pct)
        else:
            from trading_execution_ai import main_ai_enhanced
            result = main_ai_enhanced()
        agent_state["running"] = False
        agent_state["last_signal"] = "Completed"
        # Auto-export Excel after each session
        try:
            _auto_export_excel()
        except Exception:
            pass  # Export failure should never crash the agent
    except Exception as e:
        agent_state["running"] = False
        agent_state["last_signal"] = f"Error: {str(e)}"
        print(f"[AGENT ERROR] {e}")



def _start_agent_core(background_tasks: BackgroundTasks = None, mode_override: str = None):
    """Core logic to start the AI agent via subprocess

    - mode_override: optional string ('paper' or 'live') recieved from the
      request body; if provided, it takes priority over the stored trading mode.
    """
    global agent_state, agent_process

    # We determine running state by checking if a subprocess is alive
    if agent_process and agent_process.poll() is None:
        raise HTTPException(status_code=400, detail="AI Agent is already running")

    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth module not available")

    # Reject start request if market is closed
    try:
        from run_live_paper_bot import is_market_open
        if not is_market_open():
            raise HTTPException(
                status_code=400, 
                detail="Market is closed. Intraday trading is only allowed between 09:15 and 15:30 IST on weekdays."
            )
    except ImportError:
        pass # If run_live_paper_bot missing, allow it to fail naturally later

    # Determine trading mode and capital percentage.  Prefer mode_override passed
    # by the frontend (start button) so that tests can manually launch paper even if
    # the stored mode is different.
    current_mode = mode_override if mode_override else "paper"
    capital_pct = 100.0
    if MODE_MANAGER_AVAILABLE and not mode_override:
        mode_mgr = get_mode_manager()
        current_mode = mode_mgr.get_mode()
        capital_pct = mode_mgr.get_capital_allocation()

    # Authentication only required for real live mode
    if current_mode == "live":
        token = load_token_from_file()
        if not token or "access_token" not in token:
            raise HTTPException(status_code=401, detail="Not authenticated with Upstox. Connect your Demat account first.")

    # We always launch the continuous loop script; it will respect the --mode flag
    script_name = "run_live_paper_bot.py"

    try:
        # pass mode and capital as command-line arguments so the bot script can
        # configure itself accordingly.  We also capture stdout/stderr and
        # print to our console so user's terminal sees what the agent is doing.
        # convert percentage (0-100) to fraction (0.0-1.0) for the bot script
        args = ["python", script_name, "--mode", current_mode, "--capital", str(capital_pct / 100.0)]
        agent_process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        # spawn threads to echo output back to the server log
        def _stream(proc, label):
            for line in proc.stdout or []:
                print(f"[{label}] {line.decode().rstrip()}")
            for line in proc.stderr or []:
                print(f"[{label} ERR] {line.decode().rstrip()}")
        import threading
        threading.Thread(target=_stream, args=(agent_process, "AGENT"), daemon=True).start()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Python script: {e}")

    # Update state tracker
    agent_state["running"] = True
    agent_state["started_at"] = datetime.now().isoformat()
    agent_state["trades_today"] = 0
    agent_state["pnl_today"] = 0.0

    return {
        "success": True,
        "message": f"AI Agent started in {current_mode.upper()} mode",
        # normalize mode to lowercase for consumers
        "mode": current_mode.lower(),
        "capital_allocation_pct": capital_pct,
        "started_at": agent_state["started_at"],
        "pid": agent_process.pid,
        "script": script_name
    }

def _stop_agent_core():
    """Core logic to stop the AI agent subprocess"""
    global agent_state, agent_process
    
    if not agent_process or agent_process.poll() is not None:
        agent_state["running"] = False
        
        # Fallback: forcefully kill any orphaned bot processes
        killed_orphan = False
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and 'run_live_paper_bot.py' in ' '.join(proc.info['cmdline']):
                    proc.kill()
                    killed_orphan = True
        except Exception:
            pass
            
        if killed_orphan:
            return {"success": True, "message": "Orphaned AI Agent was successfully terminated"}
        return {"success": False, "message": "AI Agent is not currently running"}
        
    try:
        import psutil
        parent = psutil.Process(agent_process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        
        agent_process.wait(timeout=3)
        agent_process = None
    except Exception as e:
        # Fallback to direct kill
        if agent_process:
            agent_process.kill()
            agent_process = None
            
    agent_state["running"] = False
    agent_state["last_signal"] = "Stopped by user via dashboard"
    return {"success": True, "message": "AI Agent successfully terminated"}


# Primary endpoints (new naming)
@app.post("/api/agent/start")
async def start_agent(request: Request, background_tasks: BackgroundTasks):
    """Start the AI trading agent.

    The frontend may send a JSON body containing ``mode`` ("paper" or "live").
    This value is passed through to the core logic so that the user can
    explicitly launch paper mode even if the stored mode is different.
    """
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    mode_override = body.get('mode') if isinstance(body, dict) else None
    return _start_agent_core(background_tasks, mode_override=mode_override)


@app.post("/api/agent/stop")
async def stop_agent_endpoint():
    """Stop the AI trading agent"""
    return _stop_agent_core()


# Legacy aliases (backward compat)
@app.post("/api/bot/start")
async def start_bot_legacy(background_tasks: BackgroundTasks):
    """[Legacy] Start the AI trading agent — use /api/agent/start instead"""
    return _start_agent_core(background_tasks)


@app.post("/api/bot/stop")
async def stop_bot_legacy():
    """[Legacy] Stop the AI trading agent — use /api/agent/stop instead"""
    return _stop_agent_core()


# ============== Upstox OAuth Authentication ==============

CREDS_FILE = Path("creds.json")
ACCESS_TOKEN_FILE = Path("access_token.json")

def _load_creds():
    """Load credentials from creds.json"""
    if CREDS_FILE.exists():
        with open(CREDS_FILE, "r") as f:
            return json.load(f)
    return {"auth": {}, "api": {"headers": {"accept": "application/json", "Api-Version": "2.0", "Authorization": ""}}}

def _save_creds(creds):
    """Save credentials to creds.json"""
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=4)


@app.post("/api/auth/configure")
async def configure_auth(request: Request):
    """
    Save API key/secret and return Upstox OAuth authorization URL.
    Frontend calls this when user clicks 'Connect Demat Account'.
    The request should include the user's JWT in the Authorization header
    so we can associate the link with that user.
    """
    try:
        body = await request.json()
        api_key = body.get("api_key", "").strip()
        api_secret = body.get("api_secret", "").strip()
        redirect_uri = body.get("redirect_uri", "http://localhost:5000/api/auth/callback").strip()

        if not api_key or not api_secret:
            return JSONResponse(status_code=400, content={"detail": "API Key and Secret are required"})

        # Attempt to get user id from Authorization header
        auth_header = request.headers.get("Authorization", "")
        user_id = None
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            payload = AuthManager.verify_token(token)
            if payload:
                user_id = payload.get("user_id")

        # Save to creds.json
        creds = _load_creds()
        creds["auth"]["api_key"] = api_key
        creds["auth"]["api_secret"] = api_secret
        creds["auth"]["redirect_uri"] = redirect_uri
        if user_id:
            # remember who initiated the link so callback can update DB
            creds["linking_user_id"] = user_id
        _save_creds(creds)

        # Build Upstox OAuth authorization URL
        auth_url = (
            f"https://api-v2.upstox.com/login/authorization/dialog"
            f"?response_type=code"
            f"&client_id={api_key}"
            f"&redirect_uri={redirect_uri}"
        )

        return {
            "success": True,
            "message": "Credentials saved. Redirect user to auth_url.",
            "auth_url": auth_url
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.get("/api/auth/callback")
async def auth_callback(code: str = None):
    """
    OAuth callback from Upstox. Exchanges authorization code for access token.
    Upstox redirects here after user logs in.
    """
    if not code:
        return HTMLResponse(content="""
        <html><body style='font-family:sans-serif;text-align:center;padding:60px;'>
        <h2 style='color:red;'>Authentication Failed</h2>
        <p>No authorization code received from Upstox.</p>
        <p><a href='/frontend/demat/investment.html'>Return to Dashboard</a></p>
        </body></html>
        """)

    try:
        creds = _load_creds()
        api_key = creds.get("auth", {}).get("api_key", "")
        api_secret = creds.get("auth", {}).get("api_secret", "")
        redirect_uri = creds.get("auth", {}).get("redirect_uri", "http://localhost:5000/api/auth/callback")

        if not api_key or not api_secret:
            return HTMLResponse(content="""
            <html><body style='font-family:sans-serif;text-align:center;padding:60px;'>
            <h2 style='color:red;'>Configuration Missing</h2>
            <p>API Key and Secret not found. Please configure them first.</p>
            </body></html>
            """)

        # Exchange code for access token
        import requests as http_requests
        token_url = "https://api.upstox.com/v2/login/authorization/token"
        token_data = {
            "code": code,
            "client_id": api_key,
            "client_secret": api_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        token_headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        token_response = http_requests.post(token_url, data=token_data, headers=token_headers)

        if token_response.status_code == 200:
            token_json = token_response.json()
            access_token = token_json.get("access_token", "")

            # Save access token to creds.json
            creds["auth"]["access_token"] = access_token
            creds["auth"]["code"] = code
            creds["api"]["headers"]["Authorization"] = f"Bearer {access_token}"
            _save_creds(creds)

            # Also save to access_token.json for backward compat
            with open(ACCESS_TOKEN_FILE, "w") as f:
                json.dump({"access_token": access_token}, f)

            # If this link was initiated by a logged-in user, update DB
            linking_user = creds.get("linking_user_id")
            if linking_user and DB_AVAILABLE:
                try:
                    # use api_key as surrogate email if we don't have one
                    upstox_identifier = creds.get("auth", {}).get("client_id", "")
                    update_upstox_link(linking_user, upstox_identifier)
                except Exception as e:
                    print(f"[WARN] Failed to mark user as linked: {e}")
                finally:
                    # remove the temporary field so future config calls are clean
                    creds.pop("linking_user_id", None)
                    _save_creds(creds)

            return HTMLResponse(content="""
            <html><body style='font-family:sans-serif;text-align:center;padding:60px;background:#f0fdf4;'>
            <h2 style='color:#10b981;'>Authentication Successful!</h2>
            <p>Your Upstox account has been connected.</p>
            <p>You can close this tab and return to the UPVEST dashboard.</p>
            <script>
                // Notify opener window
                if (window.opener) {
                    window.opener.postMessage({type: 'upstox_auth_success'}, '*');
                }
            </script>
            </body></html>
            """)
        else:
            error_detail = token_response.text
            return HTMLResponse(content=f"""
            <html><body style='font-family:sans-serif;text-align:center;padding:60px;background:#fef2f2;'>
            <h2 style='color:#ef4444;'>Authentication Failed</h2>
            <p>Could not exchange code for access token.</p>
            <p style='color:#666;font-size:14px;'>{error_detail}</p>
            <p><a href='/frontend/demat/investment.html'>Return to Dashboard</a></p>
            </body></html>
            """)

    except Exception as e:
        return HTMLResponse(content=f"""
        <html><body style='font-family:sans-serif;text-align:center;padding:60px;background:#fef2f2;'>
        <h2 style='color:#ef4444;'>Error</h2>
        <p>{str(e)}</p>
        <p><a href='/frontend/demat/investment.html'>Return to Dashboard</a></p>
        </body></html>
        """)


@app.get("/api/auth/status")
async def auth_status(authorization: Optional[str] = None):
    """Check if Upstox account is connected (has valid access token).
    If a JWT token is provided in the Authorization header we also look up
    the corresponding user record and report the per-user "upstox_linked"
    flag.  This lets the frontend display linkage status even when
    multiple users are using the same backend.
    """
    try:
        creds = _load_creds()
        access_token = creds.get("auth", {}).get("access_token", "")
        api_key = creds.get("auth", {}).get("api_key", "")

        connected = bool(access_token and api_key)
        result = {
            "connected": connected,
            "broker": "Upstox" if connected else None,
            "api_key_set": bool(api_key),
            "token_set": bool(access_token)
        }

        # if a user token is supplied, include db status
        if authorization and DB_AVAILABLE:
            try:
                token = authorization.replace("Bearer ", "")
                payload = AuthManager.verify_token(token)
                if payload:
                    user = get_user_by_email(payload.get('email'))
                    if user:
                        result["upstox_linked"] = bool(user.get("upstox_linked"))
                        result["upstox_email"] = user.get("upstox_email")
            except Exception:
                pass

        return result
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.post("/api/auth/disconnect")
async def auth_disconnect():
    """Disconnect Upstox account (clear access token)"""
    try:
        creds = _load_creds()
        creds["auth"]["access_token"] = ""
        creds["auth"]["code"] = ""
        creds["api"]["headers"]["Authorization"] = ""
        _save_creds(creds)

        # Remove access_token.json if exists
        if ACCESS_TOKEN_FILE.exists():
            ACCESS_TOKEN_FILE.unlink()

        return {"success": True, "message": "Account disconnected successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/api/ai/predict", response_model=PredictionResponse)
async def get_ai_prediction(request: PredictionRequest):
    """Get AI prediction for a stock"""
    try:
        from trading_execution import fetch_historical_data
        from ai_agent.ai_decision_engine import AIDecisionEngine
        from strategy_engine import StrategyEngine
        
        # Fetch data
        df = fetch_historical_data(request.symbol, interval=request.interval, days=200)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for symbol")
        
        # Get strategy signals
        aggregated = StrategyEngine.get_all_signals(df)
        strategy_signal = aggregated['consensus']
        
        # Load AI engine
        model_path = 'data/trained_models/lstm_best.pth'
        if os.path.exists(model_path):
            ai_engine = AIDecisionEngine(model_path=model_path, use_gpu=False)
            
            # Get AI decision
            stock_name = request.symbol.split('|')[0].replace('NSE_EQ:', '')
            ai_decision = ai_engine.make_ensemble_decision(
                df, 
                strategy_signal, 
                f"aggregated_{aggregated['buy_count']}B_{aggregated['sell_count']}S",
                stock_name=stock_name,
                use_sentiment=True,
                use_rl=False
            )
            
            return PredictionResponse(
                symbol=request.symbol,
                signal=ai_decision.get('action', ai_decision.get('signal', strategy_signal)),
                confidence=ai_decision['confidence'],
                predicted_price=ai_decision.get('ai_prediction', {}).get('predicted_price'),
                price_change_pct=ai_decision.get('ai_prediction', {}).get('price_change_pct'),
                models_used=ai_decision.get('models_used', []),
                reason=ai_decision['reason']
            )
        else:
            # Fallback to strategy-only
            return PredictionResponse(
                symbol=request.symbol,
                signal=strategy_signal,
                confidence=aggregated['confidence'],
                predicted_price=None,
                price_change_pct=None,
                models_used=['Strategy Ensemble'],
                reason=f"Based on {aggregated['buy_count']} BUY, {aggregated['sell_count']} SELL, {aggregated['hold_count']} HOLD signals"
            )
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"AI modules not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Trading Mode & Risk Endpoints ==============

@app.get("/api/trading-mode")
async def get_trading_mode():
    """Get current trading mode and capital allocation"""
    if not MODE_MANAGER_AVAILABLE:
        return {"mode": "paper", "capital_allocation_pct": 100.0, "can_switch_to_live": False}
    
    mode_mgr = get_mode_manager()
    return mode_mgr.get_status()


@app.post("/api/trading-mode/switch")
async def switch_trading_mode(mode: str, confirmed: bool = False):
    """Switch between paper and live trading modes"""
    if not MODE_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Mode manager not available")
    
    if bot_state["running"]:
        raise HTTPException(status_code=400, detail="Cannot switch mode while bot is running. Stop the bot first.")
    
    mode_mgr = get_mode_manager()
    success, message = mode_mgr.set_mode(mode, confirmed=confirmed)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message, "current_mode": mode_mgr.get_mode()}


@app.post("/api/trading-mode/capital")
async def set_capital_allocation(pct: float):
    """Set capital allocation percentage (10-100)"""
    if not MODE_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Mode manager not available")
    
    mode_mgr = get_mode_manager()
    success, message = mode_mgr.set_capital_allocation(pct)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message, "capital_allocation_pct": pct}


@app.get("/api/trading-mode/strategy")
async def get_strategy_mode():
    """Get current strategy mode (stock or intraday)"""
    if not MODE_MANAGER_AVAILABLE:
        return {"strategy_mode": "stock", "active_interval": "day", "product_type": "D (CNC)"}
    mode_mgr = get_mode_manager()
    return {
        "strategy_mode": mode_mgr.get_strategy_mode(),
        "active_interval": mode_mgr.get_active_interval(),
        "product_type": "I (MIS)" if mode_mgr.is_intraday_mode() else "D (CNC)"
    }


@app.post("/api/trading-mode/strategy")
async def set_strategy_mode(mode: str):
    """
    Switch strategy mode between 'stock' and 'intraday'.

      stock    -> daily candles, CNC delivery orders (original behaviour, fully intact)
      intraday -> 30-min candles, MIS orders, auto square-off at 3:20 PM

    Bot must NOT be running when switching.
    """
    if not MODE_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Mode manager not available")
    if bot_state["running"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot switch strategy mode while bot is running. Stop the bot first."
        )
    mode_mgr = get_mode_manager()
    success, message = mode_mgr.set_strategy_mode(mode)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {
        "success": True,
        "message": message,
        "strategy_mode": mode_mgr.get_strategy_mode(),
        "active_interval": mode_mgr.get_active_interval(),
        "product_type": "I (MIS)" if mode_mgr.is_intraday_mode() else "D (CNC)"
    }


@app.get("/api/risk/status")
async def get_risk_status():
    """Get current risk manager status"""
    try:
        risk_mgr = RiskManager()
        status = risk_mgr.get_status()
        return {"success": True, **status}
    except Exception as e:
        return {
            "success": False,
            "trades_today": 0,
            "circuit_breaker_active": False,
            "error": str(e)
        }


@app.get("/api/live/portfolio")
async def get_live_portfolio():
    """Get live portfolio data from Upstox"""
    try:
        from live_portfolio_manager import LivePortfolioManager
        
        capital_pct = 100.0
        if MODE_MANAGER_AVAILABLE:
            capital_pct = get_mode_manager().get_capital_allocation()
        
        manager = LivePortfolioManager(capital_allocation_pct=capital_pct)
        
        return {
            "success": True,
            "balance": manager.get_balance(),
            "portfolio_value": manager.get_portfolio_value(),
            "positions": manager.get_positions(),
            "holdings": manager.get_holdings(),
            "statistics": manager.get_statistics(),
            "mode": "live"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch live portfolio: {str(e)}")


# ============== Paper Trading Endpoints ==============

@app.get("/api/paper-trading/transactions")
async def get_paper_trading_transactions(limit: int = 50):
    """Get paper trading transaction history from portfolio JSON."""
    try:
        from pathlib import Path
        
        # Load portfolio data
        portfolio_file = Path('data/paper_trading_balance.json')
        
        if not portfolio_file.exists():
            return {
                "success": True,
                "transactions": [],
                "portfolio": None,
                "message": "No paper trading data available yet"
            }
        
        with open(portfolio_file, 'r') as f:
            portfolio_data = json.load(f)
        
        # Get trade history
        trade_history = portfolio_data.get('trade_history', [])
        
        # Limit and reverse (most recent first)
        recent_trades = list(reversed(trade_history[-limit:]))
        
        # Calculate current portfolio value with live prices
        cash = portfolio_data.get('cash', 0)
        positions = portfolio_data.get('positions', {})
        
        from market_data_fetcher import get_market_data
        
        position_value = 0.0
        updated_positions = []
        
        for symbol, pos in positions.items():
            stock_name = pos.get('stock_name', symbol)
            # Try to get live price
            try:
                current_price, _ = get_market_data(symbol, interval="5minute", days=1, stock_name=stock_name)
                if not current_price:
                    current_price = pos.get('current_price', pos['avg_price'])
                else:
                    print(f"[DEBUG] Fetched live price for {stock_name}: {current_price} (Avg: {avg_price})")
            except Exception as e:
                print(f"[DEBUG] Error fetching price for {stock_name}: {e}")
                current_price = pos.get('current_price', pos['avg_price'])
                
            qty = pos['qty']
            avg_price = pos['avg_price']
            pos_val = qty * current_price
            position_value += pos_val
            
            # Add to updated positions list for the summary
            updated_positions.append({
                'symbol': symbol,
                'stock_name': pos.get('stock_name', symbol),
                'qty': qty,
                'avg_price': avg_price,
                'current_price': current_price,
                'pnl': (current_price - avg_price) * qty
            })
        
        total_value = cash + position_value
        initial_capital = portfolio_data.get('initial_capital', 100000)
        total_pnl = total_value - initial_capital
        
        # Calculate statistics dynamically from history
        total_trades = len(trade_history)
        winning_trades = sum(1 for t in trade_history if t.get('pnl', 0) > 0)
        losing_trades = sum(1 for t in trade_history if t.get('pnl', 0) < 0)
        
        # Calculate Today's P&L
        # Today's P&L = (Current Total Value) - (Value at the start of the day)
        # We can estimate start of day value from the balance_after of the last trade before today
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Find last trade before today
        last_trade_before_today = None
        for t in reversed(trade_history):
            if not t.get('timestamp', '').startswith(today_str):
                last_trade_before_today = t
                break
        
        start_of_day_value = last_trade_before_today.get('balance_after', initial_capital) if last_trade_before_today else initial_capital
        todays_pnl = total_value - start_of_day_value

        # Portfolio summary
        portfolio_summary = {
            'cash': cash,
            'position_value': position_value,
            'total_value': total_value,
            'initial_capital': initial_capital,
            'total_pnl': total_pnl,
            'todays_pnl': todays_pnl,
            'pnl_pct': (total_pnl / initial_capital * 100) if initial_capital > 0 else 0,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'open_positions': len(positions),
            'positions': updated_positions,
            'last_updated': portfolio_data.get('last_updated', '')
        }
        
        return {
            "success": True,
            "transactions": recent_trades,
            "portfolio": portfolio_summary,
            "message": f"Loaded {len(recent_trades)} transactions"
        }
        
    except Exception as e:
        print(f"Error loading paper trading data: {e}")
        return {
            "success": False,
            "transactions": [],
            "portfolio": None,
            "message": f"Error: {str(e)}",
        }

# ============== User Authentication Endpoints ==============

class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

@app.post("/api/auth/register", response_model=AuthResponse)
async def register_user(request: RegisterRequest):
    """Register a new user account"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Validate email format
        if not AuthManager.validate_email(request.email):
            return AuthResponse(
                success=False,
                message="Invalid email format"
            )
        
        # Validate password strength
        is_strong, error_msg = AuthManager.validate_password_strength(request.password)
        if not is_strong:
            return AuthResponse(
                success=False,
                message=error_msg
            )
        
        # Check if user already exists
        existing_user = get_user_by_email(request.email)
        if existing_user:
            return AuthResponse(
                success=False,
                message="User with this email already exists"
            )
        
        # Hash password
        password_hash = AuthManager.hash_password(request.password)
        
        # Create user
        user_id = create_user(request.email, request.full_name, password_hash)
        if not user_id:
            return AuthResponse(
                success=False,
                message="Failed to create user account"
            )
        
        # Generate JWT token
        token = AuthManager.generate_token(user_id, request.email, request.full_name)
        
        return AuthResponse(
            success=True,
            message="Account created successfully",
            token=token,
            user={
                "id": user_id,
                "email": request.email,
                "full_name": request.full_name
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login", response_model=AuthResponse)
async def login_user(request: LoginRequest):
    """Login user and return JWT token"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get user by email
        user = get_user_by_email(request.email)
        if not user:
            return AuthResponse(
                success=False,
                message="Invalid email or password"
            )
        
        # Verify password
        if not AuthManager.verify_password(request.password, user['password_hash']):
            return AuthResponse(
                success=False,
                message="Invalid email or password"
            )
        
        # Check if account is active
        if not user['is_active']:
            return AuthResponse(
                success=False,
                message="Account is deactivated"
            )
        
        # Generate JWT token
        token = AuthManager.generate_token(
            user['id'],
            user['email'],
            user['full_name']
        )
        
        return AuthResponse(
            success=True,
            message="Login successful",
            token=token,
            user={
                "id": user['id'],
                "email": user['email'],
                "full_name": user['full_name'],
                "upstox_linked": user['upstox_linked']
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me")
async def get_current_user(authorization: Optional[str] = None):
    """Get current user profile from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        
        # Verify token
        payload = AuthManager.verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Get user from database
        user = get_user_by_email(payload['email'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user['id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "upstox_linked": user['upstox_linked'],
            "upstox_email": user['upstox_email'],
            "created_at": user['created_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Bot Control Endpoints ==============

class BotStartRequest(BaseModel):
    mode: str = "paper"  # paper or live

@app.post("/api/bot/start")
async def start_trading_bot(request: BotStartRequest):
    """Start the trading bot as a background process"""
    global bot_process, bot_start_time, bot_mode
    
    # Check if already running
    if bot_process and bot_process.poll() is None:
        return {
            "success": False,
            "message": "Bot is already running",
            "pid": bot_process.pid
        }
    
    try:
        # Get trading mode from request
        bot_mode = request.mode
        
        # Start trading_execution_ai.py or paper_bot.py based on mode
        script = "paper_bot.py" if bot_mode == "paper" else "trading_execution_ai.py"
        
        bot_process = subprocess.Popen(
            ["python", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        bot_start_time = datetime.now()
        
        return {
            "success": True,
            "message": f"Trading bot started successfully in {bot_mode} mode",
            "pid": bot_process.pid,
            "status": "running",
            "mode": bot_mode
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to start bot: {str(e)}"
        }


@app.post("/api/bot/stop")
async def stop_trading_bot():
    """Stop the trading bot gracefully"""
    global bot_process, bot_start_time
    
    if not bot_process or bot_process.poll() is not None:
        return {
            "success": False,
            "message": "Bot is not running"
        }
    
    try:
        # Create stop signal file
        with open("stop_signal.txt", "w") as f:
            f.write("STOP")
            
        return {
            "success": True,
            "message": "Stop signal sent. Bot will square off and exit shortly.",
            "status": "stopping"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to stop bot: {str(e)}"
        }


@app.get("/api/bot/status")
async def get_bot_status():
    """Get current bot status"""
    global bot_process, bot_start_time, bot_mode
    
    is_running = bot_process and bot_process.poll() is None
    
    uptime = None
    if is_running and bot_start_time:
        uptime_seconds = (datetime.now() - bot_start_time).total_seconds()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        uptime = f"{hours}h {minutes}m"
    
    return {
        "success": True,
        "status": "running" if is_running else "stopped",
        "pid": bot_process.pid if is_running else None,
        "uptime": uptime,
        "mode": bot_mode if is_running else None
    }



# ============== Paper Trading API Endpoints ==============

@app.get("/api/paper/trades")
async def get_paper_trades(limit: int = 20):
    """Get recent paper trades — called by dashboard 'Recent Transactions' table."""
    try:
        from paper_portfolio_manager import PaperPortfolioManager
        paper_portfolio = PaperPortfolioManager()
        
        if paper_portfolio and paper_portfolio.trade_history:
            # Sort by timestamp descending
            trades = sorted(paper_portfolio.trade_history, key=lambda x: x.get('timestamp', ''), reverse=True)
            limited_trades = trades[:limit]
            
            # Format to match frontend expectations
            formatted = []
            for t in limited_trades:
                formatted.append({
                    "timestamp": t.get("timestamp", ""),
                    "symbol": t.get("symbol", ""),
                    "stock_name": t.get("stock_name", t.get("symbol", "")),
                    "signal": t.get("side", ""),
                    "quantity": t.get("qty", 0),
                    "price": t.get("price", 0.0),
                    "status": "SUCCESS"
                })
            return {"success": True, "trades": formatted, "count": len(formatted)}
        return {"success": True, "trades": [], "count": 0}
    except Exception as e:
        print(f"[API] Error reading paper trades: {e}")
        return {"success": False, "trades": [], "count": 0}


@app.get("/api/trades/recent")
async def get_recent_trades(limit: int = 20):
    """Get recent trades (live or paper) — called by dashboard in live mode."""
    # some older runs lacked the helper when the module was imported early;
    # prefer public API and fall back gracefully.
    try:
        trades = get_all_trades(limit=limit)
    except NameError:
        trades = []

    # sanitize values so JSON encoder doesn't choke on NaN/inf
    import math
    for t in trades:
        for k, v in t.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                t[k] = None
    return {"success": True, "trades": trades, "count": len(trades)}


# ============== Paper Trading API Endpoints ==============

@app.get("/api/paper/portfolio")
async def get_paper_portfolio():
    """Get paper trading portfolio summary — called by dashboard 'Investment Overview'."""
    try:
        from paper_portfolio_manager import PaperPortfolioManager
        paper_portfolio = PaperPortfolioManager()
        import json

        if paper_portfolio:
            stats = paper_portfolio.get_statistics()
            # Compute invested amount and current value using existing positions
            invested = sum([pos['qty'] * pos['avg_price'] for pos in paper_portfolio.positions.values()])
            current_val = paper_portfolio.cash + invested

            pnl = stats.get('total_profit', 0) - stats.get('total_loss', 0)

            # Count trades today
            today_str = datetime.now().strftime("%Y-%m-%d")
            trades_today = len([t for t in paper_portfolio.trade_history if t.get('timestamp', '').startswith(today_str)])

            return {
                "success": True,
                "balance": paper_portfolio.cash,
                "initial_capital": paper_portfolio.initial_capital,
                "total_pnl": pnl,
                "total_invested": invested,
                "current_value": current_val,
                "total_returns": pnl,
                "pnl": pnl,
                "open_positions": stats.get('open_positions', 0),
                "trades_today": trades_today,
                "total_trades": stats.get('total_trades', 0),
                "mode": "paper"
            }
        return {"success": False, "message": "Paper portfolio uninitialized"}
    except Exception as e:
        print(f"[API] Error returning paper portfolio: {e}")
        return {"success": False, "balance": 0, "total_returns": 0, "current_value": 0}

@app.get("/api/paper/positions")
async def get_paper_positions():
    """Get current open positions with live P&L for dashboard trade details"""
    try:
        from paper_portfolio_manager import PaperPortfolioManager
        from market_data_fetcher import MarketDataFetcher
        
        portfolio = PaperPortfolioManager()
        fetcher = MarketDataFetcher()
        
        positions = []
        for symbol, pos in portfolio.positions.items():
            # Determine ticker from symbol
            ticker = None
            stock_name = pos.get('stock_name', symbol)
            
            if "Nifty 50" in symbol or "NSEI" in symbol:
                ticker = "^NSEI"
                stock_name = "NIFTY 50"
            elif "Nifty Bank" in symbol or "NSEBANK" in symbol:
                ticker = "^NSEBANK"
                stock_name = "NIFTY BANK"
            
            # Get current price
            current_price = pos.get('current_price', pos.get('avg_price', 0.0))
            if ticker:
                try:
                    price_data = fetcher.get_current_price(ticker)
                    if price_data and 'price' in price_data:
                        current_price = price_data['price']
                except Exception:
                    pass
            
            positions.append({
                'stock_name': stock_name,
                'symbol': symbol,
                'action': 'BUY',  # Open positions are always BUY
                'quantity': pos.get('qty', pos.get('quantity', 0)),
                'entry_price': pos.get('avg_price', 0.0),
                'current_price': current_price,
            })
        
        return {"success": True, "positions": positions}
        
    except Exception as e:
        return {"success": False, "error": str(e), "positions": []}

@app.get("/api/paper/positions")
async def get_paper_positions():
    """Get current open positions with live P&L for dashboard trade details"""
    try:
        from paper_portfolio_manager import PaperPortfolioManager
        from market_data_fetcher import MarketDataFetcher
        
        portfolio = PaperPortfolioManager()
        fetcher = MarketDataFetcher()
        
        positions = []
        for symbol, pos in portfolio.positions.items():
            # Determine ticker from symbol
            ticker = None
            stock_name = pos.get('stock_name', symbol)
            
            if "Nifty 50" in symbol or "NSEI" in symbol:
                ticker = "^NSEI"
                stock_name = "NIFTY 50"
            elif "Nifty Bank" in symbol or "NSEBANK" in symbol:
                ticker = "^NSEBANK"
                stock_name = "NIFTY BANK"
            
            # Get current price
            current_price = pos.get('current_price', pos.get('avg_price', 0.0))
            if ticker:
                try:
                    price_data = fetcher.get_current_price(ticker)
                    if price_data and 'price' in price_data:
                        current_price = price_data['price']
                except Exception:
                    pass
            
            positions.append({
                'stock_name': stock_name,
                'symbol': symbol,
                'action': 'BUY',  # Open positions are always BUY
                'quantity': pos.get('qty', pos.get('quantity', 0)),
                'entry_price': pos.get('avg_price', 0.0),
                'current_price': current_price,
            })
        
        return {"success": True, "positions": positions}
        
    except Exception as e:
        return {"success": False, "error": str(e), "positions": []}


# ─── Analytics Endpoints ──────────────────────────────────────────────────────

# Import performance analytics module
try:
    from performance_analytics import (
        get_day_wise_analytics as _get_day_wise,
        get_performance_metrics as _get_perf_metrics,
        calculate_strategy_performance
    )
    ANALYTICS_AVAILABLE = True
except ImportError as e:
    ANALYTICS_AVAILABLE = False
    print(f"[WARN] Performance analytics not available: {e}")


@app.get("/api/analytics/daily")
async def get_daily_analytics(days: int = 30):
    """
    Get day-wise analytics: P&L, trades, win rate per day.
    Used by the Analytics Dashboard.
    """
    if not ANALYTICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Analytics module not available")
    try:
        data = _get_day_wise(days=days)
        return {"success": True, "days": days, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/performance")
async def get_performance_summary(days: int = 30):
    """
    Get comprehensive performance metrics:
    Sharpe ratio, max drawdown, win rate, streaks, best/worst day.
    """
    if not ANALYTICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Analytics module not available")
    try:
        metrics = _get_perf_metrics(days=days)
        return {"success": True, **metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/strategies")
async def get_strategy_performance():
    """
    Get per-strategy performance: win rate, total P&L, avg P&L per trade.
    """
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        trades = get_all_trades(limit=500)
        result = calculate_strategy_performance(trades)
        return {"success": True, "strategies": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Telegram Config Endpoints ────────────────────────────────────────────────

TELEGRAM_CONFIG_FILE = Path("telegram_config.json")


class TelegramConfigModel(BaseModel):
    bot_token: str
    chat_id: str
    telegram_username: Optional[str] = None


@app.get("/api/telegram/config")
async def get_telegram_config():
    """Get saved Telegram bot token and chat ID (token is masked for security)."""
    try:
        if TELEGRAM_CONFIG_FILE.exists():
            with open(TELEGRAM_CONFIG_FILE) as f:
                cfg = json.load(f)
            token = cfg.get("bot_token", "")
            chat_id = cfg.get("chat_id", "")
            enabled = bool(token and chat_id and not token.startswith("YOUR_"))
            # Mask token for security (show only last 6 chars)
            masked = ("*" * (len(token) - 6) + token[-6:]) if len(token) > 6 else token
            return {
                "success": True,
                "bot_token": masked,
                "chat_id": chat_id,
                "telegram_username": cfg.get("telegram_username", ""),
                "enabled": enabled
            }
        return {"success": True, "bot_token": "", "chat_id": "", "enabled": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/telegram/config")
async def save_telegram_config(config: TelegramConfigModel):
    """Save Telegram bot token and chat ID to telegram_config.json."""
    try:
        cfg = {
            "bot_token": config.bot_token.strip(),
            "chat_id": config.chat_id.strip(),
            "telegram_username": (config.telegram_username or "").strip()
        }
        with open(TELEGRAM_CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
        return {"success": True, "message": "Telegram config saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/telegram/test")
async def test_telegram_config():
    """Send a test message via Telegram to verify the config."""
    import urllib.request
    import urllib.error

    try:
        if not TELEGRAM_CONFIG_FILE.exists():
            raise HTTPException(status_code=400, detail="No Telegram config saved. Save config first.")

        with open(TELEGRAM_CONFIG_FILE) as f:
            cfg = json.load(f)

        token = cfg.get("bot_token", "")
        chat_id = cfg.get("chat_id", "")

        if not token or not chat_id or token.startswith("YOUR_"):
            raise HTTPException(status_code=400, detail="Invalid Telegram config. Please save valid token and chat ID.")

        # Send test message via Telegram Bot API
        msg = "UPVEST Agent: Test message! Your Telegram notifications are working correctly."
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": msg}).encode()

        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())

        if result.get("ok"):
            return {"success": True, "message": "Test message sent successfully!"}
        else:
            raise HTTPException(status_code=400, detail=f"Telegram API error: {result.get('description', 'Unknown')}")

    except HTTPException:
        raise
    except urllib.error.URLError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
#  FIX #2 — TOKEN EXPIRY CHECK
# ============================================================

@app.get("/api/auth/token-status")
async def get_token_status():
    """Check if the Upstox access token is still valid."""
    try:
        token_file = Path("access_token.json")
        creds_file = Path("creds.json")
        access_token = ""
        generated_at_str = None

        if token_file.exists():
            with open(token_file) as f:
                td = json.load(f)
                access_token = td.get("access_token", "")
                generated_at_str = td.get("generated_at")

        if not access_token and creds_file.exists():
            with open(creds_file) as f:
                cd = json.load(f)
                access_token = cd.get("auth", {}).get("access_token", "")

        if not access_token:
            return {"valid": False, "needs_relogin": True,
                    "message": "No access token. Please connect your Demat account.",
                    "expires_in_hours": 0, "hours_old": None}

        if generated_at_str:
            try:
                gen_time = datetime.strptime(generated_at_str, "%Y-%m-%d %H:%M:%S")
                age_hours = (datetime.now() - gen_time).total_seconds() / 3600
                expires_in = max(0, 24 - age_hours)
                is_valid = age_hours < 23
                return {"valid": is_valid, "needs_relogin": not is_valid,
                        "message": "Token valid" if is_valid else f"Token expired ({age_hours:.1f}h old). Re-login required.",
                        "expires_in_hours": round(expires_in, 1), "hours_old": round(age_hours, 1)}
            except Exception:
                pass

        return {"valid": True, "needs_relogin": False,
                "message": "Token present (age unknown — assumed valid)",
                "expires_in_hours": None, "hours_old": None}
    except Exception as e:
        return {"valid": False, "needs_relogin": True, "message": str(e), "expires_in_hours": 0}


# ============================================================
#  FIX #3 — DASHBOARD TRANSACTION & PORTFOLIO ENDPOINTS
# ============================================================

def _get_db_trades(limit: int = 20) -> list:
    """Read recent trades from SQLite database."""
    try:
        from database_manager import DB_PATH
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        trades = []
        for row in rows:
            t = dict(row)
            if "timestamp" in t and t["timestamp"]:
                t["timestamp"] = str(t["timestamp"])
            trades.append(t)
        return trades
    except Exception as e:
        print(f"[DB] Error reading trades: {e}")
        return []

def _get_db_portfolio_summary() -> dict:
    """Compute portfolio summary from SQLite database."""
    try:
        from database_manager import DB_PATH
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM trades WHERE date=?", (today,))
        trades_today = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM trades")
        total_trades = cursor.fetchone()[0] or 0
        cursor.execute("SELECT * FROM daily_summary ORDER BY date DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"success": True, "balance": row[3], "initial_capital": row[2],
                    "total_pnl": row[4], "total_invested": row[2], "current_value": row[3],
                    "total_returns": row[4], "pnl": row[4], "open_positions": row[10] if len(row) > 10 else 0,
                    "trades_today": trades_today, "total_trades": total_trades,
                    "mode": row[14] if len(row) > 14 else "paper"}
        else:
            return {"success": True, "balance": 100000.0, "initial_capital": 100000.0,
                    "total_pnl": 0.0, "total_invested": 100000.0, "current_value": 100000.0,
                    "total_returns": 0.0, "pnl": 0.0, "open_positions": 0, "trades_today": trades_today,
                    "total_trades": total_trades, "mode": "paper"}
    except Exception as e:
        print(f"[DB] Error reading portfolio: {e}")
        return {"success": False, "balance": 0, "total_pnl": 0, "pnl": 0, "total_returns": 0,
                "total_invested": 0, "current_value": 0, "open_positions": 0,
                "trades_today": 0, "total_trades": 0}


@app.get("/api/portfolio/overview")
async def get_portfolio_overview():
    """Get live portfolio overview (DB + agent state)."""
    summary = _get_db_portfolio_summary()
    summary["agent_running"] = agent_state.get("running", False)
    summary["agent_pnl_today"] = agent_state.get("pnl_today", 0.0)
    summary["agent_trades_today"] = agent_state.get("trades_today", 0)
    return summary


@app.get("/api/trades/history")
async def get_trade_history(days: int = 30, limit: int = 100):
    """Get trade history for the last N days."""
    try:
        from database_manager import DB_PATH
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM trades WHERE date >= date('now', ?) ORDER BY timestamp DESC LIMIT ?",
            (f"-{days} days", limit)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        for r in rows:
            if "timestamp" in r:
                r["timestamp"] = str(r["timestamp"])
        return {"success": True, "trades": rows, "count": len(rows), "days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/daily-summary")
async def get_daily_summary_list(days: int = 30):
    """Get daily P&L summaries — used for performance chart."""
    try:
        from database_manager import DB_PATH
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM daily_summary ORDER BY date DESC LIMIT ?", (days,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return {"success": True, "summaries": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
#  FIX #4 — AUTO EXCEL EXPORT
# ============================================================

def _auto_export_excel():
    """Export all trades to Excel. Called automatically when agent stops."""
    try:
        from export_trading_data import export_all_data
        result = export_all_data()
        print(f"[EXPORT] Auto-exported to Excel: {result}")
        return result
    except Exception as e:
        print(f"[EXPORT] Auto-export failed: {e}")
        return None


@app.get("/api/export/download")
async def download_excel_export():
    """Trigger an Excel export and return the file info."""
    try:
        from export_trading_data import export_all_data
        result = export_all_data()
        if result:
            return {"success": True, "message": "Excel exported successfully",
                    "file_path": str(result), "filename": Path(result).name}
        else:
            return {"success": False, "message": "No data to export yet"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/api/export/latest")
async def get_latest_export():
    """Check if a recent export exists."""
    try:
        export_dir = Path("data/exports")
        if not export_dir.exists():
            return {"exists": False, "message": "No exports yet"}
        xlsx_files = sorted(export_dir.glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not xlsx_files:
            return {"exists": False, "message": "No exports yet"}
        latest = xlsx_files[0]
        size_kb = latest.stat().st_size // 1024
        modified = datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        return {"exists": True, "filename": latest.name, "size_kb": size_kb,
                "modified": modified, "path": str(latest)}
    except Exception as e:
        return {"exists": False, "message": str(e)}


# ============== Main Entry Point ==============
if __name__ == "__main__":
    import uvicorn

    # Initialize database
    if DB_AVAILABLE:
        initialize_database()

    print("\n" + "="*50)
    print(" UPVEST Backend API Server")
    print("="*50)
    print(f" Server: http://localhost:5000")
    print(f" API Docs: http://localhost:5000/docs")
    print(f"[SYSTEM] Database: {'Available' if DB_AVAILABLE else 'Not Available'}")
    print(f"[SYSTEM] Trading: {'Available' if TRADING_AVAILABLE else 'Not Available'}")
    print(f"[SYSTEM] Auth: {'Available' if AUTH_AVAILABLE else 'Not Available'}")
    print("="*50 + "\n")

    uvicorn.run("backend_api:app", host="0.0.0.0", port=5000, reload=True)

