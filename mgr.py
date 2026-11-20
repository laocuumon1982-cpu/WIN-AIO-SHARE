# -*- coding: utf-8 -*-
"""Win AIO by Duy Anh - phần QUẢN LÝ / DỌN DẸP / SAO LƯU (v2.1).

Khởi động cùng Windows, gỡ phần mềm tận gốc, ứng dụng MS Store, Defender, dọn rác, phân tích ổ đĩa,
cache CapCut, macro Excel, metadata ảnh, sao lưu thư mục người dùng / Zalo / trình duyệt, Zalo nhiều tài khoản.
win_aio.py gọi init() để truyền các hàm dùng chung (ps, run_hidden, FAKE...).
"""
import datetime as dt
import json
import os
import re
import shutil
import struct
import subprocess
import threading
import time
import uuid
from pathlib import Path

IS_WIN = os.name == "nt"
if IS_WIN:
    import winreg
H = {}                                       # ps, run, fake, base, data, ensure_disk, log, history


def init(**kw):
    H.update(kw)


def fake():
    return H.get("fake", False) or not IS_WIN


def env(name, default=""):
    return os.path.expandvars(os.environ.get(name, default))


def human(n):
    n = float(n or 0)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.0f} {u}" if u in ("B", "KB") else f"{n:.1f} {u}"
        n /= 1024


def absp(p):
    p = Path(os.path.expandvars(str(p or "").strip().strip('"')))
    return p if p.is_absolute() else Path(H.get("base", ".")) / p


def data_dir(*parts):
    H["ensure_disk"]()
    p = Path(H["data"]).joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ================================================================= VIỆC CHẠY LÂU (có % tiến độ)
JOBS = {}


def job_start(label, fn, *args):
    jid = uuid.uuid4().hex[:10]
    j = JOBS[jid] = {"id": jid, "label": label, "pct": 0, "text": "Đang chuẩn bị...", "done": False, "ok": None,
                     "result": None, "stop": False, "t0": time.time()}

    def run():
        try:
            j["result"] = fn(j, *args)
            j["ok"] = True
        except Exception as e:              # noqa: BLE001
            j["ok"], j["result"] = False, str(e)
        j["done"], j["pct"] = True, 100
        H["log"](f"{'✔' if j['ok'] else '✖'} {label}" + ("" if j["ok"] else f": {j['result']}"), "ok" if j["ok"] else "err")
        H["history"](label, "Quản lý", "Xong" if j["ok"] else "Lỗi", j["result"] if isinstance(j["result"], str) else "")
    H["log"]("▶ " + label)
    threading.Thread(target=run, daemon=True).start()
    return jid


def job_status(jid):
    j = JOBS.get(jid)
    if not j:
        return {"done": True, "ok": False, "result": "Không có việc này"}
    return {k: v for k, v in j.items() if k != "stop"}


def job_stop(jid):
    if jid in JOBS:
        JOBS[jid]["stop"] = True
    return True


def walk_size(root, j=None, cap=None):
    """Tổng dung lượng một thư mục (bỏ qua link / junction, bỏ qua file không đọc được)."""
    total, n, stack = 0, 0, [str(root)]
    while stack:
        if j and j.get("stop"):
            break
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_symlink():
                            continue
                        if e.is_dir(follow_symlinks=False):
                            if IS_WIN and e.stat(follow_symlinks=False).st_file_attributes & 0x400:
                                continue      # junction / reparse point
                            stack.append(e.path)
                        else:
                            total += e.stat(follow_symlinks=False).st_size
                            n += 1
                    except OSError:
                        pass
        except OSError:
            pass
        if cap and n > cap:
            break
    return total, n


def copy_tree(src, dst, j, skip_dirs=(), base_pct=0, span=100, overwrite=False):
    """Chép cả thư mục, có % theo dung lượng. Trả (số file, dung lượng, số lỗi)."""
    src, dst = Path(src), Path(dst)
    total, _ = walk_size(src)
    done = copied = errs = 0
    skip = {s.lower() for s in skip_dirs}
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d.lower() not in skip]
        if j.get("stop"):
            break
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            s, t = Path(root) / f, dst / rel / f
            try:
                sz = s.stat().st_size
                if overwrite or not t.exists() or t.stat().st_size != sz:
                    shutil.copy2(s, t)
                copied += 1
                done += sz
            except OSError:
                errs += 1
            if total:
                j["pct"] = base_pct + int(span * min(1, done / total))
            j["text"] = f"{human(done)} / {human(total)} · {copied} file" + (f" · {errs} lỗi" if errs else "")
    return copied, done, errs


def proc_running(names):
    if fake():
        return []
    code, out = H["run"](["tasklist", "/fo", "csv", "/nh"], timeout=30)
    run = {l.split('","')[0].strip('"').lower() for l in (out or "").splitlines() if l.startswith('"')}
    return [n for n in names if n.lower() in run]


def kill(names):
    if not fake():
        for n in names:
            H["run"](["taskkill", "/f", "/im", n], timeout=30)
        time.sleep(1.5)


# ================================================================= KHỞI ĐỘNG CÙNG WINDOWS
APPROVED = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved"
FAKE_STARTUP = [
    {"name": "Adobe CCXProcess", "cmd": r"C:\Program Files (x86)\Adobe\Adobe Creative Cloud Experience\CCXProcess.exe", "where": "HKLM Run (32-bit)", "on": False, "pub": "Adobe Inc."},
    {"name": "BraveSoftware Update", "cmd": r'"C:\Users\Admin\AppData\Local\BraveSoftware\Update\BraveUpdateCore.exe"', "where": "HKCU Run", "on": True, "pub": "BraveSoftware Inc."},
    {"name": "IDMan", "cmd": r"C:\Program Files (x86)\Internet Download Manager\IDMan.exe /onboot", "where": "HKCU Run", "on": True, "pub": "Tonec Inc."},
    {"name": "SecurityHealth", "cmd": r"C:\Windows\system32\SecurityHealthSystray.exe", "where": "HKLM Run", "on": True, "pub": "Microsoft Corporation"},
    {"name": "UniKey", "cmd": r"C:\Program Files\UniKey\UniKeyNT.exe", "where": "HKCU Run", "on": True, "pub": "unikey.org"},
    {"name": "Zalo", "cmd": r'"C:\Users\Admin\AppData\Local\Programs\Zalo\Zalo.exe"', "where": "HKCU Run", "on": False, "pub": "VNG Corp."},
    {"name": "OneDrive.lnk", "cmd": r"C:\Users\Admin\AppData\Local\Microsoft\OneDrive\OneDrive.exe", "where": "Thư mục Startup", "on": True, "pub": "Microsoft Corporation"},
]


def _run_sources():
    if not IS_WIN:
        return []
    return [(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run", "Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "HKLM Run", "Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM Run (32-bit)", "Run32")]


def _startup_dirs():
    return [(Path(env("APPDATA")) / r"Microsoft\Windows\Start Menu\Programs\Startup", "Thư mục Startup",
             winreg.HKEY_CURRENT_USER if IS_WIN else None),
            (Path(env("ProgramData", r"C:\ProgramData")) / r"Microsoft\Windows\Start Menu\Programs\StartUp", "Startup (mọi user)",
             winreg.HKEY_LOCAL_MACHINE if IS_WIN else None)]


def _approved(hive, sub, name):
    try:
        with winreg.OpenKey(hive, APPROVED + "\\" + sub) as k:
            v, _ = winreg.QueryValueEx(k, name)
            return not (bytes(v)[0] & 1)    # 02 / 06 = bật, 03 / 07 = tắt (giống Task Manager)
    except OSError:
        return True


