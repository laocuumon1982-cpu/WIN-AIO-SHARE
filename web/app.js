"use strict";
/* ===================================================================== Win AIO by Duy Anh - giao diện */
window.__errs = [];
window.addEventListener("error", e => window.__errs.push(String(e.message || e)));
window.addEventListener("unhandledrejection", e => window.__errs.push(String(e.reason || e)));

const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const norm = s => String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");
const led = (st, cls = "") => `<span class="led ${st} ${cls}"><i></i></span>`;
async function api(name, ...args) {
  let r;
  try {
    if (window.pywebview && window.pywebview.api && window.pywebview.api[name]) r = await window.pywebview.api[name](...args);
    else r = await fetch("/api/" + name, {method: "POST", headers: {"X-Token": window.__TOKEN || ""}, body: JSON.stringify(args)}).then(x => x.json());
  } catch (e) { toast(String(e && e.message || e).replace(/^.*PermissionError:?\s*/, ""), "err"); throw e; }
  if (r && typeof r === "object" && r.__err) { toast(r.__err, "err"); throw new Error(r.__err); }
  return r;
}
function copyLocal(text) {                  // iPhone (http) không có navigator.clipboard -> dùng ô chữ tạm
  const t = document.createElement("textarea"); t.value = text; t.style.cssText = "position:fixed;top:0;left:0;opacity:0";
  document.body.appendChild(t); t.focus(); t.select(); t.setSelectionRange(0, text.length);
  let ok = false; try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
  t.remove(); return ok;
}

/* ---------------------------------------------------------------- thông báo nhỏ + hộp thoại */
function toast(t, kind) {
  const d = document.createElement("div");
  d.textContent = t;
  if (kind === "err") d.className = "err";
  $("toast").appendChild(d);
  setTimeout(() => d.remove(), kind === "err" ? 7000 : 3800);
}
window.toast = toast;

const dialogs = [];
function dialog({title, body = "", buttons = [], width = 600, onOpen, left = ""}) {
  return new Promise(resolve => {
    const ov = document.createElement("div");
    ov.className = "overlay";
    ov.innerHTML = `<div class="dlg" style="width:${width}px"><h3>${esc(title)}</h3><div class="body">${body}</div>
      <div class="btns"><div class="left">${left}</div>${buttons.map((b, i) =>
      `<button class="btn ${b.cls || ""}" data-i="${i}">${b.text}</button>`).join("")}</div></div>`;
    document.body.appendChild(ov);
    const dlg = ov.querySelector(".dlg");
    const close = v => { if (!ov.isConnected) return; ov.remove(); dialogs.splice(dialogs.indexOf(ctl), 1); resolve(v); };
    const ctl = {el: dlg, close, q: s => dlg.querySelector(s), err: t => { const e = dlg.querySelector(".err"); if (e) e.textContent = t || ""; }};
    dialogs.push(ctl);
    dlg.querySelectorAll(".btns > button").forEach(b => b.onclick = async () => {
      const bt = buttons[+b.dataset.i];
      if (bt.click) { const r = await bt.click(ctl); if (r === false) return; close(r === undefined ? bt.value : r); }
      else close(bt.value);
    });
    ctl.key = e => {
      if (e.key === "Escape") close(null);
      if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== "BUTTON") {
        const def = buttons.findIndex(b => b.def); if (def >= 0) { e.preventDefault(); dlg.querySelector(`.btns > [data-i="${def}"]`).click(); }
      }
    };
    if (onOpen) onOpen(ctl);
    const f = dlg.querySelector("input,textarea,select"); if (f) setTimeout(() => f.focus(), 30);
  });
}
document.addEventListener("keydown", e => { const top = dialogs[dialogs.length - 1]; if (top) top.key(e); });
const alertBox = (title, msg) => dialog({title, body: `<div class="msg">${esc(msg)}</div>`, buttons: [{text: "OK", cls: "red", def: true, value: true}]});
const confirmBox = (title, msg, ok = "Đồng ý", danger = true) => dialog({title, body: `<div class="msg">${esc(msg)}</div>`,
  buttons: [{text: "Hủy", value: false}, {text: ok, cls: danger ? "red" : "green", def: true, value: true}]});
function promptBox(title, label, val = "", pass = false) {
  return dialog({title, width: 460, body: `<div class="msg">${esc(label)}</div><input id="pv" ${pass ? 'type="password"' : ""} style="width:100%;margin-top:8px" value="${esc(val)}"><div class="err"></div>`,
    buttons: [{text: "Hủy", value: null}, {text: "✓ OK", cls: "red", def: true, click: c => c.q("#pv").value}]});
}
function popMenu(anchor, items) {
  document.querySelectorAll(".menu-pop").forEach(m => m.remove());
  const m = document.createElement("div");
  m.className = "menu-pop";
  m.innerHTML = items.map((it, i) => it === "-" ? "<hr>" : `<div data-i="${i}" class="${it.cls || ""}">${it.text}</div>`).join("");
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  m.style.left = Math.min(r.left, innerWidth - m.offsetWidth - 10) + "px";
  m.style.top = (r.bottom + 6 + m.offsetHeight > innerHeight ? r.top - m.offsetHeight - 6 : r.bottom + 6) + "px";
  m.onclick = e => { const d = e.target.closest("[data-i]"); if (d) { m.remove(); items[+d.dataset.i].do(); } };
  setTimeout(() => document.addEventListener("click", function h() { m.remove(); document.removeEventListener("click", h); }), 0);
}

/* ===================================================================== WIN AIO */
const PAGES = {
  system: ["Thông tin & khởi động", "Thông tin máy, khởi động đặc biệt (BIOS, Safe Mode...) và mở nhanh công cụ Windows"],
  manage: ["Thiết lập Windows", "Tiện ích, sửa lỗi, thiết lập máy, driver, bảo mật · gỡ và cập nhật phần mềm"],
  clean: ["Dọn dẹp", "Dọn rác, phân tích ổ đĩa, cache CapCut, virus macro Excel, xóa metadata ảnh"],
  backup: ["Sao lưu", "Thư mục người dùng · Zalo · Zalo nhiều tài khoản · Trình duyệt · Chuyển phần mềm sang Win mới"],
  apps: ["Cài phần mềm", "Bấm 1 nút để cài ngay, hoặc chọn nhiều mục rồi bấm ▶ Cài mục đã chọn"],
  power: ["Nguồn & Ổ USB", "Tắt máy khẩn cấp · Khóa máy · Hẹn giờ tắt · Tháo ổ USB an toàn"],
  testmac: ["Test máy MAC", "SoiMac - kiểm tra Mac cũ trước khi mua: chép ra USB, mở bằng Safari ngay trên máy Mac"],
  test: ["Test máy WIN", "Kiểm tra màn hình, cảm ứng, bàn phím, loa, micro, trackpad, webcam, pin laptop, hiệu năng"],
  mac: ["Kho bộ cài MAC", "Bộ cài macOS chính chủ Apple: Tahoe, Sequoia, Sonoma, Ventura... về tới Lion - tải thẳng từ máy chủ Apple · macUSB · Apple Configurator 2"],
  ios: ["Kho Firmware iOS", "3uTools · Firmware IPSW cho iPhone, iPad, iPod, Apple TV, Mac chip M - danh sách theo ipsw.me, tải từ máy chủ Apple"],
  iso: ["Kho bộ cài WIN", "Tải ISO gốc Microsoft · Rufus · AVL Win Master · USB boot Ventoy · Driver IRST · Kiểm tra SHA-256 file ISO"],
  web: ["Web", "Trang web hay dùng - bấm để mở · Admin bấm ✎ để sửa, ＋ để thêm link"],
  history: ["Nhật ký", "Những gì tool đã cài / đã chạy"],
  settings: ["Cài đặt", "Thư mục tải, sao lưu danh sách nút"]};
const KIND = {web: "WEB", winget: "WINGET", file: "FILE", cmd: "LỆNH", office: "OFFICE", open: "LINK", github: "GITHUB", none: "CHƯA CÓ NGUỒN"};
let lastFull, INIT = {}, G = [], NCOL = 4, LAYOUT = "grid", page = "system", ADMIN = false, picked = new Set(), logSeq = 0, ST = {}, HIST = [];

function showPage(p) {
  if (p === "tools" || p === "fix") { MT = p; p = "manage"; }     // v4.7: 2 trang cũ nằm trong Thiết lập Windows
  page = p;
  const locked = p === "settings" && !ADMIN;
  document.querySelectorAll(".page").forEach(x => x.classList.toggle("on", x.id === (locked ? "pg-locked" : "pg-" + p)));
  document.querySelectorAll(".nav").forEach(x => x.classList.toggle("on", x.dataset.p === p));
  $("ptitle").textContent = PAGES[p][0];
  const nv = document.querySelector(`.nav[data-p="${p}"] .ic`); if ($("picon") && nv) $("picon").textContent = nv.textContent;
  $("psub").textContent = PAGES[p][1];
  if (p === "history") loadHistory();
  if (p === "power") loadDisks();
  if (p === "system") { live(); loadBoot().then(fitSys).catch(() => {}); [30, 400].forEach(t => setTimeout(fitSys, t)); }
  if (p === "apps" && LAYOUT === "fit" && G.length) renderGroups();
  if (p === "test") { loadBattery(); loadDisk(); renderSum(); }
  if (p === "manage") mgrShow();
  if (p === "clean") cleanShow();
  if (p === "backup") backShow();
  if (p === "iso") isoShow();
  if (p === "mac") macShow();
  if (p === "ios") iosShow();
  if (p === "web") webShow();
  if (p === "testmac") testMacShow();
  if (p === "settings" && ADMIN) renderSettings();
}
document.querySelectorAll(".nav").forEach(n => n.onclick = () => n.dataset.p === "settings" ? openSettings() : showPage(n.dataset.p));
/* v5.7: vào tab Cài đặt luôn hỏi mật khẩu Admin (cùng mật khẩu lúc mở tool) */
async function openSettings() {
  const ok = await dialog({title: "⚙ Cài đặt", width: 420,
    body: `<div class="msg">Nhập mật khẩu Admin để vào Cài đặt.</div>
      <input id="pw" type="password" style="width:100%;margin-top:10px" placeholder="Mật khẩu Admin"><div class="err"></div>`,
    buttons: [{text: "Hủy", value: false}, {text: "🔑 Vào Cài đặt", cls: "red", def: true, click: async c => {
      if (await api("check_pw", c.q("#pw").value)) return true;
      c.err("Mật khẩu không đúng"); c.q("#pw").select(); return false; }}]});
  if (!ok) return;
  if (!ADMIN) setAdmin(true);
  showPage("settings");
}
$("fold").onclick = () => { $("side").classList.toggle("mini"); $("fold").textContent = $("side").classList.contains("mini") ? "»" : "«"; };
/* ---------------------------------------------------------------- Giao diện: chỉ còn Mặc định · Sáng (v4.8) */
function applySkin() {
  document.body.classList.remove("g01", "g01l", "robo", "dark");
  if (typeof fitSys === "function") [30, 300].forEach(t => setTimeout(() => { try { fitSys(); if (page === "apps") renderGroups(); } catch (e) { /* bỏ qua */ } }, t));
}

/* ---------------------------------------------------------------- Admin */
function setAdmin(on) {
  ADMIN = on;
  document.body.classList.toggle("admin", on);
  $("bLock").textContent = on ? "🔓 Admin: đang mở" : "🔒 Admin";
  $("bLock").classList.toggle("admin-on", on);
  $("lk-settings").hidden = on;
  showPage(page);
}
async function unlock() {
  const ok = await dialog({title: "Mở khóa Admin", width: 440,
    body: `<div class="msg">Nhập mật khẩu Admin để sửa tên nút, đổi link nguồn, thêm / xóa phần mềm.</div>
      <input id="pw" type="password" style="width:100%;margin-top:10px" placeholder="Mật khẩu Admin">
      <div class="err"></div>`,
    buttons: [{text: "Hủy", value: false}, {text: "🔑 Mở khóa", cls: "red", def: true, click: async c => {
      if (await api("unlock", c.q("#pw").value)) return true;
      c.err("Mật khẩu không đúng"); c.q("#pw").select(); return false; }}]});
  if (ok) { setAdmin(true); toast("Đã mở khóa Admin"); }
  return !!ok;
}
$("bLock").onclick = async () => { if (ADMIN) { await api("lock_admin"); setAdmin(false); toast("Đã khóa Admin"); } else unlock(); };
$("lkOpen").onclick = openSettings;

