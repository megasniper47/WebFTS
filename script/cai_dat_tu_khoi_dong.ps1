# Dang ky tac vu Windows de WebFTS tu chay khi dang nhap.
#
# CACH DUNG -- mo PowerShell (KHONG can quyen Administrator) va chay:
#
#     powershell -ExecutionPolicy Bypass -File "D:\Coding\Dự án FTS\WebFTS v4\script\cai_dat_tu_khoi_dong.ps1"
#
# Go bo tac vu:
#
#     powershell -ExecutionPolicy Bypass -File "...\cai_dat_tu_khoi_dong.ps1" -GoBo
#
# GIOI HAN: tai khoan hien tai khong co quyen Administrator nen tac vu chi
# chay duoc KHI DANG NHAP Windows, khong chay duoc tu luc may vua bat. Muon
# chay ma khong can dang nhap thi phai nho quan tri vien cap quyen, roi doi
# -LogonType thanh S4U / Password.

param([switch]$GoBo)

$ErrorActionPreference = 'Stop'

$TenTacVu = 'WebFTS - tu khoi dong'
$Root     = Split-Path -Parent $PSScriptRoot
$Script   = Join-Path $Root 'script\start_webfts.ps1'
$NguoiDung = "$env:USERDOMAIN\$env:USERNAME"

if ($GoBo) {
    if (Get-ScheduledTask -TaskName $TenTacVu -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TenTacVu -Confirm:$false
        Write-Output "Da go bo tac vu '$TenTacVu'."
    } else {
        Write-Output "Khong tim thay tac vu '$TenTacVu' -- khong co gi de go."
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $Script)) {
    Write-Output "LOI: khong thay $Script"
    exit 1
}

Write-Output "Dang ky tac vu cho tai khoan: $NguoiDung"
Write-Output "Script se chay:                $Script"

$act = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $Script) `
    -WorkingDirectory $Root

# Cho 30 giay sau khi dang nhap de o dia va mang san sang
$trg = New-ScheduledTaskTrigger -AtLogOn -User $NguoiDung
$trg.Delay = 'PT30S'

$set = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
    -MultipleInstances IgnoreNew

$prc = New-ScheduledTaskPrincipal -UserId $NguoiDung -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TenTacVu `
    -Action $act -Trigger $trg -Settings $set -Principal $prc `
    -Description 'Khoi dong WebFTS (WebATM.py, cong 8082) khi dang nhap Windows. Cloudflare Tunnel dua ra https://fts.vatmfts.com' `
    -Force | Out-Null

Write-Output ""
Write-Output "DA DANG KY XONG."
Get-ScheduledTask -TaskName $TenTacVu | Format-List TaskName, State

Write-Output "Chay thu ngay bay gio:   Start-ScheduledTask -TaskName '$TenTacVu'"
Write-Output "Xem trang thai:          Get-ScheduledTaskInfo -TaskName '$TenTacVu'"
Write-Output "Xem nhat ky khoi dong:   $Root\logs\webfts_startup.log"
Write-Output "Go bo:                   powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -GoBo"
