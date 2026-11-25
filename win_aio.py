# -*- coding: utf-8 -*-
"""Win AIO by Duy Anh - bộ tiện ích cài Win / phần mềm / thiết lập Windows.

Giao diện web trong cửa sổ app (pywebview / Edge WebView2), cùng phong cách PikPak Auto Save.
  - Mở tool không cần mật khẩu. Mật khẩu Admin (mặc định: admin) mở chế độ chỉnh sửa:
    sửa tên nút, đổi nguồn (link / file / winget / lệnh), thêm - xóa - xếp nút và nhóm.
  - Danh sách phần mềm + lịch sử: Data/winaio.db (SQLite). Cài đặt nhỏ: Data/config.json (sửa tay được).

Chạy:  python win_aio.py            -> cửa sổ app (pip install pywebview requests)
       python win_aio.py --serve    -> mở bằng trình duyệt (để thử)
"""
import ctypes
import datetime as dt
import hashlib
import json
import math
import os
import re
import unicodedata
import secrets
import shlex
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse

import mgr
import extra
import apple
import officex

APP_TITLE = "Win AIO by Duy Anh"
APP_VERSION = "v4.2"
REPO = "laocuumon1982-cpu/WIN-AIO-SHARE"                       # nơi phát hành bản mới (nút Cập nhật)
EXE_NAME = "Win AIO by Duy Anh.exe"
IS_WIN = os.name == "nt"
FAKE = os.environ.get("WINAIO_FAKE") == "1"          # chỉ để thử giao diện trên máy không phải Windows

if getattr(sys, "frozen", False):
    BASE = Path(sys.executable).resolve().parent         # thư mục chứa file exe (chạy được từ USB)
else:
    BASE = Path(__file__).resolve().parent
RES = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DATA = BASE / "Data"
DB_FILE = DATA / "winaio.db"
CONFIG_FILE = DATA / "config.json"
OLD_JSON = DATA / "apps.json"                            # file JSON cũ / bản xuất -> tự nhập 1 lần
BACKUP_DIR = DATA / "Backup"
CREATE_NO_WINDOW = 0x08000000 if IS_WIN else 0

DEFAULT_CONFIG = {
    "download_dir": "Data\\Downloads",
    "keep_installer": True,
    "theme": "light",
    "skin": "default",          # giao diện: default = Mặc định, g01 = Giao diện 01 (navy), g01l = Giao diện 01 (xanh trắng)
    "admin_salt": "",
    "admin_hash": "",
    "window": {},
}

GH_CIT = r"github:Cuongyd196/cit-voice-studio|win-x86_64\.exe$"
GH_SUBTR = r"github:rockbenben/subtitle-translator|x64_portable\.exe$"
GH_YTDL = r"github:duckmartians/YouTube_Downloader|windows\.zip$"
ARTCRAFT = ("ARTCRAFT OFFICE PORTABLE", [
    ("📝", "WordCraft (thay Word)", r"github:storytold/wordcraft|windows-x64-portable\.zip$", "", "ArtCraft - soạn thảo văn bản, bản portable"),
    ("📊", "GridCraft (thay Excel)", r"github:storytold/gridcraft|windows-x64-portable\.zip$", "", "ArtCraft - bảng tính, bản portable"),
    ("📽️", "DeckCraft (thay PowerPoint)", r"github:storytold/deckcraft|windows-x64-portable\.zip$", "", "ArtCraft - trình chiếu, bản portable"),
])
ONLYOFFICE = ("📝", "ONLYOFFICE", "winget:ONLYOFFICE.DesktopEditors", "", "Bộ văn phòng miễn phí, mở tốt file Word / Excel / PowerPoint")
WHATSAPP = ("🟢", "WhatsApp", "winget:9NKSQGP7F2NH", "", "Cài từ Microsoft Store")
# Tiện ích cài Win dạo (Hải Đỗ): file mới nhất trong bản phát hành "caiwindao" (tool đó tự đọc version.txt cùng chỗ)
CAIWINDAO = ("🧰", "Tiện ích cài Win dạo", r"github:minhhaibuitt/Caiwindao@caiwindao|^Tien\.ich\.cai\.Win\.dao\.v[\d.]+\.exe$", "",
             "Tool cài Win dạo của Hải Đỗ - luôn tải bản mới nhất (mật khẩu: haido)")
# Tiện ích văn phòng (Hải Đỗ): file mới nhất trong bản phát hành "vanphong" (tool đó tự đọc version.txt cùng chỗ)
VANPHONG = ("🧾", "Tiện ích văn phòng", r"github:minhhaibuitt/Caiwindao@vanphong|^Tien\.ich\.van\.phong\.v[\d.]+\.exe$", "",
            "Tiện ích văn phòng của Hải Đỗ - luôn tải bản mới nhất")
# Nhóm gỡ phần mềm cứng đầu (v3.2). codeberg: giống github: (Forgejo có API phát hành giống GitHub)
HIBIT = ("🧹", "HiBit Uninstaller", "winget:HiBitSoftware.HiBitUninstaller", "", "")
UNINSTALLER = ("UNINSTALLER TOOL", [
    HIBIT,
    ("🅰️", "Avast Clear", "https://files.avast.com/iavs9x/avastclear.exe", "", "Công cụ gỡ Avast chính hãng (trang chủ Avast)"),
    ("🧹", "360 Security Uninstaller Tool", r"github:ThanhNguyenVN93/360-Security-Uninstaller-Tool|\.(exe|zip)$", "",
     "Gỡ 360 Security (ThanhNguyenVN93, bản mới nhất từ GitHub)"),
    ("🛡️", "360 Total Security Remover", r"codeberg:yansuogaming/360totalremove|portable.*\.(exe|zip|rar|7z)$", "pass=123",
     "Gỡ sạch 360 Total Security (Yansuo, bản Portable mới nhất từ Codeberg)"),
    ("🧽", "WPS Office Utility & Cleaner", r"codeberg:yansuogaming/wps-utility|portable.*\.(exe|zip|rar|7z)$", "pass=123",
     "Gỡ sạch / chặn WPS Office (Yansuo, bản Portable mới nhất từ Codeberg)"),
])
TOOLS_3U = ("📱", "3uTools (64-bit)", r"page:https://www.3u.com/|https?://dl\.3u\.com/[^\"'\s<>]*3uTools_v[\d.]+_Setup_x64\.exe", "",
            "Quản lý iPhone / iPad, flash iOS - luôn lấy bản 64-bit mới nhất trên trang chủ 3u.com")
# Transub-Player bản Việt hóa của Duy Anh: lấy bộ cài trong bản phát hành mới nhất của repo fork
TRANSUB = ("🎬", "Transub-Player", r"github:laocuumon1982-cpu/Transub-Player|win-x64-setup\.exe$", "",
           "Trình xem phim tự dịch phụ đề sang tiếng Việt (bản của Duy Anh)")
# Nhóm đọc chữ thành giọng nói & phụ đề (v4.0)
LAZIBOOK = ("📚", "LaziBook", "winget:9N2X9BM8R5P9", "", "Đọc truyện, nghe sách nói giọng Việt (EPUB, PDF, Word, truyện tranh) - Microsoft Store")
VIENEU = ("🗣️", "VieNeu-TTS", r"github:pnnbao97/VieNeu-TTS|_x64-setup\.exe$", "", "Chuyển văn bản thành giọng nói tiếng Việt (bản mới nhất từ GitHub)")
TTS_SUB = ("TTS & SUB", [
    ("🎞️", "CIT Voice Studio", GH_CIT, "", ""),
    ("🎞️", "Subtitle Translator", GH_SUBTR, "", ""),
    LAZIBOOK,
    VIENEU,
])
PICVIEW = ("🖼️", "PicView", "winget:Ruben2776.PicView", "", "Cài vào ổ C và tự đặt làm trình xem ảnh mặc định")
FONT_PACK = "https://github.com/minhhaibuitt/Caiwindao/releases/download/Tonghop/fontchu.zip"     # bộ font đầy đủ (VNI, TCVN3, SVN...)

# Link cũ đã chết -> nguồn mới (tự sửa trong dữ liệu đã lưu và lúc cài)
DEAD_LINKS = [
    (re.compile(r"^https?://[^/]*(res-download-pc|chat\.zalo\.me|zadn\.vn|zdn\.vn)[^ ]*/ZaloSetup[^/]*\.exe$", re.I), "winget:VNGCorp.Zalo"),
]


# Nguồn mặc định của bản cũ -> winget / GitHub mới nhất (chỉ đổi nút còn đúng link cũ, nút bạn đã sửa thì giữ nguyên)
OLD_DEFAULT_SRC = {
    "https://github.com/duckmartians/YouTube_Downloader/releases/download/v4.0.0/YouTube_Downloader_v4.0.0_windows.zip": GH_YTDL,
    "https://github.com/Cuongyd196/cit-voice-studio/releases/download/1.0.6/CIT-Voice-Studio-v1.0.6-win-x86_64.exe": GH_CIT,
    "https://github.com/rockbenben/subtitle-translator/releases/download/v3.2.1/SubtitleTranslator_3.2.1_x64_portable.exe": GH_SUBTR,
    "https://www.unikey.org/assets/release/unikey46RC2-230919-win64.zip": "winget:UniKey.UniKey",
    "https://github.com/lamquangminh/EVKey/releases": "winget:lamquangminh.EVKey",
    "https://www.rarlab.com/rar/winrar-x64-701.exe": "winget:RARLab.WinRAR",
    "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=vi": "winget:Mozilla.Firefox.vi",
    "https://discord.com/api/download?platform=win": "winget:Discord.Discord",
    "https://zoom.us/client/latest/ZoomInstaller.exe": "winget:Zoom.Zoom",
    "https://download.viber.com/desktop/windows/ViberSetup.exe": "winget:Rakuten.Viber",
    "https://www.ultraviewer.net/vi/UltraViewer_setup_6.6_vi.exe": "winget:DucFabulous.UltraViewer",
    "https://download.teamviewer.com/download/TeamViewer_Setup.exe": "winget:TeamViewer.TeamViewer",
    "https://dl.google.com/drive-file-stream/GoogleDriveSetup.exe": "winget:Google.GoogleDrive",
    "https://aka.ms/vs/17/release/vc_redist.x64.exe": "winget:Microsoft.VCRedist.2015+.x64",
    "https://aka.ms/vs/17/release/vc_redist.x86.exe": "winget:Microsoft.VCRedist.2015+.x86",
    "https://download.microsoft.com/download/f/3/a/f3a6af84-da23-40a5-8d1c-49cc10c8e76f/NDP48-x86-x64-AllOS-ENU.exe": "winget:Microsoft.DotNet.Framework.DeveloperPack_4",
    "https://download.microsoft.com/download/1/7/1/1718CCC4-6315-4D8E-9543-8E28A4E18C4C/dxwebsetup.exe": "winget:Microsoft.DirectX",
    "https://www.bluestacks.com/download.html": "winget:BlueStack.BlueStacks",
    "winget:AnyDeskSoftwareGmbH.AnyDesk": "winget:AnyDesk.AnyDesk"
}


def wg_source(pkg):
    """ID Microsoft Store (12 ký tự, VD 9NKSQGP7F2NH) -> kho msstore, còn lại -> kho winget."""
    return "msstore" if re.fullmatch(r"[0-9A-Z]{12}", (pkg or "").strip()) else "winget"


def norm_name(t):
    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", (t or "").lower()).encode("ascii", "ignore").decode())


def fix_src(src):
    new = OLD_DEFAULT_SRC.get((src or "").strip())
    if new:
        return new
    for rx, new in DEAD_LINKS:
        if rx.match((src or "").strip()):
            return new
    return src


def nice_err(e):
    """Lỗi mạng của requests -> câu dễ hiểu."""
    t = str(e)
    host = re.search(r"host='([^']+)'", t)
    host = host.group(1) if host else ""
    if "NameResolution" in t or "getaddrinfo" in t:
        return (f"Không tìm thấy máy chủ {host} - link tải có thể đã chết, hoặc mạng / DNS đang lỗi. "
                "Thử mở web xem có vào được không; Admin bấm ✎ để đổi nguồn nút này.")
    if "ConnectTimeout" in t or "ReadTimeout" in t or "timed out" in t:
        return f"Máy chủ {host} không trả lời (quá thời gian chờ) - kiểm tra mạng rồi thử lại."
    if "SSLError" in t or "CERTIFICATE" in t:
        return f"Lỗi bảo mật SSL khi kết nối {host} - kiểm tra ngày giờ máy tính, hoặc phần mềm diệt virus chặn."
    if "ConnectionError" in t or "Max retries" in t:
        return f"Không kết nối được {host} - kiểm tra mạng rồi thử lại."
    m = re.search(r"(\d{3}) Client Error|(\d{3}) Server Error", t)
    if m:
        return f"Máy chủ báo lỗi {m.group(1) or m.group(2)} - link tải có thể đã đổi; Admin bấm ✎ để đổi nguồn."
    return t


# ---------------------------------------------------------------- danh sách mặc định (sửa được trong tool)
# Kho bộ cài WIN - nút mở trang tải của massgrave.dev (link file trên đó đổi hằng tháng nên mở trang để luôn có bản mới)
ISO_MG = "https://massgrave.dev/"
ISO_MG_PAGES = [
    ("🪟", "Windows 11", "windows_11_links", "Bản mới nhất, x64"),
    ("🪟", "Windows 10", "windows_10_links", "22H2, x64 / x86"),
    ("🏢", "Windows 10 / 11 LTSC", "windows_ltsc_links", "Enterprise LTSC"),
    ("📱", "Windows ARM64", "windows_arm_links", "Máy chip ARM (Snapdragon)"),
    ("🖥️", "Windows Server", "windows-server-links", "2016 · 2019 · 2022 · 2025"),
    ("💠", "Windows 8.1", "windows_8.1_links", ""),
    ("💠", "Windows 8", "windows_8_links", ""),
    ("🪟", "Windows 7", "windows_7_links", ""),
    ("📋", "Danh sách đầy đủ", "genuine-installation-media", "Windows, Office + mã kiểm tra"),
]
# Tab Web: nút mở trang web hay dùng (Admin sửa / thêm / xóa)
DEFAULT_WEB = [     # (nhóm, icon, tên, link) - theo file sao lưu của Duy Anh (24/11/2026 22:24)
    ("HHTQ", "🌐", "HHTQ 4K", "https://drive.google.com/drive/folders/18dpeUzn7emXhJ2pGNNgNXVHuHewF32xY"),
    ("HHTQ", "🌐", "HHTQ 4K", "https://mypikpak.com/s/VP6-HTClWBLhBU15uGQieClio2"),
    ("HHTQ", "🌐", "HHTQ 4K - KIMNGON", "https://mypikpak.com/s/VOyELoBfemkzMwlEob9EwA-Ho2/AADm8sjD8JFVYb_SKu4oEKPko2_VOx"),
    ("HHTQ", "🌐", "HHTQ 4K - KIMNGON", "https://www.fshare.vn/folder/1CENU2DFSGMG"),
    ("HAY DÙNG", "🌐", "Hoàng Phát 360", "https://hoangphat360.vn/"),
    ("HAY DÙNG", "🌐", "BEEUNLOCK", "https://beeunlock.com/"),
    ("GITHUB", "🌐", "Canon LBP2900 driver for Mac", "https://github.com/maclifevn/Canon-2900-Driver-MacLife"),
    ("GITHUB", "🌐", "macUSB", "https://github.com/Kruszoneq/macUSB"),
    ("GITHUB", "🌐", "StabilityMatrix", "https://github.com/LykosAI/StabilityMatrix"),
    ("GITHUB", "🌐", "FreeVideo", "https://github.com/FlashML-org/FreeVideo"),
    ("GITHUB", "🌐", "MangaForge", "https://github.com/PhamTienThang2510/MangaForge"),
    ("GITHUB", "🌐", "YouTube Downloader", "https://github.com/duckmartians/YouTube_Downloader"),
    ("GITHUB", "🌐", "Subtitle Translator", "https://github.com/rockbenben/subtitle-translator"),
    ("GITHUB", "🌐", "pyVideoTrans", "https://github.com/jianchang512/pyvideotrans"),
    ("GITHUB", "🌐", "Transub-Player", "https://github.com/dlsandy/Transub-Player"),
    ("GITHUB", "🌐", "CIT Voice Studio", "https://github.com/Cuongyd196/cit-voice-studio"),
    ("GITHUB", "🌐", "ViFastTts", "https://github.com/vifast-oss/ViFastTts"),
    ("GITHUB", "🌐", "VieNeu-TTS", "https://github.com/pnnbao97/VieNeu-TTS"),
]

# Hồ sơ cài đặt (preset): bấm 1 lần cài các phần mềm + chạy tiện ích Windows. Lưu tên phần mềm (không lưu id -> đổi nút vẫn khớp).
DEFAULT_PRESETS = [
    ("Máy văn phòng", "🏢", ["Google Chrome", "UniKey", "Zalo PC", "Foxit PDF Reader", "WinRAR", "UltraViewer", "MS Office"],
     ["ext", "thispc", "tz", "faststart"], {"tidy": True}),
    ("Máy kế toán", "🧮", ["Google Chrome", "UniKey", "Zalo PC", "Foxit PDF Reader", "WinRAR", "UltraViewer", "TeamViewer", "MS Office",
                         ".NET Framework 3.5", "Visual C++ 2015-2022 x86"],
     ["ext", "thispc", "tz", "faststart"], {"tidy": True, "fonts": True}),
    ("Máy game", "🎮", ["Google Chrome", "Discord", "7-Zip", "Visual C++ 2015-2022 x64", "Visual C++ 2015-2022 x86", "DirectX Runtime",
                      "OBS Studio"],
     ["faststart", "hiber", "tz"], {"tidy": True}),
]
DEFAULT_PW = "HP360"          # mật khẩu Admin mặc định
KHO_FSHARE = "open:https://www.fshare.vn/folder/BESIWSY4GNO7"
KHO_GDRIVE = "open:https://drive.google.com/drive/u/3/folders/173Ouz2LQQcrVr9SbirV68wgJvXP2Svz2"
DEFAULT_GROUPS = [     # (tên nhóm, cột, [nút...]) - thứ tự trong cột, vị trí & link theo file sao lưu của Duy Anh (24/11/2026 22:24)
    ("ACTIVE", 0, [
        ("🔑", "IDM", "", "", ""),
        ("🔑", "ADOBE", "", "", ""),
        ("🔑", "MAS AIO", "", "", ""),
    ]),
    ("KHO PHẦN MỀM", 0, [
        ("🗄️", "Kho Fshare", "open:https://www.fshare.vn/folder/BESIWSY4GNO7", "", "Mở thư mục phần mềm trên Fshare"),
        ("🗂️", "Kho Google Drive", "open:https://drive.google.com/drive/u/3/folders/173Ouz2LQQcrVr9SbirV68wgJvXP2Svz2", "", "Mở thư mục phần mềm trên Google Drive"),
        ("📦", "Kho PITVNcommunity", "", "", ""),
    ]),
    ("TRÌNH DUYỆT WEB", 0, [
        ("🌐", "Google Chrome", "winget:Google.Chrome", "", ""),
        ("🦊", "Firefox", "winget:Mozilla.Firefox.vi", "", ""),
        ("🍀", "Cốc Cốc", "winget:CocCoc.CocCoc", "", ""),
        ("🦁", "Brave", "winget:Brave.Brave", "", ""),
    ]),
    ("HỖ TRỢ TỪ XA", 0, [
        ("🖥️", "UltraViewer", "winget:DucFabulous.UltraViewer", "", ""),
        ("🖥️", "TeamViewer", "winget:TeamViewer.TeamViewer", "", ""),
        ("🖥️", "AnyDesk", "winget:AnyDesk.AnyDesk", "", ""),
    ]),
    ("ĐA PHƯƠNG TIỆN", 1, [
        ("🖼️", "PicView", "winget:Ruben2776.PicView", "", "Cài vào ổ C và tự đặt làm trình xem ảnh mặc định"),
        ("🎞️", "OBS Studio", "winget:OBSProject.OBSStudio", "", ""),
        ("🎬", "Transub-Player", r"github:laocuumon1982-cpu/Transub-Player|win-x64-setup\.exe$", "", "Trình xem phim tự dịch phụ đề sang tiếng Việt (bản của Duy Anh)"),
        ("🎬", "VLC Media Player", "winget:VideoLAN.VLC", "", ""),
        ("🎬", "K-Lite Codec Pack", "winget:CodecGuide.K-LiteCodecPack.Standard", "", ""),
    ]),
    ("TTS & SUB", 1, [
        ("📚", "LaziBook", "winget:9N2X9BM8R5P9", "", "Đọc truyện, nghe sách nói giọng Việt (EPUB, PDF, Word, truyện tranh) - Microsoft Store"),
        ("🗣️", "VieNeu-TTS", r"github:pnnbao97/VieNeu-TTS|_x64-setup\.exe$", "", "Chuyển văn bản thành giọng nói tiếng Việt (bản mới nhất từ GitHub)"),
        ("🎞️", "CIT Voice Studio", r"github:Cuongyd196/cit-voice-studio|win-x86_64\.exe$", "", ""),
        ("🎞️", "Subtitle Translator", r"github:rockbenben/subtitle-translator|x64_portable\.exe$", "", ""),
    ]),
    ("TIỆN ÍCH", 1, [
        ("🔎", "Everything", "winget:voidtools.Everything", "", "Tìm file siêu nhanh"),
        ("📸", "ShareX", "winget:ShareX.ShareX", "", "Chụp màn hình"),
        ("🛠️", "Snappy Driver Installer", "winget:GlennDelahoy.SnappyDriverInstallerOrigin", "", ""),
        ("🎞️", "YouTube Downloader", r"github:duckmartians/YouTube_Downloader|windows\.zip$", "", ""),
        ("🧰", "Tiện ích cài Win dạo", r"github:minhhaibuitt/Caiwindao@caiwindao|^Tien\.ich\.cai\.Win\.dao\.v[\d.]+\.exe$", "", "Tool cài Win dạo của Hải Đỗ - luôn tải bản mới nhất (mật khẩu: haido)"),
    ]),
    ("VĂN PHÒNG - PDF", 2, [
        ("🏢", "MS Office", "office:", "", "Cài Office 2016 / 2019 / 2021 / 2024 / 365 chính chủ từ Microsoft (Online hoặc Offline)"),
        ("🧾", "Tiện ích văn phòng", r"github:minhhaibuitt/Caiwindao@vanphong|^Tien\.ich\.van\.phong\.v[\d.]+\.exe$", "", "Tiện ích văn phòng của Hải Đỗ - luôn tải bản mới nhất"),
        ("📄", "Foxit PDF Reader", "winget:Foxit.FoxitReader", "", ""),
        ("📄", "Sumatra PDF", "winget:SumatraPDF.SumatraPDF", "", ""),
        ("📝", "Notepad++", "winget:Notepad++.Notepad++", "", ""),
        ("📝", "LibreOffice", "winget:TheDocumentFoundation.LibreOffice", "", ""),
        ("📝", "WPS Office", "winget:Kingsoft.WPSOffice", "", ""),
        ("📝", "ONLYOFFICE", "winget:ONLYOFFICE.DesktopEditors", "", "Bộ văn phòng miễn phí, mở tốt file Word / Excel / PowerPoint"),
    ]),
    ("ARTCRAFT OFFICE", 2, [
        ("📝", "WordCraft", r"github:storytold/wordcraft|windows-x64-portable\.zip$", "", "ArtCraft - soạn thảo văn bản, bản portable"),
        ("📊", "GridCraft", r"github:storytold/gridcraft|windows-x64-portable\.zip$", "", "ArtCraft - bảng tính, bản portable"),
        ("📽️", "DeckCraft", r"github:storytold/deckcraft|windows-x64-portable\.zip$", "", "ArtCraft - trình chiếu, bản portable"),
    ]),
    ("BỘ GÕ TIẾNG VIỆT", 2, [
        ("⌨️", "UniKey", "winget:UniKey.UniKey", "", ""),
        ("⌨️", "EVKey", "winget:lamquangminh.EVKey", "", ""),
    ]),
    ("NHẮN TIN - HỌP", 3, [
        ("💬", "Zalo PC", "winget:VNGCorp.Zalo", "", ""),
        ("📞", "Viber", "winget:Rakuten.Viber", "", ""),
        ("🟢", "WhatsApp", "winget:9NKSQGP7F2NH", "", "Cài từ Microsoft Store"),
        ("✈️", "Telegram", "winget:Telegram.TelegramDesktop", "", ""),
        ("🎮", "Discord", "winget:Discord.Discord", "", ""),
        ("📹", "Zoom", "winget:Zoom.Zoom", "", ""),
        ("👥", "Microsoft Teams", "winget:Microsoft.Teams", "", ""),
    ]),
    ("NÉN - GIẢI NÉN", 3, [
        ("📦", "WinRAR", "winget:RARLab.WinRAR", "", ""),
        ("📦", "7-Zip", "winget:7zip.7zip", "", ""),
    ]),
    ("UNINSTALLER TOOL", 3, [
        ("🧹", "HiBit Uninstaller", "winget:HiBitSoftware.HiBitUninstaller", "", ""),
        ("🅰️", "Avast Clear", "https://files.avast.com/iavs9x/avastclear.exe", "", "Công cụ gỡ Avast chính hãng (trang chủ Avast)"),
        ("🧹", "360 Security Uninstaller Tool", r"github:ThanhNguyenVN93/360-Security-Uninstaller-Tool|\.(exe|zip)$", "", "Gỡ 360 Security (ThanhNguyenVN93, bản mới nhất từ GitHub)"),
        ("🛡️", "360 Total Security Remover", r"codeberg:yansuogaming/360totalremove|portable.*\.(exe|zip|rar|7z)$", "pass=123", "Gỡ sạch 360 Total Security (Yansuo, bản Portable mới nhất từ Codeberg)"),
        ("🧽", "WPS Office Utility & Cleaner", r"codeberg:yansuogaming/wps-utility|portable.*\.(exe|zip|rar|7z)$", "pass=123", "Gỡ sạch / chặn WPS Office (Yansuo, bản Portable mới nhất từ Codeberg)"),
    ]),
    ("GIẢ LẬP ANDROID", 4, [
        ("📱", "BlueStacks 5", "winget:BlueStack.BlueStacks", "", ""),
        ("🎮", "LDPlayer", "https://www.ldplayer.net/", "", "Mở trang tải"),
    ]),
    ("LẬP TRÌNH", 4, [
        ("🐍", "Python 3.12", "winget:Python.Python.3.12", "", ""),
        ("📝", "VS Code", "winget:Microsoft.VisualStudioCode", "", ""),
        ("🟢", "Node.js LTS", "winget:OpenJS.NodeJS.LTS", "", ""),
        ("☕", "Java JDK 21", "winget:EclipseAdoptium.Temurin.21.JDK", "", ""),
        ("🔧", "Git", "winget:Git.Git", "", ""),
    ]),
    ("THƯ VIỆN HỆ THỐNG", 4, [
        ("⚙️", "Visual C++ 2015-2022 x64", "winget:Microsoft.VCRedist.2015+.x64", "", ""),
        ("⚙️", "Visual C++ 2015-2022 x86", "winget:Microsoft.VCRedist.2015+.x86", "", ""),
        ("⚙️", ".NET Framework 3.5", "cmd:DISM /Online /Enable-Feature /FeatureName:NetFx3 /All /NoRestart", "", "Bật tính năng có sẵn của Windows (cần mạng)"),
        ("⚙️", ".NET Framework 4.8", "winget:Microsoft.DotNet.Framework.DeveloperPack_4", "", ""),
        ("🎮", "DirectX Runtime", "winget:Microsoft.DirectX", "", ""),
    ]),
]
DEFAULT_GPOS = {"ACTIVE": 1, "KHO PHẦN MỀM": 0, "TRÌNH DUYỆT WEB": 7, "HỖ TRỢ TỪ XA": 9, "ĐA PHƯƠNG TIỆN": 6, "TTS & SUB": 15, "TIỆN ÍCH": 11, "VĂN PHÒNG - PDF": 2, "ARTCRAFT OFFICE": 3, "BỘ GÕ TIẾNG VIỆT": 4, "NHẮN TIN - HỌP": 8, "NÉN - GIẢI NÉN": 5, "UNINSTALLER TOOL": 14, "GIẢ LẬP ANDROID": 12, "LẬP TRÌNH": 13, "THƯ VIỆN HỆ THỐNG": 10}     # vị trí ở kiểu Lưới
DEFAULT_FIT_N = 5