/* ---------------------------------------------------------------- Cài phần mềm */
let FIT_N = 0;
async function loadGroups() { const r = await api("groups"); G = r.groups; NCOL = r.columns; LAYOUT = r.layout || "grid"; FIT_N = r.fit_n || 0; renderGroups(); }
function allApps() { return G.flatMap(g => g.apps); }
function renderGroups() {
  const q = norm($("q").value.trim());
  const res = ST.results || {};
  const cards = G.map((g, gi) => {
    const rows = g.apps.map(a => {
      const hit = !q || norm(a.name + " " + a.note + " " + g.name).includes(q);
      const wbad = a.wg && !a.wg.ok, wver = a.wg && a.wg.ok && a.wg.ver ? `\nwinget: bản mới nhất ${a.wg.ver}` : "";
      const st = res[a.id], l = st === "run" || st === "wait" ? led("run", "sm") : st === "ok" ? led("ok", "sm") : st === "err" ? led("err", "sm") : "";
      return `<div class="arow${hit ? "" : " hide"}" data-a="${a.id}"${ADMIN ? ' draggable="true"' : ""}>
        <span class="chk${picked.has(a.id) ? " on" : ""}" data-act="pick"></span>
        <button class="btn abtn" data-act="run" title="${esc(a.name + "\n" + (a.note ? a.note + "\n" : "") + (a.src || "Chưa có nguồn") + wver + (wbad ? "\n⚠ ID winget này không còn trong kho - Admin bấm ✎ để sửa" : ""))}">
          <span class="ai">${esc(a.icon || "▫")}</span><span class="an">${esc(a.name)}</span>${l}<span class="tag ${wbad ? "bad" : a.kind}">${wbad ? "ID LỖI" : /^codeberg:/i.test(a.src || "") ? "CODEBERG" : /^page:/i.test(a.src || "") ? "MỚI NHẤT" : KIND[a.kind]}</span></button>
        <span class="mv adm"><button class="ed xs" data-act="aup" title="Đưa nút lên">▲</button><button class="ed xs" data-act="adown" title="Đưa nút xuống">▼</button></span>
        <button class="ed adm" data-act="edit" title="Sửa tên / nguồn">✎</button></div>`;
    }).join("");
    const anyHit = !q || g.apps.some(a => norm(a.name + " " + a.note + " " + g.name).includes(q));
    const fit = LAYOUT === "fit", grid = LAYOUT === "grid" || fit, n = G.length;
    const hits = g.apps.filter(a => !q || norm(a.name + " " + a.note + " " + g.name).includes(q)).length;
    const lgrid = LAYOUT === "grid";
    const c = lgrid ? gi % NCOL : Math.min(g.col || 0, NCOL - 1), r = Math.floor(gi / NCOL);
    const dis = {gleft: c === 0, gright: lgrid ? (c === NCOL - 1 || gi === n - 1) : c === NCOL - 1,
      gup: lgrid && gi < NCOL, gdown: lgrid && gi === n - 1};
    const d = k => dis[k] ? " disabled" : "";

    return {c, gid: g.id, w: anyHit ? 1.7 + hits : 0, html: `<div class="gcard${anyHit ? "" : " empty-hit"}${fit ? " fitg" : ""}" data-g="${g.id}">
      <div class="ghead"${ADMIN ? ' draggable="true" title="Kéo để đổi chỗ nhóm"' : ""}><h4>${ADMIN ? '<i class="grip">⠿</i>' : ""}<span>${esc(g.name)}</span></h4><span class="gall" data-act="gpick">chọn nhóm</span>
        <button class="ed sm adm" data-act="gedit" title="Đổi tên nhóm">✎</button><button class="ed sm del adm" data-act="gdel" title="Xóa nhóm">✕</button></div>
      <div class="gmove adm"><button class="ed sm" data-act="gleft" title="${lgrid ? "Đổi chỗ với nhóm bên trái" : "Chuyển nhóm sang cột bên trái"}"${d("gleft")}>◀</button>
        <button class="ed sm" data-act="gup" title="${lgrid ? "Đổi chỗ với nhóm ở hàng trên" : "Đưa nhóm lên trên"}"${d("gup")}>▲</button>
        <button class="ed sm" data-act="gdown" title="${lgrid ? "Đổi chỗ với nhóm ở hàng dưới" : "Đưa nhóm xuống dưới"}"${d("gdown")}>▼</button>
        <button class="ed sm" data-act="gright" title="${lgrid ? "Đổi chỗ với nhóm bên phải" : "Chuyển nhóm sang cột bên phải"}"${d("gright")}>▶</button>
        <span>${lgrid ? `Hàng ${r + 1} · Cột ${c + 1}` : `Cột ${c + 1}`}</span></div>
      ${rows || '<div class="logl">(chưa có nút)</div>'}
      <button class="addbtn adm" data-act="add">＋ Thêm phần mềm</button></div>`};
  });
  $("groups").style.setProperty("--ncol", NCOL);
  $("groups").classList.toggle("lgrid", LAYOUT === "grid");
  $("groups").classList.toggle("fitgrid", LAYOUT === "fit");
  if (LAYOUT !== "fit") $("groups").classList.remove("notag");
  $("groups").style.zoom = "";
  if (LAYOUT === "fit") fitGroups(cards);
  else if (LAYOUT === "grid") $("groups").innerHTML = cards.map(x => x.html).join("");
  else {
    const cols = Array.from({length: NCOL}, () => []);
    cards.forEach(x => cols[x.c].push(x.html));
    $("groups").innerHTML = cols.map((h, i) => `<div class="gcol" data-c="${i}">${h.join("") || '<div class="colempty adm">Cột trống</div>'}</div>`).join("");
  }
  if ($("nCol")) $("nCol").value = NCOL;
  if ($("lay")) { $("lay").value = LAYOUT; $("nCol").parentElement.hidden = LAYOUT === "fit"; }
  $("s-total").textContent = allApps().length;
  updSel();
}
/* Tự vừa màn hình: xếp các nhóm kiểu "gạch" vào nhiều cột (nhóm kế tiếp vào cột đang thấp nhất),
   tăng số cột cho tới khi không còn phải kéo; vẫn chưa vừa thì thu nhỏ cả khối (tối đa còn 70%). */
function fitGroups(cards) {
  const el = $("groups"), wrap = el.parentElement, W = el.clientWidth || 1000;
  const draw = cols => {
    el.style.setProperty("--ncol", cols.length);
    el.innerHTML = cols.map((c, i) => `<div class="gcol" data-c="${i}">${c.map(x => x.html).join("") || '<div class="colempty adm">Cột trống</div>'}</div>`).join("");
  };
  const greedy = n => {
    const cols = Array.from({length: n}, () => ({h: 0, items: []}));
    cards.forEach(x => { const c = cols.reduce((b, k) => k.h < b.h ? k : b, cols[0]); c.items.push(x); c.h += x.w; });
    return cols.map(c => c.items);
  };
  let n = FIT_N;
  if (n && W / n >= 150 && el.offsetParent) {          // đã chốt cách chia cột -> giữ nguyên, chỉ co giãn cho vừa
    const cols = Array.from({length: n}, () => []);
    cards.forEach(x => cols[Math.min(x.c, n - 1)].push(x));
    draw(cols); fitBox(el, .6, 1.35);
  } else {
    n = bestFit(el, k => draw(greedy(k)), Math.max(2, Math.floor(W / 420)), Math.max(2, Math.floor(W / 165)), W, 220, .66, 1.35);
    if (el.offsetParent && cards.length) {             // lưu lại để lần sau / nút di chuyển dùng đúng cột này
      const cols = greedy(n).map(c => c.map(x => x.gid));
      FIT_N = n;
      api("fit_save", cols).then(() => loadGroups()).catch(() => {});
    }
  }
  el.classList.toggle("notag", W / n / (+el.style.zoom || 1) < 270);   // cột hẹp: ẩn nhãn WINGET / WEB để tên không bị cắt
}
/* Thử từng số cột: mỗi số cột tìm cỡ (zoom) lớn nhất vừa khung, chọn cách cho nút to nhất
   mà cột vẫn đủ rộng (minCol px sau khi phóng). */
function bestFit(el, put, lo, hi, W, minCol, minZ, maxZ) {
  let best = null;
  const wrap = el.parentElement;
  for (let n = lo; n <= hi; n++) {
    put(n); fitBox(el, minZ, maxZ);
    const z = +el.style.zoom || 1, ok = W / n / z >= minCol;
    const over = wrap.scrollHeight / Math.max(1, wrap.clientHeight);       // > 1: vẫn phải kéo
    const score = over > 1.01 ? -over : z;                                 // ưu tiên vừa khung, rồi tới nút to nhất
    if (ok && (!best || score > best.score + .01)) best = {n, score};
  }
  if (!best) best = {n: hi};
  put(best.n); fitBox(el, minZ, maxZ);
  return best.n;
}
let fitT;
window.addEventListener("resize", () => { clearTimeout(fitT); fitT = setTimeout(() => { if (page === "apps" && LAYOUT === "fit") renderGroups(); }, 150); });
/* thu nhỏ cả khối nội dung cho vừa khung (không phải kéo); nhỏ nhất `min` */
function fitBox(inner, min = .72, max = 1) {
  if (!inner || !inner.offsetParent) return;
  const wrap = inner.parentElement;
  inner.style.zoom = "";
  const fits = () => wrap.scrollHeight <= wrap.clientHeight + 1;
  let lo, hi;
  if (fits()) { if (max <= 1) return; lo = 1; hi = max; inner.style.zoom = max; if (fits()) return; }   // còn trống -> phóng to cho đầy
  else { lo = min; hi = 1; }
  // đổi cỡ thì chữ dàn lại và chiều cao đổi theo -> dò tìm mức lớn nhất vẫn vừa
  for (let k = 0; k < 8; k++) { const z = (lo + hi) / 2; inner.style.zoom = z.toFixed(3); fits() ? lo = z : hi = z; }
  inner.style.zoom = lo.toFixed(3);
}
const fitSys = () => fitBox($("sysbox"), .72, 1.4);
function fitSide() {
  const sd = $("side"); sd.classList.remove("tight", "tight2", "tight3", "tight4", "tight5", "tight6");
  for (const c of ["tight", "tight2", "tight3", "tight4", "tight5", "tight6"]) if (sd.scrollHeight > sd.clientHeight + 1) sd.classList.add(c);
}
let fitST;
window.addEventListener("resize", () => { clearTimeout(fitST); fitST = setTimeout(() => { fitSide(); if (page === "system") fitSys(); }, 160); });
/* ---------- Admin: kéo thả nhóm (bấm giữ tên nhóm) và kéo thả nút phần mềm ---------- */
let DRAG = null;
function clearDrop() { document.querySelectorAll(".drop-b,.drop-a,.drop-in").forEach(e => e.classList.remove("drop-b", "drop-a", "drop-in")); }
(function initDrag() {
  const box = $("groups");
  box.addEventListener("dragstart", e => {
    if (!ADMIN) return e.preventDefault();
    const row = e.target.closest(".arow"), head = e.target.closest(".ghead");
    if (row) DRAG = {t: "app", id: +row.dataset.a, el: row};
    else if (head) { const g = head.closest(".gcard"); DRAG = {t: "group", id: +g.dataset.g, el: g}; }
    else return;
    e.dataTransfer.effectAllowed = "move";
    try { e.dataTransfer.setData("text/plain", DRAG.t + ":" + DRAG.id); } catch (x) { /* bỏ qua */ }
    setTimeout(() => DRAG && DRAG.el.classList.add("dragging"), 0);
    document.body.classList.add("dnd-" + DRAG.t);
  });
  box.addEventListener("dragend", () => {
    if (DRAG) DRAG.el.classList.remove("dragging");
    document.body.classList.remove("dnd-app", "dnd-group"); clearDrop(); DRAG = null;
  });
  const spot = e => {   // tìm chỗ thả + trước / sau
    if (!DRAG) return null;
    if (DRAG.t === "app") {
      const row = e.target.closest(".arow"), card = e.target.closest(".gcard");
      if (row && row !== DRAG.el) {
        const r = row.getBoundingClientRect(), after = e.clientY > r.top + r.height / 2;
        return {el: row, cls: after ? "drop-a" : "drop-b", gid: +card.dataset.g,
          before: after ? (row.nextElementSibling && row.nextElementSibling.classList.contains("arow") ? +row.nextElementSibling.dataset.a : null) : +row.dataset.a};
      }
      if (card && !row) return {el: card, cls: "drop-in", gid: +card.dataset.g, before: null};
      return null;
    }
    const card = e.target.closest(".gcard");
    if (card && card !== DRAG.el) {
      const r = card.getBoundingClientRect();
      const after = LAYOUT !== "grid" ? e.clientY > r.top + r.height / 2 : (e.clientX > r.left + r.width / 2 || e.clientY > r.top + r.height * .75);
      return {el: card, cls: after ? "drop-a" : "drop-b", target: +card.dataset.g, after};
    }
    const col = e.target.closest(".gcol[data-c]");
    if (col && LAYOUT !== "grid") return {el: col, cls: "drop-in", target: null, col: +col.dataset.c};
    return null;
  };
  box.addEventListener("dragover", e => {
    const s = spot(e); clearDrop();
    if (!s) return;
    e.preventDefault(); e.dataTransfer.dropEffect = "move"; s.el.classList.add(s.cls);
  });
  box.addEventListener("drop", async e => {
    const s = spot(e), d = DRAG; clearDrop();
    if (!s || !d) return;
    e.preventDefault();
    try {
      if (d.t === "app") await api("drop_app", d.id, s.gid, s.before);
      else await api("drop_group", d.id, s.target, !!s.after, s.col ?? null);
      await loadGroups(); toast(d.t === "app" ? "Đã chuyển nút" : "Đã đổi chỗ nhóm");
    } catch (x) { toast(String(x), "err"); }
  });
})();
function updSel() {
  const ids = new Set(allApps().map(a => a.id));
  [...picked].forEach(i => { if (!ids.has(i)) picked.delete(i); });
  $("selcnt").textContent = "Đã chọn: " + picked.size;
  $("s-sel").textContent = picked.size;
}
let qT; $("q").oninput = () => { clearTimeout(qT); qT = setTimeout(renderGroups, 120); };
$("bAll").onclick = () => { document.querySelectorAll(".arow:not(.hide)").forEach(r => picked.add(+r.dataset.a)); renderGroups(); };
$("bNone").onclick = () => { picked.clear(); renderGroups(); };
$("bGo").onclick = async () => {
  if (!picked.size) return toast("Chưa chọn phần mềm nào (bấm ô tròn bên trái nút)", "err");
  const order = allApps().filter(a => picked.has(a.id)).map(a => a.id);
  const n = await api("install", order);
  toast(`Đã thêm ${n} phần mềm vào hàng đợi`);
  picked.clear(); renderGroups();
};
$("bStop").onclick = () => api("stop");
$("bArrange").onclick = async () => {
  const r = await dialog({title: "Tự sắp xếp nhóm phần mềm", width: 500, body: `<div class="msg">Chia lại các nhóm cho đều chiều cao (kiểu Lưới: nhóm nhiều nút lên trước).</div>
      <label class="ck" style="margin-top:10px"><input type="checkbox" id="arA"> Xếp các nút trong mỗi nhóm theo tên A → Z</label>`,
    buttons: [{text: "Hủy", value: null}, {text: "⚖ Sắp xếp", cls: "red", def: true, click: c => ({a: c.q("#arA").checked})}]});
  if (!r) return;
  await api("auto_arrange", r.a);
  if (LAYOUT === "fit") { await api("fit_reset"); FIT_N = 0; }
  loadGroups(); toast("Đã sắp xếp lại các nhóm");
};
$("lay").onchange = async () => { await api("set_layout", $("lay").value); loadGroups(); toast("Kiểu xếp: " + $("lay").selectedOptions[0].text); };
$("nCol").onchange = async () => { await api("set_columns", +$("nCol").value); loadGroups(); toast(`Đã chia lại thành ${$("nCol").value} cột`); };
$("bAddGroup").onclick = async () => {
  const n = await promptBox("Thêm nhóm", "Tên nhóm mới:", "NHÓM MỚI");
  if (n !== null) { await api("save_group", 0, n); loadGroups(); }
};
$("groups").onclick = async e => {
  const t = e.target.closest("[data-act]"); if (!t) return;
  const act = t.dataset.act, row = t.closest(".arow"), card = t.closest(".gcard");
  const gid = card ? +card.dataset.g : 0, g = G.find(x => x.id === gid);
  const a = row ? allApps().find(x => x.id === +row.dataset.a) : null;
  if (act === "pick") { picked.has(a.id) ? picked.delete(a.id) : picked.add(a.id); t.classList.toggle("on"); updSel(); }
  else if (act === "gpick") {
    const vis = g.apps.filter(x => !card.querySelector(`.arow[data-a="${x.id}"]`).classList.contains("hide"));
    const all = vis.every(x => picked.has(x.id));
    vis.forEach(x => all ? picked.delete(x.id) : picked.add(x.id)); renderGroups();
  }
  else if (act === "run") {
    if (a.kind === "office") return openOffice();
    if (a.kind === "open") { await api("quick", a.src.slice(5).trim()); return toast("🌐 Đang mở " + a.name); }
    if (a.kind === "none") { if (ADMIN) return editApp(a, gid); return toast("Nút này chưa có nguồn. Mở Admin rồi bấm ✎ để thêm link.", "err"); }
    await api("install", [a.id]); toast("▶ " + a.name);
  }
  else if (act === "edit") editApp(a, gid);
  else if (act === "add") editApp(null, gid);
  else if (act === "gedit") { const n = await promptBox("Đổi tên nhóm", "Tên nhóm:", g.name); if (n !== null) { await api("save_group", gid, n); loadGroups(); } }
  else if (["gup", "gdown", "gleft", "gright"].includes(act)) {
    if (!(await api("move_group", gid, act.slice(1)))) return toast("Không di chuyển được về phía đó", "err");
    await loadGroups();
    const el = document.querySelector(`.gcard[data-g="${gid}"]`);
    if (el) { el.classList.add("flash"); setTimeout(() => el.classList.remove("flash"), 900); }
  }
  else if (act === "aup" || act === "adown") { await api("move_app", a.id, act === "aup" ? -1 : 1); loadGroups(); }
  else if (act === "gdel") {
    if (await confirmBox("Xóa nhóm", `Xóa nhóm "${g.name}" cùng ${g.apps.length} nút bên trong?`, "🗑 Xóa nhóm")) { await api("delete_group", gid); loadGroups(); }
  }
};

