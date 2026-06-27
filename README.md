# StockGraber

A desktop stock-charting app built with [finplot](https://github.com/highfestiva/finplot)
embedded in a [PySide6](https://doc.qt.io/qtforpython/) (Qt) window, styled as a
dark "trading terminal". It pulls real daily OHLC data from Yahoo Finance (via
`yfinance`), caches it locally in SQLite, and renders candlesticks with volume,
moving-average crossovers, RSI/MACD sub-panels, and a percent-change
index-comparison view. It launches **full screen**.

> ⚠️ **Not financial advice.** StockGraber is a charting/learning tool. The
> indicators and signals it draws (golden/death crosses, RSI, MACD, etc.) are
> common technical-analysis conventions, not buy/sell recommendations. No
> indicator reliably predicts price.

---

## Features

- **Dark terminal UI** — title bar, command bar, a stacked chart column
  (price / volume / RSI / MACD) and a sidebar of cards (Quote / Indicators /
  Comparison / Legend / Date Range). Launches full screen; **Exit** button or
  **Esc** to quit.
- **Bilingual UI** — one-click toggle between **English** and **Traditional
  Chinese (繁體中文)** for the whole interface.
- **Real data, cached** — daily OHLC from Yahoo Finance, stored in a local
  SQLite database so repeat loads are instant and only missing dates are
  downloaded.
- **Candlesticks + volume** — price panel with a volume sub-panel, colored by
  up/down day.
- **Moving-average crossovers** — preset fast/slow pairs (9/21, 20/50, 50/200,
  100/200) shown as Fast/Slow value tiles; toggle **SMA ↔ EMA**.
- **Golden / death cross markers** — bright-yellow-ringed ▲ (bullish) / ▼
  (bearish) arrows where the fast MA crosses the slow MA.
- **RSI & MACD sub-panels** — RSI (14) with a 30–70 band, MACD (12,26,9) with a
  green/red histogram; Volume / RSI / MACD panels can each be shown/hidden.
- **Index comparison (percent mode)** — pick a market index (US / Canada /
  Hong Kong / global) and the price panel switches to a **rebased %-change**
  view: stock as a filled area, index as a line, MAs in %, on a percent axis —
  rebased to the start of the visible window and re-fit (~90% height) as you
  pan/zoom.
- **Hover readout** — a boxed O/H/L/C panel with the day's change vs. the
  previous close (color-coded ▲/▼).
- **Navigation** — drag to pan, mouse-wheel or `+`/`−`/`Reset` buttons to zoom,
  a timeframe segmented control (1M…MAX), and a log/linear toggle. In candle
  mode the highest visible bar is kept ~80% up the panel.
- **Responsive UI** — all network fetches run on a background thread, so the
  window never freezes on a cold symbol.

---

## Requirements

- **Python 3.10+** (developed on 3.12)
- Windows / macOS / Linux (developed on Windows 10)
- Packages: `PySide6`, `finplot`, `pandas`, `numpy`, `yfinance`
  (`pyqtgraph` is pulled in by finplot)
- An internet connection for the first fetch of each symbol/date range

---

## Installation

```bash
pip install PySide6 finplot pandas numpy yfinance
```

> **Qt binding note:** finplot installs **PyQt6**, while this app uses
> **PySide6**. The app pins `PYQTGRAPH_QT_LIB=PySide6` at startup so both halves
> agree — you don't need to set anything yourself.

### Windows helper scripts

On Windows you can just double-click the included batch files:

| Script | What it does |
|---|---|
| `setup.bat` | Install all dependencies (incl. PyInstaller & Pillow). |
| `run.bat` | Run the app from source. |
| `build.bat` | Build the standalone `dist\StockGraber.exe`. |

---

## Usage

```bash
python StockGraber.py
```

(or double-click `run.bat` on Windows)

It opens **full screen** with `AAPL` loaded. Type a ticker and press **Enter**
(or click **Load**) to chart another symbol. Quit with the **✕ Exit** button
(top-right) or the **Esc** key.

### Ticker symbols

Use the Yahoo Finance symbol format:

| Market | Example | Note |
|---|---|---|
| US | `AAPL`, `MSFT`, `SPY` | plain symbol |
| Hong Kong | `0005.HK` | `.HK` suffix |
| Canada (TSX) | `RY.TO` | `.TO` suffix |
| Indices | `^GSPC`, `^HSI` | `^` prefix |

---

## Controls

**Command bar (top)**

| Control | What it does |
|---|---|
| **Ticker field + Load** | Symbol to chart (Enter or **Load**). |
| **🔍 Find** | Open a lookup window to search ticker codes by company name across markets, then **Copy code** or **Use in chart**. |
| **Timeframe** | Segmented `1M / 3M / 6M / 1Y / 5Y / MAX` — sets the visible window. |
| **Zoom − / + / Reset** | Zoom the date range out/in, or reset to the default view. |
| **中文 / EN** | Toggle the UI language (English ↔ Traditional Chinese). |
| **✕ Exit** | Quit the app (also **Esc**). |

**Sidebar — Indicators card**

| Control | What it does |
|---|---|
| **MA crossover** | Preset fast/slow pair (9/21, 20/50, 50/200, 100/200). |
| **Fast / Slow** | Read-only tiles showing the active periods. |
| **EMA** | Use exponential MAs instead of simple ones. |
| **Volume / RSI / MACD** | Show or hide each sub-panel. |
| **Log scale** | Toggle log / linear price scale (auto-off while comparing). |

**Sidebar — other cards**

| Card | What it does |
|---|---|
| **Quote** | Ticker, exchange, last close, change vs. previous day. |
| **Comparison** | Pick an index → percent-compare mode; **Off** to revert. |
| **Legend** | Colour key for the lines currently drawn. |
| **Date Range** | From / To dates (only missing dates are downloaded). |

**Mouse**

- **Drag** — pan left/right through history
- **Wheel** — zoom; **Ctrl+Wheel** — vertical zoom
- **Right-drag** — box zoom
- **Hover** — OHLC + change readout box (top-left of the price panel)

---

## Indicators & signals (quick reference)

| Signal | Meaning (convention) |
|---|---|
| **Golden cross** (▲) | Fast MA crosses **above** slow MA — bullish. |
| **Death cross** (▼) | Fast MA crosses **below** slow MA — bearish. |
| **RSI > 70 / < 30** | Overbought / oversold. |
| **MACD line vs. signal** | Momentum turning up/down. |

MA-pair character: **50/200** = long-term, fewest/most-trusted signals;
**20/50** = swing trading; **10/20** & **5/10** = short-term, more signals and
more noise (whipsaws); **9/21** & **12/26** = popular short–medium pairings,
traditionally used as EMAs.

---

## Index comparison list

- **United States** — S&P 500 (`^GSPC`), Dow (`^DJI`), Nasdaq Composite
  (`^IXIC`), Nasdaq 100 (`^NDX`), Russell 2000 (`^RUT`), VIX (`^VIX`)
- **Canada** — S&P/TSX Composite (`^GSPTSE`)
- **Hong Kong** — Hang Seng (`^HSI`), HS China Enterprises (`^HSCE`)
- **Global / Other** — FTSE 100 (`^FTSE`), DAX (`^GDAXI`), CAC 40 (`^FCHI`),
  Nikkei 225 (`^N225`), Euro Stoxx 50 (`^STOXX50E`), ASX 200 (`^AXJO`),
  Nifty 50 (`^NSEI`)

Selecting an index switches the price panel to **percent-change mode**: both the
stock and the index are rebased to 0% at the start of the visible window, so
where the stock line ends above the index line, the stock outperformed.

---

## Building a standalone Windows .exe

Double-click **`build.bat`**, or run:

```bash
pip install pyinstaller
build.bat
```

It produces **`dist\StockGraber.exe`** — a single-file app with the StockGraber
icon that runs without a Python install. Under the hood it forces the PySide6 Qt
binding (PyQt5/PyQt6 are excluded, since PyInstaller can't bundle multiple Qt
bindings):

```bat
pyinstaller --noconfirm --windowed --onefile --name StockGraber ^
  --icon StockGraber.ico --collect-all finplot --collect-all pyqtgraph ^
  --exclude-module PyQt5 --exclude-module PyQt6 StockGraber.py
```

The exe writes its SQLite cache next to itself. The build output (`build/`,
`dist/`) is git-ignored — distribute the exe via a GitHub **Release** rather
than committing it.

---

## Project layout

```
StockGraber/
├── StockGraber.py     # the app: PySide6 window, chart panels, controls
├── data.py            # data layer: yfinance fetch, SQLite cache, indicators
├── StockGraber.ico    # app icon (built from StockGraber.png)
├── setup / run / build.bat   # Windows helper scripts
├── stockgraber.db     # SQLite cache (auto-created on first run, git-ignored)
└── README.md
```

### `data.py` — data layer

- `get_ohlc(symbol, start, end, force_refresh=False)` — daily OHLC for a date
  range. Reads from cache and downloads **only the missing dates**; never
  re-downloads data already stored (a per-symbol coverage window is tracked so
  even empty spans, like pre-IPO dates, aren't re-requested).
- `moving_average(series, period, method)` — SMA or EMA.
- `ma_cross_markers(df, fast, slow, method)` — golden/death cross points.
- `rsi(close, period=14)` — Wilder's RSI.
- `macd(close, fast=12, slow=26, signal=9)` — MACD line, signal, histogram.

The cache lives in two SQLite tables: `ohlc` (the candles, keyed by
`symbol, date`) and `coverage` (the date span already fetched per symbol).

### `StockGraber.py` — the app

A single `SpikeWindow` (QMainWindow) hosting four x-linked finplot panels
(price / volume / RSI / MACD) plus the dark control chrome and sidebar cards.
Network fetches run on a `QThread` worker and deliver results back to the UI
thread via Qt signals. Chart items are split into **volume**, **panel**
(RSI+MACD) and **price** (candles or percent lines) groups, so changing MA
settings re-renders only the price panel without refetching or losing your zoom.

Tunable constants on `SpikeWindow`:

| Constant | Default | Purpose |
|---|---|---|
| `INITIAL_SYMBOL` | `"AAPL"` | Symbol loaded at startup. |
| `MA_PRESETS` | 4 pairs | Crossover presets (label, fast, slow). |
| `TIMEFRAMES` | 6 | Command-bar timeframe segments (label, # bars). |
| `RSI_PERIOD` | `14` | RSI period. |
| `MACD_FAST/SLOW/SIGNAL` | `12/26/9` | MACD periods. |
| `PRICE_MAX_FRACTION` | `0.80` | Candle mode: height the highest bar sits at. |
| `COMPARE_FILL` | `0.90` | Percent mode: fraction of panel height filled. |

`data.py` constant `DEFAULT_START` (`"2015-01-01"`) sets how far back a symbol is
first fetched when no start date is given.

---

## Notes & limitations

- **Prices are not split/dividend-adjusted** (`auto_adjust=False`). Cached rows
  are only overwritten when re-fetched, so old bars keep their raw values after
  a split until that range is re-fetched.
- **Index comparison is rebased to the start of the visible window** and re-fits
  as you pan/zoom; it replaces the candles with a percent-change view while
  active.
- **MA periods are preset-only** (4 pairs); **RSI/MACD periods are fixed**
  (14, and 12/26/9).
- Data quality depends on Yahoo Finance; occasional gaps or glitches are
  possible.

---

## Disclaimer

StockGraber is for **educational and informational purposes only** and is **not
financial advice**. Do your own research and consult a qualified professional
before making investment decisions. Market data is provided by Yahoo Finance and
may be delayed or inaccurate.
