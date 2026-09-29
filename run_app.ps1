# Tender Guard — Start Backend and Frontend Services
# Usage: .\run_app.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "             TENDER GUARD (SIH 2026)                        " -ForegroundColor Cyan
Write-Host " AI Recommender of BIS Standards for Procurement Tenders    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Start FastAPI Backend
Write-Host "`n[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory "app\backend" -PassThru

# Wait 2 seconds for backend to initialize
Start-Sleep -Seconds 2

# 2. Start Next.js Frontend
Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory "app\frontend" -PassThru

Write-Host "`n============================================================" -ForegroundColor Yellow
Write-Host " Services Running:" -ForegroundColor Yellow
Write-Host "   • Web UI:      http://localhost:3000" -ForegroundColor White
Write-Host "   • API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "   • Health:      http://localhost:8000/api/health" -ForegroundColor White
Write-Host "`n Press Ctrl+C in this window to stop services." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow

try {
    # Keep script open while processes run
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping background services..." -ForegroundColor Red
    if ($backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }
    if ($frontendProcess -and !$frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force
    }
    Write-Host "Tender Guard services stopped." -ForegroundColor Red
}
