# Run Game Debug
$UTILS_DIR= $PWD.Path
Write-Host "Utils directory: $UTILS_DIR"
Set-Location $UTILS_DIR

Write-Host "Running game..."
& "$UTILS_DIR\dist\rpg_game.exe" *> run_game_debug.log

Write-Host "Error code: $LASTEXITCODE"

Write-Host "Output log contents:"
Get-Content run_game_debug.log

Write-Host "Press Enter to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")