def exe_of(cmd):
    c = os.path.expandvars((cmd or "").strip())
    if c.startswith('"'):
        return c[1:].split('"', 1)[0]
    m = re.match(r"(.+?\.(exe|bat|cmd|com|lnk|vbs|ps1))\b", c, re.I)
    return m.group(1) if m else c.split(" ")[0]


def _publishers(paths):
    """Nhà phát hành (CompanyName) + đích của file .lnk, đọc 1 lượt bằng PowerShell."""
    paths = [p for p in dict.fromkeys(paths) if p]
    if not paths or fake():
        return {}
    js = json.dumps(paths, ensure_ascii=False).replace("'", "''")
    script = ("$r=@{}; $sh=New-Object -ComObject WScript.Shell; foreach($p in (ConvertFrom-Json '" + js + "')){ $t=$p; "
              "if($p -like '*.lnk' -and (Test-Path -LiteralPath $p)){ $t=$sh.CreateShortcut($p).TargetPath }; $c='';"
              "if($t -and (Test-Path -LiteralPath $t)){ $c=(Get-Item -LiteralPath $t).VersionInfo.CompanyName }; "
              "$r[$p]=@{t=[string]$t; c=[string]$c} }; $r | ConvertTo-Json -Compress")
    code, out = H["ps"]("$ErrorActionPreference='SilentlyContinue'; " + script, timeout=120)
    try:
        return json.loads(out[out.index("{"):])
    except Exception:                       # noqa: BLE001
        return {}


def startup_list():
    if fake():
        return [dict(x, id=f"f{i}", path=exe_of(x["cmd"])) for i, x in enumerate(FAKE_STARTUP)]
    items = []
    for hive, key, where, sub in _run_sources():
        try:
            with winreg.OpenKey(hive, key) as k:
                i = 0
                while True:
                    try:
                        name, val, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    i += 1
                    items.append({"id": f"r|{where}|{name}", "name": name, "cmd": str(val), "where": where,
                                  "on": _approved(hive, sub, name), "path": exe_of(str(val))})
        except OSError:
            pass
    for d, where, hive in _startup_dirs():
        if d.exists():
            for f in sorted(d.iterdir()):
                if f.name.lower() == "desktop.ini" or f.is_dir():
                    continue
                items.append({"id": f"f|{where}|{f.name}", "name": f.name, "cmd": str(f), "where": where,
                              "on": _approved(hive, "StartupFolder", f.name), "path": str(f)})
    pubs = _publishers([x["path"] for x in items])
    for x in items:
        p = pubs.get(x["path"]) or {}
        x["pub"] = p.get("c") or ""
        if x["path"].lower().endswith(".lnk") and p.get("t"):
            x["cmd"] = p["t"]
    items.sort(key=lambda x: x["name"].lower())
    return items


def _locate(item_id):
    kind, where, name = item_id.split("|", 2)
    if kind == "r":
        for hive, key, w, sub in _run_sources():
            if w == where:
                return "r", hive, key, sub, name
    else:
        for d, w, hive in _startup_dirs():
            if w == where:
                return "f", hive, str(d), "StartupFolder", name
    raise ValueError("Không tìm thấy mục khởi động")


def startup_set(item_id, on):
    if fake():
        return ""
    _, hive, _, sub, name = _locate(item_id)
    data = (b"\x02" + b"\x00" * 11) if on else (b"\x03" + struct.pack("<Q", int((time.time() + 11644473600) * 1e7)) + b"\x00" * 3)
    with winreg.CreateKeyEx(hive, APPROVED + "\\" + sub, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, name, 0, winreg.REG_BINARY, data)
    return ""


