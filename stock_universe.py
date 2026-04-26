"""
Stock Universe — UPVEST Trading Platform
==========================================
Central registry of 100+ NSE-listed stocks with Upstox instrument tokens.
Covers Nifty 50, Nifty Next 50, Nifty Midcap 100, and high-momentum sectors.

Each stock entry:
  symbol   : Upstox instrument token (NSE_EQ|ISIN format)
  name     : Human-readable short name
  sector   : Sector classification
  strategy : Preferred primary strategy for this stock
  interval : Preferred candle interval
  risk     : 'low' | 'medium' | 'high'
"""

# ─────────────────────────────────────────────
#  NIFTY 50  (Large Cap — Low Risk)
# ─────────────────────────────────────────────
NIFTY_50 = [
    {"symbol": "NSE_EQ|INE002A01018", "name": "RELIANCE",    "sector": "Energy",      "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE467B01029", "name": "TCS",         "sector": "IT",          "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE009A01021", "name": "INFY",        "sector": "IT",          "strategy": "breakout",       "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE040A01034", "name": "HDFCBANK",    "sector": "Banking",     "strategy": "bollinger",      "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE238A01034", "name": "AXISBANK",    "sector": "Banking",     "strategy": "bollinger",      "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE090A01021", "name": "ICICIBANK",   "sector": "Banking",     "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE397D01024", "name": "KOTAKBANK",   "sector": "Banking",     "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE585B01010", "name": "SBIN",        "sector": "Banking",     "strategy": "breakout",       "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE062A01020", "name": "BAJFINANCE",  "sector": "Finance",     "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE296A01024", "name": "BAJAJFINSV",  "sector": "Finance",     "strategy": "ma_crossover",   "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE101A01026", "name": "WIPRO",       "sector": "IT",          "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE018A01030", "name": "HINDUNILVR",  "sector": "FMCG",        "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE030A01027", "name": "NESTLEIND",   "sector": "FMCG",        "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE155A01022", "name": "ASIANPAINT",  "sector": "Consumer",    "strategy": "bollinger",      "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE021A01026", "name": "TITAN",       "sector": "Consumer",    "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE001A01036", "name": "ADANIPORTS",  "sector": "Infra",       "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE669C01036", "name": "ADANIENT",    "sector": "Conglomerate","strategy": "momentum",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE758T01015", "name": "ADANIGREEN",  "sector": "Energy",      "strategy": "breakout",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE216A01030", "name": "M&M",         "sector": "Auto",        "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE721A01013", "name": "MARUTI",      "sector": "Auto",        "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE066A01021", "name": "TATAMOTORS",  "sector": "Auto",        "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE081A01020", "name": "TATASTEEL",   "sector": "Metals",      "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE043D01016", "name": "JSWSTEEL",    "sector": "Metals",      "strategy": "bollinger",      "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE019A01038", "name": "HINDALCO",    "sector": "Metals",      "strategy": "ma_crossover",   "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE361B01024", "name": "SUNPHARMA",   "sector": "Pharma",      "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE406A01037", "name": "DRREDDY",     "sector": "Pharma",      "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE214T01019", "name": "CIPLA",       "sector": "Pharma",      "strategy": "bollinger",      "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE117A01022", "name": "DIVISLAB",    "sector": "Pharma",      "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE070A01015", "name": "ONGC",        "sector": "Energy",      "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE242A01010", "name": "BPCL",        "sector": "Energy",      "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE129A01019", "name": "GAIL",        "sector": "Energy",      "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE752E01010", "name": "POWERGRID",   "sector": "Utilities",   "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE860A01027", "name": "NTPC",        "sector": "Utilities",   "strategy": "bollinger",      "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE115A01026", "name": "COALINDIA",   "sector": "Mining",      "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE176B01034", "name": "LTIM",        "sector": "IT",          "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE018E01016", "name": "HCLTECH",     "sector": "IT",          "strategy": "breakout",       "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE683A01023", "name": "TECHM",       "sector": "IT",          "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE503A01015", "name": "ULTRACEMCO",  "sector": "Cement",      "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE070B01039", "name": "SHREECEM",    "sector": "Cement",      "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE148I01020", "name": "INDUSINDBK",  "sector": "Banking",     "strategy": "bollinger",      "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE092T01019", "name": "BHARTIARTL",  "sector": "Telecom",     "strategy": "breakout",       "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE364U01010", "name": "JIOFIN",      "sector": "Finance",     "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE028A01039", "name": "BANKBARODA",  "sector": "Banking",     "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE860H01027", "name": "TRENT",       "sector": "Retail",      "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE040A01034", "name": "HDFCLIFE",    "sector": "Insurance",   "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE726G01019", "name": "SBILIFE",     "sector": "Insurance",   "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE491A01021", "name": "EICHERMOT",   "sector": "Auto",        "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE158A01026", "name": "HEROMOTOCO",  "sector": "Auto",        "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE029A01011", "name": "APOLLOHOSP",  "sector": "Healthcare",  "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE256A01028", "name": "ZOMATO",      "sector": "Consumer",    "strategy": "momentum",       "interval": "day",      "risk": "high"},
]