# ---------------------------------------------------------------- tiện ích Windows cố định
# (id, nhóm, nhãn, kiểu, lệnh, cần xác nhận)  kiểu: ps = PowerShell, cmd = cmd /c, open = mở chương trình
TOOLS = [
    ("ext", "THIẾT LẬP WINDOWS", "👁 Hiện đuôi file", "ps",
     "Set-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced' HideFileExt 0", ""),
    ("thispc", "THIẾT LẬP WINDOWS", "🖥 This PC ra Desktop", "ps",
     "$k='HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel'; "
     "New-Item $k -Force | Out-Null; Set-ItemProperty $k '{20D04FE0-3AEA-1069-A2D8-08002B30309D}' 0", ""),
    ("faststart", "THIẾT LẬP WINDOWS", "⚡ Tắt Fast Startup", "ps",
     "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power' HiberbootEnabled 0", ""),
    ("hiber", "THIẾT LẬP WINDOWS", "💤 Tắt ngủ đông", "cmd", "powercfg -h off", ""),
    ("tz", "THIẾT LẬP WINDOWS", "🕒 Múi giờ Việt Nam", "cmd", 'tzutil /s "SE Asia Standard Time" && w32tm /resync', ""),
    ("restart_explorer", "THIẾT LẬP WINDOWS", "🔄 Khởi động lại Explorer", "cmd", "taskkill /f /im explorer.exe & start explorer.exe", ""),
    ("arrow_off", "THIẾT LẬP WINDOWS", "🏹 Xóa mũi tên shortcut", "ps",
     "$k='HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Icons'; New-Item $k -Force | Out-Null; "
     "Set-ItemProperty $k '29' ($env:windir + '\\System32\\shell32.dll,-50'); ie4uinit.exe -show; "
     + ("Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3; "
        "if(-not (Get-Process explorer -ErrorAction SilentlyContinue)){ Start-Process explorer.exe }") + "; 'Đã xóa mũi tên trên biểu tượng shortcut'", ""),
    ("arrow_on", "THIẾT LẬP WINDOWS", "↩ Hiện lại mũi tên shortcut", "ps",
     "Remove-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Icons' '29' -ErrorAction SilentlyContinue; "
     "ie4uinit.exe -show; " + ("Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3; "
        "if(-not (Get-Process explorer -ErrorAction SilentlyContinue)){ Start-Process explorer.exe }") + "; 'Đã hiện lại mũi tên shortcut'", ""),
    ("ctx_old", "THIẾT LẬP WINDOWS", "🖱 Menu chuột phải kiểu cũ", "ps",
     "New-Item 'HKCU:\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32' -Force | Out-Null; "
     "Set-Item 'HKCU:\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32' -Value ''; "
     + ("Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3; "
        "if(-not (Get-Process explorer -ErrorAction SilentlyContinue)){ Start-Process explorer.exe }") + "; 'Đã chuyển menu chuột phải về kiểu cũ (Windows 10)'", ""),
    ("ctx_new", "THIẾT LẬP WINDOWS", "🖱 Menu chuột phải Win 11", "ps",
     "Remove-Item 'HKCU:\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}' -Recurse -Force -ErrorAction SilentlyContinue; "
     + ("Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3; "
        "if(-not (Get-Process explorer -ErrorAction SilentlyContinue)){ Start-Process explorer.exe }") + "; 'Đã trả menu chuột phải về kiểu Windows 11'", ""),

    ("def_off", "MICROSOFT DEFENDER", "⛔ Tắt Real-time Protection", "ps",
     "Set-MpPreference -DisableRealtimeMonitoring $true; Start-Sleep -Seconds 2; "
     "$s=Get-MpComputerStatus; if(-not $s.RealTimeProtectionEnabled){ 'Đã TẮT bảo vệ thời gian thực (Real-time Protection).' } "
     "elseif($s.IsTamperProtected){ throw 'Không tắt được vì Tamper Protection đang bật. Bấm \"Mở Windows Security\", tắt Tamper Protection rồi bấm lại nút này.' } "
     "else { throw 'Không tắt được (có thể bị chính sách công ty hoặc phần mềm diệt virus khác quản lý).' }",
     "Tắt bảo vệ thời gian thực của Microsoft Defender?\nWindows có thể tự bật lại sau một thời gian hoặc sau khi khởi động lại máy."),
    ("def_on", "MICROSOFT DEFENDER", "✅ Bật Real-time Protection", "ps",
     "Set-MpPreference -DisableRealtimeMonitoring $false; Start-Sleep -Seconds 2; "
     "if((Get-MpComputerStatus).RealTimeProtectionEnabled){ 'Đã BẬT lại bảo vệ thời gian thực.' } else { throw 'Chưa bật lại được, hãy bật trong Windows Security.' }", ""),
    ("def_status", "MICROSOFT DEFENDER", "🔍 Xem trạng thái Defender", "ps",
     "$s=Get-MpComputerStatus; $b={param($v) if($v){'BẬT'}else{'TẮT'}}; "
     "\"Real-time Protection : $(& $b $s.RealTimeProtectionEnabled)`nTamper Protection    : $(& $b $s.IsTamperProtected)`n"
     "Diệt virus (Antivirus): $(& $b $s.AntivirusEnabled)`nPhiên bản dữ liệu    : $($s.AntivirusSignatureVersion) ($($s.AntivirusSignatureLastUpdated))\"", ""),
    ("def_open", "MICROSOFT DEFENDER", "⚙ Mở Windows Security", "open", "windowsdefender://threatsettings", ""),

    ("upd_off", "WINDOWS UPDATE", "⛔ Tắt Windows Update", "ps",
     "Stop-Service wuauserv -Force -ErrorAction SilentlyContinue; Set-Service wuauserv -StartupType Disabled; "
     "$k='HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU'; New-Item $k -Force | Out-Null; "
     "Set-ItemProperty $k NoAutoUpdate 1", "Tắt Windows Update? (bật lại được bằng nút bên cạnh)"),
    ("upd_on", "WINDOWS UPDATE", "✅ Bật lại Windows Update", "ps",
     "Remove-ItemProperty 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU' NoAutoUpdate -ErrorAction SilentlyContinue; "
     "Set-Service wuauserv -StartupType Manual; Start-Service wuauserv", ""),
    ("upd_open", "WINDOWS UPDATE", "⚙ Mở Windows Update", "open", "ms-settings:windowsupdate", ""),

    ("dns_google", "MẠNG", "🌐 DNS Google 8.8.8.8", "ps",
     "Get-NetAdapter | Where-Object Status -eq 'Up' | Set-DnsClientServerAddress -ServerAddresses 8.8.8.8,8.8.4.4; Clear-DnsClientCache; 'Đã đặt DNS Google cho mạng đang dùng'", ""),
    ("dns_cf", "MẠNG", "🌐 DNS Cloudflare 1.1.1.1", "ps",
     "Get-NetAdapter | Where-Object Status -eq 'Up' | Set-DnsClientServerAddress -ServerAddresses 1.1.1.1,1.0.0.1; Clear-DnsClientCache; 'Đã đặt DNS Cloudflare cho mạng đang dùng'", ""),
    ("dns_auto", "MẠNG", "↺ DNS tự động (nhà mạng)", "ps",
     "Get-NetAdapter | Where-Object Status -eq 'Up' | Set-DnsClientServerAddress -ResetServerAddresses; Clear-DnsClientCache; 'Đã trả DNS về tự động'", ""),
    ("dns_flush", "MẠNG", "🧹 Xóa cache DNS", "cmd", "ipconfig /flushdns", ""),
    ("wifi_pw", "MẠNG", "🔑 Xem mật khẩu Wifi đã lưu", "fn", "wifi_passwords", ""),
    ("net_reset", "MẠNG", "🔁 Reset mạng (Winsock, TCP/IP)", "cmd", "netsh winsock reset & netsh int ip reset & ipconfig /flushdns",
     "Đặt lại toàn bộ cấu hình mạng (Winsock, TCP/IP)? Cần khởi động lại máy sau khi xong."),

    ("clean_temp", "DỌN DẸP", "🗑 Xóa file tạm", "ps",
     "$n=0; foreach($p in @($env:TEMP,'C:\\Windows\\Temp')){ Get-ChildItem $p -Force -ErrorAction SilentlyContinue | "
     "ForEach-Object { try { Remove-Item $_.FullName -Recurse -Force -ErrorAction Stop; $n++ } catch {} } }; \"Đã xóa $n mục\"", ""),
    ("recycle", "DỌN DẸP", "♻ Dọn thùng rác", "ps", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue; 'Đã dọn thùng rác'", "Xóa hết thùng rác?"),
    ("cleanmgr", "DỌN DẸP", "🧽 Disk Cleanup", "open", "cleanmgr.exe", ""),

    ("spooler", "MÁY IN", "🔁 Khởi động lại Spooler", "cmd", "net stop spooler /y & net start spooler", ""),
    ("printq", "MÁY IN", "🧾 Xóa hàng đợi in", "cmd",
     'net stop spooler /y & del /q /f /s "%systemroot%\\System32\\spool\\PRINTERS\\*" & net start spooler', ""),
    ("printers", "MÁY IN", "🖨 Máy in & thiết bị", "open", "control printers", ""),

    ("bl_status", "BITLOCKER", "🔍 Xem trạng thái", "cmd", "manage-bde -status", ""),
    ("bl_off", "BITLOCKER", "🔓 Tắt BitLocker ổ C", "cmd", "manage-bde -off C:",
     "Giải mã BitLocker ổ C? Máy sẽ giải mã ngầm, mất một lúc tùy dung lượng."),

    ("wifi_bak", "SAO LƯU - KHÔI PHỤC", "📡 Sao lưu Wifi", "fn", "wifi_backup", ""),
    ("wifi_res", "SAO LƯU - KHÔI PHỤC", "📡 Khôi phục Wifi", "fn", "wifi_restore", ""),
    ("drv_bak", "SAO LƯU - KHÔI PHỤC", "🧩 Sao lưu Driver", "fn", "driver_backup", "Sao lưu toàn bộ driver (mất vài phút)?"),
    ("drv_res", "SAO LƯU - KHÔI PHỤC", "🧩 Khôi phục Driver", "fn", "driver_restore", ""),
    ("restore_pt", "SAO LƯU - KHÔI PHỤC", "📌 Tạo điểm khôi phục", "ps",
     "Enable-ComputerRestore -Drive 'C:\\' -ErrorAction SilentlyContinue; "
     "Checkpoint-Computer -Description ('Win AIO ' + (Get-Date -Format 'dd-MM-yyyy HH:mm')) -RestorePointType MODIFY_SETTINGS; 'Đã tạo điểm khôi phục'", ""),

    ("lic", "BẢN QUYỀN (KEY CỦA BẠN)", "🔑 Xem trạng thái bản quyền", "cmd", "cscript //nologo %windir%\\System32\\slmgr.vbs /dli", ""),
    ("ipk", "BẢN QUYỀN (KEY CỦA BẠN)", "🔑 Nhập key Windows", "fn", "win_key", ""),
    ("act_open", "BẢN QUYỀN (KEY CỦA BẠN)", "⚙ Mở trang Kích hoạt", "open", "ms-settings:activation", ""),
]

QUICK = [
    ("💻 Thông tin máy", "ms-settings:about"), ("🧰 Device Manager", "devmgmt.msc"), ("💽 Disk Management", "diskmgmt.msc"),
    ("🎛 Control Panel", "control"), ("📈 Task Manager", "taskmgr"), ("🧩 Services", "services.msc"),
    ("🗝 Registry", "regedit"), ("🛡 Group Policy", "gpedit.msc"), ("📟 CMD Admin", "cmd.exe"),
    ("🔷 PowerShell Admin", "powershell.exe"), ("🌐 Kết nối mạng", "ncpa.cpl"), ("🔊 Âm thanh", "mmsys.cpl"),
    ("🧪 DxDiag", "dxdiag"), ("⚙ System Properties", "sysdm.cpl"), ("📦 Programs & Features", "appwiz.cpl"),
    ("🗓 Event Viewer", "eventvwr.msc"),
]


# ================================================================= tiện ích chung
def now():
    return dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def load_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:                       # noqa: BLE001
        return default


def save_json(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def hash_pw(pw, salt):
    return hashlib.sha256((salt + "|" + pw).encode("utf-8")).hexdigest()


def is_admin_windows():
    if not IS_WIN:
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:                       # noqa: BLE001
        return False


def clean_env():
    """Môi trường cho tiến trình mở lại chính tool (cập nhật, xin quyền Admin).
    Bỏ biến nội bộ của PyInstaller và bật PYINSTALLER_RESET_ENVIRONMENT để exe mới chạy như một bản độc lập.
    Thiếu bước này, exe mới tưởng mình là tiến trình con của bản cũ (đã thoát) và báo lỗi
    "Security validation failure: invalid originating onefile parent process (PID not found)"."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("_PYI_", "_MEI"))}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


def relaunch_as_admin():
    """Chạy lại tool bằng quyền Administrator (cài phần mềm, sửa hệ thống cần quyền này)."""
    if getattr(sys, "frozen", False):
        exe, args = sys.executable, sys.argv[1:]
    else:
        exe = sys.executable.replace("python.exe", "pythonw.exe")
        args = [str(Path(__file__).resolve())] + sys.argv[1:]
    params = subprocess.list2cmdline(args)
    os.environ.update({"PYINSTALLER_RESET_ENVIRONMENT": "1"})   # exe mở lại chạy như bản độc lập
    for k in [k for k in os.environ if k.upper().startswith(("_PYI_", "_MEI"))]:
        os.environ.pop(k, None)
    r = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, str(BASE), 1)
    return r > 32


def human(n):
    n = float(n or 0)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def src_kind(src):
    s = (src or "").strip()
    if not s:
        return "none"
    if s.lower().startswith("winget:"):
        return "winget"
    if s.lower().startswith("cmd:"):
        return "cmd"
    if s.lower().startswith("office:"):
        return "office"
    if s.lower().startswith("open:"):
        return "open"
    if s.lower().startswith(("github:", "codeberg:", "page:")):
        return "github"
    if re.match(r"^https?://", s, re.I):
        return "web"
    return "file"


def resolve_github(src):
    """github:chủ/repo|mẫu-tên-file  ->  (link tải file mới nhất, tên bản). Link không bao giờ cũ vì luôn hỏi bản mới nhất."""
    if src.lower().startswith("page:"):
        return resolve_page(src)
    site, body = src.split(":", 1)
    cb = site.strip().lower() == "codeberg"
    repo, _, pat = body.strip().partition("|")
    repo, _, tag = repo.strip().strip("/").partition("@")      # github:chủ/repo@tên-bản|mẫu -> lấy trong bản phát hành cố định
    host = "Codeberg" if cb else "GitHub"
    if FAKE:
        return f"https://{host.lower()}.org/{repo}/releases/download/v9.9.9/demo-windows-x64.zip", "v9.9.9"
    import requests
    hdr = {"User-Agent": "WinAIO", "Accept": "application/vnd.github+json"}
    if os.environ.get("GH_TOKEN"):
        hdr["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    api = "https://codeberg.org/api/v1" if cb else "https://api.github.com"
    if cb:
        hdr = {"User-Agent": "WinAIO", "Accept": "application/json"}
    r = requests.get(f"{api}/repos/{repo}/releases/" + (f"tags/{tag}" if tag else "latest"), headers=hdr, timeout=20)
    if r.status_code == 404 and cb:          # Codeberg chưa có "bản phát hành" -> tìm file trong kho mã nguồn
        return _forge_tree_file(api, repo, pat, hdr)
    if r.status_code == 404:
        raise RuntimeError(f"Không thấy bản phát hành nào của {repo} trên {host}.")
    if r.status_code == 403:
        raise RuntimeError("GitHub tạm chặn vì hỏi quá nhiều lần (60 lần / giờ) - đợi ít phút rồi thử lại.")
    r.raise_for_status()
    js = r.json()
    assets = js.get("assets") or []
    rx = re.compile(pat.strip() or r"\.(exe|msi|zip)$", re.I)
    hits = [a for a in assets if rx.search(a.get("name", ""))]
    if "portable" in pat.lower():        # mẫu có chữ portable -> ưu tiên file portable
        hits.sort(key=lambda a: "portable" not in a.get("name", "").lower())
    if tag and hits:                     # bản phát hành chứa nhiều phiên bản -> lấy số phiên bản lớn nhất
        a = max(hits, key=lambda a: [int(x) for x in re.findall(r"\d+", a["name"])])
        return a["browser_download_url"], ".".join(re.findall(r"\d+", a["name"]))
    for a in hits:
        return a["browser_download_url"], js.get("tag_name", "")
    raise RuntimeError(f"Bản {js.get('tag_name', '')} của {repo} không có file khớp mẫu '{pat}'. "
                       "Admin bấm ✎ để sửa mẫu tên file.")


def resolve_page(src):
    """page:https://trang-tải|mẫu-link  ->  đọc trang chủ của hãng, lấy link tải có số phiên bản lớn nhất (khi hãng đổi bản là có link mới)."""
    body = src.split(":", 1)[1].strip()
    url, _, pat = body.partition("|")
    if FAKE:
        return "https://dl.example.com/demo_v9.9.9_Setup_x64.exe", "9.9.9"
    import requests
    r = requests.get(url.strip(), timeout=20, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130"})
    r.raise_for_status()
    rx = re.compile(pat.strip() or r"https?://[^\"'\s<>]+\.exe", re.I)
    links = sorted({m.group(0) for m in rx.finditer(r.text)})
    if not links:
        raise RuntimeError(f"Trang {url} không còn link tải khớp mẫu - Admin bấm ✎ để sửa.")
    best = max(links, key=lambda u: [int(x) for x in re.findall(r"\d+", u.rsplit("/", 1)[-1])] or [0])
    mv = re.search(r"[vV]?(\d+(?:\.\d+)+)", best.rsplit("/", 1)[-1])
    return best, mv.group(1) if mv else ""


def _forge_tree_file(api, repo, pat, hdr):
    """Kho Codeberg không dùng mục Releases mà để thẳng file exe/zip trong mã nguồn: lấy file khớp mẫu, số phiên bản lớn nhất."""
    import requests
    info = requests.get(f"{api}/repos/{repo}", headers=hdr, timeout=20)
    if info.status_code == 404:
        raise RuntimeError(f"Không thấy kho {repo} trên Codeberg.")
    br = info.json().get("default_branch") or "main"
    t = requests.get(f"{api}/repos/{repo}/git/trees/{br}?recursive=true&per_page=1000", headers=hdr, timeout=20).json()
    rx = re.compile(pat.strip() or r"\.(exe|zip)$", re.I)
    files = [x["path"] for x in t.get("tree") or [] if x.get("type") == "blob" and rx.search(x["path"].rsplit("/", 1)[-1])]
    if not files:
        raise RuntimeError(f"Kho {repo} không có file khớp mẫu '{pat}'.")
    if "portable" in pat.lower():
        files.sort(key=lambda f: "portable" not in f.lower())
        files = [f for f in files if "portable" in f.lower()] or files
    best = max(files, key=lambda f: [int(x) for x in re.findall(r"\d+", f.rsplit("/", 1)[-1])] or [0])
    from urllib.parse import quote
    mv = re.search(r"[vV](\d+(?:\.\d+)*)", best.rsplit("/", 1)[-1])
    return f"https://codeberg.org/{repo}/raw/branch/{br}/{quote(best)}", (mv.group(1) if mv else br)


def _rar_selftest():
    """Selftest: tải file .rar của Codeberg, giải nén thử (tar.exe / 7-Zip), liệt kê exe bên trong."""
    import requests
    import tempfile
    out = []
    for a in UNINSTALLER[1][:2]:
        url, ver = resolve_github(a[2])
        d = Path(tempfile.mkdtemp())
        f = d / url.rsplit("/", 1)[-1]
        f.write_bytes(requests.get(url, timeout=120).content)
        ok = Engine._unarchive(f, d / "x", "123")
        tc, to = run_hidden(["tar", "-xf", str(f), "-C", str(d)], timeout=300)
        out.append([a[1], url, f.stat().st_size, ok, [x.name for x in (d / "x").rglob("*.exe")] if ok else [], "tar", tc, to[-120:]])
    return out


def _try(f):
    try:
        return f()
    except Exception as e:                  # noqa: BLE001
        return "LỖI: " + str(e)[:200]


def _assets(src):
    """Selftest: tên các file trong bản phát hành mới nhất (để chỉnh mẫu tên file)."""
    import requests
    site, repo = src.split(":", 1)
    api = "https://codeberg.org/api/v1" if site == "codeberg" else "https://api.github.com"
    try:
        if site == "codeberg":
            br = requests.get(f"{api}/repos/{repo}", timeout=20).json().get("default_branch")
            t = requests.get(f"{api}/repos/{repo}/git/trees/{br}?recursive=true", timeout=20).json()
            return [repo, br, [(x["path"], x.get("size")) for x in t.get("tree") or [] if x.get("type") == "blob"][:40]]
        js = requests.get(f"{api}/repos/{repo}/releases/latest", timeout=20, headers={"User-Agent": "WinAIO"}).json()
        return [repo, js.get("tag_name"), [a.get("name") for a in js.get("assets") or []]]
    except Exception as e:                  # noqa: BLE001
        return [repo, "LỖI " + str(e)[:150]]


def requests_head(url):
    """Selftest: link còn sống không (mã HTTP, dung lượng)."""
    import requests
    r = requests.head(url, allow_redirects=True, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    return r.status_code, int(r.headers.get("Content-Length") or 0)


def run_hidden(cmd, shell=False, timeout=None):
    """Chạy lệnh không hiện cửa sổ, trả (mã thoát, chữ in ra)."""
    if FAKE:
        time.sleep(0.6)
        return 0, f"(chạy thử) {cmd if isinstance(cmd, str) else ' '.join(cmd)}"
    p = subprocess.run(cmd, shell=shell, capture_output=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)
    raw = (p.stdout or b"") + (p.stderr or b"")
    for enc in ("utf-8", "cp1258", "cp437"):
        try:
            out = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        out = raw.decode("utf-8", "replace")
    return p.returncode, out.strip()


def ps(script, timeout=600):
    full = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; $ProgressPreference='SilentlyContinue'; "
            "$ErrorActionPreference='Stop'; " + script)
    import base64                            # gửi lệnh dạng mã hóa: không lỗi dấu ngoặc kép, ký tự tiếng Việt
    enc = base64.b64encode(full.encode("utf-16-le")).decode("ascii")
    code, out = run_hidden(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc],
                           timeout=timeout)
    return code, _clixml(out)


def _clixml(out):
    """-EncodedCommand trả lỗi / tiến độ dạng XML (#< CLIXML): bỏ phần đó, chỉ giữ câu báo lỗi."""
    if "#< CLIXML" not in (out or ""):
        return out
    import html
    head, _, xml = out.partition("#< CLIXML")
    msg = "".join(re.findall(r'<S S="Error">(.*?)</S>', xml, re.S))
    msg = html.unescape(msg.replace("_x000D_", "").replace("_x000A_", "\n")).strip()
    return (head.strip() + ("\n" + msg if msg else "")).strip()


def open_target(t):
    if FAKE or not IS_WIN:
        return
    os.startfile(t)                          # noqa: S606


# ================================================================= dữ liệu (SQLite + config.json)
class Store:
    """Dữ liệu nằm trong bộ nhớ cho tới khi cần lưu (tải app, sửa nút, đổi cài đặt, sao lưu).
    Lúc đó mới tạo thư mục Data kế bên file exe -> chỉ chép 1 file exe đi là dùng được."""

    def __init__(self):
        self.lock = threading.RLock()
        self.on_disk = DB_FILE.exists() or CONFIG_FILE.exists() or OLD_JSON.exists()
        self.cfg = dict(DEFAULT_CONFIG)
        self.cfg.update(load_json(CONFIG_FILE, {}))
        if not self.cfg.get("admin_hash"):
            self.cfg["admin_salt"] = secrets.token_hex(8)
            self.cfg["admin_hash"] = hash_pw(DEFAULT_PW, self.cfg["admin_salt"])
        elif self.cfg["admin_hash"] == hash_pw("admin", self.cfg.get("admin_salt", "")):
            self.cfg["admin_hash"] = hash_pw(DEFAULT_PW, self.cfg["admin_salt"])   # mật khẩu mặc định cũ "admin" -> HP360
            self._pw_migrated = True
        if self.on_disk:
            DATA.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(DB_FILE) if self.on_disk else ":memory:", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS groups(id INTEGER PRIMARY KEY, name TEXT, ord INTEGER, col INTEGER, gpos INTEGER);
            CREATE TABLE IF NOT EXISTS weblinks(id INTEGER PRIMARY KEY, grp TEXT, icon TEXT, name TEXT, url TEXT, ord INTEGER);
            CREATE TABLE IF NOT EXISTS presets(id INTEGER PRIMARY KEY, name TEXT, icon TEXT, apps TEXT, tools TEXT, opts TEXT, ord INTEGER);
            CREATE TABLE IF NOT EXISTS winget_info(pkg TEXT PRIMARY KEY, ok INTEGER, ver TEXT, url TEXT, pname TEXT, checked REAL);
            CREATE TABLE IF NOT EXISTS apps(id INTEGER PRIMARY KEY, group_id INTEGER, icon TEXT, name TEXT,
                src TEXT, args TEXT, note TEXT, ord INTEGER);
            CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, ts TEXT, name TEXT, src TEXT,
                status TEXT, detail TEXT);
        """)
        cols_ = [r[1] for r in self.db.execute("PRAGMA table_info(groups)")]
        if "col" not in cols_:
            self.db.execute("ALTER TABLE groups ADD COLUMN col INTEGER")     # dữ liệu bản cũ: thêm cột "col"
        if "gpos" not in cols_:
            self.db.execute("ALTER TABLE groups ADD COLUMN gpos INTEGER")    # vị trí trong kiểu xếp Lưới
        self.db.commit()
        if self.on_disk:
            self.save_config()
        if OLD_JSON.exists():
            self._import_old_json()
        if not self.db.execute("SELECT COUNT(*) FROM groups").fetchone()[0]:
            self.load_defaults(persist=False)
        self._migrate()
        if self.db.execute("SELECT 1 FROM groups WHERE col IS NULL").fetchone():
            self.auto_columns()
            self.commit(persist=False)
        if self.db.execute("SELECT 1 FROM groups WHERE gpos IS NULL").fetchone():
            self.grid_from_columns()
            self.commit(persist=False)

    def layout(self):
        """fit = tự vừa màn hình (mặc định từ v2.1.1), grid = lưới thẳng hàng, columns = cột dọc."""
        if not self.cfg.get("layout_v211"):
            return "fit"
        v = self.cfg.get("layout")
        return v if v in ("fit", "grid", "columns") else "fit"

    def grid_from_columns(self):
        """Vị trí Lưới = thứ tự đọc từ trái sang phải, trên xuống dưới của kiểu cột dọc."""
        with self.lock:
            ids = [r[0] for r in self.db.execute("SELECT id FROM groups ORDER BY ord, COALESCE(col, 0), id")]
            for k, x in enumerate(ids):
                self.db.execute("UPDATE groups SET gpos=? WHERE id=?", (k, x))

    def columns(self):
        try:
            if self.layout() == "fit" and self.cfg.get("fit_n"):
                return max(1, min(10, int(self.cfg["fit_n"])))
            return max(2, min(6, int(self.cfg.get("columns", 4))))
        except (TypeError, ValueError):
            return 4

    def auto_columns(self, all_groups=False):
        """Xếp nhóm vào các cột dọc: theo thứ tự cũ, mỗi nhóm vào cột đang ngắn nhất (giống lưới hiện ra trên màn hình)."""
        n = self.columns()
        with self.lock:
            order = "g.ord, COALESCE(g.col, 0), g.id" if all_groups else "COALESCE(g.col, 99), g.ord, g.id"
            rows = self.db.execute("SELECT g.id, g.col, (SELECT COUNT(*) FROM apps a WHERE a.group_id=g.id) FROM groups g "
                                   "ORDER BY " + order).fetchall()
            height = [0.0] * n
            cnt = [0] * n
            for gid, col, napps in rows:
                if all_groups or col is None:
                    c = min(range(n), key=lambda i: (height[i], i))
                else:
                    c = min(int(col), n - 1)
                self.db.execute("UPDATE groups SET col=?, ord=? WHERE id=?", (c, cnt[c], gid))
                cnt[c] += 1
                height[c] += 2.2 + napps          # đầu nhóm + số nút

    def _migrate(self):
        """Dữ liệu từ bản cũ: thêm nút mới của phiên bản này (chỉ 1 lần, không đụng nút đã sửa)."""
        done = set(self.cfg.get("migrated") or [])
        self.fix_dead_links()
        if getattr(self, "_pw_migrated", False):
            self.save_config(persist=False)
        if "notes217" not in done:
            self.db.execute("UPDATE apps SET note='' WHERE src LIKE 'winget:%' AND note IN "
                            "('Bản portable, giải nén rồi chạy', 'Mở trang tải EVKey', 'Mở trang tải')")
            self.commit(persist=False)
            done.add("notes217")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "web" not in done:
            if not self.db.execute("SELECT 1 FROM weblinks").fetchone():
                for i, (g, ic, n, u) in enumerate(DEFAULT_WEB):
                    self.db.execute("INSERT INTO weblinks(grp, icon, name, url, ord) VALUES(?,?,?,?,?)", (g, ic, n, u, i))
                self.commit(persist=False)
            done.add("web")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "presets" not in done:
            if not self.db.execute("SELECT 1 FROM presets").fetchone():
                for i, (n, ic, apps, tools, opts) in enumerate(DEFAULT_PRESETS):
                    self.db.execute("INSERT INTO presets(name, icon, apps, tools, opts, ord) VALUES(?,?,?,?,?,?)",
                                    (n, ic, json.dumps(apps, ensure_ascii=False), json.dumps(tools), json.dumps(opts), i))
                self.commit(persist=False)
            done.add("presets")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "v32" not in done:
            has = lambda src: self.db.execute("SELECT 1 FROM apps WHERE src=?", (src,)).fetchone()     # noqa: E731
            if not any(has(a[2]) for a in UNINSTALLER[1] if a is not HIBIT):
                pos = self.db.execute("SELECT COALESCE(MAX(gpos),0)+1, COALESCE(MAX(ord),0)+1 FROM groups").fetchone()
                col = self.db.execute("SELECT col FROM groups GROUP BY col ORDER BY COUNT(*), col LIMIT 1").fetchone()
                gid = self.db.execute("INSERT INTO groups(name, ord, col, gpos) VALUES(?,?,?,?)",
                                      (UNINSTALLER[0], pos[1], col[0] if col else 0, pos[0])).lastrowid
                for i, a in enumerate(UNINSTALLER[1]):
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)", (gid,) + a + (i,))
            if not has(PICVIEW[2]):
                g = self.db.execute("SELECT id FROM groups WHERE name LIKE 'ĐA PHƯƠNG TIỆN%' ORDER BY id LIMIT 1").fetchone()
                if g:
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)", (g[0],) + PICVIEW + (-1,))
            self.commit(persist=False)
            done.add("v32")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "v40" not in done:
            # nhóm TTS & SUB: đặt ngay dưới nhóm TIỆN ÍCH, chuyển CIT Voice / Subtitle Translator sang, thêm LaziBook, VieNeu-TTS
            if not self.db.execute("SELECT 1 FROM groups WHERE name=?", (TTS_SUB[0],)).fetchone():
                ti = self.db.execute("SELECT col, ord FROM groups WHERE name LIKE 'TIỆN ÍCH%' ORDER BY id LIMIT 1").fetchone()
                col, o = (ti[0], ti[1] + 1) if ti else (self.db.execute("SELECT COALESCE(MAX(col),0) FROM groups").fetchone()[0], 999)
                self.db.execute("UPDATE groups SET ord=ord+1 WHERE col=? AND ord>=?", (col, o))
                gp = self.db.execute("SELECT COALESCE(MAX(gpos),0)+1 FROM groups").fetchone()[0]
                gid = self.db.execute("INSERT INTO groups(name, ord, col, gpos) VALUES(?,?,?,?)", (TTS_SUB[0], o, col, gp)).lastrowid
                for i, a in enumerate(TTS_SUB[1]):
                    if self.db.execute("SELECT 1 FROM apps WHERE src=?", (a[2],)).fetchone():
                        self.db.execute("UPDATE apps SET group_id=?, ord=? WHERE src=?", (gid, i, a[2]))
                    else:
                        self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)", (gid,) + a + (i,))
                self.commit(persist=False)
            done.add("v40")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "v39" not in done:
            if not self.db.execute("SELECT 1 FROM apps WHERE src=?", (TRANSUB[2],)).fetchone():
                g = self.db.execute("SELECT id FROM groups WHERE name LIKE 'ĐA PHƯƠNG TIỆN%' ORDER BY id LIMIT 1").fetchone()
                if g:
                    o = self.db.execute("SELECT COALESCE(MAX(ord),0)+1 FROM apps WHERE group_id=?", (g[0],)).fetchone()[0]
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)", (g[0],) + TRANSUB + (o,))
                    self.commit(persist=False)
            done.add("v39")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "v36" not in done:
            # 3uTools chuyển sang tab Kho iOS; HiBit Uninstaller về nhóm UNINSTALLER TOOL
            self.db.execute("DELETE FROM apps WHERE src=?", (TOOLS_3U[2],))
            g = self.db.execute("SELECT id FROM groups WHERE name=? ORDER BY id LIMIT 1", (UNINSTALLER[0],)).fetchone()
            if g:
                if self.db.execute("SELECT 1 FROM apps WHERE group_id=? AND src=?", (g[0], HIBIT[2])).fetchone():
                    self.db.execute("DELETE FROM apps WHERE src=? AND group_id<>?", (HIBIT[2], g[0]))
                else:
                    self.db.execute("UPDATE apps SET group_id=?, ord=-1 WHERE src=?", (g[0], HIBIT[2]))
            self.commit(persist=False)
            done.update({"v35", "v36"})
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "v31" not in done:
            if not self.db.execute("SELECT 1 FROM apps WHERE src=?", (VANPHONG[2],)).fetchone():
                g = self.db.execute("SELECT group_id FROM apps WHERE src LIKE 'office:%' LIMIT 1").fetchone() or \
                    self.db.execute("SELECT id FROM groups WHERE name LIKE 'VĂN PHÒNG%' ORDER BY id LIMIT 1").fetchone()
                if g:
                    o = self.db.execute("SELECT COALESCE(MAX(ord),0)+1 FROM apps WHERE group_id=?", (g[0],)).fetchone()[0]
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)", (g[0],) + VANPHONG + (o,))
                    self.commit(persist=False)
            done.add("v31")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "v28" not in done:
            if not self.db.execute("SELECT 1 FROM apps WHERE src=?", (CAIWINDAO[2],)).fetchone():
                g = self.db.execute("SELECT id FROM groups WHERE name LIKE 'TIỆN ÍCH%' ORDER BY id LIMIT 1").fetchone()
                if g:
                    o = self.db.execute("SELECT COALESCE(MAX(ord),0)+1 FROM apps WHERE group_id=?", (g[0],)).fetchone()[0]
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)", (g[0],) + CAIWINDAO + (o,))
                    self.commit(persist=False)
            done.add("v28")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "v223" not in done:
            if not self.db.execute("SELECT 1 FROM apps WHERE src=?", (ONLYOFFICE[2],)).fetchone():
                g = self.db.execute("SELECT id FROM groups WHERE name LIKE 'VĂN PHÒNG%' ORDER BY id LIMIT 1").fetchone()
                if g:
                    o = self.db.execute("SELECT COALESCE(MAX(ord),0)+1 FROM apps WHERE group_id=?", (g[0],)).fetchone()[0]
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)",
                                    (g[0],) + ONLYOFFICE + (o,))
                    self.commit(persist=False)
            done.add("v223")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "v219" not in done:
            def has(src):
                return self.db.execute("SELECT 1 FROM apps WHERE src=?", (src,)).fetchone()
            if not has(WHATSAPP[2]):
                g = self.db.execute("SELECT id FROM groups WHERE name LIKE 'NHẮN TIN%' ORDER BY id LIMIT 1").fetchone()
                if g:
                    o = self.db.execute("SELECT COALESCE(MAX(ord),0)+1 FROM apps WHERE group_id=?", (g[0],)).fetchone()[0]
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)",
                                    (g[0],) + WHATSAPP + (o,))
            if not any(has(a[2]) for a in ARTCRAFT[1]):
                pos = self.db.execute("SELECT COALESCE(MAX(gpos),0)+1, COALESCE(MAX(ord),0)+1 FROM groups").fetchone()
                gid = self.db.execute("INSERT INTO groups(name, ord, col, gpos) VALUES(?,?,?,?)", (ARTCRAFT[0], pos[1], 0, pos[0])).lastrowid
                for i, a in enumerate(ARTCRAFT[1]):
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)", (gid,) + a + (i,))
            self.commit(persist=False)
            done.add("v219")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "kho" not in done:
            if not self.db.execute("SELECT 1 FROM apps WHERE src LIKE 'open:%fshare.vn%' OR src LIKE 'open:%drive.google.com%'").fetchone():
                self.db.execute("UPDATE groups SET gpos=COALESCE(gpos,0)+1")
                self.db.execute("UPDATE groups SET ord=ord+1 WHERE col=0")
                gid = self.db.execute("INSERT INTO groups(name, ord, col, gpos) VALUES(?,?,?,?)", ("KHO PHẦN MỀM", 0, 0, 0)).lastrowid
                kho = next(g[2] for g in DEFAULT_GROUPS if g[0] == "KHO PHẦN MỀM")
                for i, (icon, name, src, args, note) in enumerate(kho):
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)",
                                    (gid, icon, name, src, args, note, i))
                self.commit(persist=False)
            done.add("kho")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)
        if "office" not in done:
            if not self.db.execute("SELECT 1 FROM apps WHERE src LIKE 'office:%'").fetchone():
                g = (self.db.execute("SELECT id FROM groups WHERE name LIKE '%VĂN PHÒNG%' ORDER BY ord LIMIT 1").fetchone()
                     or self.db.execute("SELECT id FROM groups ORDER BY ord LIMIT 1").fetchone())
                if g:
                    self.db.execute("UPDATE apps SET ord=ord+1 WHERE group_id=?", (g[0],))
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,0)",
                                    (g[0], "🏢", "MS Office", "office:", "", "Cài Office 2016 / 2019 / 2021 / 2024 / 365 chính chủ từ Microsoft (Online hoặc Offline)"))
                    self.commit(persist=False)
            done.add("office")
            self.cfg["migrated"] = sorted(done)
            self.save_config(persist=False)

    def fix_dead_links(self):
        with self.lock:
            n = 0
            for aid, src in self.db.execute("SELECT id, src FROM apps").fetchall():
                new = fix_src(src)
                if new != src:            # đổi sang winget -> bỏ tham số cài cũ (/S, /quiet...) vì winget tự cài im lặng
                    self.db.execute("UPDATE apps SET src=?, args='' WHERE id=?", (new, aid))
                    n += 1
            if n:
                self.commit(persist=self.on_disk)
            return n

    def ensure_disk(self):
        """Tạo thư mục Data + chép dữ liệu đang ở bộ nhớ xuống file (chỉ 1 lần)."""
        with self.lock:
            if self.on_disk:
                return
            DATA.mkdir(parents=True, exist_ok=True)
            disk = sqlite3.connect(str(DB_FILE), check_same_thread=False)
            self.db.commit()
            self.db.backup(disk)
            self.db.close()
            disk.row_factory = sqlite3.Row
            self.db = disk
            self.on_disk = True
            save_json(CONFIG_FILE, self.cfg)

    def commit(self, persist=True):
        with self.lock:
            if persist:
                self.ensure_disk()
            self.db.commit()

    def save_config(self, persist=True):
        if persist:
            self.ensure_disk()
        if self.on_disk:
            save_json(CONFIG_FILE, self.cfg)

    # ---- nhập file JSON cũ (bản xuất / dữ liệu cũ), giữ bản sao
    def _import_old_json(self):
        data = load_json(OLD_JSON, None)
        if isinstance(data, dict) and isinstance(data.get("groups"), list):
            self.import_data(data)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(OLD_JSON), str(BACKUP_DIR / f"apps_da_nhap_{dt.datetime.now():%Y%m%d_%H%M%S}.json"))

    def load_defaults(self, persist=True):
        with self.lock:
            self.db.execute("DELETE FROM apps")
            self.db.execute("DELETE FROM groups")
            per_col = {}
            for gi, (gname, col, apps) in enumerate(DEFAULT_GROUPS):
                o = per_col.get(col, 0)
                per_col[col] = o + 1
                gid = self.db.execute("INSERT INTO groups(name, ord, col, gpos) VALUES(?,?,?,?)",
                                      (gname, o, col, DEFAULT_GPOS.get(gname, gi))).lastrowid
                for ai, (icon, name, src, args, note) in enumerate(apps):
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)",
                                    (gid, icon, name, src, args, note, ai))
            self.cfg["fit_n"] = DEFAULT_FIT_N          # Tự vừa màn hình: 5 cột như cách đã sắp
            self.commit(persist)

    def export_data(self):
        out = []
        for g in self.groups():
            out.append({"name": g["name"], "col": g.get("col"), "pos": g.get("gpos"), "apps": [{k: a[k] for k in ("icon", "name", "src", "args", "note")} for a in g["apps"]]})
        web = [{k: w[k] for k in ("grp", "icon", "name", "url")} for w in self.web_list()]
        pre = [{k: p[k] for k in ("name", "icon", "apps", "tools", "opts")} for p in self.preset_list()]
        return {"app": APP_TITLE, "version": APP_VERSION, "exported": now(), "groups": out, "web": web, "presets": pre}

    def web_list(self):
        with self.lock:
            return [dict(r) for r in self.db.execute("SELECT * FROM weblinks ORDER BY ord, id")]

    def preset_list(self):
        out = []
        with self.lock:
            for r in self.db.execute("SELECT * FROM presets ORDER BY ord, id"):
                d = dict(r)
                for k, dflt in (("apps", []), ("tools", []), ("opts", {})):
                    try:
                        d[k] = json.loads(d[k] or "null") or dflt
                    except ValueError:
                        d[k] = dflt
                out.append(d)
        return out

    def import_data(self, data):
        with self.lock:
            if isinstance(data.get("presets"), list):
                self.db.execute("DELETE FROM presets")
                for i, p in enumerate(data["presets"]):
                    self.db.execute("INSERT INTO presets(name, icon, apps, tools, opts, ord) VALUES(?,?,?,?,?,?)",
                                    (str(p.get("name", "Hồ sơ")), str(p.get("icon", "📋")), json.dumps(p.get("apps") or [], ensure_ascii=False),
                                     json.dumps(p.get("tools") or []), json.dumps(p.get("opts") or {}), i))
            if isinstance(data.get("web"), list):
                self.db.execute("DELETE FROM weblinks")
                for i, w in enumerate(data["web"]):
                    self.db.execute("INSERT INTO weblinks(grp, icon, name, url, ord) VALUES(?,?,?,?,?)",
                                    (str(w.get("grp", "")), str(w.get("icon", "")), str(w.get("name", "")), str(w.get("url", "")), i))
            self.db.execute("DELETE FROM apps")
            self.db.execute("DELETE FROM groups")
            for gi, g in enumerate(data.get("groups") or []):
                col = g.get("col")
                pos = g.get("pos")
                gid = self.db.execute("INSERT INTO groups(name, ord, col, gpos) VALUES(?,?,?,?)",
                                      (str(g.get("name", "NHÓM")), gi, int(col) if isinstance(col, int) else None,
                                       int(pos) if isinstance(pos, int) else gi)).lastrowid
                for ai, a in enumerate(g.get("apps") or []):
                    self.db.execute("INSERT INTO apps(group_id, icon, name, src, args, note, ord) VALUES(?,?,?,?,?,?,?)",
                                    (gid, a.get("icon", ""), a.get("name", "Nút mới"), fix_src(a.get("src", "")), a.get("args", ""),
                                     a.get("note", ""), ai))
            self.auto_columns()
            self.commit()

    def groups(self):
        with self.lock:
            order = "gpos, id" if self.layout() == "grid" else "col, ord, id"
            gs = [dict(r) for r in self.db.execute("SELECT * FROM groups ORDER BY " + order)]
            apps = [dict(r) for r in self.db.execute("SELECT * FROM apps ORDER BY ord, id")]
            wi = {r["pkg"].lower(): dict(r) for r in self.db.execute("SELECT * FROM winget_info")}
        for g in gs:
            g["apps"] = []
            for a in apps:
                if a["group_id"] != g["id"]:
                    continue
                a = dict(a, kind=src_kind(a["src"]))
                if a["kind"] == "winget":
                    w = wi.get(a["src"].split(":", 1)[1].strip().lower())
                    if w:
                        a["wg"] = {"ok": w["ok"], "ver": w["ver"] or ""}
                g["apps"].append(a)
        return gs

    def wg_get(self, pkg):
        with self.lock:
            r = self.db.execute("SELECT * FROM winget_info WHERE pkg=? COLLATE NOCASE", (pkg,)).fetchone()
        return dict(r) if r else None

    def wg_put(self, pkg, ok, ver="", url="", pname=""):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO winget_info(pkg, ok, ver, url, pname, checked) VALUES(?,?,?,?,?,?)",
                            (pkg, int(ok), ver, url, pname, time.time()))
            self.commit(persist=self.on_disk)

    def app(self, aid):
        with self.lock:
            r = self.db.execute("SELECT * FROM apps WHERE id=?", (aid,)).fetchone()
        return dict(r) if r else None

    def add_history(self, name, src, status, detail=""):
        with self.lock:
            self.db.execute("INSERT INTO history(ts, name, src, status, detail) VALUES(?,?,?,?,?)",
                            (now(), name, src, status, detail[:2000]))
            self.commit(persist=False)
            self.hist_ver = getattr(self, "hist_ver", 0) + 1


# ================================================================= bộ máy cài đặt
class Engine:
    def __init__(self, store):
        self.st = store
        self.logs = []                     # (seq, giờ, chữ, loại)
        self.seq = 0
        self.queue = []                    # id app đang chờ
        self.cur = None                    # {"id","name","phase","pct","done","total","speed"}
        self.batch_n = 0
        self.batch_i = 0
        self.stop_flag = threading.Event()
        self.worker = None
        self.busy_tool = ""
        self.results = {}                  # id app -> ok / err / run
        self.sysinfo = None
        self.checks = {"admin": is_admin_windows() or FAKE, "net": None, "winget": None}
        self.lock = threading.RLock()
        self.winget = {"state": "check", "cur": "", "latest": ""}
        self.wg_ready = threading.Event()
        self.wg_ready.set()
        self.power = Power(self)
        self.office = OfficeSetup(self)
        mgr.init(ps=ps, run=run_hidden, fake=FAKE, base=BASE, data=DATA, ensure_disk=store.ensure_disk, log=self.log, live=self.live, gh=resolve_github, odt=self.office._setup_exe, src3u=TOOLS_3U[2],
                 history=lambda n, src, st, d="": store.add_history(n, src, st, d or ""))
        threading.Thread(target=self._bg_checks, daemon=True).start()

    # ---- nhật ký
    def log(self, text, kind=""):
        with self.lock:
            self.seq += 1
            self.logs.append((self.seq, dt.datetime.now().strftime("%H:%M:%S"), str(text), kind))
            del self.logs[:-600]

    # ---- kiểm tra nền: mạng, winget, thông tin máy
    def _bg_checks(self):
        try:
            import requests
            requests.head("https://www.microsoft.com", timeout=6)
            self.checks["net"] = True
        except Exception:                   # noqa: BLE001
            self.checks["net"] = FAKE
        if FAKE:
            self.checks["winget"] = True
        elif IS_WIN:
            self.checks["winget"] = shutil.which("winget") is not None
        else:
            self.checks["winget"] = False
        threading.Thread(target=self.winget_auto_update, daemon=True).start()
        self.sysinfo = self._read_sysinfo()

    FAKE_SYSINFO = {
        "pc": {"name": "DUYANH-PC", "user": "DUYANH-PC\\duyanh", "maker": "Dell Inc.", "model": "OptiPlex 7090", "tag": "7XK2F93", "type": "Desktop"},
        "os": {"name": "Windows 11 Pro", "ver": "24H2", "build": "26100.2314", "arch": "64-bit", "installed": "12/03/2025",
               "boot": "19/11/2026 08:02", "license": "Đã kích hoạt", "bitlocker": "Tắt"},
        "cpu": {"name": "Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz", "cores": 8, "threads": 16, "mhz": 4800, "socket": "LGA1200"},
        "ram": {"total": 32, "type": "DDR4", "speed": 2933, "slots": 4,
                "sticks": [{"size": 16, "slot": "DIMM1", "maker": "Samsung"}, {"size": 16, "slot": "DIMM2", "maker": "Samsung"}]},
        "gpu": [{"name": "NVIDIA GeForce RTX 3060", "vram": 12, "res": "2560×1440", "hz": 144, "driver": "32.0.15.6614"},
                {"name": "Intel(R) UHD Graphics 630", "vram": 1, "res": "", "hz": 0, "driver": "31.0.101.2125"}],
        "disks": [{"name": "Samsung SSD 980 PRO 1TB", "bus": "NVMe", "media": "SSD", "size": 1000, "health": "Tốt"},
                  {"name": "WDC WD20EZBX-00AYRA0", "bus": "SATA", "media": "HDD", "size": 2000, "health": "Tốt"}],
        "vols": [{"l": "C", "label": "Windows", "fs": "NTFS", "size": 476.3, "free": 120.5},
                 {"l": "D", "label": "Data", "fs": "NTFS", "size": 931.5, "free": 800.1}],
        "board": {"maker": "Dell Inc.", "product": "0K6CM1", "bios": "Dell Inc. 1.21.0", "bios_date": "12/03/2024",
                  "mode": "UEFI", "secure": "Bật", "tpm": "2.0"},
        "net": [{"name": "Ethernet", "desc": "Intel(R) Ethernet Connection (11) I219-LM", "ip": "192.168.1.25",
                 "mac": "A4-BB-6D-12-34-56", "speed": "1 Gbps"}],
    }

    def _read_sysinfo(self):
        if not IS_WIN or FAKE:
            return json.loads(json.dumps(self.FAKE_SYSINFO))
        script = r"""
$ErrorActionPreference='SilentlyContinue'
function Q($c,$ns='root\cimv2'){ try { @(Get-CimInstance -Namespace $ns -Query $c -ErrorAction Stop) } catch { @() } }
function E($v,$m){ if($null -eq $v){ return '' }; $t=[string]$v; if($t -match '^\d+$'){ $r=$m[[int]$t]; if($r){ $r } else { '' } } else { $t } }
function D($d){ if($d){ try { ([datetime]$d).ToString('dd/MM/yyyy') } catch { '' } } else { '' } }
$cs=Q 'SELECT Manufacturer, Model, TotalPhysicalMemory FROM Win32_ComputerSystem' | Select-Object -First 1
$os=Q 'SELECT Caption, BuildNumber, InstallDate, LastBootUpTime, OSArchitecture FROM Win32_OperatingSystem' | Select-Object -First 1
$bios=Q 'SELECT SerialNumber, SMBIOSBIOSVersion, ReleaseDate, Manufacturer FROM Win32_BIOS' | Select-Object -First 1
$bb=Q 'SELECT Manufacturer, Product FROM Win32_BaseBoard' | Select-Object -First 1
$enc=Q 'SELECT ChassisTypes FROM Win32_SystemEnclosure' | Select-Object -First 1
$ver=Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$wn=($os.Caption -replace '^Microsoft ','').Trim(); if([int]$ver.CurrentBuild -ge 22000){ $wn=$wn -replace 'Windows 10','Windows 11' }
$tag=[string]$bios.SerialNumber; if($tag -match '^(to be filled.*|default string|system serial number|none|not applicable|o\.e\.m\.|0+)?$'){ $tag='' }
$laptop=@(8,9,10,11,12,14,18,21,30,31,32)
$type='Desktop'; foreach($c in @($enc.ChassisTypes)){ if($laptop -contains [int]$c){ $type='Laptop' } }
$cpu=Q 'SELECT Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, SocketDesignation FROM Win32_Processor' | Select-Object -First 1
$mem=Q 'SELECT Capacity, Speed, ConfiguredClockSpeed, SMBIOSMemoryType, Manufacturer, DeviceLocator FROM Win32_PhysicalMemory'
$slots=(Q 'SELECT MemoryDevices FROM Win32_PhysicalMemoryArray' | Measure-Object MemoryDevices -Sum).Sum
$types=@{26='DDR4';34='DDR5';24='DDR3';30='LPDDR4';35='LPDDR5';29='LPDDR3'}
$sp=$mem | Select-Object -First 1; $spd= if($sp.ConfiguredClockSpeed){$sp.ConfiguredClockSpeed}else{$sp.Speed}
$vram=@{}; Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}' | ForEach-Object {
  $p=Get-ItemProperty $_.PSPath; if($p.DriverDesc -and $p.'HardwareInformation.qwMemorySize'){ $vram[$p.DriverDesc]=[double]$p.'HardwareInformation.qwMemorySize' } }
