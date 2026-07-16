"""
StockGraber data layer
======================
Real daily OHLC candles via yfinance, cached locally in SQLite so we don't
re-hit the network on every chart load.

Public API:
    get_ohlc(symbol, start=None, end=None, force_refresh=False) -> DataFrame
        Returns a DataFrame indexed by a (tz-naive) DatetimeIndex with columns
        open, high, low, close, volume for the requested [start, end] window --
        exactly what finplot's candlestick_ochl() and plot() want after column
        selection.

Caching / no re-fetch:
    Two tables live in stockgraber.db next to this module.
      * ohlc      -- the candles, keyed by (symbol, date).
      * coverage  -- the contiguous [start, end] date span we've ALREADY
                     requested from the source for each symbol.
    On each call we only download the parts of the requested window that fall
    OUTSIDE the recorded coverage, then widen the coverage. So data already in
    the database is never downloaded again -- including spans that returned
    nothing (e.g. dates before a stock was listed).
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import sys

import pandas as pd
import yfinance as yf

# Cache location. As a PyInstaller exe, __file__ lives in a temp extraction dir
# that's wiped each run, so keep the cache next to the executable instead.
if getattr(sys, "frozen", False):
    DB_PATH = Path(sys.executable).with_name("stockgraber.db")
else:
    DB_PATH = Path(__file__).with_name("stockgraber.db")

# Default window when the caller doesn't specify one: a fixed start (keeps the
# trading calendar consistent across symbols) through the most recent weekday.
DEFAULT_START = "2015-01-01"

_OHLC_COLS = ["open", "high", "low", "close", "volume"]
_DAY = pd.Timedelta(days=1)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ohlc (
            symbol TEXT NOT NULL,
            date   TEXT NOT NULL,          -- ISO 'YYYY-MM-DD'
            open   REAL NOT NULL,
            high   REAL NOT NULL,
            low    REAL NOT NULL,
            close  REAL NOT NULL,
            volume REAL,
            PRIMARY KEY (symbol, date)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS coverage (
            symbol TEXT PRIMARY KEY,
            start  TEXT NOT NULL,          -- ISO 'YYYY-MM-DD', inclusive
            end    TEXT NOT NULL           -- ISO 'YYYY-MM-DD', inclusive
        )
        """
    )
    # symbols the user has actually charted, for quick reuse
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            symbol    TEXT PRIMARY KEY,
            last_used TEXT NOT NULL,       -- ISO 'YYYY-MM-DD HH:MM:SS'
            uses      INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    return conn


