# Khoi dong WebFTS (WebATM.py) - dung cho Task Scheduler chay khi dang nhap.
#
# Script nay:
#   - Kiem tra cong 8082 da co ai chiem chua (tranh chay hai ban cung luc)
#   - Doi o dia/thu muc du an san sang (khi bat may, o D: co the chua mount)
#   - Chay ung dung bang Python cua moi truong ao (KHONG dung "py" -- tren may
#     nay "py" tro toi mot ban Python da bi xoa)
#   - Ghi log ra logs\webfts_startup.log, giu lai 5 ban gan nhat
#
# Chay thu bang tay:
#   powershell -ExecutionPolicy Bypass -File "D:\Coding\Dự án FTS\WebFTS v4\script\start_webfts.ps1"

$ErrorActionPreference = 'Stop'

$Root    = Split-Path -Parent $PSScriptRoot      # goc du an
$Python  = Join-Path $Root '.venv\Scripts\python.exe'
$App     = Join-Path $Root 'WebATM.py'
$LogDir  = Join-Path $Root 'logs'
$LogFile = Join-Path $LogDir 'webfts_startup.log'
$Port    = 8082

function Ghi([string]$msg) {
    $dong = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Write-Output $dong
    try { Add-Content -LiteralPath $LogFile -Value $dong -Encoding utf8 } catch { }
}

# --- Chuan bi thu muc log, xoay vong giu 5 ban ---------------------------
if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
if ((Test-Path -LiteralPath $LogFile) -and ((Get-Item -LiteralPath $LogFile).Length -gt 2MB)) {
    $cu = Join-Path $LogDir ("webfts_startup_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
    Move-Item -LiteralPath $LogFile -Destination $cu -Force
    Get-ChildItem -LiteralPath $LogDir -Filter 'webfts_startup_*.log' |
        Sort-Object LastWriteTime -Descending | Select-Object -Skip 5 |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

Ghi "=== Task Scheduler goi start_webfts.ps1 ==="

# --- Doi thu muc du an san sang ------------------------------------------
# Khi may vua khoi dong, o dia D: co the chua san sang ngay.
$san_sang = $false
foreach ($lan in 1..30) {
    if ((Test-Path -LiteralPath $App) -and (Test-Path -LiteralPath $Python)) { $san_sang = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $san_sang) {
    Ghi "LOI: sau 60 giay van khong thay $App hoac $Python -- dung lai."
    exit 1
}

# --- Da co ban nao dang chay chua? ---------------------------------------
$dang_chay = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($dang_chay) {
    $p = Get-Process -Id $dang_chay[0].OwningProcess -ErrorAction SilentlyContinue
    Ghi ("Cong {0} da co tien trinh chiem (PID {1} - {2}). Khong chay them ban nua." -f `
         $Port, $dang_chay[0].OwningProcess, $(if ($p) { $p.ProcessName } else { '?' }))
    exit 0
}

# --- Chay ung dung -------------------------------------------------------
Ghi "Khoi dong: $Python $App"
Set-Location -LiteralPath $Root
$env:PYTHONUTF8 = '1'          # duong dan du an co dau tieng Viet
$env:PYTHONIOENCODING = 'utf-8'

& $Python $App *>&1 | ForEach-Object { Ghi $_ }

Ghi "Ung dung da dung (ma thoat $LASTEXITCODE)."
exit $LASTEXITCODE
