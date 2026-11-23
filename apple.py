"""Win AIO by Duy Anh - v2.7: Kho bộ cài Mac (giống trình tải của macUSB: lấy thẳng từ máy chủ Apple)
và Kho iOS (danh sách firmware IPSW theo api.ipsw.me, file tải từ máy chủ Apple).
Tải có %, tốc độ, tải tiếp khi bị ngắt; hoặc chỉ lấy link để dán vào IDM."""
import gzip
import plistlib
import re
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from mgr import absp, data_dir, fake, human

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
CATALOG = ("https://swscan.apple.com/content/catalogs/others/index-26-15-14-13-12-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9"
           "-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog.gz")
SUPPORT = "https://support.apple.com/en-us/102662"           # trang Apple: link tải macOS đời cũ (.dmg)
LEGACY = [("Sierra 10.12", "macOS Sierra", "10.12.6"), ("El Capitan 10.11", "OS X El Capitan", "10.11.6"),
          ("Yosemite 10.10", "OS X Yosemite", "10.10.5"), ("Mountain Lion 10.8", "OS X Mountain Lion", "10.8.5"),
          ("Lion 10.7", "Mac OS X Lion", "10.7.5")]
LEGACY_PKGS = ("installassistantauto.pkg", "recoveryhdmetadmg.pkg", "installesddmg.pkg")      # 10.13 - 10.15
APPLE_HOSTS = ("apple.com", "cdn-apple.com")
IPSW_API = "https://api.ipsw.me/v4"
_CACHE = {}
_LOCK = threading.Lock()


def _get(url, timeout=30):
    import requests
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r


def _apple(url):
    h = (urlparse(url).hostname or "").lower()
    return any(h == d or h.endswith("." + d) for d in APPLE_HOSTS)


def _cached(key, ttl, fn):
    with _LOCK:
        v = _CACHE.get(key)
        if v and time.time() - v[0] < ttl:
            return v[1]
    data = fn()
    with _LOCK:
        _CACHE[key] = (time.time(), data)
    return data


# ================================================================ KHO BỘ CÀI MAC
FAKE_MAC = [
    {"id": "093-22004", "name": "macOS Tahoe 26", "family": "macOS Tahoe", "version": "26.1", "build": "25B78", "kind": "pkg", "size": 17_100_000_000,
     "date": "2026-11-03", "files": [{"name": "InstallAssistant.pkg", "url": "https://swcdn.apple.com/content/downloads/x/InstallAssistant.pkg", "size": 17_100_000_000}]},
    {"id": "082-08674", "name": "macOS Sequoia", "family": "macOS Sequoia", "version": "15.7.2", "build": "24G325", "kind": "pkg", "size": 15_200_000_000,
     "date": "2026-11-03", "files": [{"name": "InstallAssistant.pkg", "url": "https://swcdn.apple.com/content/downloads/y/InstallAssistant.pkg", "size": 15_200_000_000}]},
    {"id": "072-01382", "name": "macOS Sonoma", "family": "macOS Sonoma", "version": "14.8.2", "build": "23J126", "kind": "pkg", "size": 13_300_000_000,
     "date": "2026-11-03", "files": [{"name": "InstallAssistant.pkg", "url": "https://swcdn.apple.com/content/downloads/z/InstallAssistant.pkg", "size": 13_300_000_000}]},
    {"id": "001-68446", "name": "macOS Big Sur", "family": "macOS Big Sur", "version": "11.7.10", "build": "20G1427", "kind": "pkg", "size": 12_400_000_000,
     "date": "2023-09-11", "files": [{"name": "InstallAssistant.pkg", "url": "https://swcdn.apple.com/content/downloads/w/InstallAssistant.pkg", "size": 12_400_000_000}]},
    {"id": "061-86291", "name": "macOS Catalina", "family": "macOS Catalina", "version": "10.15.7", "build": "19H15", "kind": "multi", "size": 8_250_000_000,
     "date": "2020-11-05", "files": [{"name": n, "url": "https://swcdn.apple.com/content/downloads/c/" + n, "size": 2_750_000_000}
                                     for n in ("InstallAssistantAuto.pkg", "RecoveryHDMetaDmg.pkg", "InstallESDDmg.pkg")]},
    {"id": "legacy-10.12.6", "name": "macOS Sierra", "family": "macOS Sierra", "version": "10.12.6", "build": "", "kind": "dmg", "size": 5_000_000_000,
     "date": "", "files": [{"name": "InstallOS.dmg", "url": "https://updates.cdn-apple.com/2019/cert/x/InstallOS.dmg", "size": 5_000_000_000}]},
]


