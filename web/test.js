/* Win AIO by Duy Anh - tab TEST MÁY (màn hình, cảm ứng, bàn phím, loa, mic, trackpad, webcam, pin) */
const TESTS = [
  {id: "screen", ic: "🖥️", c: "#e0262a", t: "Màn hình - dải màu", d: "Toàn màn hình từng màu: tìm điểm chết, hở sáng, ám màu, sọc."},
  {id: "touch", ic: "👆", c: "#d97706", t: "Màn hình cảm ứng", d: "Chạm / kéo khắp màn hình, các ô chuyển xanh. Đếm số ngón chạm cùng lúc."},
  {id: "kb", ic: "⌨️", c: "#2f7fa3", t: "Bàn phím", d: "Bấm lần lượt các phím, phím nào nhận sẽ sáng xanh."},
  {id: "spk", ic: "🔊", c: "#7c3aed", t: "Loa", d: "Phát tiếng loa trái, loa phải, quét tần số để nghe rè."},
  {id: "mic", ic: "🎤", c: "#16a34a", t: "Micro", d: "Cột âm lượng theo giọng nói, ghi âm 5 giây rồi nghe lại."},
  {id: "pad", ic: "🖱️", c: "#0d9488", t: "Trackpad / chuột", d: "Di chuyển, click trái / phải, cuộn 2 ngón, phóng to thu nhỏ."},
  {id: "cam", ic: "📷", c: "#0f8fd8", t: "Webcam", d: "Xem hình camera, độ phân giải, chụp thử."},
  {id: "bat", ic: "🔋", c: "#65a30d", t: "Pin laptop", d: "Dung lượng thiết kế, dung lượng còn lại, độ chai, số lần sạc."},
];
const TRES = {};                       // kết quả: id -> "ok" | "err"
let BAT = null;

function initTests() {
  $("tests").innerHTML = TESTS.map(x => `<div class="tst" data-id="${x.id}" style="--ac:${x.c}">
      <div class="sh"><span class="si">${x.ic}</span><div><b>${esc(x.t)}</b><small>${esc(x.d)}</small></div><span class="tres" id="tr-${x.id}"></span></div>
      <div class="tbody" id="tb-${x.id}">${x.id === "bat" ? '<div class="logl"><span class="spin"></span> Đang đọc pin...</div>' : ""}</div>
      <div class="tacts">${x.id === "bat" ? `<button class="btn sm" data-a="batref">⟳ Đọc lại</button><button class="btn sm" data-a="batrep">📄 Báo cáo pin chi tiết</button>`
        : `<button class="btn red shine" data-a="run">▶ Bắt đầu test</button>`}
        <span class="sp"></span><button class="btn sm ok" data-a="pass">✓ Đạt</button><button class="btn sm bad" data-a="fail">✗ Lỗi</button></div></div>`).join("");
  $("tests").onclick = e => {
    const b = e.target.closest("[data-a]"); if (!b) return;
    const id = b.closest(".tst").dataset.id, a = b.dataset.a;
    if (a === "run") ({screen: tScreen, touch: tTouch, kb: tKb, spk: tSpk, mic: tMic, pad: tPad, cam: tCam})[id]();
    else if (a === "pass" || a === "fail") setRes(id, a === "pass" ? "ok" : "err");
    else if (a === "batref") loadBattery(true);
    else if (a === "batrep") api("battery_report").then(m => m ? toast(m, "err") : toast("Đã mở báo cáo pin của Windows"));
  };
  renderSum();
}
function setRes(id, r) {
  TRES[id] = TRES[id] === r ? undefined : r;
  const el = $("tr-" + id);
  el.className = "tres " + (TRES[id] || ""); el.textContent = TRES[id] === "ok" ? "ĐẠT" : TRES[id] === "err" ? "LỖI" : "";
  document.querySelector(`.tst[data-id="${id}"]`).classList.toggle("done", !!TRES[id]);
  renderSum();
}
function renderSum() {
  const n = TESTS.filter(x => TRES[x.id]).length, bad = TESTS.filter(x => TRES[x.id] === "err").length;
  const pc = ST.sysinfo && ST.sysinfo.pc ? ST.sysinfo.pc : {};
  $("tsum").innerHTML = `<div class="sl"><b>PHIẾU KIỂM TRA MÁY</b><span>${esc(pc.name || "")}${pc.model ? " · " + esc((pc.maker || "") + " " + pc.model) : ""}</span></div>
    <div class="sp">${TESTS.map(x => `<span class="sdot ${TRES[x.id] || ""}" title="${esc(x.t)}">${x.ic}</span>`).join("")}</div>
    <div class="sn"><b>${n}/${TESTS.length}</b> đã test${bad ? ` · <em>${bad} lỗi</em>` : ""}</div>
    <button class="btn sm" id="tCopy">⧉ Copy phiếu</button><button class="btn sm" id="tReset">↺ Làm lại</button>`;
  $("tCopy").onclick = () => {
    const lines = [`PHIẾU KIỂM TRA MÁY - ${new Date().toLocaleString("vi-VN")}`, `Máy: ${pc.name || ""} · ${(pc.maker || "") + " " + (pc.model || "")} · Service Tag ${pc.tag || "-"}`, ""];
    TESTS.forEach(x => lines.push(`${TRES[x.id] === "ok" ? "[ĐẠT]" : TRES[x.id] === "err" ? "[LỖI]" : "[ -- ]"} ${x.t}`));
    if (BAT && BAT.batteries && BAT.batteries[0]) { const b = BAT.batteries[0]; lines.push("", `Pin: còn ${b.health ?? "?"}% so với lúc mới (${b.full} / ${b.design} mWh), ${b.cycles ?? "?"} lần sạc`); }
    copyLocal(lines.join("\n")); toast("Đã copy phiếu kiểm tra");
  };
  $("tReset").onclick = () => { TESTS.forEach(x => { if (TRES[x.id]) setRes(x.id, TRES[x.id]); }); };
}

