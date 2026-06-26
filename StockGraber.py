"""
StockGraber -- finplot + PySide6 stock charter
==============================================
A dark "trading terminal" UI: title bar + command bar on top, a stacked chart
column (price / volume / RSI / MACD) on the left, and a sidebar of cards
(Quote / Indicators / Comparison / Legend / Date Range) on the right.

The GUI layout/palette follow the StockGraber.dc.html design; the data and
charting layers (yfinance + SQLite cache in data.py, finplot panels) are
unchanged underneath.

Run:
    pip install PySide6 finplot pandas numpy yfinance
    python StockGraber.py
"""

import os
import sys

# Both PyQt6 (pulled in by finplot) and PySide6 are installed. pyqtgraph -- and
# therefore finplot -- will bind to whichever it finds first, and if that isn't
# PySide6 the chart widget can't be added to our PySide6 layout (cross-binding
# TypeError). Pin it to PySide6 BEFORE importing finplot so both halves agree.
os.environ.setdefault("PYQTGRAPH_QT_LIB", "PySide6")

import finplot as fplt
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

import data

# ---- design tokens (from StockGraber.dc.html) -------------------------------
BG0      = "#000000"     # outer backdrop
SHELL    = "#060607"     # app shell
PANEL    = "#050506"     # chart panels
SIDEBAR  = "#070708"     # sidebar
CARD     = "#0a0a0d"     # sidebar cards
INSET    = "#0c0c10"     # inset controls
BORDER   = "#141418"
ACCENT   = "#a855f7"     # brand purple
UP       = "#22c98a"     # bullish
DOWN     = "#f6465d"     # bearish
MA_FAST  = "#4f8cff"     # fast MA (blue)
MA_SLOW  = "#f3a13a"     # slow MA (orange)
COMPARE  = "#22d3ee"     # rebased index (cyan)
TXT      = "#e8eaed"
TXT2     = "#cfd3da"
MUT      = "#8a909a"
MUT2     = "#6a707a"
DIM      = "#5a606b"

APP_STYLE = f"""
QWidget#central {{ background-color: {BG0}; }}
QFrame#shell {{ background-color: {SHELL}; border: 1px solid #1b1b21; border-radius: 15px; }}
QFrame#header {{ background-color: {SHELL}; border-bottom: 1px solid {BORDER}; }}
QFrame#cmdbar {{ background-color: #08080a; border-bottom: 1px solid {BORDER}; }}
QFrame#sidebar {{ background-color: {SIDEBAR}; border-left: 1px solid {BORDER}; }}
QScrollArea {{ background: {SIDEBAR}; border: none; }}
QScrollArea > QWidget > QWidget {{ background: {SIDEBAR}; }}
QFrame#card {{ background-color: {CARD}; border: 1px solid rgba(255,255,255,0.055); border-radius: 13px; }}
QFrame#tile {{ background-color: {INSET}; border: 1px solid rgba(255,255,255,0.06); border-radius: 9px; }}
QLabel {{ color: {TXT2}; background: transparent; }}
QLabel#cardtitle {{ color: {MUT2}; font-weight: 800; font-size: 10px; }}
QLabel#brand {{ color: {TXT}; font-weight: 800; font-size: 14px; }}
QLabel#ver {{ color: {DIM}; font-family: 'JetBrains Mono','Consolas',monospace; font-size: 11px; }}
QLabel#hsym {{ color: {MUT}; font-family: 'JetBrains Mono','Consolas',monospace; font-size: 12px; }}
QLineEdit {{
    background-color: #0d0d11; color: {TXT};
    border: 1px solid rgba(255,255,255,0.08); border-radius: 10px;
    padding: 7px 12px; font-family: 'JetBrains Mono','Consolas',monospace;
    font-size: 13px; font-weight: 600; selection-background-color: {ACCENT};
}}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
QPushButton#load {{
    background-color: {ACCENT}; color: #fff; border: none; border-radius: 10px;
    padding: 8px 18px; font-weight: 700; font-size: 13px;
}}
QPushButton#load:hover {{ background-color: #b066f8; }}
QPushButton#load:disabled {{ background-color: #4a3060; color: #b9a9cf; }}
QPushButton#tool {{
    background-color: #0d0d11; color: {TXT2};
    border: 1px solid rgba(255,255,255,0.07); border-radius: 9px; padding: 6px 12px;
}}
QPushButton#tool:hover {{ background-color: #17171c; color: {TXT}; }}
QPushButton#exit {{
    background-color: rgba(246,70,93,0.12); color: {DOWN};
    border: 1px solid rgba(246,70,93,0.35); border-radius: 8px;
    padding: 5px 14px; font-weight: 700;
}}
QPushButton#exit:hover {{ background-color: {DOWN}; color: #fff; }}
QFrame#segwrap {{ background-color: {INSET}; border: 1px solid rgba(255,255,255,0.06); border-radius: 9px; }}
QPushButton#seg {{
    background: transparent; border: none; border-radius: 7px;
    padding: 6px 10px; color: {MUT}; font-weight: 600; font-size: 12px;
}}
QPushButton#seg:hover {{ color: {TXT}; }}
QPushButton#seg:checked {{ background-color: #23262e; color: #fff; }}
QComboBox {{
    background-color: {INSET}; color: {TXT2};
    border: 1px solid rgba(255,255,255,0.06); border-radius: 9px; padding: 7px 10px;
}}
QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background-color: {INSET}; color: {TXT}; outline: none;
    border: 1px solid #3a3f4b; selection-background-color: {ACCENT};
}}
QDateEdit {{
    background-color: {INSET}; color: {TXT2};
    border: 1px solid rgba(255,255,255,0.06); border-radius: 9px; padding: 7px 10px;
    font-family: 'JetBrains Mono','Consolas',monospace; font-size: 13px;
}}
QDateEdit:focus {{ border: 1px solid {ACCENT}; }}
QToolTip {{ background-color: {INSET}; color: {TXT}; border: 1px solid {ACCENT}; padding: 4px; }}
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #2a2e37; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QDialog {{ background-color: {SHELL}; }}
QTableWidget {{
    background-color: {INSET}; color: {TXT2}; gridline-color: #1c1c22;
    border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;
    selection-background-color: {ACCENT}; selection-color: #fff;
}}
QTableWidget::item:selected {{ background-color: {ACCENT}; color: #fff; }}
QHeaderView::section {{
    background-color: #0d0d11; color: {MUT}; border: none;
    border-bottom: 1px solid #1c1c22; padding: 6px; font-weight: 700;
}}
"""


