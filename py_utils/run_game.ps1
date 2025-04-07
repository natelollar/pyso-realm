# Run Game
$UTILS_DIR= $PWD.Path
Write-Host "Utils directory: $UTILS_DIR"
Set-Location $UTILS_DIR

Write-Host "Running game..."
& "$UTILS_DIR\dist\rpg_game.exe"
Read-Host "Press Enter to continue..."