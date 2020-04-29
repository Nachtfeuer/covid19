@echo off
set PYTHONPATH=%CD%

rem ensure packages
pip install -r requirements.txt

rem Validating styleguide I
flake8 --max-line-length=100 --ignore=E402 visualize.py
if %ERRORLEVEL% gtr 0 Exit /B

rem Validating styleguide II
pylint --rcfile=pylint.rcfile .
if %ERRORLEVEL% gtr 0 Exit /B

rem Checking for vulnerations
bandit -r engine tests
if %ERRORLEVEL% gtr 0 Exit /B

rem Show Complexity > A
radon cc --show-complexity --min A .