/* ---------------- khung xem toàn cửa sổ dùng chung ---------------- */
let tvClose = null;
function openView(id, title, html, hint, opts = {}) {
  const v = $("tview");
  v.className = "tview" + (opts.bare ? " bare" : "");
  v.innerHTML = `${opts.bare ? "" : `<div class="tvh"><b>${esc(title)}</b><span class="tvhint">${hint || ""}</span>
      <button class="btn sm ok" data-v="pass">✓ Đạt</button><button class="btn sm bad" data-v="fail">✗ Lỗi</button><button class="btn sm" data-v="close">✕ Đóng (Esc)</button></div>`}
    <div class="tvb">${html}</div>`;
  v.hidden = false;
  const close = () => { if (tvClose) { const f = tvClose; tvClose = null; f(); } v.hidden = true; v.innerHTML = "";
    document.removeEventListener("keydown", esc_); if (document.fullscreenElement) document.exitFullscreen().catch(() => {}); };
  const esc_ = e => { if (e.key === "Escape" && !opts.keepEsc) { e.preventDefault(); close(); } };
  document.addEventListener("keydown", esc_);
  v.onclick = e => { const b = e.target.closest("[data-v]"); if (!b) return;
    if (b.dataset.v === "close") close(); else { const r = b.dataset.v === "pass" ? "ok" : "err"; if (TRES[id] !== r) setRes(id, r); close(); } };
  if (opts.full) v.requestFullscreen && v.requestFullscreen().catch(() => {});
  return close;
}
function judge(id, close) {                        // sau bài test toàn màn hình: hỏi Đạt / Lỗi
  dialog({title: TESTS.find(x => x.id === id).t, body: `<div class="msg">Kết quả bài test?</div>`,
    buttons: [{text: "Để sau", value: 0}, {text: "✗ Lỗi", cls: "out", value: "err"}, {text: "✓ Đạt", cls: "green", def: true, value: "ok"}]})
    .then(r => { if (r && TRES[id] !== r) setRes(id, r); });
}

