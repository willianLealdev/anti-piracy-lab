# ============================================================
# PAINEL LOCAL (ferramenta do "pirata") -> aponta para o CORE
# que esta ONLINE na VPS (o "provedor" simulado).
# ============================================================
# Mude a URL abaixo para o dominio do CORE na VPS, se precisar.
$env:CORE_URL = "https://servidor-tv-sky-servidor-tv-sky.sbporu.easypanel.host"

# O Windows tem PORT=3000 global; sobrescreve para a porta do painel.
$env:PORT = "5050"
$env:HOST = "0.0.0.0"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " PAINEL LOCAL (ferramenta do pirata)" -ForegroundColor Yellow
Write-Host " CORE (provedor) online em: $env:CORE_URL" -ForegroundColor Green
Write-Host " Painel local em: http://localhost:5050" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan

python app.py
