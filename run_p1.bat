@echo off
cd /d "%~dp0"
echo Running P1 benchmark on this machine...
python --version
python p1.py > p1_run_log.txt 2>&1
echo exit code %ERRORLEVEL% >> p1_run_log.txt
echo DONE >> p1_run_log.txt
