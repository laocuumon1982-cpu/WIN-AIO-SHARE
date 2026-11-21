"""Kiểm tra các link tải trực tiếp trong danh sách mặc định (chạy trên GitHub Actions). Chỉ báo cáo, không làm hỏng bản build."""
import ast
import pathlib
import requests

src = pathlib.Path(__file__).resolve().parent.parent.joinpath("win_aio.py").read_text(encoding="utf-8")
tree = ast.parse(src)
ns = {}
for n in tree.body:      # chỉ chạy các dòng gán hằng chuỗi + DEFAULT_GROUPS (không import cả tool)
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and isinstance(
            n.value, (ast.Constant, ast.Tuple, ast.List, ast.Dict)):
        try:
            exec(compile(ast.Module([n], []), "win_aio", "exec"), ns)
        except Exception:   # noqa: BLE001
            pass
groups = ns["DEFAULT_GROUPS"]
ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
bad = 0
for gname, _col, apps in groups:
    for icon, name, link, args, note in apps:
        if link.startswith("github:"):
            body = link.split(":", 1)[1]
            repo, _, pat = body.partition("|")
            try:
                import os, re as _re
                h = {"User-Agent": "WinAIO"}
                if os.environ.get("GH_TOKEN"):
                    h["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
                js = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=h, timeout=25).json()
                hit = [a["name"] for a in js.get("assets", []) if _re.search(pat, a["name"], _re.I)]
                ok, info = bool(hit), f"{js.get('tag_name')} -> {hit[:1] or 'KHONG CO FILE KHOP'}"
            except Exception as e:  # noqa: BLE001
                ok, info = False, str(e)[:150]
            bad += not ok
            print(("OK  " if ok else "LOI ") + f"{name}: {info}  <- {link}")
            continue
        if not link.startswith("http"):
            continue
        try:
            r = requests.get(link, headers=ua, stream=True, timeout=25, allow_redirects=True)
            ok = r.status_code < 400
            info = f"{r.status_code} {r.headers.get('Content-Type', '')[:30]} {r.headers.get('Content-Length', '?')}"
            r.close()
        except Exception as e:      # noqa: BLE001
            ok, info = False, type(e).__name__ + ": " + str(e)[:150]
        bad += not ok
        print(("OK  " if ok else "LOI ") + f"{name}: {info}  <- {link}")
print(f"LINK LOI: {bad}")
