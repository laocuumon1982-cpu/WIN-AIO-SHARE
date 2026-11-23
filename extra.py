"""Win AIO by Duy Anh - chức năng v2.6:
sửa lỗi Windows 1 chạm, dọn Win 11, font tiếng Việt, chuyển phần mềm sang Win mới, driver lỗi,
thiết lập máy mới, nhiệt độ CPU, test hiệu năng (ổ cứng + CPU), USB boot Ventoy.
Dùng chung H / job / data_dir của mgr.py."""
import ctypes
import json
import os
import re
import shutil
import subprocess
import threading
import time
import zipfile
from pathlib import Path

import mgr
from mgr import H, absp, data_dir, fake, human

NOWIN = 0x08000000


def _ps(script, timeout=900):
    return H["ps"](script, timeout=timeout)


def _decode(b):
    if b.count(b"\x00") > len(b) // 4:                 # sfc / một số lệnh in UTF-16
        try:
            return b.decode("utf-16-le", "ignore")
        except Exception:                               # noqa: BLE001
            pass
    for enc in ("utf-8", "cp1258", "cp437"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", "replace")


def run_stream(cmd, j, label, base=0, span=100, pct_re=r"(\d{1,3}(?:[.,]\d)?)\s*%", timeout=7200):
    """Chạy lệnh, đọc % in ra để cập nhật thanh tiến độ. Trả (mã thoát, toàn bộ chữ)."""
    if fake():
        for i in range(0, 101, 10):
            if j.get("stop"):
                raise RuntimeError("Đã dừng")
            j["pct"], j["text"] = int(base + span * i / 100), f"{label}: {i}%"
            time.sleep(0.12)
        return 0, f"(chạy thử) {' '.join(cmd) if isinstance(cmd, list) else cmd}\nWindows Resource Protection did not find any integrity violations."
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=NOWIN)
    raw, t0 = b"", time.time()
    while True:
        ch = p.stdout.read(512)
        if not ch:
            break
        raw += ch
        if j.get("stop"):
            p.kill()
            raise RuntimeError("Đã dừng")
        tail = _decode(raw[-2048:] if len(raw) > 2048 else raw)
        m = re.findall(pct_re, tail)
        if m:
            v = float(m[-1].replace(",", "."))
            j["pct"] = int(base + span * min(100, v) / 100)
            j["text"] = f"{label}: {v:.0f}%"
        if time.time() - t0 > timeout:
            p.kill()
            raise RuntimeError("Quá thời gian chờ")
    return p.wait(), _decode(raw)


# ================================================================ SỬA LỖI WINDOWS 1 CHẠM
def fix_sfc(j, base=0, span=100):
    code, out = run_stream(["sfc", "/scannow"], j, "SFC kiểm tra file hệ thống", base, span)
    low = out.lower()
    if "did not find any integrity" in low or "không tìm thấy" in low:
        msg = "SFC: không có file hệ thống nào bị lỗi."
    elif "successfully repaired" in low or "đã sửa" in low:
        msg = "SFC: đã tìm thấy và SỬA XONG file hệ thống bị lỗi. Nên khởi động lại máy."
    elif "unable to fix" in low or "không thể sửa" in low:
        msg = "SFC: có file lỗi KHÔNG sửa được - chạy DISM RestoreHealth rồi chạy lại SFC."
    else:
        msg = "SFC xong (mã %d)." % code
    return {"text": msg, "out": out[-3000:]}


def fix_dism(j, base=0, span=100):
    code, out = run_stream(["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"], j, "DISM sửa kho Windows", base, span)
    ok = code == 0
    msg = "DISM: đã sửa xong kho thành phần Windows." if ok else f"DISM báo lỗi (mã {code}) - kiểm tra mạng (DISM cần tải file từ Windows Update)."
    return {"text": msg, "out": out[-3000:]}


def fix_wu(j):
    j["text"] = "Đang dừng dịch vụ Windows Update, xóa bộ nhớ đệm..."
    if fake():
        time.sleep(1)
        return {"text": "Đã đặt lại Windows Update (chạy thử)."}
    code, out = _ps(r"""
$sv='wuauserv','bits','cryptsvc','msiserver','usosvc'
foreach($s in $sv){ Stop-Service $s -Force -ErrorAction SilentlyContinue }
Start-Sleep 2
foreach($d in "$env:SystemRoot\SoftwareDistribution","$env:SystemRoot\System32\catroot2"){
  if(Test-Path "$d.bak"){ Remove-Item "$d.bak" -Recurse -Force -ErrorAction SilentlyContinue }
  if(Test-Path $d){ try { Rename-Item $d "$d.bak" -ErrorAction Stop } catch { Remove-Item "$d\*" -Recurse -Force -ErrorAction SilentlyContinue } }
}
& netsh winsock reset | Out-Null
foreach($s in $sv){ Start-Service $s -ErrorAction SilentlyContinue }
'OK'""", timeout=300)
    msg = "Đã đặt lại Windows Update (xóa bộ nhớ đệm tải về, khởi động lại dịch vụ). Vào Windows Update bấm Kiểm tra lại." if "OK" in out \
        else "Đặt lại Windows Update chưa xong: " + out[-300:]
    return {"text": msg}


def fix_store(j):
    j["text"] = "Đang đặt lại Microsoft Store..."
    if fake():
        time.sleep(1)
        return {"text": "Đã đặt lại Microsoft Store (chạy thử)."}
    code, out = _ps(r"""
$p = Get-AppxPackage -AllUsers Microsoft.WindowsStore -ErrorAction SilentlyContinue | Select-Object -First 1
if(-not $p){ 'NOSTORE'; return }
try { Get-AppxPackage Microsoft.WindowsStore | Reset-AppxPackage -ErrorAction Stop } catch {}
try { Add-AppxPackage -DisableDevelopmentMode -Register "$($p.InstallLocation)\AppXManifest.xml" -ErrorAction Stop } catch {}
Start-Process wsreset.exe -ArgumentList '-i' -WindowStyle Hidden -ErrorAction SilentlyContinue
'OK'""", timeout=300)
    if "NOSTORE" in out:
        msg = "Máy này không có Microsoft Store (bản LTSC / đã gỡ)."
    else:
        msg = "Đã đặt lại Microsoft Store. Mở lại Store để kiểm tra."
    return {"text": msg}


