@echo off
echo Building DKCModInstaller.exe...
echo.

cd /d "%~dp0"

pyinstaller --onefile --name DKCModInstaller --console --clean ^
    --add-data "pe_patcher.py;." ^
    --add-data "hex_gen.py;." ^
    --add-data "cpk_tools.py;." ^
    --add-data "data_tables.py;." ^
    --add-data "stagebase_parser.py;." ^
    mod_installer.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo Copying DKCModInstaller.exe to parent directory...
copy /y "dist\DKCModInstaller.exe" "..\DKCModInstaller.exe"

echo.
echo Build complete! DKCModInstaller.exe is ready in the parent directory.
pause