/* ---------------- 1. màn hình: dải màu ---------------- */
const SCREENS = [
  ["#ff0000", "ĐỎ"], ["#00ff00", "XANH LÁ"], ["#0000ff", "XANH DƯƠNG"], ["#ffffff", "TRẮNG - tìm điểm chết tối"],
  ["#000000", "ĐEN - tìm điểm sáng, hở sáng viền"], ["#808080", "XÁM 50%"], ["#ffff00", "VÀNG"], ["#00ffff", "CYAN"], ["#ff00ff", "MAGENTA"],
  ["linear-gradient(90deg,#000,#fff)", "DẢI XÁM ĐEN → TRẮNG - xem có bị sọc / phân tầng"],
  ["linear-gradient(90deg,#f00,#ff0,#0f0,#0ff,#00f,#f0f,#f00)", "DẢI CẦU VỒNG"],
  ["linear-gradient(90deg,#000,#f00)", "DẢI ĐỎ"], ["linear-gradient(90deg,#000,#0f0)", "DẢI XANH LÁ"], ["linear-gradient(90deg,#000,#00f)", "DẢI XANH DƯƠNG"],
  ["repeating-conic-gradient(#000 0 25%,#fff 0 50%) 0 0/40px 40px", "BÀN CỜ - xem độ nét, nhòe chữ"],
];
function tScreen() {
  let i = 0;
  const close = openView("screen", "", `<div class="scr" id="scr"><div class="scrl" id="scrl"></div></div>`, "", {bare: true, full: true, keepEsc: true});
  const show = () => { $("scr").style.background = SCREENS[i][0];
    $("scrl").innerHTML = `${i + 1}/${SCREENS.length} · ${SCREENS[i][1]}<small>Bấm chuột / → / Space: màu tiếp · ←: lùi · Esc: thoát</small>`;
    $("scrl").classList.remove("fade"); void $("scrl").offsetWidth; $("scrl").classList.add("fade"); };
  const key = e => { if (["ArrowRight", " ", "Enter", "PageDown"].includes(e.key)) { e.preventDefault(); next(1); }
    else if (["ArrowLeft", "PageUp"].includes(e.key)) { e.preventDefault(); next(-1); } else if (e.key === "Escape") { e.preventDefault(); end(); } };
  const next = d => { i += d; if (i < 0) i = 0; if (i >= SCREENS.length) return end(); show(); };
  const end = () => { document.removeEventListener("keydown", key); close(); judge("screen"); };
  $("scr").onclick = () => next(1); $("scr").oncontextmenu = e => { e.preventDefault(); next(-1); };
  document.addEventListener("keydown", key);
  show();
}

/* ---------------- 2. cảm ứng ---------------- */
function tTouch() {
  const C = 10, R = 6;
  const close = openView("touch", "", `<div class="tch" id="tch">${Array.from({length: C * R}, (_, k) => `<i data-k="${k}"></i>`).join("")}
      <canvas id="tcv"></canvas><div class="tchl" id="tchl"></div></div>`, "", {bare: true, full: true, keepEsc: true});
  const box = $("tch"), cv = $("tcv"), g = cv.getContext("2d"), pts = new Map(), done = new Set();
  let maxTouch = 0;
  const fit = () => { cv.width = box.clientWidth; cv.height = box.clientHeight; };
  setTimeout(fit, 120); window.addEventListener("resize", fit);
  const info = () => { $("tchl").innerHTML = `Đã chạm ${done.size}/${C * R} ô · nhiều nhất <b>${maxTouch}</b> ngón cùng lúc
    <small>Chạm / kéo khắp màn hình · nhấp đúp hoặc Esc để thoát</small>`; };
  const mark = (x, y) => { const k = Math.min(R - 1, Math.floor(y / box.clientHeight * R)) * C + Math.min(C - 1, Math.floor(x / box.clientWidth * C));
    if (!done.has(k)) { done.add(k); box.querySelector(`i[data-k="${k}"]`).classList.add("on"); info(); } };
  box.onpointerdown = e => { pts.set(e.pointerId, [e.clientX, e.clientY]); maxTouch = Math.max(maxTouch, [...pts.keys()].length); mark(e.clientX, e.clientY); info(); };
  box.onpointermove = e => { if (!pts.has(e.pointerId) && e.pointerType !== "mouse") return; if (e.pointerType === "mouse" && !e.buttons) return;
    const p = pts.get(e.pointerId) || [e.clientX, e.clientY];
    g.strokeStyle = e.pointerType === "touch" ? "#ff3b3b" : "#2f7fa3"; g.lineWidth = 4; g.lineCap = "round";
    g.beginPath(); g.moveTo(p[0], p[1]); g.lineTo(e.clientX, e.clientY); g.stroke();
    pts.set(e.pointerId, [e.clientX, e.clientY]); mark(e.clientX, e.clientY); };
  box.onpointerup = box.onpointercancel = e => pts.delete(e.pointerId);
  const key = e => { if (e.key === "Escape") { e.preventDefault(); end(); } };
  const end = () => { document.removeEventListener("keydown", key); window.removeEventListener("resize", fit); close(); judge("touch"); };
  box.ondblclick = end; document.addEventListener("keydown", key);
  info();
}