const EMOJI = "📦 🌐 ⌨️ 📄 📝 🎬 🎞️ 🖥️ 💬 ☁️ ⚙️ 🛠️ 🔎 🧹 📸 🐍 🟢 ☕ 🔧 📱 🎮 🛡️ 🔑 💽 🖨️ 🎧 🧩 📊 🚀 ⭐".split(" ");
function editApp(a, gid) {
  const isNew = !a;
  a = a || {id: 0, icon: "📦", name: "", src: "", args: "", note: "", group_id: gid};
  const gopts = G.map(g => `<option value="${g.id}"${g.id === (a.group_id || gid) ? " selected" : ""}>${esc(g.name)}</option>`).join("");
  return dialog({title: isNew ? "Thêm phần mềm" : "Sửa nút: " + a.name, width: 640,
    body: `<label class="fl">TÊN NÚT</label>
      <div class="row2"><input id="eIcon" style="width:56px;flex:none;text-align:center;font-size:16px" value="${esc(a.icon)}">
        <input id="eName" value="${esc(a.name)}" placeholder="VD: Google Chrome"></div>
      <div class="emo">${EMOJI.map(x => `<span>${x}</span>`).join("")}</div>
      <label class="fl">NGUỒN APP (link tải / file trên máy / winget / lệnh)</label>
      <div class="row2"><input id="eSrc" value="${esc(a.src)}" placeholder="https://...  hoặc  Soft\\UniKey.exe  hoặc  winget:Google.Chrome">
        <button class="btn sm" id="ePick">📂 Chọn file</button><button class="btn sm" id="eTest">🧪 Thử</button></div>
      <div class="srcinfo" id="eInfo"></div>
      <div class="help">
        <code>https://...</code> link tải trực tiếp file .exe / .msi / .zip (link Google Drive dạng /file/d/... cũng được). Nếu là trang web, tool mở trang bằng trình duyệt.<br>
        <code>Soft\\Ten file.exe</code> file nằm trong thư mục tool (để chạy từ USB), hoặc đường dẫn đầy đủ <code>D:\\Setup\\app.exe</code>.<br>
        <code>winget:Google.Chrome</code> cài bản mới nhất bằng winget của Windows.<br>
        <code>cmd:lệnh</code> chạy lệnh Windows bằng quyền Admin. <code>page:trang-web|mẫu-link</code> đọc trang web lấy link tải mới nhất. <code>office:</code> mở cửa sổ cài MS Office.<br>
        <code>open:https://...</code> chỉ mở link bằng trình duyệt (kho phần mềm, trang tải...).<br>
        <code>github:chủ/repo|mẫu-tên-file</code> luôn tải file mới nhất trên GitHub, VD <code>github:storytold/wordcraft|windows-x64-portable\.zip$</code>.<br>
        <code>winget:9NKSQGP7F2NH</code> (ID 12 ký tự) cài từ Microsoft Store.</div>
      <label class="fl">THAM SỐ CÀI ĐẶT (không bắt buộc, VD cài im lặng: /S, /silent, /quiet)</label>
      <input id="eArgs" style="width:100%" value="${esc(a.args)}">
      <div class="row2" style="margin-top:4px;gap:14px">
        <div style="flex:1"><label class="fl">GHI CHÚ (hiện khi rê chuột)</label><input id="eNote" style="width:100%" value="${esc(a.note)}"></div>
        <div style="width:210px"><label class="fl">NHÓM</label><select id="eGroup" style="width:100%">${gopts}</select></div></div>
      <div class="err"></div>`,
    left: isNew ? "" : `<button class="btn out" id="eDel">🗑 Xóa nút</button><button class="btn sm" id="eUp" title="Đưa lên">▲</button><button class="btn sm" id="eDown" title="Đưa xuống">▼</button>`,
    buttons: [{text: "Hủy", value: false}, {text: "✓ Lưu", cls: "green", def: true, click: async c => {
      const d = {id: a.id, icon: c.q("#eIcon").value, name: c.q("#eName").value.trim(), src: c.q("#eSrc").value.trim(),
        args: c.q("#eArgs").value, note: c.q("#eNote").value, group_id: +c.q("#eGroup").value};
      if (!d.name) { c.err("Chưa nhập tên nút"); return false; }
      await api("save_app", d); await loadGroups(); toast("Đã lưu nút " + d.name); return true; }}],
    onOpen: c => {
      c.q(".emo").onclick = e => { if (e.target.tagName === "SPAN") c.q("#eIcon").value = e.target.textContent; };
      c.q("#ePick").onclick = async () => { const p = await api("pick_file"); if (p) c.q("#eSrc").value = p; else if (p === null && !window.pywebview) toast("Bản trình duyệt: hãy gõ đường dẫn vào ô"); };
      c.q("#eTest").onclick = async () => { c.q("#eInfo").innerHTML = '<span class="spin"></span> Đang kiểm tra...'; c.q("#eInfo").textContent = await api("test_source", c.q("#eSrc").value); };
      if (!isNew) {
        c.q("#eDel").onclick = async () => { if (await confirmBox("Xóa nút", `Xóa nút "${a.name}"?`, "🗑 Xóa")) { await api("delete_app", a.id); await loadGroups(); c.close(false); } };
        c.q("#eUp").onclick = async () => { await api("move_app", a.id, -1); loadGroups(); };
        c.q("#eDown").onclick = async () => { await api("move_app", a.id, 1); loadGroups(); };
      }
      setTimeout(() => c.q("#eName").focus(), 40);
    }});
}


/* ---------------------------------------------------------------- MS Office */
let OFF = {ver: "2024", ed: "ProPlus", bit: "64", lang: "en-us", en: false, apps: ["Word", "Excel", "PowerPoint"], project: false, visio: false, shortcut: true};
async function openOffice() {
  const info = await api("office_info"), st = info.status;
  try { OFF = Object.assign(OFF, JSON.parse(localStorage.getItem("winaio_office") || "{}")); } catch (e) { /* bỏ qua */ }
  const vers = ["2016", "2019", "2021", "2024", "365"];
  const radio = (name, list, cur) => list.map(([v, t]) => `<label class="ofr${v === cur ? " on" : ""}"><input type="radio" name="${name}" value="${v}"${v === cur ? " checked" : ""}> ${esc(t)}</label>`).join("");
  const body = `
    <div class="ofsrc ${st.offline ? "off" : "on"}">${st.offline ? `📦 <b>OFFLINE</b> — có thư viện cài sẵn ở ${esc(st.offline_dir)}, cài nhanh không cần mạng.`
      : `🌐 <b>ONLINE</b> — Microsoft sẽ tải bộ cài trong lúc cài (cần mạng). Muốn cài offline: bấm "⬇ Tải thư viện offline" một lần.`}</div>
    ${st.installed.length ? `<div class="pwwarn">Máy đang có Office: ${esc(st.installed.join(", "))}. Cài bản khác nên bấm "🗑 Gỡ Office cũ" trước.</div>` : ""}
    <label class="fl">PHIÊN BẢN</label><div class="ofrow" id="oVer">${radio("ver", vers.map(v => [v, v === "365" ? "Office 365" : "Office " + v]), OFF.ver)}</div>
    <label class="fl">BIẾN THỂ (EDITION)</label><div class="ofrow" id="oEd"></div>
    <div class="row2" style="gap:24px;align-items:flex-start">
      <div><label class="fl">KIẾN TRÚC</label><div class="ofrow" id="oBit">${radio("bit", [["64", "64-bit"], ["32", "32-bit"]], OFF.bit)}</div></div>
      <div style="flex:1"><label class="fl">NGÔN NGỮ</label><div class="row2"><select id="oLang">${info.langs.map(([c, n]) => `<option value="${c}"${c === OFF.lang ? " selected" : ""}>${esc(n)} – ${c}</option>`).join("")}</select>
        <label class="ck" style="margin:0"><input type="checkbox" id="oEn"${OFF.en ? " checked" : ""}> kèm English</label></div></div></div>
    <label class="fl">ỨNG DỤNG <a id="oAll" style="margin-left:8px;font-weight:700">chọn tất cả</a></label>
    <div class="ofapps" id="oApps">${info.apps.map(a => `<label class="ck"><input type="checkbox" value="${a}"${OFF.apps.includes(a) ? " checked" : ""}> ${a}</label>`).join("")}
      <label class="ck"><input type="checkbox" id="oProj"${OFF.project ? " checked" : ""}> 📋 Project Pro</label>
      <label class="ck"><input type="checkbox" id="oVisio"${OFF.visio ? " checked" : ""}> 📈 Visio Pro</label></div>
    <label class="ck" style="margin-top:8px"><input type="checkbox" id="oSc"${OFF.shortcut ? " checked" : ""}> Ghim biểu tượng Word / Excel / PowerPoint... ra Desktop sau khi cài</label>
    <div class="help">Cài bằng Office Deployment Tool chính chủ của Microsoft. Office cài xong ở trạng thái chưa kích hoạt — nhập key bản quyền của khách ở nút "🔑 Bản quyền" (có cả kích hoạt qua điện thoại).</div>
    <div class="err"></div>`;
  const read = c => {
    const v = n => (c.el.querySelector(`input[name="${n}"]:checked`) || {}).value;
    OFF = {ver: v("ver"), ed: v("ed"), bit: v("bit"), lang: c.q("#oLang").value, en: c.q("#oEn").checked,
      apps: [...c.el.querySelectorAll("#oApps input[value]")].filter(x => x.checked).map(x => x.value),
      project: c.q("#oProj").checked, visio: c.q("#oVisio").checked, shortcut: c.q("#oSc").checked};
    try { localStorage.setItem("winaio_office", JSON.stringify(OFF)); } catch (e) { /* bỏ qua */ }
    return OFF;
  };
  dialog({title: "Cài đặt Microsoft Office", width: 720, body,
    left: `<button class="btn sm" id="oDl" title="Tải bộ cài về Soft\\Office để lần sau cài không cần mạng">⬇ Tải thư viện offline</button>
      <button class="btn sm" id="oUn">🗑 Gỡ Office</button><button class="btn sm" id="oLic">🔑 Bản quyền</button>
      <button class="btn sm" id="oTune" title="A4, lề, Times New Roman, giãn dòng, tắt Protected View...">📝 Thiết lập Office</button><button class="btn sm" id="oSc2">🔗 Ghim Desktop</button>`,
    buttons: [{text: "Đóng", value: false}, {text: "⚙ CÀI ĐẶT", cls: "red shine", def: true, click: async c => {
      const o = read(c); const m = await api("office_install", o);
      if (m) { c.err(m); return false; }
      toast("Đang cài Office — theo dõi cửa sổ cài của Microsoft và nhật ký"); return true; }}],
    onOpen: c => {
      c.el.addEventListener("change", e => { const l = e.target.closest(".ofr"); if (l) l.parentElement.querySelectorAll(".ofr").forEach(x => x.classList.toggle("on", x.contains(c.el.querySelector(`input[name="${e.target.name}"]:checked`)))); });
      c.q("#oAll").onclick = () => { const bs = [...c.el.querySelectorAll("#oApps input[value]")]; const all = bs.every(b => b.checked); bs.forEach(b => b.checked = !all); };
      c.q("#oDl").onclick = async () => { if (!(await confirmBox("Tải thư viện offline", `Tải bộ cài Office theo lựa chọn hiện tại về thư mục Soft\\Office kế bên tool (khoảng 2-4 GB).\nLần sau cài không cần mạng.`, "⬇ Tải", false))) return;
        const m = await api("office_download", read(c)); m ? c.err(m) : toast("Đang tải thư viện Office — xem nhật ký"); };
      c.q("#oUn").onclick = () => offRemoveBox();
      c.q("#oSc2").onclick = async () => { const m = await api("office_shortcuts"); m ? c.err(m) : toast("Đã ghim biểu tượng Office ra Desktop"); };
      c.q("#oLic").onclick = () => licBox("office");
      c.q("#oTune").onclick = () => offTuneBox();
      const edRow = () => { const v = (c.el.querySelector('input[name="ver"]:checked') || {}).value; const list = v === "365" ? info.editions365 : info.editions;
        const cur = list.some(x => x[0] === OFF.ed) ? OFF.ed : list[0][0]; c.q("#oEd").innerHTML = radio("ed", list, cur); };
      edRow(); c.q("#oVer").addEventListener("change", edRow);
    }});
}