def _family(name):
    f = re.sub(r"^Install\s+", "", name.strip())
    f = re.sub(r"\s+(?:(?:Public|Developer)\s+)?(?:Beta|Seed|Preview)(?:\s+\d+)?$", "", f, flags=re.I)
    return re.sub(r"\s+(?:Release Candidate|RC)(?:\s+\d+)?$", "", f, flags=re.I).strip()


def _mac_catalog():
    raw = _get(CATALOG, 60).content
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    prods = plistlib.loads(raw).get("Products", {})
    cands = []
    for pid, p in prods.items():
        if "InstallAssistantPackageIdentifiers" not in (p.get("ExtendedMetaInfo") or {}):
            continue
        dist = p.get("Distributions") or {}
        durl = next((dist[k] for k in ("English", "en", "en_US", "en_GB") if k in dist), None) or next(iter(dist.values()), None)
        if not durl:
            continue
        pk = [{"name": Path(urlparse(x["URL"]).path).name, "url": x["URL"], "size": int(x.get("Size") or 0)}
              for x in p.get("Packages") or [] if x.get("URL") and _apple(x["URL"])]
        date = p.get("PostDate")
        cands.append((pid, durl, pk, date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else ""))

    def parse(c):
        pid, durl, pk, date = c
        try:
            t = _get(durl, 30).text
        except Exception:                               # noqa: BLE001
            return None
        m = re.search(r'suDisabledGroupID="([^"]+)"', t)
        v = re.search(r"<key>VERSION</key>\s*<string>([^<]+)</string>", t)
        b = re.search(r"<key>BUILD</key>\s*<string>([^<]+)</string>", t)
        if not m or not v:
            return None
        name, ver = m.group(1).replace("Install ", "").strip(), v.group(1).strip()
        major = int(ver.split(".")[0]) if ver.split(".")[0].isdigit() else 0
        if major >= 11:
            files = [x for x in pk if x["name"].lower() == "installassistant.pkg"]
            kind = "pkg"
        else:
            files = sorted([x for x in pk if x["name"].lower() in LEGACY_PKGS], key=lambda x: LEGACY_PKGS.index(x["name"].lower()))
            kind = "multi"
            if len(files) < 3:
                return None
        if not files:
            return None
        return {"id": pid, "name": name, "family": _family(name), "version": ver, "build": b.group(1).strip() if b else "",
                "kind": kind, "size": sum(x["size"] for x in files), "date": date, "files": files}

    with ThreadPoolExecutor(8) as ex:
        out = [x for x in ex.map(parse, cands) if x]
    return out


def _mac_legacy():
    try:
        html = _get(SUPPORT, 30).text
    except Exception:                                   # noqa: BLE001
        return []
    out = []
    for label, name, ver in LEGACY:
        m = re.search(r'<a href="([^"]+)"[^>]*>\s*' + re.escape(label) + r"\s*</a>", html)
        if not m or not _apple(m.group(1)) or not m.group(1).lower().endswith(".dmg"):
            continue
        url = m.group(1).replace("http://", "https://", 1)
        out.append({"id": "legacy-" + ver, "name": name, "family": name, "version": ver, "build": "", "kind": "dmg", "size": 0, "date": "",
                    "files": [{"name": Path(urlparse(url).path).name, "url": url, "size": 0}]})
    return out


def _vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4])


def mac_list(j=None, refresh=False):
    """Danh sách bộ cài macOS chính chủ Apple (mới nhất trước). Có thể chạy như việc dài (j) hoặc gọi thẳng."""
    if fake():
        if j:
            j["text"] = "Đang đọc danh mục bộ cài của Apple..."
            time.sleep(1)
        return FAKE_MAC
    if j:
        j["pct"], j["text"] = -1, "Đang đọc danh mục bộ cài của Apple (10 - 30 giây)..."
    if refresh:
        _CACHE.pop("mac", None)

    def build():
        items = _mac_catalog() + _mac_legacy()
        seen, out = set(), []
        for x in sorted(items, key=lambda x: (_vkey(x["version"]), x["build"], x["date"]), reverse=True):
            k = (x["name"], x["version"], x["build"])
            if k not in seen:
                seen.add(k)
                out.append(x)
        return out
    return _cached("mac", 3600, build)