/* ---------------- 3. bàn phím ---------------- */
const KB = [
  [["Escape", "Esc"], 0.5, ["F1"], ["F2"], ["F3"], ["F4"], 0.25, ["F5"], ["F6"], ["F7"], ["F8"], 0.25, ["F9"], ["F10"], ["F11"], ["F12"], 0.25, ["PrintScreen", "PrtSc"], ["Insert", "Ins"], ["Delete", "Del"]],
  [["Backquote", "`"], ["Digit1", "1"], ["Digit2", "2"], ["Digit3", "3"], ["Digit4", "4"], ["Digit5", "5"], ["Digit6", "6"], ["Digit7", "7"], ["Digit8", "8"], ["Digit9", "9"], ["Digit0", "0"], ["Minus", "-"], ["Equal", "="], ["Backspace", "⌫ Backspace", 2], 0.25, ["Home"], ["PageUp", "PgUp"]],
  [["Tab", "Tab", 1.5], ["KeyQ", "Q"], ["KeyW", "W"], ["KeyE", "E"], ["KeyR", "R"], ["KeyT", "T"], ["KeyY", "Y"], ["KeyU", "U"], ["KeyI", "I"], ["KeyO", "O"], ["KeyP", "P"], ["BracketLeft", "["], ["BracketRight", "]"], ["Backslash", "\\", 1.5], 0.25, ["End"], ["PageDown", "PgDn"]],
  [["CapsLock", "Caps", 1.75], ["KeyA", "A"], ["KeyS", "S"], ["KeyD", "D"], ["KeyF", "F"], ["KeyG", "G"], ["KeyH", "H"], ["KeyJ", "J"], ["KeyK", "K"], ["KeyL", "L"], ["Semicolon", ";"], ["Quote", "'"], ["Enter", "Enter ↵", 2.25]],
  [["ShiftLeft", "⇧ Shift", 2.25], ["KeyZ", "Z"], ["KeyX", "X"], ["KeyC", "C"], ["KeyV", "V"], ["KeyB", "B"], ["KeyN", "N"], ["KeyM", "M"], ["Comma", ","], ["Period", "."], ["Slash", "/"], ["ShiftRight", "⇧ Shift", 2.75], 1.25, ["ArrowUp", "▲"]],
  [["ControlLeft", "Ctrl", 1.25], ["MetaLeft", "⊞ Win", 1.25], ["AltLeft", "Alt", 1.25], ["Space", "Space", 6.25], ["AltRight", "Alt", 1.25], ["ContextMenu", "☰", 1.25], ["ControlRight", "Ctrl", 1.25], 0.25, ["ArrowLeft", "◀"], ["ArrowDown", "▼"], ["ArrowRight", "▶"]],
];
const NUMPAD = [[["NumLock", "Num"], ["NumpadDivide", "/"], ["NumpadMultiply", "*"], ["NumpadSubtract", "-"]],
  [["Numpad7", "7"], ["Numpad8", "8"], ["Numpad9", "9"], ["NumpadAdd", "+"]], [["Numpad4", "4"], ["Numpad5", "5"], ["Numpad6", "6"], 1],
  [["Numpad1", "1"], ["Numpad2", "2"], ["Numpad3", "3"], ["NumpadEnter", "↵"]], [["Numpad0", "0", 2], ["NumpadDecimal", "."], 1]];
