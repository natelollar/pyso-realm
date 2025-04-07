@echo off
echo Running PowerShell file...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0py_build.ps1"
pause