$gpu=@(Q 'SELECT Name, AdapterRAM, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate, DriverVersion FROM Win32_VideoController' |
  Where-Object { $_.Name -notmatch 'Remote Display|Mirror|Basic Display' } | ForEach-Object {
  $v= if($vram[$_.Name]){$vram[$_.Name]}else{[double]$_.AdapterRAM}
  [ordered]@{ name=$_.Name; vram=[math]::Round($v/1GB,1); res=$(if($_.CurrentHorizontalResolution){"$($_.CurrentHorizontalResolution)×$($_.CurrentVerticalResolution)"}else{''}); hz=[int]$_.CurrentRefreshRate; driver=[string]$_.DriverVersion } })
$bus=@{7='USB';11='SATA';17='NVMe';8='RAID';10='SAS';3='ATA';12='SD'}; $mt=@{3='HDD';4='SSD';5='SCM'}
$hm=@{'0'='Tốt';'1'='Cảnh báo';'2'='Lỗi';'Healthy'='Tốt';'Warning'='Cảnh báo';'Unhealthy'='Lỗi'}
$disks=@(Q 'SELECT FriendlyName, MediaType, BusType, Size, HealthStatus FROM MSFT_PhysicalDisk' 'root\Microsoft\Windows\Storage' | ForEach-Object {
  $m=E $_.MediaType $mt; if($m -eq 'Unspecified'){ $m='' }
  [ordered]@{ name=[string]$_.FriendlyName; bus=(E $_.BusType $bus); media=$m; size=[math]::Round($_.Size/1GB); health=[string]$hm[[string]$_.HealthStatus] } })