function tKb() {
  const row = r => `<div class="kr">${r.map(k => typeof k === "number" ? `<span class="kgap" style="--w:${k}"></span>`
    : `<span class="key" data-c="${k[0]}" style="--w:${k[2] || 1}">${esc(k[1] || k[0])}</span>`).join("")}</div>`;
  const total = KB.flat().filter(k => typeof k !== "number").length;
  const close = openView("kb", "Test bàn phím", `<div class="kbwrap"><div class="kbd">${KB.map(row).join("")}</div>
      <div class="kbd np" id="np" hidden>${NUMPAD.map(row).join("")}</div></div>
    <div class="kbinfo"><span>Đã nhận <b id="kbn">0</b>/${total} phím</span><span>Phím vừa bấm: <b id="kbl">—</b></span>
      <label class="ck" style="margin:0"><input type="checkbox" id="npck"> Có bàn phím số (Numpad)</label><button class="btn sm" id="kbr">↺ Làm lại</button></div>
    <div class="logl">Bấm lần lượt từng phím. Phím Fn và vài phím chức năng của hãng (tăng sáng, âm lượng...) Windows không báo nên không sáng. Bấm Esc hai lần liền để thoát.</div>`,
    "Phím đang giữ: đỏ · đã nhận: xanh", {keepEsc: true});
  const got = new Set(); let lastEsc = 0;
  const upd = () => { $("kbn").textContent = [...got].filter(c => KB.flat().some(k => k[0] === c)).length; };
  const dn = e => {
    if (e.code === "Escape") { if (Date.now() - lastEsc < 600) { e.preventDefault(); return close(); } lastEsc = Date.now(); }
    e.preventDefault();
    const k = document.querySelector(`.key[data-c="${e.code}"]`);
    if (k) { k.classList.add("down", "got"); got.add(e.code); upd(); }
    $("kbl").textContent = `${e.key === " " ? "Space" : e.key} (${e.code || "?"})`;
  };
  const up = e => { e.preventDefault(); const k = document.querySelector(`.key[data-c="${e.code}"]`); if (k) k.classList.remove("down");
    if (e.code === "PrintScreen" && k) { k.classList.add("got"); got.add(e.code); upd(); } };   // PrtSc chỉ báo lúc nhả
  document.addEventListener("keydown", dn, true); document.addEventListener("keyup", up, true);
  tvClose = () => { document.removeEventListener("keydown", dn, true); document.removeEventListener("keyup", up, true); };
  $("npck").onchange = () => { $("np").hidden = !$("npck").checked; };
  $("kbr").onclick = () => { got.clear(); document.querySelectorAll(".key").forEach(k => k.classList.remove("got", "down")); upd(); };
}

/* ---------------- 4. loa ---------------- */
let AC = null;
function actx() { if (!AC) AC = new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === "suspended") AC.resume(); return AC; }
function tone({pan = 0, f = 440, f2 = null, dur = 1.5, type = "sine", vol = 0.35} = {}) {
  const c = actx(), o = c.createOscillator(), g = c.createGain(), p = c.createStereoPanner ? c.createStereoPanner() : null, t = c.currentTime;
  o.type = type; o.frequency.setValueAtTime(f, t); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t + dur);
  g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol * (+$("spv").value / 100), t + 0.04); g.gain.setValueAtTime(vol * (+$("spv").value / 100), t + dur - 0.08); g.gain.linearRampToValueAtTime(0, t + dur);
  if (p) { p.pan.value = pan; o.connect(g).connect(p).connect(c.destination); } else o.connect(g).connect(c.destination);
  o.start(t); o.stop(t + dur);
}
function melody() { [523, 659, 784, 1047, 784, 659, 523].forEach((f, i) => setTimeout(() => tone({f, dur: 0.28, type: "triangle"}), i * 260)); }
function tSpk() {
  openView("spk", "Test loa", `<div class="spk">
      <button class="sbig" data-s="l"><span>◀🔊</span><b>Loa TRÁI</b><small>Chỉ bên trái kêu</small></button>
      <button class="sbig" data-s="b"><span>🔊🔊</span><b>Cả hai loa</b><small>Hai bên đều kêu</small></button>
      <button class="sbig" data-s="r"><span>🔊▶</span><b>Loa PHẢI</b><small>Chỉ bên phải kêu</small></button>
      <button class="sbig" data-s="sw"><span>〰️</span><b>Quét 60 Hz → 12 kHz</b><small>Nghe có rè / rung / mất tiếng ở dải nào</small></button>
      <button class="sbig" data-s="bass"><span>🥁</span><b>Âm trầm 60 Hz</b><small>Nghe màng loa có rè không</small></button>
      <button class="sbig" data-s="mel"><span>🎵</span><b>Giai điệu thử</b><small>Kiểm tra âm thanh tổng thể</small></button></div>
    <div class="fr" style="justify-content:center">Âm lượng thử <input type="range" id="spv" min="5" max="100" value="60" style="width:260px"> <span class="logl" style="margin:0">Âm lượng Windows vẫn áp dụng.</span></div>`,
    "Mở âm lượng Windows vừa phải trước khi test");
  document.querySelector(".spk").onclick = e => { const b = e.target.closest("[data-s]"); if (!b) return;
    b.classList.add("on"); setTimeout(() => b.classList.remove("on"), 1500);
    ({l: () => tone({pan: -1}), r: () => tone({pan: 1}), b: () => tone({}), sw: () => tone({f: 60, f2: 12000, dur: 6, vol: 0.3}),
      bass: () => tone({f: 60, dur: 2.5, vol: 0.6}), mel: melody})[b.dataset.s](); };
}