/* ---------------------------------------------------------------- Hệ thống */
const gb = v => v >= 1000 ? (v / 1000).toFixed(v % 1000 ? 1 : 0) + " TB" : (+v).toLocaleString("vi-VN") + " GB";
const pill = (t, cls) => `<span class="pill ${cls}">${esc(t)}</span>`;
const goodBad = (t, good) => pill(t || "—", good === null ? "t-skip" : good ? "t-done" : "t-err");
const kv = rows => `<div class="kv">${rows.filter(r => r && r[1] !== undefined && r[1] !== "").map(([k, v, raw]) =>
  `<div class="k">${esc(k)}</div><div class="v">${raw ? v : esc(v)}</div>`).join("")}</div>`;
/* ===== Hình minh họa 3D (SVG tự vẽ) cho Giao diện 01 ===== */
const ISO = (x, y, body) => `<g transform="translate(${x},${y}) matrix(.75,.4,-.75,.4,0,0)">${body}</g>`;
const EXT = (x, y, h, sil) => { let o = ""; for (let i = h; i > 0; i -= 1) o += ISO(x, y + i, sil); return o; };
const SVG = (inner, vb = "0 0 200 150") => `<svg viewBox="${vb}" xmlns="http://www.w3.org/2000/svg">${inner}</svg>`;
const ILLU = {
  cpu: () => SVG(`<defs><linearGradient id="cpA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#34407a"/><stop offset="1" stop-color="#141a3a"/></linearGradient>
    <linearGradient id="cpB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#c3cbe0"/><stop offset="1" stop-color="#7f8aa8"/></linearGradient></defs>
    <ellipse cx="100" cy="100" rx="78" ry="26" fill="var(--ac)" opacity=".35" filter="blur(8px)"/>
    ${EXT(100, 66, 9, `<rect x="-50" y="-50" width="100" height="100" rx="6" fill="#0a0f24"/>`)}
    ${ISO(100, 66, `<rect x="-50" y="-50" width="100" height="100" rx="6" fill="url(#cpA)" stroke="var(--ac)" stroke-width="1.5"/>` +
      Array.from({length: 12}, (_, i) => -44 + i * 8).map(v => `<circle cx="${v}" cy="-45" r="1.6" fill="#f0c860"/><circle cx="${v}" cy="45" r="1.6" fill="#f0c860"/><circle cx="-45" cy="${v}" r="1.6" fill="#f0c860"/><circle cx="45" cy="${v}" r="1.6" fill="#f0c860"/>`).join(""))}
    ${EXT(100, 60, 6, `<rect x="-33" y="-33" width="66" height="66" rx="8" fill="#5b6687"/>`)}
    ${ISO(100, 60, `<rect x="-33" y="-33" width="66" height="66" rx="8" fill="url(#cpB)"/><text x="0" y="7" text-anchor="middle" font-size="19" font-weight="900" font-family="Segoe UI,Arial" fill="#46507a">CPU</text><rect x="-20" y="12" width="40" height="3" rx="1.5" fill="#8a94b4"/>`)}`),
  ram: () => { const stick = (x, y) => EXT(x, y, 5, `<rect x="-78" y="-17" width="156" height="34" rx="3" fill="#07331c"/>`) +
      ISO(x, y, `<rect x="-78" y="-17" width="156" height="34" rx="3" fill="url(#rmA)" stroke="#7dffb4" stroke-width=".8"/>` +
        [-58, -29, 0, 29, 58].map(c => `<rect x="${c - 11}" y="-12" width="22" height="15" rx="1.5" fill="#10151f" stroke="#3a4458" stroke-width=".6"/>`).join("") +
        Array.from({length: 30}, (_, i) => `<rect x="${-74 + i * 5}" y="9" width="3" height="7" fill="#f2c95b"/>`).join(""));
    return SVG(`<defs><linearGradient id="rmA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2fbf6a"/><stop offset="1" stop-color="#0d6b38"/></linearGradient></defs>
      <ellipse cx="100" cy="104" rx="80" ry="24" fill="var(--ac)" opacity=".35" filter="blur(8px)"/>${stick(92, 58)}${stick(108, 84)}`); },
  gpu: () => { const fan = (cx) => `<circle cx="${cx}" cy="0" r="30" fill="#0a0d14" stroke="#3c475c" stroke-width="2"/>` +
      Array.from({length: 9}, (_, i) => `<path d="M${cx} 0 q 10 -14 0 -27 q -6 12 0 27z" fill="#262f40" transform="rotate(${i * 40} ${cx} 0)"/>`).join("") +
      `<circle cx="${cx}" cy="0" r="8" fill="#1c2433" stroke="var(--ac)" stroke-width="1.5"/>`;
    return SVG(`<defs><linearGradient id="gpA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a4357"/><stop offset="1" stop-color="#11151f"/></linearGradient></defs>
      <ellipse cx="100" cy="106" rx="82" ry="26" fill="var(--ac)" opacity=".35" filter="blur(8px)"/>
      ${EXT(100, 66, 14, `<rect x="-72" y="-40" width="144" height="80" rx="9" fill="#06080d"/>`)}
      ${ISO(100, 66, `<rect x="-72" y="-40" width="144" height="80" rx="9" fill="url(#gpA)" stroke="var(--ac)" stroke-width="1.5"/>${fan(-34)}${fan(34)}<rect x="-66" y="-37" width="132" height="3" rx="1.5" fill="var(--ac)"/>`)}`); },
  wifi: () => SVG(`<g fill="none" stroke="url(#wfA)" stroke-linecap="round" stroke-width="13" filter="drop-shadow(0 0 6px var(--ac))">
      <path d="M58 82 A60 60 0 0 1 142 82"/><path d="M76 98 A34 34 0 0 1 124 98"/></g>
      <path d="M38 64 A88 88 0 0 1 162 64" fill="none" stroke="url(#wfA)" stroke-width="13" stroke-linecap="round" filter="drop-shadow(0 0 6px var(--ac))"/>
      <circle cx="100" cy="118" r="10" fill="#bff1ff" filter="drop-shadow(0 0 8px var(--ac))"/>
      <defs><linearGradient id="wfA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9fbff"/><stop offset="1" stop-color="#4cc3ff"/></linearGradient></defs>`),
  lan: () => SVG(`<defs><radialGradient id="lnA" cx=".35" cy=".3"><stop offset="0" stop-color="#bfe9ff"/><stop offset=".5" stop-color="#3b8cff"/><stop offset="1" stop-color="#123a9a"/></radialGradient></defs>
      <circle cx="100" cy="74" r="52" fill="url(#lnA)" filter="drop-shadow(0 0 10px var(--ac))"/>
      <g fill="none" stroke="#e6f6ff" stroke-width="2.4" opacity=".85"><ellipse cx="100" cy="74" rx="22" ry="52"/><path d="M48 74 H152 M56 48 H144 M56 100 H144 M100 22 V126"/></g>`),
  os: () => SVG(`<defs><linearGradient id="osA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#42e08a"/><stop offset=".5" stop-color="#1b8fd0"/><stop offset="1" stop-color="#173d9a"/></linearGradient></defs>
      <ellipse cx="100" cy="136" rx="70" ry="10" fill="var(--ac)" opacity=".4" filter="blur(6px)"/>
      <path d="M86 112 h28 l6 18 h-40z" fill="#9aa6c0"/><rect x="66" y="128" width="68" height="6" rx="3" fill="#c9d2e6"/>
      <rect x="26" y="14" width="148" height="100" rx="9" fill="#0b1430" stroke="var(--ac)" stroke-width="2"/>
      <rect x="34" y="22" width="132" height="84" rx="4" fill="url(#osA)"/>
      <rect x="44" y="34" width="66" height="44" rx="4" fill="#fff" opacity=".92"/><rect x="44" y="34" width="66" height="8" rx="4" fill="#d7e3ff"/>
      <rect x="92" y="54" width="62" height="42" rx="4" fill="#fff" opacity=".7"/><rect x="92" y="54" width="62" height="8" rx="4" fill="#c4d6ff"/>
      <rect x="50" y="48" width="40" height="4" rx="2" fill="#9fb4e0"/><rect x="50" y="56" width="30" height="4" rx="2" fill="#9fb4e0"/>`),
  board: () => SVG(`<defs><linearGradient id="bdA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d59bff"/><stop offset=".5" stop-color="#8a3cf0"/><stop offset="1" stop-color="#3c138a"/></linearGradient></defs>
      <g stroke="var(--ac)" stroke-width="2.5" fill="none" opacity=".75"><path d="M20 60 H48 M20 84 H40 L48 92 M180 60 H152 M180 84 H160 L152 92"/></g>
      <g fill="var(--ac)"><circle cx="20" cy="60" r="4"/><circle cx="20" cy="84" r="4"/><circle cx="180" cy="60" r="4"/><circle cx="180" cy="84" r="4"/></g>
      <path d="M100 14 L152 32 V72 C152 104 130 124 100 136 C70 124 48 104 48 72 V32 Z" fill="url(#bdA)" stroke="#f1dcff" stroke-width="2" filter="drop-shadow(0 0 10px var(--ac))"/>
      <path d="M100 26 L142 40 V72 C142 98 124 114 100 124 Z" fill="#fff" opacity=".12"/>
      <path d="M76 74 L94 92 L126 58" fill="none" stroke="#fff" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>`),
  disk: () => SVG(`<defs><linearGradient id="sdA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f4f7ff"/><stop offset=".6" stop-color="#b4bfd8"/><stop offset="1" stop-color="#7d89a8"/></linearGradient></defs>
      <ellipse cx="100" cy="104" rx="76" ry="24" fill="var(--ac)" opacity=".35" filter="blur(8px)"/>
      ${EXT(100, 66, 10, `<rect x="-56" y="-38" width="112" height="76" rx="6" fill="#4f5a78"/>`)}
      ${ISO(100, 66, `<rect x="-56" y="-38" width="112" height="76" rx="6" fill="url(#sdA)"/><rect x="-42" y="-24" width="84" height="48" rx="4" fill="#1b2a52"/>
        <text x="0" y="4" text-anchor="middle" font-size="20" font-weight="900" font-family="Segoe UI,Arial" fill="#8fb4ff">SSD</text><rect x="-26" y="10" width="52" height="3" rx="1.5" fill="var(--ac)"/>`)}`),
  laptop: () => SVG(`<defs><linearGradient id="lpA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7fd0ff"/><stop offset=".45" stop-color="#2a7bff"/><stop offset="1" stop-color="#0d2a8a"/></linearGradient>
      <linearGradient id="lpB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9eef8"/><stop offset="1" stop-color="#8d98b3"/></linearGradient></defs>
      <rect x="42" y="12" width="136" height="90" rx="8" fill="#141c33" stroke="#9cc4ff" stroke-width="1.5"/>
      <rect x="49" y="19" width="122" height="76" rx="3" fill="url(#lpA)"/>
      <path d="M49 80 C90 60 120 92 171 48 V95 H49z" fill="#fff" opacity=".14"/><path d="M49 62 C88 40 130 70 171 30" stroke="#d6f0ff" stroke-width="2" fill="none" opacity=".7"/>
      <rect x="92" y="38" width="36" height="36" rx="8" fill="#fff" opacity=".18" stroke="#e7f5ff" stroke-width="1.5"/>
      <path d="M22 104 H198 L184 124 Q182 128 176 128 H44 Q38 128 36 124Z" fill="url(#lpB)"/><rect x="96" y="104" width="28" height="4" rx="2" fill="#7b86a2"/>`, "0 0 220 140"),
  desktop: () => SVG(`<defs><linearGradient id="dkA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7fd0ff"/><stop offset=".45" stop-color="#2a7bff"/><stop offset="1" stop-color="#0d2a8a"/></linearGradient></defs>
      <rect x="150" y="26" width="44" height="98" rx="6" fill="#1a2440" stroke="#9cc4ff" stroke-width="1.5"/><circle cx="172" cy="42" r="5" fill="#6fd0ff"/>
      <rect x="158" y="56" width="28" height="3" rx="1.5" fill="#4b5c8a"/><rect x="158" y="64" width="28" height="3" rx="1.5" fill="#4b5c8a"/>
      <rect x="18" y="14" width="132" height="88" rx="8" fill="#141c33" stroke="#9cc4ff" stroke-width="1.5"/>
      <rect x="25" y="21" width="118" height="74" rx="3" fill="url(#dkA)"/><path d="M25 78 C64 58 96 90 143 46 V95 H25z" fill="#fff" opacity=".14"/>
      <path d="M72 102 h24 l6 16 h-36z" fill="#9aa6c0"/><rect x="56" y="116" width="56" height="6" rx="3" fill="#c9d2e6"/>`, "0 0 210 130"),
};
function scard(ic, color, title, body, wide, k) {
  return `<div class="scard${wide ? " wide" : ""}" style="--ac:${color}" data-deco="${ic}"${k ? ` data-k="${k}"` : ""}>${k && ILLU[k] ? `<div class="illu">${ILLU[k]()}</div>` : ""}<div class="sh"><span class="si">${ic}</span><b>${esc(title)}</b></div>${body}</div>`;
}
function ring(id, label, color) {
  return `<div class="ring" id="${id}" style="--c:${color};--p:0"><div class="rin"><b>0%</b><small>${label}</small></div></div>`;
}
function renderInfo() {
  const si = ST.sysinfo;
  if (!si) { $("hero").innerHTML = '<div class="empty"><span class="spin"></span> Đang đọc thông tin máy... (lần đầu mất vài giây)</div>'; $("info").innerHTML = ""; return; }
  if (si.err) { $("hero").innerHTML = `<div class="empty">Không đọc được thông tin máy: ${esc(si.err)}</div>`; return; }
  const pc = si.pc || {}, os = si.os || {}, cpu = si.cpu || {}, ram = si.ram || {}, bd = si.board || {};
  const ip = (si.net || []).map(n => n.ip).filter(Boolean).join(", ");
  $("hero").innerHTML = `
    <div class="hl"><div class="hico"><span class="hemo">${pc.type === "Laptop" ? "💻" : "🖥️"}</span><span class="hsvg">${ILLU[pc.type === "Laptop" ? "laptop" : "desktop"]()}</span></div>
      <div class="hx"><div class="hn">${esc(pc.name)}</div>
        <div class="hs">${esc([pc.maker, pc.model].filter(Boolean).join(" · "))} <span class="pill t-new">${pc.type === "Laptop" ? "Laptop" : "Desktop"}</span></div>
        <div class="chips2">
          <span class="chip"><i>🪟</i>${esc(os.name)} ${esc(os.ver)} <em>build ${esc(os.build)}</em></span>
          <span class="chip"><i>👤</i>${esc(pc.user)}</span>
          <span class="chip cp" data-copy="${esc(pc.tag || "")}" title="Bấm để copy"><i>🏷️</i>Service Tag <b>${esc(pc.tag || "không có")}</b>${pc.tag ? " ⧉" : ""}</span>
          ${ip ? `<span class="chip cp" data-copy="${esc(ip)}" title="Bấm để copy"><i>🌐</i>IP <b>${esc(ip)}</b> ⧉</span>` : ""}
        </div></div></div>
    <div class="hr">${ring("rCpu", "CPU", "#e0262a")}${ring("rRam", "RAM", "#2f7fa3")}${ring("rGpu", "GPU", "#7c3aed")}
      <div class="upt"><small>ĐÃ CHẠY</small><b id="upt">—</b><small id="ramtx"></small></div>
      <div class="hbtn"><button class="btn sm" id="bSysRef">⟳ Làm mới</button><button class="btn sm" id="bSysCopy">⧉ Copy tất cả</button></div></div>`;
  const slots = Math.max(ram.slots || 0, (ram.sticks || []).length);
  const slotHtml = slots ? `<div class="slots">${Array.from({length: slots}, (_, i) => { const st = (ram.sticks || [])[i];
    return st ? `<div class="slot on"><b>${st.size} GB</b><small>${esc(st.slot || "Khe " + (i + 1))}${st.maker && !/^0+$|unknown/i.test(st.maker) ? " · " + esc(st.maker) : ""}</small></div>`
      : `<div class="slot"><b>Trống</b><small>Khe ${i + 1}</small></div>`; }).join("")}</div>` : "";
  const cards = [
    scard("⚙️", "#e0262a", "BỘ XỬ LÝ", `<div class="big">${esc(cpu.name)}</div>` + kv([
      ["Nhân / Luồng", `${cpu.cores} nhân · ${cpu.threads} luồng`], ["Xung tối đa", cpu.mhz ? (cpu.mhz / 1000).toFixed(2) + " GHz" : ""], ["Socket", cpu.socket]]) +
      `<div class="lbar"><span>Đang dùng</span><div class="bar"><div class="b-red" id="lCpu"></div></div><b id="lCpuT">0%</b></div>`, false, "cpu"),
    scard("🧠", "#2f7fa3", "BỘ NHỚ RAM", `<div class="big">${ram.total} GB ${esc(ram.type || "")}${ram.speed ? ` <em>· ${ram.speed} MT/s</em>` : ""}</div>` +
      kv([["Đã gắn", `${(ram.sticks || []).length} thanh${slots ? " / " + slots + " khe" : ""}`]]) + slotHtml +
      `<div class="lbar"><span>Đang dùng</span><div class="bar"><div class="b-blue" id="lRam"></div></div><b id="lRamT">0%</b></div>`, false, "ram"),
    scard("🎮", "#7c3aed", "CARD ĐỒ HỌA", (si.gpu || []).map(g => `<div class="gpu"><div class="big sm2">${esc(g.name)}</div><div class="chips3">
      ${g.vram ? `<span>${g.vram} GB VRAM</span>` : ""}${g.res ? `<span>${esc(g.res)}${g.hz > 1 ? " @ " + g.hz + " Hz" : ""}</span>` : ""}${g.driver ? `<span>Driver ${esc(g.driver)}</span>` : ""}</div></div>`).join("") || '<div class="logl">Không đọc được</div>', false, "gpu"),
    scard("🌐", "#16a34a", "MẠNG", (si.net || []).map(n => `<div class="nic"><div class="big sm2">${esc(n.name)} <em>${esc(n.speed)}</em></div>
      <div class="logl" style="margin:0 0 4px">${esc(n.desc)}</div>${kv([["IPv4", n.ip], ["MAC", n.mac]])}</div>`).join("") || '<div class="logl">Không có mạng đang kết nối</div>', false, /wi-?fi|wireless|wlan|802\.11/i.test(((si.net || [])[0] || {}).name + " " + ((si.net || [])[0] || {}).desc) ? "wifi" : "lan"),
    scard("🪟", "#0f8fd8", "HỆ ĐIỀU HÀNH", kv([["Phiên bản", `${os.name} ${os.ver}`], ["Build", os.build], ["Kiến trúc", os.arch], ["Ngày cài Win", os.installed],
      ["Khởi động lúc", os.boot], ["Bản quyền", goodBad(os.license, /Đã/.test(os.license || "") ? true : /Chưa/.test(os.license || "") ? false : null), true],
      ["BitLocker ổ C", goodBad(os.bitlocker, /BẬT/.test(os.bitlocker || "") ? false : /Tắt/.test(os.bitlocker || "") ? true : null), true]]), false, "os"),
    scard("🧩", "#d97706", "BO MẠCH & BẢO MẬT", kv([["Mainboard", [bd.maker, bd.product].filter(Boolean).join(" ")], ["BIOS", [bd.bios, bd.bios_date].filter(Boolean).join(" · ")],
      ["Chế độ khởi động", bd.mode ? pill(bd.mode, bd.mode === "UEFI" ? "t-done" : "t-skip") : "", true],
      ["Secure Boot", goodBad(bd.secure, bd.secure === "Bật" ? true : bd.secure === "Tắt" ? false : null), true],
      ["TPM", goodBad(bd.tpm && bd.tpm !== "Không có" ? "TPM " + bd.tpm : "Không có", bd.tpm && bd.tpm !== "Không có" ? true : null), true]]), false, "board"),
    scard("💽", "#0d9488", "LƯU TRỮ", `<div class="dgrid"><div>${(si.disks || []).map(d => `<div class="pdisk"><span class="di">${d.media === "HDD" ? "🗄️" : "⚡"}</span>
        <div class="dx"><b>${esc(d.name)}</b><div class="chips3"><span>${esc([d.bus, d.media].filter(Boolean).join(" "))}</span><span>${gb(d.size)}</span></div></div>
        ${goodBad(d.health || "?", d.health === "Tốt" ? true : d.health ? false : null)}</div>`).join("")}</div>
      <div>${(si.vols || []).filter(v => v.bl === "locked").length ? `<div class="blwarn">🔒 Ổ ${(si.vols || []).filter(v => v.bl === "locked").map(v => esc(v.l) + ":").join(", ")} đang bị KHÓA BitLocker - cần mật khẩu / Recovery Key để mở</div>` : ""}
        ${(si.vols || []).map(v => { const used = v.size - v.free, pct = v.size ? Math.round(used / v.size * 100) : 0;
        if (v.bl === "locked") return `<div class="vol locked"><div class="vt"><b>${esc(v.l)}:</b> 🔒 <b class="blk">ĐANG KHÓA BITLOCKER</b><span>${gb(Math.round(v.size))}</span></div>
          <div class="bar"><div class="b-red" style="width:100%"></div></div></div>`;
        return `<div class="vol"><div class="vt"><b>${esc(v.l)}:</b> ${esc(v.label || "Local Disk")} <em>${esc(v.fs)}</em>${v.bl === "on" ? ' <em class="blon" title="Ổ được mã hóa BitLocker (đang mở khóa)">🔐</em>' : ""}<span>${v.free.toFixed(1)} GB trống / ${gb(Math.round(v.size))}</span></div>
          <div class="bar"><div class="${pct >= 90 ? "b-red" : pct >= 75 ? "b-orange" : "b-green"}" style="width:${pct}%"></div></div></div>`; }).join("")}</div></div>`, true, "disk"),
  ];
  $("info").innerHTML = cards.join("");
  [30, 400, 1500].forEach(t => setTimeout(fitSys, t));
  $("bSysRef").onclick = () => { api("refresh_sysinfo"); ST.sysinfo = SYSI = null; SIV = null; infoShown = undefined; renderInfo(); };
  $("bSysCopy").onclick = () => { copyLocal(sysText(si)) && toast("Đã copy thông tin máy"); };
  live();
}
$("hero").addEventListener("click", e => { const c = e.target.closest(".cp"); if (c && c.dataset.copy) { copyLocal(c.dataset.copy); toast("Đã copy: " + c.dataset.copy); } });
function sysText(si) {
  const pc = si.pc || {}, os = si.os || {}, cpu = si.cpu || {}, ram = si.ram || {}, bd = si.board || {};
  return [`Tên máy: ${pc.name}`, `Model: ${pc.maker} ${pc.model} (${pc.type})`, `Service Tag: ${pc.tag || "-"}`, `Windows: ${os.name} ${os.ver} build ${os.build} ${os.arch}`,
    `Bản quyền: ${os.license} · BitLocker C: ${os.bitlocker}`, `CPU: ${cpu.name} · ${cpu.cores} nhân ${cpu.threads} luồng`,
    `RAM: ${ram.total} GB ${ram.type || ""} ${ram.speed || ""} MT/s · ${(ram.sticks || []).map(x => x.size + " GB").join(" + ")} · ${ram.slots || "?"} khe`,
    ...(si.gpu || []).map(g => `GPU: ${g.name} · ${g.vram} GB${g.res ? " · " + g.res : ""}`),
    ...(si.disks || []).map(d => `Ổ cứng: ${d.name} · ${d.bus} ${d.media} · ${gb(d.size)} · ${d.health}`),
    ...(si.vols || []).map(v => `Phân vùng ${v.l}: ${v.free} / ${v.size} GB trống`),
    `Mainboard: ${bd.maker} ${bd.product} · BIOS ${bd.bios} ${bd.bios_date} · ${bd.mode} · Secure Boot ${bd.secure} · TPM ${bd.tpm}`,
    ...(si.net || []).map(n => `Mạng: ${n.name} · ${n.ip} · ${n.mac}`)].join("\n");
}
let liveBusy = false;
async function live() {
  if (liveBusy || page !== "system" || !ST.sysinfo || document.hidden || !$("rCpu")) return;
  liveBusy = true;
  try {
    const L = await api("live");
    const set = (id, p, t) => { const r = $(id); r.style.setProperty("--p", p); r.querySelector("b").textContent = t; };
    set("rCpu", L.cpu, L.cpu + "%"); set("rRam", L.ram_pct, L.ram_pct + "%");
    const gr = $("rGpu"), G = L.gpu;
    if (gr) { const gb = n => (n / 1073741824).toFixed(1);
      set("rGpu", G && G.pct != null ? G.pct : 0, !G ? "—" : G.pct != null ? G.pct + "%" : gb(G.used) + "G");
      gr.style.setProperty("--c", !G ? "#9ca3af" : G.pct >= 90 ? "#e0262a" : G.pct >= 70 ? "#d97706" : "#7c3aed");
      gr.title = !G ? "Không đọc được bộ nhớ GPU (Windows 10 bản 1709 trở lên + driver WDDM 2 mới có)"
        : `Bộ nhớ GPU (VRAM) đang dùng: ${gb(G.used)}${G.total ? " / " + gb(G.total) : ""} GB · tải 3D ${G.load}%`;
      gr.querySelector("small").textContent = G && G.total ? `GPU ${gb(G.used)}/${Math.round(G.total / 1073741824)}G` : "GPU"; }
    $("lCpu").style.width = L.cpu + "%"; $("lCpuT").textContent = L.cpu + "%";
    $("lRam").style.width = L.ram_pct + "%"; $("lRamT").textContent = `${L.ram_used} / ${L.ram_total} GB`;
    const u = L.uptime, d = Math.floor(u / 86400), h = Math.floor(u % 86400 / 3600), m = Math.floor(u % 3600 / 60);
    $("upt").textContent = (d ? d + " ngày " : "") + `${h} giờ ${m} phút`;
    $("ramtx").textContent = `RAM ${L.ram_used} / ${L.ram_total} GB`;
  } catch (e) { /* bỏ qua */ } finally { liveBusy = false; }
}
setInterval(live, 1500);
let infoShown = null;