class ToggleSwitch(QtWidgets.QCheckBox):
    """A pill toggle (iOS-style) that behaves like a QCheckBox."""

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setChecked(checked)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(40, 22)

    def sizeHint(self):
        return QtCore.QSize(40, 22)

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, _ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        on = self.isChecked()
        r = self.rect().adjusted(1, 1, -1, -1)
        track = QtGui.QColor(ACCENT) if on else QtGui.QColor(255, 255, 255, 30)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        d = r.height() - 6
        x = r.right() - d - 2 if on else r.left() + 3
        p.setBrush(QtGui.QColor("#ffffff"))
        p.drawEllipse(int(x), r.top() + 3, d, d)


def _card(title):
    """A sidebar card: returns (frame, inner vertical layout)."""
    f = QtWidgets.QFrame()
    f.setObjectName("card")
    v = QtWidgets.QVBoxLayout(f)
    v.setContentsMargins(16, 14, 16, 14)
    v.setSpacing(10)
    if title:
        t = QtWidgets.QLabel(title.upper())
        t.setObjectName("cardtitle")
        f = (f, v, t)
        v.addWidget(t)
        return f[0], f[1]
    return f, v


def _switch_row(label, toggle):
    """A 'Label .......... [toggle]' row."""
    row = QtWidgets.QHBoxLayout()
    lbl = QtWidgets.QLabel(label)
    lbl.setStyleSheet(f"color:{TXT2}; font-size:13px;")
    row.addWidget(lbl)
    row.addStretch(1)
    row.addWidget(toggle)
    return row


