"""Kiểm tra các link tải trực tiếp trong danh sách mặc định (chạy trên GitHub Actions). Chỉ báo cáo, không làm hỏng bản build."""
import ast
import pathlib
import requests

src = pathlib.Path(__file__).resolve().parent.parent.joinpath("win_aio.py").read_text(encoding="utf-8")
tree = ast.parse(src)
groups = next(ast.literal_eval(n.value) for n in tree.body
              if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "DEFAULT_GROUPS")
ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
bad = 0
for gname, apps in groups:
    for icon, name, link, args, note in apps:
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