def mac_download(j, pid, dest=""):
    """Tải bộ cài đã chọn (1 file InstallAssistant.pkg / .dmg, hoặc bộ 3 file cho 10.13 - 10.15) vào thư mục riêng."""
    it = next((x for x in mac_list() if x["id"] == pid), None)
    if not it:
        raise RuntimeError("Không thấy bản macOS này - bấm Làm mới danh sách")
    folder = re.sub(r'[\\/:*?"<>|]', "", f"{it['name']} {it['version']}" + (f" ({it['build']})" if it["build"] else "")).strip()
    out = absp(dest) if dest else (absp("Data/macOS") if fake() else data_dir("macOS"))
    if it["kind"] == "multi":
        out = out / folder
    res = dl_files(j, it["files"], out, folder)
    note = {"pkg": "Trên máy Mac: mở InstallAssistant.pkg để có ứng dụng 'Install macOS' trong Applications, rồi dùng macUSB tạo USB.",
            "dmg": "Trên máy Mac: mở file .dmg, chạy gói cài bên trong để có ứng dụng cài đặt, rồi dùng macUSB tạo USB.",
            "multi": "Bộ 3 file của Apple cho macOS 10.13 - 10.15: chép cả thư mục sang máy Mac để ráp bộ cài (macUSB / gibMacOS)."}[it["kind"]]
    res["text"] = f"Đã tải xong {folder}. {note}"
    return res


# ================================================================ KHO iOS (IPSW)
FAKE_DEV = [{"name": "iPhone 16 Pro Max", "identifier": "iPhone17,2"}, {"name": "iPhone 16 Pro", "identifier": "iPhone17,1"},
            {"name": "iPhone 15 Pro", "identifier": "iPhone16,1"}, {"name": "iPhone 14 Pro", "identifier": "iPhone15,2"},
            {"name": "iPhone 11", "identifier": "iPhone12,1"}, {"name": "iPhone X (Global)", "identifier": "iPhone10,3"},
            {"name": "iPad Pro 11-inch (M4) (WiFi)", "identifier": "iPad16,3"}, {"name": "iPad (10th generation) (WiFi)", "identifier": "iPad13,18"},
            {"name": "iPod touch (7th generation)", "identifier": "iPod9,1"}, {"name": "Apple TV 4K (3rd generation)", "identifier": "AppleTV14,1"},
            {"name": "MacBook Air (M2, 2022)", "identifier": "Mac14,2"}, {"name": "Mac mini (M4, 2024)", "identifier": "Mac16,10"},
            {"name": "HomePod mini", "identifier": "AudioAccessory5,1"}]


def _cat(ident):
    for p, c in (("iPhone", "iPhone"), ("iPad", "iPad"), ("iPod", "iPod"), ("AppleTV", "Apple TV"), ("Watch", "Apple Watch"),
                 ("AudioAccessory", "HomePod"), ("iBridge", "Khác")):
        if ident.startswith(p):
            return c
    if re.match(r"^(Mac|iMac|MacBook|Macmini|MacPro|VirtualMac|ADP)", ident):
        return "Mac (Apple Silicon)"
    return "Khác"


def _ident_key(i):
    m = re.match(r"^([A-Za-z]+)(\d+),(\d+)$", i)
    return (m.group(1), -int(m.group(2)), int(m.group(3))) if m else (i, 0, 0)


def ios_devices():
    """Tất cả thiết bị Apple có firmware IPSW (iPhone, iPad, iPod, Apple TV, HomePod, Mac chip M)."""
    rows = FAKE_DEV if fake() else _cached("ipsw_dev", 6 * 3600, lambda: _get(IPSW_API + "/devices", 30).json())
    out = [{"name": d.get("name") or d["identifier"], "id": d["identifier"], "cat": _cat(d["identifier"])} for d in rows if d.get("identifier")]
    return sorted(out, key=lambda d: _ident_key(d["id"]))


def ios_firmwares(ident):
    """Firmware của 1 thiết bị: phiên bản, build, ngày phát hành, dung lượng, Apple còn ký không, link tải."""
    if fake():
        import random
        random.seed(ident)
        base = [("26.1", "23B85", True), ("26.0.1", "23A355", True), ("26.0", "23A341", False), ("18.7.2", "22H124", True),
                ("18.6.2", "22G100", False), ("18.5", "22F76", False), ("17.6.1", "21G93", False)]
        return {"name": next((d["name"] for d in FAKE_DEV if d["identifier"] == ident), ident), "id": ident,
                "fw": [{"version": v, "build": b, "signed": s, "size": random.randint(6, 9) * 10**9, "date": "2026-11-0%d" % (i + 1),
                        "url": f"https://updates.cdn-apple.com/2026FallFCS/fullrestores/x/{ident}_{v}_{b}_Restore.ipsw", "sha1": "a" * 40}
                       for i, (v, b, s) in enumerate(base)]}
    ident = re.sub(r"[^A-Za-z0-9,]", "", ident or "")
    d = _cached("ipsw_fw_" + ident, 1800, lambda: _get(f"{IPSW_API}/device/{ident}?type=ipsw", 30).json())
    fw = [{"version": f.get("version", ""), "build": f.get("buildid", ""), "signed": bool(f.get("signed")), "size": int(f.get("filesize") or 0),
           "date": (f.get("releasedate") or "")[:10], "url": f.get("url", ""), "sha1": f.get("sha1sum", "")}
          for f in d.get("firmwares") or [] if f.get("url")]
    return {"name": d.get("name", ident), "id": ident, "fw": fw}


