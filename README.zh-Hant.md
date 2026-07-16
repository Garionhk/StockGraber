# StockGraber

[English](README.md) | **繁體中文**

一個桌面股票圖表程式，以 [finplot](https://github.com/highfestiva/finplot) 嵌入
[PySide6](https://doc.qt.io/qtforpython/)（Qt）視窗，採用深色「交易終端機」風格。
它透過 `yfinance` 由 Yahoo Finance 取得每日 OHLC 資料，於本機 SQLite 快取，
並繪製含成交量的 K 線、移動平均交叉、RSI／MACD 子面板，以及百分比變化的
指數比較檢視。程式以**全螢幕**啟動。

> ⚠️ **並非投資建議。** StockGraber 是圖表／學習工具。它所繪製的指標與訊號
> （黃金／死亡交叉、RSI、MACD 等）只是常見的技術分析慣例，並非買賣建議。
> 沒有任何指標能可靠地預測價格。

---

## 功能特色

- **深色終端機介面** — 標題列、指令列、垂直排列的圖表欄
  （價格／成交量／RSI／MACD），以及側邊欄卡片（報價／指標／比較／圖例／日期範圍）。
  全螢幕啟動；以 **Exit** 按鈕或 **Esc** 鍵退出。
- **雙語介面** — 一鍵切換**英文**與**繁體中文**，整個介面同步更新。
- **最近使用代碼** — 每個成功繪製過的代碼都會記錄於本機資料庫，並以可點擊的
  標籤列出，一鍵即可重新載入。
- **真實資料並快取** — 由 Yahoo Finance 取得每日 OHLC，存於本機 SQLite，
  重複載入即時完成，且只下載缺少的日期。
- **K 線 + 成交量** — 價格面板加上成交量子面板，依漲跌日上色。
- **移動平均交叉** — 預設快／慢線組合（9/21、20/50、50/200、100/200），
  以「快線／慢線」數值方塊顯示；可切換 **SMA ↔ EMA**。
- **黃金／死亡交叉標記** — 在快線穿越慢線處顯示亮黃圈的 ▲（看漲）／▼（看跌）箭頭。
- **RSI 與 MACD 子面板** — RSI (14) 含 30–70 區帶，MACD (12,26,9) 含紅綠柱狀圖；
  成交量／RSI／MACD 面板皆可個別顯示或隱藏。
- **指數比較（百分比模式）** — 選取一個市場指數（美國／加拿大／香港／全球），
  價格面板即切換為**重新基準的百分比變化**檢視：個股為填色區域、指數為線、
  移動平均亦以百分比顯示，採用百分比座標軸 — 以可見視窗起點為基準，
  並隨平移／縮放重新調整（約佔高度 90%）。
- **游標讀數** — 一個方框顯示當日 O/H/L/C，以及相對前一日的漲跌（▲/▼ 並上色）。
- **導覽操作** — 拖曳平移、滾輪或 `+`/`−`/`Reset` 按鈕縮放、時間範圍分段控制
  （1M…MAX），以及對數／線性切換。K 線模式下，最高的可見柱保持在面板約 80% 高度。
- **流暢介面** — 所有網路下載皆在背景執行緒進行，視窗在載入新代碼時不會卡住。

---

## 系統需求

- **Python 3.10+**（以 3.12 開發）
- Windows / macOS / Linux（以 Windows 10 開發）
- 套件：`PySide6`、`finplot`、`pandas`、`numpy`、`yfinance`
  （`pyqtgraph` 由 finplot 一併安裝）
- 首次取得各代碼／日期範圍時需要網路連線

---

## 安裝

```bash
pip install PySide6 finplot pandas numpy yfinance
```

> **Qt 綁定說明：** finplot 會安裝 **PyQt6**，而本程式使用 **PySide6**。
> 程式在啟動時固定 `PYQTGRAPH_QT_LIB=PySide6`，因此兩者一致 — 你無需自行設定。

### Windows 輔助批次檔

在 Windows 上可直接雙擊隨附的批次檔：

| 批次檔 | 用途 |
|---|---|
| `setup.bat` | 安裝所有相依套件（含 PyInstaller 與 Pillow）。 |
| `run.bat` | 由原始碼執行程式。 |
| `build.bat` | 建置獨立的 `dist\StockGraber.exe`。 |

---

## 使用方式

```bash
python StockGraber.py
```

（在 Windows 上也可雙擊 `run.bat`）

程式以**全螢幕**啟動並載入 `AAPL`。輸入代碼後按 **Enter**（或點 **Load**）即可
切換到其他標的。以右上角的 **✕ Exit** 按鈕或 **Esc** 鍵退出。

### 股票代碼

請使用 Yahoo Finance 的代碼格式：

| 市場 | 範例 | 說明 |
|---|---|---|
| 美國 | `AAPL`、`MSFT`、`SPY` | 純代碼 |
| 香港 | `0005.HK` | `.HK` 後綴 |
| 加拿大（TSX） | `RY.TO` | `.TO` 後綴 |
| 指數 | `^GSPC`、`^HSI` | `^` 前綴 |

---

## 操作控制

**指令列（上方）**

| 控制項 | 功能 |
|---|---|
| **代碼欄 + Load** | 要繪製的代碼（按 Enter 或 **Load**）。 |
| **🔍 Find** | 開啟搜尋視窗，依公司名稱跨市場查詢代碼，再「複製代碼」或「套用至圖表」。 |
| **時間範圍** | 分段 `1M / 3M / 6M / 1Y / 5Y / MAX` — 設定可見視窗。 |
| **Zoom − / + / Reset** | 縮小／放大日期範圍，或重設為預設檢視。 |
| **中文 / EN** | 切換介面語言（英文 ↔ 繁體中文）。 |
| **✕ Exit** | 退出程式（也可按 **Esc**）。 |

**側邊欄 — 指標卡片**

| 控制項 | 功能 |
|---|---|
| **移動平均交叉** | 預設快／慢線組合（9/21、20/50、50/200、100/200）。 |
| **快線 / 慢線** | 顯示目前週期的唯讀方塊。 |
| **EMA** | 改用指數移動平均，而非簡單移動平均。 |
| **成交量 / RSI / MACD** | 顯示或隱藏各子面板。 |
| **對數刻度** | 切換對數／線性價格刻度（比較模式下會自動關閉）。 |

**側邊欄 — 其他卡片**

| 卡片 | 功能 |
|---|---|
| **報價** | 代碼、交易所、最新收市價、相對前一日的漲跌。 |
| **最近使用代碼** | 曾繪製過的代碼標籤 — 按一下重新載入，右鍵移除。目前代碼會以醒目顏色標示。 |
| **比較** | 選取指數 → 進入百分比比較模式；按 **Off** 還原。 |
| **圖例** | 目前繪製線條的顏色對照。 |
| **日期範圍** | 由／至日期（只會下載缺少的日期）。 |

**滑鼠**

- **拖曳** — 左右平移瀏覽歷史
- **滾輪** — 縮放；**Ctrl+滾輪** — 垂直縮放
- **右鍵拖曳** — 框選縮放
- **游標停留** — 在價格面板左上角顯示 O/H/L/C 與漲跌讀數方框

---

## 指標與訊號（速查）

| 訊號 | 慣例含義 |
|---|---|
| **黃金交叉**（▲） | 快線**向上**穿越慢線 — 看漲。 |
| **死亡交叉**（▼） | 快線**向下**穿越慢線 — 看跌。 |
| **RSI > 70 / < 30** | 超買／超賣。 |
| **MACD 線 vs. 訊號線** | 動能轉強／轉弱。 |

各組合特性：**50/200** = 長線，訊號最少、最受信賴；**20/50** = 波段交易；
**10/20** 與 **5/10** = 短線，訊號較多、雜訊也較多（容易來回假訊號）；
**9/21** 與 **12/26** = 常見的短中線組合，傳統上以 EMA 計算。

---

## 指數比較清單

- **美國** — S&P 500 (`^GSPC`)、道瓊 (`^DJI`)、Nasdaq 綜合指數
  (`^IXIC`)、Nasdaq 100 (`^NDX`)、Russell 2000 (`^RUT`)、VIX (`^VIX`)
- **加拿大** — S&P/TSX 綜合指數 (`^GSPTSE`)
- **香港** — 恒生指數 (`^HSI`)、恒生中國企業指數 (`^HSCE`)
- **全球／其他** — FTSE 100 (`^FTSE`)、DAX (`^GDAXI`)、CAC 40 (`^FCHI`)、
  日經 225 (`^N225`)、Euro Stoxx 50 (`^STOXX50E`)、ASX 200 (`^AXJO`)、
  Nifty 50 (`^NSEI`)

選取指數後，價格面板會切換為**百分比變化模式**：個股與指數都以可見視窗起點
重新基準為 0%，因此當個股線收在指數線之上，即代表個股表現勝過指數。

---

## 建置獨立的 Windows .exe

雙擊 **`build.bat`**，或執行：

```bash
pip install pyinstaller
build.bat
```

它會產生 **`dist\StockGraber.exe`** — 帶有 StockGraber 圖示的單檔程式，
無需安裝 Python 即可執行。背後會強制使用 PySide6 的 Qt 綁定
（排除 PyQt5/PyQt6，因為 PyInstaller 無法同時打包多個 Qt 綁定）：

```bat
pyinstaller --noconfirm --windowed --onefile --name StockGraber ^
  --icon StockGraber.ico --collect-all finplot --collect-all pyqtgraph ^
  --exclude-module PyQt5 --exclude-module PyQt6 StockGraber.py
```

該 exe 會將 SQLite 快取寫在自身旁邊。建置輸出（`build/`、`dist/`）已被 git 忽略 —
請以 GitHub **Release** 發佈 exe，而非提交進版本庫。

---

## 專案結構

```
StockGraber/
├── StockGraber.py     # 主程式：PySide6 視窗、圖表面板、控制項
├── data.py            # 資料層：yfinance 下載、SQLite 快取、指標
├── StockGraber.ico    # 程式圖示（由 StockGraber.png 產生）
├── setup / run / build.bat   # Windows 輔助批次檔
├── stockgraber.db     # SQLite 快取（首次執行自動建立，已被 git 忽略）
└── README.md
```

### `data.py` — 資料層

- `get_ohlc(symbol, start, end, force_refresh=False)` — 指定日期範圍的每日 OHLC。
  先讀取快取，**只下載缺少的日期**；已存在的資料不會重複下載
  （每個代碼會記錄涵蓋範圍，連無資料的區段，如上市前日期，也不會重複請求）。
- `moving_average(series, period, method)` — SMA 或 EMA。
- `ma_cross_markers(df, fast, slow, method)` — 黃金／死亡交叉點。
- `rsi(close, period=14)` — Wilder's RSI。
- `macd(close, fast=12, slow=26, signal=9)` — MACD 線、訊號線、柱狀圖。
- `record_symbol(symbol)` / `recent_symbols(limit)` / `forget_symbol(symbol)` —
  「最近使用代碼」卡片背後的重用記錄。

資料庫共有三個 SQLite 資料表：`ohlc`（K 線，以 `symbol, date` 為主鍵）、
`coverage`（每個代碼已下載的日期範圍），以及 `history`
（你曾繪製過的代碼，含使用次數與最後使用時間）。

### `StockGraber.py` — 主程式

一個 `SpikeWindow`（QMainWindow），承載四個 x 軸連動的 finplot 面板
（價格／成交量／RSI／MACD），以及深色控制外殼與側邊欄卡片。網路下載在
`QThread` 工作執行緒進行，並透過 Qt 訊號把結果送回 UI 執行緒。圖表項目分為
**volume**、**panel**（RSI+MACD）與 **price**（K 線或百分比線）三組，因此變更
移動平均設定時只會重繪價格面板，不需重新下載，也不會遺失目前縮放。

`SpikeWindow` 上可調整的常數：

| 常數 | 預設 | 用途 |
|---|---|---|
| `INITIAL_SYMBOL` | `"AAPL"` | 啟動時載入的代碼。 |
| `MA_PRESETS` | 4 組 | 交叉預設（標籤、快線、慢線）。 |
| `TIMEFRAMES` | 6 | 指令列時間範圍分段（標籤、柱數）。 |
| `RSI_PERIOD` | `14` | RSI 週期。 |
| `MACD_FAST/SLOW/SIGNAL` | `12/26/9` | MACD 週期。 |
| `PRICE_MAX_FRACTION` | `0.80` | K 線模式：最高柱所在的高度比例。 |
| `COMPARE_FILL` | `0.90` | 百分比模式：填滿面板高度的比例。 |

`data.py` 常數 `DEFAULT_START`（`"2015-01-01"`）設定在未指定起始日期時，
首次抓取一個代碼要回溯多久。

---

## 注意事項與限制

- **價格未經拆股／股息調整**（`auto_adjust=False`）。快取列僅在重新下載時覆寫，
  因此拆股後舊柱會保留原始數值，直到該範圍被重新抓取。
- **指數比較以可見視窗起點為基準**，並隨平移／縮放重新調整；啟用期間會以
  百分比變化檢視取代 K 線。
- **移動平均週期僅限預設**（4 組）；**RSI/MACD 週期固定**（14，以及 12/26/9）。
- 資料品質取決於 Yahoo Finance；偶有缺漏或異常值。

---

## 免責聲明

StockGraber 僅供**教育與資訊用途**，**並非投資建議**。在做出投資決定前，
請自行研究並諮詢合資格的專業人士。市場資料由 Yahoo Finance 提供，
可能有延遲或不準確之處。