class _Fetcher(QtCore.QThread):
    """Runs data.get_ohlc() off the UI thread so the window never freezes."""

    loaded = QtCore.Signal(str, object)   # symbol, DataFrame
    failed = QtCore.Signal(str, str)      # symbol, error message

    def __init__(self, symbol, start, end, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self._start = start          # NB: don't name this 'start' -- QThread.start()
        self._end = end

    def run(self):
        try:
            df = data.get_ohlc(self.symbol, self._start, self._end)
            self.loaded.emit(self.symbol, df)
        except Exception as e:
            self.failed.emit(self.symbol, str(e))


class _SearchWorker(QtCore.QThread):
    """Runs data.search_symbols() off the UI thread."""

    done = QtCore.Signal(str, object)     # query, list of result dicts
    failed = QtCore.Signal(str, str)

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self._q = query

    def run(self):
        try:
            self.done.emit(self._q, data.search_symbols(self._q))
        except Exception as e:
            self.failed.emit(self._q, str(e))


class SymbolSearchDialog(QtWidgets.QDialog):
    """Find a ticker code by name across markets, then copy it or send it to the
    main chart."""

    def __init__(self, parent, on_pick):
        super().__init__(parent)
        self._on_pick = on_pick
        self._worker = None
        self.setWindowTitle("Find a stock code")
        self.setMinimumSize(580, 480)

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        row = QtWidgets.QHBoxLayout()
        self.q = QtWidgets.QLineEdit()
        self.q.setPlaceholderText("Company name or ticker — e.g. apple, tencent, hsbc")
        self.q.returnPressed.connect(self._search)
        row.addWidget(self.q)
        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.setObjectName("load")
        self.search_btn.clicked.connect(self._search)
        row.addWidget(self.search_btn)
        v.addLayout(row)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Exchange", "Type"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setColumnWidth(0, 110)
        self.table.setColumnWidth(1, 250)
        self.table.setColumnWidth(2, 120)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellDoubleClicked.connect(lambda *_a: self._use())
        v.addWidget(self.table, 1)

        self.status = QtWidgets.QLabel("Type a name or ticker and press Search.")
        self.status.setStyleSheet(f"color:{MUT}; font-size:12px;")
        v.addWidget(self.status)

        btns = QtWidgets.QHBoxLayout()
        self.copy_btn = QtWidgets.QPushButton("Copy code")
        self.copy_btn.setObjectName("tool")
        self.copy_btn.clicked.connect(self._copy)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setObjectName("tool")
        close_btn.clicked.connect(self.close)
        self.use_btn = QtWidgets.QPushButton("Use in chart")
        self.use_btn.setObjectName("load")
        self.use_btn.clicked.connect(self._use)
        btns.addWidget(self.copy_btn)
        btns.addStretch(1)
        btns.addWidget(close_btn)
        btns.addWidget(self.use_btn)
        v.addLayout(btns)

    def _search(self):
        q = self.q.text().strip()
        if not q or (self._worker is not None and self._worker.isRunning()):
            return
        self.status.setText("Searching…")
        self.search_btn.setEnabled(False)
        self._worker = _SearchWorker(q, self)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_done(self, _q, results):
        self.table.setRowCount(0)
        for r in results:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, key in enumerate(("symbol", "name", "exchange", "type")):
                self.table.setItem(row, col,
                                   QtWidgets.QTableWidgetItem(str(r.get(key, ""))))
        if results:
            self.table.selectRow(0)
            self.status.setText(
                f"{len(results)} result(s) — double-click a row or 'Use in chart'.")
        else:
            self.status.setText("No matches.")

    def _on_failed(self, _q, message):
        self.status.setText("Search failed: " + message)

    def _on_finished(self):
        self.search_btn.setEnabled(True)
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

    def _selected_symbol(self):
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return item.text() if item else None

    def _copy(self):
        sym = self._selected_symbol()
        if sym:
            QtWidgets.QApplication.clipboard().setText(sym)
            self.status.setText(f"Copied to clipboard: {sym}")

    def _use(self):
        sym = self._selected_symbol()
        if sym:
            self._on_pick(sym)
            self.close()


class SpikeWindow(QtWidgets.QMainWindow):
    TITLE = "StockGraber"
    INITIAL_SYMBOL = "AAPL"
    # (label, fast, slow) MA crossover presets from the design
    MA_PRESETS = [("9/21", 9, 21), ("20/50", 20, 50),
                  ("50/200", 50, 200), ("100/200", 100, 200)]
    DEFAULT_PRESET = 2                       # 50/200
    # timeframe -> number of trailing trading days to show (None = all)
    TIMEFRAMES = [("1M", 21), ("3M", 63), ("6M", 126),
                  ("1Y", 252), ("5Y", 1260), ("MAX", None)]
    DEFAULT_TF = 2                           # 6M
    RSI_PERIOD = 14
    MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
    PRICE_MAX_FRACTION = 0.80                # candle mode: highest bar ~80% up
    COMPARE_FILL = 0.90                      # percent mode: fill ~90% of height
    COMPARE_INDICES = [
        ("United States", [
            ("S&P 500", "^GSPC"), ("Dow Jones", "^DJI"),
            ("Nasdaq Composite", "^IXIC"), ("Nasdaq 100", "^NDX"),
            ("Russell 2000", "^RUT"), ("VIX (volatility)", "^VIX"),
        ]),
        ("Canada", [("S&P/TSX Composite", "^GSPTSE")]),
        ("Hong Kong", [("Hang Seng", "^HSI"), ("HS China Enterprises", "^HSCE")]),
        ("Global / Other", [
            ("FTSE 100 (UK)", "^FTSE"), ("DAX (Germany)", "^GDAXI"),
            ("CAC 40 (France)", "^FCHI"), ("Nikkei 225 (Japan)", "^N225"),
            ("Euro Stoxx 50", "^STOXX50E"), ("ASX 200 (Australia)", "^AXJO"),
            ("Nifty 50 (India)", "^NSEI"),
        ]),
    ]
    _RING_Z = 20
    _ARROW_Z = 21

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.TITLE)
        self.resize(1480, 920)
        self.current_symbol = None
        self._df = None
        self._vol_items = []             # volume bars (independent of mode)
        self._panel_items = []           # RSI + MACD
        self._price_items = []           # price panel: candles or %-compare lines
        self._compare_ticker = None
        self._compare_df = None
        self._fetcher = None
        self._compare_fetcher = None
        self._fast, self._slow = self.MA_PRESETS[self.DEFAULT_PRESET][1:3]
        self._tf = self.TIMEFRAMES[self.DEFAULT_TF][1]

        central = QtWidgets.QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        outer = QtWidgets.QVBoxLayout(central)
        outer.setContentsMargins(14, 14, 14, 14)

        shell = QtWidgets.QFrame()
        shell.setObjectName("shell")
        outer.addWidget(shell)
        shellv = QtWidgets.QVBoxLayout(shell)
        shellv.setContentsMargins(0, 0, 0, 0)
        shellv.setSpacing(0)

        shellv.addWidget(self._build_header())
        shellv.addWidget(self._build_cmdbar())

        body = QtWidgets.QWidget()
        bodyh = QtWidgets.QHBoxLayout(body)
        bodyh.setContentsMargins(0, 0, 0, 0)
        bodyh.setSpacing(0)
        bodyh.addWidget(self._build_chart_column(), 1)
        bodyh.addWidget(self._build_sidebar())
        shellv.addWidget(body, 1)

        self._wire_after_chart()
        self.load_symbol(self.INITIAL_SYMBOL)

    # ---- UI construction -------------------------------------------------

    def _build_header(self):
        f = QtWidgets.QFrame()
        f.setObjectName("header")
        f.setFixedHeight(46)
        h = QtWidgets.QHBoxLayout(f)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(11)
        logo = QtWidgets.QLabel("S")
        logo.setFixedSize(24, 24)
        logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {ACCENT}, "
            f"stop:1 #7c3aed); border-radius:7px; color:#fff; font-weight:800; font-size:13px;")
        h.addWidget(logo)
        brand = QtWidgets.QLabel("StockGraber")
        brand.setObjectName("brand")
        h.addWidget(brand)
        ver = QtWidgets.QLabel("v2.0")
        ver.setObjectName("ver")
        h.addWidget(ver)
        h.addWidget(self._sep())
        self.hdr_symbol = QtWidgets.QLabel("—")
        self.hdr_symbol.setObjectName("hsym")
        h.addWidget(self.hdr_symbol)
        h.addStretch(1)
        self.exit_btn = QtWidgets.QPushButton("✕  Exit")
        self.exit_btn.setObjectName("exit")
        self.exit_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.exit_btn.setToolTip("Exit StockGraber (Esc)")
        self.exit_btn.clicked.connect(self.close)
        h.addWidget(self.exit_btn)
        return f

    def _build_cmdbar(self):
        f = QtWidgets.QFrame()
        f.setObjectName("cmdbar")
        h = QtWidgets.QHBoxLayout(f)
        h.setContentsMargins(16, 11, 16, 11)
        h.setSpacing(12)

        self.symbol_input = QtWidgets.QLineEdit(self.INITIAL_SYMBOL)
        self.symbol_input.setFixedWidth(120)
        self.symbol_input.returnPressed.connect(self.load_symbol)
        h.addWidget(self.symbol_input)
        self.load_button = QtWidgets.QPushButton("Load")
        self.load_button.setObjectName("load")
        self.load_button.clicked.connect(lambda: self.load_symbol())
        h.addWidget(self.load_button)
        self.find_btn = self._tool_btn("🔍 Find", self._open_search)
        self.find_btn.setToolTip("Find a stock code by company name")
        h.addWidget(self.find_btn)

        h.addWidget(self._sep())

        # timeframe segmented control
        seg = QtWidgets.QFrame()
        seg.setObjectName("segwrap")
        sh = QtWidgets.QHBoxLayout(seg)
        sh.setContentsMargins(3, 3, 3, 3)
        sh.setSpacing(2)
        self.tf_group = QtWidgets.QButtonGroup(self)
        self.tf_group.setExclusive(True)
        for i, (label, _n) in enumerate(self.TIMEFRAMES):
            b = QtWidgets.QPushButton(label)
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            b.setChecked(i == self.DEFAULT_TF)
            b.clicked.connect(lambda _c, idx=i: self._set_timeframe(idx))
            self.tf_group.addButton(b, i)
            sh.addWidget(b)
        h.addWidget(seg)

        h.addStretch(1)

        # zoom controls
        self.zoom_out_btn = self._tool_btn("−", lambda: self._zoom_x(1.25), w=34)
        self.zoom_in_btn = self._tool_btn("+", lambda: self._zoom_x(0.8), w=34)
        self.zoom_reset_btn = self._tool_btn("Reset", self._reset_zoom)
        h.addWidget(self.zoom_out_btn)
        h.addWidget(self.zoom_in_btn)
        h.addWidget(self.zoom_reset_btn)
        return f

    def _build_chart_column(self):
        col = QtWidgets.QWidget()
        cv = QtWidgets.QVBoxLayout(col)
        cv.setContentsMargins(14, 14, 14, 14)
        cv.setSpacing(10)

        self.ax, self.ax_vol, self.ax_rsi, self.ax_macd = fplt.create_plot_widget(
            master=self, rows=4, init_zoom_periods=126)
        self.axs = [self.ax, self.ax_vol, self.ax_rsi, self.ax_macd]
        self.ax.vb.v_zoom_scale = 2 * (self.PRICE_MAX_FRACTION - 0.5)
        panel_css = ("border:1px solid rgba(255,255,255,0.06); "
                     f"border-radius:12px; background:{PANEL};")
        for w, stretch in ((self.ax.ax_widget, 6), (self.ax_vol.ax_widget, 2),
                           (self.ax_rsi.ax_widget, 2), (self.ax_macd.ax_widget, 3)):
            w.setStyleSheet(panel_css)
            cv.addWidget(w, stretch)
        return col

    def _build_sidebar(self):
        bar = QtWidgets.QFrame()
        bar.setObjectName("sidebar")
        bar.setFixedWidth(320)
        outer = QtWidgets.QVBoxLayout(bar)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        inner = QtWidgets.QWidget()
        scroll.setWidget(inner)
        v = QtWidgets.QVBoxLayout(inner)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(14)

        v.addWidget(self._build_quote_card())
        v.addWidget(self._build_indicators_card())
        v.addWidget(self._build_comparison_card())
        v.addWidget(self._build_legend_card())
        v.addWidget(self._build_range_card())
        v.addStretch(1)
        return bar

    def _build_quote_card(self):
        card, v = _card("")
        top = QtWidgets.QHBoxLayout()
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(3)
        self.q_ticker = QtWidgets.QLabel(self.INITIAL_SYMBOL)
        self.q_ticker.setStyleSheet(
            f"color:{TXT}; font-family:'JetBrains Mono','Consolas',monospace; "
            "font-size:18px; font-weight:700;")
        self.q_name = QtWidgets.QLabel("—")
        self.q_name.setStyleSheet(f"color:{MUT}; font-size:12px;")
        left.addWidget(self.q_ticker)
        left.addWidget(self.q_name)
        top.addLayout(left)
        top.addStretch(1)
        self.q_exch = QtWidgets.QLabel("—")
        self.q_exch.setStyleSheet(
            f"color:{MUT2}; font-family:'JetBrains Mono','Consolas',monospace; "
            f"font-size:10px; border:1px solid #1c1c22; border-radius:6px; padding:3px 7px;")
        self.q_exch.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        top.addWidget(self.q_exch)
        v.addLayout(top)

        prow = QtWidgets.QHBoxLayout()
        prow.setSpacing(10)
        self.q_close = QtWidgets.QLabel("0.00")
        self.q_close.setStyleSheet(
            "color:#fff; font-family:'JetBrains Mono','Consolas',monospace; "
            "font-size:28px; font-weight:700;")
        prow.addWidget(self.q_close)
        self.q_pill = QtWidgets.QLabel("")
        self.q_pill.setStyleSheet(
            f"color:{UP}; font-family:'JetBrains Mono','Consolas',monospace; font-size:12px;")
        self.q_pill.setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom)
        prow.addWidget(self.q_pill)
        prow.addStretch(1)
        v.addLayout(prow)

        sub = QtWidgets.QLabel("USD · Daily close")
        sub.setStyleSheet(f"color:{DIM}; font-size:11px; "
                          "font-family:'JetBrains Mono','Consolas',monospace;")
        v.addWidget(sub)
        return card

    def _build_indicators_card(self):
        card, v = _card("MA Crossover")
        # preset segmented control
        seg = QtWidgets.QFrame()
        seg.setObjectName("segwrap")
        sh = QtWidgets.QHBoxLayout(seg)
        sh.setContentsMargins(3, 3, 3, 3)
        sh.setSpacing(3)
        self.preset_group = QtWidgets.QButtonGroup(self)
        self.preset_group.setExclusive(True)
        for i, (label, _f, _s) in enumerate(self.MA_PRESETS):
            b = QtWidgets.QPushButton(label)
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            b.setChecked(i == self.DEFAULT_PRESET)
            b.clicked.connect(lambda _c, idx=i: self._select_preset(idx))
            self.preset_group.addButton(b, i)
            sh.addWidget(b, 1)
        v.addWidget(seg)

        # Fast / Slow value tiles
        tiles = QtWidgets.QHBoxLayout()
        tiles.setSpacing(10)
        self.fast_tile = self._value_tile("Fast", str(self._fast), MA_FAST)
        self.slow_tile = self._value_tile("Slow", str(self._slow), MA_SLOW)
        tiles.addWidget(self.fast_tile[0])
        tiles.addWidget(self.slow_tile[0])
        v.addLayout(tiles)

        self.ema_checkbox = ToggleSwitch(False)
        self.ema_checkbox.toggled.connect(self._on_ma_changed)
        v.addLayout(_switch_row("Exponential (EMA)", self.ema_checkbox))

        v.addWidget(self._hline())
        ptitle = QtWidgets.QLabel("PANELS")
        ptitle.setObjectName("cardtitle")
        v.addWidget(ptitle)
        self.vol_checkbox = ToggleSwitch(True)
        self.rsi_checkbox = ToggleSwitch(True)
        self.macd_checkbox = ToggleSwitch(True)
        v.addLayout(_switch_row("Volume", self.vol_checkbox))
        v.addLayout(_switch_row("RSI (14)", self.rsi_checkbox))
        v.addLayout(_switch_row("MACD (12,26,9)", self.macd_checkbox))

        v.addWidget(self._hline())
        self.line_checkbox = ToggleSwitch(False)   # off = candles, on = line
        self.line_checkbox.toggled.connect(self._on_chart_type_changed)
        v.addLayout(_switch_row("Line chart", self.line_checkbox))
        self.log_checkbox = ToggleSwitch(False)
        self.log_checkbox.toggled.connect(self.toggle_log)
        v.addLayout(_switch_row("Log scale", self.log_checkbox))
        return card

    def _build_comparison_card(self):
        card, v = _card("Comparison")
        self.compare_combo = QtWidgets.QComboBox()
        self.compare_combo.addItem("None", None)
        for market, items in self.COMPARE_INDICES:
            self.compare_combo.insertSeparator(self.compare_combo.count())
            self.compare_combo.addItem(f"— {market} —", None)
            self.compare_combo.model().item(
                self.compare_combo.count() - 1).setEnabled(False)
            for name, ticker in items:
                self.compare_combo.addItem(f"   {name}  ({ticker})", ticker)
        self.compare_combo.currentIndexChanged.connect(self._on_compare_changed)
        v.addWidget(self.compare_combo)
        self.compare_off_btn = self._tool_btn("Off", self._disable_compare)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.compare_off_btn)
        v.addLayout(row)
        return card

    def _build_legend_card(self):
        card, v = _card("Legend")
        self.legend_label = QtWidgets.QLabel("")
        self.legend_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        v.addWidget(self.legend_label)
        return card

    def _build_range_card(self):
        card, v = _card("Date Range")
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(10)
        fcol = QtWidgets.QVBoxLayout()
        fcol.setSpacing(5)
        fl = QtWidgets.QLabel("FROM")
        fl.setStyleSheet(f"color:{MUT2}; font-size:10px;")
        self.start_date = QtWidgets.QDateEdit(QtCore.QDate(2015, 1, 1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setMaximumDate(QtCore.QDate.currentDate())
        fcol.addWidget(fl)
        fcol.addWidget(self.start_date)
        tcol = QtWidgets.QVBoxLayout()
        tcol.setSpacing(5)
        tl = QtWidgets.QLabel("TO")
        tl.setStyleSheet(f"color:{MUT2}; font-size:10px;")
        self.end_date = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setMaximumDate(QtCore.QDate.currentDate())
        tcol.addWidget(tl)
        tcol.addWidget(self.end_date)
        row.addLayout(fcol)
        row.addLayout(tcol)
        v.addLayout(row)
        return card

    def _wire_after_chart(self):
        """Setup that needs the chart axes to exist."""
        # static sub-panel decorations + labels (match the design)
        fplt.set_y_range(0, 100, ax=self.ax_rsi)
        fplt.add_horizontal_band(30, 70, color="#787b8622", ax=self.ax_rsi)
        fplt.add_legend("Volume", ax=self.ax_vol)
        fplt.add_legend(f"RSI · {self.RSI_PERIOD}", ax=self.ax_rsi)
        fplt.add_legend(
            f"MACD · {self.MACD_FAST},{self.MACD_SLOW},{self.MACD_SIGNAL}",
            ax=self.ax_macd)

        self.vol_checkbox.toggled.connect(self.ax_vol.ax_widget.setVisible)
        self.rsi_checkbox.toggled.connect(self.ax_rsi.ax_widget.setVisible)
        self.macd_checkbox.toggled.connect(self.ax_macd.ax_widget.setVisible)

        # OHLC readout box overlaid on the price panel, updated on hover
        self.info_box = QtWidgets.QLabel(self.ax.ax_widget)
        self.info_box.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.info_box.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.info_box.setStyleSheet(
            "QLabel { background: rgba(8,8,10,0.82); border:1px solid rgba(255,255,255,0.07);"
            " border-radius:10px; padding:9px 13px; color:%s;"
            " font-family:'JetBrains Mono','Consolas',monospace; font-size:12pt; }" % TXT2)
        self.info_box.move(18, 14)
        self.info_box.hide()
        fplt.add_crosshair_info(self._crosshair_info, ax=self.ax)

        # in percent-compare mode, rebase to the visible window's start; recompute
        # (debounced) whenever the user pans/zooms so the % stays bounded on screen
        self._rebasing = False
        self._xtimer = QtCore.QTimer(self)
        self._xtimer.setSingleShot(True)
        self._xtimer.setInterval(60)
        self._xtimer.timeout.connect(self._on_xrange_settled)
        self.ax.vb.sigXRangeChanged.connect(lambda *_a: self._xtimer.start())

        # controls locked during a load
        self._lockable = [
            self.symbol_input, self.load_button, self.start_date, self.end_date,
            self.compare_combo, self.compare_off_btn, self.ema_checkbox,
            self.vol_checkbox, self.rsi_checkbox, self.macd_checkbox,
            self.line_checkbox, self.log_checkbox,
        ]
        self._lockable += list(self.preset_group.buttons())
        self._lockable += list(self.tf_group.buttons())

    # ---- small UI helpers ------------------------------------------------

    def _sep(self):
        s = QtWidgets.QLabel()
        s.setFixedSize(1, 16)
        s.setStyleSheet("background:#1c1c22;")
        return s

    def _hline(self):
        ln = QtWidgets.QFrame()
        ln.setFixedHeight(1)
        ln.setStyleSheet("background:rgba(255,255,255,0.06);")
        return ln

    def _tool_btn(self, text, slot, w=None):
        b = QtWidgets.QPushButton(text)
        b.setObjectName("tool")
        b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        b.setFixedHeight(34)
        if w:
            b.setFixedWidth(w)
        b.clicked.connect(slot)
        return b

    def _value_tile(self, label, value, color):
        f = QtWidgets.QFrame()
        f.setObjectName("tile")
        v = QtWidgets.QVBoxLayout(f)
        v.setContentsMargins(11, 9, 11, 9)
        v.setSpacing(2)
        cap = QtWidgets.QLabel(label.upper())
        cap.setStyleSheet(f"color:{MUT2}; font-size:10px;")
        val = QtWidgets.QLabel(value)
        val.setStyleSheet(f"color:{color}; font-family:'JetBrains Mono','Consolas',"
                          "monospace; font-size:16px; font-weight:600;")
        v.addWidget(cap)
        v.addWidget(val)
        return f, val

    def _exchange(self, sym):
        if sym.startswith("^"):
            return "INDEX"
        if "." in sym:
            return {"HK": "HKEX", "TO": "TSX"}.get(sym.split(".")[-1], sym.split(".")[-1])
        return "US"

    # ---- loading & drawing (logic preserved) -----------------------------

    def load_symbol(self, symbol=None):
        symbol = (symbol if isinstance(symbol, str) else self.symbol_input.text())
        symbol = symbol.strip().upper()
        if not symbol:
            return
        if self._fetcher is not None and self._fetcher.isRunning():
            return
        start = self.start_date.date()
        end = self.end_date.date()
        if end < start:
            QtWidgets.QMessageBox.warning(
                self, "Invalid range", "The 'To' date is before the 'From' date.")
            return
        start = start.toString("yyyy-MM-dd")
        end = end.toString("yyyy-MM-dd")
        self._set_loading(True, symbol)
        self._fetcher = _Fetcher(symbol, start, end, self)
        self._fetcher.loaded.connect(self._on_loaded)
        self._fetcher.failed.connect(self._on_failed)
        self._fetcher.finished.connect(self._on_fetch_finished)
        self._fetcher.start()

    def _on_loaded(self, symbol, df):
        self._df = df
        for item in (self._vol_items + self._panel_items + self._price_items):
            fplt.remove_primitive(item)
        self._vol_items = []
        self._panel_items = []
        self._price_items = []
        self._compare_df = None          # stale: index refetched for the new range
        # reset each viewbox datasrc so a new symbol isn't outer-join merged
        # into the previous one's dates (wrecks y-zoom across markets)
        for ax in self.axs:
            ax.vb.datasrc = None
            ax.vb.standalones.clear()

        vol = fplt.volume_ocv(df[["open", "close", "volume"]], ax=self.ax_vol)
        self._vol_items = [vol]
        self._render_panels()
        self._render_price()             # candles, or %-compare if an index is on

        self._apply_log()
        fplt.refresh()
        self._apply_timeframe()

        self.current_symbol = symbol
        self.symbol_input.setText(symbol)
        self._update_quote(symbol, df)
        self.setWindowTitle(f"{self.TITLE}  --  {symbol}")
        self._set_loading(False)
        if self._compare_ticker:
            self._load_compare()

    def _in_compare_mode(self):
        return bool(self._compare_ticker and self._compare_df is not None)

    def _render_price(self):
        """Draw the price panel. With an index comparison active it switches to a
        rebased percent-change view (stock area + index line + MAs in %); without
        one it's the usual candlesticks + MA lines + cross markers."""
        if self._df is None:
            return
        vb = self.ax.vb
        had = vb.datasrc is not None
        vr = vb.targetRect()
        x0, x1 = (vr.left(), vr.right()) if had else (None, None)
        for item in self._price_items:
            fplt.remove_primitive(item)
        self._price_items = []
        # fresh datasrc for the price panel so re-plots don't merge into stale data
        vb.datasrc = None
        vb.standalones.clear()

        df = self._df
        fast, slow = self._ma_periods()
        method = self._ma_method()
        if self._in_compare_mode():
            self._render_percent(df, fast, slow, method, x0)
        else:
            self._render_candles(df, fast, slow, method)
        self._update_legend()
        # percent mode fills ~90% of the panel; candle mode keeps ~80% headroom
        vb.v_zoom_scale = (self.COMPARE_FILL if self._in_compare_mode()
                           else 2 * (self.PRICE_MAX_FRACTION - 0.5))
        # keep the current x window and refit y to whatever is now plotted (the
        # scale changes drastically between price candles and percent lines)
        if x0 is not None and vb.datasrc is not None:
            vb.update_y_zoom(x0, x1)
        # candle pictures are cached and only regenerate on a range change; since
        # we preserve the zoom (no range change), nudge them to redraw -- otherwise
        # a freshly re-added candlestick (e.g. toggling Line off) stays blank
        fplt._repaint_candles()

    def _render_candles(self, df, fast, slow, method):
        if self._line_mode():
            line = fplt.plot(df["close"], ax=self.ax, color="#e8eaed", width=1.6)
            try:
                line.setFillLevel(float(df["low"].min()))   # subtle area to baseline
                line.setFillBrush(pg.mkBrush("#4f8cff18"))
            except Exception:
                pass
            self._price_items.append(line)
        else:
            self._price_items.append(
                fplt.candlestick_ochl(df[["open", "close", "high", "low"]], ax=self.ax))
        self._price_items.append(
            fplt.plot(data.moving_average(df["close"], fast, method),
                      ax=self.ax, color=MA_FAST, width=1.5))
        self._price_items.append(
            fplt.plot(data.moving_average(df["close"], slow, method),
                      ax=self.ax, color=MA_SLOW, width=1.5))
        golden, death = data.ma_cross_markers(df, fast, slow, method)
        self._plot_cross_markers(golden, UP, "^")
        self._plot_cross_markers(death, DOWN, "v")

    def _render_percent(self, df, fast, slow, method, x0=None):
        """Rebased percent-change comparison (like the reference): stock and index
        both as % change from the start of the VISIBLE window, MAs in % too. The
        stock is a filled area, the index a line, all on a percent y-axis."""
        stock = df["close"]
        index = self._compare_df["close"]
        common = stock.index.intersection(index.index)
        if len(common) == 0:
            self._render_candles(df, fast, slow, method)
            return
        # base = the leftmost visible bar, so % is bounded to what's on screen
        pos = 0 if x0 is None else max(0, min(int(round(x0)), len(stock) - 1))
        base_date = stock.index[pos]
        base_s = float(stock.iloc[pos])
        iloc = index.index.get_indexer([base_date], method="nearest")
        base_i = float(index.iloc[iloc[0]]) if len(iloc) and iloc[0] != -1 \
            else float(index.iloc[0])

        def pct(series, base):
            return (series / base - 1.0) * 100.0

        # stock %: plot first so the viewbox datasrc spans the full stock range
        stock_line = fplt.plot(pct(stock, base_s), ax=self.ax, color="#4f8cff", width=1.5)
        try:
            stock_line.setFillLevel(0)
            stock_line.setFillBrush(pg.mkBrush("#1f6feb44"))   # translucent mountain
        except Exception:
            pass
        idx_line = fplt.plot(pct(index.loc[common], base_i),
                             ax=self.ax, color=COMPARE, width=1.5)
        maf = fplt.plot(pct(data.moving_average(stock, fast, method), base_s),
                        ax=self.ax, color="#ef4444", width=1.4)        # ma fast (red)
        mas = fplt.plot(pct(data.moving_average(stock, slow, method), base_s),
                        ax=self.ax, color="#7fb8ff", width=1.4)        # ma slow (lt blue)
        self._price_items += [stock_line, idx_line, maf, mas]

    def _on_xrange_settled(self):
        """Pan/zoom settled: in percent mode, rebase to the new visible window."""
        if self._rebasing or not self._in_compare_mode():
            return
        self._rebasing = True
        try:
            self._render_price()
        finally:
            self._rebasing = False

    def _render_panels(self):
        if self._df is None:
            return
        for item in self._panel_items:
            fplt.remove_primitive(item)
        self._panel_items = []
        close = self._df["close"]
        rsi_series = data.rsi(close, self.RSI_PERIOD)
        self._panel_items.append(
            fplt.plot(rsi_series, ax=self.ax_rsi, color=ACCENT, width=1.5))
        macd_line, signal_line, hist = data.macd(
            close, self.MACD_FAST, self.MACD_SLOW, self.MACD_SIGNAL)
        mask = hist.notna().values
        xs = np.arange(len(hist))[mask]
        heights = hist.values[mask]
        brushes = [pg.mkBrush(UP) if v >= 0 else pg.mkBrush(DOWN) for v in heights]
        bars = pg.BarGraphItem(x=xs, height=heights, width=0.7,
                               brushes=brushes, pen=pg.mkPen(None))
        bars.ax = self.ax_macd
        bars.setZValue(-10)
        self.ax_macd.addItem(bars)
        self._panel_items.append(bars)
        self._panel_items.append(
            fplt.plot(macd_line, ax=self.ax_macd, color=MA_FAST, width=1.5))
        self._panel_items.append(
            fplt.plot(signal_line, ax=self.ax_macd, color=MA_SLOW, width=1.5))

    def _plot_cross_markers(self, positions, arrow_color, arrow_style):
        if not len(positions):
            return
        ring = fplt.plot(positions, ax=self.ax, color="#ffff00", style="o", width=3)
        ring.setSymbolBrush(pg.mkBrush(0, 0, 0, 0))
        ring.setSymbolPen(pg.mkPen("#ffff00", width=2))
        ring.setSymbolSize(26)
        ring.setZValue(self._RING_Z)
        arrow = fplt.plot(positions, ax=self.ax, color=arrow_color,
                          style=arrow_style, width=2)
        arrow.setSymbolSize(13)
        arrow.setZValue(self._ARROW_Z)
        self._price_items += [ring, arrow]

    # ---- sidebar updates -------------------------------------------------

    def _update_quote(self, symbol, df):
        last = float(df["close"].iloc[-1])
        prev = float(df["close"].iloc[-2]) if len(df) > 1 else last
        chg = last - prev
        pct = (chg / prev * 100.0) if prev else 0.0
        up = chg >= 0
        col = UP if up else DOWN
        arrow = "▲" if up else "▼"
        exch = self._exchange(symbol)
        self.q_ticker.setText(symbol)
        self.q_exch.setText(exch)
        self.q_close.setText(f"{last:,.2f}")
        self.q_pill.setText(f"{arrow} {chg:+.2f}  ({pct:+.2f}%)")
        self.q_pill.setStyleSheet(
            f"color:{col}; font-family:'JetBrains Mono','Consolas',monospace; font-size:12px;")
        self.hdr_symbol.setText(f"{symbol} · {exch}")

    def _update_legend(self):
        tag = "EMA" if self._ma_method() == "ema" else "SMA"
        if self._in_compare_mode():
            name = self._compare_name(self._compare_ticker)
            rows = [("#4f8cff", "—", f"{self.current_symbol or 'Stock'}  %"),
                    (COMPARE, "—", f"{name}  %"),
                    ("#ef4444", "—", f"{tag}{self._fast}"),
                    ("#7fb8ff", "—", f"{tag}{self._slow}")]
        else:
            rows = [(MA_FAST, "—", f"{tag}{self._fast}"),
                    (MA_SLOW, "—", f"{tag}{self._slow}"),
                    (UP, "▲", "Golden cross"),
                    (DOWN, "▼", "Death cross")]
        html = "".join(
            f"<div style='margin:5px 0;'>"
            f"<span style=\"color:{c};font-family:'JetBrains Mono';font-size:13px;\">{g}</span>"
            f"&nbsp;&nbsp;<span style='color:#aab0b8;font-size:12px;'>{lbl}</span></div>"
            for c, g, lbl in rows)
        self.legend_label.setText(html)

    # ---- MA periods / method ---------------------------------------------

    def _ma_periods(self):
        return self._fast, self._slow

    def _ma_method(self):
        return "ema" if self.ema_checkbox.isChecked() else "sma"

    def _open_search(self):
        """Open the symbol-lookup window; picking a result loads it here."""
        self._search_dialog = SymbolSearchDialog(self, self._use_symbol)
        self._search_dialog.show()

    def _use_symbol(self, symbol):
        self.symbol_input.setText(symbol)
        self.load_symbol(symbol)

    def _line_mode(self):
        return self.line_checkbox.isChecked()

    def _on_chart_type_changed(self):
        if self._df is not None:
            self._render_price()

    def _select_preset(self, idx):
        self._fast, self._slow = self.MA_PRESETS[idx][1:3]
        self.fast_tile[1].setText(str(self._fast))
        self.slow_tile[1].setText(str(self._slow))
        self._on_ma_changed()

    def _on_ma_changed(self):
        if self._df is None:
            return
        self._render_price()

    # ---- timeframe -------------------------------------------------------

    def _set_timeframe(self, idx):
        self._tf = self.TIMEFRAMES[idx][1]
        self._apply_timeframe()

    def _apply_timeframe(self):
        vb = self.ax.vb
        if vb.datasrc is None:
            return
        total = len(vb.datasrc.df)
        n = self._tf
        x0 = 0 if (n is None or n >= total) else total - n
        vb.update_y_zoom(x0, total)

    # ---- log toggle ------------------------------------------------------

    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(ev)

    def toggle_log(self):
        self._apply_log()

    def _apply_log(self):
        # log is meaningless on the percent-change axis (negative values), so it's
        # forced linear whenever a comparison is active
        self.ax.setLogMode(
            y=self.log_checkbox.isChecked() and not self._in_compare_mode())

    # ---- zoom ------------------------------------------------------------

    def _zoom_x(self, scale_fact):
        vb = self.ax.vb
        if vb.datasrc is None:
            return
        vr = vb.targetRect()
        center = QtCore.QPointF((vr.left() + vr.right()) / 2.0,
                                (vr.top() + vr.bottom()) / 2.0)
        vb.zoom_rect(vr, scale_fact, center)

    def _reset_zoom(self):
        if self.ax.vb.datasrc is None:
            return
        fplt.refresh()
        self._apply_timeframe()

    # ---- crosshair readout ----------------------------------------------

    def _crosshair_info(self, x, y, xtext, ytext):
        df = self._df
        if df is None or len(df) == 0:
            return "", ""
        idx = max(0, min(int(round(x)), len(df) - 1))
        ds = getattr(self.ax.vb, "datasrc", None)
        if ds is not None and getattr(ds, "df", None) is not None and len(ds.df):
            i = max(0, min(int(round(x)), len(ds.df) - 1))
            ts = pd.Timestamp(ds.x.iloc[i])
            loc = df.index.get_indexer([ts], method="nearest")
            if len(loc) and loc[0] != -1:
                idx = loc[0]
        row = df.iloc[idx]
        o, hi, lo, c = (float(row["open"]), float(row["high"]),
                        float(row["low"]), float(row["close"]))
        sp = "&nbsp;"
        date = str(df.index[idx])[:10]
        lab = f"color:{MUT2};"
        line1 = (f"<span style='{lab}'>O</span> {o:.2f}{sp*3}"
                 f"<span style='{lab}'>H</span> {hi:.2f}{sp*3}"
                 f"<span style='{lab}'>L</span> {lo:.2f}")
        change = ""
        if idx > 0:
            prev = float(df["close"].iloc[idx - 1])
            chg = c - prev
            pct = (chg / prev * 100.0) if prev else 0.0
            col = UP if chg > 0 else (DOWN if chg < 0 else MUT)
            arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "•")
            change = (f"{sp*3}<span style='color:{col};'>{arrow} {chg:+.2f} "
                      f"({pct:+.2f}%)</span>")
        line2 = (f"<span style='{lab}'>C</span> "
                 f"<span style='color:{TXT};font-weight:600;'>{c:.2f}</span>{change}")
        self.info_box.setText(
            f"<div style='color:{MUT2}; font-size:10pt'>{date}</div>"
            f"<div>{line1}</div><div style='margin-top:2px;'>{line2}</div>")
        self.info_box.adjustSize()
        self.info_box.show()
        return "", ""

    # ---- index comparison -------------------------------------------------

    def _compare_name(self, ticker):
        for _market, items in self.COMPARE_INDICES:
            for name, tkr in items:
                if tkr == ticker:
                    return name
        return ticker

    def _disable_compare(self):
        if self.compare_combo.currentIndex() == 0:
            self._compare_ticker = None
            self._compare_df = None
            self._apply_log()
            self._render_price()         # back to candlesticks
        else:
            self.compare_combo.setCurrentIndex(0)

    def _on_compare_changed(self):
        ticker = self.compare_combo.currentData()
        self._compare_ticker = ticker
        if not ticker:
            self._compare_df = None
            self._apply_log()
            self._render_price()         # back to candlesticks
            return
        self._load_compare()             # on arrival, switch to percent mode

    def _load_compare(self):
        if not self._compare_ticker:
            return
        if self._compare_fetcher is not None and self._compare_fetcher.isRunning():
            return
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        self._compare_fetcher = _Fetcher(self._compare_ticker, start, end, self)
        self._compare_fetcher.loaded.connect(self._on_compare_loaded)
        self._compare_fetcher.failed.connect(self._on_compare_failed)
        self._compare_fetcher.finished.connect(self._on_compare_finished)
        self._compare_fetcher.start()

    def _on_compare_loaded(self, ticker, df):
        if ticker != self._compare_ticker:
            return
        self._compare_df = df
        self._apply_log()                # linear before plotting percent values
        self._render_price()             # switch the price panel to percent mode

    def _on_compare_failed(self, ticker, message):
        QtWidgets.QMessageBox.warning(self, "Index load failed", message)

    def _on_compare_finished(self):
        if self._compare_fetcher is not None:
            self._compare_fetcher.deleteLater()
            self._compare_fetcher = None

    # ---- fetch lifecycle / lock ------------------------------------------

    def _on_failed(self, symbol, message):
        QtWidgets.QMessageBox.warning(self, "Load failed", message)
        self._set_loading(False)

    def _on_fetch_finished(self):
        if self._fetcher is not None:
            self._fetcher.deleteLater()
            self._fetcher = None

    def _set_loading(self, loading, symbol=None):
        for w in getattr(self, "_lockable", []):
            w.setEnabled(not loading)
        self.load_button.setText("Loading..." if loading else "Load")


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    # finplot chart colors to match the design
    fplt.background = PANEL
    fplt.odd_plot_background = PANEL
    fplt.foreground = "#3a3f4b"               # axis lines / grid (subtle)
    fplt.cross_hair_color = "#6a707a"
    fplt.candle_bull_color = UP
    fplt.candle_bear_color = DOWN
    fplt.candle_bull_body_color = UP          # filled up candles
    fplt.candle_bear_body_color = DOWN
    fplt.volume_bull_color = "#22c98a66"
    fplt.volume_bear_color = "#f6465d66"
    fplt.volume_bull_body_color = "#22c98a66"
    # sub-panel labels: dark translucent, muted text (match the design)
    fplt.legend_border_color = "#ffffff14"
    fplt.legend_fill_color = "#0a0a0dcc"
    fplt.legend_text_color = MUT

    win = SpikeWindow()
    fplt.show(qt_exec=False)     # our QApplication owns the event loop
    win.showFullScreen()        # launch full screen (Exit button / Esc to quit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