$vols=@(Get-Volume | Where-Object { $_.DriveLetter -and $_.Size -gt 0 -and $_.DriveType -in 'Fixed','Removable' } | Sort-Object DriveLetter | ForEach-Object {
  [ordered]@{ l=[string]$_.DriveLetter; label=[string]$_.FileSystemLabel; fs=[string]$_.FileSystem; size=[math]::Round($_.Size/1GB,1); free=[math]::Round($_.SizeRemaining/1GB,1) } })
$bl='Không rõ'; try { $v=Get-BitLockerVolume -MountPoint 'C:' -ErrorAction Stop; $bl= if($v.ProtectionStatus -eq 'On'){'BẬT ('+$v.VolumeStatus+')'}else{'Tắt'} } catch {}
$lic='Không rõ'; try { $l=Get-CimInstance SoftwareLicensingProduct -Filter "PartialProductKey IS NOT NULL AND ApplicationID='55c92734-d682-4d71-983e-d6ec3f16059f'" | Select-Object -First 1; $lic= if($l.LicenseStatus -eq 1){'Đã kích hoạt'}else{'Chưa kích hoạt'} } catch {}
$sb='Không hỗ trợ'; try { $sb= if(Confirm-SecureBootUEFI -ErrorAction Stop){'Bật'}else{'Tắt'} } catch {}
$tpm='Không có'; try { $t=Get-CimInstance -Namespace root\cimv2\Security\MicrosoftTpm -ClassName Win32_Tpm -ErrorAction Stop | Select-Object -First 1; if($t){ $tpm=([string]$t.SpecVersion -split ',')[0].Trim() } } catch {}
$net=@(Get-NetAdapter -Physical | Where-Object Status -eq 'Up' | ForEach-Object {
  $ip=(Get-NetIPAddress -InterfaceIndex $_.ifIndex -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '169.254*' } | ForEach-Object IPAddress) -join ', '
  [ordered]@{ name=$_.Name; desc=$_.InterfaceDescription; ip=$ip; mac=$_.MacAddress; speed=[string]$_.LinkSpeed } })
[ordered]@{
 pc=[ordered]@{ name=$env:COMPUTERNAME; user="$env:USERDOMAIN\$env:USERNAME"; maker=[string]$cs.Manufacturer; model=[string]$cs.Model; tag=$tag; type=$type }
 os=[ordered]@{ name=$wn; ver=[string]$ver.DisplayVersion; build="$($ver.CurrentBuild).$($ver.UBR)"; arch=[string]$os.OSArchitecture; installed=(D $os.InstallDate);
   boot=$(if($os.LastBootUpTime){([datetime]$os.LastBootUpTime).ToString('dd/MM/yyyy HH:mm')}else{''}); license=$lic; bitlocker=$bl }
 cpu=[ordered]@{ name=(($cpu.Name -replace '\s+',' ').Trim()); cores=[int]$cpu.NumberOfCores; threads=[int]$cpu.NumberOfLogicalProcessors; mhz=[int]$cpu.MaxClockSpeed; socket=[string]$cpu.SocketDesignation }
 ram=[ordered]@{ total=[math]::Round(($mem | Measure-Object Capacity -Sum).Sum/1GB); type=[string]$types[[int]$sp.SMBIOSMemoryType]; speed=[int]$spd; slots=[int]$slots;
   sticks=@($mem | ForEach-Object { [ordered]@{ size=[math]::Round($_.Capacity/1GB); slot=[string]$_.DeviceLocator; maker=([string]$_.Manufacturer).Trim() } }) }
 gpu=$gpu; disks=$disks; vols=$vols
 board=[ordered]@{ maker=[string]$bb.Manufacturer; product=[string]$bb.Product; bios=("$($bios.Manufacturer) $($bios.SMBIOSBIOSVersion)").Trim(); bios_date=(D $bios.ReleaseDate);
   mode=$(if($env:firmware_type){$env:firmware_type}else{''}); secure=$sb; tpm=$tpm }
 net=$net } | ConvertTo-Json -Depth 5 -Compress
"""
        code, out = ps(script, timeout=150)
        try:
            return json.loads(out[out.index("{"):])
        except Exception:                   # noqa: BLE001
            return {"err": out[:300] or f"mã {code}"}

    # ---- đồng hồ CPU / RAM / thời gian chạy (đọc trực tiếp, rất nhẹ)
    _cpu_prev = None

    def live(self):
        if FAKE or not IS_WIN:
            import random
            return {"cpu": random.randint(8, 35), "ram_used": round(random.uniform(11, 14), 1), "ram_total": 31.8,
                    "ram_pct": random.randint(35, 45), "uptime": int(time.monotonic()) + 3600 * 5, "gpu": extra.gpu_usage()}
        from ctypes import wintypes

        class MEM(ctypes.Structure):
            _fields_ = [("len", wintypes.DWORD), ("load", wintypes.DWORD), ("total", ctypes.c_ulonglong), ("avail", ctypes.c_ulonglong),
                        ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong),
                        ("aev", ctypes.c_ulonglong)]
        m = MEM()
        m.len = ctypes.sizeof(MEM)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        idle, kern, user = (wintypes.FILETIME() for _ in range(3))
        ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user))
        ft = lambda f: (f.dwHighDateTime << 32) | f.dwLowDateTime          # noqa: E731
        cur = (ft(idle), ft(kern) + ft(user))
        cpu = 0
        if self._cpu_prev:
            di, dt_ = cur[0] - self._cpu_prev[0], cur[1] - self._cpu_prev[1]
            cpu = max(0, min(100, round(100 * (dt_ - di) / dt_))) if dt_ else 0
        self._cpu_prev = cur
        ctypes.windll.kernel32.GetTickCount64.restype = ctypes.c_ulonglong
        return {"cpu": cpu, "ram_used": round((m.total - m.avail) / 2**30, 1), "ram_total": round(m.total / 2**30, 1),
                "ram_pct": int(m.load), "uptime": int(ctypes.windll.kernel32.GetTickCount64() // 1000), "gpu": self._gpu()}

    def _gpu(self):
        try:
            return extra.gpu_usage()
        except Exception:                   # noqa: BLE001  máy không đọc được bộ đếm GPU -> không hiện
            return None

    # ---- winget: kiểm tra bản cũ / mới, tự cài bản mới (im lặng)
    def _winget_version(self):
        if FAKE:
            return "v1.6.10121"
        exe = shutil.which("winget")
        if not exe:
            return ""
        code, out = run_hidden([exe, "--version"], timeout=60)
        m = re.search(r"v?\d+(\.\d+)+", out or "")
        return m.group(0) if code == 0 and m else ""

    @staticmethod
    def _vtuple(v):
        return tuple(int(x) for x in re.findall(r"\d+", v or "")[:3]) or (0,)

    def winget_auto_update(self):
        """Mở tool: so bản winget trên máy với bản mới nhất của Microsoft; cũ / thiếu thì tự cài bản mới (chạy ngầm)."""
        if not (IS_WIN or FAKE) or self.st.cfg.get("winget_auto", True) is False or "--selftest" in sys.argv:
            self.winget["state"] = "skip"
            return
        self.wg_ready.clear()
        try:
            cur = self._winget_version()
            self.winget["cur"] = cur
            if FAKE:
                latest = "v1.12.350"
            else:
                import requests
                r = requests.get("https://api.github.com/repos/microsoft/winget-cli/releases/latest", timeout=15,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "WinAIO"})
                r.raise_for_status()
                latest = r.json().get("tag_name", "")
            self.winget["latest"] = latest
            if cur and self._vtuple(cur) >= self._vtuple(latest):
                self.winget["state"] = "ok"
                return
            self.winget["state"] = "updating"
            self.log(f"⟳ winget trên máy {'là bản cũ ' + cur if cur else 'chưa có'} → đang tự cài bản mới {latest} (chạy ngầm)...", "warn")
            ok, why = self._winget_install_latest()
            new = self._winget_version()
            if FAKE:
                new = latest
            self.winget["cur"] = new
            if ok and new:
                self.checks["winget"] = True
                self.winget["state"] = "ok"
                self.log(f"✔ Đã cập nhật winget lên {new}", "ok")
            else:
                self.winget["state"] = "err"
                self.log(f"✖ Chưa cập nhật được winget ({why}). Các nút WINGET vẫn thử chạy bằng bản cũ.", "err")
        except Exception as e:              # noqa: BLE001
            self.winget["state"] = "skip"
            self.log(f"Bỏ qua kiểm tra winget: {e}", "dim")
        finally:
            self.wg_ready.set()
            if self.checks.get("winget") and "--selftest" not in sys.argv:
                threading.Thread(target=self.winget_maintain, daemon=True).start()

    # ------------------------------------------------ winget nhanh hơn + tự kiểm tra ID
    WG_SETTINGS = Path(os.environ.get("LOCALAPPDATA", ".")) / "Packages" / "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe" / "LocalState" / "settings.json"

    def winget_tune(self):
        """winget mặc định tải qua Delivery Optimization (hay chậm, nhất là máy mới cài) và tự làm mới kho mỗi 5 phút
        (lần cài nào cũng phải chờ tải lại danh mục). Đổi: tải trực tiếp (wininet), làm mới kho 6 giờ / lần -
        tool tự làm mới kho mỗi lần mở nên danh mục vẫn luôn mới."""
        if FAKE or not IS_WIN or self.st.cfg.get("winget_fast", True) is False:
            return False
        f = self.WG_SETTINGS
        try:
            data = {}
            if f.exists():
                raw = f.read_text(encoding="utf-8-sig", errors="ignore")
                try:
                    data = json.loads(re.sub(r"(?m)^\s*//.*$", "", raw) or "{}")
                except Exception:           # noqa: BLE001
                    shutil.copy2(f, f.with_suffix(".json.winaio.bak"))
                    data = {}
            net = data.setdefault("network", {})
            src = data.setdefault("source", {})
            if net.get("downloader") == "wininet" and src.get("autoUpdateIntervalInMinutes") == 360:
                return False
            net["downloader"] = "wininet"
            src["autoUpdateIntervalInMinutes"] = 360
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            self.log("⚡ Đã chỉnh winget tải trực tiếp (nhanh hơn Delivery Optimization).", "ok")
            return True
        except Exception as e:              # noqa: BLE001
            self.log(f"Không chỉnh được cấu hình winget: {e}", "dim")
            return False

    def _wg_run(self, args, timeout=60):
        cmd = ["winget"] + args + ["--accept-source-agreements", "--disable-interactivity"]
        code, out = run_hidden(cmd, timeout=timeout)
        if (code & 0xFFFFFFFF) == 0x8A150002:          # winget cũ không hiểu --disable-interactivity
            code, out = run_hidden(cmd[:-1], timeout=timeout)
        return code, out

    @staticmethod
    def _wg_parse_show(out):
        ver = re.search(r"(?m)^\s*Version:\s*(\S+)", out)
        url = re.search(r"(?m)^\s*Installer Url:\s*(\S+)", out)
        name = re.search(r"(?m)^Found (.+?) \[", out)
        return (ver.group(1) if ver else ""), (url.group(1) if url else ""), (name.group(1).strip() if name else "")

    def winget_check(self, pkg, force=False):
        """Hỏi kho winget gói này còn không, bản mới nhất, link tải. Lưu cache 12 giờ."""
        w = self.st.wg_get(pkg)
        if w and not force and time.time() - (w["checked"] or 0) < 12 * 3600:
            return w
        if FAKE:
            ok = not pkg.lower().startswith("sai.")
            self.st.wg_put(pkg, ok, "1.2.3" if ok else "", "https://example.com/setup.exe" if ok else "", pkg.split(".")[-1])
            return self.st.wg_get(pkg)
        code, out = self._wg_run(["show", "--id", pkg, "-e", "--source", wg_source(pkg)])
        ver, url, name = self._wg_parse_show(out)
        if code == 0 or ver:
            self.st.wg_put(pkg, True, ver, url, name)
        elif (code & 0xFFFFFFFF) in (0x8A150014, 0x8A15000B) or "No package found" in out:
            self.st.wg_put(pkg, False)
        else:
            return w                        # lỗi mạng... giữ kết quả cũ
        return self.st.wg_get(pkg)

    def _wg_find_new_id(self, name):
        """ID cũ không còn: tìm theo tên nút, chỉ nhận khi đúng 1 gói trùng tên."""
        if FAKE:
            return None
        code, out = self._wg_run(["search", "--name", name, "--source", "winget"])
        hits = []
        for line in out.splitlines():
            m = re.match(r"^(.+?)\s{2,}(\S+\.\S+)\s{2,}\S+", line.strip())
            if m and norm_name(m.group(1)) == norm_name(name):
                hits.append(m.group(2))
        hits = list(dict.fromkeys(hits))
        return hits[0] if len(hits) == 1 else None

    def winget_maintain(self):
        """Mở tool: chỉnh winget cho nhanh, làm mới kho, kiểm tra từng nút WINGET (ID còn không, bản mới nhất),
        ID hỏng thì thử tự tìm ID mới theo tên nút."""
        try:
            self.winget_tune()
            if not FAKE:
                self._wg_run(["source", "update", "--name", "winget"], timeout=180)
            apps = [a for g in self.st.groups() for a in g["apps"] if a["kind"] == "winget"]
            bad, fixed = [], []
            for a in apps:
                pkg = a["src"].split(":", 1)[1].strip()
                w = self.winget_check(pkg)
                if not w or w["ok"]:
                    continue
                new = self._wg_find_new_id(a["name"])
                if new and (self.winget_check(new) or {}).get("ok"):
                    with self.st.lock:
                        self.st.db.execute("UPDATE apps SET src=? WHERE id=?", ("winget:" + new, a["id"]))
                        self.st.commit(persist=self.st.on_disk)
                    fixed.append(f"{a['name']}: {pkg} → {new}")
                else:
                    bad.append(f"{a['name']} ({pkg})")
            for f in fixed:
                self.log(f"🔧 Đã tự sửa ID winget {f}", "ok")
            if bad:
                self.log("⚠ ID winget không còn trong kho: " + ", ".join(bad) + " - bật Admin, bấm ✎ để sửa.", "warn")
            else:
                self.log(f"✔ Đã kiểm tra {len(apps)} nút WINGET: tất cả còn dùng được.", "dim")
            self.wg_checked = time.time()
            try:                            # phần mềm nào có bản mới -> hiện số trên menu Quản lý
                up = mgr.wg_upgrades()
                self.upg_n = len(up)
                if up:
                    self.log(f"⬆ {len(up)} phần mềm có bản mới: " + ", ".join(x["name"] for x in up[:6])
                             + (" ..." if len(up) > 6 else "") + " - vào Quản lý › Cập nhật app.", "warn")
            except Exception:               # noqa: BLE001
                pass
        except Exception as e:              # noqa: BLE001
            self.log(f"Bỏ qua kiểm tra nút winget: {e}", "dim")

    def _winget_install_latest(self):
        if FAKE:
            time.sleep(3)
            return True, ""
        # Cách 1: mô-đun chính chủ Microsoft.WinGet.Client -> Repair-WinGetPackageManager (tự kèm thư viện phụ thuộc)
        c1, o1 = ps("Set-ExecutionPolicy Bypass -Scope Process -Force; [Net.ServicePointManager]::SecurityProtocol='Tls12';"
                    "Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope AllUsers | Out-Null;"
                    "Set-PSRepository PSGallery -InstallationPolicy Trusted;"
                    "Install-Module Microsoft.WinGet.Client -Force -Scope AllUsers -Repository PSGallery -AllowClobber | Out-Null;"
                    "Import-Module Microsoft.WinGet.Client -Force; Repair-WinGetPackageManager -AllUsers -Latest -Force; 'OK'",
                    timeout=900)
        if c1 == 0 and self._winget_version():
            return True, ""
        self.log("Cách 1 không được, thử cài trực tiếp gói App Installer từ GitHub của Microsoft...", "dim")
        # Cách 2: tải gói .msixbundle + thư viện phụ thuộc từ bản phát hành chính thức trên GitHub
        script = r"""
$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol='Tls12'
$d=Join-Path $env:TEMP 'winaio_winget'; New-Item -ItemType Directory -Force $d | Out-Null
$rel=Invoke-RestMethod 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' -Headers @{ 'User-Agent'='WinAIO' }
$bundle=$rel.assets | Where-Object name -like '*.msixbundle' | Select-Object -First 1
$deps=$rel.assets | Where-Object name -like '*Dependencies*.zip' | Select-Object -First 1
$arch= if([Environment]::Is64BitOperatingSystem){'x64'}else{'x86'}
if($deps){ Invoke-WebRequest $deps.browser_download_url -OutFile "$d\deps.zip"; Expand-Archive "$d\deps.zip" "$d\deps" -Force
  Get-ChildItem "$d\deps" -Recurse -Include *.appx | Where-Object { $_.FullName -match "\\$arch\\" } | ForEach-Object { try { Add-AppxPackage $_.FullName -ErrorAction Stop } catch {} } }