def fix_printer(j):
    """Lỗi chia sẻ máy in 0x0000011b / 0x00000709 (sau các bản vá PrintNightmare)."""
    j["text"] = "Đang sửa lỗi chia sẻ máy in..."
    if fake():
        time.sleep(1)
        return {"text": "Đã sửa lỗi chia sẻ máy in 0x0000011b / 0x00000709 (chạy thử)."}
    code, out = _ps(r"""
New-Item 'HKLM:\SYSTEM\CurrentControlSet\Control\Print' -Force | Out-Null
Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Print' RpcAuthnLevelPrivacyEnabled 0 -Type DWord
$k='HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC'
New-Item $k -Force | Out-Null
Set-ItemProperty $k RpcUseNamedPipeProtocol 1 -Type DWord
Set-ItemProperty $k RpcProtocols 7 -Type DWord
Set-ItemProperty $k ForceKerberosForRpc 0 -Type DWord
$k2='HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint'
New-Item $k2 -Force | Out-Null
Set-ItemProperty $k2 RestrictDriverInstallationToAdministrators 0 -Type DWord
Restart-Service Spooler -Force
'OK'""", timeout=120)
    msg = ("Đã sửa lỗi chia sẻ máy in 0x0000011b / 0x00000709 và khởi động lại Spooler. "
           "Làm trên CẢ máy chủ (máy cắm máy in) và máy con, rồi thêm lại máy in.") if "OK" in out else "Chưa sửa được: " + out[-300:]
    return {"text": msg}


def fix_all(j):
    """DISM trước (sửa kho) rồi SFC (sửa file hệ thống) - đúng thứ tự Microsoft khuyên."""
    a = fix_dism(j, 0, 50)
    b = fix_sfc(j, 50, 50)
    return {"text": a["text"] + "\n" + b["text"], "out": (a.get("out", "") + "\n\n" + b.get("out", ""))[-4000:]}


# ================================================================ DỌN WIN 11 CHO GỌN
TIDY_ON = r"""
function S($k,$n,$v){ if(-not (Test-Path $k)){ New-Item $k -Force | Out-Null }; Set-ItemProperty $k $n $v -Type DWord -Force }
S 'HKCU:\Software\Policies\Microsoft\Windows\WindowsCopilot' TurnOffWindowsCopilot 1
S 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot' TurnOffWindowsCopilot 1
S 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' ShowCopilotButton 0
S 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' DisableAIDataAnalysis 1
S 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' AllowRecallEnablement 0
$c='HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager'
foreach($n in 'SubscribedContent-338388Enabled','SubscribedContent-338389Enabled','SubscribedContent-353694Enabled','SubscribedContent-353696Enabled','SubscribedContent-310093Enabled','SystemPaneSuggestionsEnabled','SilentInstalledAppsEnabled','SoftLandingEnabled','PreInstalledAppsEnabled','OemPreInstalledAppsEnabled'){ S $c $n 0 }
S 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' Start_IrisRecommendations 0
S 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' ShowSyncProviderNotifications 0
S 'HKLM:\SOFTWARE\Policies\Microsoft\Dsh' AllowNewsAndInterests 0
S 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' AllowTelemetry 0
S 'HKCU:\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo' Enabled 0
S 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Privacy' TailoredExperiencesWithDiagnosticDataEnabled 0
S 'HKCU:\Software\Policies\Microsoft\Windows\Explorer' DisableSearchBoxSuggestions 1
Set-Service DiagTrack -StartupType Disabled -ErrorAction SilentlyContinue; Stop-Service DiagTrack -Force -ErrorAction SilentlyContinue
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
'OK'"""
TIDY_OFF = r"""
function R($k,$n){ Remove-ItemProperty $k $n -Force -ErrorAction SilentlyContinue }
function S($k,$n,$v){ if(-not (Test-Path $k)){ New-Item $k -Force | Out-Null }; Set-ItemProperty $k $n $v -Type DWord -Force }
R 'HKCU:\Software\Policies\Microsoft\Windows\WindowsCopilot' TurnOffWindowsCopilot
R 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot' TurnOffWindowsCopilot
R 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' ShowCopilotButton
R 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' DisableAIDataAnalysis
R 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' AllowRecallEnablement
$c='HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager'
foreach($n in 'SubscribedContent-338388Enabled','SubscribedContent-338389Enabled','SubscribedContent-353694Enabled','SubscribedContent-353696Enabled','SubscribedContent-310093Enabled','SystemPaneSuggestionsEnabled','SilentInstalledAppsEnabled','SoftLandingEnabled','PreInstalledAppsEnabled','OemPreInstalledAppsEnabled'){ S $c $n 1 }
R 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' Start_IrisRecommendations
R 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' ShowSyncProviderNotifications
R 'HKLM:\SOFTWARE\Policies\Microsoft\Dsh' AllowNewsAndInterests
R 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' AllowTelemetry
S 'HKCU:\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo' Enabled 1
R 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Privacy' TailoredExperiencesWithDiagnosticDataEnabled
R 'HKCU:\Software\Policies\Microsoft\Windows\Explorer' DisableSearchBoxSuggestions
Set-Service DiagTrack -StartupType Automatic -ErrorAction SilentlyContinue; Start-Service DiagTrack -ErrorAction SilentlyContinue
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
'OK'"""


def win11_tidy(j, on=True):
    j["text"] = "Đang dọn Win 11..." if on else "Đang bật lại như cũ..."
    if fake():
        time.sleep(1)
    else:
        code, out = _ps(TIDY_ON if on else TIDY_OFF, timeout=120)
        if "OK" not in out:
            raise RuntimeError(out[-300:] or f"mã {code}")
        for _ in range(6):                        # Windows thường tự mở lại thanh tác vụ; chờ tới 6 giây rồi mới tự mở
            time.sleep(1)
            if mgr.proc_running(["explorer.exe"]):
                break
        else:
            subprocess.Popen(["explorer.exe"])
    msg = ("Đã tắt Copilot, Recall, quảng cáo / gợi ý trong Start, Widgets, gửi dữ liệu chẩn đoán, quảng cáo cá nhân hóa, "
           "gợi ý Bing khi tìm kiếm. Một số mục cần đăng xuất / khởi động lại mới thấy.") if on else \
        "Đã bật lại các mục như mặc định của Windows (khởi động lại máy để áp dụng đủ)."
    return {"text": msg}


# ================================================================ FONT TIẾNG VIỆT
FONT_EXT = (".ttf", ".otf", ".ttc", ".fon")