/* ---------------- 5. micro ---------------- */
function noMedia(kind) {
  return `<div class="empty big">Không mở được ${kind}.\nKiểm tra: Cài đặt Windows → Quyền riêng tư → ${kind === "micro" ? "Microphone" : "Camera"} → cho phép ứng dụng dùng.</div>`;
}
async function devSelect(kind, sel) {
  try { const d = (await navigator.mediaDevices.enumerateDevices()).filter(x => x.kind === kind);
    sel.innerHTML = d.map((x, i) => `<option value="${x.deviceId}">${esc(x.label || (kind === "audioinput" ? "Micro " : "Camera ") + (i + 1))}</option>`).join(""); } catch (e) { /* bỏ qua */ }
}
function tMic() {
  let stream = null, raf = 0, rec = null, peak = 0;
  openView("mic", "Test micro", `<div class="micw">
      <div class="fr">Micro <select id="micsel" style="min-width:320px"></select> <button class="btn sm" id="micset">⚙ Cài đặt âm thanh Windows</button></div>
      <div class="vu"><div class="vub" id="vub"></div><div class="vup" id="vup"></div></div>
      <div class="vut"><span>Âm lượng: <b id="vuv">0</b>%</span><span>Đỉnh: <b id="vupk">0</b>%</span></div>
      <div class="row-acts" style="justify-content:center"><button class="btn red shine" id="micrec">⏺ Ghi âm 5 giây</button>
        <audio id="micplay" controls hidden></audio></div>
      <div class="logl" id="micmsg">Nói thử vào micro, cột âm lượng phải nhảy theo giọng.</div></div>`, "Nói vào micro");
  const start = async id => {
    stop();
    try { stream = await navigator.mediaDevices.getUserMedia({audio: id ? {deviceId: {exact: id}} : true}); }
    catch (e) { document.querySelector(".micw").insertAdjacentHTML("afterbegin", noMedia("micro")); return; }
    await devSelect("audioinput", $("micsel")); if (id) $("micsel").value = id;
    const c = actx(), src = c.createMediaStreamSource(stream), an = c.createAnalyser(); an.fftSize = 1024; src.connect(an);
    const buf = new Float32Array(an.fftSize);
    const loop = () => { an.getFloatTimeDomainData(buf); let s = 0; for (const v of buf) s += v * v;
      const lv = Math.min(100, Math.round(Math.sqrt(s / buf.length) * 300)); peak = Math.max(peak * 0.995, lv);
      if ($("vub")) { $("vub").style.width = lv + "%"; $("vup").style.left = peak + "%"; $("vuv").textContent = lv; $("vupk").textContent = Math.round(peak); raf = requestAnimationFrame(loop); } };
    loop();
  };
  const stop = () => { cancelAnimationFrame(raf); if (stream) stream.getTracks().forEach(t => t.stop()); stream = null; };
  tvClose = stop;
  if (!navigator.mediaDevices) { document.querySelector(".micw").insertAdjacentHTML("afterbegin", noMedia("micro")); return; }
  start();
  $("micsel").onchange = () => start($("micsel").value);
  $("micset").onclick = () => api("quick", "ms-settings:sound");
  $("micrec").onclick = () => {
    if (!stream || !window.MediaRecorder) return toast("Chưa mở được micro", "err");
    const chunks = []; rec = new MediaRecorder(stream); rec.ondataavailable = e => chunks.push(e.data);
    rec.onstop = () => { const a = $("micplay"); if (!a) return; a.src = URL.createObjectURL(new Blob(chunks)); a.hidden = false; a.play(); $("micmsg").textContent = "Đang phát lại đoạn vừa ghi. Nghe rõ, không rè là đạt."; };
    rec.start(); let n = 5; $("micrec").disabled = true;
    const tick = () => { if (!$("micrec")) return; if (n === 0) { rec.stop(); $("micrec").disabled = false; $("micrec").textContent = "⏺ Ghi âm 5 giây"; return; }
      $("micrec").textContent = `⏺ Đang ghi... ${n}s`; n--; setTimeout(tick, 1000); };
    tick();
  };
}