else { Invoke-WebRequest "https://aka.ms/Microsoft.VCLibs.$arch.14.00.Desktop.appx" -OutFile "$d\vclibs.appx"; try { Add-AppxPackage "$d\vclibs.appx" } catch {} }
Invoke-WebRequest $bundle.browser_download_url -OutFile "$d\winget.msixbundle"
Add-AppxPackage "$d\winget.msixbundle" -ForceApplicationShutdown
Remove-Item $d -Recurse -Force; 'OK'
"""
        c2, o2 = ps(script, timeout=900)
        if c2 == 0 and self._winget_version():
            return True, ""
        return False, (o2 or o1)[-200:]

    # ---- hàng đợi cài
    def enqueue(self, ids):
        added = 0
        with self.lock:
            for i in ids:
                i = int(i)
                if i not in self.queue and not (self.cur and self.cur["id"] == i):
                    self.queue.append(i)
                    self.results[i] = "wait"
                    added += 1
            if not self.worker or not self.worker.is_alive():
                self.batch_n, self.batch_i = len(self.queue), 0
                self.stop_flag.clear()
                self.worker = threading.Thread(target=self._work, daemon=True)
                self.worker.start()
            else:
                self.batch_n += added
        return added

    def stop(self):
        self.stop_flag.set()
        with self.lock:
            for i in self.queue:
                self.results.pop(i, None)
            self.queue.clear()
        self.log("Đã yêu cầu dừng. Mục đang chạy sẽ dừng sau khi tải xong phần hiện tại.", "warn")

    def _work(self):
        while not self.stop_flag.is_set():
            with self.lock:
                if not self.queue:
                    break
                aid = self.queue.pop(0)
                self.batch_i += 1
            a = self.st.app(aid)
            if not a:
                continue
            self.cur = {"id": aid, "name": a["name"], "phase": "Chuẩn bị", "pct": 0, "done": 0, "total": 0, "speed": "",
                        "dl": None, "inst": None, "est": False, "secs": 0}
            self.results[aid] = "run"
            self.log(f"▶ [{self.batch_i}/{self.batch_n}] {a['name']}")
            try:
                status, detail = self._install(a)
            except Exception as e:          # noqa: BLE001
                status, detail = "err", nice_err(e)
            if status in ("ok", "web") and self.cur:
                self.cur.update(inst=100, est=False, phase="Xong")
                time.sleep(0.6)                      # để thanh % kịp hiện 100%
            self.results[aid] = "ok" if status in ("ok", "web") else "err"
            if status == "ok" and "picview" in (a.get("src") or "").lower():
                try:
                    self.log("🖼️ " + extra.picview_default())
                except Exception as e:      # noqa: BLE001
                    self.log("Chưa đặt được PicView làm mặc định: " + nice_err(e), "warn")
            label = {"ok": "Xong", "web": "Đã mở trang web", "err": "Lỗi", "stop": "Đã dừng"}.get(status, status)
            self.log(f"{'✔' if status in ('ok', 'web') else '✖'} {a['name']}: {label}{(' - ' + detail) if detail else ''}",
                     "ok" if status in ("ok", "web") else "err")
            self.st.add_history(a["name"], a["src"], label, detail)
        self.cur = None
        self.log("Hàng đợi đã xong." if not self.stop_flag.is_set() else "Đã dừng hàng đợi.")

    def _install(self, a):
        if fix_src(a["src"]) != a["src"]:
            a = dict(a, src=fix_src(a["src"]), args="")
        kind, src = src_kind(a["src"]), a["src"].strip()
        args = (a.get("args") or "").strip()
        if kind == "none":
            return "err", "Nút chưa có nguồn (bật Admin rồi bấm ✎ để thêm link)"
        if kind == "office":
            return "err", "Nút MS Office mở cửa sổ cài Office riêng (bấm trực tiếp vào nút)."
        if kind == "open":
            open_target(src.split(":", 1)[1].strip())
            return "web", "đã mở bằng trình duyệt"
        if kind == "winget":
            return self._winget(src.split(":", 1)[1].strip(), args)
        if kind == "cmd":
            stop = self._est_start(30.0, "Đang chạy lệnh")
            code, out = run_hidden(src.split(":", 1)[1].strip(), shell=True, timeout=3600)
            stop.set()
            self.log(out[-800:] if out else "(không có kết quả)", "dim")
            return ("ok" if code == 0 else "err"), "" if code == 0 else f"mã thoát {code}"
        if kind == "file":
            p = Path(os.path.expandvars(src))
            if not p.is_absolute():
                p = BASE / p                 # đường dẫn tương đối theo thư mục tool (dùng được trên USB)
            if not p.exists() and not FAKE:
                return "err", f"Không thấy file: {p}"
            return self._run_file(p, args)
        if kind == "github":
            self.cur.update(phase="Hỏi bản mới nhất", pct=-1)
            src, tag = resolve_github(src)
            self.log(f"Bản mới nhất {tag} → {src.rsplit('/', 1)[-1]}", "dim")
        # web
        path = self._download(src)
        if path == "web":
            return "web", ""
        if path is None:
            return "stop", ""
        return self._run_file(path, args)

    # ---- % cài đặt: trình cài của hãng không báo tiến độ -> ước tính theo thời gian (tiến dần tới 95%, xong mới 100%)
    def _est_start(self, tau, phase="Đang cài đặt"):
        cur = self.cur
        cur.update(phase=phase, inst=0, est=True, secs=0)
        stop = threading.Event()
        t0 = time.time()

        def run():
            while not stop.wait(0.4):
                el = time.time() - t0
                cur.update(inst=min(95, int(95 * (1 - math.exp(-el / tau)))), secs=int(el))
        threading.Thread(target=run, daemon=True).start()
        return stop

    @staticmethod
    def _tau_for(path):
        try:
            mb = Path(path).stat().st_size / 1048576
        except OSError:
            mb = 30
        return max(8.0, min(240.0, 6 + mb * 0.35))      # file cài càng nặng thì cài càng lâu

    def _stream(self, cmd, on_line, timeout=3600):
        """Chạy lệnh ẩn, đọc từng dòng (kể cả dòng cập nhật bằng \r của winget) để lấy %."""
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=CREATE_NO_WINDOW)
        buf, lines, t0 = b"", [], time.time()
        while True:
            ch = p.stdout.read1(512) if hasattr(p.stdout, "read1") else p.stdout.read(1)
            if not ch:
                break
            buf += ch
            parts = re.split(rb"[\r\n]", buf)
            buf = parts[-1]
            for raw in parts[:-1]:
                try:
                    t = raw.decode("utf-8")
                except UnicodeDecodeError:
                    t = raw.decode("cp1258", "replace")
                if t.strip():
                    lines.append(t)
                    on_line(t)
            if time.time() - t0 > timeout:
                p.kill()
                break
        code = p.wait()
        return code, "\n".join(lines)

    WG_RETRY = {0x8A150008, 0x8A150011, 0x8A150014, 0x80190194, 0x80072EE7, 0x80072EFD}
    WINGET_ERR = {
        0x8A150008: "Tải bộ cài thất bại (mạng chập chờn hoặc link của hãng đã đổi).",
        0x8A150011: "File tải về không khớp mã kiểm tra (hãng vừa thay bộ cài, kho winget chưa cập nhật kịp).",
        0x8A150002: "Lệnh có tham số mà bản winget trên máy này không hiểu (winget cũ). Nên cập nhật App Installer trong Microsoft Store.",
        0x8A150014: "Không tìm thấy gói này trong kho winget (sai ID hoặc ID đã đổi). Bật Admin, bấm ✎ để sửa ID / đổi sang link tải.",
    }

    def _winget(self, pkg, args):
        if not self.wg_ready.is_set():
            self.wg_ready.wait(900)
        if not self.checks.get("winget"):
            return "err", "Máy này chưa có winget (App Installer). Hãy đổi nguồn nút này sang link tải trực tiếp."
        if not self.wg_ready.is_set():
            self.cur.update(phase="Chờ cập nhật winget xong", pct=-1)
            self.wg_ready.wait(900)
        self.cur.update(phase="winget đang cài", pct=-1)
        base = ["winget", "install", "--id", pkg, "-e", "--source", wg_source(pkg), "--silent",
                "--accept-package-agreements", "--accept-source-agreements"]
        extra = shlex.split(args) if args else []
        # winget bản cũ (Windows mới cài) không có --disable-interactivity -> báo 0x8A150002; chạy lại không có tham số đó
        cur = self.cur
        est = {"stop": None}
        unit = {"KB": 1 / 1024, "MB": 1, "GB": 1024}

        def on_line(t):
            m = re.search(r"([\d.,]+)\s*(KB|MB|GB)\s*/\s*([\d.,]+)\s*(KB|MB|GB)", t)
            if m and not est["stop"]:
                d = float(m.group(1).replace(",", ".")) * unit[m.group(2)]
                tot = float(m.group(3).replace(",", ".")) * unit[m.group(4)]
                if tot > 0:
                    cur.update(phase="winget đang tải", dl=min(100, int(d * 100 / tot)), pct=min(100, int(d * 100 / tot)),
                               done=int(d * 1048576), total=int(tot * 1048576), speed="")
                return
            low = t.lower()
            if not est["stop"] and ("install" in low or "cài đặt" in low or "hash" in low or "xác minh" in low) \
                    and not re.search(r"\d+\s*%", t):
                if cur.get("dl") is not None:
                    cur["dl"] = 100
                est["stop"] = self._est_start(45.0, "winget đang cài")

        if FAKE:
            for i in range(0, 101, 5):
                on_line(f"  ███  {i * 0.8:.1f} MB / 80.0 MB")
                time.sleep(0.07)
            on_line("Starting package install...")
            time.sleep(2.5)
            code, out = 0, "Successfully installed"
        else:
            for attempt in (1, 2):
                for cmd in (base + ["--disable-interactivity"] + extra, base + extra):
                    code, out = self._stream(cmd, on_line)
                    if (code & 0xFFFFFFFF) != 0x8A150002:
                        break
                    self.log("winget trên máy này là bản cũ, chạy lại lệnh không có --disable-interactivity...", "warn")
                if attempt == 1 and (code & 0xFFFFFFFF) in self.WG_RETRY:
                    self.log("winget tải lỗi / link trong kho đã đổi → làm mới kho winget rồi thử lại...", "warn")
                    cur.update(phase="Làm mới kho winget", pct=-1)
                    self._wg_run(["source", "update", "--name", "winget"], timeout=180)
                    continue
                break
        if est["stop"]:
            est["stop"].set()
        keep = [l for l in out.splitlines() if l.strip() and not re.match(r"^[\s\-\\|/█▒]+$", l)
                and not re.search(r"(KB|MB|GB)\s*/\s*[\d.,]+\s*(KB|MB|GB)|\d+\s*%\s*$", l)]
        tail = "\n".join(dict.fromkeys(keep))[-600:]           # bỏ các dòng thanh tiến độ, bỏ dòng trùng
        if tail:
            self.log(tail, "dim")
        low = out.lower()
        if code == 0 or any(x in low for x in ("already installed", "no available upgrade", "đã được cài", "không tìm thấy bản nâng cấp")):
            return "ok", ""
        hx = code & 0xFFFFFFFF
        why = self.WINGET_ERR.get(hx, "")
        return "err", f"winget mã 0x{hx:08X}" + (f" - {why}" if why else "")

    @staticmethod
    def _gdrive_direct(url):
        m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?.*?id=)([\w-]{20,})", url)
        if m:
            return f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
        return url

    def dl_path(self):
        d = Path(os.path.expandvars(self.st.cfg.get("download_dir") or "Data\\Downloads"))
        return d if d.is_absolute() else BASE / d

    def dl_dir(self):
        """Thư mục tải - lần tải đầu tiên mới tạo thư mục Data kế bên exe."""
        self.st.ensure_disk()
        d = self.dl_path()
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _download(self, url):
        self.cur.update(phase="Đang kết nối", pct=0)
        if FAKE:
            self.dl_dir()
            total = 40 * 1024 * 1024
            for i in range(41):
                if self.stop_flag.is_set():
                    return None
                time.sleep(0.08)
                self.cur.update(phase="Đang tải", done=i * 1024 * 1024, total=total, pct=i * 100 // 40, dl=i * 100 // 40, speed="12.5 MB/s")
            if "bluestacks" in url or url.endswith("/"):
                self.log(f"Link là trang web, đã mở bằng trình duyệt: {url}")
                return "web"
            return Path("setup.exe")
        import requests
        url = self._gdrive_direct(url)
        s = requests.Session()
        s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
        r = s.get(url, stream=True, timeout=30, allow_redirects=True)
        ctype = r.headers.get("Content-Type", "")
        if "text/html" in ctype:
            html = r.text
            # Google Drive: trang cảnh báo file lớn -> lấy form tải thật
            form = re.search(r'<form[^>]+action="([^"]+)"', html)
            if form and "drive" in r.url:
                params = dict(re.findall(r'name="([^"]+)"\s+value="([^"]*)"', html))
                r = s.get(form.group(1).replace("&amp;", "&"), params=params, stream=True, timeout=30)
                ctype = r.headers.get("Content-Type", "")
            if "text/html" in ctype:
                os.startfile(r.url if IS_WIN else url)       # noqa: S606
                self.log(f"Link là trang web (không phải file), đã mở bằng trình duyệt: {url}")
                return "web"
        r.raise_for_status()
        name = ""
        cd = r.headers.get("Content-Disposition", "")
        m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="?([^";]+)"?', cd)
        if m:
            name = unquote(m.group(1))
        if not name:
            name = unquote(Path(urlparse(r.url).path).name) or "setup.exe"
        name = re.sub(r'[\\/:*?"<>|]', "_", name)
        if "." not in name:
            name += ".exe"
        out = self.dl_dir() / name
        total = int(r.headers.get("Content-Length") or 0)
        if out.exists() and total and out.stat().st_size == total and self.st.cfg.get("keep_installer", True):
            self.cur.update(dl=100, pct=100, done=total, total=total)
            self.log(f"Dùng lại file đã tải: {out.name}")
            return out
        part = out.with_suffix(out.suffix + ".part")
        done, t0, last = 0, time.time(), 0
        self.cur.update(phase="Đang tải", total=total, dl=0 if total else -1)
        with open(part, "wb") as f:
            for chunk in r.iter_content(256 * 1024):
                if self.stop_flag.is_set():
                    f.close()
                    part.unlink(missing_ok=True)
                    return None
                f.write(chunk)
                done += len(chunk)
                if time.time() - last > 0.25:
                    last = time.time()
                    sp = done / max(0.1, last - t0)
                    pc = int(done * 100 / total) if total else -1
                    self.cur.update(done=done, pct=pc, dl=pc, speed=human(sp) + "/s")
        os.replace(part, out)
        self.cur.update(done=done, pct=100, dl=100)
        self.log(f"Đã tải {out.name} ({human(done)})")
        return out

    @staticmethod
    def _unarchive(p, dest, pw=""):
        """Giải nén .rar / .7z: 7-Zip -> WinRAR -> tar.exe của Windows 11 (đọc được rar, không đọc được rar có mật khẩu)."""
        Path(dest).mkdir(parents=True, exist_ok=True)
        pf = [os.environ.get("ProgramW6432", ""), os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")]
        tries = []
        for b in pf:
            if b:
                tries.append([str(Path(b) / "7-Zip" / "7z.exe"), "x", "-y"] + ([f"-p{pw}"] if pw else []) + [f"-o{dest}", str(p)])
                tries.append([str(Path(b) / "WinRAR" / "UnRAR.exe"), "x", "-y", "-o+", f"-p{pw}" if pw else "-p-", str(p), str(dest) + "\\"])
        if not pw:
            tries.append([str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "tar.exe"), "-xf", str(p), "-C", str(dest)])
        for cmd in tries:
            if not Path(cmd[0]).exists():
                continue
            code, _ = run_hidden(cmd, timeout=600)
            if code == 0 and any(dest.iterdir()):
                return True
        return False

    def _run_file(self, p, args):
        ext = p.suffix.lower()
        if FAKE:
            stop = self._est_start(1.5)
            time.sleep(2.5)
            stop.set()
            return "ok", ""
        a = shlex.split(args, posix=False) if args else []
        if ext == ".zip":
            dest = self.dl_dir() / p.stem
            self.cur.update(phase="Đang giải nén", inst=0, est=False)
            with zipfile.ZipFile(p) as z:
                items = z.infolist()
                for i, it in enumerate(items, 1):             # % giải nén là % thật
                    z.extract(it, dest)
                    self.cur["inst"] = int(i * 100 / max(1, len(items)))
            exes = [x for x in dest.rglob("*.exe")]
            self.log(f"Đã giải nén vào {dest}")
            if len(exes) == 1:
                subprocess.Popen([str(exes[0])] + a, cwd=str(exes[0].parent))
            else:
                os.startfile(dest)            # noqa: S606
            return "ok", ""
        if ext in (".rar", ".7z"):
            pw = next((x.split("=", 1)[1] for x in a if x.lower().startswith("pass=")), "")
            a = [x for x in a if not x.lower().startswith("pass=")]
            dest = self.dl_dir() / p.stem
            dest.mkdir(parents=True, exist_ok=True)
            stop = self._est_start(8.0, "Đang giải nén")
            ok = self._unarchive(p, dest, pw)
            if not ok and not FAKE:                 # máy chưa có 7-Zip -> cài 7-Zip rồi thử lại
                self.log("Máy chưa có công cụ giải nén file này - đang cài 7-Zip...")
                run_hidden(["winget", "install", "--id", "7zip.7zip", "-e", "--source", "winget", "--silent",
                            "--accept-package-agreements", "--accept-source-agreements"], timeout=600)
                ok = self._unarchive(p, dest, pw)
            stop.set()
            if not ok:
                os.startfile(str(p))          # noqa: S606
                return "err", f"Không giải nén được {p.name} (cài 7-Zip / WinRAR rồi thử lại) - đã mở file để giải nén tay"
            exes = [x for x in dest.rglob("*.exe")]
            self.log(f"Đã giải nén vào {dest}")
            if len(exes) == 1:
                subprocess.Popen([str(exes[0])] + a, cwd=str(exes[0].parent))
            else:
                os.startfile(dest)            # noqa: S606
            return "ok", ""
        stop = None
        if ext == ".msi":
            stop = self._est_start(self._tau_for(p))
            code = subprocess.call(["msiexec", "/i", str(p)] + a)
        elif ext in (".exe", ".bat", ".cmd"):
            stop = self._est_start(self._tau_for(p))
            code = subprocess.call([str(p)] + a, cwd=str(p.parent), shell=ext != ".exe")
        else:
            os.startfile(str(p))              # noqa: S606
            return "ok", ""
        if stop:
            stop.set()
        if not self.st.cfg.get("keep_installer", True) and str(p).startswith(str(self.dl_path())):
            try:
                p.unlink()
            except OSError:
                pass
        # 3010 = cần khởi động lại, 1641 = đã khởi động lại
        return ("ok" if code in (0, 3010, 1641) else "err"), ("Cần khởi động lại máy" if code == 3010 else ("" if code == 0 else f"mã thoát {code}"))

    # ---- tiện ích Windows
    def preset_run(self, j, pid):
        """Hồ sơ cài đặt: xếp các phần mềm vào hàng đợi cài, chờ cài xong, chạy tiện ích Windows, dọn Win 11, cài font."""
        p = next((x for x in self.st.preset_list() if x["id"] == int(pid)), None)
        if not p:
            raise RuntimeError("Không có hồ sơ này")
        apps = {}
        for g in self.st.groups():
            for a in g["apps"]:
                apps.setdefault(norm_name(a["name"]), a)
        want = [apps.get(norm_name(n)) for n in p["apps"]]
        miss = [n for n, a in zip(p["apps"], want) if not a]
        ids = [a["id"] for a in want if a and (a.get("src") or "").strip()]
        nosrc = [a["name"] for a in want if a and not (a.get("src") or "").strip()]
        steps = len(p["tools"]) + bool(p["opts"].get("tidy")) + bool(p["opts"].get("fonts"))
        if ids:
            self.enqueue(ids)
            j["text"] = f"Đang cài {len(ids)} phần mềm..."
            time.sleep(0.5)
            while self.worker and self.worker.is_alive():
                if j.get("stop"):
                    self.stop()
                    raise RuntimeError("Đã dừng")
                with self.lock:
                    n, i = max(1, self.batch_n), self.batch_i
                    cur = self.cur["name"] if self.cur else ""
                j["pct"] = int(80 * i / n) if steps else int(100 * i / n)
                j["text"] = f"Cài phần mềm {min(i + 1, n)}/{n}: {cur}" if cur else f"Cài phần mềm {i}/{n}"
                time.sleep(0.7)
        base = 80 if ids else 0
        k = 0
        notes = []
        for tid in p["tools"]:
            t = next((x for x in TOOLS if x[0] == tid), None)
            if not t:
                continue
            j["pct"], j["text"] = base + int((100 - base) * k / max(1, steps)), "Tiện ích: " + t[2]
            self.run_tool(tid)
            k += 1
        if p["opts"].get("tidy"):
            j["text"] = "Dọn Win 11 cho gọn..."
            extra.win11_tidy(j, True)
            k += 1
        if p["opts"].get("fonts"):
            url = self.st.cfg.get("font_pack_url") or FONT_PACK
            if url:
                j["text"] = "Cài bộ font tiếng Việt..."
                notes.append(extra.font_install(j, url)["text"])
            else:
                notes.append("Bỏ qua cài font: Admin chưa gắn link bộ font (tab Tiện ích Windows > Font tiếng Việt).")
        ok_n = sum(1 for i in ids if self.results.get(i) == "ok")
        msg = f"Hồ sơ '{p['name']}': cài xong {ok_n}/{len(ids)} phần mềm, chạy {len(p['tools'])} tiện ích" + \
              (", đã dọn Win 11" if p["opts"].get("tidy") else "") + "."
        if miss:
            msg += " Không thấy nút: " + ", ".join(miss) + "."
        if nosrc:
            msg += " Nút chưa có nguồn: " + ", ".join(nosrc) + "."
        return {"text": " ".join([msg] + notes)}

    def run_tool(self, tid, extra=None):
        t = next((x for x in TOOLS if x[0] == tid), None)
        if not t:
            return {"ok": False, "out": "Không có chức năng này"}
        _, _, label, kind, cmd, _ = t
        self.busy_tool = label
        self.log(f"▶ {label}")
        try:
            if kind == "open":
                open_target(cmd)
                code, out = 0, ""
            elif kind == "ps":
                code, out = ps(cmd)
                if code != 0:                       # bỏ phần "At line:1 char:..." của PowerShell, giữ câu báo lỗi
                    out = re.split(r"\r?\n(?:At line:|\+ |    \+ )", out)[0].strip()
            elif kind == "cmd":
                code, out = run_hidden(cmd, shell=True, timeout=1800)
            else:
                code, out = getattr(self, "_t_" + cmd)(extra)
        except Exception as e:              # noqa: BLE001
            code, out = 1, str(e)
        finally:
            self.busy_tool = ""
        ok = code == 0
        self.log(f"{'✔' if ok else '✖'} {label}" + (f": {out[-500:]}" if out else ""), "ok" if ok else "err")
        self.st.add_history(label, "Tiện ích", "Xong" if ok else "Lỗi", out)
        return {"ok": ok, "out": out}

    def _bak_dir(self, kind):
        self.st.ensure_disk()
        d = BACKUP_DIR / f"{kind}_{os.environ.get('COMPUTERNAME', 'PC')}_{dt.datetime.now():%Y%m%d_%H%M}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _t_wifi_backup(self, _):
        d = self._bak_dir("Wifi")
        code, out = run_hidden(["netsh", "wlan", "export", "profile", "key=clear", f"folder={d}"])
        if code == 0:
            open_target(str(d))
        return code, f"Đã lưu vào {d}\n{out}"

    def _t_wifi_restore(self, folder):
        if not folder:
            return 1, "Chưa chọn thư mục"
        files = list(Path(folder).glob("*.xml"))
        ok = 0
        for f in files:
            c, _ = run_hidden(["netsh", "wlan", "add", "profile", f"filename={f}", "user=all"])
            ok += c == 0
        return (0 if ok else 1), f"Đã nạp {ok}/{len(files)} mạng Wifi"

    def _t_driver_backup(self, _):
        d = self._bak_dir("Driver")
        code, out = run_hidden(["dism", "/online", "/export-driver", f"/destination:{d}"], timeout=3600)
        if code == 0:
            open_target(str(d))
        return code, f"Đã lưu vào {d}\n{out[-400:]}"

    def _t_driver_restore(self, folder):
        if not folder:
            return 1, "Chưa chọn thư mục"
        return run_hidden(["pnputil", "/add-driver", str(Path(folder) / "*.inf"), "/subdirs", "/install"], timeout=3600)

    def _t_wifi_passwords(self, _):
        if FAKE:
            return 0, "Wifi_NhaDuyAnh    →  12345678\nCafe_Sang         →  cafesang2026\nAndroidAP         →  (mạng mở / không lưu mật khẩu)"
        _, out = run_hidden(["netsh", "wlan", "show", "profiles"], timeout=30)
        names = [m.strip() for m in re.findall(r":\s*(.+)$", out or "", re.M) if m.strip() and "<" not in m]
        names = [n for n in names if not re.search(r"(?i)^(none|không)$", n)]
        rows = []
        for n in dict.fromkeys(names):
            _, o = run_hidden(["netsh", "wlan", "show", "profile", f"name={n}", "key=clear"], timeout=30)
            if not o or "SSID" not in o and "Profile" not in o:
                continue
            m = re.search(r"(?im)^\s*(Key Content|Nội dung khóa|Nội dung Khóa)\s*:\s*(.+)$", o)
            rows.append(f"{n:<30} →  {m.group(2).strip() if m else '(mạng mở / không lưu mật khẩu)'}")
        return (0, "\n".join(rows)) if rows else (1, "Máy chưa lưu mạng Wifi nào (hoặc không có card Wifi).")

    def _t_win_key(self, key):
        key = (key or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{5}(-[A-Z0-9]{5}){4}", key):
            return 1, "Key không đúng dạng XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
        slmgr = r"%windir%\System32\slmgr.vbs"
        c1, o1 = run_hidden(f"cscript //nologo {slmgr} /ipk {key}", shell=True)
        if c1 != 0:
            return c1, o1
        c2, o2 = run_hidden(f"cscript //nologo {slmgr} /ato", shell=True, timeout=180)
        return c2, o1 + "\n" + o2


# ================================================================= MS OFFICE (viết lại từ "Cài đặt Office v4.1", bổ sung theo v4.3 ở officex.py)
# Dùng Office Deployment Tool (ODT) chính chủ của Microsoft: cài Online từ máy chủ Microsoft,
# hoặc Offline từ thư viện đã tải sẵn trong thư mục Soft\Office kế bên exe.
ODT_SETUP_URL = "https://officecdn.microsoft.com/pr/wsus/setup.exe"
ODT_PACK_URL = "https://download.microsoft.com/download/6c1eeb25-cf8b-41d9-8d0d-cc1dbc032140/officedeploymenttool_18925-20138.exe"
OFFICE_APPS = ["Word", "Excel", "PowerPoint", "Outlook", "Access", "Publisher", "OneNote"]
OFFICE_EXES = {"Word": "WINWORD.EXE", "Excel": "EXCEL.EXE", "PowerPoint": "POWERPNT.EXE", "Outlook": "OUTLOOK.EXE",
               "Access": "MSACCESS.EXE", "Publisher": "MSPUB.EXE", "OneNote": "ONENOTE.EXE", "Project": "WINPROJ.EXE",
               "Visio": "VISIO.EXE"}
OFFICE_LANGS = [("en-us", "English (US)"), ("vi-vn", "Tiếng Việt"), ("zh-cn", "Chinese"), ("fr-fr", "French"),
                ("de-de", "German"), ("ko-kr", "Korean"), ("ja-jp", "Japanese"), ("ru-ru", "Russian")]
OFFICE_EDITIONS = [("ProPlus", "Professional Plus (đầy đủ nhất)"), ("Standard", "Standard (doanh nghiệp)"),
                   ("HomeBusiness", "Home & Business"), ("HomeStudent", "Home & Student")]


OFFICE_365_EDITIONS = [("ProPlus", "Microsoft 365 Apps for enterprise (doanh nghiệp lớn)"),
                       ("Business", "Microsoft 365 Apps for business (doanh nghiệp vừa & nhỏ)"),
                       ("HomeStudent", "Microsoft 365 Personal / Family (cá nhân, gia đình)")]


def office_product_id(ver, ed):
    if ver == "365":
        return {"HomeStudent": "O365HomePremRetail", "HomeBusiness": "O365HomePremRetail", "Business": "O365BusinessRetail"}.get(ed, "O365ProPlusRetail")
    return f"{ed}Retail" if ver == "2016" else f"{ed}{ver}Retail"


def office_extra_id(kind, ver):            # kind = ProjectPro / VisioPro
    return f"{kind}Retail" if ver in ("2016", "365") else f"{kind}{ver}Retail"


def office_dir():
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
        d = Path(base) / "Microsoft Office" / "root" / "Office16"
        if d.exists():
            return d
    return None


def office_config(o, source=""):
    """Tạo file cấu hình XML cho ODT từ lựa chọn trên giao diện."""
    ver, ed, bit, lang = o.get("ver", "2024"), o.get("ed", "ProPlus"), o.get("bit", "64"), o.get("lang", "vi-vn")
    apps = set(o.get("apps") or [])
    langs = [lang] + (["en-us"] if o.get("en") and lang != "en-us" else [])
    lang_xml = "".join(f'      <Language ID="{l}" />\n' for l in langs)
    src = f' SourcePath="{source}"' if source else ""
    x = f'<?xml version="1.0" encoding="UTF-8"?>\n<Configuration>\n  <Add OfficeClientEdition="{bit}" Channel="Current"{src}>\n'
    if apps:
        x += f'    <Product ID="{office_product_id(ver, ed)}">\n{lang_xml}'
        for a in OFFICE_APPS:
            if a not in apps:
                x += f'      <ExcludeApp ID="{a}" />\n'
        for a in ("Teams", "Lync", "OneDrive", "Groove", "Bing"):
            x += f'      <ExcludeApp ID="{a}" />\n'
        x += "    </Product>\n"
    if o.get("project"):
        x += f'    <Product ID="{office_extra_id("ProjectPro", ver)}">\n{lang_xml}    </Product>\n'
    if o.get("visio"):
        x += f'    <Product ID="{office_extra_id("VisioPro", ver)}">\n{lang_xml}    </Product>\n'
    x += '  </Add>\n  <Display Level="Full" AcceptEULA="TRUE" />\n'
    if apps:
        x += "  <RemoveMSI />\n"
    x += '  <Property Name="AUTOACTIVATE" Value="0" />\n</Configuration>\n'
    return x


def odt_latest_url():
    """Link gói ODT mới nhất trên trang tải của Microsoft (id=49117); lỗi thì dùng link dự phòng."""
    import requests
    try:
        t = requests.get("https://www.microsoft.com/en-us/download/details.aspx?id=49117", timeout=20,
                         headers={"User-Agent": "Mozilla/5.0"}).text
        m = re.search(r"https://download\.microsoft\.com/download/[^\"'\s]+/officedeploymenttool_[^\"'\s]+\.exe", t)
        if m:
            return m.group(0)
    except Exception:                       # noqa: BLE001
        pass
    return ODT_PACK_URL


class OfficeSetup:
    def __init__(self, eng):
        self.e = eng
        self.busy = ""

    def offline_dir(self):
        return BASE / "Soft" / "Office"

    def has_offline(self):
        d = self.offline_dir()
        return (d / "setup.exe").exists() and (d / "Office" / "Data").exists()

    def status(self):
        d = office_dir()
        installed = [n for n, exe in OFFICE_EXES.items() if d and (d / exe).exists()]
        return {"offline": self.has_offline(), "offline_dir": str(self.offline_dir()), "installed": installed,
                "office_dir": str(d) if d else "", "busy": self.busy}

    def _setup_exe(self):
        """Lấy setup.exe của ODT: ưu tiên bản trong thư viện offline, không thì tải từ Microsoft."""
        if self.has_offline():
            return self.offline_dir() / "setup.exe"
        d = self.e.dl_dir() / "ODT"
        d.mkdir(parents=True, exist_ok=True)
        exe = d / "setup.exe"
        if exe.exists() and exe.stat().st_size > 1_000_000 and time.time() - exe.stat().st_mtime < 30 * 86400:
            return exe
        if FAKE:
            exe.write_bytes(b"0" * 1_100_000)
            return exe
        import requests
        self.e.log("⬇ Đang tải Office Deployment Tool từ Microsoft...")
        try:
            r = requests.get(ODT_SETUP_URL, timeout=60)
            r.raise_for_status()
            exe.write_bytes(r.content)
            return exe
        except Exception as e:              # noqa: BLE001
            self.e.log(f"Không tải được setup.exe trực tiếp ({e}), thử gói ODT...", "warn")
        pack = d / "odt.exe"
        r = requests.get(odt_latest_url(), timeout=120)
        r.raise_for_status()
        pack.write_bytes(r.content)
        run_hidden([str(pack), f"/extract:{d}", "/quiet"], timeout=300)
        if not exe.exists():
            raise RuntimeError("Không lấy được setup.exe của ODT")
        return exe

    def _run(self, label, fn):
        if self.busy or self.e.busy_tool:
            return "Đang chạy một việc khác, chờ xong rồi thử lại."
        self.busy = label

        def job():
            self.e.busy_tool = label
            self.e.log(f"▶ {label}")
            try:
                ok, detail = fn()
            except Exception as e:          # noqa: BLE001
                ok, detail = False, str(e)
            self.e.log(f"{'✔' if ok else '✖'} {label}" + (f": {detail}" if detail else ""), "ok" if ok else "err")
            self.e.st.add_history(label, "MS Office", "Xong" if ok else "Lỗi", detail)
            self.busy = ""
            self.e.busy_tool = ""
        threading.Thread(target=job, daemon=True).start()
        return ""

    def _configure(self, xml, workdir=None, mode="/configure"):
        exe = self._setup_exe()
        cfg = Path(os.environ.get("TEMP", str(BASE))) / f"winaio_office_{int(time.time())}.xml"
        cfg.write_text(xml, encoding="utf-8")
        self.e.log("Cấu hình ODT:\n" + xml.strip(), "dim")
        if FAKE:
            time.sleep(2)
            return True, ""
        code = subprocess.call([str(exe), mode, str(cfg)], cwd=str(workdir or exe.parent), creationflags=CREATE_NO_WINDOW)
        try:
            cfg.unlink()
        except OSError:
            pass
        return code == 0, "" if code == 0 else f"ODT trả mã {code}"

    def install(self, o):
        if not (o.get("apps") or o.get("project") or o.get("visio")):
            return "Chọn ít nhất 1 ứng dụng (hoặc Project / Visio)."
        ver = o.get("ver", "2024")
        name = f"Cài Microsoft Office {ver if ver != '365' else '365'} {o.get('ed', 'ProPlus')} {o.get('bit', '64')}-bit"

        def fn():
            src = str(self.offline_dir()) if self.has_offline() else ""
            self.e.log("📦 Cài OFFLINE từ " + src if src else "🌐 Cài ONLINE: Microsoft tải bộ cài trong lúc cài")
            ok, d = self._configure(office_config(o, src), workdir=src or None)
            if ok and o.get("shortcut", True):
                self.shortcuts()
            return ok, d
        return self._run(name, fn)

    def download_offline(self, o):
        def fn():
            dest = self.offline_dir()
            dest.mkdir(parents=True, exist_ok=True)
            exe = self._setup_exe()
            if exe.parent != dest and not FAKE:
                shutil.copy2(exe, dest / "setup.exe")
            self.e.log(f"⬇ Tải thư viện Office về {dest} (vài GB, mất khá lâu)...")
            return self._configure(office_config(o, str(dest)), workdir=dest, mode="/download")
        return self._run("Tải thư viện Office offline", fn)

    def uninstall(self):
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<Configuration>\n  <Remove All="TRUE" />\n'
               '  <Display Level="Full" AcceptEULA="TRUE" />\n  <RemoveMSI />\n</Configuration>\n')
        return self._run("Gỡ toàn bộ Microsoft Office", lambda: self._configure(xml))

    def shortcuts(self):
        d = office_dir()
        if not d:
            return "Chưa thấy Office (Office16) trên máy."
        made = []
        desk = Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop"
        for n, exe in OFFICE_EXES.items():
            if (d / exe).exists():
                made.append(n)
                if not FAKE and IS_WIN:
                    ps(f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{desk / (n + '.lnk')}'); "
                       f"$s.TargetPath='{d / exe}'; $s.Save()", timeout=30)
        self.e.log("🔗 Đã ghim ra Desktop: " + ", ".join(made) if made else "Không có ứng dụng Office nào để ghim.")
        return ""

    @staticmethod
    def _ospp():
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
            for sub in ("root\\Office16", "Office16"):
                p = Path(base) / "Microsoft Office" / sub / "ospp.vbs"
                if p.exists():
                    return p
        return None

    def license_status(self):
        p = self._ospp()
        if FAKE:
            return {"ok": True, "out": "LICENSE NAME: Office 24, Office24ProPlus2024R_Retail edition\nLICENSE STATUS:  ---LICENSED---\nLast 5 characters of installed product key: XXXXX"}
        if not p:
            return {"ok": False, "out": "Chưa thấy Office trên máy (không có ospp.vbs)."}
        code, out = run_hidden(f'cscript //nologo "{p}" /dstatus', shell=True, timeout=120)
        return {"ok": code == 0, "out": out}

    def enter_key(self, key):
        key = (key or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{5}(-[A-Z0-9]{5}){4}", key):
            return {"ok": False, "out": "Key không đúng dạng XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"}
        p = self._ospp()
        if FAKE:
            return {"ok": True, "out": "(chạy thử) Product key installation successful\nProduct activation successful"}
        if not p:
            return {"ok": False, "out": "Chưa thấy Office trên máy (không có ospp.vbs)."}
        c1, o1 = run_hidden(f'cscript //nologo "{p}" /inpkey:{key}', shell=True, timeout=120)
        c2, o2 = run_hidden(f'cscript //nologo "{p}" /act', shell=True, timeout=180)
        self.e.st.add_history("Nhập key Office", "MS Office", "Xong" if c2 == 0 else "Lỗi", o1 + "\n" + o2)
        return {"ok": c2 == 0, "out": o1 + "\n" + o2}


# ================================================================= NGUỒN & Ổ USB (gộp từ Power & USB Eject)
BUS = {1: "SCSI", 2: "ATAPI", 3: "ATA", 4: "1394", 5: "SSA", 6: "Fibre", 7: "USB", 8: "RAID", 9: "iSCSI", 10: "SAS",
       11: "SATA", 12: "SD", 13: "MMC", 14: "Virtual", 15: "VHD", 16: "Spaces", 17: "NVMe", 18: "SCM", 19: "UFS"}
VETO = ["Không rõ lý do", "Thiết bị legacy", "Có tệp/cửa sổ đang mở trên ổ", "Ứng dụng Windows đang dùng ổ",
        "Dịch vụ Windows đang dùng ổ", "Có chương trình đang giữ ổ", "Thiết bị khác chặn", "Driver chặn",
        "Yêu cầu không hợp lệ", "Thiếu nguồn", "Thiết bị không thể tắt", "Driver legacy", "Không đủ quyền"]

DISK_PS = r"""
$vols=@{}; Get-Volume -ErrorAction SilentlyContinue | Where-Object DriveLetter | ForEach-Object { $vols[[string]$_.DriveLetter]=$_.FileSystemLabel }
$parts=@(Get-Partition -ErrorAction SilentlyContinue)
$dd=@{}; Get-CimInstance Win32_DiskDrive -ErrorAction SilentlyContinue | ForEach-Object { $dd[[int]$_.Index]=$_ }
$out=@()
foreach($d in Get-CimInstance -Namespace root\Microsoft\Windows\Storage MSFT_Disk){
  $w=$dd[[int]$d.Number]
  $ls=@($parts | Where-Object { $_.DiskNumber -eq $d.Number -and $_.DriveLetter } | ForEach-Object { [string]$_.DriveLetter })
  $out += [ordered]@{ n=[int]$d.Number; name=[string]$d.FriendlyName; bus=[string]$d.BusType; off=[bool]$d.IsOffline;
    ro=[bool]$d.IsReadOnly; size=[double]$d.Size; sys=[bool]($d.IsSystem -or $d.IsBoot);
    pnp=$(if($w){[string]$w.PNPDeviceID}else{''}); media=$(if($w){[string]$w.MediaType}else{''});
    letters=@($ls | ForEach-Object { [ordered]@{ l=$_; label=[string]$vols[$_] } }) }
}
ConvertTo-Json -InputObject @($out) -Depth 4 -Compress
"""

FAKE_DISKS = [
    {"n": 0, "name": "Samsung SSD 980 PRO 1TB", "bus": 17, "off": False, "ro": False, "size": 1e12, "sys": True, "pnp": "", "media": "Fixed hard disk media", "letters": [{"l": "C", "label": "Windows"}]},
    {"n": 1, "name": "WDC WD20EZBX-00AYRA0", "bus": 11, "off": False, "ro": False, "size": 2e12, "sys": False, "pnp": "", "media": "Fixed hard disk media", "letters": [{"l": "D", "label": "Data"}]},
    {"n": 2, "name": "WD Elements 25A2", "bus": 7, "off": False, "ro": False, "size": 4e12, "sys": False, "pnp": "USBSTOR\\DISK", "media": "External hard disk media", "letters": [{"l": "E", "label": "Phim"}, {"l": "F", "label": "Backup"}]},
    {"n": 3, "name": "Samsung PSSD T7", "bus": 7, "off": False, "ro": False, "size": 1e12, "sys": False, "pnp": "SCSI\\DISK", "media": "External hard disk media", "letters": [{"l": "G", "label": "T7"}]},
]


class Power:
    def __init__(self, eng):
        self.e = eng
        self.busy = False
        self.shutdown_at = 0.0
        sa = eng.st.cfg.get("shutdown_at") or 0
        if sa and sa > time.time():
            self.shutdown_at = float(sa)

    # ---- nguồn & phiên
    def force_shutdown(self):
        self.e.log("⏻ TẮT MÁY NGAY (force)", "warn")
        if FAKE or not IS_WIN:
            return True
        try:
            self._shutdown_privilege()
            EWX_SHUTDOWN, EWX_FORCE, EWX_POWEROFF = 0x1, 0x4, 0x8
            if ctypes.windll.user32.ExitWindowsEx(ctypes.c_uint(EWX_SHUTDOWN | EWX_FORCE | EWX_POWEROFF), ctypes.c_uint32(0x80000000)):
                return True
        except Exception:                   # noqa: BLE001
            pass
        subprocess.Popen(["shutdown.exe", "/s", "/f", "/t", "0"], creationflags=CREATE_NO_WINDOW)
        return True

    @staticmethod
    def _shutdown_privilege():
        from ctypes import wintypes
        adv, k32 = ctypes.windll.advapi32, ctypes.windll.kernel32

        class LUID(ctypes.Structure):
            _fields_ = [("Low", wintypes.DWORD), ("High", wintypes.LONG)]

        class TP(ctypes.Structure):
            _fields_ = [("Count", wintypes.DWORD), ("Luid", LUID), ("Attr", wintypes.DWORD)]
        tok = wintypes.HANDLE()
        adv.OpenProcessToken(k32.GetCurrentProcess(), 0x20 | 0x8, ctypes.byref(tok))
        tp = TP(1, LUID(), 0x2)
        adv.LookupPrivilegeValueW(None, "SeShutdownPrivilege", ctypes.byref(tp.Luid))
        adv.AdjustTokenPrivileges(tok, False, ctypes.byref(tp), 0, None, None)
        k32.CloseHandle(tok)

    def lock(self):
        self.e.log("🔒 Khóa máy")
        if FAKE or not IS_WIN:
            return True
        return bool(ctypes.windll.user32.LockWorkStation())

    def switch_user(self):
        self.e.log("👥 Đổi người dùng")
        if FAKE or not IS_WIN:
            return True
        try:
            if ctypes.windll.wtsapi32.WTSDisconnectSession(None, ctypes.c_uint32(0xFFFFFFFF), False):
                return True
        except Exception:                   # noqa: BLE001
            pass
        tsd = Path(os.environ.get("WINDIR", "C:\\Windows")) / "System32" / "tsdiscon.exe"
        if tsd.exists():
            subprocess.Popen([str(tsd)], creationflags=CREATE_NO_WINDOW)
            return True
        return bool(ctypes.windll.user32.LockWorkStation())

    def schedule(self, mode, minutes=0, hh=0, mm=0):
        now_ = dt.datetime.now()
        if mode == "at":
            t = now_.replace(hour=int(hh) % 24, minute=int(mm) % 60, second=0, microsecond=0)
            if t <= now_:
                t += dt.timedelta(days=1)          # giờ này đã qua -> tắt vào ngày mai
        else:
            m = int(minutes)
            if m < 1:
                return "Số phút phải từ 1 trở lên"
            t = now_ + dt.timedelta(minutes=m)
        secs = max(1, int((t - now_).total_seconds()))
        if not FAKE and IS_WIN:
            run_hidden(["shutdown.exe", "/a"])
            code, out = run_hidden(["shutdown.exe", "/s", "/f", "/t", str(secs), "/c", f"{APP_TITLE}: tắt máy theo hẹn giờ"])
            if code != 0:
                return f"Hẹn giờ thất bại (shutdown.exe trả mã {code}). {out}"
        self.shutdown_at = t.timestamp()
        self.e.st.cfg["shutdown_at"] = self.shutdown_at
        self.e.st.save_config(persist=False)
        self.e.log(f"⏱ Đã hẹn ép tắt máy lúc {t:%H:%M} ngày {t:%d/%m}", "warn")
        return ""

    def cancel(self):
        if not FAKE and IS_WIN:
            code, _ = run_hidden(["shutdown.exe", "/a"])
            msg = "Đã hủy hẹn giờ tắt máy." if code == 0 else (
                "Lệnh hẹn giờ đã không còn (có thể đã bị hủy trước đó)." if self.shutdown_at else "Không có lệnh tắt máy nào đang hẹn.")
        else:
            msg = "Đã hủy hẹn giờ tắt máy."
        self.shutdown_at = 0.0
        self.e.st.cfg["shutdown_at"] = 0
        self.e.st.save_config(persist=False)
        self.e.log(msg)
        return msg

    # ---- ổ đĩa
    def disks(self):
        if FAKE or not IS_WIN:
            raw = [dict(d) for d in FAKE_DISKS]
        else:
            code, out = ps(DISK_PS, timeout=60)
            try:
                raw = json.loads(out[out.index("["):])
            except Exception:               # noqa: BLE001
                return {"err": out[:300] or f"mã {code}", "disks": []}
        for d in raw:
            media = (d.get("media") or "").lower()
            b = str(d.get("bus", "")).strip()
            d["bus_name"] = BUS.get(int(b), "Khác") if b.isdigit() else (b or "Khác")   # Windows trả số hoặc chữ (USB, SATA...)
            d["size_text"] = human(d.get("size") or 0)
            d["external"] = (d["bus_name"].upper() in ("USB", "1394", "SD", "MMC") or "external" in media
                             or "removable" in media) and not d.get("sys")
        return {"err": "", "disks": raw}

    def _disk(self, n):
        return next((d for d in self.disks()["disks"] if int(d["n"]) == int(n)), None)

    @staticmethod
    def _flush_dismount(letter, dismount=True):
        """Ghi hết dữ liệu đang đệm xuống ổ, rồi dismount (tháo ổ khỏi hệ thống tệp)."""
        from ctypes import wintypes
        k32 = ctypes.windll.kernel32
        k32.CreateFileW.restype = ctypes.c_void_p
        k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                                    wintypes.DWORD, ctypes.c_void_p]
        h = k32.CreateFileW(f"\\\\.\\{letter}:", 0xC0000000, 3, None, 3, 0, None)
        if not h or h == ctypes.c_void_p(-1).value:
            return f"{letter}: không mở được (lỗi {k32.GetLastError()})"
        try:
            k32.FlushFileBuffers(ctypes.c_void_p(h))
            if not dismount:
                return f"{letter}: đã ghi hết"
            ret = ctypes.c_ulong()
            locked = k32.DeviceIoControl(ctypes.c_void_p(h), 0x00090018, None, 0, None, 0, ctypes.byref(ret), None)
            ok = k32.DeviceIoControl(ctypes.c_void_p(h), 0x00090020, None, 0, None, 0, ctypes.byref(ret), None)
            if not ok:
                return f"{letter}: dismount lỗi {k32.GetLastError()}"
            return f"{letter}: " + ("đã ghi hết + dismount" if locked else "đã ghi hết + dismount ép (có chương trình đang mở tệp)")
        finally:
            k32.CloseHandle(ctypes.c_void_p(h))

    @staticmethod
    def _eject(pnp):
        """Yêu cầu Windows tháo thiết bị (giống Safely Remove Hardware). Trả '' nếu được, ngược lại lý do."""
        cm = ctypes.windll.cfgmgr32
        dev = ctypes.c_uint32()
        if cm.CM_Locate_DevNodeW(ctypes.byref(dev), ctypes.c_wchar_p(pnp), 0) != 0:
            return "Không tìm thấy thiết bị"
        targets = []
        parent = ctypes.c_uint32()
        if cm.CM_Get_Parent(ctypes.byref(parent), dev, 0) == 0:
            targets.append(parent.value)          # thường là thiết bị USB chứa ổ (USB\VID_...)
        targets.append(dev.value)
        reason = "Không rõ lý do"
        for t in targets:
            veto = ctypes.c_int(0)
            name = ctypes.create_unicode_buffer(260)
            r = cm.CM_Request_Device_EjectW(ctypes.c_uint32(t), ctypes.byref(veto), name, 260, 0)
            if r == 0 and veto.value == 0:
                return ""
            v = veto.value
            reason = (VETO[v] if 0 <= v < len(VETO) else f"Mã {v}") + (f" — {name.value}" if name.value else "") + f" (CR={r})"
        return reason

    def safe_remove(self, n):
        if self.busy:
            return {"ok": False, "msg": "Đang xử lý một ổ khác, thử lại sau giây lát."}
        self.busy = True
        try:
            d = self._disk(n)
            if not d:
                return {"ok": False, "msg": "Không thấy ổ này nữa (đã rút?)"}
            nm = d["name"]
            self.e.log(f"⏏ Safely Remove: {nm}")
            if FAKE or not IS_WIN:
                time.sleep(1)
                FAKE_DISKS[:] = [x for x in FAKE_DISKS if x["n"] != int(n)]
                msg = f"✓ Đã tháo an toàn “{nm}”. Có thể rút ổ ra."
                self.e.log(msg, "ok")
                return {"ok": True, "msg": msg}
            for l in d.get("letters") or []:
                self._flush_dismount(l["l"], dismount=False)
            why = self._eject(d["pnp"]) if d.get("pnp") else "Không có mã thiết bị"
            if not why:
                msg = f"✓ Đã tháo an toàn “{nm}”. Có thể rút ổ ra."
                self.e.log(msg, "ok")
                return {"ok": True, "msg": msg}
            msg = f"✗ Windows từ chối: {why}\n→ Đóng chương trình / cửa sổ đang mở tệp trên ổ rồi thử lại, hoặc dùng “Ép ngắt ổ”."
            self.e.log(msg, "err")
            return {"ok": False, "msg": msg}
        finally:
            self.busy = False

    def force_remove(self, n):
        if self.busy:
            return {"ok": False, "msg": "Đang xử lý một ổ khác, thử lại sau giây lát."}
        self.busy = True
        try:
            d = self._disk(n)
            if not d:
                return {"ok": False, "msg": "Không thấy ổ này nữa (đã rút?)"}
            nm = d["name"]
            self.e.log(f"⚡ Ép ngắt: {nm}", "warn")
            if FAKE or not IS_WIN:
                time.sleep(1.2)
                for x in FAKE_DISKS:
                    if x["n"] == int(n):
                        x["off"] = True
                msg = f"✓ Đã ngắt ổ “{nm}”. Có thể rút ra."
                self.e.log(msg, "ok")
                return {"ok": True, "msg": msg}
            for l in d.get("letters") or []:
                self.e.log("  " + self._flush_dismount(l["l"]))
            code, out = ps(f"Set-Disk -Number {int(n)} -IsOffline $true", timeout=60)
            self.e.log("  Disk → Offline (tạm thời)" if code == 0 else f"  Không đặt được Offline: {out[:200]}")
            why = self._eject(d["pnp"]) if d.get("pnp") else "Không có mã thiết bị"
            if not why:
                msg = f"✓ Đã ngắt ổ “{nm}”. Có thể rút ra."
            elif code == 0:
                msg = (f"! Windows vẫn chưa cho tháo ({why}).\n✓ Nhưng ổ đã được ghi hết dữ liệu + dismount + Offline → AN TOÀN để rút. "
                       "Cắm lại hoặc khởi động lại máy, ổ sẽ tự Online.")
            else:
                msg = f"✗ Không ngắt được ({why}). Hãy tắt máy rồi rút ổ."
            self.e.log(msg, "ok" if (not why or code == 0) else "err")
            return {"ok": not why or code == 0, "msg": msg}
        finally:
            self.busy = False


# ================================================================= TEST MÁY: PIN LAPTOP
FAKE_BATTERY = {"has": True, "ac": False, "charging": False, "pct": 78, "left_min": 214,
                "batteries": [{"name": "DELL 9JRV0", "maker": "SMP", "chem": "LiP", "serial": "1234",
                               "design": 54000, "full": 46310, "cycles": 312, "health": 86}]}


def battery_info():
    """% pin hiện tại (GetSystemPowerStatus) + độ chai pin từ báo cáo powercfg /batteryreport của Windows."""
    if FAKE or not IS_WIN:
        return json.loads(json.dumps(FAKE_BATTERY))

    class SPS(ctypes.Structure):
        _fields_ = [("ac", ctypes.c_ubyte), ("flag", ctypes.c_ubyte), ("pct", ctypes.c_ubyte), ("saver", ctypes.c_ubyte),
                    ("life", ctypes.c_ulong), ("full", ctypes.c_ulong)]
    st = SPS()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(st))
    has = not (st.flag & 128) and st.flag != 255
    res = {"has": has, "ac": st.ac == 1, "charging": bool(st.flag & 8), "pct": st.pct if st.pct <= 100 else None,
           "left_min": (st.life // 60) if st.life not in (0xFFFFFFFF, 4294967295) else None, "batteries": []}
    if not has:
        return res
    out = Path(os.environ.get("TEMP", str(BASE))) / "winaio_battery.xml"
    run_hidden(["powercfg", "/batteryreport", "/xml", "/output", str(out)], timeout=60)
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(out).getroot()
        ns = {"b": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else {}
        q = (lambda e, t: e.findtext(f"b:{t}", default="", namespaces=ns)) if ns else (lambda e, t: e.findtext(t, default=""))
        for b in root.iter(f"{{{ns['b']}}}Battery" if ns else "Battery"):
            design, full = int(q(b, "DesignCapacity") or 0), int(q(b, "FullChargeCapacity") or 0)
            res["batteries"].append({"name": q(b, "Id"), "maker": q(b, "Manufacturer"), "chem": q(b, "Chemistry"),
                                     "serial": q(b, "SerialNumber"), "design": design, "full": full,
                                     "cycles": int(q(b, "CycleCount") or 0) or None,
                                     "health": round(full * 100 / design) if design else None})
    except Exception as e:                  # noqa: BLE001
        res["err"] = f"Không đọc được báo cáo pin: {e}"
    finally:
        try:
            out.unlink()
        except OSError:
            pass
    return res


def battery_report_html():
    if FAKE or not IS_WIN:
        return ""
    out = Path(os.environ.get("TEMP", str(BASE))) / f"BaoCaoPin_{os.environ.get('COMPUTERNAME', 'PC')}.html"
    code, txt = run_hidden(["powercfg", "/batteryreport", "/output", str(out)], timeout=60)
    if code != 0 or not out.exists():
        return txt or "Không tạo được báo cáo pin"
    os.startfile(str(out))                   # noqa: S606
    return ""


# ================================================================= TEST MÁY: SỨC KHỎE Ổ CỨNG (SMART)
DISK_HEALTH_PS = r"""
$ErrorActionPreference='SilentlyContinue'
$fp=@{}; Get-CimInstance -Namespace root\wmi -ClassName MSStorageDriver_FailurePredictStatus | ForEach-Object { $fp[(($_.InstanceName -replace '_\d+$','')).ToUpper()]=[bool]$_.PredictFailure }
$pnp=@{}; Get-CimInstance Win32_DiskDrive | ForEach-Object { $pnp[[string]$_.Index]=([string]$_.PNPDeviceID).ToUpper() }
$out=@(Get-PhysicalDisk | Sort-Object { [int]$_.DeviceId } | ForEach-Object {
  $r=$_ | Get-StorageReliabilityCounter
  $id=[string]$_.DeviceId; $pf=$null; if($pnp[$id] -and $fp.ContainsKey($pnp[$id])){ $pf=$fp[$pnp[$id]] }
  [ordered]@{ id=[int]$id; name=[string]$_.FriendlyName; media=[string]$_.MediaType; bus=[string]$_.BusType; size=[math]::Round($_.Size/1GB);
    health=[string]$_.HealthStatus; op=[string]($_.OperationalStatus -join ', '); serial=([string]$_.SerialNumber).Trim(); fw=[string]$_.FirmwareVersion;
    temp=$r.Temperature; tmax=$r.TemperatureMax; wear=$r.Wear; hours=$r.PowerOnHours; starts=$r.StartStopCycleCount;
    rerr=$r.ReadErrorsTotal; werr=$r.WriteErrorsTotal; runc=$r.ReadErrorsUncorrected; wunc=$r.WriteErrorsUncorrected; predict=$pf } })
