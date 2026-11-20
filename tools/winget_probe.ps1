# Kiểm tra ID winget có tồn tại không (chạy trên GitHub Actions)
$ErrorActionPreference = 'Continue'
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Runner chua co winget - cai qua Microsoft.WinGet.Client"
    Install-PackageProvider -Name NuGet -Force | Out-Null
    Install-Module -Name Microsoft.WinGet.Client -Force -Repository PSGallery | Out-Null
    Repair-WinGetPackageManager -Latest -Force -AllUsers
}
winget --version
winget source update --disable-interactivity | Out-Null
$ids = @(
  'UniKey.UniKey','PhamKimLong.UniKey','LongPham.UniKey','EVKey.EVKey','LamQuangMinh.EVKey','lamquangminh.EVKey',
  'RARLab.WinRAR','Mozilla.Firefox','Mozilla.Firefox.vi','Discord.Discord','Zoom.Zoom','Rakuten.Viber','Viber.Viber',
  'DucFabulous.UltraViewer','UltraViewer.UltraViewer','TeamViewer.TeamViewer','Google.GoogleDrive',
  'Microsoft.VCRedist.2015+.x64','Microsoft.VCRedist.2015+.x86','Microsoft.DotNet.Framework.DeveloperPack_4',
  'Microsoft.DotNet.Framework.DeveloperPack.4.8','Microsoft.DirectX','BlueStack.BlueStacks','BlueStacks.BlueStacks',
  'XUANZHI.LDPlayer','XuanZhi.LDPlayer','LDPlayer.LDPlayer','VNGCorp.Zalo'
)
$src = Get-Content win_aio.py -Raw -Encoding UTF8
$ids += ([regex]::Matches($src, '"winget:([^"]+)"') | ForEach-Object { $_.Groups[1].Value }) | Sort-Object -Unique
foreach ($q in 'AnyDesk','LDPlayer','EVKey') { Write-Host "== search $q"; winget search $q --accept-source-agreements --disable-interactivity 2>&1 | Select-Object -Last 8 | ForEach-Object { Write-Host "S  $_" } }
$ids = @('AnyDesk.AnyDesk','AnyDesk.AnyDesk.MSI') + $ids
foreach ($id in $ids) {
    $o = winget show --id $id --exact --accept-source-agreements --disable-interactivity 2>&1 | Out-String
    $v = ([regex]::Match($o, '(?m)^\s*(Version|Phi.n b.n):\s*(.+)$')).Groups[2].Value.Trim()
    $n = ([regex]::Match($o, '(?m)^Found (.+?) \[')).Groups[1].Value
    if ($LASTEXITCODE -eq 0) { Write-Host "CO    $id  | $n | $v" } else { Write-Host "KHONG $id" }
}