def _install_font_file(f, fonts_dir, reg):
    import winreg
    dst = fonts_dir / f.name
    if dst.exists():
        return False
    shutil.copy2(f, dst)
    kind = "OpenType" if f.suffix.lower() == ".otf" else "TrueType"
    winreg.SetValueEx(reg, f"{f.stem} ({kind})", 0, winreg.REG_SZ, f.name)
    try:
        ctypes.windll.gdi32.AddFontResourceW(str(dst))
    except Exception:                                   # noqa: BLE001
        pass
    return True


def font_install(j, src):
    """Cài font từ link tải (.zip) / file .zip / thư mục / file font. Bỏ qua font máy đã có."""
    src = (src or "").strip().strip('"')
    if not src:
        raise RuntimeError("Chưa có nguồn font: chọn file .zip / thư mục font, hoặc Admin gắn link bộ font.")
    if fake():
        for i in range(0, 101, 10):
            j["pct"], j["text"] = i, f"Đang cài font {i}%"
            time.sleep(0.1)
        return {"text": "Đã cài 86 font mới, bỏ qua 12 font máy đã có (chạy thử)."}
    work = data_dir("Tools", "Font")
    if re.match(r"^https?://", src, re.I):
        import requests
        j["text"] = "Đang tải bộ font..."
        zp = work / "font_pack.zip"
        with requests.get(src, stream=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as r:
            r.raise_for_status()
            if "text/html" in r.headers.get("Content-Type", ""):
                raise RuntimeError("Link không phải file tải trực tiếp (là trang web). Dùng link tải thẳng file .zip.")
            tot, done = int(r.headers.get("Content-Length") or 0), 0
            with open(zp, "wb") as fh:
                for ch in r.iter_content(1 << 20):
                    fh.write(ch)
                    done += len(ch)
                    if tot:
                        j["pct"] = int(done * 40 / tot)
        src = str(zp)
    p = absp(src)
    files = []
    if p.is_dir():
        files = [x for x in p.rglob("*") if x.suffix.lower() in FONT_EXT]
    elif p.suffix.lower() == ".zip":
        out = work / "giai_nen"
        shutil.rmtree(out, ignore_errors=True)
        with zipfile.ZipFile(p) as z:
            z.extractall(out)
        files = [x for x in out.rglob("*") if x.suffix.lower() in FONT_EXT]
    elif p.suffix.lower() in FONT_EXT:
        files = [p]
    if not files:
        raise RuntimeError("Không thấy file font (.ttf / .otf) nào trong nguồn đã chọn.")
    import winreg
    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    new = old = 0
    errs = []
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", 0, winreg.KEY_SET_VALUE) as reg:
        for i, f in enumerate(files):
            j["pct"] = 40 + int(i * 60 / len(files))
            j["text"] = f"Đang cài font {i + 1}/{len(files)}: {f.name}"
            try:
                if _install_font_file(f, fonts_dir, reg):
                    new += 1
                else:
                    old += 1
            except Exception as e:                      # noqa: BLE001
                errs.append(f"{f.name}: {e}")
    try:
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)   # WM_FONTCHANGE
    except Exception:                                   # noqa: BLE001
        pass
    msg = f"Đã cài {new} font mới, bỏ qua {old} font máy đã có" + (f", {len(errs)} font lỗi" if errs else "") + "."
    return {"text": msg, "errs": errs[:20]}


# ================================================================ CHUYỂN PHẦN MỀM SANG WIN MỚI
def apps_export(j, dest):
    name = f"PhanMem_{os.environ.get('COMPUTERNAME', 'May')}_{time.strftime('%Y%m%d_%H%M')}.json"
    j["pct"], j["text"] = -1, "Đang lấy danh sách phần mềm đã cài (winget export)..."
    if fake():
        time.sleep(1)
        pk = ["Google.Chrome", "7zip.7zip", "VNGCorp.Zalo", "VideoLAN.VLC"]
        return {"path": str(Path(dest) / name), "dest": str(dest), "count": len(pk), "ids": pk,
                "text": f"Đã lưu danh sách {len(pk)} phần mềm vào {name} (chạy thử)."}
    out = absp(dest)
    out.mkdir(parents=True, exist_ok=True)
    f = out / name
    code, o = H["run"](["winget", "export", "-o", str(f), "--source", "winget", "--accept-source-agreements"], timeout=300)
    if not f.exists():
        raise RuntimeError("winget export lỗi: " + " ".join(o.split())[-200:])
    pk = [p["PackageIdentifier"] for s in json.loads(f.read_text(encoding="utf-8-sig")).get("Sources", []) for p in s.get("Packages", [])]
    return {"path": str(f), "dest": str(out), "count": len(pk), "ids": pk,
            "text": f"Đã lưu danh sách {len(pk)} phần mềm vào {name}. Cài Win xong mở tool, bấm 'Cài lại từ danh sách'."}


def apps_list_file(path):
    if fake():
        return ["Google.Chrome", "7zip.7zip", "VNGCorp.Zalo", "VideoLAN.VLC"]
    data = json.loads(absp(path).read_text(encoding="utf-8-sig"))
    return [p["PackageIdentifier"] for s in data.get("Sources", []) for p in s.get("Packages", [])]


def apps_import(j, path, ids=None):
    """Cài lại lần lượt từng phần mềm trong danh sách (winget install, im lặng) - có % theo số phần mềm."""
    allids = apps_list_file(path)
    ids = [x for x in (ids or allids)]
    done, skip, errs, n = [], [], [], len(ids)
    for i, pid in enumerate(ids):
        label = f"[{i + 1}/{n}] {pid}"
        if fake():
            j["pct"], j["text"] = int((i + 1) * 100 / n), label
            time.sleep(0.25)
            done.append(pid)
            continue
        cmd = ["winget", "install", "--id", pid, "-e", "--source", "winget", "--silent",
               "--accept-package-agreements", "--accept-source-agreements", "--disable-interactivity"]
        code, out = run_stream(cmd, j, label, i * 100 / n, 100 / n)
        code &= 0xFFFFFFFF
        if code in mgr.WG_OK or code == 0x8A150061:
            (skip if code in (0x8A15002B, 0x8A150061) else done).append(pid)
        else:
            errs.append(f"{pid}: mã 0x{code:08X}")
    return {"done": done, "skip": skip, "errs": errs,
            "text": f"Đã cài {len(done)} phần mềm, {len(skip)} phần mềm máy đã có sẵn" + (f", {len(errs)} lỗi" if errs else "") + "."}