/* ---------------- 6. trackpad ---------------- */
function tPad() {
  const items = [["move", "Di chuyển con trỏ"], ["left", "Click trái"], ["right", "Click phải"], ["dbl", "Nhấp đúp"],
    ["vs", "Cuộn dọc (2 ngón)"], ["hs", "Cuộn ngang (2 ngón)"], ["zoom", "Phóng to / thu nhỏ (chụm 2 ngón)"], ["drag", "Giữ và kéo"]];
  openView("pad", "Test trackpad / chuột", `<div class="padw"><div class="pada" id="pada"><canvas id="pcv"></canvas><div class="padt">Thực hiện các thao tác trong vùng này</div></div>
      <div class="padl">${items.map(([k, t]) => `<div class="pi" data-k="${k}">${led("off", "sm")}<span>${t}</span></div>`).join("")}
        <div class="logl" id="padn"></div></div></div>`, "Làm hết các thao tác, mục nào nhận sẽ sáng xanh");
  const A = $("pada"), cv = $("pcv"), g = cv.getContext("2d"); let last = null, dist = 0;
  setTimeout(() => { cv.width = A.clientWidth; cv.height = A.clientHeight; }, 60);
  const ok = k => { const el = document.querySelector(`.pi[data-k="${k}"]`); if (el && !el.classList.contains("on")) { el.classList.add("on"); el.querySelector(".led").className = "led sm ok";
    $("padn").textContent = `Đã nhận ${document.querySelectorAll(".pi.on").length}/${items.length} thao tác`; } };
  A.onmousemove = e => { const r = A.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    if (last) { dist += Math.hypot(x - last[0], y - last[1]); g.strokeStyle = e.buttons & 1 ? "#e0262a" : "rgba(47,127,163,.55)"; g.lineWidth = e.buttons & 1 ? 4 : 2;
      g.beginPath(); g.moveTo(last[0], last[1]); g.lineTo(x, y); g.stroke(); if (e.buttons & 1) ok("drag"); }
    last = [x, y]; if (dist > 300) ok("move"); };
  A.onmouseleave = () => { last = null; };
  A.onmousedown = e => { if (e.button === 0) ok("left"); if (e.button === 2) ok("right"); };
  A.oncontextmenu = e => { e.preventDefault(); ok("right"); };
  A.ondblclick = () => ok("dbl");
  A.addEventListener("wheel", e => { e.preventDefault(); if (e.ctrlKey) return ok("zoom"); if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) ok("vs"); else if (e.deltaX) ok("hs"); }, {passive: false});
}

