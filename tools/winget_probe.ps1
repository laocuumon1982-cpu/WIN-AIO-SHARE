# Đo tốc độ winget: mặc định (Delivery Optimization) vs wininet; và thời gian winget show
$ErrorActionPreference = 'Continue'
winget --version
$exp = winget settings export | ConvertFrom-Json
$f = $exp.userSettingsFile; Write-Host "settings: $f"
function T($label, [scriptblock]$b) { $s = [Diagnostics.Stopwatch]::StartNew(); & $b | Out-Null; Write-Host ("{0,-40} {1,6:N1} s" -f $label, $s.Elapsed.TotalSeconds) }
T 'source update' { winget source update --name winget --disable-interactivity }
T 'show VLC (source winget)' { winget show --id VideoLAN.VLC -e --source winget --accept-source-agreements --disable-interactivity }
T 'show VLC (moi nguon)' { winget show --id VideoLAN.VLC -e --accept-source-agreements --disable-interactivity }
$o = winget show --id VideoLAN.VLC -e --source winget --accept-source-agreements --disable-interactivity | Out-String
Write-Host ($o -split "`n" | Select-String 'Version|Installer Url|Installer Type')
Set-Content $f '{ "network": { "downloader": "do" } }'
T 'download VLC - Delivery Optimization' { winget download --id VideoLAN.VLC -e --source winget -d "$env:TEMP\d1" --accept-package-agreements --accept-source-agreements --disable-interactivity }
Set-Content $f '{ "network": { "downloader": "wininet" } }'
T 'download VLC - wininet' { winget download --id VideoLAN.VLC -e --source winget -d "$env:TEMP\d2" --accept-package-agreements --accept-source-agreements --disable-interactivity }
Set-Content $f '{ "network": { "downloader": "do" } }'
T 'download Firefox - Delivery Optimization' { winget download --id Mozilla.Firefox -e --source winget -d "$env:TEMP\d3" --accept-package-agreements --accept-source-agreements --disable-interactivity }
Set-Content $f '{ "network": { "downloader": "wininet" } }'
T 'download Firefox - wininet' { winget download --id Mozilla.Firefox -e --source winget -d "$env:TEMP\d4" --accept-package-agreements --accept-source-agreements --disable-interactivity }
Get-ChildItem "$env:TEMP\d1","$env:TEMP\d2" -Recurse -File | ForEach-Object { Write-Host ("{0} {1:N1} MB" -f $_.Name, ($_.Length/1MB)) }
