"""Win AIO by Duy Anh - v3.0: phần bổ sung cho nút MS Office (lấy ý tưởng từ "Cài đặt Office v4.3"):
- Gỡ Office tận gốc (Click-to-Run + MSI + dọn tàn dư)
- Thiết lập Office cho văn bản Việt Nam (A4, lề, Times New Roman, giãn dòng, tắt Protected View / màn hình Start / kiểm tra chính tả)
- Bản quyền Office / Windows bằng key của khách: nhập key online, kích hoạt qua điện thoại (IID → CID),
  đổi Office Retail → Volume khi khách có key Volume (MAK), lấy key Windows OEM trong BIOS,
  kiểm tra & dọn dấu vết crack KMS / Ohook, xóa key Windows.
Không có chức năng bẻ khóa / KMS lậu."""
import json
import os
import re
import time
from pathlib import Path

from mgr import H, fake

KEY_RE = re.compile(r"^[A-Z0-9]{5}(-[A-Z0-9]{5}){4}$")
OFFICE_PROCS = ["WINWORD", "EXCEL", "POWERPNT", "OUTLOOK", "ONENOTE", "MSACCESS", "MSPUB", "VISIO", "WINPROJ", "OfficeClickToRun",
                "OfficeC2RClient", "AppVShNotify", "MSOSYNC", "SDXHelper"]
OFFICE_SVCS = ["ClickToRunSvc", "OfficeClickToRun", "OfficeSvc", "ose", "ose64", "osppsvc"]


def _ps(script, timeout=600):
    return H["ps"](script, timeout=timeout)


def _norm_key(k):
    k = re.sub(r"[^A-Za-z0-9]", "", k or "").upper()
    return "-".join(k[i:i + 5] for i in range(0, 25, 5)) if len(k) == 25 else ""


# ================================================================ OSPP / SLMGR
def ospp_path():
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                 os.environ.get("ProgramW6432", r"C:\Program Files")):
        for sub in ("Office16", "root\\Office16", "Office15"):
            p = Path(base) / "Microsoft Office" / sub / "ospp.vbs"
            if p.exists():
                return p
    return None


def _vbs(script, args, timeout=180):
    code, out = H["run"](f'cscript //nologo "{script}" {args}', shell=True, timeout=timeout)
    return code, (out or "").strip()


def _ospp(args, timeout=180):
    p = ospp_path()
    if not p:
        raise RuntimeError("Chưa thấy Office trên máy (không có ospp.vbs).")
    return _vbs(p, args, timeout)


def _slmgr(args, timeout=180):
    return _vbs(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "slmgr.vbs", args, timeout)


def _err(out):
    return bool(re.search(r"ERROR CODE|Error:|0x[Cc]00[0-9A-Fa-f]{5}|<Product activation failed>|failed", out or ""))


def lic_status(kind):
    """Trạng thái bản quyền Office (ospp /dstatus) hoặc Windows (slmgr /dli + /xpr)."""
    if fake():
        return {"ok": True, "out": ("LICENSE NAME: Office 24, Office24ProPlus2024R_Retail edition\nLICENSE STATUS:  ---LICENSED---\n"
                                    "Last 5 characters of installed product key: XXXXX") if kind == "office" else
                "Name: Windows(R), Professional edition\nPartial Product Key: XXXXX\nLicense Status: Licensed\n\nThe machine is permanently activated."}
    if kind == "office":
        if not ospp_path():
            return {"ok": False, "out": "Chưa thấy Office trên máy (không có ospp.vbs)."}
        code, out = _ospp("/dstatus")
        return {"ok": code == 0, "out": out}
    c1, o1 = _slmgr("/dli")
    c2, o2 = _slmgr("/xpr")
    return {"ok": c1 == 0, "out": o1 + "\n\n" + o2}