# ================================================================ DRIVER
CM_ERR = {1: "Cấu hình sai", 3: "Driver hỏng hoặc thiếu bộ nhớ", 10: "Thiết bị không khởi động được", 12: "Xung đột tài nguyên",
          14: "Cần khởi động lại máy", 18: "Cần cài lại driver", 19: "Lỗi registry", 21: "Đang gỡ thiết bị", 22: "Thiết bị đang bị tắt",
          24: "Không có thiết bị / thiếu driver", 28: "CHƯA CÓ DRIVER", 31: "Driver không chạy được", 32: "Dịch vụ driver bị tắt",
          37: "Driver lỗi khởi tạo", 39: "Driver hỏng hoặc thiếu", 40: "Lỗi registry dịch vụ", 41: "Driver tải được nhưng không thấy thiết bị",
          43: "Thiết bị báo lỗi (code 43)", 45: "Thiết bị không cắm", 47: "Đã tháo an toàn", 48: "Driver bị chặn", 52: "Driver chưa được ký số"}
FAKE_DRV = [
    {"name": "PCI Simple Communications Controller", "cls": "Other devices", "code": 28, "id": "PCI\\VEN_8086&DEV_A3BA"},
    {"name": "Unknown device", "cls": "Other devices", "code": 28, "id": "ACPI\\INT33A1\\0"},
    {"name": "Realtek Audio", "cls": "Sound", "code": 10, "id": "HDAUDIO\\FUNC_01&VEN_10EC"},
]


def drv_problems():
    """Thiết bị đang lỗi / thiếu driver (dấu chấm than vàng trong Device Manager)."""
    if fake():
        rows = FAKE_DRV
    else:
        code, out = _ps("Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 -and $_.ConfigManagerErrorCode -ne 45 } | "
                        "Select-Object @{n='name';e={if($_.Name){$_.Name}else{$_.Description}}}, @{n='cls';e={$_.PNPClass}}, "
                        "@{n='code';e={[int]$_.ConfigManagerErrorCode}}, @{n='id';e={$_.PNPDeviceID}} | ConvertTo-Json -Compress", timeout=90)
        try:
            rows = json.loads(out) if out.strip() else []
        except ValueError:
            rows = []
        rows = rows if isinstance(rows, list) else [rows]
    for r in rows:
        r["err"] = CM_ERR.get(int(r.get("code") or 0), f"Mã lỗi {r.get('code')}")
        r["name"] = r.get("name") or "Thiết bị không tên"
    return rows


DRV_WU = r"""
$s = New-Object -ComObject Microsoft.Update.Session
$s.ClientApplicationID = 'Win AIO'
$se = $s.CreateUpdateSearcher()
$se.ServiceID = '7971f918-a847-4430-9279-4a52d1efe18d'; $se.SearchScope = 1; $se.ServerSelection = 3
$r = $se.Search("IsInstalled=0 and Type='Driver' and IsHidden=0")
$list = @(); foreach($u in $r.Updates){ $list += [pscustomobject]@{ id=$u.Identity.UpdateID; title=$u.Title; size=[int64]$u.MaxDownloadSize; date=$u.LastDeploymentChangeTime.ToString('dd/MM/yyyy'); model=$u.DriverModel; cls=$u.DriverClass } }
"""


def drv_wu_scan(j):
    j["pct"], j["text"] = -1, "Đang hỏi Windows Update driver còn thiếu / bản mới (1 - 3 phút)..."
    if fake():
        time.sleep(1.5)
        return [{"id": "a1", "title": "Intel - System - 10.1.19444.8378", "size": 1200000, "date": "12/03/2024", "cls": "System"},
                {"id": "a2", "title": "Realtek Semiconductor Corp. - MEDIA - 6.0.9600.1", "size": 48000000, "date": "05/08/2025", "cls": "MEDIA"}]
    code, out = _ps(DRV_WU + "$list | ConvertTo-Json -Compress", timeout=900)
    try:
        rows = json.loads(out) if out.strip() else []
    except ValueError:
        raise RuntimeError("Windows Update không trả lời: " + out[-300:])
    return rows if isinstance(rows, list) else [rows]


def drv_wu_install(j, ids):
    j["pct"], j["text"] = -1, f"Đang tải và cài {len(ids)} driver từ Windows Update (có thể mất vài phút)..."
    if fake():
        time.sleep(2)
        return {"text": f"Đã cài {len(ids)} driver. Nên khởi động lại máy.", "reboot": True}
    want = ",".join("'%s'" % i.replace("'", "") for i in ids)
    code, out = _ps(DRV_WU + r"""
$want = @(""" + want + r""")
$c = New-Object -ComObject Microsoft.Update.UpdateColl
foreach($u in $r.Updates){ if($want -contains $u.Identity.UpdateID){ if(-not $u.EulaAccepted){ $u.AcceptEula() }; [void]$c.Add($u) } }
if($c.Count -eq 0){ 'NONE'; return }
$d = $s.CreateUpdateDownloader(); $d.Updates = $c; [void]$d.Download()
$i = $s.CreateUpdateInstaller(); $i.Updates = $c; $res = $i.Install()
"RESULT=$($res.ResultCode);REBOOT=$($res.RebootRequired)"
""", timeout=3600)
    m = re.search(r"RESULT=(\d+);REBOOT=(\w+)", out)
    if not m:
        raise RuntimeError("Cài driver lỗi: " + out[-300:])
    ok = m.group(1) in ("2", "3")          # 2 = thành công, 3 = thành công một phần
    reboot = m.group(2).lower() == "true"
    msg = ("Đã cài driver." if m.group(1) == "2" else "Đã cài một phần driver.") if ok else f"Cài driver không thành công (mã {m.group(1)})."
    if reboot:
        msg += " Cần khởi động lại máy."
    return {"text": msg, "reboot": reboot}