def ios_download(j, url, dest=""):
    if not _apple(url):
        raise RuntimeError("Chỉ tải firmware từ máy chủ Apple")
    name = Path(urlparse(url).path).name
    out = absp(dest) if dest else (absp("Data/iOS") if fake() else data_dir("iOS"))
    res = dl_files(j, [{"name": name, "url": url, "size": 0}], out, name)
    res["text"] = (f"Đã tải xong {name}. Cắm iPhone / iPad vào máy có iTunes (Windows) hoặc Finder (Mac), "
                   "giữ Shift (Windows) / Option (Mac) rồi bấm Khôi phục (Restore) và chọn file này.")
    return res


# ================================================================ TẢI FILE (dùng chung, tải tiếp khi bị ngắt)
def dl_files(j, files, out, label):
    out = Path(out)
    tot = sum(int(f.get("size") or 0) for f in files)
    if fake():
        tot = tot or 6_000_000_000
        for i in range(0, 101, 5):
            if j.get("stop"):
                raise RuntimeError("Đã dừng (lần sau tải tiếp từ chỗ dừng)")
            j["pct"], j["text"] = i, f"{label}: {human(tot * i // 100)} / {human(tot)} · 92.0 MB/s"
            time.sleep(0.05)
        return {"dest": str(out), "path": str(out / files[0]["name"]), "size": tot}
    import requests
    out.mkdir(parents=True, exist_ok=True)
    if tot and shutil.disk_usage(out).free < tot - sum((out / (f["name"] + ".tai")).stat().st_size for f in files if (out / (f["name"] + ".tai")).exists()):
        raise RuntimeError(f"Ổ đĩa không đủ chỗ: cần {human(tot)}, còn trống {human(shutil.disk_usage(out).free)}. Chọn ổ khác.")
    base_done = 0
    t0, last, got0 = time.time(), 0, None
    for n, f in enumerate(files):
        path, part = out / f["name"], out / (f["name"] + ".tai")
        if path.exists() and f.get("size") and path.stat().st_size == f["size"]:
            base_done += f["size"]
            continue
        have = part.stat().st_size if part.exists() else 0
        hdr = dict(UA)
        if have:
            hdr["Range"] = f"bytes={have}-"
        with requests.get(f["url"], headers=hdr, stream=True, timeout=30) as r:
            if r.status_code != 416:
                r.raise_for_status()
                if have and r.status_code != 206:
                    have = 0
                size = have + int(r.headers.get("Content-Length") or 0)
                if not tot:
                    tot = size
                    free = shutil.disk_usage(out).free
                    if size - have > free:
                        raise RuntimeError(f"Ổ đĩa không đủ chỗ: cần {human(size - have)}, còn trống {human(free)}. Chọn ổ khác.")
                done = have
                if got0 is None:
                    got0 = base_done + have
                with open(part, "ab" if have else "wb") as fh:
                    for chunk in r.iter_content(4 << 20):
                        if j.get("stop"):
                            raise RuntimeError("Đã dừng (lần sau bấm tải là tải tiếp từ chỗ dừng)")
                        fh.write(chunk)
                        done += len(chunk)
                        if time.time() - last > 0.4:
                            last = time.time()
                            cur = base_done + done
                            sp = (cur - got0) / max(0.1, time.time() - t0)
                            j["pct"] = int(cur * 100 / max(1, tot))
                            j["text"] = (f"{label}" + (f" · file {n + 1}/{len(files)}" if len(files) > 1 else "")
                                         + f": {human(cur)} / {human(tot)} · {human(sp)}/s")
        if path.exists():
            path.unlink()
        part.rename(path)
        base_done += path.stat().st_size
    return {"dest": str(out), "path": str(out / files[0]["name"]), "size": base_done}