# ─────────────────────────────────────────────
#  NIFTY NEXT 50  (Large-Mid Cap — Medium Risk)
# ─────────────────────────────────────────────
NIFTY_NEXT_50 = [
    {"symbol": "NSE_EQ|INE437A01024", "name": "DMART",       "sector": "Retail",      "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE040A01034", "name": "PIDILITIND",  "sector": "Chemicals",   "strategy": "rsi_reversion",  "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE481G01011", "name": "SIEMENS",     "sector": "Industrials", "strategy": "ma_crossover",   "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE585B01010", "name": "GODREJCP",    "sector": "FMCG",        "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE192A01025", "name": "DABUR",       "sector": "FMCG",        "strategy": "bollinger",      "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE200A01026", "name": "MARICO",      "sector": "FMCG",        "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE322A01013", "name": "COLPAL",      "sector": "FMCG",        "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE066A01021", "name": "TATAPOWER",   "sector": "Utilities",   "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE467B01029", "name": "MPHASIS",     "sector": "IT",          "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE318A01026", "name": "PERSISTENT",  "sector": "IT",          "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE121A01024", "name": "COFORGE",     "sector": "IT",          "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE406A01037", "name": "LUPIN",       "sector": "Pharma",      "strategy": "rsi_reversion",  "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE214T01019", "name": "TORNTPHARM",  "sector": "Pharma",      "strategy": "ma_crossover",   "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE205A01025", "name": "BIOCON",      "sector": "Pharma",      "strategy": "breakout",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE883A01011", "name": "GLENMARK",    "sector": "Pharma",      "strategy": "momentum",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE028A01039", "name": "CANBK",       "sector": "Banking",     "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE476A01014", "name": "PNB",         "sector": "Banking",     "strategy": "rsi_reversion",  "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE562A01011", "name": "FEDERALBNK",  "sector": "Banking",     "strategy": "bollinger",      "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE090A01021", "name": "BANDHANBNK",  "sector": "Banking",     "strategy": "momentum",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE774D01024", "name": "CHOLAFIN",    "sector": "Finance",     "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE721A01013", "name": "MOTHERSON",   "sector": "Auto",        "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE216A01030", "name": "ASHOKLEY",    "sector": "Auto",        "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE066A01021", "name": "BOSCHLTD",    "sector": "Auto",        "strategy": "ma_crossover",   "interval": "day",      "risk": "low"},
    {"symbol": "NSE_EQ|INE503A01015", "name": "ACC",         "sector": "Cement",      "strategy": "rsi_reversion",  "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE070B01039", "name": "AMBUJACEM",   "sector": "Cement",      "strategy": "bollinger",      "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE001A01036", "name": "CONCOR",      "sector": "Logistics",   "strategy": "ma_crossover",   "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE092T01019", "name": "IDEA",        "sector": "Telecom",     "strategy": "breakout",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE364U01010", "name": "NYKAA",       "sector": "Consumer",    "strategy": "momentum",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE860A01027", "name": "IRCTC",       "sector": "Travel",      "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE115A01026", "name": "NHPC",        "sector": "Utilities",   "strategy": "rsi_reversion",  "interval": "day",      "risk": "low"},
]

# ─────────────────────────────────────────────
#  HIGH-MOMENTUM SECTORS  (Medium-High Risk)
# ─────────────────────────────────────────────
HIGH_MOMENTUM = [
    # Defence & Aerospace
    {"symbol": "NSE_EQ|INE145H01013", "name": "HAL",         "sector": "Defence",     "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE202B01012", "name": "BEL",         "sector": "Defence",     "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE200M01013", "name": "COCHINSHIP",  "sector": "Defence",     "strategy": "breakout",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE205A01025", "name": "MAZAGON",     "sector": "Defence",     "strategy": "momentum",       "interval": "day",      "risk": "high"},
    # Renewables & Green Energy
    {"symbol": "NSE_EQ|INE758T01015", "name": "ADANIGREEN",  "sector": "Renewables",  "strategy": "breakout",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE066A01021", "name": "TATAPOWER",   "sector": "Renewables",  "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE752E01010", "name": "SJVN",        "sector": "Renewables",  "strategy": "rsi_reversion",  "interval": "day",      "risk": "medium"},
    # Railways & Infra
    {"symbol": "NSE_EQ|INE752E01010", "name": "IRFC",        "sector": "Railways",    "strategy": "momentum",       "interval": "day",      "risk": "medium"},
    {"symbol": "NSE_EQ|INE860A01027", "name": "RVNL",        "sector": "Railways",    "strategy": "breakout",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE115A01026", "name": "RAILVIKAS",   "sector": "Railways",    "strategy": "momentum",       "interval": "day",      "risk": "high"},
    # EV & New Tech
    {"symbol": "NSE_EQ|INE066A01021", "name": "TATAMOTORS",  "sector": "EV",          "strategy": "momentum",       "interval": "30minute", "risk": "high"},
    {"symbol": "NSE_EQ|INE216A01030", "name": "M&M",         "sector": "EV",          "strategy": "breakout",       "interval": "30minute", "risk": "medium"},
    # Chemicals
    {"symbol": "NSE_EQ|INE318A01026", "name": "AARTI",       "sector": "Chemicals",   "strategy": "breakout",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE121A01024", "name": "DEEPAKNTR",   "sector": "Chemicals",   "strategy": "momentum",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE406A01037", "name": "NAVINFLUOR",  "sector": "Chemicals",   "strategy": "rsi_reversion",  "interval": "day",      "risk": "medium"},
    # Hospitality & Travel (post-COVID recovery)
    {"symbol": "NSE_EQ|INE860A01027", "name": "IRCTC",       "sector": "Travel",      "strategy": "momentum",       "interval": "30minute", "risk": "medium"},
    {"symbol": "NSE_EQ|INE029A01011", "name": "INDHOTEL",    "sector": "Hospitality", "strategy": "breakout",       "interval": "day",      "risk": "medium"},
    # Consumer Discretionary
    {"symbol": "NSE_EQ|INE256A01028", "name": "ZOMATO",      "sector": "Food-Tech",   "strategy": "momentum",       "interval": "30minute", "risk": "high"},
    {"symbol": "NSE_EQ|INE364U01010", "name": "PAYTM",       "sector": "Fintech",     "strategy": "breakout",       "interval": "day",      "risk": "high"},
    {"symbol": "NSE_EQ|INE860H01027", "name": "TRENT",       "sector": "Retail",      "strategy": "momentum",       "interval": "day",      "risk": "medium"},
]

# ─────────────────────────────────────────────
#  INTRADAY MOMENTUM PICKS  (30-min candles)
# ─────────────────────────────────────────────
INTRADAY_PICKS = [
    {"symbol": "NSE_EQ|INE002A01018", "name": "RELIANCE_I",  "sector": "Energy",      "strategy": "vwap",           "interval": "30minute", "risk": "medium"},
    {"symbol": "NSE_EQ|INE467B01029", "name": "TCS_I",       "sector": "IT",          "strategy": "vwap",           "interval": "30minute", "risk": "medium"},
    {"symbol": "NSE_EQ|INE040A01034", "name": "HDFCBANK_I",  "sector": "Banking",     "strategy": "vwap",           "interval": "30minute", "risk": "medium"},
    {"symbol": "NSE_EQ|INE090A01021", "name": "ICICIBANK_I", "sector": "Banking",     "strategy": "vwap",           "interval": "30minute", "risk": "medium"},
    {"symbol": "NSE_EQ|INE062A01020", "name": "BAJFINANCE_I","sector": "Finance",     "strategy": "vwap",           "interval": "30minute", "risk": "high"},
    {"symbol": "NSE_EQ|INE066A01021", "name": "TATAMOTORS_I","sector": "Auto",        "strategy": "vwap",           "interval": "30minute", "risk": "high"},
    {"symbol": "NSE_EQ|INE081A01020", "name": "TATASTEEL_I", "sector": "Metals",      "strategy": "vwap",           "interval": "30minute", "risk": "high"},
    {"symbol": "NSE_EQ|INE256A01028", "name": "ZOMATO_I",    "sector": "Consumer",    "strategy": "vwap",           "interval": "30minute", "risk": "high"},
]


# ─────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────

def get_watchlist(
    include_nifty50: bool = True,
    include_next50: bool = True,
    include_momentum: bool = True,
    include_intraday: bool = True,
    risk_levels: list = None,       # e.g. ['low', 'medium'] to exclude high-risk
    sectors: list = None,           # e.g. ['IT', 'Banking'] to filter specific sectors
    max_stocks: int = 100
) -> list:
    """
    Returns a deduplicated watchlist of stocks based on filters.

    Args:
        include_nifty50    : Include Nifty 50 stocks
        include_next50     : Include Nifty Next 50 stocks
        include_momentum   : Include high-momentum sector picks
        include_intraday   : Include intraday picks (30-min candles)
        risk_levels        : List of risk levels to include. None = all levels.
        sectors            : List of sectors to filter. None = all sectors.
        max_stocks         : Maximum number of stocks to return (default 100)

    Returns:
        List of stock dicts with symbol, name, sector, strategy, interval, risk
    """
    pool = []
    if include_nifty50:
        pool.extend(NIFTY_50)
    if include_next50:
        pool.extend(NIFTY_NEXT_50)
    if include_momentum:
        pool.extend(HIGH_MOMENTUM)
    if include_intraday:
        pool.extend(INTRADAY_PICKS)

    # Filter by risk level
    if risk_levels:
        pool = [s for s in pool if s["risk"] in risk_levels]

    # Filter by sector
    if sectors:
        pool = [s for s in pool if s["sector"] in sectors]

    # Deduplicate by (symbol, interval) — same stock can appear as both daily and intraday
    seen = set()
    unique = []
    for s in pool:
        key = (s["symbol"], s["interval"])
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique[:max_stocks]


def get_stock_by_name(name: str) -> dict:
    """Find a stock entry by its short name (case-insensitive)."""
    all_stocks = NIFTY_50 + NIFTY_NEXT_50 + HIGH_MOMENTUM + INTRADAY_PICKS
    name_upper = name.upper()
    for s in all_stocks:
        if s["name"].upper() == name_upper or s["name"].upper().startswith(name_upper.split("_")[0]):
            return s
    return None


def get_sector_stocks(sector: str) -> list:
    """Get all stocks from a specific sector."""
    all_stocks = NIFTY_50 + NIFTY_NEXT_50 + HIGH_MOMENTUM + INTRADAY_PICKS
    return [s for s in all_stocks if s["sector"].lower() == sector.lower()]


def get_all_sectors() -> list:
    """Return list of all unique sectors."""
    all_stocks = NIFTY_50 + NIFTY_NEXT_50 + HIGH_MOMENTUM + INTRADAY_PICKS
    return sorted(set(s["sector"] for s in all_stocks))


if __name__ == "__main__":
    wl = get_watchlist()
    print(f"Total watchlist: {len(wl)} stocks")
    print(f"Sectors covered: {get_all_sectors()}")
    low_risk = get_watchlist(risk_levels=["low"])
    print(f"Low-risk only: {len(low_risk)} stocks")
