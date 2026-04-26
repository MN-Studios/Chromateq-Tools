@echo off
echo.
echo  _____ _                               _               _____           _
echo /  __ ^| ^|                             ^| ^|             ^|_   _^|         ^| ^|
echo ^| /  \/ ^|__  _ __ ___  _ __ ___   __ _^| ^|_ ___  __ _    ^| ^| ___   ___ ^| ^|___
echo ^| ^|   ^| '_ \^| '__/ _ \^| '_ ` _ \ / _` ^| __/ _ \/ _` ^|   ^| ^|/ _ \ / _ \^| / __^|
echo ^| \__/\ ^| ^| ^| ^| ^| (_) ^| ^| ^| ^| ^| ^| (_^| ^| ^|^|  __/ (_^| ^|   ^| ^| (_) ^| (_) ^| \__ \
echo  \____/_^| ^|_^|_^|  \___/^|_^| ^|_^| ^|_^|\__,_^|\__\___\__,  ^|   \_/\___/ \___/^|_^|___/
echo                                                   ^| ^|
echo                                                   ^|_^|
echo by MeisterJETI
echo A second monitor highly recomended.
echo.

echo Go to Pro DMX 2 Main view!
start "" .\Chromateq\Pro2.exe
timeout /t 5 >nul
echo Is Pro DMX 2 ready (y to continue)?
choice /c Y /n >nul

echo Open Studio DMX via Pro DMX 2 (Tools --^> 3D)!
timeout /t 3 >nul
echo Is Studio DMX up and running (y to continue)?
choice /c Y /n >nul

echo Starting Chromateq to sACN Script...
start "" .\python-3.13.13-embed-amd64\python.exe .\UPD-sACN.py
echo Starting Capture 2024...
start "" ".\Capture 2024\Capture 2024.exe"

echo Waiting 5 seconds...
timeout /t 5 >nul

:Capture
echo "Did Capture 2024 open? (n for no, y for yes)"
choice /c YN >nul
if errorlevel 2 (
    echo Trying again...
	start "" ".\Capture 2024\Capture 2024.exe"
	timeout /t 5 >nul
    goto Capture
)

if errorlevel 1 (
    echo Nice!
)

timeout /t 2 >nul