ConvertTo-Json -InputObject $out -Depth 3 -Compress
"""

FAKE_DISK_HEALTH = [
    {"id": 0, "name": "Samsung SSD 980 PRO 1TB", "media": "SSD", "bus": "NVMe", "size": 932, "health": "Healthy", "op": "OK",
     "serial": "S5GXNF0R123456", "fw": "5B2QGXA7", "temp": 41, "tmax": 68, "wear": 6, "hours": 5120, "starts": 1830,
     "rerr": 0, "werr": 0, "runc": 0, "wunc": 0, "predict": False},
    {"id": 1, "name": "WDC WD20EZBX-00AYRA0", "media": "HDD", "bus": "SATA", "size": 1863, "health": "Warning", "op": "OK",
     "serial": "WD-WX12A3456789", "fw": "01.01A01", "temp": 47, "tmax": 55, "wear": None, "hours": 28750, "starts": 4210,
     "rerr": 12, "werr": 0, "runc": 3, "wunc": 0, "predict": False},
]


def disk_health():
    """Sức khỏe từng ổ: trạng thái Windows, dự báo hỏng SMART, nhiệt độ, độ hao mòn SSD, giờ chạy, lỗi đọc / ghi."""
    if FAKE or not IS_WIN:
        raw = json.loads(json.dumps(FAKE_DISK_HEALTH))
    else:
        code, out = ps(DISK_HEALTH_PS, timeout=120)
        try:
            raw = json.loads(out[out.index("["):])
        except Exception:                   # noqa: BLE001
            return {"err": out[:300] or f"mã {code}", "disks": []}
    for d in raw:
        h = (d.get("health") or "").lower()
        why = []
        if h in ("unhealthy", "2"):
            why.append("Windows báo ổ LỖI")
        if d.get("predict"):
            why.append("SMART dự báo ổ sắp hỏng")
        if (d.get("runc") or 0) + (d.get("wunc") or 0) > 0:
            why.append(f"{(d.get('runc') or 0) + (d.get('wunc') or 0)} lỗi đọc / ghi không sửa được")
        bad = bool(why)
        warn = []
        if h in ("warning", "1"):
            warn.append("Windows cảnh báo ổ")
        if (d.get("wear") or 0) >= 80:
            warn.append(f"SSD đã hao mòn {d['wear']}%")
        lim = 70 if (d.get("media") or "").upper() == "SSD" or (d.get("bus") or "").upper() == "NVME" else 55
        if (d.get("temp") or 0) >= lim:
            warn.append(f"Nhiệt độ cao {d['temp']}°C")
        if (d.get("rerr") or 0) + (d.get("werr") or 0) > 0 and not bad:
            warn.append(f"{(d.get('rerr') or 0) + (d.get('werr') or 0)} lỗi đọc / ghi đã tự sửa")
        d["verdict"] = "bad" if bad else ("warn" if warn else "ok")
        d["notes"] = why + warn
        ssd = (d.get("media") or "").upper() == "SSD" or (d.get("bus") or "").upper() == "NVME"
        d["life"] = (100 - d["wear"]) if ssd and isinstance(d.get("wear"), (int, float)) else None   # chỉ SSD mới có hao mòn
    return {"err": "", "disks": raw}


# ================================================================= HỆ THỐNG: KHỞI ĐỘNG ĐẶC BIỆT
FAKE_BOOT_ENTRIES = [{"id": "{9dea862c-5cdd-4e70-acc1-f32b344d4795}", "name": "Windows Boot Manager"},
                     {"id": "{a1b2c3d4-0000-1111-2222-333344445555}", "name": "UEFI: SanDisk Ultra USB 3.0"},
                     {"id": "{b2c3d4e5-6666-7777-8888-999900001111}", "name": "UEFI: WDC WD20EZBX"}]


def firmware_type():
    if FAKE or not IS_WIN:
        return "UEFI"
    t = ctypes.c_uint(0)
    try:
        if ctypes.windll.kernel32.GetFirmwareType(ctypes.byref(t)):
            return {1: "Legacy BIOS", 2: "UEFI"}.get(t.value, "Không rõ")
    except Exception:                       # noqa: BLE001
        pass
    return "Không rõ"


def boot_status():
    if FAKE or not IS_WIN:
        return {"fw": "UEFI", "safe_now": False, "safe_set": "", "entries": FAKE_BOOT_ENTRIES}
    _, cur = run_hidden(["bcdedit", "/enum", "{current}"], timeout=30)
    m = re.search(r"^\s*safeboot\s+(\S+)", cur or "", re.I | re.M)
    fw = firmware_type()
    return {"fw": fw, "safe_now": bool(ctypes.windll.user32.GetSystemMetrics(67)),
            "safe_set": m.group(1) if m else "", "entries": boot_entries() if fw == "UEFI" else []}


def boot_entries():
    """Danh sách mục khởi động trong UEFI (ổ cứng, USB, mạng...) từ bcdedit /enum firmware."""
    _, out = run_hidden(["bcdedit", "/enum", "firmware", "/v"], timeout=30)
    res = []
    for blk in re.split(r"\r?\n\s*\r?\n", out or ""):
        lines = [l for l in blk.splitlines() if l.strip() and not set(l.strip()) <= set("-")]
        kv = [re.split(r"\s{2,}", l.strip(), maxsplit=1) for l in lines]
        kv = [x for x in kv if len(x) == 2]
        gid = next((v for _, v in kv if re.fullmatch(r"\{[0-9a-fA-F-]{36}\}", v)), "")
        if not gid:
            continue
        name = next((v for k, v in kv if k.lower() in ("description", "mô tả", "beschreibung", "descripción")), "")
        if not name:                          # Windows ngôn ngữ khác: lấy giá trị chữ đầu tiên không phải mã / đường dẫn
            name = next((v for _, v in kv if not re.match(r"^(\{|partition=|\\\\|\d+$|Yes$|No$|Có$|Không$)", v)), "")
        if name and "fwbootmgr" not in gid.lower():
            res.append({"id": gid, "name": name})
    return res


def _restart(args, label):
    if FAKE or not IS_WIN:
        return 0, f"(chạy thử) {label}"
    return run_hidden(["shutdown.exe"] + args, timeout=30)


def boot_action(kind, arg=""):
    """kind: bios / recovery / once (arg = mã ổ) / safe (arg = minimal|network|cmd) / normal."""
    if kind == "bios":
        if firmware_type() != "UEFI":
            return "Máy đang khởi động kiểu Legacy BIOS nên Windows không đưa thẳng vào BIOS được. Khởi động lại rồi bấm phím vào BIOS của hãng (thường là F2, Del, F10, Esc)."
        code, out = _restart(["/r", "/fw", "/t", "0"], "vào BIOS / UEFI")
        return "" if code == 0 else f"Không vào được BIOS: {out}"
    if kind == "recovery":
        code, out = _restart(["/r", "/o", "/t", "0"], "menu Recovery nâng cao")
        return "" if code == 0 else f"Không mở được menu Recovery: {out}"
    if kind == "once":
        if not re.fullmatch(r"\{[0-9a-fA-F-]{36}\}", arg or ""):
            return "Mục khởi động không hợp lệ"
        if not FAKE and IS_WIN:
            code, out = run_hidden(["bcdedit", "/set", "{fwbootmgr}", "bootsequence", arg], timeout=30)
            if code != 0:
                return f"Không đặt được ổ khởi động: {out}"
        code, out = _restart(["/r", "/t", "0"], "khởi động vào ổ đã chọn")
        return "" if code == 0 else out
    if kind == "safe":
        mode = {"minimal": "minimal", "network": "network", "cmd": "minimal"}.get(arg)
        if not mode:
            return "Kiểu Safe Mode không hợp lệ"
        if not FAKE and IS_WIN:
            code, out = run_hidden(["bcdedit", "/set", "{current}", "safeboot", mode], timeout=30)
            if code != 0:
                return f"Không đặt được Safe Mode: {out}"
            if arg == "cmd":
                run_hidden(["bcdedit", "/set", "{current}", "safebootalternateshell", "yes"], timeout=30)
            else:
                run_hidden(["bcdedit", "/deletevalue", "{current}", "safebootalternateshell"], timeout=30)
        code, out = _restart(["/r", "/t", "0"], "vào Safe Mode")
        return "" if code == 0 else out
    if kind == "normal":
        if not FAKE and IS_WIN:
            run_hidden(["bcdedit", "/deletevalue", "{current}", "safebootalternateshell"], timeout=30)
            code, out = run_hidden(["bcdedit", "/deletevalue", "{current}", "safeboot"], timeout=30)
            if code != 0 and "safeboot" in boot_status().get("safe_set", "safeboot"):
                return f"Không tắt được Safe Mode: {out}"
        return ""
    return "Lệnh không hợp lệ"


# ================================================================= API cho giao diện
class Api:
    def __init__(self, eng, app=None):
        self._e = eng
        self._s = eng.st
        self._app = app
        self._admin = False
        self._upd = {}
        self._quit_fn = None

    def _need_admin(self):
        if not self._admin:
            raise PermissionError("Cần mở khóa Admin")

    # ---- đọc
    def init(self):
        return {"title": APP_TITLE, "version": APP_VERSION, "repo": REPO, "browser": getattr(self, "_browser", False), "theme": self._s.cfg.get("theme", "light"), "skin": self._s.cfg.get("skin", "default"),
                "tools": [{"id": t[0], "group": t[1], "label": t[2], "confirm": t[5], "kind": t[3], "fn": t[4]} for t in TOOLS],
                "quick": [{"label": q[0], "target": q[1]} for q in QUICK], "is_win": IS_WIN or FAKE,
                "iso_langs": mgr.ISO_LANGS,
                "iso_mg": [{"icon": i, "name": n, "url": ISO_MG + u, "note": d} for i, n, u, d in ISO_MG_PAGES],
                "default_pw": self._s.cfg.get("admin_hash") == hash_pw(DEFAULT_PW, self._s.cfg.get("admin_salt", ""))}

    def groups(self):
        return {"columns": self._s.columns(), "layout": self._s.layout(), "groups": self._s.groups(),
                "fit_n": self._s.cfg.get("fit_n") if self._s.layout() == "fit" else None}

    def set_layout(self, mode):
        self._need_admin()
        self._s.cfg["layout"] = mode if mode in ("fit", "grid", "columns") else "fit"
        self._s.cfg["layout_v211"] = True
        self._s.save_config()
        return True

    def auto_arrange(self, sort_apps=False):
        """Tự sắp xếp nhóm: chia các nhóm vào cột sao cho chiều cao đều nhau (giữ thứ tự nhóm);
        kiểu Lưới: nhóm nhiều nút lên trước để mỗi hàng cao gần bằng nhau. Tùy chọn xếp nút A-Z."""
        self._need_admin()
        st = self._s
        n = st.columns()
        with st.lock:
            rows = st.db.execute("SELECT g.id, (SELECT COUNT(*) FROM apps a WHERE a.group_id=g.id) FROM groups g "
                                 "ORDER BY " + ("gpos, id" if st.layout() == "grid" else "col, ord, id")).fetchall()
            h, ords = [0] * n, [0] * n
            for gid, cnt in rows:                    # cột dọc: nhóm kế tiếp vào cột đang thấp nhất
                c = min(range(n), key=lambda i: (h[i], i))
                st.db.execute("UPDATE groups SET col=?, ord=? WHERE id=?", (c, ords[c], gid))
                h[c] += 2 + cnt
                ords[c] += 1
            for k, (gid, _) in enumerate(sorted(rows, key=lambda r: -r[1])):
                st.db.execute("UPDATE groups SET gpos=? WHERE id=?", (k, gid))
            if sort_apps:
                for gid, _ in rows:
                    ids = [r[0] for r in st.db.execute("SELECT id FROM apps WHERE group_id=? ORDER BY name COLLATE NOCASE", (gid,))]
                    for k, x in enumerate(ids):
                        st.db.execute("UPDATE apps SET ord=? WHERE id=?", (k, x))
            st.commit()
        return True

    def set_columns(self, n):
        self._need_admin()
        self._s.cfg["columns"] = max(2, min(6, int(n)))
        self._s.save_config()
        if self._s.layout() == "columns":
            with self._s.lock:
                self._s.auto_columns(all_groups=True)    # chia lại các nhóm cho đều theo số cột mới
                self._s.commit()
        return True

    _done_cache = (None, None, 0)
    _si_obj, _si_n = None, 0

    def state(self, since=0, si=None):
        """Gọi 0,7 giây / lần: chỉ gửi phần thay đổi (thông tin máy chỉ gửi lại khi đổi, đếm 'xong hôm nay' chỉ tính lại khi có nhật ký mới)."""
        e = self._e
        with e.lock:
            logs = [l for l in e.logs if l[0] > since]
            q = list(e.queue)
        today = dt.datetime.now().strftime("%d/%m/%Y")
        hv = getattr(self._s, "hist_ver", 0)
        if self._done_cache[:2] != (today, hv):
            with self._s.lock:
                n = self._s.db.execute("SELECT COUNT(*) FROM history WHERE ts LIKE ? AND status IN ('Xong','Đã mở trang web')",
                                       (today + "%",)).fetchone()[0]
            self._done_cache = (today, hv, n)
        done_today = self._done_cache[2]
        if e.sysinfo is not self._si_obj:              # giữ tham chiếu -> so "is" chắc chắn, không nhầm khi đọc lại
            self._si_obj, self._si_n = e.sysinfo, self._si_n + 1
        siv = self._si_n
        return {"logs": logs, "cur": e.cur, "queue": q, "batch": [e.batch_i, e.batch_n], "results": e.results,
                "checks": e.checks, "winget": e.winget, "admin": self._admin, "busy_tool": e.busy_tool, "si": siv,
                "sysinfo": None if (si is not None and si == siv) else e.sysinfo,
                "done_today": done_today, "running": bool(e.worker and e.worker.is_alive()),
                "shutdown_at": e.power.shutdown_at, "now": time.time(), "upd": self._upd,
                "wg_checked": getattr(e, "wg_checked", 0), "upg_n": getattr(e, "upg_n", None)}

    def history(self, limit=1000):
        with self._s.lock:
            return [dict(r) for r in self._s.db.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (int(limit),))]

    def settings(self):
        self._need_admin()
        c = self._s.cfg
        return {"download_dir": c.get("download_dir"), "keep_installer": c.get("keep_installer", True),
                "winget_auto": c.get("winget_auto", True), "winget": self._e.winget, "data_dir": str(DATA), "dl_path": str(self._e.dl_path()), "on_disk": self._s.on_disk}

    # ---- admin
    def unlock(self, pw):
        c = self._s.cfg
        if hash_pw(pw or "", c.get("admin_salt", "")) == c.get("admin_hash"):
            self._admin = True
            self._e.log("🔓 Đã mở khóa Admin: hiện nút ✎ để sửa tên, đổi nguồn.")
            return True
        return False

    def lock_admin(self):
        self._admin = False
        self._e.log("🔒 Đã khóa Admin.")
        return True

    def change_password(self, old, new):
        self._need_admin()
        c = self._s.cfg
        if hash_pw(old or "", c.get("admin_salt", "")) != c.get("admin_hash"):
            return "Mật khẩu cũ không đúng"
        if len(new or "") < 4:
            return "Mật khẩu mới cần ít nhất 4 ký tự"
        c["admin_salt"] = secrets.token_hex(8)
        c["admin_hash"] = hash_pw(new, c["admin_salt"])
        self._s.save_config()
        return ""

    def save_settings(self, d):
        self._need_admin()
        for k in ("download_dir", "keep_installer", "winget_auto"):
            if k in d:
                self._s.cfg[k] = d[k]
        self._s.save_config()
        return True

    def set_theme(self, t):
        self._s.cfg["theme"] = "dark" if t == "dark" else "light"
        self._s.save_config()
        return True

    def set_skin(self, k):
        """Giao diện: default (Mặc định, có Sáng / Tối) hoặc g01 (Giao diện 01 - xanh neon)."""
        self._s.cfg["skin"] = k if k in ("default", "g01", "g01l") else "default"
        self._s.save_config()
        return True

    # ---- sửa nút / nhóm (chỉ Admin)
    def save_app(self, a):
        self._need_admin()
        st = self._s
        with st.lock:
            vals = (a.get("icon", "").strip(), a.get("name", "").strip() or "Nút mới", a.get("src", "").strip(),
                    a.get("args", "").strip(), a.get("note", "").strip(), int(a["group_id"]))
            if a.get("id"):
                old = st.app(int(a["id"]))
                if old and old["group_id"] != int(a["group_id"]):      # đổi nhóm -> xuống cuối nhóm mới
                    o = st.db.execute("SELECT COALESCE(MAX(ord),-1)+1 FROM apps WHERE group_id=?", (int(a["group_id"]),)).fetchone()[0]
                    st.db.execute("UPDATE apps SET ord=? WHERE id=?", (o, int(a["id"])))
                st.db.execute("UPDATE apps SET icon=?, name=?, src=?, args=?, note=?, group_id=? WHERE id=?", vals + (int(a["id"]),))
            else:
                o = st.db.execute("SELECT COALESCE(MAX(ord),-1)+1 FROM apps WHERE group_id=?", (int(a["group_id"]),)).fetchone()[0]
                st.db.execute("INSERT INTO apps(icon, name, src, args, note, group_id, ord) VALUES(?,?,?,?,?,?,?)", vals + (o,))
            st.commit()
        self._e.log(f"✎ Đã lưu nút: {vals[1]}")
        return True

    def delete_app(self, aid):
        self._need_admin()
        with self._s.lock:
            self._s.db.execute("DELETE FROM apps WHERE id=?", (int(aid),))
            self._s.commit()
        return True

    def move_app(self, aid, delta):
        self._need_admin()
        st = self._s
        a = st.app(int(aid))
        if not a:
            return False
        with st.lock:
            ids = [r[0] for r in st.db.execute("SELECT id FROM apps WHERE group_id=? ORDER BY ord, id", (a["group_id"],))]
            i = ids.index(a["id"])
            j = max(0, min(len(ids) - 1, i + int(delta)))
            ids.insert(j, ids.pop(i))
            for k, x in enumerate(ids):
                st.db.execute("UPDATE apps SET ord=? WHERE id=?", (k, x))
            st.commit()
        return True

    def save_group(self, gid, name):
        self._need_admin()
        st = self._s
        name = (name or "").strip().upper() or "NHÓM MỚI"
        with st.lock:
            if gid:
                st.db.execute("UPDATE groups SET name=? WHERE id=?", (name, int(gid)))
            else:                                   # nhóm mới -> cuối cột đang ngắn nhất
                n = st.columns()
                h = [0] * n
                for col, napps in st.db.execute("SELECT g.col, (SELECT COUNT(*) FROM apps a WHERE a.group_id=g.id) FROM groups g"):
                    h[min(int(col or 0), n - 1)] += 2 + napps
                c = min(range(n), key=lambda i: (h[i], i))
                o = st.db.execute("SELECT COALESCE(MAX(ord),-1)+1 FROM groups WHERE col=?", (c,)).fetchone()[0]
                gp = st.db.execute("SELECT COALESCE(MAX(gpos),-1)+1 FROM groups").fetchone()[0]
                st.db.execute("INSERT INTO groups(name, ord, col, gpos) VALUES(?,?,?,?)", (name, o, c, gp))
            st.commit()
        return True

    def delete_group(self, gid):
        self._need_admin()
        with self._s.lock:
            self._s.db.execute("DELETE FROM apps WHERE group_id=?", (int(gid),))
            self._s.db.execute("DELETE FROM groups WHERE id=?", (int(gid),))
            self._s.commit()
        return True

    def move_group(self, gid, way):
        """way: up / down (trong cột), left / right (sang cột bên cạnh, giữ vị trí hàng)."""
        self._need_admin()
        st = self._s
        n = st.columns()
        if st.layout() == "grid":
            # Lưới: đổi chỗ với ô bên cạnh (trái / phải) hoặc ô ngay trên / dưới (cách n ô)
            with st.lock:
                ids = [r[0] for r in st.db.execute("SELECT id FROM groups ORDER BY gpos, id")]
                i = ids.index(int(gid))
                if st.layout() == "fit":            # tự vừa màn hình: chỉ đổi thứ tự trước / sau
                    way = {"left": "prev", "up": "prev", "right": "next", "down": "next"}.get(way, way)
                step = {"left": -1, "right": 1, "up": -n, "down": n, "prev": -1, "next": 1}.get(way, 0)
                if way == "left" and i % n == 0 or way == "right" and (i % n == n - 1 or i == len(ids) - 1):
                    return False
                j = i + step
                if j >= len(ids):
                    j = len(ids) - 1              # hàng dưới chưa đủ ô -> xuống cuối
                if j < 0 or j == i:
                    return False
                ids[i], ids[j] = ids[j], ids[i]
                for k, x in enumerate(ids):
                    st.db.execute("UPDATE groups SET gpos=? WHERE id=?", (k, x))
                st.commit()
            return True
        with st.lock:
            rows = st.db.execute("SELECT id, col FROM groups ORDER BY col, ord, id").fetchall()
            cols = [[] for _ in range(n)]
            for gid_, col in rows:
                cols[min(int(col or 0), n - 1)].append(gid_)
            c = next(i for i, x in enumerate(cols) if int(gid) in x)
            i = cols[c].index(int(gid))
            if way in ("up", "down", -1, 1):
                j = max(0, min(len(cols[c]) - 1, i + (-1 if way in ("up", -1) else 1)))
                if j == i:
                    return False
                cols[c].insert(j, cols[c].pop(i))
            else:
                c2 = c + (-1 if way == "left" else 1)
                if not 0 <= c2 < n:
                    return False
                cols[c2].insert(min(i, len(cols[c2])), cols[c].pop(i))
            for ci, ids in enumerate(cols):
                for k, x in enumerate(ids):
                    st.db.execute("UPDATE groups SET col=?, ord=? WHERE id=?", (ci, k, x))
            st.commit()
        return True

    def drop_group(self, gid, target=None, after=False, col=None):
        """Kéo thả nhóm: đặt nhóm gid ngay trước / sau nhóm target (kiểu Lưới / Tự vừa màn hình: theo thứ tự;
        kiểu Cột dọc: vào cột của target). target rỗng + col: đưa xuống cuối cột col."""
        self._need_admin()
        st = self._s
        gid = int(gid)
        target = int(target) if target not in (None, "", 0) else None
        if target == gid:
            return False
        with st.lock:
            if st.layout() == "grid":
                ids = [r[0] for r in st.db.execute("SELECT id FROM groups ORDER BY gpos, id")]
                ids.remove(gid)
                k = ids.index(target) + (1 if after else 0) if target in ids else len(ids)
                ids.insert(k, gid)
                for i, x in enumerate(ids):
                    st.db.execute("UPDATE groups SET gpos=? WHERE id=?", (i, x))
            else:
                n = st.columns()
                cols = [[] for _ in range(n)]
                for g_, c_ in st.db.execute("SELECT id, col FROM groups ORDER BY col, ord, id").fetchall():
                    cols[min(int(c_ or 0), n - 1)].append(g_)
                for c_ in cols:
                    if gid in c_:
                        c_.remove(gid)
                if target is not None:
                    c = next((i for i, c_ in enumerate(cols) if target in c_), 0)
                    cols[c].insert(cols[c].index(target) + (1 if after else 0), gid)
                else:
                    cols[max(0, min(n - 1, int(col or 0)))].append(gid)
                for ci, c_ in enumerate(cols):
                    for k, x in enumerate(c_):
                        st.db.execute("UPDATE groups SET col=?, ord=? WHERE id=?", (ci, k, x))
            st.commit()
        return True

    def fit_save(self, cols):
        """Kiểu Tự vừa màn hình: lưu cách chia nhóm vào cột (tool tự tính lần đầu) -> lần sau giữ nguyên,
        nút ◀ ▲ ▼ ▶ / kéo thả di chuyển chính xác. cols = [[id nhóm cột 1...], [cột 2...], ...]."""
        st = self._s
        with st.lock:
            for ci, ids in enumerate(cols):
                for k, x in enumerate(ids):
                    st.db.execute("UPDATE groups SET col=?, ord=? WHERE id=?", (ci, k, int(x)))
            st.cfg["fit_n"] = len(cols)
            st.commit()
        st.save_config(persist=st.on_disk)
        return True

    def fit_reset(self):
        self._need_admin()
        self._s.cfg.pop("fit_n", None)
        self._s.save_config(persist=self._s.on_disk)
        return True

    # ---- tab Web
    def web_list(self):
        return self._s.web_list()

    def web_save(self, w):
        self._need_admin()
        st = self._s
        url = (w.get("url") or "").strip()
        if url and not re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I):
            url = "https://" + url
        name = (w.get("name") or "").strip() or re.sub(r"^https?://(www\.)?", "", url).split("/")[0] or "Trang web"
        grp = (w.get("grp") or "").strip().upper() or "HAY DÙNG"
        icon = (w.get("icon") or "").strip() or "🌐"
        with st.lock:
            if w.get("id"):
                st.db.execute("UPDATE weblinks SET grp=?, icon=?, name=?, url=? WHERE id=?", (grp, icon, name, url, int(w["id"])))
            else:
                o = st.db.execute("SELECT COALESCE(MAX(ord),-1)+1 FROM weblinks").fetchone()[0]
                st.db.execute("INSERT INTO weblinks(grp, icon, name, url, ord) VALUES(?,?,?,?,?)", (grp, icon, name, url, o))
            st.commit()
        return True

    # ---- Hồ sơ cài đặt (preset)
    def preset_list(self):
        return self._s.preset_list()

    def preset_save(self, p):
        self._need_admin()
        st = self._s
        name = (p.get("name") or "").strip() or "Hồ sơ mới"
        row = (name, (p.get("icon") or "📋").strip(), json.dumps([str(x) for x in p.get("apps") or []], ensure_ascii=False),
               json.dumps([str(x) for x in p.get("tools") or []]), json.dumps(p.get("opts") or {}))
        with st.lock:
            if p.get("id"):
                st.db.execute("UPDATE presets SET name=?, icon=?, apps=?, tools=?, opts=? WHERE id=?", row + (int(p["id"]),))
            else:
                o = st.db.execute("SELECT COALESCE(MAX(ord),-1)+1 FROM presets").fetchone()[0]
                st.db.execute("INSERT INTO presets(name, icon, apps, tools, opts, ord) VALUES(?,?,?,?,?,?)", row + (o,))
            st.commit()
        return True

    def preset_delete(self, pid):
        self._need_admin()
        with self._s.lock:
            self._s.db.execute("DELETE FROM presets WHERE id=?", (int(pid),))
            self._s.commit()
        return True

    def font_cfg(self, url=None):
        """Link tải bộ font tiếng Việt (.zip) do Admin gắn. Gọi không tham số -> đọc."""
        if url is None:
            return self._s.cfg.get("font_pack_url") or FONT_PACK
        self._need_admin()
        self._s.cfg["font_pack_url"] = url.strip()
        self._s.save_config(persist=True)
        return True

    def web_delete(self, wid):
        self._need_admin()
        with self._s.lock:
            self._s.db.execute("DELETE FROM weblinks WHERE id=?", (int(wid),))
            self._s.commit()
        return True

    def web_move(self, wid, delta):
        """Đổi chỗ với nút trước / sau trong cùng nhóm."""
        self._need_admin()
        st = self._s
        with st.lock:
            rows = st.db.execute("SELECT id, grp FROM weblinks ORDER BY ord, id").fetchall()
            ids = [r[0] for r in rows]
            grp = dict(rows).get(int(wid))
            same = [r[0] for r in rows if r[1] == grp]
            k = same.index(int(wid))
            j = k + int(delta)
            if not 0 <= j < len(same):
                return False
            a, b = ids.index(same[k]), ids.index(same[j])
            ids[a], ids[b] = ids[b], ids[a]
            for i, x in enumerate(ids):
                st.db.execute("UPDATE weblinks SET ord=? WHERE id=?", (i, x))
            st.commit()
        return True

    def swap_groups(self, a, b):
        """Đổi chỗ 2 nhóm (thứ tự và cột)."""
        self._need_admin()
        st = self._s
        with st.lock:
            ra = st.db.execute("SELECT gpos, col, ord FROM groups WHERE id=?", (int(a),)).fetchone()
            rb = st.db.execute("SELECT gpos, col, ord FROM groups WHERE id=?", (int(b),)).fetchone()
            if not ra or not rb:
                return False
            st.db.execute("UPDATE groups SET gpos=?, col=?, ord=? WHERE id=?", (rb[0], rb[1], rb[2], int(a)))
            st.db.execute("UPDATE groups SET gpos=?, col=?, ord=? WHERE id=?", (ra[0], ra[1], ra[2], int(b)))
            st.commit()
        return True

    def drop_app(self, aid, gid, before=None):
        """Kéo thả nút: đưa nút aid vào nhóm gid, đứng trước nút before (rỗng = cuối nhóm)."""
        self._need_admin()
        st = self._s
        aid, gid = int(aid), int(gid)
        before = int(before) if before not in (None, "", 0) else None
        if before == aid:
            return False
        with st.lock:
            st.db.execute("UPDATE apps SET group_id=? WHERE id=?", (gid, aid))
            ids = [r[0] for r in st.db.execute("SELECT id FROM apps WHERE group_id=? AND id<>? ORDER BY ord, id", (gid, aid))]
            ids.insert(ids.index(before) if before in ids else len(ids), aid)
            for k, x in enumerate(ids):
                st.db.execute("UPDATE apps SET ord=? WHERE id=?", (k, x))
            st.commit()
        return True

    def export_data(self):
        self._need_admin()
        self._s.ensure_disk()
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        p = BACKUP_DIR / f"WinAIO_nut_{dt.datetime.now():%Y%m%d_%H%M%S}.json"
        save_json(p, self._s.export_data())
        open_target(str(BACKUP_DIR))
        return str(p)

    def import_file(self, path):
        self._need_admin()
        data = load_json(path, None)
        if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
            return "File không đúng định dạng bản xuất của Win AIO"
        self.export_data_silent()
        self._s.import_data(data)
        return ""

    def export_data_silent(self):
        self._s.ensure_disk()
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        save_json(BACKUP_DIR / f"WinAIO_truoc_khi_doi_{dt.datetime.now():%Y%m%d_%H%M%S}.json", self._s.export_data())

    def reset_defaults(self):
        self._need_admin()
        self.export_data_silent()
        self._s.load_defaults()
        return True

    def clear_history(self):
        self._need_admin()
        with self._s.lock:
            self._s.db.execute("DELETE FROM history")
            self._s.commit()
        return True

    def test_source(self, src):
        """Kiểm tra nhanh link: là file tải được hay trang web."""
        kind = src_kind(src)
        if kind == "github":
            try:
                url, tag = resolve_github(src)
                return f"Bản mới nhất {tag}: {url.rsplit('/', 1)[-1]}"
            except Exception as e:          # noqa: BLE001
                return "Lỗi: " + nice_err(e)
        if kind != "web":
            if kind == "file":
                p = Path(os.path.expandvars(src))
                p = p if p.is_absolute() else BASE / p
                return f"File trên máy: {'CÓ' if p.exists() else 'KHÔNG THẤY'} ({p})"
            return {"winget": "Cài bằng winget (Windows tự tải bản mới nhất).", "cmd": "Chạy lệnh Windows.",
                    "open": "Mở link bằng trình duyệt (không tải, không cài).", "office": "Mở cửa sổ cài MS Office.",
                    "none": "Chưa nhập nguồn."}.get(kind, "")
        if FAKE:
            return "File tải được: setup.exe (40.0 MB)"
        try:
            import requests
            r = requests.get(Engine._gdrive_direct(src), stream=True, timeout=15, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            ct = r.headers.get("Content-Type", "")
            size = int(r.headers.get("Content-Length") or 0)
            r.close()
            if "text/html" in ct:
                return f"Đây là TRANG WEB (HTTP {r.status_code}). Bấm nút sẽ mở trang bằng trình duyệt."
            name = unquote(Path(urlparse(r.url).path).name)
            return f"File tải được (HTTP {r.status_code}): {name or '?'} {('(' + human(size) + ')') if size else ''}"
        except Exception as e:              # noqa: BLE001
            return f"Không kết nối được: {e}"

    # ---- cập nhật từ GitHub
    @staticmethod
    def _vt(v):
        return tuple(int(x) for x in re.findall(r"\d+", v or "0")[:4]) or (0,)

    def check_update(self, silent=False):
        try:
            import requests
            r = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest", timeout=15,
                             headers={"Accept": "application/vnd.github+json", "User-Agent": "WinAIO"})
            if r.status_code == 404:
                res = {"ok": False, "msg": "Chưa đọc được bản phát hành trên GitHub (repo WIN-AIO cần để Public và có Release)."}
            else:
                r.raise_for_status()
                j = r.json()
                asset = next((a for a in j.get("assets", []) if a["name"].lower().endswith(".exe")), None)
                tag = j.get("tag_name", "")
                newer = self._vt(tag) > self._vt(APP_VERSION)
                res = {"ok": True, "has": bool(newer and asset), "latest": tag, "current": APP_VERSION,
                       "notes": (j.get("body") or "").strip()[:3000], "page": j.get("html_url", ""),
                       "url": asset["browser_download_url"] if asset else "", "size": asset["size"] if asset else 0}
        except Exception as e:              # noqa: BLE001
            res = {"ok": False, "msg": f"Không kiểm tra được cập nhật: {e}"}
        self._upd = {k: res.get(k) for k in ("has", "latest")} if res.get("ok") else {}
        if not silent:
            self._e.log("⟳ " + (f"Có bản mới {res['latest']}" if res.get("has") else
                               f"Đang dùng bản mới nhất ({APP_VERSION})" if res.get("ok") else res["msg"]))
        return res

    def do_update(self):
        info = self.check_update(silent=True)
        if not info.get("has"):
            return info.get("msg") or "Đang dùng bản mới nhất."
        if not getattr(sys, "frozen", False):
            open_target(info["page"])
            return "Bản chạy bằng Python: đã mở trang tải bản mới."
        import requests
        exe = Path(sys.executable).resolve()
        new = exe.with_name(exe.stem + ".new.exe")
        self._e.log(f"⟳ Đang tải bản {info['latest']}...")
        with requests.get(info["url"], stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(new, "wb") as f:
                for chunk in r.iter_content(256 * 1024):
                    f.write(chunk)
        if new.stat().st_size < 1_000_000:
            new.unlink(missing_ok=True)
            return "File tải về bị lỗi (quá nhỏ), thử lại sau."
        bat = Path(os.environ.get("TEMP", str(BASE))) / "winaio_update.bat"
        pid = os.getpid()
        bat.write_text(
            "@echo off\r\nchcp 65001 >nul\r\n:w\r\n"
            f'tasklist /fi "PID eq {pid}" | find "{pid}" >nul && (ping -n 2 127.0.0.1 >nul & goto w)\r\n'
            "set n=0\r\n:m\r\n"
            f'move /y "{new}" "{exe}" >nul 2>&1 && goto ok\r\n'
            "set /a n+=1\r\nif %n% lss 40 (ping -n 2 127.0.0.1 >nul & goto m)\r\n:ok\r\n"
            f'start "" "{exe}"\r\ndel "%~f0"\r\n', encoding="utf-8")
        subprocess.Popen(["cmd", "/c", str(bat)], creationflags=CREATE_NO_WINDOW | 0x00000200, close_fds=True, env=clean_env())
        self._e.log(f"⟳ Đã tải xong {info['latest']}, tool sẽ tự mở lại.")
        threading.Timer(0.8, lambda: self._quit_fn() if self._quit_fn else os._exit(0)).start()
        return ""

    def open_url(self, u):
        if u:
            if IS_WIN and not FAKE:
                os.startfile(u)              # noqa: S606
        return True

    # ---- MS Office
    def office_info(self):
        return {"status": self._e.office.status(), "apps": OFFICE_APPS, "langs": OFFICE_LANGS, "editions": OFFICE_EDITIONS,
                "editions365": OFFICE_365_EDITIONS}

    def office_install(self, o):
        return self._e.office.install(o)

    def office_download(self, o):
        return self._e.office.download_offline(o)

    def office_uninstall(self):
        return self._e.office.uninstall()

    def office_shortcuts(self):
        return self._e.office.shortcuts()

    def office_license(self):
        return self._e.office.license_status()

    def office_key(self, key):
        return self._e.office.enter_key(key)

    # ---- nguồn & ổ USB
    def pw_shutdown(self):
        return self._e.power.force_shutdown()

    def pw_lock(self):
        return self._e.power.lock()

    def pw_switch(self):
        return self._e.power.switch_user()

    def pw_schedule(self, mode, minutes=0, hh=0, mm=0):
        return self._e.power.schedule(mode, minutes, hh, mm)

    def pw_cancel(self):
        return self._e.power.cancel()

    def disks(self):
        return self._e.power.disks()

    def disk_safe(self, n):
        return self._e.power.safe_remove(n)

    def disk_force(self, n):
        return self._e.power.force_remove(n)

    # ---- chạy
    def install(self, ids):
        n = self._e.enqueue(ids)
        return n

    def stop(self):
        self._e.stop()
        return True

    def run_tool(self, tid, extra=None):
        return self._e.run_tool(tid, extra)

    def quick(self, target):
        if target in ("cmd.exe", "powershell.exe") and IS_WIN and not FAKE:
            subprocess.Popen(["cmd", "/c", "start", "", target], cwd=os.environ.get("USERPROFILE", "C:\\"))
        else:
            open_target(target)
        return True

    def open_path(self, p):
        p = Path(p)
        open_target(str(p if p.is_absolute() else BASE / p))
        return True

    def live(self):
        return self._e.live()

    def battery(self):
        return battery_info()

    # ---- Quản lý / Dọn dẹp / Sao lưu (mgr.py)
    M_SYNC = {"startup_list", "startup_set", "startup_delete", "programs_list", "leftovers_rescan", "leftovers_delete", "appx_list",
              "defender_status", "defender_set", "defender_excl", "capcut_info", "xlstart_scan", "xlstart_quarantine", "excel_safe_macro",
              "backup_info", "zalo_info", "zalo_open", "zalo_profile_delete", "browsers_info", "job_status", "job_stop",
              # extra.py (v2.6)
              "drv_problems", "setup_info", "setup_rename", "setup_user", "setup_nopass", "setup_browser", "setup_unikey",
              "usb_disks", "iso_files", "apps_list_file", "cpu_temp",
              # apple.py (v2.7)
              "ios_devices", "ios_firmwares", "irst_info",
              # officex.py (v3.0)
              "off_scan", "lic_status", "lic_iid", "lic_oem", "crack_check"}
    M_JOB = {"uninstall_run", "appx_remove", "clean_scan", "clean_run", "folder_sizes", "capcut_clean", "metadata_strip", "backup_user",
             "restore_user", "zalo_backup", "zalo_restore", "browser_backup", "browser_restore", "sha256_file", "iso_download", "wg_upgrades", "wg_upgrade",
             "fix_sfc", "fix_dism", "fix_wu", "fix_store", "fix_printer", "fix_all", "win11_tidy", "font_install", "apps_export",
             "apps_import", "drv_wu_scan", "drv_wu_install", "bench_disk", "bench_cpu", "ventoy_install", "ventoy_copy", "preset_run",
             "mac_list", "mac_download", "ios_download", "irst_get", "rufus_run", "tools3u_run",
             "lic_key", "lic_cid", "crack_clear", "win_clear_key", "to_volume", "off_remove", "off_tune"}

    def set_upg_n(self, n):
        self._e.upg_n = int(n)
        return True

    def m(self, name, *args):
        if name not in self.M_SYNC:
            raise ValueError("Không có chức năng " + name)
        return getattr(self._mod(name), name)(*args)

    @staticmethod
    def _mod(name):
        return next(x for x in (mgr, extra, apple, officex) if hasattr(x, name))

    def mjob(self, name, label, *args):
        if name not in self.M_JOB:
            raise ValueError("Không có chức năng " + name)
        if name == "preset_run":
            return mgr.job_start(label, self._e.preset_run, *args)
        return mgr.job_start(label, getattr(self._mod(name), name), *args)

    def open_folder(self, p):
        if p and (FAKE or Path(p).exists()):
            open_target(str(Path(p) if Path(p).is_dir() else Path(p).parent))
        return True

    def select_in_explorer(self, p):
        if not FAKE and IS_WIN and p:
            q = mgr.exe_of(p)
            if Path(q).exists():
                subprocess.Popen(["explorer", "/select,", q])
            elif Path(q).parent.exists():
                os.startfile(str(Path(q).parent))     # noqa: S606
        return True

    def disk_health(self):
        return disk_health()

    def boot_status(self):
        return boot_status()

    def boot_action(self, kind, arg=""):
        self._e.log(f"⏻ Khởi động đặc biệt: {kind} {arg}".strip(), "warn")
        msg = boot_action(kind, arg)
        self._e.st.add_history("Khởi động: " + kind, "Hệ thống", "Lỗi" if msg else "Xong", msg)
        if msg:
            self._e.log("✖ " + msg, "err")
        return msg

    def battery_report(self):
        return battery_report_html()

    def refresh_sysinfo(self):
        self._e.sysinfo = None
        threading.Thread(target=lambda: setattr(self._e, "sysinfo", self._e._read_sysinfo()), daemon=True).start()
        return True

    def pick_file(self):
        return self._dialog("file")

    def win_full(self, on):
        """Bật / tắt toàn màn hình thật cho cửa sổ (che cả thanh tiêu đề và taskbar) - dùng cho test màn hình, cảm ứng."""
        on = bool(on)
        w = self._app.win if self._app else None
        if not w or getattr(self, "_full", False) == on:
            return False
        try:
            w.toggle_fullscreen()
            self._full = on
            return True
        except Exception:                   # noqa: BLE001
            return False

    def pick_folder(self):
        return self._dialog("folder")

    def pick_file_abs(self):
        r = self._dialog("file")
        return str(mgr.absp(r)) if r else r

    def pick_folder_abs(self):
        r = self._dialog("folder")
        return str(mgr.absp(r)) if r else r

    def _dialog(self, kind):
        if not self._app or not self._app.win:
            return None
        import webview
        t = webview.FOLDER_DIALOG if kind == "folder" else webview.OPEN_DIALOG
        r = self._app.win.create_file_dialog(t, directory=str(BASE))
        if not r:
            return None
        p = Path(r[0])
        try:                                 # file nằm trong thư mục tool -> lưu đường dẫn tương đối (chạy được từ USB)
            return str(p.resolve().relative_to(BASE))
        except ValueError:
            return str(p)


# ================================================================= cửa sổ
_PAGE = {}


def page_html(token=""):
    """Ghép index.html + css + js thành 1 trang. Bản exe: đọc file 1 lần rồi giữ trong RAM (mở lại trang không đọc đĩa)."""
    key = token if getattr(sys, "frozen", False) else None
    if key is not None and key in _PAGE:
        return _PAGE[key]
    web = RES / "web"
    html = (web / "index.html").read_text(encoding="utf-8")
    css = (web / "style.css").read_text(encoding="utf-8")
    js = (web / "app.js").read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>{css}</style>")
    for name in ("test.js", "mgr.js", "extra.js", "apple.js", "office.js"):
        html = html.replace(f'<script src="{name}"></script>', f"<script>{(web / name).read_text(encoding='utf-8')}</script>")
    html = html.replace('<script src="app.js"></script>', f"<script>window.__TOKEN={json.dumps(token)};</script><script>{js}</script>")
    if key is not None:
        _PAGE[key] = html
    return html


def start_http(api, port=0):
    """Server nội bộ 127.0.0.1 phục vụ giao diện + API.
    - Trang chạy trên http://127.0.0.1 (ngữ cảnh an toàn) nên dùng được mic, webcam cho tab Test máy.
    - API bắt buộc header X-Token ngẫu nhiên: trang web lạ trên máy không gọi được (bị CORS chặn, không đọc được mã)."""
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    token = secrets.token_urlsafe(24)
    last = {"t": time.time()}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype):
            b = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            last["t"] = time.time()
            if self.path.split("?")[0] == "/favicon.ico":
                ico = RES / "icon.ico"
                return self._send(200, ico.read_bytes() if ico.exists() else b"", "image/x-icon")
            if self.path.split("?")[0] not in ("/", "/index.html"):
                return self._send(404, "not found", "text/plain")
            self._send(200, page_html(token), "text/html; charset=utf-8")

        def do_POST(self):
            if self.client_address[0] not in ("127.0.0.1", "::1") or self.headers.get("X-Token") != token:
                return self._send(403, "forbidden", "text/plain")
            last["t"] = time.time()
            name = self.path.rsplit("/", 1)[-1]
            args = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"[]")
            fn = getattr(api, name, None)
            if name.startswith("_") or not callable(fn):
                return self._send(404, "{}", "application/json")
            try:
                res = fn(*args)
            except PermissionError as e:
                return self._send(200, json.dumps({"__err": str(e)}, ensure_ascii=False), "application/json; charset=utf-8")
            except Exception as e:          # noqa: BLE001
                return self._send(500, json.dumps({"__err": str(e)}, ensure_ascii=False), "application/json; charset=utf-8")
            self._send(200, json.dumps(res, ensure_ascii=False), "application/json; charset=utf-8")

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/", last


def has_webview2():
    """Edge WebView2 Runtime (Win 11 và Win 10 cập nhật đều có). Thiếu -> dùng trình duyệt."""
    if not IS_WIN:
        return True
    import winreg
    key = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    for root, path in ((winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\" + key), (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\" + key),
                       (winreg.HKEY_CURRENT_USER, "Software\\" + key)):
        try:
            with winreg.OpenKey(root, path) as k:
                v = winreg.QueryValueEx(k, "pv")[0]
                if v and v != "0.0.0.0":
                    return True
        except OSError:
            continue
    return False


class App:
    def __init__(self):
        self.st = Store()
        self.eng = Engine(self.st)
        self.win = None
        self.api = Api(self.eng, self)
        self.api._quit_fn = self.quit

    def quit(self):
        try:
            self.win.destroy()
        except Exception:                   # noqa: BLE001
            os._exit(0)

    def _on_close(self):
        self.eng.stop_flag.set()
        self.st.save_config(persist=False)        # chỉ lưu nếu đã có thư mục Data

    def run(self, selftest=False):
        import webview
        g = self.st.cfg.get("window") or {}
        sw, sh = 1920, 1080
        try:
            sc = webview.screens[0]
            sw, sh = int(sc.width), int(sc.height)
        except Exception:                   # noqa: BLE001
            pass
        kw = dict(width=max(1000, min(int(g.get("width", min(1440, sw - 60))), sw)),
                  height=max(640, min(int(g.get("height", min(900, sh - 80))), sh - 30)),
                  min_size=(min(1000, sw - 40), min(640, sh - 80)), background_color="#eef1f5")
        _, url, _ = start_http(self.api)            # nạp từ 127.0.0.1 -> dùng được mic / webcam
        self.win = webview.create_window(f"{APP_TITLE} {APP_VERSION}", url=url, js_api=self.api,
                                         maximized=self.st.cfg.get("start_maximized", True) or sw < 1280, **kw)
        self.win.events.resized += lambda w, h: self.st.cfg.setdefault("window", {}).update(width=w, height=h)
        self.win.events.closing += self._on_close
        if selftest:
            threading.Thread(target=self._selftest, daemon=True).start()
        icon = RES / "icon.ico"
        try:
            webview.start(icon=str(icon) if icon.exists() else None)
        except TypeError:
            webview.start()

    def _selftest(self):
        """Dùng khi build trên GitHub: mở cửa sổ, đọc giao diện, ghi kết quả ra selftest.txt rồi thoát."""
        lines = []
        try:
            time.sleep(10)
            for _ in range(60):                     # chờ đọc xong thông tin máy (PowerShell lần đầu hơi chậm)
                if self.eng.sysinfo:
                    break
                time.sleep(1)
            js = ("JSON.stringify({errs: window.__errs, started: !!window.__started, rows: document.querySelectorAll('.arow').length,"
                  " groups: document.querySelectorAll('.gcard').length, title: document.getElementById('ptitle').textContent,"
                  " ver: document.getElementById('ver').textContent, navs: document.querySelectorAll('.nav').length,"
                  " tests: document.querySelectorAll('.tst').length, md: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),"
                  " secure: window.isSecureContext, origin: location.origin})")
            lines.append("UI: " + str(self.win.evaluate_js(js)))
            lines.append("sysinfo: " + json.dumps(self.eng.sysinfo, ensure_ascii=False))
            lines.append("checks: " + json.dumps(self.eng.checks))
            d = self.eng.power.disks()
            lines.append("disks: " + json.dumps(d, ensure_ascii=False)[:1500])
            lines.append("diskhealth: " + json.dumps(disk_health(), ensure_ascii=False)[:1200])
            lines.append("boot: " + json.dumps(boot_status(), ensure_ascii=False)[:800])
            lines.append("battery: " + json.dumps(battery_info(), ensure_ascii=False))
            lines.append("defender: " + json.dumps(self.eng.run_tool("def_status"), ensure_ascii=False))
            E = self.eng
            for nm, f in [("wg_tune", lambda: [E.winget_tune(), E.WG_SETTINGS.read_text(encoding="utf-8-sig")[:300] if E.WG_SETTINGS.exists() else "no file"]),
                          ("wg_show_ok", lambda: E.winget_check("VideoLAN.VLC", force=True)),
                          ("wg_show_bad", lambda: E.winget_check("Sai.KhongCoGoiNay", force=True)),
                          ("wg_find_7zip", lambda: E._wg_find_new_id("7-Zip")),
                          ("wg_find_vlc", lambda: E._wg_find_new_id("VLC media player")),
                          ("wg_whatsapp_msstore", lambda: E.winget_check("9NKSQGP7F2NH", force=True)),
                          ("wg_idm", lambda: E.winget_check("Tonec.InternetDownloadManager", force=True)),
                          ("wg_acrobat", lambda: E.winget_check("Adobe.Acrobat.Reader.64-bit", force=True)),
                          ("gh_wordcraft", lambda: resolve_github(ARTCRAFT[1][0][2])),
                          ("gh_ytdl", lambda: resolve_github(GH_YTDL)),
                          ("gh_ventoy", lambda: resolve_github(r"github:ventoy/Ventoy|windows\.zip$")),
                          ("gh_caiwindao", lambda: resolve_github(CAIWINDAO[2])), ("gh_vanphong", lambda: resolve_github(VANPHONG[2])), ("gh_rufus", lambda: resolve_github(extra.RUFUS)), ("gh_transub", lambda: _try(lambda: resolve_github(TRANSUB[2]))),
                          ("gh_vieneu", lambda: [_try(lambda: resolve_github(VIENEU[2])), _assets("github:pnnbao97/VieNeu-TTS")]),
                          ("wg_lazibook", lambda: run_hidden(["winget", "show", "--id", "9N2X9BM8R5P9", "--source", "msstore",
                                                              "--accept-source-agreements"], timeout=180)[1][-500:]),
                          ("uninst_links", lambda: [(a[1], _try(lambda a=a: resolve_github(a[2]) if src_kind(a[2]) == "github" else requests_head(a[2])))
                                                    for a in UNINSTALLER[1]]),
                          ("wg_picview", lambda: run_hidden(["winget", "show", "--id", "Ruben2776.PicView", "-e", "--source", "winget",
                                                             "--accept-source-agreements"], timeout=180)[1][-300:]),
                          ("page_3u", lambda: resolve_page(TOOLS_3U[2])),

                          ("off_scan", officex.off_scan), ("crack_check", officex.crack_check), ("lic_oem", officex.lic_oem),
                          ("lic_win", lambda: officex.lic_status("windows")["out"][:400]), ("odt_latest", odt_latest_url), ("irst_info", extra.irst_info),
                          ("irst_links", lambda: [(v["file"], requests_head(v["url"])) for v in extra.irst_info()["list"]] + [("font", requests_head(FONT_PACK))]),
                          ("wg_upgrades", lambda: [(x["name"], x["id"], x["ver"], x["new"], x["cut"]) for x in mgr.wg_upgrades()])]:
                try:
                    lines.append(f"{nm}: " + json.dumps(f(), ensure_ascii=False, default=str)[:600])
                except Exception as ex:     # noqa: BLE001
                    lines.append(f"{nm}: ERROR {ex!r}")
            for nm, f in [("startup", lambda: [(x["name"], x["on"], x["pub"]) for x in mgr.startup_list()]),
                          ("programs", lambda: [len(mgr.programs_list())] + [x["name"] for x in mgr.programs_list()[:8]]),
                          ("appx", lambda: len(mgr.appx_list())), ("mgr_defender", mgr.defender_status),
                          ("backup", lambda: [(d["key"], d["path"], d["exists"]) for d in mgr.backup_info()["dirs"]]),
                          ("zalo", mgr.zalo_info), ("browsers", mgr.browsers_info), ("capcut", mgr.capcut_info), ("xlstart", mgr.xlstart_scan),
                          ("drv_problems", extra.drv_problems), ("gpu", lambda: [extra.gpu_usage(), time.sleep(2), extra.gpu_usage(), extra._vram_total()]), ("cpu_temp", lambda: [extra.cpu_temp(), time.sleep(3), extra.cpu_temp(), extra.cpu_clock()]),
                          ("usb_disks", extra.usb_disks), ("setup_info", extra.setup_info),
                          ("mac_list", lambda: [len(apple.mac_list())] + [(x["name"], x["version"], x["build"], x["kind"], x["size"], len(x["files"]),
                                                                            x["files"][0]["url"]) for x in apple.mac_list()[:40]]),
                          ("mac_old", lambda: [(x["name"], x["version"], x["build"], x["kind"], x["size"], [f["name"] for f in x["files"]])
                                               for x in apple.mac_list() if x["kind"] == "dmg" or x["version"].startswith("10.13")]),
                          ("ios_devices", lambda: [len(apple.ios_devices())] + apple.ios_devices()[:4]),
                          ("ios_fw", lambda: [(f["version"], f["build"], f["signed"], f["size"], f["url"]) for f in apple.ios_firmwares("iPhone15,2")["fw"][:3]])]:
                try:
                    lines.append(f"{nm}: " + json.dumps(f(), ensure_ascii=False, default=str)[:4000 if nm in ("mac_list", "probe_3u") else 1200])
                except Exception as e:      # noqa: BLE001
                    lines.append(f"{nm}: ERROR {e!r}")
            lines.append("Data folder exists: " + str(DATA.exists()))
            lines.append("webview2: " + str(has_webview2()))
        except Exception as e:              # noqa: BLE001
            lines.append("ERROR: " + repr(e))
        (BASE / "selftest.txt").write_text("\n".join(lines), encoding="utf-8")
        if getattr(sys, "frozen", False):
            # Tái hiện đúng cách nút Cập nhật mở lại tool: chờ bản này thoát rồi mới mở exe (chế độ --ping ghi ping.txt)
            pid, exe = os.getpid(), Path(sys.executable).resolve()
            bat = BASE / "ping_test.bat"
            bat.write_text("@echo off\r\n:w\r\n"
                           f'tasklist /fi "PID eq {pid}" | find "{pid}" >nul && (ping -n 2 127.0.0.1 >nul & goto w)\r\n'
                           f'start "" "{exe}" --ping\r\n', encoding="utf-8")
            subprocess.Popen(["cmd", "/c", str(bat)], creationflags=CREATE_NO_WINDOW | 0x00000200, close_fds=True, env=clean_env())
        self.quit()


def serve(port=8765, open_browser=False):
    """Giao diện bằng trình duyệt: để thử, và dự phòng khi máy chưa có WebView2."""
    st = Store()
    api = Api(Engine(st))
    api._browser = open_browser
    srv, url, last = start_http(api, port)
    print(f"Giao diện: {url}", flush=True)
    api._quit_fn = lambda: os._exit(0)
    if open_browser:
        api._e.log("Máy chưa có Edge WebView2 → đang mở giao diện bằng trình duyệt. Đóng tab trình duyệt là tool tự thoát.", "warn")
        edge = next((p for p in (Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
                                 Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe") if p.exists()), None)
        if edge:
            subprocess.Popen([str(edge), f"--app={url}", "--window-size=1440,900"])
        else:
            import webbrowser
            webbrowser.open(url)
    while True:                              # đóng tab trình duyệt -> không còn gọi API -> tự thoát
        time.sleep(5)
        if open_browser and time.time() - last["t"] > 25 and not (api._e.worker and api._e.worker.is_alive()):
            os._exit(0)


def main():
    if "--ping" in sys.argv:                 # dùng khi tự kiểm tra trên GitHub: exe mở lại được, không báo lỗi
        (BASE / "ping.txt").write_text(f"ok {APP_VERSION} pid={os.getpid()}", encoding="utf-8")
        return
    if "--serve" in sys.argv:
        serve(int(os.environ.get("WINAIO_PORT", "8765")))
        return
    if IS_WIN and not is_admin_windows() and "--no-admin" not in sys.argv:
        if relaunch_as_admin():
            return
    if "--browser" in sys.argv or not has_webview2():
        serve(0, open_browser=True)
        return
    try:
        App().run(selftest="--selftest" in sys.argv)
    except Exception as e:                  # noqa: BLE001  pywebview lỗi -> dùng trình duyệt
        if "--selftest" in sys.argv:
            (BASE / "selftest.txt").write_text("ERROR pywebview: " + repr(e), encoding="utf-8")
            return
        serve(0, open_browser=True)


if __name__ == "__main__":
    main()