def record_symbol(symbol):
    """Remember a symbol the user successfully charted (upsert + bump count)."""
    symbol = (symbol or "").strip().upper()
    if not symbol:
        return
    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO history (symbol, last_used, uses) VALUES (?, ?, 1)
            ON CONFLICT(symbol) DO UPDATE SET
                last_used = excluded.last_used, uses = history.uses + 1
            """,
            (symbol, now),
        )
        conn.commit()
    finally:
        conn.close()


def recent_symbols(limit=15):
    """Previously charted symbols, most recently used first.

    Pass limit=None for the complete history.
    """
    query = ("SELECT symbol, last_used, uses FROM history "
             "ORDER BY last_used DESC")
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    conn = _connect()
    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()
    return [{"symbol": r[0], "last_used": r[1], "uses": r[2]} for r in rows]


def forget_symbol(symbol):
    """Drop one symbol from the reuse history."""
    symbol = (symbol or "").strip().upper()
    conn = _connect()
    try:
        conn.execute("DELETE FROM history WHERE symbol = ?", (symbol,))
        conn.commit()
    finally:
        conn.close()


def _most_recent_weekday() -> pd.Timestamp:
    day = pd.Timestamp.now().normalize()
    while day.weekday() >= 5:        # 5 = Sat, 6 = Sun
        day -= _DAY
    return day


def _coverage(conn: sqlite3.Connection, symbol: str):
    row = conn.execute(
        "SELECT start, end FROM coverage WHERE symbol = ?", (symbol,)
    ).fetchone()
    if not row:
        return None
    return pd.Timestamp(row[0]), pd.Timestamp(row[1])


def _set_coverage(conn, symbol, start, end) -> None:
    conn.execute(
        """
        INSERT INTO coverage (symbol, start, end) VALUES (?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET start=excluded.start, end=excluded.end
        """,
        (symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")),
    )
    conn.commit()


def _has_rows(conn: sqlite3.Connection, symbol: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM ohlc WHERE symbol = ? LIMIT 1", (symbol,)
    ).fetchone()
    return row is not None


def _data_bounds(conn: sqlite3.Connection, symbol: str):
    """Min/max cached date for a symbol, or None -- used to seed coverage for
    databases that predate the coverage table."""
    row = conn.execute(
        "SELECT MIN(date), MAX(date) FROM ohlc WHERE symbol = ?", (symbol,)
    ).fetchone()
    if not row or row[0] is None:
        return None
    return pd.Timestamp(row[0]), pd.Timestamp(row[1])


def _fetch(symbol: str, start, end) -> pd.DataFrame:
    """Download [start, end] inclusive. Returns empty frame if nothing there."""
    raw = yf.download(
        symbol,
        start=pd.Timestamp(start).strftime("%Y-%m-%d"),
        # yfinance's 'end' is EXCLUSIVE, so bump a day to include the end date
        end=(pd.Timestamp(end) + _DAY).strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if raw is None or raw.empty:
        return pd.DataFrame(columns=_OHLC_COLS)
    # Recent yfinance returns a (field, ticker) MultiIndex on the columns even
    # for a single ticker -- flatten it down to just the field name.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw.rename(columns=str.lower)
    df = raw[_OHLC_COLS].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df.dropna(subset=["open", "high", "low", "close"])


def _upsert(conn: sqlite3.Connection, symbol: str, df: pd.DataFrame) -> None:
    rows = [
        (
            symbol,
            idx.strftime("%Y-%m-%d"),
            float(r.open), float(r.high), float(r.low), float(r.close),
            None if pd.isna(r.volume) else float(r.volume),
        )
        for idx, r in df.iterrows()
    ]
    conn.executemany(
        """
        INSERT INTO ohlc (symbol, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, date) DO UPDATE SET
            open=excluded.open, high=excluded.high, low=excluded.low,
            close=excluded.close, volume=excluded.volume
        """,
        rows,
    )
    conn.commit()


def _read_range(conn, symbol, start, end) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT date, open, high, low, close, volume FROM ohlc "
        "WHERE symbol = ? AND date BETWEEN ? AND ? ORDER BY date",
        conn,
        params=(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")),
        parse_dates=["date"],
        index_col="date",
    )


def get_ohlc(symbol, start=None, end=None, force_refresh=False) -> pd.DataFrame:
    """Daily OHLC for `symbol` over [start, end], fetching only what's missing.

    Already-cached data is never re-downloaded: we track the date span already
    requested per symbol and only hit the network for the bits outside it.
    Pass force_refresh=True to re-download the requested window regardless.
    """
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ValueError("No ticker symbol given.")
    start = pd.Timestamp(start).normalize() if start else pd.Timestamp(DEFAULT_START)
    end = pd.Timestamp(end).normalize() if end else _most_recent_weekday()
    if end < start:
        raise ValueError("End date is before start date.")

    conn = _connect()
    try:
        stored = _coverage(conn, symbol)
        if stored is None and _has_rows(conn, symbol):
            # DB predates the coverage table: treat existing rows as covered so
            # we don't re-download what's already there.
            stored = _data_bounds(conn, symbol)
        cov = None if force_refresh else stored

        # Work out which sub-ranges still need downloading. With coverage known,
        # we only ever extend past its edges -- the interior is never refetched.
        to_fetch = []
        if cov is None:
            to_fetch.append((start, end))
        else:
            cstart, cend = cov
            if start < cstart:
                to_fetch.append((start, cstart - _DAY))
            if end > cend:
                to_fetch.append((cend + _DAY, end))

        for s, e in to_fetch:
            if e < s:
                continue
            fresh = _fetch(symbol, s, e)
            if not fresh.empty:
                _upsert(conn, symbol, fresh)

        # Widen recorded coverage for valid symbols (ones that have rows), so we
        # won't request the same span again -- even spans that returned nothing.
        if _has_rows(conn, symbol):
            lo, hi = start, end
            if stored is not None:
                lo, hi = min(lo, stored[0]), max(hi, stored[1])
            _set_coverage(conn, symbol, lo, hi)

        cached = _read_range(conn, symbol, start, end)
    finally:
        conn.close()

    if cached.empty:
        raise ValueError(f"No data for ticker '{symbol}' in the given range.")
    return cached


def rsi(close, period=14):
    """Relative Strength Index (Wilder's smoothing), 0-100.

    >70 is conventionally "overbought", <30 "oversold".
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder's smoothing == EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def macd(close, fast=12, slow=26, signal=9):
    """MACD. Returns (macd_line, signal_line, histogram).

    macd_line = EMA(fast) - EMA(slow); signal = EMA(macd_line, signal);
    histogram = macd_line - signal_line. MACD is inherently EMA-based.
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def moving_average(series, period, method="sma"):
    """Moving average of `series` over `period`.

    method="sma": simple (equal-weighted) -- the plain rolling mean.
    method="ema": exponential -- weights recent prices more, so it reacts
    faster. adjust=False gives the standard recursive EMA traders expect.
    """
    if method == "ema":
        return series.ewm(span=period, adjust=False).mean()
    return series.rolling(period).mean()


def search_symbols(query, limit=25):
    """Look up ticker codes by company name or partial ticker, across all major
    markets (via Yahoo Finance search). Returns a list of dicts with keys
    symbol, name, exchange, type. Empty list for a blank query."""
    query = (query or "").strip()
    if not query:
        return []
    results = yf.Search(query, max_results=limit)
    out = []
    for r in results.quotes:
        sym = r.get("symbol")
        if not sym:
            continue
        out.append({
            "symbol": sym,
            "name": r.get("shortname") or r.get("longname") or "",
            "exchange": r.get("exchDisp") or r.get("exchange") or "",
            "type": (r.get("quoteType") or "").title(),
        })
    return out


def ma_cross_markers(df, fast=50, slow=200, method="sma", pad=0.03):
    """Find moving-average crossovers and where to draw their markers.

    Golden cross: the fast MA crosses ABOVE the slow MA (bullish).
    Death cross : the fast MA crosses BELOW the slow MA (bearish).
    `method` ("sma"/"ema") must match what the chart's MA lines use.

    Returns (golden, death): two pandas Series indexed by the crossover date.
    Each value is a y-coordinate for the marker -- golden sits just under the
    bar's low, death just over its high (offset by `pad`, a fraction) so the
    arrows don't sit on top of the candles. Either Series may be empty.
    """
    fast_ma = moving_average(df["close"], fast, method)
    slow_ma = moving_average(df["close"], slow, method)

    valid = fast_ma.notna() & slow_ma.notna()
    # EMA produces values from the first bar (no NaN warmup), so enforce a
    # `slow`-bar warmup explicitly -- otherwise early, unreliable EMAs would
    # fire spurious crosses. (For SMA those bars are already NaN/invalid.)
    if slow < len(valid):
        valid.iloc[:slow] = False
    above = (fast_ma > slow_ma) & valid
    prev_above = above.shift(1, fill_value=False)
    prev_valid = valid.shift(1, fill_value=False)

    # only count a cross when BOTH this bar and the previous one have valid MAs,
    # so we don't fire a false signal on the first bar the slow MA exists
    golden_mask = valid & prev_valid & above & ~prev_above
    death_mask = valid & prev_valid & ~above & prev_above

    golden = df.loc[golden_mask, "low"] * (1.0 - pad)
    death = df.loc[death_mask, "high"] * (1.0 + pad)
    return golden, death
