@echo off
REM Install all dependencies needed to run and build StockGraber.
echo Installing dependencies...
python -m pip install --upgrade PySide6 finplot pandas numpy yfinance pyinstaller pillow
echo.
echo Done.
pause
