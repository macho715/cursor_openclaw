@echo off
set "LOG=%USERPROFILE%\AppData\Local\Temp\stack_test.txt"
echo [%date% %time%] test-write started >> "%LOG%"
echo Wrote to %LOG%
pause
