# Win AIO by Duy Anh - tai va mo tool bang 1 dong lenh (PowerShell):
#   irm https://raw.githubusercontent.com/laocuumon1982-cpu/WIN-AIO-SHARE/main/aio.ps1 | iex
# Tool luu o %LOCALAPPDATA%\WinAIO (Data cung nam o day); lan sau chay lai chi tai khi co ban moi.
& {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072 } catch {}   # TLS 1.2 cho Win 10 cu

    $repo = 'laocuumon1982-cpu/WIN-AIO-SHARE'
    $dir  = Join-Path $env:LOCALAPPDATA 'WinAIO'
    $exe  = Join-Path $dir 'Win AIO by Duy Anh.exe'
    $verf = Join-Path $dir 'version.txt'
    try {
        Write-Host ''
        Write-Host '  WIN AIO by Duy Anh' -ForegroundColor Red
        Write-Host '  Dang kiem tra ban moi nhat...' -ForegroundColor Gray
        New-Item -ItemType Directory -Force $dir | Out-Null

        $tag = $null
        try {
            $tag = (Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest" -UseBasicParsing -Headers @{ 'User-Agent' = 'WinAIO' }).tag_name
        } catch { }
        $have = if (Test-Path $verf) { (Get-Content $verf -Raw).Trim() } else { '' }

        if (-not (Test-Path $exe) -or ($tag -and $have -ne $tag)) {
            Write-Host "  Dang tai Win AIO $tag (~15 MB)..." -ForegroundColor Yellow
            $tmp = "$exe.tai"
            (New-Object Net.WebClient).DownloadFile("https://github.com/$repo/releases/latest/download/Win-AIO-by-Duy-Anh.exe", $tmp)
            if ((Get-Item $tmp).Length -lt 5MB) { throw 'File tai ve bi loi (qua nho).' }
            try {
                Move-Item -Force $tmp $exe
                if ($tag) { Set-Content -Path $verf -Value $tag -Encoding Ascii }
            } catch {
                Remove-Item $tmp -Force -ErrorAction SilentlyContinue
                Write-Host '  Tool dang mo - dung ban hien co (trong tool bam Cap nhat de len ban moi).' -ForegroundColor Gray
            }
        } else {
            Write-Host "  Da co ban moi nhat $have." -ForegroundColor Gray
        }

        if ($env:WINAIO_NOSTART) { Write-Host "  OK: $exe"; return }
        Write-Host '  Dang mo Win AIO (bam Yes o hop UAC)...' -ForegroundColor Green
        Start-Process -FilePath $exe -WorkingDirectory $dir
    } catch {
        Write-Host ''
        Write-Host ('  LOI: ' + $_.Exception.Message) -ForegroundColor Red
        Write-Host '  Kiem tra mang, hoac tai tay: https://github.com/laocuumon1982-cpu/WIN-AIO-SHARE/releases/latest' -ForegroundColor Yellow
        if ($env:WINAIO_NOSTART) { throw }
    }
}
