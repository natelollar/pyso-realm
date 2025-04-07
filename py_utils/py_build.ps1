# Run Python Game Build
$UTILS_DIR= $PWD.Path
$BASE_DIR = Split-Path -Parent $UTILS_DIR
Write-Host "Base directory: $BASE_DIR"
Write-Host "Utils directory: $UTILS_DIR"
Set-Location $UTILS_DIR

Write-Host "Running Python game build script..."
# Run PyInstaller with output redirection
# Overwrite previous build
# Redirect both standard outputs to log.
& "$BASE_DIR\.venv\Scripts\python.exe" `
  "$BASE_DIR\.venv\Scripts\pyinstaller.exe" `
  "$BASE_DIR\py_utils\rpg_game.spec" `
  "$BASE_DIR\src\rpg_game.py" `
  -y `
  *> py_build.log

# Show error code
Write-Host "Error code: $LASTEXITCODE"

# Display logs
Write-Host "Output log contents:"
Get-Content py_build.log

# Wait for user input before closing
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")