# ================================================================ THIẾT LẬP MÁY MỚI
def setup_info():
    if fake():
        return {"pc": "DESKTOP-ABC123", "users": [{"name": "Admin", "enabled": True, "pw": True, "admin": True},
                                                {"name": "KeToan", "enabled": True, "pw": False, "admin": False}],
                "unikey": r"C:\Program Files\UniKey\UniKeyNT.exe", "unikey_auto": False, "chrome": True}
    code, out = _ps(r"""
$adm = @(); try { $adm = (Get-LocalGroupMember -SID 'S-1-5-32-544' -ErrorAction Stop | ForEach-Object { ($_.Name -split '\\')[-1] }) } catch {}
$u = Get-LocalUser | Where-Object { $_.Name -notin 'DefaultAccount','WDAGUtilityAccount','Guest' } | ForEach-Object {
  [pscustomobject]@{ name=$_.Name; enabled=[bool]$_.Enabled; pw=[bool]$_.PasswordRequired; admin=($adm -contains $_.Name) } }
[pscustomobject]@{ pc=$env:COMPUTERNAME; users=@($u) } | ConvertTo-Json -Compress -Depth 4""", timeout=60)
    try:
        d = json.loads(out)
    except ValueError:
        d = {"pc": os.environ.get("COMPUTERNAME", ""), "users": []}
    d["users"] = d.get("users") or []
    d["unikey"] = str(_unikey_path() or "")
    d["unikey_auto"] = _run_get("UniKey") is not None
    d["chrome"] = bool(_chrome_path())
    return d


def _unikey_path():
    cands = []
    for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", ""), os.environ.get("LOCALAPPDATA", ""),
                 os.environ.get("SystemDrive", "C:") + "\\"):
        if base:
            cands += [Path(base) / "UniKey" / "UniKeyNT.exe", Path(base) / "unikey" / "UniKeyNT.exe"]
    wg = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if wg.exists():
        cands += list(wg.glob("UniKey.UniKey*/**/UniKeyNT.exe"))
    for c in cands:
        if c.exists():
            return c
    return None


def _chrome_path():
    for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", ""), os.environ.get("LOCALAPPDATA", "")):
        p = Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe"
        if base and p.exists():
            return p
    return None


def _run_get(name):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return None


def _valid_name(n, maxlen):
    n = (n or "").strip()
    if not n or len(n) > maxlen or re.search(r'[\\/:*?"<>|\[\];=+,@ ]', n):
        return None
    return n


def setup_rename(name):
    n = _valid_name(name, 15)
    if not n or n.isdigit():
        return "Tên máy 1-15 ký tự, không dấu cách, không ký tự đặc biệt, không toàn số. VD: KETOAN-01"
    if fake():
        return ""
    code, out = _ps(f"Rename-Computer -NewName '{n}' -Force -ErrorAction Stop; 'OK'", timeout=60)
    if "OK" not in out:
        return "Không đổi được tên máy: " + out[-200:]
    H["history"]("Đổi tên máy", n, "Xong", "Khởi động lại để áp dụng")
    return ""


def setup_user(name, pw, admin):
    n = _valid_name(name, 20)
    if not n:
        return "Tên tài khoản 1-20 ký tự, không dấu cách, không ký tự đặc biệt."
    if fake():
        return ""
    pw = pw or ""
    esc = pw.replace("'", "''")
    script = (f"$p = if('{esc}'){{ ConvertTo-SecureString '{esc}' -AsPlainText -Force }} else {{ $null }}; "
              f"if($p){{ New-LocalUser -Name '{n}' -Password $p -PasswordNeverExpires -ErrorAction Stop | Out-Null }} "
              f"else {{ New-LocalUser -Name '{n}' -NoPassword -ErrorAction Stop | Out-Null; Set-LocalUser -Name '{n}' -PasswordNeverExpires $true }}; "
              f"Add-LocalGroupMember -SID 'S-1-5-32-545' -Member '{n}' -ErrorAction SilentlyContinue; "
              + (f"Add-LocalGroupMember -SID 'S-1-5-32-544' -Member '{n}' -ErrorAction Stop; " if admin else "") + "'OK'")
    code, out = _ps(script, timeout=60)
    if "OK" not in out:
        return "Không tạo được tài khoản: " + out[-200:]
    H["history"]("Tạo tài khoản", n, "Xong", "Admin" if admin else "Thường")
    return ""


def setup_nopass(name):
    """Bỏ mật khẩu tài khoản cục bộ (máy chỉ 1 tài khoản sẽ tự vào thẳng Windows)."""
    n = _valid_name(name, 20)
    if not n:
        return "Tên tài khoản không hợp lệ."
    if fake():
        return ""
    code, out = _ps(f"$u = Get-LocalUser -Name '{n}' -ErrorAction Stop; "
                    "if($u.PrincipalSource -ne 'Local'){ 'MSA'; return }; "
                    f"Set-LocalUser -Name '{n}' -Password (New-Object System.Security.SecureString) -ErrorAction Stop; "
                    f"Set-LocalUser -Name '{n}' -PasswordNeverExpires $true; "
                    "New-Item 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\PasswordLess\\Device' -Force | Out-Null; "
                    "Set-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\PasswordLess\\Device' DevicePasswordLessBuildVersion 0 -Type DWord; 'OK'",
                    timeout=60)
    if "MSA" in out:
        return "Tài khoản này đăng nhập bằng tài khoản Microsoft - không bỏ mật khẩu được ở đây (dùng tài khoản cục bộ)."
    if "OK" not in out:
        return "Không bỏ được mật khẩu: " + out[-200:]
    H["history"]("Bỏ mật khẩu đăng nhập", n, "Xong", "")
    return ""


def setup_browser():
    """Windows 10/11 không cho phần mềm tự đặt trình duyệt mặc định - mở đúng trang để bấm 1 lần."""
    if fake():
        return "Đã mở trang chọn trình duyệt mặc định (chạy thử)."
    c = _chrome_path()
    if c:
        subprocess.Popen([str(c), "--make-default-browser"], creationflags=NOWIN)
        return "Chrome đã yêu cầu làm trình duyệt mặc định - trong cửa sổ Cài đặt vừa mở, bấm 'Đặt mặc định' cho Google Chrome."
    os.startfile("ms-settings:defaultapps")
    return "Máy chưa có Chrome (cài ở tab Cài phần mềm). Đã mở trang Ứng dụng mặc định."


def setup_unikey(on):
    import winreg
    p = _unikey_path()
    if on and not p:
        return "Không tìm thấy UniKey trên máy - cài UniKey ở tab Cài phần mềm trước."
    if fake():
        return ""
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, "UniKey", 0, winreg.REG_SZ, f'"{p}"')
        else:
            try:
                winreg.DeleteValue(k, "UniKey")
            except OSError:
                pass
    if on and not mgr.proc_running(["UniKeyNT.exe"]):
        subprocess.Popen([str(p)], creationflags=NOWIN)
    return ""