/* ---------------------------------------------------------------- Khởi động đặc biệt */
let BOOT = null;
async function loadBoot() {
  BOOT = await api("boot_status");
  const b = BOOT;
  $("bootst").innerHTML = `${pill(b.fw, b.fw === "UEFI" ? "t-done" : "t-skip")}${b.safe_now ? pill("Đang ở Safe Mode", "t-err") : ""}${b.safe_set ? pill("Lần sau vào Safe Mode", "t-err") : ""}`;
  document.querySelector('[data-b="normal"]').classList.toggle("hot", !!(b.safe_set || b.safe_now));
}
async function bootGo(kind, arg, title, text, okText) {
  if (!(await confirmBox(title, text, okText || "⏻ Khởi động lại ngay"))) return;
  const m = await api("boot_action", kind, arg || "");
  if (m) dialog({title, body: `<div class="msg">${esc(m)}</div>`, buttons: [{text: "OK", cls: "red", def: true}]});
  else if (kind === "normal") { toast("Đã tắt Safe Mode: lần khởi động sau sẽ vào Windows bình thường"); loadBoot(); }
  else toast("Đang khởi động lại...");
}
document.querySelector(".bootgrid").onclick = async e => {
  const b = e.target.closest("[data-b]"); if (!b) return;
  const k = b.dataset.b;
  if (k === "bios") return bootGo("bios", "", "Vào BIOS / UEFI", "Máy sẽ khởi động lại ngay và vào thẳng màn hình BIOS / UEFI.\nLưu hết công việc đang mở trước khi tiếp tục.");
  if (k === "recovery") return bootGo("recovery", "", "Menu Recovery nâng cao", "Máy sẽ khởi động lại vào menu khôi phục của Windows (Troubleshoot → Startup Repair, System Restore, Startup Settings...).");
  if (k === "normal") return bootGo("normal", "", "Thoát Safe Mode", "Bỏ chế độ Safe Mode để lần khởi động sau vào Windows bình thường?\n(Không khởi động lại ngay — bạn tự khởi động lại khi sẵn sàng.)", "✓ Thoát Safe Mode");
  if (k === "safe") {
    const mode = await dialog({title: "Vào Safe Mode", width: 560, body: `<div class="msg">Chọn kiểu Safe Mode. Máy sẽ khởi động lại ngay, và <b>sẽ vào Safe Mode mỗi lần khởi động</b> cho tới khi bạn bấm "Thoát Safe Mode" (nút này cũng có trong Win AIO khi đang ở Safe Mode).</div>
      <div class="ofrow" style="margin-top:12px;flex-direction:column">
        <label class="ofr on"><input type="radio" name="sm" value="minimal" checked> 🛡️ <b>Tối giản</b> — chỉ driver cơ bản (dùng để gỡ phần mềm / driver lỗi, diệt virus)</label>
        <label class="ofr"><input type="radio" name="sm" value="network"> 🌐 <b>Có mạng</b> — như trên, thêm Internet / mạng LAN</label>
        <label class="ofr"><input type="radio" name="sm" value="cmd"> ⌨️ <b>Command Prompt</b> — chỉ cửa sổ dòng lệnh, không có màn hình Windows</label></div>`,
      buttons: [{text: "Hủy", value: false}, {text: "⏻ Khởi động lại vào Safe Mode", cls: "red", def: true, click: c => c.el.querySelector('input[name="sm"]:checked').value}],
      onOpen: c => c.el.addEventListener("change", e => { if (e.target.name === "sm") c.el.querySelectorAll(".ofr").forEach(l => l.classList.toggle("on", l.contains(e.target))); })});
    if (!mode) return;
    const m = await api("boot_action", "safe", mode);
    return m ? dialog({title: "Vào Safe Mode", body: `<div class="msg">${esc(m)}</div>`, buttons: [{text: "OK", cls: "red", def: true}]}) : toast("Đang khởi động lại vào Safe Mode...");
  }
  if (k === "once") {
    if (!BOOT) await loadBoot();
    if (BOOT.fw !== "UEFI") return dialog({title: "Chọn ổ khởi động", body: `<div class="msg">Máy đang khởi động kiểu Legacy BIOS nên Windows không chọn ổ khởi động hộ được.\nKhởi động lại rồi bấm phím Boot Menu của hãng (thường là F12, F11, F8, Esc).</div>`, buttons: [{text: "OK", cls: "red", def: true}]});
    const E = BOOT.entries || [];
    if (!E.length) return dialog({title: "Chọn ổ khởi động", body: `<div class="msg">Không đọc được danh sách ổ khởi động từ UEFI.</div>`, buttons: [{text: "OK", cls: "red", def: true}]});
    const id = await dialog({title: "Chọn ổ khởi động (1 lần)", width: 600, body: `<div class="msg">Chọn ổ / USB để khởi động <b>một lần</b>. Lần khởi động sau đó máy trở lại thứ tự cũ.</div>
      <div class="ofrow" style="margin-top:12px;flex-direction:column">${E.map((x, i) => `<label class="ofr${i ? "" : " on"}"><input type="radio" name="be" value="${esc(x.id)}"${i ? "" : " checked"}>
        ${/usb|sandisk|kingston|flash/i.test(x.name) ? "🔌" : /windows/i.test(x.name) ? "🪟" : /pxe|network|ipv|lan/i.test(x.name) ? "🌐" : "💽"} ${esc(x.name)}</label>`).join("")}</div>
      <div class="logl">Cắm USB trước rồi mới mở danh sách này. USB boot cần là loại UEFI.</div>`,
      buttons: [{text: "Hủy", value: false}, {text: "⏻ Khởi động lại vào ổ này", cls: "red", def: true, click: c => c.el.querySelector('input[name="be"]:checked').value}],
      onOpen: c => c.el.addEventListener("change", e => { if (e.target.name === "be") c.el.querySelectorAll(".ofr").forEach(l => l.classList.toggle("on", l.contains(e.target))); })});
    if (!id) return;
    const m = await api("boot_action", "once", id);
    return m ? dialog({title: "Chọn ổ khởi động", body: `<div class="msg">${esc(m)}</div>`, buttons: [{text: "OK", cls: "red", def: true}]}) : toast("Đang khởi động lại...");
  }
};

