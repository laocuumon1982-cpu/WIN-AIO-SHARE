$ErrorActionPreference = 'Continue'
foreach ($r in 'storytold/craft-launcher','storytold/wordcraft','storytold/gridcraft','storytold/deckcraft','storytold/pdfcraft') {
  try {
    $rel = Invoke-RestMethod "https://api.github.com/repos/$r/releases/latest" -Headers @{ 'User-Agent'='WinAIO'; 'Authorization'="Bearer $env:GH_TOKEN" }
    Write-Host "== $r $($rel.tag_name)"
    $rel.assets | ForEach-Object { Write-Host ("A  {0}  {1:N1}MB  {2}" -f $_.name, ($_.size/1MB), $_.browser_download_url) }
  } catch { Write-Host "== $r LOI $($_.Exception.Message)" }
}
foreach ($id in 'WhatsApp.WhatsApp','9NKSQGP7F2NH') {
  $src = if ($id -match '^9') { 'msstore' } else { 'winget' }
  $o = winget show --id $id -e --source $src --accept-source-agreements --disable-interactivity 2>&1 | Out-String
  Write-Host "== $id ($src) exit $LASTEXITCODE"
  Write-Host (($o -split "`n") | Select-String 'Found|Version|Installer Url|Installer Type|Publisher:' | Out-String)
}
foreach ($q in 'WhatsApp','ArtCraft','WordCraft') { Write-Host "== search $q"; winget search $q --source winget --accept-source-agreements --disable-interactivity 2>&1 | Select-Object -Last 6 | ForEach-Object { Write-Host "S  $_" } }