# ================================================================ NHIỆT ĐỘ CPU (PDH, không cần driver)
class _Pdh:
    """Đọc bộ đếm hiệu năng Windows bằng pdh.dll (nhanh, không mở PowerShell mỗi lần)."""

    def __init__(self, paths):
        self.ok = False
        try:
            self.pdh = ctypes.windll.pdh
            self.q = ctypes.c_void_p()
            if self.pdh.PdhOpenQueryW(None, 0, ctypes.byref(self.q)):
                return
            self.c = {}
            for k, p in paths.items():
                h = ctypes.c_void_p()
                if not self.pdh.PdhAddEnglishCounterW(self.q, p, 0, ctypes.byref(h)):
                    self.c[k] = h
            self.pdh.PdhCollectQueryData(self.q)
            self.ok = bool(self.c)
        except Exception:                               # noqa: BLE001
            self.ok = False

    def read(self):
        """Trả {tên: [giá trị của từng phiên bản]}."""
        out = {}
        if not self.ok:
            return out

        class FMT(ctypes.Structure):
            _fields_ = [("status", ctypes.c_ulong), ("pad", ctypes.c_ulong), ("val", ctypes.c_double)]

        class ITEM(ctypes.Structure):
            _fields_ = [("name", ctypes.c_wchar_p), ("fmt", FMT)]
        self.pdh.PdhCollectQueryData(self.q)
        for k, h in self.c.items():
            size, cnt = ctypes.c_ulong(0), ctypes.c_ulong(0)
            self.pdh.PdhGetFormattedCounterArrayW(h, 0x200, ctypes.byref(size), ctypes.byref(cnt), None)
            if not size.value:
                continue
            buf = (ctypes.c_byte * size.value)()
            if self.pdh.PdhGetFormattedCounterArrayW(h, 0x200, ctypes.byref(size), ctypes.byref(cnt), buf):
                continue
            arr = ctypes.cast(buf, ctypes.POINTER(ITEM))
            out[k] = [arr[i].fmt.val for i in range(cnt.value) if arr[i].fmt.status in (0, 1)]
        return out


_PDH = {"q": None, "t": 0, "v": None, "lock": threading.Lock(), "acpi": None}


def cpu_temp():
    """Nhiệt độ cao nhất các vùng nhiệt (°C) - đọc từ cảm biến ACPI của Windows. Máy không có cảm biến -> None."""
    if fake():
        import random
        return round(random.uniform(48, 63), 1)
    with _PDH["lock"]:
        if time.time() - _PDH["t"] < 2.5:
            return _PDH["v"]
        _PDH["t"] = time.time()
        if _PDH["q"] is None:
            _PDH["q"] = _Pdh({"t": r"\Thermal Zone Information(*)\High Precision Temperature",
                              "t2": r"\Thermal Zone Information(*)\Temperature",
                              "perf": r"\Processor Information(_Total)\% Processor Performance",
                              "freq": r"\Processor Information(_Total)\Processor Frequency"})
        d = _PDH["q"].read()
        vals = [v / 10 - 273.15 for v in d.get("t", []) if v > 2000] or [v - 273.15 for v in d.get("t2", []) if v > 200]
        if not vals and _PDH["acpi"] is not False:          # máy không có bộ đếm -> thử ACPI (WMI) 1 lần mỗi 15 giây
            if time.time() - (_PDH.get("acpi_t") or 0) > 15:
                _PDH["acpi_t"] = time.time()
                code, out = _ps("(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop).CurrentTemperature", timeout=20)
                nums = [int(x) for x in re.findall(r"\d+", out or "")]
                if nums:
                    _PDH["acpi"] = True
                    _PDH["acpi_v"] = [n / 10 - 273.15 for n in nums if n > 2000]
                else:
                    _PDH["acpi"] = False
            vals = _PDH.get("acpi_v") or []
        vals = [v for v in vals if 5 < v < 125]
        _PDH["v"] = round(max(vals), 1) if vals else None
        _PDH["perf"] = (d.get("perf") or [None])[0]
        _PDH["freq"] = (d.get("freq") or [None])[0]
        return _PDH["v"]


def cpu_clock():
    """(MHz hiện tại, % so với xung gốc) - để biết CPU có bị hạ xung vì nóng không."""
    if fake():
        import random
        p = random.uniform(70, 115)
        return int(2600 * p / 100), round(p)
    cpu_temp()
    perf, freq = _PDH.get("perf"), _PDH.get("freq")
    if perf and freq:
        return int(freq * perf / 100), round(perf)
    return None, None


# ================================================================ TEST HIỆU NĂNG
def bench_disk(j, drive="C"):
    """Đo tốc độ ổ cứng bằng WinSAT có sẵn trong Windows: đọc / ghi tuần tự, đọc ngẫu nhiên 4K."""
    drive = (drive or "C").strip(":\\ ").upper()[:1] or "C"
    tests = [("seq_read", "Đọc tuần tự", ["-seq", "-read"]), ("seq_write", "Ghi tuần tự", ["-seq", "-write"]),
             ("rnd_read", "Đọc ngẫu nhiên 4K", ["-ran", "-read", "-ransize", "4096"])]
    res = {}
    for i, (k, name, args) in enumerate(tests):
        if j.get("stop"):
            raise RuntimeError("Đã dừng")
        j["pct"], j["text"] = int(i * 100 / len(tests)), f"Ổ {drive}: đang đo {name}..."
        if fake():
            time.sleep(0.8)
            res[k] = {"name": name, "mbs": {"seq_read": 3120.5, "seq_write": 2480.2, "rnd_read": 412.7}[k]}
            continue
        code, out = H["run"](["winsat", "disk", "-drive", drive] + args, timeout=300)
        m = re.search(r"Disk\s+.*?([\d.,]+)\s*MB/s", out or "")
        res[k] = {"name": name, "mbs": float(m.group(1).replace(",", "")) if m else None,
                  "err": None if m else " ".join((out or "").split())[-160:]}
    j["pct"] = 100
    sr = (res.get("seq_read") or {}).get("mbs") or 0
    kind = "SSD NVMe" if sr > 1500 else "SSD SATA" if sr > 350 else "HDD / ổ chậm" if sr else "?"
    return {"drive": drive, "res": res, "kind": kind}


def _burn(stop):
    """Vòng tính SHA-256 trên khối 4 MB: hashlib nhả GIL nên mỗi luồng chiếm trọn 1 nhân CPU, không cần mở tiến trình mới."""
    import hashlib
    buf = os.urandom(4 << 20)
    while not stop.is_set():
        hashlib.sha256(buf).digest()