/* ---------------------------------------------------------------- Tiện ích */
const TOOL_SEC = {
  "THIẾT LẬP WINDOWS": ["🛠️", "#2f7fa3", "Tinh chỉnh nhanh sau khi cài Win"],
  "SAO LƯU - KHÔI PHỤC": ["💾", "#0d9488", "Wifi, Driver, điểm khôi phục hệ thống"],
  "DỌN DẸP": ["🧹", "#65a30d", "Giải phóng dung lượng ổ C"],
  "MICROSOFT DEFENDER": ["🛡️", "#16a34a", "Bật / tắt bảo vệ thời gian thực"],
  "WINDOWS UPDATE": ["🔄", "#0f8fd8", "Tắt / bật cập nhật tự động"],
  "MÁY IN": ["🖨️", "#7c3aed", "Sửa lỗi kẹt lệnh in, lỗi Spooler"],
  "BITLOCKER": ["🔐", "#d97706", "Kiểm tra và tắt mã hóa ổ đĩa"],
  "MẠNG": ["🌐", "#0891b2", "DNS, Wifi đã lưu, sửa lỗi mạng"],
  "BẢN QUYỀN (KEY CỦA BẠN)": ["🔑", "#e0262a", "Kiểm tra / nhập key Windows hợp lệ"],
};
function renderTools() {
  const el = $("tools"), wrap = el.parentElement, w = el.clientWidth || 1100;
  const groups = [];
  INIT.tools.filter(t => t.group !== "MICROSOFT DEFENDER").forEach(t => { let g = groups.find(x => x.name === t.group); if (!g) groups.push(g = {name: t.group, items: []}); g.items.push(t); });
  const cards = groups.map(g => {
    const [ic, color, sub] = TOOL_SEC[g.name] || ["🧰", "#6b7280", ""];
    const btns = g.items.map((t, i) => {
      const m = t.label.match(/^(\S+)\s+(.*)$/), icon = m ? m[1] : "▫", text = m ? m[2] : t.label;
      const wide = g.items.length % 2 === 1 && i === g.items.length - 1;
      return `<button class="tbtn${wide ? " wide" : ""}" data-t="${t.id}" title="${esc(text)}"><span class="ti">${esc(icon)}</span><span class="tt">${esc(text)}</span></button>`;
    }).join("");
    return {h: 1.6 + Math.ceil(g.items.length / 2), html: `<div class="tcard" style="--ac:${color}"><div class="sh"><span class="si">${ic}</span><div><b>${esc(g.name)}</b><small>${esc(sub)}</small></div></div>
      <div class="tgrid">${btns}</div></div>`};
  });
  // chia các nhóm vào n cột cho đều chiều cao; thêm cột cho tới khi vừa màn hình, vẫn chưa vừa thì thu nhỏ
  const put = n => {
    const cols = Array.from({length: n}, () => ({h: 0, html: []}));
    cards.forEach(x => { const c = cols.reduce((a, b) => b.h < a.h ? b : a); c.h += x.h; c.html.push(x.html); });
    el.style.setProperty("--tcols", n);
    el.innerHTML = cols.map(c => `<div class="tcol">${c.html.join("")}</div>`).join("");
  };
  el.style.zoom = "";
  bestFit(el, put, Math.max(1, Math.floor(w / 480)), Math.max(1, Math.floor(w / 250)), w, 290, .72, 1.4);
  $("quick").innerHTML = INIT.quick.map((q, i) => { const m = q.label.match(/^(\S+)\s+(.+)$/), emo = m && !/[0-9A-Za-zÀ-ỹ]/.test(m[1]);
    return `<button class="btn" data-q="${i}">${emo ? `<span class="qi">${m[1]}</span>${esc(m[2])}` : esc(q.label)}</button>`; }).join("");
}
let toolT;
window.addEventListener("resize", () => { clearTimeout(toolT); toolT = setTimeout(() => { if (page === "manage" && MT === "tools") renderTools(); }, 150); });
$("quick").onclick = e => { const b = e.target.closest("[data-q]"); if (b) api("quick", INIT.quick[+b.dataset.q].target); };
$("tools").onclick = async e => {
  const b = e.target.closest("[data-t]"); if (!b) return;
  const t = INIT.tools.find(x => x.id === b.dataset.t);
  if (t.confirm && !(await confirmBox(t.label, t.confirm))) return;
  let extra = null;
  if (t.fn === "wifi_restore" || t.fn === "driver_restore") {
    extra = await api("pick_folder");
    if (!extra && !window.pywebview) extra = await promptBox(t.label, "Đường dẫn thư mục sao lưu:", "Data\\Backup\\");
    if (!extra) return;
  }
  if (t.fn === "win_key") {
    extra = await promptBox("Nhập key Windows", "Key bản quyền của bạn (XXXXX-XXXXX-XXXXX-XXXXX-XXXXX):", "");
    if (!extra) return;
  }
  b.disabled = true; const old = b.innerHTML; b.innerHTML = '<span class="spin"></span> ' + esc(t.label);
  try {
    const r = await api("run_tool", t.id, extra);
    if (r.out && (t.kind === "cmd" || t.kind === "fn" || r.out.length > 60)) dialog({title: (r.ok ? "✔ " : "✖ ") + t.label, width: 720,
      body: `<div class="outbox">${esc(r.out)}</div>`, buttons: [{text: "⧉ Copy", click: () => { copyLocal(r.out); toast("Đã copy"); return false; }}, {text: "OK", cls: "red", def: true}]});
    else toast((r.ok ? "✔ " : "✖ ") + t.label + (r.out ? ": " + r.out : ""), r.ok ? "" : "err");
  } finally { b.disabled = false; b.innerHTML = old; }
};