def startup_delete(item_id):
    if fake():
        return ""
    kind, hive, key, sub, name = _locate(item_id)
    bk = data_dir("Backup") / "khoi_dong_da_xoa.json"
    old = []
    try:
        old = json.loads(bk.read_text(encoding="utf-8"))
    except Exception:                       # noqa: BLE001
        pass
    if kind == "r":
        with winreg.OpenKey(hive, key, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as k:
            val, typ = winreg.QueryValueEx(k, name)
            old.append({"time": dt.datetime.now().isoformat(timespec="seconds"), "key": key, "hive": "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM",
                        "name": name, "value": val})
            bk.write_text(json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8")
            winreg.DeleteValue(k, name)
    else:
        f = Path(key) / name
        dst = data_dir("Backup", "KhoiDong_DaXoa")
        shutil.move(str(f), str(dst / name))
    try:
        with winreg.OpenKey(hive, APPROVED + "\\" + sub, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, name)
    except OSError:
        pass
    return ""


# ================================================================= GỠ PHẦN MỀM TẬN GỐC
UNINST = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
FAKE_PROGRAMS = [
    {"id": "HKLM|{A1}", "name": "7-Zip 24.08 (x64)", "pub": "Igor Pavlov", "ver": "24.08", "size": 5.9e6, "date": "15/10/2026", "loc": r"C:\Program Files\7-Zip", "quiet": True},
    {"id": "HKLM|{A2}", "name": "Google Chrome", "pub": "Google LLC", "ver": "131.0.6778.86", "size": 4.2e8, "date": "12/11/2026", "loc": r"C:\Program Files\Google\Chrome\Application", "quiet": False},
    {"id": "HKCU|{A3}", "name": "Zalo", "pub": "VNG Corp.", "ver": "24.11.1", "size": 6.1e8, "date": "02/11/2026", "loc": "", "quiet": False},
    {"id": "HKLM|{A4}", "name": "UltraViewer version 6.6.95", "pub": "DucFabulous", "ver": "6.6.95", "size": 1.6e7, "date": "01/10/2026", "loc": r"C:\Program Files (x86)\UltraViewer", "quiet": False},
    {"id": "HKLM|{A5}", "name": "Microsoft Visual C++ 2015-2022 Redistributable (x64)", "pub": "Microsoft Corporation", "ver": "14.40.33810", "size": 2.0e7, "date": "", "loc": "", "quiet": True},
]


def _uninst_sources():
    return [(winreg.HKEY_LOCAL_MACHINE, UNINST, "HKLM"), (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM32"),
            (winreg.HKEY_CURRENT_USER, UNINST, "HKCU")]


def _q(k, n, d=""):
    try:
        return winreg.QueryValueEx(k, n)[0]
    except OSError:
        return d


def programs_list():
    if fake():
        return FAKE_PROGRAMS
    res, seen = [], set()
    for hive, key, tag in _uninst_sources():
        try:
            root = winreg.OpenKey(hive, key)
        except OSError:
            continue
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(root, i)
            except OSError:
                break
            i += 1
            try:
                with winreg.OpenKey(root, sub) as k:
                    name = str(_q(k, "DisplayName") or "").strip()
                    if not name or _q(k, "SystemComponent", 0) == 1 or _q(k, "ParentKeyName") or \
                            str(_q(k, "ReleaseType")).lower() in ("update", "hotfix", "security update"):
                        continue
                    us = str(_q(k, "UninstallString") or "")
                    if not us:
                        continue
                    ver = str(_q(k, "DisplayVersion") or "")
                    if (name.lower(), ver) in seen:
                        continue
                    seen.add((name.lower(), ver))
                    d = str(_q(k, "InstallDate") or "")
                    res.append({"id": f"{tag}|{sub}", "name": name, "pub": str(_q(k, "Publisher") or ""), "ver": ver,
                                "size": int(_q(k, "EstimatedSize", 0) or 0) * 1024,
                                "date": f"{d[6:8]}/{d[4:6]}/{d[:4]}" if re.fullmatch(r"\d{8}", d) else "",
                                "loc": str(_q(k, "InstallLocation") or "").strip('"'), "quiet": bool(_q(k, "QuietUninstallString"))})
            except OSError:
                pass
        winreg.CloseKey(root)
    res.sort(key=lambda x: x["name"].lower())
    return res


def _prog(pid):
    tag, sub = pid.split("|", 1)
    hive, key = {"HKLM": (winreg.HKEY_LOCAL_MACHINE, UNINST), "HKCU": (winreg.HKEY_CURRENT_USER, UNINST),
                 "HKLM32": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")}[tag]
    with winreg.OpenKey(hive, key + "\\" + sub) as k:
        return {"name": str(_q(k, "DisplayName")), "pub": str(_q(k, "Publisher") or ""), "us": str(_q(k, "UninstallString") or ""),
                "qus": str(_q(k, "QuietUninstallString") or ""), "loc": str(_q(k, "InstallLocation") or "").strip('"'),
                "hive": hive, "key": key + "\\" + sub, "tag": tag}


def uninstall_run(j, pid, quiet):
    """Chạy trình gỡ của chính phần mềm (chờ xong), rồi quét phần còn sót."""
    if fake():
        for i in range(10):
            time.sleep(0.25)
            j["pct"], j["text"] = i * 8, "Đang chạy trình gỡ của phần mềm..."
        p = next(x for x in FAKE_PROGRAMS if x["id"] == pid)
        j["pct"], j["text"] = 85, "Đang tìm phần còn sót..."
        return {"left": leftovers(p["name"], p["pub"], p["loc"], None)}
    p = _prog(pid)
    us = p["qus"] if quiet and p["qus"] else p["us"]
    m = re.search(r"msiexec(?:\.exe)?\s+/[IX]\s*(\{[0-9A-F-]{36}\})", us, re.I)
    if m:
        cmd = f'msiexec.exe /x {m.group(1)}' + (" /qn /norestart" if quiet else "")
    else:
        mm = re.match(r'^\s*([A-Za-z]:\\[^"]+?\.exe)(.*)$', us, re.I)   # đường dẫn có dấu cách mà không có ngoặc kép
        cmd = f'"{mm.group(1)}"{mm.group(2)}' if mm and not us.strip().startswith('"') else us
    j["pct"], j["text"] = 10, "Đang chạy trình gỡ của phần mềm (làm theo cửa sổ gỡ nếu có)..."
    subprocess.call(cmd, shell=True)
    time.sleep(2)
    j["pct"], j["text"] = 85, "Đang tìm phần còn sót..."
    return {"left": leftovers(p["name"], p["pub"], p["loc"], p)}


def leftovers_rescan(pid):
    if fake():
        p = next(x for x in FAKE_PROGRAMS if x["id"] == pid)
        return leftovers(p["name"], p["pub"], p["loc"], None)
    try:
        p = _prog(pid)
        return leftovers(p["name"], p["pub"], p["loc"], p)
    except OSError:
        return []


def _norm(s):
    """Bỏ phần phiên bản / kiến trúc: "UltraViewer version 6.6.95" -> "UltraViewer", "7-Zip 24.08 (x64)" -> "7-Zip"."""
    s = re.sub(r"\(.*?\)|\bversion\s*[\d.]+|\bv?\d+(\.\d+)+\b|\bx64\b|\bx86\b|\b64-bit\b|\b32-bit\b", " ", s or "", flags=re.I)
    return re.sub(r"\s+", " ", s).strip(" -_.,")


SAFE_ROOTS = None


def _safe_roots():
    global SAFE_ROOTS
    if SAFE_ROOTS is None:
        SAFE_ROOTS = [Path(env(v)) for v in ("ProgramFiles", "ProgramFiles(x86)", "ProgramData", "APPDATA", "LOCALAPPDATA") if env(v)]
        SAFE_ROOTS += [Path(env("LOCALAPPDATA")) / "Programs"]
    return SAFE_ROOTS


def _deletable(p):
    """Chỉ cho xóa thư mục nằm DƯỚI các thư mục phần mềm (không bao giờ là chính thư mục gốc, Windows, Users)."""
    try:
        p = Path(p).resolve()
    except OSError:
        return False
    for r in _safe_roots():
        try:
            rel = p.relative_to(r.resolve())
            if rel.parts:
                return True
        except (ValueError, OSError):
            continue
    return False


GENERIC = {"microsoft", "windows", "google", "intel", "nvidia", "amd", "realtek", "common files", "apple", "adobe", "packages",
           "programs", "temp", "microsoft corporation", "google llc", "mozilla", "oracle", "java", "hp", "dell", "lenovo", "asus"}


def leftovers(name, pub, loc, p):
    """Thư mục / khóa registry có tên KHỚP ĐÚNG tên phần mềm vừa gỡ (người dùng xem lại và tick chọn xóa).
    Không lấy tên chung (Microsoft, Google...) để tránh xóa nhầm phần mềm khác cùng hãng."""
    nm = _norm(name)
    names = {x.lower() for x in (name.strip(), nm) if x and len(x) >= 4 and x.lower() not in GENERIC}
    pb = _norm(pub).lower() if pub else ""
    if fake():
        return [{"kind": "dir", "path": loc or r"C:\Program Files\Demo", "size": 2.4e7, "why": "Thư mục cài đặt"},
                {"kind": "dir", "path": "C:\\Users\\Admin\\AppData\\Roaming\\%s" % nm, "size": 3.1e6, "why": "Dữ liệu ứng dụng"},
                {"kind": "reg", "path": "HKCU\\Software\\%s" % nm, "size": 0, "why": "Cài đặt trong registry"}]
    found, seen = [], set()

    def add(path, why):
        try:
            key = str(Path(path).resolve()).lower()
        except OSError:
            return
        if key not in seen and _deletable(path):
            seen.add(key)
            found.append({"kind": "dir", "path": str(path), "why": why})
    if loc and Path(loc).is_dir():
        add(loc, "Thư mục cài đặt")
    for r in _safe_roots():
        if not r.is_dir():
            continue
        try:
            kids = {c.name.lower(): c for c in r.iterdir() if c.is_dir()}
        except OSError:
            continue
        for n in names:
            if n in kids:
                add(kids[n], "Dữ liệu / thư mục còn sót")
        if pb and pb in kids:                 # dạng <Hãng>\<Tên phần mềm>
            try:
                sub = {c.name.lower(): c for c in kids[pb].iterdir() if c.is_dir()}
            except OSError:
                sub = {}
            for n in names:
                if n in sub:
                    add(sub[n], "Dữ liệu / thư mục còn sót")
    for x in found:
        x["size"] = walk_size(x["path"], cap=200000)[0]
    pubs = [x for x in {pub.strip(), _norm(pub)} if x and x.lower() not in GENERIC] if pub else []
    for hive, hn in ((winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")):
        for base in ("Software", r"Software\WOW6432Node"):
            subs = [f"{base}\\{pb_}\\{n}" for pb_ in pubs for n in (name.strip(), nm) if n] + [f"{base}\\{n}" for n in (name.strip(), nm) if n and n.lower() not in GENERIC]
            for sub in dict.fromkeys(subs):
                try:
                    winreg.CloseKey(winreg.OpenKey(hive, sub))
                    found.append({"kind": "reg", "path": f"{hn}\\{sub}", "size": 0, "why": "Cài đặt trong registry"})
                except OSError:
                    pass
    if p:
        try:
            winreg.CloseKey(winreg.OpenKey(p["hive"], p["key"]))
            found.append({"kind": "reg", "path": ("HKCU\\" if p["hive"] == winreg.HKEY_CURRENT_USER else "HKLM\\") + p["key"],
                          "size": 0, "why": "Mục gỡ cài đặt còn sót"})
        except OSError:
            pass
    return found


def _del_reg_tree(hive, sub):
    with winreg.OpenKey(hive, sub, 0, winreg.KEY_ALL_ACCESS) as k:
        while True:
            try:
                child = winreg.EnumKey(k, 0)
            except OSError:
                break
            _del_reg_tree(hive, sub + "\\" + child)
    winreg.DeleteKey(hive, sub)


def leftovers_delete(items):
    done, errs = 0, []
    for it in items:
        path = it.get("path", "")
        try:
            if fake():
                done += 1
                continue
            if it.get("kind") == "dir":
                if not _deletable(path):
                    errs.append(f"Bỏ qua (thư mục hệ thống): {path}")
                    continue
                shutil.rmtree(path, ignore_errors=True)
                if Path(path).exists():
                    errs.append(f"Còn file đang bị khóa: {path}")
                else:
                    done += 1
            elif it.get("kind") == "reg":
                hn, sub = path.split("\\", 1)
                if sub.count("\\") < 1 or not sub.lower().startswith("software\\"):
                    errs.append(f"Bỏ qua: {path}")
                    continue
                _del_reg_tree(winreg.HKEY_CURRENT_USER if hn == "HKCU" else winreg.HKEY_LOCAL_MACHINE, sub)
                done += 1
        except OSError as e:
            errs.append(f"{path}: {e}")
    return {"done": done, "errs": errs}


# ================================================================= ỨNG DỤNG MS STORE
FAKE_APPX = [{"name": "Microsoft.BingNews", "disp": "Microsoft News", "ver": "4.55.62231.0", "full": "Microsoft.BingNews_4.55_x64__8wekyb3d8bbwe", "pub": "Microsoft"},
             {"name": "Microsoft.GetHelp", "disp": "Get Help", "ver": "10.2409.22951.0", "full": "Microsoft.GetHelp_10.2409_x64__8wekyb3d8bbwe", "pub": "Microsoft"},
             {"name": "Microsoft.ZuneMusic", "disp": "Media Player", "ver": "11.2410.15.0", "full": "Microsoft.ZuneMusic_11.2410_x64__8wekyb3d8bbwe", "pub": "Microsoft"},
             {"name": "SpotifyAB.SpotifyMusic", "disp": "Spotify", "ver": "1.250.506.0", "full": "SpotifyAB.SpotifyMusic_1.250_x64__zpdnekdrzrea0", "pub": "Spotify AB"},
             {"name": "Clipchamp.Clipchamp", "disp": "Microsoft Clipchamp", "ver": "3.1.12050.0", "full": "Clipchamp.Clipchamp_3.1_x64__yxz26nhyzhsrt", "pub": "Microsoft"}]


def appx_list():
    if fake():
        return FAKE_APPX
    script = r"""
$ErrorActionPreference='SilentlyContinue'
$o=@(Get-AppxPackage | Where-Object { -not $_.IsFramework -and -not $_.NonRemovable -and $_.SignatureKind -ne 'System' } | ForEach-Object {
  $d=$_.Name; try { $m=(Get-AppxPackageManifest $_).Package.Properties; if($m.DisplayName -and $m.DisplayName -notlike 'ms-resource*'){ $d=$m.DisplayName } } catch {}
  $pn=''; if($_.Publisher -match 'CN=([^,]+)'){ $pn=$matches[1] }
  [ordered]@{ name=$_.Name; disp=[string]$d; ver=[string]$_.Version; full=$_.PackageFullName; pub=$pn } })
ConvertTo-Json -InputObject $o -Compress
"""
    code, out = H["ps"](script, timeout=180)
    try:
        return sorted(json.loads(out[out.index("["):]), key=lambda x: x["disp"].lower())
    except Exception:                       # noqa: BLE001
        return []


def appx_remove(j, fulls, all_users):
    ok, errs = 0, []
    for i, f in enumerate(fulls):
        if j.get("stop"):
            break
        j["pct"], j["text"] = int(i * 100 / max(1, len(fulls))), f"Đang gỡ {f.split('_')[0]}..."
        if not re.fullmatch(r"[\w.\-~]+", f):
            errs.append(f"Tên gói không hợp lệ: {f}")
            continue
        if fake():
            time.sleep(0.3)
            ok += 1
            continue
        code, out = H["ps"](f"Remove-AppxPackage -Package '{f}'" + (" -AllUsers" if all_users else ""), timeout=300)
        if code == 0:
            ok += 1
        else:
            errs.append(f"{f.split('_')[0]}: {out[:150]}")
    return {"done": ok, "errs": errs}


# ================================================================= DEFENDER / FIREWALL / SMARTSCREEN / UAC
FAKE_DEF = {"svc": "Running", "rt": True, "tamper": True, "cloud": 2, "sample": 1, "av": True, "sig": "1.463.368.0",
            "sigdate": "20/11/2026 03:05", "excl_path": [r"D:\Tools"], "excl_proc": [], "excl_ext": [".iso"],
            "fw": [{"n": "Domain", "on": True}, {"n": "Private", "on": True}, {"n": "Public", "on": True}],
            "smart": "Warn", "uac": 5, "lua": 1}


def defender_status():
    if fake():
        return dict(FAKE_DEF)
    script = r"""
$ErrorActionPreference='SilentlyContinue'
$s=Get-MpComputerStatus; $p=Get-MpPreference
$ss=(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer').SmartScreenEnabled
$u=Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
[ordered]@{ svc=[string](Get-Service WinDefend).Status; rt=[bool]$s.RealTimeProtectionEnabled; tamper=[bool]$s.IsTamperProtected;
 cloud=[int]$p.MAPSReporting; sample=[int]$p.SubmitSamplesConsent; av=[bool]$s.AntivirusEnabled; sig=[string]$s.AntivirusSignatureVersion;
 sigdate=$(if($s.AntivirusSignatureLastUpdated){$s.AntivirusSignatureLastUpdated.ToString('dd/MM/yyyy HH:mm')}else{''});
 excl_path=@($p.ExclusionPath | Where-Object { $_ -and $_ -notlike 'N/A*' }); excl_proc=@($p.ExclusionProcess | Where-Object { $_ -and $_ -notlike 'N/A*' });
 excl_ext=@($p.ExclusionExtension | Where-Object { $_ -and $_ -notlike 'N/A*' });
 fw=@(Get-NetFirewallProfile | ForEach-Object { @{ n=[string]$_.Name; on=[bool]($_.Enabled -eq 'True' -or $_.Enabled -eq 1) } });
 smart=$(if($ss){[string]$ss}else{'Mặc định'}); uac=[int]$u.ConsentPromptBehaviorAdmin; lua=[int]$u.EnableLUA } | ConvertTo-Json -Depth 4 -Compress
"""
    code, out = H["ps"](script, timeout=90)
    try:
        return json.loads(out[out.index("{"):])
    except Exception:                       # noqa: BLE001
        return {"err": out[:300] or f"mã {code}"}


def defender_set(what, on):
    """Bật / tắt từng phần bằng lệnh chính thức. Trả '' nếu được, ngược lại câu báo."""
    on = bool(on)
    cmd = {
        "rt": f"Set-MpPreference -DisableRealtimeMonitoring ${str(not on).lower()}",
        "cloud": f"Set-MpPreference -MAPSReporting {2 if on else 0}",
        "sample": f"Set-MpPreference -SubmitSamplesConsent {1 if on else 2}",
        "fw": f"Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled {'True' if on else 'False'}",
        "smart": "Set-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer' SmartScreenEnabled "
                 + ("'Warn'" if on else "'Off'"),
        "uac": "Set-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' ConsentPromptBehaviorAdmin "
               + ("5" if on else "0"),
    }.get(what)
    if not cmd:
        return "Không có mục này"
    if fake():
        key = {"rt": "rt", "fw": None}.get(what, what)
        if what == "fw":
            for f in FAKE_DEF["fw"]:
                f["on"] = on
        elif what == "cloud":
            FAKE_DEF["cloud"] = 2 if on else 0
        elif what == "sample":
            FAKE_DEF["sample"] = 1 if on else 2
        elif what == "smart":
            FAKE_DEF["smart"] = "Warn" if on else "Off"
        elif what == "uac":
            FAKE_DEF["uac"] = 5 if on else 0
        elif key:
            if FAKE_DEF["tamper"] and what == "rt":
                return "Windows không cho đổi vì Tamper Protection đang bật. Bấm \"Mở Windows Security\", tắt Tamper Protection rồi thử lại."
            FAKE_DEF[key] = on
        return ""
    code, out = H["ps"](cmd, timeout=90)
    if code != 0:
        return "Lỗi: " + re.split(r"\r?\nAt line", out or "")[0][:300]
    if what in ("rt", "cloud", "sample"):
        st = defender_status()
        real = {"rt": st.get("rt") == on, "cloud": (st.get("cloud", 0) > 0) == on, "sample": (st.get("sample") in (1, 3)) == on}[what]
        if not real:
            return ("Windows không cho đổi vì Tamper Protection đang bật. Bấm \"Mở Windows Security\", tắt Tamper Protection rồi thử lại."
                    if st.get("tamper") else "Lệnh đã chạy nhưng trạng thái không đổi (có thể bị chính sách công ty quản lý).")
    return ""


def defender_excl(action, kind, value):
    value = (value or "").strip()
    if not value or kind not in ("path", "proc", "ext"):
        return "Thiếu giá trị"
    param = {"path": "ExclusionPath", "proc": "ExclusionProcess", "ext": "ExclusionExtension"}[kind]
    if fake():
        lst = FAKE_DEF["excl_" + kind]
        if action == "add" and value not in lst:
            lst.append(value)
        if action == "remove" and value in lst:
            lst.remove(value)
        return ""
    v = value.replace("'", "''")
    code, out = H["ps"](f"{'Add' if action == 'add' else 'Remove'}-MpPreference -{param} '{v}'", timeout=60)
    return "" if code == 0 else "Lỗi: " + re.split(r"\r?\nAt line", out or "")[0][:300]


# ================================================================= DỌN DẸP
def _clean_targets():
    L, R, W = Path(env("LOCALAPPDATA")), Path(env("APPDATA")), Path(env("WINDIR", r"C:\Windows"))
    chromium = {"Chrome": L / r"Google\Chrome\User Data", "Edge": L / r"Microsoft\Edge\User Data",
                "Cốc Cốc": L / r"CocCoc\Browser\User Data", "Brave": L / r"BraveSoftware\Brave-Browser\User Data"}
    browser = []
    for b, ud in chromium.items():
        if ud.exists():
            for prof in [p for p in ud.iterdir() if p.is_dir() and (p.name == "Default" or p.name.startswith("Profile"))]:
                browser += [prof / "Cache", prof / "Code Cache", prof / "GPUCache", prof / r"Service Worker\CacheStorage"]
            browser += [ud / "ShaderCache", ud / "GrShaderCache"]
    ff = L / r"Mozilla\Firefox\Profiles"
    if ff.exists():
        browser += [p / "cache2" for p in ff.iterdir() if p.is_dir()]
    return [
        ("temp", "🗂️", "File tạm của người dùng", "%TEMP%", [Path(env("TEMP"))], True),
        ("wintemp", "🪟", "File tạm của Windows", r"C:\Windows\Temp", [W / "Temp"], True),
        ("wu", "🔄", "Bộ cài Windows Update đã tải", "SoftwareDistribution\\Download", [W / r"SoftwareDistribution\Download"], True),
        ("do", "📡", "Delivery Optimization", "Cache chia sẻ bản cập nhật", [W / r"ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization\Cache"], True),
        ("dump", "💥", "Báo lỗi & file dump", "Minidump, WER, CrashDumps", [W / "Minidump", L / "CrashDumps", Path(env("ProgramData", r"C:\ProgramData")) / r"Microsoft\Windows\WER\ReportArchive",
                                                                          Path(env("ProgramData", r"C:\ProgramData")) / r"Microsoft\Windows\WER\ReportQueue"], True),
        ("thumb", "🖼️", "Cache ảnh thu nhỏ", "thumbcache (Explorer tự tạo lại)", [L / r"Microsoft\Windows\Explorer"], False),
        ("browser", "🌐", "Cache trình duyệt", "Chrome, Edge, Cốc Cốc, Brave, Firefox (không xóa mật khẩu, lịch sử)", browser, False),
        ("recycle", "♻️", "Thùng rác", "Tất cả ổ đĩa", [], True),
    ]


FAKE_CLEAN = {"temp": 1.82e9, "wintemp": 3.4e8, "wu": 2.9e9, "do": 7.7e8, "dump": 1.2e8, "thumb": 2.1e8, "browser": 1.35e9, "recycle": 4.6e9}


def clean_scan(j):
    res = []
    T = _clean_targets()
    for i, (cid, ic, name, sub, paths, default) in enumerate(T):
        j["pct"], j["text"] = int(i * 100 / len(T)), f"Đang đo: {name}"
        if fake():
            time.sleep(0.15)
            size, n = FAKE_CLEAN[cid], 1200
        elif cid == "recycle":
            size = n = 0
            for d in "CDEFGH":
                rb = Path(f"{d}:\\$Recycle.Bin")
                if rb.exists():
                    s, c = walk_size(rb, j)
                    size, n = size + s, n + c
        elif cid == "thumb":
            size = n = 0
            for p in paths:
                for f in p.glob("thumbcache_*.db") if p.exists() else []:
                    try:
                        size, n = size + f.stat().st_size, n + 1
                    except OSError:
                        pass
        else:
            size = n = 0
            for p in paths:
                if p.exists():
                    s, c = walk_size(p, j)
                    size, n = size + s, n + c
        res.append({"id": cid, "ic": ic, "name": name, "sub": sub, "size": size, "files": n, "def": default})
    return res


def _rm_contents(p, j):
    freed = 0
    for root, dirs, files in os.walk(p, topdown=False):
        for f in files:
            fp = os.path.join(root, f)
            try:
                s = os.path.getsize(fp)
                os.remove(fp)
                freed += s
            except OSError:
                pass
        for d in dirs:
            try:
                os.rmdir(os.path.join(root, d))
            except OSError:
                pass
        if j.get("stop"):
            break
    return freed


def clean_run(j, ids):
    T = {t[0]: t for t in _clean_targets()}
    freed = 0
    for i, cid in enumerate(ids):
        if cid not in T or j.get("stop"):
            continue
        _, ic, name, sub, paths, _ = T[cid]
        j["pct"], j["text"] = int(i * 100 / max(1, len(ids))), f"Đang dọn: {name}"
        if fake():
            time.sleep(0.4)
            freed += FAKE_CLEAN[cid] * 0.93
            continue
        if cid == "recycle":
            H["ps"]("Clear-RecycleBin -Force -ErrorAction SilentlyContinue", timeout=300)
            continue
        if cid == "wu":
            H["run"](["net", "stop", "wuauserv"], timeout=120)
        if cid == "thumb":
            for p in paths:
                for f in p.glob("thumbcache_*.db") if p.exists() else []:
                    try:
                        s = f.stat().st_size
                        f.unlink()
                        freed += s
                    except OSError:
                        pass
            continue
        for p in paths:
            if p.exists():
                freed += _rm_contents(p, j)
        if cid == "wu":
            H["run"](["net", "start", "wuauserv"], timeout=120)
    return {"freed": freed, "text": f"Đã dọn được {human(freed)} (file đang được dùng sẽ bỏ qua)"}


def folder_sizes(j, path):
    """Phân tích ổ / thư mục: dung lượng từng thư mục con, xếp từ lớn tới nhỏ."""
    path = str(absp(path)) if path and not re.fullmatch(r"[A-Za-z]:\\?", path.strip()) else (path or "C:\\")
    if fake():
        demo = [("Users", 1.84e11), ("Windows", 3.2e10), ("Program Files", 2.4e10), ("Program Files (x86)", 1.1e10),
                ("ProgramData", 6.1e9), ("hiberfil.sys", 1.27e10), ("pagefile.sys", 8.0e9), ("$Recycle.Bin", 4.6e9)]
        time.sleep(1)
        return {"path": path, "items": [{"name": n, "size": s, "dir": not n.endswith(".sys"), "path": path.rstrip("\\") + "\\" + n} for n, s in demo],
                "total": sum(s for _, s in demo)}
    root = Path(path)
    entries = []
    try:
        entries = list(os.scandir(root))
    except OSError as e:
        raise RuntimeError(f"Không mở được {path}: {e}")
    items = []
    for i, e in enumerate(entries):
        if j.get("stop"):
            break
        j["pct"], j["text"] = int(i * 100 / max(1, len(entries))), f"Đang đo {e.name}"
        try:
            if e.is_dir(follow_symlinks=False):
                if IS_WIN and e.stat(follow_symlinks=False).st_file_attributes & 0x400:
                    continue
                s, _ = walk_size(e.path, j)
                items.append({"name": e.name, "size": s, "dir": True, "path": e.path})
            else:
                items.append({"name": e.name, "size": e.stat(follow_symlinks=False).st_size, "dir": False, "path": e.path})
        except OSError:
            pass
    items.sort(key=lambda x: -x["size"])
    return {"path": str(root), "items": items[:60], "total": sum(x["size"] for x in items)}


def capcut_info():
    L = Path(env("LOCALAPPDATA"))
    paths = [L / r"CapCut\User Data\Cache", L / r"CapCut\User Data\CEF\Cache", L / r"JianyingPro\User Data\Cache"]
    if fake():
        return {"found": True, "size": 8.4e9, "paths": [str(paths[0])], "running": False}
    found = [p for p in paths if p.exists()]
    return {"found": bool(found) or (L / "CapCut").exists(), "size": sum(walk_size(p)[0] for p in found), "paths": [str(p) for p in found],
            "running": bool(proc_running(["CapCut.exe"]))}


def capcut_clean(j):
    info = capcut_info()
    if info["running"]:
        kill(["CapCut.exe"])
    freed = 0
    for p in info["paths"]:
        j["text"] = f"Đang xóa {p}"
        if fake():
            time.sleep(0.8)
            freed = info["size"]
        else:
            freed += _rm_contents(Path(p), j)
    return {"freed": freed, "text": f"Đã xóa {human(freed)} cache CapCut (dự án của bạn giữ nguyên)"}


# ---- macro Excel
def xlstart_scan():
    dirs = [Path(env("APPDATA")) / r"Microsoft\Excel\XLSTART"]
    for pf in (env("ProgramFiles"), env("ProgramFiles(x86)")):
        if pf:
            dirs += [Path(pf) / r"Microsoft Office\root\Office16\XLSTART", Path(pf) / r"Microsoft Office\Office16\XLSTART"]
    alt = ""
    vba = None
    if IS_WIN and not fake():
        for ver in ("16.0", "15.0"):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Microsoft\Office\{ver}\Excel\Options") as k:
                    alt = alt or str(_q(k, "AltStartup") or "")
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Microsoft\Office\{ver}\Excel\Security") as k:
                    vba = vba if vba is not None else _q(k, "VBAWarnings", None)
            except OSError:
                pass
    if alt:
        dirs.append(Path(alt))
    if fake():
        return {"files": [{"path": r"C:\Users\Admin\AppData\Roaming\Microsoft\Excel\XLSTART\PERSONAL.XLSB", "size": 18432, "date": "02/03/2025", "note": "Sổ macro cá nhân (thường là của bạn)"},
                          {"path": r"C:\Users\Admin\AppData\Roaming\Microsoft\Excel\XLSTART\Book1.xls", "size": 86016, "date": "18/11/2026", "note": "File lạ tự mở cùng Excel - nghi virus macro"}],
                "vba": 1, "dirs": [str(d) for d in dirs[:1]]}
    files = []
    for d in dirs:
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    st = f.stat()
                    note = "Sổ macro cá nhân (thường là của bạn)" if f.name.upper() == "PERSONAL.XLSB" else (
                        "File lạ tự mở cùng Excel - nghi virus macro" if f.suffix.lower() in (".xls", ".xlsm", ".xlsb", ".xla", ".xlam", ".xlt", ".xltm")
                        else "File tự mở cùng Excel")
                    files.append({"path": str(f), "size": st.st_size, "date": dt.datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y"), "note": note})
    return {"files": files, "vba": vba, "dirs": [str(d) for d in dirs if d.exists()]}


def xlstart_quarantine(paths):
    dst = data_dir("Backup", "MacroExcel_CachLy_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    ok = 0
    for p in paths:
        if fake():
            ok += 1
            continue
        if "xlstart" not in p.lower() and not p.lower().endswith((".xls", ".xlsm", ".xlsb", ".xla", ".xlam", ".xlt", ".xltm")):
            continue
        try:
            shutil.move(p, str(dst / Path(p).name))
            ok += 1
        except OSError:
            pass
    return {"done": ok, "dir": str(dst)}


def excel_safe_macro():
    """Đặt Excel về mặc định an toàn: tắt macro, có thông báo (VBAWarnings = 2)."""
    if fake():
        return ""
    for ver in ("16.0", "15.0"):
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, rf"Software\Microsoft\Office\{ver}\Excel\Security", 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "VBAWarnings", 0, winreg.REG_DWORD, 2)
        except OSError:
            pass
    return ""


# ---- metadata ảnh
def _strip_jpeg(b):
    if b[:2] != b"\xff\xd8":
        raise ValueError("không phải JPEG")
    out, i = bytearray(b[:2]), 2
    while i < len(b):
        if b[i] != 0xFF:
            raise ValueError("JPEG lỗi")
        m = b[i + 1]
        if m == 0xDA:                        # bắt đầu dữ liệu ảnh: chép phần còn lại
            out += b[i:]
            break
        if m in (0xD8,) or 0xD0 <= m <= 0xD7:
            out += b[i:i + 2]
            i += 2
            continue
        ln = struct.unpack(">H", b[i + 2:i + 4])[0]
        seg = b[i:i + 2 + ln]
        if m == 0xE1 or m == 0xED or m == 0xFE:   # APP1 (EXIF / XMP: GPS, máy chụp, giờ chụp), APP13 (IPTC), ghi chú
            pass
        else:
            out += seg
        i += 2 + ln
    return bytes(out)


def _strip_png(b):
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("không phải PNG")
    out, i = bytearray(b[:8]), 8
    while i < len(b):
        ln = struct.unpack(">I", b[i:i + 4])[0]
        typ = b[i + 4:i + 8]
        chunk = b[i:i + 12 + ln]
        if typ not in (b"tEXt", b"iTXt", b"zTXt", b"eXIf", b"tIME"):
            out += chunk
        i += 12 + ln
        if typ == b"IEND":
            break
    return bytes(out)


def metadata_strip(j, folder, recursive):
    folder = absp(folder)
    if fake():
        time.sleep(1)
        return {"done": 24, "skip": 3, "out": str(folder / "Da_xoa_metadata"), "text": "Đã xóa metadata 24 ảnh"}
    if not folder.is_dir():
        raise RuntimeError("Không thấy thư mục")
    out = folder / "Da_xoa_metadata"
    files = [p for p in (folder.rglob("*") if recursive else folder.iterdir())
             if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png") and out not in p.parents]
    done = skip = 0
    for i, f in enumerate(files):
        if j.get("stop"):
            break
        j["pct"], j["text"] = int(i * 100 / max(1, len(files))), f"{i + 1}/{len(files)} · {f.name}"
        try:
            b = f.read_bytes()
            nb = _strip_jpeg(b) if f.suffix.lower() in (".jpg", ".jpeg") else _strip_png(b)
            t = out / f.relative_to(folder)
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_bytes(nb)
            done += 1
        except Exception:                   # noqa: BLE001
            skip += 1
    return {"done": done, "skip": skip, "out": str(out),
            "text": f"Đã xóa metadata {done} ảnh" + (f", bỏ qua {skip} file lỗi" if skip else "") + f". Ảnh sạch nằm trong {out}"}


# ================================================================= SAO LƯU
USER_DIRS = [("Desktop", "🖥️", "Desktop", "Desktop"), ("Documents", "📄", "Tài liệu", "Personal"), ("Downloads", "⬇️", "Tải về", "{374DE290-123F-4565-9164-39C4925E467B}"),
             ("Pictures", "🖼️", "Ảnh", "My Pictures"), ("Videos", "🎬", "Video", "My Video"), ("Music", "🎵", "Nhạc", "My Music")]


def user_dir(regname, fallback):
    if IS_WIN and not fake():
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
                return Path(os.path.expandvars(winreg.QueryValueEx(k, regname)[0]))
        except OSError:
            pass
    return Path(env("USERPROFILE", str(Path.home()))) / fallback


def backup_info():
    res = []
    for key, ic, vn, reg in USER_DIRS:
        p = user_dir(reg, key)
        size = {"Desktop": 2.1e9, "Documents": 1.4e10, "Downloads": 3.3e10, "Pictures": 8.8e9, "Videos": 2.6e10, "Music": 1.1e9}[key] if fake() else \
            (walk_size(p, cap=400000)[0] if p.exists() else 0)
        res.append({"key": key, "ic": ic, "name": vn, "path": str(p), "size": size, "exists": fake() or p.exists()})
    drives = []
    if IS_WIN and not fake():
        for d in "DEFGHIJKLMNOPQRSTUVWXYZ":
            if os.path.exists(f"{d}:\\"):
                try:
                    tot, used, free = shutil.disk_usage(f"{d}:\\")
                    drives.append({"d": d, "free": free, "total": tot})
                except OSError:
                    pass
    elif fake():
        drives = [{"d": "D", "free": 8.0e11, "total": 1.0e12}, {"d": "E", "free": 2.1e12, "total": 4.0e12}]
    return {"dirs": res, "drives": drives, "pc": os.environ.get("COMPUTERNAME", "PC")}


def backup_user(j, keys, dest):
    dest = absp(dest) / f"SaoLuu_{os.environ.get('COMPUTERNAME', 'PC')}_{dt.datetime.now():%Y%m%d_%H%M}"
    if fake():
        for i in range(21):
            time.sleep(0.08)
            j["pct"], j["text"] = i * 5, f"{human(i * 1.2e9)} / {human(2.4e10)}"
        return {"dest": str(dest), "text": f"Đã sao lưu vào {dest}"}
    items = [(k, user_dir(reg, k)) for k, _, _, reg in USER_DIRS if k in keys]
    n = max(1, len(items))
    errs = 0
    for i, (k, src) in enumerate(items):
        if src.exists():
            j["text"] = f"Đang chép {k}..."
            _, _, e = copy_tree(src, dest / k, j, skip_dirs=("desktop.ini",), base_pct=int(i * 100 / n), span=int(100 / n))
            errs += e
    (dest / "WinAIO_saoluu.json").write_text(json.dumps({"pc": os.environ.get("COMPUTERNAME"), "time": dt.datetime.now().isoformat(),
                                                         "dirs": [k for k, _ in items]}, ensure_ascii=False), encoding="utf-8")
    return {"dest": str(dest), "text": f"Đã sao lưu vào {dest}" + (f" ({errs} file không chép được - đang mở hoặc không có quyền)" if errs else "")}


def restore_user(j, src):
    src = absp(src)
    if fake():
        time.sleep(1)
        return {"text": "Đã khôi phục (file trùng tên giữ nguyên bản đang có)"}
    keys = [k for k, *_ in USER_DIRS if (src / k).is_dir()]
    if not keys:
        raise RuntimeError("Thư mục này không phải bản sao lưu của Win AIO (không có Desktop / Documents...)")
    n = len(keys)
    for i, k in enumerate(keys):
        reg = next(r for kk, _, _, r in USER_DIRS if kk == k)
        copy_tree(src / k, user_dir(reg, k), j, base_pct=int(i * 100 / n), span=int(100 / n))
    return {"text": f"Đã khôi phục {', '.join(keys)} (file trùng tên giữ nguyên bản đang có)"}


# ---- Zalo
def zalo_paths():
    R, L = Path(env("APPDATA")), Path(env("LOCALAPPDATA"))
    docs = user_dir("Personal", "Documents")
    return {"data": R / "ZaloPC", "local": L / "ZaloPC", "files": docs / "Zalo Received Files", "exe": L / r"Programs\Zalo\Zalo.exe"}


def zalo_info():
    z = zalo_paths()
    if fake():
        return {"installed": True, "running": True, "data": 5.6e9, "files": 2.2e9, "profiles": zalo_profiles()}
    return {"installed": z["exe"].exists() or z["data"].exists(), "running": bool(proc_running(["Zalo.exe"])),
            "data": walk_size(z["data"], cap=300000)[0] if z["data"].exists() else 0,
            "files": walk_size(z["files"], cap=300000)[0] if z["files"].exists() else 0, "profiles": zalo_profiles()}


def zalo_backup(j, dest, close):
    z = zalo_paths()
    if close:
        kill(["Zalo.exe"])
    elif proc_running(["Zalo.exe"]):
        raise RuntimeError("Zalo đang mở. Hãy tắt Zalo (hoặc tick \"Tự tắt Zalo\") rồi sao lưu lại.")
    out = absp(dest) / f"Zalo_{os.environ.get('COMPUTERNAME', 'PC')}_{dt.datetime.now():%Y%m%d_%H%M}"
    if fake():
        for i in range(21):
            time.sleep(0.06)
            j["pct"] = i * 5
        return {"dest": str(out), "text": f"Đã sao lưu Zalo vào {out}"}
    parts = [(k, z[k]) for k in ("data", "local", "files") if z[k].exists()]
    for i, (k, p) in enumerate(parts):
        copy_tree(p, out / {"data": "ZaloPC_Roaming", "local": "ZaloPC_Local", "files": "Zalo Received Files"}[k], j,
                  skip_dirs=("Cache", "Code Cache", "GPUCache"), base_pct=int(i * 100 / len(parts)), span=int(100 / len(parts)))
    return {"dest": str(out), "text": f"Đã sao lưu Zalo (tin nhắn + file) vào {out}"}


def zalo_restore(j, src, close):
    z, src = zalo_paths(), absp(src)
    if not (src / "ZaloPC_Roaming").is_dir():
        raise RuntimeError("Thư mục này không phải bản sao lưu Zalo của Win AIO")
    if close or proc_running(["Zalo.exe"]):
        kill(["Zalo.exe"])
    if fake():
        time.sleep(1)
        return {"text": "Đã khôi phục Zalo"}
    if z["data"].exists():
        shutil.move(str(z["data"]), str(z["data"]) + f".truoc_khoi_phuc_{dt.datetime.now():%Y%m%d_%H%M}")
    copy_tree(src / "ZaloPC_Roaming", z["data"], j, base_pct=0, span=60)
    if (src / "ZaloPC_Local").is_dir():
        copy_tree(src / "ZaloPC_Local", z["local"], j, base_pct=60, span=15)
    if (src / "Zalo Received Files").is_dir():
        copy_tree(src / "Zalo Received Files", z["files"], j, base_pct=75, span=25)
    return {"text": "Đã khôi phục Zalo. Dữ liệu cũ trên máy được đổi tên thành ZaloPC.truoc_khoi_phuc_..."}


def zalo_profiles():
    if fake():
        return [{"name": "Shop", "size": 1.2e9}, {"name": "Ca nhan 2", "size": 3.4e8}]
    base = Path(H["data"]) / "ZaloTaiKhoan"
    if not base.exists():
        return []
    return [{"name": p.name, "size": walk_size(p, cap=100000)[0]} for p in sorted(base.iterdir()) if p.is_dir()]


def zalo_open(name):
    """Mở thêm 1 Zalo dùng thư mục dữ liệu riêng (đăng nhập tài khoản khác, không ảnh hưởng Zalo chính)."""
    name = re.sub(r'[\\/:*?"<>|]', "_", (name or "").strip())[:40]
    if not name:
        return "Chưa nhập tên tài khoản"
    z = zalo_paths()
    if fake():
        return ""
    if not z["exe"].exists():
        return "Không thấy Zalo.exe trên máy (cài Zalo PC trước)"
    prof = data_dir("ZaloTaiKhoan", name)
    (prof / "Roaming").mkdir(exist_ok=True)
    e = dict(os.environ)
    e["APPDATA"] = str(prof / "Roaming")
    subprocess.Popen([str(z["exe"])], env=e, cwd=str(z["exe"].parent))
    return ""


def zalo_profile_delete(name):
    if fake():
        return ""
    p = Path(H["data"]) / "ZaloTaiKhoan" / name
    if p.is_dir() and p.parent.name == "ZaloTaiKhoan":
        shutil.rmtree(p, ignore_errors=True)
    return ""


# ---- trình duyệt
BROWSERS = [("chrome", "Google Chrome", "chrome.exe", r"Google\Chrome\User Data"), ("edge", "Microsoft Edge", "msedge.exe", r"Microsoft\Edge\User Data"),
            ("coccoc", "Cốc Cốc", "browser.exe", r"CocCoc\Browser\User Data"), ("brave", "Brave", "brave.exe", r"BraveSoftware\Brave-Browser\User Data")]
BROWSER_SKIP = ("Cache", "Code Cache", "GPUCache", "ShaderCache", "GrShaderCache", "DawnCache", "DawnGraphiteCache", "DawnWebGPUCache",
                "component_crx_cache", "Crashpad", "CacheStorage", "optimization_guide_model_store", "Safe Browsing", "SwReporter")


def browsers_info():
    res = []
    for bid, name, exe, rel in BROWSERS:
        p = Path(env("LOCALAPPDATA")) / rel
        if fake():
            res.append({"id": bid, "name": name, "found": bid != "brave", "running": bid == "chrome", "profiles": 2 if bid == "chrome" else 1, "path": str(p)})
            continue
        if p.exists():
            profs = [x for x in p.iterdir() if x.is_dir() and (x.name == "Default" or x.name.startswith("Profile"))]
            res.append({"id": bid, "name": name, "found": True, "running": bool(proc_running([exe])), "profiles": len(profs), "path": str(p)})
        else:
            res.append({"id": bid, "name": name, "found": False, "running": False, "profiles": 0, "path": str(p)})
    ff = Path(env("APPDATA")) / r"Mozilla\Firefox"
    res.append({"id": "firefox", "name": "Firefox", "found": fake() or ff.exists(), "running": False if fake() else bool(proc_running(["firefox.exe"])),
                "profiles": 1, "path": str(ff)})
    return res


def browser_backup(j, ids, dest, close):
    dest = absp(dest) / f"TrinhDuyet_{os.environ.get('COMPUTERNAME', 'PC')}_{dt.datetime.now():%Y%m%d_%H%M}"
    info = {b["id"]: b for b in browsers_info()}
    exes = {bid: exe for bid, _, exe, _ in BROWSERS}
    exes["firefox"] = "firefox.exe"
    sel = [i for i in ids if info.get(i, {}).get("found")]
    running = [i for i in sel if info[i]["running"]]
    if running and not close:
        raise RuntimeError("Đang mở: " + ", ".join(info[i]["name"] for i in running) + ". Tắt trình duyệt (hoặc tick \"Tự tắt trình duyệt\") rồi thử lại.")
    if running:
        kill([exes[i] for i in running])
    if fake():
        for i in range(21):
            time.sleep(0.06)
            j["pct"] = i * 5
        return {"dest": str(dest), "text": f"Đã sao lưu {len(sel)} trình duyệt vào {dest}"}
    n = max(1, len(sel))
    for i, bid in enumerate(sel):
        j["text"] = f"Đang chép {info[bid]['name']}..."
        copy_tree(info[bid]["path"], dest / bid, j, skip_dirs=BROWSER_SKIP, base_pct=int(i * 100 / n), span=int(100 / n))
    (dest / "WinAIO_trinhduyet.json").write_text(json.dumps({"browsers": sel, "pc": os.environ.get("COMPUTERNAME"),
                                                              "user": os.environ.get("USERNAME")}, ensure_ascii=False), encoding="utf-8")
    return {"dest": str(dest), "text": f"Đã sao lưu {len(sel)} trình duyệt (dấu trang, tiện ích, mật khẩu, lịch sử) vào {dest}"}


def browser_restore(j, src, close):
    src = absp(src)
    try:
        meta = json.loads((src / "WinAIO_trinhduyet.json").read_text(encoding="utf-8"))
    except Exception:                       # noqa: BLE001
        raise RuntimeError("Thư mục này không phải bản sao lưu trình duyệt của Win AIO")
    info = {b["id"]: b for b in browsers_info()}
    exes = {bid: exe for bid, _, exe, _ in BROWSERS}
    exes["firefox"] = "firefox.exe"
    sel = [b for b in meta.get("browsers", []) if (src / b).is_dir()]
    kill([exes[b] for b in sel if info.get(b, {}).get("running")] if close else [])
    if any(info.get(b, {}).get("running") for b in sel) and not close and not fake():
        raise RuntimeError("Hãy tắt trình duyệt (hoặc tick \"Tự tắt trình duyệt\") rồi thử lại.")
    if fake():
        time.sleep(1)
        return {"text": "Đã khôi phục trình duyệt"}
    for i, b in enumerate(sel):
        dst = Path(info[b]["path"])
        if dst.exists():
            shutil.move(str(dst), str(dst) + f".truoc_khoi_phuc_{dt.datetime.now():%Y%m%d_%H%M}")
        copy_tree(src / b, dst, j, base_pct=int(i * 100 / len(sel)), span=int(100 / len(sel)))
    note = "" if meta.get("user") == os.environ.get("USERNAME") else " Mật khẩu đã lưu chỉ dùng được khi khôi phục trên cùng tài khoản Windows đã sao lưu."
    return {"text": f"Đã khôi phục {len(sel)} trình duyệt. Dữ liệu cũ được đổi tên thành ...truoc_khoi_phuc_....{note}"}
