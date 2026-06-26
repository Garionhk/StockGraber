@echo off
REM Build a standalone Windows executable: dist\StockGraber.exe
REM Forces the PySide6 Qt binding (PyQt5/PyQt6 are excluded so PyInstaller
REM doesn't choke on multiple Qt bindings).
setlocal
set QT_API=PySide6
set PYQTGRAPH_QT_LIB=PySide6

echo Building StockGraber.exe (this can take a few minutes)...
python -m PyInstaller --noconfirm --windowed --onefile --name StockGraber --icon StockGraber.ico --collect-all finplot --collect-all pyqtgraph --exclude-module PyQt5 --exclude-module PyQt6 StockGraber.py

if errorlevel 1 (
  echo.
  echo Build FAILED.
  pause
  exit /b 1
)

echo.
echo Done. See dist\StockGraber.exe
pause