def bench_cpu(j, secs=60):
    """Chạy tải 100% toàn bộ nhân CPU trong secs giây, ghi lại % CPU, nhiệt độ, xung nhịp mỗi giây."""
    secs = max(15, min(600, int(secs or 60)))
    n = os.cpu_count() or 4
    series, stop = [], threading.Event()
    try:
        if not fake():
            for _ in range(n):
                threading.Thread(target=_burn, args=(stop,), daemon=True).start()
        t0 = time.time()
        while time.time() - t0 < secs:
            if j.get("stop"):
                break
            time.sleep(1)
            t = cpu_temp()
            mhz, pct = cpu_clock()
            load = H["live"]()["cpu"] if H.get("live") else None
            series.append({"s": round(time.time() - t0), "cpu": load, "temp": t, "mhz": mhz, "perf": pct})
            el = time.time() - t0
            j["pct"] = int(el * 100 / secs)
            j["text"] = (f"Đang chạy tải {n} luồng: {int(el)}/{secs} giây · CPU {load if load is not None else '?'}%"
                         + (f" · {t}°C" if t else "") + (f" · {mhz} MHz" if mhz else ""))
    finally:
        stop.set()
    temps = [x["temp"] for x in series if x["temp"]]
    perfs = [x["perf"] for x in series if x["perf"]]
    out = {"threads": n, "secs": secs, "series": series,
           "tmax": max(temps) if temps else None, "tavg": round(sum(temps) / len(temps), 1) if temps else None,
           "perf_min": min(perfs) if perfs else None, "perf_avg": round(sum(perfs) / len(perfs)) if perfs else None}
    tail = perfs[len(perfs) // 2:] if perfs else []
    out["throttle"] = bool(tail and min(tail) < 60)
    return out


# ================================================================ USB BOOT (VENTOY)
FAKE_USB = [{"num": 2, "model": "SanDisk Ultra USB 3.0", "size": 32_000_000_000, "letters": "E", "labels": "USB", "ventoy": False},
            {"num": 3, "model": "Kingston DataTraveler", "size": 64_000_000_000, "letters": "F,G", "labels": "Ventoy,VTOYEFI", "ventoy": True}]


def usb_disks():
    """Ổ USB đang cắm (chỉ ổ BusType USB, không bao giờ lấy ổ Windows)."""
    if fake():
        return FAKE_USB
    code, out = _ps(r"""
$sys = (Get-Partition -DriveLetter ($env:SystemDrive.TrimEnd(':')) -ErrorAction SilentlyContinue).DiskNumber
Get-Disk | Where-Object { $_.BusType -eq 'USB' -and $_.Number -ne $sys } | ForEach-Object {
  $parts = Get-Partition -DiskNumber $_.Number -ErrorAction SilentlyContinue
  $vols = $parts | ForEach-Object { Get-Volume -Partition $_ -ErrorAction SilentlyContinue }
  [pscustomobject]@{ num=$_.Number; model=$_.FriendlyName; size=[int64]$_.Size
    letters=(($parts | Where-Object DriveLetter | ForEach-Object { $_.DriveLetter }) -join ',')
    labels=(($vols | Where-Object FileSystemLabel | ForEach-Object { $_.FileSystemLabel }) -join ',') } } | ConvertTo-Json -Compress""", timeout=60)
    try:
        rows = json.loads(out) if out.strip() else []
    except ValueError:
        rows = []
    rows = rows if isinstance(rows, list) else [rows]
    for r in rows:
        r["ventoy"] = "Ventoy" in (r.get("labels") or "")
    return rows


def _ventoy_dir(j):
    d = data_dir("Tools", "Ventoy")
    exe = next(d.rglob("Ventoy2Disk.exe"), None)
    if exe and time.time() - exe.stat().st_mtime < 30 * 86400:
        return exe
    import requests
    j["text"] = "Đang tải Ventoy bản mới nhất..."
    url, tag = H["gh"](r"github:ventoy/Ventoy|windows\.zip$")
    zp = d / "ventoy.zip"
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(zp, "wb") as fh:
            for ch in r.iter_content(1 << 20):
                fh.write(ch)
    shutil.rmtree(d / "bin", ignore_errors=True)
    with zipfile.ZipFile(zp) as z:
        z.extractall(d / "bin")
    exe = next((d / "bin").rglob("Ventoy2Disk.exe"), None)
    if not exe:
        raise RuntimeError("Gói Ventoy tải về không có Ventoy2Disk.exe")
    return exe


def ventoy_install(j, num, gpt=False):
    """Cài Ventoy vào USB số num (XÓA SẠCH USB). Kiểm tra lại đúng là ổ USB ngay trước khi chạy."""
    num = int(num)
    disk = next((d for d in usb_disks() if int(d["num"]) == num), None)
    if not disk:
        raise RuntimeError("Không thấy USB số %d (đã rút ra?). Bấm Làm mới." % num)
    if fake():
        for i in range(0, 101, 10):
            j["pct"], j["text"] = i, f"Đang cài Ventoy vào {disk['model']}: {i}%"
            time.sleep(0.15)
        return {"text": f"Đã cài Ventoy vào {disk['model']}. Chép file ISO vào ổ 'Ventoy' là boot được.", "letter": "E"}
    exe = _ventoy_dir(j)
    wd = exe.parent
    for f in ("cli_percent.txt", "cli_done.txt", "cli_log.txt"):
        (wd / f).unlink(missing_ok=True)
    cmd = [str(exe), "VTOYCLI", "/I", f"/PhyDrive:{num}", "/NOUSBCheck"] + (["/GPT"] if gpt else [])
    p = subprocess.Popen(cmd, cwd=str(wd), creationflags=NOWIN)
    while p.poll() is None:
        time.sleep(0.5)
        try:
            v = int((wd / "cli_percent.txt").read_text().strip() or 0)
            j["pct"], j["text"] = v, f"Đang cài Ventoy vào {disk['model']}: {v}%"
        except (OSError, ValueError):
            j["text"] = f"Đang cài Ventoy vào {disk['model']}..."
    try:
        done = (wd / "cli_done.txt").read_text().strip()
    except OSError:
        done = str(p.returncode)
    if done != "0":
        log = ""
        try:
            log = (wd / "cli_log.txt").read_text(errors="ignore")[-400:]
        except OSError:
            pass
        raise RuntimeError("Cài Ventoy không thành công. " + log)
    time.sleep(3)
    d2 = next((d for d in usb_disks() if int(d["num"]) == num), {})
    letter = (d2.get("letters") or "").split(",")[0]
    return {"text": f"Đã cài Ventoy vào {disk['model']}" + (f" (ổ {letter}:)" if letter else "") + ". Chép file ISO vào là boot được.",
            "letter": letter}


def ventoy_copy(j, iso, letter):
    """Chép file ISO vào ổ USB Ventoy (có %)."""
    src = absp(iso)
    letter = (letter or "").strip(":\\ ").upper()[:1]
    if not letter:
        raise RuntimeError("Chưa chọn ổ USB Ventoy.")
    dst = Path(f"{letter}:\\") / src.name
    if fake():
        for i in range(0, 101, 5):
            j["pct"], j["text"] = i, f"Đang chép {src.name} vào {letter}: {i}%"
            time.sleep(0.05)
        return {"text": f"Đã chép {src.name} vào USB {letter}:. Cắm USB vào máy cần cài, chọn boot từ USB."}
    if not src.is_file():
        raise RuntimeError(f"Không thấy file: {src}")
    size = src.stat().st_size
    free = shutil.disk_usage(f"{letter}:\\").free
    if size > free:
        raise RuntimeError(f"USB không đủ chỗ: cần {human(size)}, còn {human(free)}.")
    done, part = 0, dst.with_name(dst.name + ".tmp")
    with open(src, "rb") as fi, open(part, "wb") as fo:
        while True:
            if j.get("stop"):
                fo.close()
                part.unlink(missing_ok=True)
                raise RuntimeError("Đã dừng")
            b = fi.read(8 << 20)
            if not b:
                break
            fo.write(b)
            done += len(b)
            j["pct"], j["text"] = int(done * 100 / max(1, size)), f"Đang chép {src.name}: {human(done)} / {human(size)}"
        fo.flush()
        os.fsync(fo.fileno())
    if dst.exists():
        dst.unlink()
    part.rename(dst)
    return {"text": f"Đã chép {src.name} vào USB {letter}:. Cắm USB vào máy cần cài, chọn boot từ USB."}


def iso_files():
    """File .iso trong Data\\ISO (đã tải bằng Kho ISO)."""
    d = Path(H["data"]) / "ISO" if H.get("data") else None
    if fake():
        return [{"path": r"D:\WinAIO\Data\ISO\Win11_25H2_English_x64.iso", "name": "Win11_25H2_English_x64.iso", "size": 5_800_000_000}]
    if not d or not d.exists():
        return []
    return [{"path": str(f), "name": f.name, "size": f.stat().st_size} for f in sorted(d.glob("*.iso"))]


# ================================================================ KHO DRIVER IRST (Intel RST / VMD)
# Máy Intel đời 11 trở lên bật VMD: lúc cài Win không thấy ổ cứng -> chép driver này vào USB, bấm "Load driver".
IRST_BASE = "https://github.com/laocuumon1982-cpu/WIN-AIO-SHARE/raw/main/drivers/"
IRST = [
    {"ver": "19.5.8.1059.2", "gen": "Intel Core đời 11 - 13", "min": 11, "max": 13, "file": "IntelRstVmd_19.5.8.1059.2_Intel-Gen11-13.zip"},
    {"ver": "20.2.7.1026", "gen": "Intel Core đời 13 - 15, Core Ultra", "min": 13, "max": 99, "file": "IntelRstVmd_20.2.7.1026-Gen13-15.zip"},
]


def _cpu_gen(name):
    """(đời CPU Intel, cần IRST?) theo tên CPU - giống cách Tiện ích cài Win dạo nhận biết."""
    if "intel" not in name.lower():
        return None, False
    if re.search(r"Core\(TM\)\s*Ultra|Core Ultra", name, re.I):
        return "Ultra", True
    m = re.search(r"(\d+)(?:st|nd|rd|th)\s+Gen", name, re.I)
    if m:
        g = int(m.group(1))
    else:
        m = re.search(r"i\d-?(\d{4,5})", name, re.I)
        if not m:
            return None, False
        n = m.group(1)
        g = int(n[:2]) if len(n) >= 5 else int(n[:1])
    return g, g >= 11


def irst_info():
    if fake():
        cpu = "13th Gen Intel(R) Core(TM) i5-13400"
    else:
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                cpu = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            cpu = ""
    gen, need = _cpu_gen(cpu)
    rows = []
    for it in IRST:
        r = dict(it, url=IRST_BASE + it["file"])
        r["fit"] = bool(need and (gen == "Ultra" and it["max"] == 99 or isinstance(gen, int) and it["min"] <= gen <= it["max"]))
        rows.append(r)
    if need and not any(r["fit"] for r in rows):
        rows[-1]["fit"] = True
    return {"cpu": cpu, "gen": gen, "need": need, "list": rows}


def _extract_zip(zp, dest):
    zp, dest = Path(zp), Path(dest)
    out = dest / zp.stem
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        top = {n.split("/")[0] for n in names if n.strip("/")}
        z.extractall(dest if top == {zp.stem} else out)       # zip đã có sẵn thư mục cùng tên -> không lồng 2 lớp
    return out


def irst_get(j, file, dest="", local=""):
    """Tải (hoặc lấy file .zip có sẵn) driver IRST rồi giải nén vào dest (thường là gốc USB cài Win)."""
    it = next((x for x in IRST if x["file"] == file), None)
    if not it and not local:
        raise RuntimeError("Không có bản driver này")
    dest = absp(dest) if dest else (absp("Data/Driver") if fake() else data_dir("Driver"))
    if fake():
        time.sleep(0.8)
        return {"text": f"Đã giải nén driver vào {dest}\\{Path(local or file).stem}.", "dest": str(dest)}
    if local:
        zp = absp(local)
    else:
        import apple
        zp = Path(apple.dl_files(j, [{"name": it["file"], "url": IRST_BASE + it["file"], "size": 0}], data_dir("Driver"), "Driver IRST " + it["ver"])["path"])
    j["pct"], j["text"] = 99, "Đang giải nén driver..."
    dest.mkdir(parents=True, exist_ok=True)
    out = _extract_zip(zp, dest)
    return {"text": f"Đã giải nén driver vào {out}. Lúc cài Win không thấy ổ cứng: bấm 'Load driver' → Browse → chọn thư mục này "
                    "(thư mục VMD), bỏ tick 'Hide drivers...' nếu không thấy, chọn 'Intel RST VMD Controller' → Next.",
            "dest": str(out)}