/* ---------------------------------------------------------------- Nhật ký */
async function loadHistory() { HIST = await api("history"); renderHistory(); }
function renderHistory() {
  const q = norm($("hq").value), sh = $("hShow").value, today = new Date().toLocaleDateString("en-GB");
  const list = HIST.filter(h => (!q || norm(h.name + " " + h.src + " " + h.detail).includes(q)) &&
    (sh === "Tất cả" || (sh === "Xong" && /Xong|mở trang/.test(h.status)) || (sh === "Lỗi" && h.status === "Lỗi") || (sh === "Hôm nay" && h.ts.startsWith(today))));
  $("hRows").innerHTML = list.map(h => `<tr data-i="${h.id}"><td>${esc(h.ts)}</td><td><b>${esc(h.name)}</b></td><td>${esc(h.src)}</td>
    <td><span class="pill ${h.status === "Lỗi" ? "t-err" : h.status === "Đã dừng" ? "t-skip" : "t-done"}">${esc(h.status)}</span></td><td>${esc((h.detail || "").split("\n")[0])}</td></tr>`).join("")
    || `<tr><td colspan="5" class="empty">Chưa có gì.</td></tr>`;
  $("hCount").textContent = `${list.length} / ${HIST.length} dòng`;
}
$("hq").oninput = renderHistory; $("hShow").onchange = renderHistory; $("hRef").onclick = loadHistory;
$("hClear").onclick = async () => { if (await confirmBox("Xóa nhật ký", "Xóa toàn bộ nhật ký?")) { await api("clear_history"); loadHistory(); } };
$("hRows").ondblclick = e => { const tr = e.target.closest("tr[data-i]"); if (!tr) return; const h = HIST.find(x => x.id === +tr.dataset.i);
  dialog({title: h.name, width: 720, body: `<div class="msg">${esc(h.ts)} · ${esc(h.status)}\n${esc(h.src)}</div><div class="outbox" style="margin-top:8px">${esc(h.detail || "(không có chi tiết)")}</div>`,
    buttons: [{text: "OK", cls: "red", def: true}]}); };

/* ---------------------------------------------------------------- Cài đặt (Admin) */
async function renderSettings() {
  const s = await api("settings");
  $("sets").innerHTML = `
    <div class="sec"><h4>TẢI VỀ</h4>
      <div class="fr"><label>Thư mục lưu file cài đặt</label><input id="sDir" value="${esc(s.download_dir)}"><button class="btn sm" id="sDirPick">📂 Chọn</button><button class="btn sm" id="sDirOpen">▸ Mở</button></div>
      <div class="hint">Đường dẫn tương đối tính theo thư mục tool (hiện tại: ${esc(s.dl_path)}).</div>
      <label class="ck"><input type="checkbox" id="sKeep" ${s.keep_installer ? "checked" : ""}> Giữ lại file cài đặt sau khi cài (lần sau cài lại không phải tải)</label>
      <label class="ck"><input type="checkbox" id="sWg" ${s.winget_auto ? "checked" : ""}> Mở tool tự kiểm tra winget, bản cũ thì tự cài bản mới (chạy ngầm)
        <span style="color:var(--muted)">· trên máy: ${esc(s.winget.cur || "chưa có")}${s.winget.latest ? " · mới nhất: " + esc(s.winget.latest) : ""}</span></label>
      <div class="row-acts"><button class="btn green" id="sSave">✓ Lưu cài đặt</button></div></div>
    <div class="sec"><h4>DANH SÁCH NÚT PHẦN MỀM</h4><div class="d">Dữ liệu nằm trong ${esc(s.data_dir)}\\winaio.db. Xuất ra file JSON để chép sang máy khác / USB khác.</div>
      <div class="row-acts" style="margin-top:4px"><button class="btn" id="dExp">⇩ Xuất ra file JSON</button>
        <button class="btn" id="dImp">⇧ Nhập từ file JSON</button><button class="btn out" id="dReset">↺ Khôi phục danh sách mặc định</button></div>
      <div class="hint" style="margin-left:0;margin-top:8px">Mẹo: chép file JSON vào Data\\apps.json rồi mở tool, tool sẽ tự nhập (bản cũ được giữ trong Data\\Backup).</div></div>`;
  $("sDirPick").onclick = async () => { const p = await api("pick_folder"); if (p) $("sDir").value = p; };
  $("sDirOpen").onclick = () => api("open_path", $("sDir").value);
  $("sSave").onclick = async () => { await api("save_settings", {download_dir: $("sDir").value.trim(), keep_installer: $("sKeep").checked, winget_auto: $("sWg").checked}); toast("Đã lưu cài đặt"); renderSettings(); };
  $("dExp").onclick = async () => toast("Đã xuất: " + await api("export_data"));
  $("dImp").onclick = async () => {
    let p = await api("pick_file");
    if (!p && !window.pywebview) p = await promptBox("Nhập danh sách", "Đường dẫn file JSON:", "");
    if (!p) return;
    if (!(await confirmBox("Nhập danh sách", "Thay toàn bộ nút hiện tại bằng nội dung file này?\n(Danh sách hiện tại được tự sao lưu vào Data\\Backup)"))) return;
    const m = await api("import_file", p); if (m) toast(m, "err"); else { toast("Đã nhập danh sách"); loadGroups(); }
  };
  $("dReset").onclick = async () => { if (await confirmBox("Khôi phục mặc định", "Thay toàn bộ nút bằng danh sách mặc định?\n(Danh sách hiện tại được tự sao lưu vào Data\\Backup)")) { await api("reset_defaults"); loadGroups(); toast("Đã khôi phục"); } };
}


/* ---------------------------------------------------------------- Nguồn & Ổ USB */
$("pwOff").onclick = () => api("pw_shutdown");                 // khẩn cấp: không hỏi lại
$("pwLock").onclick = () => api("pw_lock");
$("pwSwitch").onclick = () => api("pw_switch");
let pwMode = "after";
$("pwSeg").onclick = e => { const d = e.target.closest("[data-m]"); if (!d) return; pwMode = d.dataset.m;
  $("pwSeg").querySelectorAll("div").forEach(x => x.classList.toggle("on", x === d));
  $("pwAfter").hidden = pwMode !== "after"; $("pwAt").hidden = pwMode !== "at"; };
$("pwChips").onclick = e => { const c = e.target.closest("[data-v]"); if (c) $("pwMin").value = c.dataset.v; };
$("pwMin").onwheel = e => { e.preventDefault(); $("pwMin").value = Math.max(1, (+$("pwMin").value || 0) + (e.deltaY < 0 ? 5 : -5)); };
$("pwSet").onclick = async () => {
  const [hh, mm] = ($("pwTime").value || "23:00").split(":");
  const m = await api("pw_schedule", pwMode, +$("pwMin").value || 0, +hh, +mm);
  if (m) toast(m, "err"); else toast("Đã hẹn giờ tắt máy (force)");
};
$("pwCancel").onclick = async () => toast(await api("pw_cancel"));
function countdown() {
  const at = ST.shutdown_at || 0, off = (ST.now || Date.now() / 1000) - Date.now() / 1000;
  const left = at ? Math.max(0, Math.round(at - (Date.now() / 1000 + off))) : 0;
  const box = $("pwCd").parentElement;
  box.classList.toggle("on", !!left);
  if (!left) { $("pwCd").textContent = "--:--:--"; $("pwCdText").textContent = "Chưa hẹn giờ"; $("bd-power").hidden = true; return; }
  const h = Math.floor(left / 3600), mi = Math.floor(left % 3600 / 60), se = left % 60, p2 = n => String(n).padStart(2, "0");
  $("pwCd").textContent = `${p2(h)}:${p2(mi)}:${p2(se)}`;
  const d = new Date(at * 1000);
  $("pwCdText").textContent = `Đã hẹn ép tắt máy lúc ${p2(d.getHours())}:${p2(d.getMinutes())} ngày ${p2(d.getDate())}/${p2(d.getMonth() + 1)}`;
  $("bd-power").hidden = false; $("bd-power").textContent = h ? `${h}h${p2(mi)}` : `${mi}:${p2(se)}`;
}
setInterval(countdown, 1000);

let DK = [], dkBusy = false;
async function loadDisks(force) {
  if (dkBusy) return; dkBusy = true;
  try { const r = await api("disks", force === true); DK = r.disks || []; if (r.err) $("dkInfo").textContent = "Lỗi đọc ổ: " + r.err; renderDisks(!!r.err); }
  finally { dkBusy = false; }
}
function renderDisks(hasErr) {
  const showInt = $("dkInt").checked;
  const ext = DK.filter(d => d.external), ints = DK.filter(d => !d.external);
  const list = showInt ? DK : ext;
  if (!hasErr) $("dkInfo").textContent = `Phát hiện ${DK.length} ổ, đang hiện ${list.length}` + (!showInt && ints.length ? ` · ${ints.length} ổ trong (SATA/NVMe) đang ẩn` : "");
  $("dkList").innerHTML = list.map(d => {
    const lt = (d.letters || []).map(l => `<span class="lt">${esc(l.l)}:</span>${l.label ? " " + esc(l.label) : ""}`).join(" &nbsp;");
    const st = d.off ? "off" : "ok", sys = d.sys;
    return `<div class="dk${d.external ? "" : " int"}" data-n="${d.n}">${led(st, "big")}
      <div class="dkx"><div class="dkn">${esc(d.name)}</div>
        <div class="dkm"><span class="pill ${d.external ? "t-new" : "t-skip"}">${esc(d.bus_name)}</span><b>${esc(d.size_text)}</b>
          <span>Disk ${d.n}</span>${d.off ? '<span class="pill t-err">OFFLINE</span>' : ""}${d.ro ? '<span class="pill t-skip">chỉ đọc</span>' : ""}
          ${sys ? '<span class="pill t-err">ổ Windows</span>' : d.external ? "" : '<span>ổ trong</span>'}</div>
        <div class="dkm">${lt || (d.off ? "Đang Offline — rút ra cắm lại để dùng tiếp" : "Chưa có phân vùng / ký tự ổ")}</div></div>
      <div class="dka">${sys ? "" : `<button class="btn green" data-a="safe">⏏ Tháo an toàn<br><small style="font-weight:600;opacity:.85">kiểu Windows</small></button>
        <button class="btn out" data-a="force">⚡ Ép ngắt ổ<br><small style="font-weight:600;color:var(--muted)">Dismount + Offline rồi tháo</small></button>`}</div></div>`;
  }).join("") || `<div class="empty big">Không có ổ USB / ổ ngoài nào đang cắm\nCắm ổ vào — danh sách tự cập nhật</div>`;
}
$("dkInt").onchange = () => renderDisks();
$("dkRef").onclick = () => loadDisks(true);
$("dkList").onclick = async e => {
  const b = e.target.closest("[data-a]"); if (!b) return;
  const d = DK.find(x => x.n === +b.closest(".dk").dataset.n);
  const lt = (d.letters || []).map(l => l.l + ":").join(", ");
  if (b.dataset.a === "force" && !(await confirmBox("Ép ngắt ổ này?", `Ổ: ${d.name}${lt ? " (" + lt + ")" : ""}\n\nMọi chương trình đang mở tệp trên ổ sẽ mất thay đổi chưa lưu; tệp đang chép dở sẽ hỏng.`, "⚡ Ép ngắt"))) return;
  b.closest(".dka").querySelectorAll("button").forEach(x => x.disabled = true);
  b.innerHTML = '<span class="spin"></span> ' + (b.dataset.a === "safe" ? "Đang tháo ổ…" : "Đang ép ngắt ổ…");
  const r = await api(b.dataset.a === "safe" ? "disk_safe" : "disk_force", d.n);
  if (r.ok) toast(r.msg); else dialog({title: "Chưa tháo được ổ", body: `<div class="msg">${esc(r.msg)}</div>`, buttons: [{text: "OK", cls: "red", def: true}]});
  loadDisks();
};
setInterval(() => { if (page === "power" && !document.hidden) loadDisks(); }, 6000);

/* ---------------------------------------------------------------- Cập nhật */
async function checkUpd(silent) {
  const r = await api("check_update", !!silent);
  const b = $("bUpd");
  if (r.ok && r.has) { b.textContent = "⟳ Có bản " + r.latest; b.classList.add("hot2"); }
  if (silent) return;
  if (!r.ok) return alertBox("Cập nhật", r.msg);
  if (!r.has) return alertBox("Cập nhật", `Đang dùng bản mới nhất (${r.current}).`);
  const ok = await dialog({title: `Có bản mới ${r.latest}`, width: 620,
    body: `<div class="msg">Bản đang dùng: <b>${esc(r.current)}</b> → bản mới: <b>${esc(r.latest)}</b> (${(r.size / 1048576).toFixed(1)} MB)</div>
      ${r.notes ? `<div class="outbox" style="margin-top:10px;background:var(--head);color:var(--text)">${esc(r.notes)}</div>` : ""}
      <div class="logl">Tool sẽ tải bản mới, tự thay file exe rồi mở lại. Dữ liệu trong thư mục Data giữ nguyên.</div>`,
    buttons: [{text: "Để sau", value: false}, {text: "⬇ Cập nhật ngay", cls: "green", def: true, value: true}]});
  if (!ok) return;
  b.disabled = true; b.innerHTML = '<span class="spin"></span> Đang tải bản mới...';
  try { const m = await api("do_update"); if (m) { toast(m, "err"); } } finally { b.disabled = false; b.textContent = "⟳ Cập nhật"; }
}
$("bUpd").onclick = () => checkUpd(false);