def lic_key(j, kind, key):
    """Nhập key của khách rồi kích hoạt online. Office báo 0xC004F069 (key Volume cho Office Retail) -> báo cần đổi sang Volume."""
    key = _norm_key(key)
    if not key:
        raise RuntimeError("Key không đúng dạng XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")
    j["pct"], j["text"] = -1, "Đang nhập key và kích hoạt online..."
    if fake():
        time.sleep(1)
        return {"ok": True, "text": "Đã nhập key và kích hoạt (chạy thử).", "out": "Product key installation successful\nProduct activation successful"}
    if kind == "office":
        c1, o1 = _ospp(f"/inpkey:{key}")
        if "0xC004F069" in o1.upper() or ("sku" in o1.lower() and "not found" in o1.lower()):
            return {"ok": False, "need_volume": True, "out": o1,
                    "text": "Key này là key Volume nhưng Office đang cài là bản Retail. Bấm 'Đổi sang Volume rồi nhập key' để tool tự chuyển (dùng ODT của Microsoft)."}
        if _err(o1):
            return {"ok": False, "out": o1, "text": "Không nhập được key - key sai hoặc không đúng phiên bản Office đang cài."}
        c2, o2 = _ospp("/act", 240)
        ok = not _err(o2)
    else:
        c1, o1 = _slmgr(f"/ipk {key}")
        if _err(o1):
            return {"ok": False, "out": o1, "text": "Không nhập được key - key sai hoặc không đúng bản Windows đang cài (Home / Pro...)."}
        c2, o2 = _slmgr("/ato", 240)
        ok = not _err(o2)
    return {"ok": ok, "out": o1 + "\n\n" + o2,
            "text": "Đã kích hoạt thành công." if ok else "Đã nhập key nhưng kích hoạt online chưa được - xem chi tiết, hoặc dùng Kích hoạt qua điện thoại."}


def _fmt_groups(digits, n):
    return "-".join(digits[i:i + n] for i in range(0, len(digits), n))


def lic_iid(kind, key=""):
    """(Tùy chọn nhập key trước) rồi lấy Installation ID để gọi tổng đài / trang kích hoạt của Microsoft lấy Confirmation ID."""
    if fake():
        return {"ok": True, "iid": _fmt_groups("1234567" * 9, 7 if kind != "office" else 6), "out": "(chạy thử)"}
    pre = ""
    if key:
        k = _norm_key(key)
        if not k:
            return {"ok": False, "out": "Key không đúng dạng."}
        c, pre = _ospp(f"/inpkey:{k}") if kind == "office" else _slmgr(f"/ipk {k}")
        if _err(pre):
            return {"ok": False, "out": pre}
    c, out = _ospp("/dinstid") if kind == "office" else _slmgr("/dti")
    digits = ""
    for ln in out.splitlines():
        d = re.sub(r"[\s-]", "", ln.rsplit(":", 1)[-1])
        if re.fullmatch(r"\d{54,63}", d):
            digits = d
    return {"ok": bool(digits), "iid": _fmt_groups(digits, 6 if kind == "office" else 7) if digits else "", "out": (pre + "\n" + out).strip()}


def lic_cid(j, kind, cid):
    digits = re.sub(r"\D", "", cid or "")
    if len(digits) != 48:
        raise RuntimeError("Confirmation ID phải đủ 48 chữ số (8 nhóm x 6 số).")
    j["pct"], j["text"] = -1, "Đang kích hoạt bằng Confirmation ID..."
    if fake():
        time.sleep(1)
        return {"ok": True, "text": "Đã kích hoạt qua điện thoại (chạy thử).", "out": ""}
    if kind == "office":
        c1, o1 = _ospp(f"/actcid:{digits}")
        c2, o2 = _ospp("/act")
        out = o1 + "\n\n" + o2
    else:
        c1, o1 = _slmgr(f"/atp {digits}")
        c2, o2 = _slmgr("/dli")
        out = o1 + "\n\n" + o2
    ok = not _err(o1)
    return {"ok": ok, "out": out, "text": "Đã kích hoạt bằng Confirmation ID." if ok else "Confirmation ID không đúng hoặc không khớp Installation ID."}


def lic_oem():
    """Key Windows OEM gắn trong BIOS (máy bán kèm Windows bản quyền)."""
    if fake():
        return {"key": "ABCDE-FGHIJ-KLMNO-PQRST-UVWXY", "desc": "[4.0] Professional OEM:DM"}
    code, out = _ps("$s = Get-CimInstance SoftwareLicensingService; [pscustomobject]@{key=$s.OA3xOriginalProductKey; "
                    "desc=$s.OA3xOriginalProductKeyDescription} | ConvertTo-Json -Compress", timeout=60)
    try:
        d = json.loads(out)
    except ValueError:
        d = {}
    return {"key": (d.get("key") or "").strip().upper(), "desc": (d.get("desc") or "").strip()}


