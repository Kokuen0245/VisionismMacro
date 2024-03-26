@echo off
REM Install requirements
py -m pip install -r requirements.txt

REM Run main.py
py main.py

REM Pause to keep the command prompt window open after execution
pause