/* ---------------- 7. webcam ---------------- */
function tCam() {
  let stream = null;
  openView("cam", "Test webcam", `<div class="camw"><div class="camv"><video id="camv" autoplay playsinline muted></video><canvas id="camc" hidden></canvas></div>
      <div class="caml"><div class="fr">Camera <select id="camsel" style="min-width:260px"></select></div>
        <label class="ck"><input type="checkbox" id="cammir" checked> Lật hình như gương</label>
        <div class="kv" id="caminfo"></div>
        <div class="row-acts"><button class="btn red shine" id="camsnap">📸 Chụp thử</button><button class="btn sm" id="camapp">Mở app Camera của Windows</button></div>
        <img id="camimg" class="camimg" hidden></div></div>`, "Xem hình có rõ, đúng màu, không sọc / nhiễu");
  const stop = () => { if (stream) stream.getTracks().forEach(t => t.stop()); stream = null; };
  tvClose = stop;
  const start = async id => {
    stop();
    try { stream = await navigator.mediaDevices.getUserMedia({video: id ? {deviceId: {exact: id}, width: {ideal: 1920}, height: {ideal: 1080}} : {width: {ideal: 1920}, height: {ideal: 1080}}}); }
    catch (e) { $("camv").parentElement.innerHTML = noMedia("camera"); return; }
    $("camv").srcObject = stream; await devSelect("videoinput", $("camsel")); if (id) $("camsel").value = id;
    const s = stream.getVideoTracks()[0].getSettings();
    $("caminfo").innerHTML = `<div class="k">Độ phân giải</div><div class="v">${s.width || "?"} × ${s.height || "?"}${s.height >= 1080 ? " (Full HD)" : s.height >= 720 ? " (HD)" : ""}</div>
      <div class="k">Khung hình</div><div class="v">${s.frameRate ? Math.round(s.frameRate) + " fps" : "?"}</div>`;
  };
  if (!navigator.mediaDevices) { $("camv").parentElement.innerHTML = noMedia("camera"); }
  else start();
  $("camsel").onchange = () => start($("camsel").value);
  $("cammir").onchange = () => $("camv").classList.toggle("nomir", !$("cammir").checked);
  $("camapp").onclick = () => { stop(); api("quick", "microsoft.windows.camera:"); };
  $("camsnap").onclick = () => { const v = $("camv"); if (!v || !v.videoWidth) return; const c = $("camc"); c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d").drawImage(v, 0, 0); $("camimg").src = c.toDataURL("image/jpeg", 0.9); $("camimg").hidden = false; };
}

/* ---------------- 8. pin ---------------- */
async function loadBattery(force) {
  if (BAT && !force) return renderBattery();
  $("tb-bat").innerHTML = '<div class="logl"><span class="spin"></span> Đang đọc pin...</div>';
  BAT = await api("battery"); renderBattery();
}
function renderBattery() {
  const B = BAT, el = $("tb-bat");
  if (!B.has) { el.innerHTML = `<div class="empty">🔌 Máy này không có pin (máy bàn hoặc đã tháo pin).</div>`; return; }
  const st = B.charging ? "⚡ Đang sạc" : B.ac ? "🔌 Cắm sạc" : "🔋 Đang dùng pin";
  const left = B.left_min ? `${Math.floor(B.left_min / 60)} giờ ${B.left_min % 60} phút` : "";
  el.innerHTML = `<div class="batnow"><div class="batc"><div class="batf" style="width:${B.pct ?? 0}%"></div><b>${B.pct ?? "?"}%</b></div><span>${st}${left ? " · còn khoảng " + left : ""}</span></div>` +
    (B.batteries || []).map(b => { const h = b.health ?? 0, cls = h >= 80 ? "good" : h >= 60 ? "mid" : "bad";
      return `<div class="batrow"><div class="ring sm ${cls}" style="--p:${Math.min(100, h)};--c:${h >= 80 ? "#16a34a" : h >= 60 ? "#d97706" : "#e0262a"}"><div class="rin"><b>${b.health ?? "?"}%</b><small>SỨC KHỎE</small></div></div>
        <div class="kv"><div class="k">Pin</div><div class="v">${esc([b.maker, b.name].filter(Boolean).join(" · "))}${b.chem ? " · " + esc(b.chem) : ""}</div>
          <div class="k">Thiết kế</div><div class="v">${(b.design || 0).toLocaleString("vi-VN")} mWh</div>
          <div class="k">Sạc đầy hiện tại</div><div class="v">${(b.full || 0).toLocaleString("vi-VN")} mWh</div>
          <div class="k">Độ chai</div><div class="v">${b.health != null ? Math.max(0, 100 - b.health) + "%" : "?"} ${h >= 80 ? pill("Tốt", "t-done") : h >= 60 ? pill("Chai vừa", "t-skip") : pill("Chai nhiều - nên thay", "t-err")}</div>
          <div class="k">Số lần sạc</div><div class="v">${b.cycles ?? "Máy không báo"}</div></div></div>`; }).join("") +
    (B.err ? `<div class="logl">${esc(B.err)}</div>` : "");
}