OHOOK = ["root\\vfs\\System\\sppc.dll", "root\\vfs\\System\\sppcs.dll", "root\\vfs\\SystemX86\\sppc.dll", "root\\vfs\\SystemX86\\sppcs.dll"]
CRACK_FILES = [r"C:\Windows\SECOH-QAD.dll", r"C:\Windows\SECOH-QAD.exe", r"C:\Program Files\KMSpico", r"C:\ProgramData\KMSAutoS",
               r"C:\Windows\System32\SppExtComObjHook.dll", r"C:\Windows\System32\SppExtComObjPatcher.dll"]


def _office_roots():
    out = []
    for base in {os.environ.get("ProgramW6432", r"C:\Program Files"), os.environ.get("ProgramFiles", r"C:\Program Files"),
                 os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")}:
        out.append(Path(base) / "Microsoft Office")
    return out


def crack_check():
    """Phân tích Office có đang kích hoạt bằng KMS lậu / Ohook không (để dọn trước khi nhập key thật)."""
    if fake():
        return {"found": True, "items": ["Office đang trỏ tới máy chủ KMS 127.0.0.1 (crack KMS cục bộ)",
                                         r"Tệp Ohook giả mạo: C:\Program Files\Microsoft Office\root\vfs\System\sppc.dll"]}
    items = []
    p = ospp_path()
    if p:
        code, st = _vbs(p, "/dstatus")
        if "VOLUME_KMSCLIENT" in st.upper():
            m = re.search(r"KMS machine (?:name|IP address)[^:]*:\s*(\S+)", st, re.I)
            host = m.group(1) if m else ""
            if not host:
                items.append("Office là bản Volume KMS nhưng chưa thấy máy chủ KMS")
            elif host.lower() in ("127.0.0.1", "0.0.0.0", "localhost") or host.startswith("127."):
                items.append(f"Office đang trỏ tới máy chủ KMS {host} (crack KMS cục bộ: KMSpico, KMSAuto, AAct...)")
            else:
                items.append(f"Office đang kích hoạt qua máy chủ KMS {host} - nếu không phải máy chủ của công ty thì là KMS lậu")
    for f in CRACK_FILES:
        if os.path.exists(f):
            items.append("Tệp crack: " + f)
    for r in _office_roots():
        for h in OHOOK:
            if (r / h).exists():
                items.append("Tệp Ohook giả mạo: " + str(r / h))
    return {"found": bool(items), "items": items}


def crack_clear(j):
    """Dọn dấu vết kích hoạt lậu của Office: máy chủ KMS, key KMS/Volume giả, tệp Ohook, cache giấy phép."""
    j["pct"], j["text"] = -1, "Đang dọn dấu vết kích hoạt lậu của Office..."
    if fake():
        time.sleep(1)
        return {"text": "Đã dọn sạch dấu vết KMS / Ohook của Office (chạy thử). Giờ có thể nhập key bản quyền."}
    p = ospp_path()
    if p:
        _vbs(p, "/remhst")
    hooks = ",".join("'%s'" % str(r / h).replace("'", "''") for r in _office_roots() for h in OHOOK)
    _ps(r"""
Remove-ItemProperty 'HKLM:\SOFTWARE\Microsoft\OfficeSoftwareProtectionPlatform' KeyManagementServiceName -ErrorAction SilentlyContinue
Remove-ItemProperty 'HKLM:\SOFTWARE\Microsoft\OfficeSoftwareProtectionPlatform' KeyManagementServicePort -ErrorAction SilentlyContinue
Get-CimInstance SoftwareLicensingProduct -Filter "ApplicationID='0ff1ce15-a989-479d-af46-f275c6370663' AND PartialProductKey IS NOT NULL" -ErrorAction SilentlyContinue |
  Where-Object { $_.Description -match 'KMS' } | ForEach-Object { Invoke-CimMethod -InputObject $_ -MethodName UninstallProductKey | Out-Null }
foreach($f in @(""" + hooks + r""")){ if(Test-Path $f){ Remove-Item $f -Force -ErrorAction SilentlyContinue } }
foreach($c in '{80E5DF79-4BDB-40B1-A3EE-07F2959DD7A3}','{825BDE9D-1F03-4D88-AC10-44DEBCEB9DB3}'){
  Remove-Item "HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\REGISTRY\MACHINE\Software\Classes\CLSID\$c" -Recurse -Force -ErrorAction SilentlyContinue }
Remove-Item "$env:LOCALAPPDATA\Microsoft\Office\16.0\Licenses\*" -Force -ErrorAction SilentlyContinue
Restart-Service sppsvc -Force -ErrorAction SilentlyContinue
'OK'""", timeout=180)
    left = crack_check()
    return {"text": "Đã dọn dấu vết KMS / Ohook của Office." + ("" if not left["found"] else " Còn sót: " + "; ".join(left["items"])),
            "left": left["items"]}


def win_clear_key(j):
    """Gỡ key Windows đang cài + xóa máy chủ KMS (để nhập key bản quyền mới)."""
    j["pct"], j["text"] = -1, "Đang gỡ key Windows và cấu hình KMS..."
    if fake():
        time.sleep(1)
        return {"text": "Đã gỡ key Windows (chạy thử). Nhập key mới rồi kích hoạt."}
    outs = [_slmgr(a)[1] for a in ("/upk", "/cpky", "/ckms")]
    return {"text": "Đã gỡ key Windows và xóa cấu hình KMS. Nhập key bản quyền mới rồi bấm Kích hoạt.", "out": "\n\n".join(outs)}


def _office_info():
    code, out = _ospp("/dstatus")
    g = lambda k: (re.search(k + r"\s*:\s*(.+)", out, re.I) or [None, ""])[1].strip()   # noqa: E731
    return g("LICENSE NAME"), g("LICENSE DESCRIPTION"), out


def to_volume(j, key):
    """Office Retail + key Volume (MAK) của khách: cài lại Office kênh Volume bằng ODT rồi nhập key + kích hoạt."""
    key = _norm_key(key)
    if not key:
        raise RuntimeError("Key không đúng dạng")
    if fake():
        for i in range(0, 101, 20):
            j["pct"], j["text"] = i, f"Đang chuyển Office sang Volume: {i}%"
            time.sleep(0.3)
        return {"ok": True, "text": "Đã chuyển sang ProPlus2024Volume và kích hoạt bằng key (chạy thử).", "out": ""}
    name, desc, _ = _office_info()
    t = name + " " + desc
    year = "2024" if re.search("2024", t) else "2019" if re.search("2019", t) else "2021"
    prod = ("VisioPro" if re.search("Visio", t, re.I) else "ProjectPro" if re.search("Project", t, re.I)
            else "Standard" if re.search("Standard", t, re.I) else "ProPlus") + year + "Volume"
    import winreg
    arch = "64"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration") as k:
            arch = "32" if "86" in winreg.QueryValueEx(k, "Platform")[0] else "64"
    except OSError:
        pass
    xml = (f'<Configuration>\n  <Add OfficeClientEdition="{arch}" Channel="PerpetualVL{year}">\n    <Product ID="{prod}">\n'
           '      <Language ID="MatchOS" />\n    </Product>\n  </Add>\n  <Display Level="None" AcceptEULA="TRUE" />\n</Configuration>\n')
    exe = Path(H["odt"]())
    cfg = exe.parent / "winaio_volume.xml"
    cfg.write_text(xml, encoding="utf-8")
    j["pct"], j["text"] = -1, f"Đang chuyển Office sang {prod} (kênh PerpetualVL{year}) - 5 - 15 phút, cần mạng..."
    code, out = H["run"]([str(exe), "/configure", str(cfg)], timeout=3600)
    cfg.unlink(missing_ok=True)
    _, d2, _ = _office_info()
    if not re.search("VOLUME", d2, re.I):
        return {"ok": False, "text": f"Chưa chuyển được sang Volume (ODT mã {code}).", "out": out}
    c1, o1 = _ospp(f"/inpkey:{key}")
    c2, o2 = _ospp("/act", 240)
    ok = not _err(o1) and not _err(o2)
    return {"ok": ok, "out": o1 + "\n\n" + o2,
            "text": f"Đã chuyển sang {prod} và " + ("kích hoạt thành công." if ok else "nhập key, nhưng kích hoạt chưa được - xem chi tiết.")}


# ================================================================ GỠ OFFICE TẬN GỐC
SCAN_PS = r"""
$k='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
$r = Get-ItemProperty $k -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match 'Microsoft Office|Microsoft 365|Microsoft Project|Microsoft Visio' } |
  ForEach-Object { [pscustomobject]@{ name=$_.DisplayName; c2r=[bool]($_.UninstallString -match 'OfficeClickToRun'); msi=[bool]($_.WindowsInstaller -eq 1); code=$_.PSChildName } }
@($r) | ConvertTo-Json -Compress"""


def off_scan():
    if fake():
        return {"c2r": ["Microsoft Office Professional Plus 2024 - vi-vn"], "msi": ["Microsoft Office Professional Plus 2010"]}
    code, out = _ps(SCAN_PS, timeout=60)
    try:
        rows = json.loads(out) if out.strip() else []
    except ValueError:
        rows = []
    rows = rows if isinstance(rows, list) else [rows]
    c2r = sorted({r["name"] for r in rows if r.get("c2r")})
    msi = sorted({r["name"] for r in rows if r.get("msi") and re.match(r"^\{[0-9A-F-]+\}$", r.get("code") or "", re.I)
                  and re.search(r"Microsoft Office|Microsoft Project|Microsoft Visio", r["name"])})
    return {"c2r": c2r, "msi": msi}


def off_remove(j, c2r=True, msi=True, clean=True):
    """Gỡ Office: Click-to-Run (365 / 2016 - 2024) bằng OfficeClickToRun.exe, MSI (2010 - 2016) bằng msiexec, rồi dọn tàn dư."""
    steps = [s for s, on in (("c2r", c2r), ("msi", msi), ("clean", clean)) if on]
    if not steps:
        raise RuntimeError("Chưa chọn mục nào để gỡ")
    if fake():
        for i in range(0, 101, 10):
            j["pct"], j["text"] = i, f"Đang gỡ Office: {i}%"
            time.sleep(0.15)
        return {"text": "Đã gỡ sạch Microsoft Office (chạy thử). Khởi động lại máy trước khi cài bản mới."}
    procs = ",".join("'%s'" % p for p in OFFICE_PROCS)
    _ps(f"Stop-Process -Name {procs} -Force -ErrorAction SilentlyContinue", timeout=60)
    log = []
    if c2r:
        j["pct"], j["text"] = 5, "Đang gỡ Office Click-to-Run (2 - 5 phút)..."
        code, out = _ps(r"""
$p = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun' -ErrorAction SilentlyContinue).InstallPath
$exe = @("$p\OfficeClickToRun.exe", "$env:CommonProgramFiles\Microsoft Shared\ClickToRun\OfficeClickToRun.exe",
         "${env:CommonProgramFiles(x86)}\Microsoft Shared\ClickToRun\OfficeClickToRun.exe") | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if(-not $exe){ 'NOC2R'; return }
$plat = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' -ErrorAction SilentlyContinue).Platform; if(-not $plat){ $plat='x64' }
$a = "scenario=install scenariosubtype=ARP sourcetype=None productstoremove=AllProducts platform=$plat culture=en-us forceappshutdown=true DisplayLevel=False"
$pr = Start-Process $exe -ArgumentList $a -PassThru -WindowStyle Hidden
if(-not $pr.WaitForExit(900000)){ $pr.Kill() }
'C2R=' + $pr.ExitCode""", timeout=960)
        log.append("Click-to-Run: " + ("không có" if "NOC2R" in out else out.strip()[-60:]))
    if msi:
        j["pct"], j["text"] = 50, "Đang gỡ Office MSI..."
        code, out = _ps(r"""
$k='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
$n = 0
Get-ItemProperty $k -ErrorAction SilentlyContinue | Where-Object { $_.WindowsInstaller -eq 1 -and $_.DisplayName -match 'Microsoft Office|Microsoft Project|Microsoft Visio' -and $_.PSChildName -match '^\{' } |
  ForEach-Object { Start-Process msiexec.exe -ArgumentList "/x $($_.PSChildName) /qn /norestart" -Wait -WindowStyle Hidden; $n++ }
'MSI=' + $n""", timeout=1800)
        log.append("MSI: " + out.strip()[-30:])
    if clean:
        j["pct"], j["text"] = 80, "Đang dọn tàn dư: dịch vụ, tác vụ, registry, thư mục, lối tắt, key..."
        svcs = ",".join("'%s'" % s for s in OFFICE_SVCS)
        p = ospp_path()
        if p:
            code, st = _vbs(p, "/dstatus")
            for k5 in re.findall(r"Last 5 characters of installed product key:\s*([A-Z0-9]{5})", st, re.I):
                _vbs(p, f"/unpkey:{k5}")
        _ps(r"""
foreach($s in @(""" + svcs + r""")){ Stop-Service $s -Force -ErrorAction SilentlyContinue; & sc.exe delete $s 2>$null | Out-Null }
Get-ScheduledTask -TaskPath '\Microsoft\Office\*' -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue
$reg = 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun','HKLM:\SOFTWARE\Microsoft\AppVISV','HKLM:\SOFTWARE\WOW6432Node\Microsoft\AppVISV',
       'HKLM:\SOFTWARE\Microsoft\Office\16.0','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Office\16.0','HKLM:\SOFTWARE\Microsoft\Office\15.0',
       'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Office\15.0','HKCU:\Software\Microsoft\Office\16.0\Common\Licensing'
foreach($r in $reg){ Remove-Item $r -Recurse -Force -ErrorAction SilentlyContinue }
$k='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
foreach($b in $k){ Get-ChildItem $b -ErrorAction SilentlyContinue | Where-Object { (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue).DisplayName -match '^Microsoft (Office|365)' } |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }
$d = "$env:ProgramFiles\Microsoft Office","${env:ProgramFiles(x86)}\Microsoft Office","$env:CommonProgramFiles\Microsoft Shared\ClickToRun",
     "${env:CommonProgramFiles(x86)}\Microsoft Shared\ClickToRun","$env:CommonProgramFiles\Microsoft Shared\OFFICE16","${env:CommonProgramFiles(x86)}\Microsoft Shared\OFFICE16",
     "$env:ProgramData\Microsoft\ClickToRun","$env:ProgramData\Microsoft\Office\Licenses","$env:LOCALAPPDATA\Microsoft\Office\16.0\Licenses"
foreach($x in $d){ if($x -and (Test-Path $x)){ & takeown.exe /f $x /r /d y 2>$null | Out-Null; & icacls.exe $x /grant *S-1-5-32-544:F /t /q 2>$null | Out-Null
  Remove-Item $x -Recurse -Force -ErrorAction SilentlyContinue } }
$lnk = "$env:PUBLIC\Desktop","$env:USERPROFILE\Desktop","$env:ProgramData\Microsoft\Windows\Start Menu\Programs","$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
foreach($l in $lnk){ Get-ChildItem $l -Filter *.lnk -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.BaseName -match '^(Word|Excel|PowerPoint|Outlook|OneNote|Access|Publisher|Project|Visio|Skype for Business)( 20\d\d)?$' } |
  Remove-Item -Force -ErrorAction SilentlyContinue }
'OK'""", timeout=900)
        log.append("Đã dọn tàn dư")
    left = off_scan()
    still = left["c2r"] + left["msi"]
    msg = ("Đã gỡ sạch Microsoft Office. Khởi động lại máy trước khi cài bản mới." if not still
           else "Đã gỡ, nhưng vẫn còn: " + ", ".join(still) + ". Khởi động lại máy rồi gỡ lại lần nữa.")
    return {"text": msg, "out": "\n".join(log)}


# ================================================================ THIẾT LẬP OFFICE CHO VĂN BẢN VIỆT NAM
def off_tune(j, o):
    """Word: khổ A4, lề, font + cỡ chữ, giãn dòng (lưu vào Normal.dotm để mọi văn bản mới đều theo), đơn vị cm, tắt kiểm tra chính tả.
    Word / Excel / PowerPoint: tắt Protected View, tắt màn hình Start. Excel: font mặc định."""
    o = o or {}
    font = re.sub(r"[^\w .-]", "", o.get("font") or "Times New Roman")[:40] or "Times New Roman"
    size = max(8, min(30, float(o.get("size") or 14)))
    m = [max(0.0, min(6.0, float(x))) for x in (o.get("margins") or [2, 2, 3, 2])][:4]
    line = max(1.0, min(3.0, float(o.get("line") or 1.15)))
    after = max(0, min(24, float(o.get("after") or 0)))
    if fake():
        time.sleep(1)
        return {"text": f"Đã thiết lập Office: A4, lề {m[0]}/{m[1]}/{m[2]}/{m[3]} cm, {font} {size:g}, giãn dòng {line:g} (chạy thử)."}
    running = [p for p in ("WINWORD.EXE", "EXCEL.EXE", "POWERPNT.EXE") if __import__("mgr").proc_running([p])]
    if running:
        raise RuntimeError("Đang mở " + ", ".join(running) + " - lưu và đóng Word / Excel / PowerPoint rồi bấm lại.")
    pts = [round(x * 72 / 2.54, 2) for x in m]
    b = lambda k: "$true" if o.get(k, True) else "$false"   # noqa: E731
    j["pct"], j["text"] = -1, "Đang mở Word / Excel ngầm để thiết lập..."
    code, out = _ps(r"""
$ErrorActionPreference = 'Continue'
function S($k,$n,$v){ if(-not (Test-Path $k)){ New-Item $k -Force | Out-Null }; Set-ItemProperty $k $n $v -Type DWord -Force }
$base = 'HKCU:\Software\Microsoft\Office\16.0'
if(""" + b("nostart") + r"""){ S "$base\Common\General" DisableBootToOfficeStart 1; S "$base\Excel\Options" ShowStart 0; S "$base\PowerPoint\Options" ShowStart 0 }
if(""" + b("pv") + r"""){ foreach($a in 'Word','Excel','PowerPoint'){ foreach($n in 'DisableInternetFilesInPV','DisableUnsafeLocationsInPV','DisableAttachmentsInPV'){ S "$base\$a\Security\ProtectedView" $n 1 } } }
$res = @()
try {
  $w = New-Object -ComObject Word.Application
  $w.Visible = $false; $w.DisplayAlerts = 0; $w.Options.SaveNormalPrompt = $false
  $w.Options.MeasurementUnit = 1
  if(""" + b("nospell") + r"""){ $w.Options.CheckSpellingAsYouType = $false; $w.Options.CheckGrammarAsYouType = $false }
  $tp = $w.NormalTemplate.FullName
  if(Test-Path $tp){ $d = $w.Documents.Open($tp) } else { $d = $w.Documents.Add(); $d.SaveAs2($tp, 15) }
  $ps = $d.PageSetup; $ps.Orientation = 0; $ps.PaperSize = 7
  $ps.TopMargin = """ + str(pts[0]) + "; $ps.BottomMargin = " + str(pts[1]) + "; $ps.LeftMargin = " + str(pts[2]) + "; $ps.RightMargin = " + str(pts[3]) + r"""
  $st = $d.Styles.Item(-1)
  $st.Font.Name = '""" + font + "'; $st.Font.Size = " + f"{size:g}" + r"""
  $st.ParagraphFormat.LineSpacingRule = 5; $st.ParagraphFormat.LineSpacing = """ + f"{12 * line:.2f}" + r"""
  $st.ParagraphFormat.SpaceBefore = 0; $st.ParagraphFormat.SpaceAfter = """ + f"{after:g}" + r"""
  $d.Save(); $d.Close($false); $w.Quit(); $res += 'WORD'
} catch { $res += 'WORDERR:' + $_.Exception.Message; try { $w.Quit() } catch {} }
try {
  $x = New-Object -ComObject Excel.Application; $x.DisplayAlerts = $false
  $x.StandardFont = '""" + font + "'; $x.StandardFontSize = " + f"{size:g}" + r"""
  $x.Quit(); $res += 'EXCEL'
} catch { $res += 'EXCELERR' }
if(""" + b("nospell") + r"""){ S "$base\PowerPoint\Options" DefaultProofingState 0; S "$base\PowerPoint\Options" AutoProofing 0 }
[System.GC]::Collect()
$res -join ';'""", timeout=300)
    if "WORD" not in out:
        raise RuntimeError("Không mở được Word để thiết lập (Office chưa cài / chưa mở lần đầu?): " + out[-300:])
    msg = (f"Đã thiết lập: văn bản mới trong Word khổ A4, lề trên {m[0]:g} - dưới {m[1]:g} - trái {m[2]:g} - phải {m[3]:g} cm, "
           f"{font} {size:g}, giãn dòng {line:g}, đơn vị cm" + (", tắt gạch đỏ chính tả" if o.get("nospell", True) else "")
           + (", tắt Protected View" if o.get("pv", True) else "") + (", bỏ màn hình Start" if o.get("nostart", True) else "")
           + (". Excel: font mặc định " + font if "EXCEL;" in out + ";" else "") + ".")
    return {"text": msg}