/* ---------------------------------------------------------------- vòng cập nhật trạng thái */
function tiles() {
  const c = ST.checks || {}, run = ST.running, q = (ST.queue || []).length + (ST.cur ? 1 : 0);
  const w = ST.winget || {};
  const T = [   // [tên, đèn, chữ ngắn hiện trên đèn, giải thích đầy đủ khi rê chuột]
    ["Quyền Admin", c.admin ? "ok" : "err", c.admin ? "Có quyền" : "Thiếu quyền", c.admin ? "Đang chạy bằng quyền Administrator" : "Không có quyền Admin - một số chức năng sẽ lỗi"],
    ["Internet", c.net == null ? "run" : c.net ? "ok" : "err", c.net == null ? "Đang kiểm tra" : c.net ? "Đã kết nối" : "Mất mạng", c.net === false ? "Không vào được mạng" : ""],
    w.state === "updating" ? ["winget", "run", "Đang cập nhật", `Đang cài bản mới ${w.latest || ""}`]
      : w.state === "err" ? ["winget", "err", "Cập nhật lỗi", `Bản cũ ${w.cur || ""} - cập nhật lỗi`]
      : c.winget == null || w.state === "check" ? ["winget", "run", "Đang kiểm tra", ""]
      : !c.winget ? ["winget", "off", "Không có", "Không có winget - nút WINGET sẽ lỗi"]
      : ["winget", "ok", w.cur || "Có sẵn", w.state === "ok" ? "Đã là bản mới nhất" : ""],
    ["Hàng đợi", run ? "run" : "ok", run ? `${q} đang cài` : "Trống", run ? `${q} mục đang cài / chờ` : "Không có gì đang cài"],
    ["Hẹn tắt máy", ST.shutdown_at ? "run" : "off", ST.shutdown_at ? "Tắt " + new Date(ST.shutdown_at * 1000).toLocaleTimeString("vi-VN", {hour: "2-digit", minute: "2-digit"}) : "Chưa hẹn", ""],
    ["Chế độ Admin", ADMIN ? "run" : "off", ADMIN ? "Đang mở" : "Đã khóa", ADMIN ? "Đang mở - có thể sửa nút" : ""]];
  const html = T.map(([n, s, d, l]) => `<div class="raised tile" title="${esc(n + ": " + (l || d))}">${led(s)}<div class="tx"><b>${n}</b><small class="s-${s}">${esc(d)}</small></div></div>`).join("");
  if (html !== $("tiles").innerHTML) { $("tiles").innerHTML = html; fitSide(); }
}
function bar(id, pct, text) {
  $(id).style.width = (pct < 0 ? 100 : pct) + "%";
  $(id + "-p").textContent = pct < 0 ? "…" : pct + "%";
  $(id + "-i").textContent = text;
}
function addLogs(lines) {
  if (!lines.length) return;
  const html = lines.map(([, t, m, k]) => `<div style="${k === "err" ? "color:#ff8a8a" : k === "warn" ? "color:#ffd24a" : k === "dim" ? "opacity:.7;white-space:pre-wrap" : ""}">[${t}] ${esc(m)}</div>`).join("");
  for (const id of ["log", "log2", "log3"]) { const L = $(id); L.insertAdjacentHTML("beforeend", html); while (L.children.length > 400) L.firstChild.remove(); L.scrollTop = L.scrollHeight; }
}
let lastRes = "";
function progOnButton(cur, d, n) {                       // vệt tiến độ + số % ngay trên nút đang cài
  document.querySelectorAll(".abtn.prog").forEach(b => { if (!cur || b.closest(".arow").dataset.a != cur.id) { b.classList.remove("prog", "pdl", "pin"); b.style.removeProperty("--pp"); const x = b.querySelector(".ppct"); if (x) x.remove(); } });
  if (!cur) return;
  const b = document.querySelector(`.arow[data-a="${cur.id}"] .abtn`); if (!b) return;
  const downloading = d !== null && d < 100, v = downloading ? d : n;
  b.classList.add("prog"); b.classList.toggle("pdl", downloading); b.classList.toggle("pin", !downloading);
  b.style.setProperty("--pp", Math.max(0, v) + "%");
  let x = b.querySelector(".ppct"); if (!x) { x = document.createElement("span"); x.className = "ppct"; b.appendChild(x); }
  x.textContent = (downloading ? "⬇ " : "⚙ ") + Math.max(0, v) + "%";
}
let WGC = 0;
document.addEventListener("click", e => { if (e.target.id === "upgN") setTimeout(() => { const t = $("mtabs").querySelector('[data-t="upgrade"]'); if (t) t.click(); }, 60); });
function setUpgBadge(n) { for (const id of ["upgN", "upgB"]) { const b = $(id); if (b) { b.hidden = !n; b.textContent = n; } } }
let SIV = null, SYSI = null, hidTick = 0;
let tickBusy = false;
async function tick() {
  if (tickBusy) return;                                            // v5.11: lần hỏi trước chưa xong thì bỏ qua, không dồn lệnh
  tickBusy = true;
  try {
    if (document.hidden && ++hidTick % 4) return;                 // cửa sổ ẩn / thu nhỏ: hỏi chậm lại
    ST = await api("state", logSeq, SIV);
    if (ST.si !== SIV) { SIV = ST.si; SYSI = ST.sysinfo; }
    ST.sysinfo = SYSI;
    if (ST.logs.length) { logSeq = ST.logs[ST.logs.length - 1][0]; addLogs(ST.logs); }
    if (ST.admin !== ADMIN) setAdmin(ST.admin);
    if (ST.wg_checked && ST.wg_checked !== WGC) { WGC = ST.wg_checked; loadGroups(); }
    if (ST.upg_n !== null && ST.upg_n !== undefined) setUpgBadge(ST.upg_n);   // vừa kiểm tra xong các nút winget
    const cur = ST.cur, [bi, bn] = ST.batch, run = ST.running;
    let frac = 0;
    if (cur) {
      const mb = x => (x / 1048576).toFixed(1);
      if (cur.dl === null || cur.dl === undefined) bar("e-dl", 0, `${cur.name} · không cần tải (winget / file trên máy / lệnh)`);
      else bar("e-dl", cur.dl, `${cur.name} · ${cur.total ? `${mb(cur.done)} / ${mb(cur.total)} MB` : cur.phase}${cur.speed ? " · " + cur.speed : ""}${cur.dl >= 100 ? " · đã tải xong" : ""}`);
      if (cur.inst === null || cur.inst === undefined) bar("e-in", 0, cur.dl !== null && cur.dl !== undefined && cur.dl < 100 ? "Chờ tải xong..." : `${cur.name} · ${cur.phase}`);
      else bar("e-in", cur.inst, `${cur.name} · ${cur.phase}${cur.est && cur.inst < 100 ? " (ước tính)" : ""}${cur.secs ? " · " + cur.secs + " giây" : ""}`);
      const d = cur.dl === null || cur.dl === undefined ? null : Math.max(0, cur.dl), n = Math.max(0, cur.inst || 0);
      frac = d === null ? n / 100 : (d * 0.5 + n * 0.5) / 100;
      progOnButton(cur, d, n);
    } else { bar("e-dl", 0, "—"); bar("e-in", 0, "—"); progOnButton(null); }
    bar("e-all", bn ? Math.min(100, Math.round(((bi - (cur ? 1 : 0) + frac) / bn) * 100)) : 0, run ? `Mục ${bi} / ${bn}` : (bn ? `Xong ${bn} mục` : "—"));
    const q = (ST.queue || []).length + (cur ? 1 : 0);
    $("s-run").textContent = q; $("s-done").textContent = ST.done_today;
    $("bStop").disabled = !run;
    $("bd-apps").hidden = !q; $("bd-apps").textContent = q;
    const a = $("alert"), al = $("aled");
    if (run) { $("a1").textContent = `Đang cài ${bi}/${bn}`; $("a2").textContent = cur ? `${cur.name} · ${cur.phase}` : ""; al.className = "led big run"; }
    else if (ST.busy_tool) { $("a1").textContent = "Đang chạy tiện ích"; $("a2").textContent = ST.busy_tool; al.className = "led big run"; }
    else if (!ST.checks.admin) { $("a1").textContent = "Thiếu quyền Admin"; $("a2").textContent = "Chạy lại tool bằng Run as administrator"; al.className = "led big err"; }
    else { $("a1").textContent = "Sẵn sàng"; $("a2").textContent = ADMIN ? "Admin đang mở" : "Chọn phần mềm để cài"; al.className = "led big ok"; }
    a.classList.toggle("bad", al.classList.contains("err"));
    $("status").textContent = run ? `Đang cài: ${cur ? cur.name : ""}` : (ST.busy_tool ? "Đang chạy: " + ST.busy_tool : "Sẵn sàng.");
    $("fb").style.width = run && bn ? Math.round((bi / bn) * 100) + "%" : "0";
    const rs = JSON.stringify(ST.results);
    if (rs !== lastRes) { lastRes = rs; renderGroups(); }
    if (ST.sysinfo !== infoShown) { infoShown = ST.sysinfo; renderInfo(); }
    if (ST.full !== lastFull) { if (lastFull !== undefined) loadGroups(); lastFull = ST.full; }   // v5.8: mở đầy đủ -> hiện nhóm bị ẩn
    tiles();
  } catch (e) { /* bỏ qua 1 nhịp */ } finally { tickBusy = false; }
}

async function start() {
  if (window.__started) return; window.__started = true;
  INIT = await api("init");
  applySkin();
  $("ver").textContent = "by Duy Anh · " + INIT.version;
  $("verfoot").textContent = INIT.title + " " + INIT.version;
  renderTools();
  initTests();
  if (INIT.browser) $("ptitle").parentElement.insertAdjacentHTML("beforeend", '<div class="browserbar">Đang chạy bằng trình duyệt (máy chưa có Edge WebView2). Đóng tab này là tool tự thoát.</div>');
  await loadGroups();
  showPage("system");
  tick(); setInterval(tick, 700);
}

/* ---------------------------------------------------------------- v5.7: đăng nhập khi mở tool + tự cập nhật */
let INIT_VER = "";
async function boot() {
  if (window.__booted) return; window.__booted = true;
  let info = {};
  try { info = await api("login_info"); } catch (e) { /* bỏ qua */ }
  if (info.version) { $("lgVer").textContent = info.version; INIT_VER = info.version; }
  if (info.logged) return afterLogin(false);
  const L = $("login"); L.hidden = false;
  setTimeout(() => $("lgPw").focus(), 50);
}
async function doLogin(pw) {
  const btn = $("lgGo"); btn.disabled = true; $("lgErr").textContent = "";
  let r = {ok: false};
  try { r = await api("login", pw); } catch (e) { r = {ok: false}; }
  btn.disabled = false;
  if (!r.ok) { $("lgErr").textContent = "Mật khẩu không đúng"; $("lgPw").select(); $("lgBox").classList.remove("shake"); void $("lgBox").offsetWidth; $("lgBox").classList.add("shake"); return false; }
  $("lgPw").value = "";
  if (r.auto_update === false) $("login").hidden = true;
  afterLogin(r.auto_update !== false);
  return true;
}
window.__doLogin = doLogin;
window.__selftestStart = () => { $("login").hidden = true; afterLogin(false); };   // chỉ dùng khi build trên GitHub
async function afterLogin(autoUpd) {
  if (autoUpd && !(await forceUpdate())) return;     // v5.9: bắt buộc bản mới nhất mới vào được tool
  await start();
}
/* v5.9: sau khi đăng nhập luôn kiểm tra bản mới; có bản mới thì bắt buộc cập nhật xong (tool tự mở lại) mới vào được */
async function forceUpdate() {
  const L = $("login"), box = $("lgBox"); L.hidden = false;
  const show = html => { box.innerHTML = `<div class="lglogo">W</div><h2>WIN AIO</h2><div class="lgsub">by Duy Anh · ${esc(INIT_VER)}</div>${html}`; };
  show('<div class="lgst"><span class="spin"></span> Đang kiểm tra bản mới...</div>');
  let r = {};
  try { r = await api("check_update", true); } catch (e) { r = {ok: false, msg: String(e)}; }
  if (r.ok && !r.has) { L.hidden = true; return true; }
  if (!r.ok) {
    show(`<div class="lgst bad">Không kiểm tra được bản mới.<br><small>Tool cần kết nối mạng để kiểm tra phiên bản trước khi dùng.</small></div>
      <button class="btn red shine" id="lgRetry" type="button">⟳ Thử lại</button>`);
    return new Promise(res => { $("lgRetry").onclick = async () => res(await forceUpdate()); });
  }
  show(`<div class="lgst">Có bản mới <b>${esc(r.latest)}</b> (đang dùng ${esc(r.current)}).<br><span class="spin"></span> Đang tải và cập nhật${r.size ? " " + (r.size / 1048576).toFixed(1) + " MB" : ""}...<br>
      <small>Cập nhật xong tool tự mở lại - bản cũ không dùng được nữa.</small></div>`);
  let m = "";
  try { m = await api("do_update"); } catch (e) { m = String(e); }
  if (m) {
    show(`<div class="lgst bad">Cập nhật chưa được: ${esc(m)}</div><button class="btn red shine" id="lgRetry" type="button">⟳ Thử lại</button>`);
    return new Promise(res => { $("lgRetry").onclick = async () => res(await forceUpdate()); });
  }
  return new Promise(() => {});                      // đang thay file exe, tool sẽ tự đóng và mở lại
}
$("lgForm").onsubmit = e => { e.preventDefault(); doLogin($("lgPw").value); };
window.addEventListener("pywebviewready", boot);
if (location.protocol.startsWith("http")) boot();
else setTimeout(() => { if (window.pywebview && window.pywebview.api) boot(); }, 1500);
