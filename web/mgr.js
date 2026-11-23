/* Win AIO by Duy Anh - trang QUẢN LÝ / DỌN DẸP / SAO LƯU (v2.1) */
const m = (name, ...a) => api("m", name, ...a);
const hs = n => { n = +n || 0; const u = ["B", "KB", "MB", "GB", "TB"]; let i = 0; while (n >= 1024 && i < 4) { n /= 1024; i++; } return (i < 2 ? n.toFixed(0) : n.toFixed(1)) + " " + u[i]; };
const errBox = (title, msg) => dialog({title, body: `<div class="msg">${esc(msg)}</div>`, buttons: [{text: "OK", cls: "red", def: true}]});

/* ---------- việc chạy lâu: hộp tiến độ có % và nút Dừng ---------- */
function runJob(name, label, args) {
  return new Promise(async resolve => {
    let jid;
    try { jid = await api("mjob", name, label, ...args); } catch (e) { return resolve({ok: false, result: String(e)}); }
    let ctl = null;
    dialog({title: label, width: 560, body: `<div class="jobt" id="jobt">Đang chuẩn bị...</div>
        <div class="bar jbar"><div class="b-green" id="jobb" style="width:0"></div></div><div class="jobp"><b id="jobp">0%</b><span id="jobs"></span></div>`,
      buttons: [{text: "■ Dừng", cls: "out", click: () => { m("job_stop", jid); toast("Đang dừng..."); return false; }}], onOpen: c => { ctl = c; }});
    const t0 = Date.now();
    const poll = setInterval(async () => {
      let s; try { s = await m("job_status", jid); } catch (e) { return; }
      if ($("jobb")) { $("jobb").style.width = s.pct + "%"; $("jobp").textContent = s.pct + "%"; $("jobt").textContent = s.text || ""; $("jobs").textContent = Math.round((Date.now() - t0) / 1000) + " giây"; }
      if (s.done) { clearInterval(poll); if (ctl) ctl.close(false); if (!s.ok) errBox(label, s.result); resolve(s); }
    }, 450);
  });
}
const tbl = (cols, rows, empty) => `<div class="tablewrap mt"><table><thead><tr>${cols.map(c => `<th${c[1] ? ` style="width:${c[1]}"` : ""}>${c[0]}</th>`).join("")}</tr></thead>
  <tbody>${rows || `<tr><td colspan="${cols.length}" class="empty">${empty || "Không có gì"}</td></tr>`}</tbody></table></div>`;

/* =============================================================== QUẢN LÝ */
let MT = "startup";
const MLOAD = {};
function mgrShow() {
  $("mtabs").onclick = e => { const d = e.target.closest("[data-t]"); if (!d) return; MT = d.dataset.t;
    $("mtabs").querySelectorAll("div").forEach(x => x.classList.toggle("on", x === d));
    document.querySelectorAll(".mpane").forEach(p => p.hidden = p.id !== "mp-" + MT); mgrShow(); };
  if (!MLOAD[MT]) { MLOAD[MT] = 1; ({startup: stLoad, programs: prLoad, appx: axLoad, defender: dfLoad, upgrade: upLoad, driver: drvLoad})[MT](); }
}

/* ---------- khởi động cùng Windows ---------- */
let ST_ITEMS = [], stSel = new Set();
async function stLoad() {
  $("mp-startup").innerHTML = `<div class="mbar"><button class="btn" id="stRef">⟳ Làm mới</button>
      <button class="btn" id="stOff">⏸ Vô hiệu</button><button class="btn green" id="stOn">▶ Kích hoạt</button>
      <button class="btn out" id="stDel">🗑 Xóa</button><button class="btn" id="stLoc">📂 Mở vị trí</button>
      <span class="cnt" id="stCnt">Đang đọc...</span><span class="sp"></span>⌕ <input type="search" id="stQ" placeholder="tìm..." style="width:200px"></div>
    <div id="stTbl">${tbl([["Tên"]], "", '<span class="spin"></span> Đang đọc danh sách...')}</div>
    <div class="logl">Vô hiệu = không chạy cùng Windows nữa nhưng vẫn giữ lại (giống Task Manager). Xóa = bỏ hẳn (có lưu bản sao trong Data\\Backup).</div>`;
  $("stRef").onclick = stLoad;
  $("stQ").oninput = stRender;
  $("stOff").onclick = () => stAct(false); $("stOn").onclick = () => stAct(true);
  $("stDel").onclick = async () => { const L = stPicked(); if (!L.length) return toast("Chọn mục trước", "err");
    if (!(await confirmBox("Xóa mục khởi động", `Xóa ${L.length} mục khỏi danh sách khởi động?\n${L.map(x => "• " + x.name).join("\n")}\n\n(Bản sao lưu giữ trong Data\\Backup)`, "🗑 Xóa"))) return;
    for (const x of L) { await m("startup_delete", x.id); } toast(`Đã xóa ${L.length} mục`); stLoad(); };
  $("stLoc").onclick = () => { const L = stPicked(); if (!L.length) return toast("Chọn 1 mục trước", "err"); api("select_in_explorer", L[0].cmd); };
  ST_ITEMS = await m("startup_list"); stSel.clear(); stRender();
}
const stPicked = () => ST_ITEMS.filter(x => stSel.has(x.id));
async function stAct(on) { const L = stPicked(); if (!L.length) return toast("Chọn mục trước", "err");
  for (const x of L) await m("startup_set", x.id, on); toast(`${on ? "Đã kích hoạt" : "Đã vô hiệu"} ${L.length} mục`); ST_ITEMS = await m("startup_list"); stRender(); }
function stRender() {
  const q = norm($("stQ").value);
  const L = ST_ITEMS.filter(x => !q || norm(x.name + " " + x.pub + " " + x.cmd).includes(q));
  $("stCnt").textContent = `Tìm thấy ${ST_ITEMS.length} mục khởi động · ${ST_ITEMS.filter(x => x.on).length} đang bật`;
  $("stTbl").innerHTML = tbl([["", "34px"], ["Tên", "20%"], ["Nhà phát hành", "16%"], ["Trạng thái", "100px"], ["Vị trí", "140px"], ["Đường dẫn"]],
    L.map(x => `<tr data-id="${esc(x.id)}" class="${x.on ? "" : "dim"}${stSel.has(x.id) ? " sel" : ""}"><td><span class="chk${stSel.has(x.id) ? " on" : ""}"></span></td>
      <td><b>${esc(x.name)}</b></td><td>${esc(x.pub || "Không rõ")}</td><td>${x.on ? pill("Đã bật", "t-done") : pill("Đã tắt", "t-skip")}</td>
      <td>${esc(x.where)}</td><td class="path" title="${esc(x.cmd)}">${esc(x.cmd)}</td></tr>`).join(""), "Không có chương trình nào chạy cùng Windows");
  $("stTbl").querySelector("tbody").onclick = e => { const tr = e.target.closest("tr[data-id]"); if (!tr) return;
    const id = tr.dataset.id; stSel.has(id) ? stSel.delete(id) : stSel.add(id); stRender(); };
}

/* ---------- gỡ phần mềm tận gốc ---------- */
let PR = [];
async function prLoad() {
  $("mp-programs").innerHTML = `<div class="mbar"><button class="btn" id="prRef">⟳ Làm mới</button><span class="cnt" id="prCnt">Đang đọc...</span>
      <span class="sp"></span>Sắp xếp <select id="prSort"><option value="name">Tên</option><option value="size">Dung lượng</option><option value="date">Ngày cài</option></select>
      ⌕ <input type="search" id="prQ" placeholder="tìm phần mềm..." style="width:220px"></div>
    <div id="prTbl">${tbl([["Tên"]], "", '<span class="spin"></span> Đang đọc danh sách phần mềm...')}</div>
    <div class="logl">Gỡ tận gốc: chạy trình gỡ của phần mềm, sau đó tìm thư mục và registry còn sót để bạn xem lại và chọn xóa.</div>`;
  $("prRef").onclick = prLoad; $("prQ").oninput = prRender; $("prSort").onchange = prRender;
  PR = await m("programs_list"); prRender();
}
function prRender() {
  const q = norm($("prQ").value), so = $("prSort").value;
  const dkey = d => d ? d.split("/").reverse().join("") : "";
  const L = PR.filter(x => !q || norm(x.name + " " + x.pub).includes(q))
    .sort((a, b) => so === "size" ? b.size - a.size : so === "date" ? dkey(b.date).localeCompare(dkey(a.date)) : a.name.localeCompare(b.name));
  $("prCnt").textContent = `${PR.length} phần mềm · ${hs(PR.reduce((s, x) => s + x.size, 0))}`;
  $("prTbl").innerHTML = tbl([["Tên"], ["Nhà phát hành", "18%"], ["Phiên bản", "120px"], ["Dung lượng", "100px"], ["Ngày cài", "100px"], ["", "110px"]],
    L.map(x => `<tr data-id="${esc(x.id)}"><td><b>${esc(x.name)}</b></td><td>${esc(x.pub)}</td><td>${esc(x.ver)}</td>
      <td>${x.size ? hs(x.size) : ""}</td><td>${esc(x.date)}</td><td><button class="btn sm out" data-a="un">🗑 Gỡ</button></td></tr>`).join(""));
  $("prTbl").querySelector("tbody").onclick = e => { const b = e.target.closest("[data-a]"); if (!b) return;
    prUninstall(PR.find(x => x.id === b.closest("tr").dataset.id)); };
}
async function prUninstall(p) {
  const quiet = await dialog({title: "Gỡ " + p.name, width: 560, body: `<div class="msg">Gỡ <b>${esc(p.name)}</b>${p.ver ? " " + esc(p.ver) : ""}?
      Trình gỡ của phần mềm sẽ chạy, xong tool tìm phần còn sót để bạn chọn xóa.</div>
      <label class="ck" style="margin-top:10px"><input type="checkbox" id="prQuiet"${p.quiet ? "" : " disabled"}> Gỡ im lặng (không hiện cửa sổ gỡ)${p.quiet ? "" : " — phần mềm này không hỗ trợ"}</label>`,
    buttons: [{text: "Hủy", value: null}, {text: "🗑 Gỡ tận gốc", cls: "red", def: true, click: c => c.q("#prQuiet").checked ? 1 : 0}]});
  if (quiet === null || quiet === undefined || quiet === false) return;
  const r = await runJob("uninstall_run", "Gỡ " + p.name, [p.id, !!quiet]);
  if (r.ok) await leftoverBox(p, r.result.left || []);
  PR = await m("programs_list"); prRender();
}
async function leftoverBox(p, left) {
  const body = L => L.length ? `<div class="msg">Tìm thấy ${L.length} mục còn sót của <b>${esc(p.name)}</b>. Bỏ tick mục bạn muốn giữ lại.</div>
      <div class="lolist">${L.map((x, i) => `<label class="ck lo"><input type="checkbox" data-i="${i}" checked> <span class="pill ${x.kind === "dir" ? "t-new" : "t-skip"}">${x.kind === "dir" ? "THƯ MỤC" : "REGISTRY"}</span>
        <span class="lp">${esc(x.path)}</span><em>${x.size ? hs(x.size) : ""} · ${esc(x.why)}</em></label>`).join("")}</div>`
    : `<div class="msg">✔ Không còn sót thư mục hay registry nào của <b>${esc(p.name)}</b>.
       Nếu cửa sổ gỡ của phần mềm vẫn đang mở, làm xong rồi bấm "⟳ Quét lại".</div>`;
  let L = left;
  await dialog({title: "Dọn phần còn sót", width: 760, body: `<div id="lobody">${body(L)}</div>`,
    left: `<button class="btn sm" id="loRe">⟳ Quét lại</button>`,
    buttons: [{text: "Đóng", value: false}, {text: "🗑 Xóa mục đã chọn", cls: "red", def: true, click: async c => {
      const sel = [...c.el.querySelectorAll("input[data-i]:checked")].map(x => L[+x.dataset.i]);
      if (!sel.length) return true;
      const r = await m("leftovers_delete", sel);
      toast(`Đã xóa ${r.done} mục` + (r.errs.length ? `, ${r.errs.length} mục không xóa được` : ""), r.errs.length ? "err" : "");
      if (r.errs.length) errBox("Chưa xóa hết", r.errs.join("\n"));
      return true; }}],
    onOpen: c => { c.q("#loRe").onclick = async () => { c.q("#lobody").innerHTML = '<span class="spin"></span> Đang quét...'; L = await m("leftovers_rescan", p.id); c.q("#lobody").innerHTML = body(L); }; }});
}

/* ---------- ứng dụng MS Store ---------- */
let AX = [], axSel = new Set();
async function axLoad() {
  $("mp-appx").innerHTML = `<div class="mbar"><button class="btn" id="axRef">⟳ Làm mới</button><button class="btn out" id="axDel">🗑 Gỡ mục đã chọn</button>
      <label class="ck" style="margin:0"><input type="checkbox" id="axAll"> Gỡ cho mọi tài khoản trên máy</label>
      <span class="cnt" id="axCnt">Đang đọc...</span><span class="sp"></span>⌕ <input type="search" id="axQ" placeholder="tìm ứng dụng..." style="width:220px"></div>
    <div id="axTbl">${tbl([["Tên"]], "", '<span class="spin"></span> Đang đọc ứng dụng MS Store (mất vài giây)...')}</div>
    <div class="logl">Chỉ hiện ứng dụng gỡ được. Ứng dụng hệ thống và thư viện nền (framework) đã được ẩn để tránh gỡ nhầm. Gỡ xong có thể cài lại từ Microsoft Store.</div>`;
  $("axRef").onclick = axLoad; $("axQ").oninput = axRender;
  $("axDel").onclick = async () => {
    const L = AX.filter(x => axSel.has(x.full)); if (!L.length) return toast("Chọn ứng dụng trước", "err");
    if (!(await confirmBox("Gỡ ứng dụng MS Store", `Gỡ ${L.length} ứng dụng?\n${L.map(x => "• " + x.disp).join("\n")}`, "🗑 Gỡ"))) return;
    const r = await runJob("appx_remove", `Gỡ ${L.length} ứng dụng MS Store`, [L.map(x => x.full), $("axAll").checked]);
    if (r.ok) { toast(`Đã gỡ ${r.result.done} ứng dụng`); if (r.result.errs.length) errBox("Có ứng dụng chưa gỡ được", r.result.errs.join("\n")); }
    axLoad();
  };
  AX = await m("appx_list"); axSel.clear(); axRender();
}
function axRender() {
  const q = norm($("axQ").value), L = AX.filter(x => !q || norm(x.disp + " " + x.name + " " + x.pub).includes(q));
  $("axCnt").textContent = `${AX.length} ứng dụng · đã chọn ${axSel.size}`;
  $("axTbl").innerHTML = tbl([["", "34px"], ["Tên ứng dụng", "28%"], ["Gói"], ["Phiên bản", "140px"], ["Nhà phát hành", "18%"]],
    L.map(x => `<tr data-id="${esc(x.full)}" class="${axSel.has(x.full) ? "sel" : ""}"><td><span class="chk${axSel.has(x.full) ? " on" : ""}"></span></td>
      <td><b>${esc(x.disp)}</b></td><td class="path">${esc(x.name)}</td><td>${esc(x.ver)}</td><td>${esc(x.pub)}</td></tr>`).join(""));
  $("axTbl").querySelector("tbody").onclick = e => { const tr = e.target.closest("tr[data-id]"); if (!tr) return;
    axSel.has(tr.dataset.id) ? axSel.delete(tr.dataset.id) : axSel.add(tr.dataset.id); axRender(); };
}

/* ---------- Defender & bảo mật ---------- */
let DF = null;
async function dfLoad() {
  $("mp-defender").innerHTML = '<div class="empty"><span class="spin"></span> Đang đọc trạng thái Defender...</div>';
  DF = await m("defender_status"); dfRender();
}
function dfRender() {
  const d = DF;
  if (d.err) { $("mp-defender").innerHTML = `<div class="empty">Không đọc được Defender: ${esc(d.err)}</div>`; return; }
  const fwOn = (d.fw || []).filter(f => f.on).length, fwAll = (d.fw || []).length;
  const parts = [d.rt, d.cloud > 0, d.av, fwOn === fwAll];
  const lv = parts.every(Boolean) ? ["ĐANG BẢO VỆ ĐẦY ĐỦ", "ok"] : parts.some(Boolean) ? ["TẮT MỘT PHẦN", "warn"] : ["ĐANG TẮT", "bad"];
  const row = (name, on, what, note) => `<div class="dfr"><span class="dfn">${name}</span>${on === null ? pill("Không rõ", "t-skip") : on ? pill("Bật", "t-done") : pill("Tắt", "t-err")}
    <span class="sp"></span>${what ? `<button class="btn sm out" data-off="${what}">⛔ Tắt</button><button class="btn sm green" data-on="${what}">✓ Bật</button>` : note || ""}</div>`;
  const ex = (k, title, ph) => `<div class="exg"><b>${title}</b><div class="exl">${(d["excl_" + k] || []).map(v => `<span class="exi">${esc(v)}<i data-rm="${k}" data-v="${esc(v)}">✕</i></span>`).join("") || '<span class="logl" style="margin:0">(chưa có)</span>'}</div>
    <div class="row2"><input id="ex-${k}" placeholder="${ph}">${k === "path" ? '<button class="btn sm" data-pick="1">📂</button>' : ""}<button class="btn sm green" data-add="${k}">＋ Thêm</button></div></div>`;
  $("mp-defender").innerHTML = `<div class="syswrap"><div class="dfban ${lv[1]}"><span class="dfdot"></span>Windows Defender: <b>${lv[0]}</b>
      <span class="sp"></span><button class="btn sm" id="dfRef">⟳ Kiểm tra lại</button><button class="btn sm" id="dfOpen">⚙ Mở Windows Security</button></div>
    <div class="dfgrid">
      <div class="tcard" style="--ac:#16a34a"><div class="sh"><span class="si">🛡️</span><div><b>THÀNH PHẦN BẢO VỆ</b><small>Bật / tắt từng phần bằng lệnh chính thức của Windows</small></div></div>
        ${row("Realtime Protection", d.rt, "rt")}${row("Cloud Protection", d.cloud > 0, "cloud")}${row("Gửi mẫu tự động", d.sample === 1 || d.sample === 3, "sample")}
        ${row("Tamper Protection", d.tamper, "", '<button class="btn sm" data-sec="1">Đổi trong Windows Security</button>')}
        <div class="dfnote">⚠ Khi <b>Tamper Protection</b> đang bật, Windows chặn mọi công cụ đổi Defender: tắt nó trong Windows Security trước.</div></div>
      <div class="tcard" style="--ac:#0f8fd8"><div class="sh"><span class="si">🧱</span><div><b>FIREWALL · SMARTSCREEN · UAC</b><small>Tường lửa, cảnh báo file tải về, hỏi quyền Admin</small></div></div>
        ${row(`Firewall (${(d.fw || []).map(f => f.n + (f.on ? " ✓" : " ✗")).join(" · ")})`, fwOn === fwAll ? true : fwOn === 0 ? false : null, "fw")}
        ${row("SmartScreen (Windows)", d.smart === "Off" ? false : true, "smart")}
        ${row(`UAC hỏi quyền Admin${d.uac === 0 ? " (đang: không hỏi)" : ""}`, d.uac !== 0, "uac")}</div>
      <div class="tcard wide" style="--ac:#d97706"><div class="sh"><span class="si">📁</span><div><b>NGOẠI LỆ (EXCLUSIONS)</b><small>Defender sẽ không quét các mục này — chỉ thêm thứ bạn tin tưởng</small></div></div>
        <div class="exgrid">${ex("path", "Thư mục / file", "D:\\Tools")}${ex("proc", "Tiến trình", "app.exe")}${ex("ext", "Đuôi file", ".iso")}</div></div>
      <div class="tcard wide" style="--ac:#6b7280"><div class="sh"><span class="si">📋</span><div><b>TRẠNG THÁI CHI TIẾT</b></div></div>
        ${tbl([["Thành phần", "26%"], ["Trạng thái", "16%"], ["Chi tiết"]], [
          ["Dịch vụ WinDefend", d.svc === "Running", d.svc], ["Realtime Protection", d.rt, d.rt ? "Đang quét theo thời gian thực" : "Không quét file khi mở"],
          ["Tamper Protection", d.tamper, d.tamper ? "Chặn công cụ khác đổi Defender" : "Tắt"], ["Cloud Protection", d.cloud > 0, "MAPSReporting = " + d.cloud],
          ["Diệt virus (Antivirus)", d.av, "Dữ liệu virus " + (d.sig || "?") + (d.sigdate ? " · cập nhật " + d.sigdate : "")]]
          .map(([n, on, t]) => `<tr><td>${n}</td><td>${on ? pill("Bật", "t-done") : pill("Tắt", "t-err")}</td><td>${esc(t || "")}</td></tr>`).join(""))}</div>
    </div></div>`;
  const w = $("mp-defender");
  $("dfRef").onclick = dfLoad;
  $("dfOpen").onclick = () => api("quick", "windowsdefender://threatsettings");
  w.querySelectorAll("[data-sec]").forEach(b => b.onclick = () => api("quick", "windowsdefender://threatsettings"));
  w.onclick = async e => {
    const b = e.target.closest("[data-on],[data-off],[data-add],[data-rm],[data-pick]"); if (!b) return;
    if (b.dataset.pick) { const p = await api("pick_folder_abs"); if (p) $("ex-path").value = p; return; }
    if (b.dataset.add) { const v = $("ex-" + b.dataset.add).value; const r = await m("defender_excl", "add", b.dataset.add, v); if (r) return errBox("Thêm ngoại lệ", r); toast("Đã thêm ngoại lệ"); return dfLoad(); }
    if (b.dataset.rm) { const r = await m("defender_excl", "remove", b.dataset.rm, b.dataset.v); if (r) return errBox("Bỏ ngoại lệ", r); toast("Đã bỏ ngoại lệ"); return dfLoad(); }
    const what = b.dataset.on || b.dataset.off, on = !!b.dataset.on;
    const names = {rt: "Realtime Protection", cloud: "Cloud Protection", sample: "gửi mẫu tự động", fw: "Firewall (cả 3 mạng)", smart: "SmartScreen", uac: "hỏi quyền UAC"};
    if (!on && !(await confirmBox("Tắt " + names[what], `Tắt ${names[what]}? Máy sẽ kém an toàn hơn — nhớ bật lại khi xong việc.`, "⛔ Tắt"))) return;
    b.disabled = true;
    const r = await m("defender_set", what, on);
    if (r) errBox(names[what], r); else toast(`Đã ${on ? "bật" : "tắt"} ${names[what]}`);
    dfLoad();
  };
}

/* =============================================================== DỌN DẸP */
let CL = null, FS = null, FSP = "C:\\";
function cleanShow() {
  if ($("cleanwrap").dataset.ok) return;
  $("cleanwrap").dataset.ok = 1;
  $("cleanwrap").innerHTML = `<div class="cgrid">
    <div class="tcard wide2" style="--ac:#16a34a"><div class="sh"><span class="si">🧹</span><div><b>DỌN RÁC HỆ THỐNG</b><small>File tạm, bộ cài Windows Update, cache trình duyệt, thùng rác...</small></div>
        <span class="sp"></span><button class="btn red shine" id="clScan">🔍 Quét</button></div><div id="clList"><div class="logl">Bấm "Quét" để đo dung lượng rác.</div></div></div>
    <div class="tcard" style="--ac:#7c3aed"><div class="sh"><span class="si">🎬</span><div><b>CACHE CAPCUT PC</b><small>Xóa cache dựng video, dự án của bạn giữ nguyên</small></div></div><div id="ccBody"><div class="logl"><span class="spin"></span> Đang đo...</div></div></div>
    <div class="tcard wide2" style="--ac:#0f8fd8"><div class="sh"><span class="si">📊</span><div><b>PHÂN TÍCH Ổ ĐĨA</b><small>Thư mục nào đang chiếm nhiều dung lượng nhất</small></div></div>
      <div class="row2"><button class="btn sm" id="fsUp" title="Lên thư mục cha">⬆</button><input id="fsPath" value="C:\\"><button class="btn sm" id="fsPick">📂</button><button class="btn red shine" id="fsGo">▶ Phân tích</button></div>
      <div id="fsList"></div></div>
    <div class="tcard" style="--ac:#e0262a"><div class="sh"><span class="si">🦠</span><div><b>VIRUS MACRO EXCEL</b><small>File lạ tự mở cùng Excel (XLSTART) và cài đặt macro</small></div></div>
      <div class="row-acts"><button class="btn" id="xlScan">🔍 Quét</button></div><div id="xlBody"></div></div>
    <div class="tcard wide2" style="--ac:#d97706"><div class="sh"><span class="si">🖼️</span><div><b>XÓA METADATA ẢNH</b><small>Bỏ GPS, tên máy chụp, giờ chụp... khỏi ảnh JPG / PNG trước khi gửi đi</small></div></div>
      <div class="row2"><input id="mdPath" placeholder="Thư mục chứa ảnh"><button class="btn sm" id="mdPick">📂</button>
        <label class="ck" style="margin:0;white-space:nowrap"><input type="checkbox" id="mdRec" checked> gồm thư mục con</label><button class="btn red shine" id="mdGo">▶ Xóa metadata</button></div>
      <div class="logl">Ảnh gốc giữ nguyên, ảnh đã xóa metadata lưu vào thư mục con "Da_xoa_metadata". Video chưa hỗ trợ.</div><div id="mdRes"></div></div>
    <div class="tcard" style="--ac:#6b7280"><div class="sh"><span class="si">🗑️</span><div><b>GỠ BỎ</b><small>Nằm trong trang Quản lý</small></div></div>
      <div class="tgrid"><button class="tbtn" data-go="programs"><span class="ti">🗑️</span><span class="tt">Gỡ phần mềm tận gốc</span></button>
        <button class="tbtn" data-go="appx"><span class="ti">🛍️</span><span class="tt">Ứng dụng MS Store</span></button></div></div></div>`;
  const W = $("cleanwrap");
  W.querySelectorAll("[data-go]").forEach(b => b.onclick = () => { MT = b.dataset.go; showPage("manage");
    $("mtabs").querySelector(`[data-t="${MT}"]`).click(); });
  $("clScan").onclick = clScan;
  $("fsGo").onclick = () => fsRun($("fsPath").value);
  $("fsUp").onclick = () => { const p = $("fsPath").value.replace(/\\+$/, ""); const i = p.lastIndexOf("\\"); if (i > 1) fsRun(p.slice(0, i) + (i === 2 ? "\\" : "")); };
  $("fsPick").onclick = async () => { const p = await api("pick_folder_abs"); if (p) $("fsPath").value = p; };
  $("mdPick").onclick = async () => { const p = await api("pick_folder_abs"); if (p) $("mdPath").value = p; };
  $("mdGo").onclick = async () => { const p = $("mdPath").value.trim(); if (!p) return toast("Chọn thư mục ảnh trước", "err");
    const r = await runJob("metadata_strip", "Xóa metadata ảnh", [p, $("mdRec").checked]);
    if (r.ok) $("mdRes").innerHTML = `<div class="okbox">✔ ${esc(r.result.text)} <button class="btn sm" data-of="${esc(r.result.out)}">📂 Mở</button></div>`; };
  W.addEventListener("click", e => { const b = e.target.closest("[data-of]"); if (b) api("open_folder", b.dataset.of); });
  $("xlScan").onclick = xlScan;
  ccLoad();
}
async function clScan() {
  const r = await runJob("clean_scan", "Quét rác hệ thống", []);
  if (!r.ok) return;
  CL = r.result; clRender();
}
function clRender() {
  const sum = () => CL.filter(x => x.sel).reduce((s, x) => s + x.size, 0);
  CL.forEach(x => { if (x.sel === undefined) x.sel = x.def; });
  $("clList").innerHTML = `<div class="cll">${CL.map((x, i) => `<label class="clr"><input type="checkbox" data-i="${i}"${x.sel ? " checked" : ""}><span class="cli">${x.ic}</span>
      <span class="clx"><b>${esc(x.name)}</b><small>${esc(x.sub)}</small></span><span class="cls">${hs(x.size)}</span></label>`).join("")}</div>
    <div class="row-acts"><span class="cnt">Đã chọn: <b id="clSum">${hs(sum())}</b> / ${hs(CL.reduce((s, x) => s + x.size, 0))}</span><span class="sp"></span>
      <button class="btn red shine" id="clGo">🧹 Dọn mục đã chọn</button></div>`;
  $("clList").querySelectorAll("input[data-i]").forEach(c => c.onchange = () => { CL[+c.dataset.i].sel = c.checked; $("clSum").textContent = hs(sum()); });
  $("clGo").onclick = async () => {
    const ids = CL.filter(x => x.sel).map(x => x.id); if (!ids.length) return toast("Chưa chọn mục nào", "err");
    if (ids.includes("browser") && !(await confirmBox("Dọn cache trình duyệt", "Nên tắt trình duyệt trước khi dọn cache (mật khẩu, lịch sử, dấu trang không bị xóa).", "Tiếp tục", false))) return;
    const r = await runJob("clean_run", "Dọn rác hệ thống", [ids]);
    if (r.ok) { toast(r.result.text); clScan(); }
  };
}
async function fsRun(path) {
  $("fsPath").value = path;
  const r = await runJob("folder_sizes", "Phân tích " + path, [path]);
  if (!r.ok) return;
  FS = r.result; const max = Math.max(1, ...FS.items.map(x => x.size));
  $("fsList").innerHTML = `<div class="logl">${esc(FS.path)} · tổng ${hs(FS.total)} · bấm thư mục để xem bên trong</div><div class="fsl">${FS.items.map((x, i) =>
    `<div class="fsr${x.dir ? " dir" : ""}" data-i="${i}"><span class="fsn">${x.dir ? "📁" : "📄"} ${esc(x.name)}</span>
      <div class="bar"><div class="${x.size / max > .6 ? "b-red" : x.size / max > .25 ? "b-orange" : "b-green"}" style="width:${Math.max(1, x.size / max * 100)}%"></div></div>
      <span class="fss">${hs(x.size)}</span><button class="btn sm" data-of="${esc(x.path)}">📂</button></div>`).join("")}</div>`;
  $("fsList").querySelectorAll(".fsr.dir .fsn").forEach(n => n.onclick = () => fsRun(FS.items[+n.parentElement.dataset.i].path));
}
async function ccLoad() {
  const c = await m("capcut_info");
  $("ccBody").innerHTML = !c.found ? '<div class="logl">Máy chưa cài CapCut PC.</div>' :
    `<div class="big2">${hs(c.size)}</div><div class="logl" style="margin:2px 0 10px">cache${c.running ? " · CapCut đang mở (sẽ được tắt khi dọn)" : ""}</div>
     <button class="btn red shine" id="ccGo"${c.size ? "" : " disabled"}>🧹 Xóa cache CapCut</button>`;
  if ($("ccGo")) $("ccGo").onclick = async () => {
    if (!(await confirmBox("Xóa cache CapCut", `Xóa ${hs(c.size)} cache của CapCut?${c.running ? "\nCapCut đang mở sẽ được tắt (lưu dự án trước)." : ""}\nDự án của bạn không bị xóa.`, "🧹 Xóa"))) return;
    const r = await runJob("capcut_clean", "Xóa cache CapCut", []); if (r.ok) toast(r.result.text); ccLoad(); };
}
async function xlScan() {
  const r = await m("xlstart_scan");
  const vbaBad = r.vba === 1;
  $("xlBody").innerHTML = (vbaBad ? `<div class="warnbox">⚠ Excel đang <b>cho chạy mọi macro</b> (nguy hiểm). <button class="btn sm green" id="xlSafe">✓ Đặt lại an toàn</button></div>` : "") +
    (r.files.length ? `<div class="lolist">${r.files.map((f, i) => `<label class="ck lo st"><input type="checkbox" data-i="${i}"${/nghi virus/.test(f.note) ? " checked" : ""}>
        <span class="lp">${esc(f.path.split("\\").pop())}</span><em>${hs(f.size)} · ${esc(f.date)} · ${esc(f.note)}</em></label>`).join("")}</div>
      <div class="row-acts"><button class="btn out" id="xlQ">🧪 Cách ly file đã chọn</button></div>` : '<div class="okbox">✔ Không có file nào tự mở cùng Excel.</div>');
  if ($("xlSafe")) $("xlSafe").onclick = async () => { await m("excel_safe_macro"); toast("Đã đặt Excel: tắt macro, có thông báo"); xlScan(); };
  if ($("xlQ")) $("xlQ").onclick = async () => { const sel = [...$("xlBody").querySelectorAll("input[data-i]:checked")].map(x => r.files[+x.dataset.i].path);
    if (!sel.length) return toast("Chưa chọn file", "err");
    const q = await m("xlstart_quarantine", sel); toast(`Đã cách ly ${q.done} file vào Data\\Backup`); xlScan(); };
}

/* =============================================================== SAO LƯU */
let BK = null;
function destVal() { return $("bkDest").value.trim(); }
async function backShow() {
  if ($("backwrap").dataset.ok) return;
  $("backwrap").dataset.ok = 1;
  $("backwrap").innerHTML = '<div class="empty"><span class="spin"></span> Đang đọc dữ liệu cần sao lưu...</div>';
  BK = await m("backup_info");
  const other = (BK.drives || []).sort((a, b) => b.free - a.free)[0];
  $("backwrap").innerHTML = `<div class="destbar"><b>💾 NƠI LƯU BẢN SAO LƯU</b>
      ${(BK.drives || []).map(d => `<span class="chip cp" data-d="${d.d}">${d.d}: <em>${hs(d.free)} trống</em></span>`).join("") || '<span class="logl" style="margin:0">Máy chỉ có ổ C — nên cắm ổ USB / ổ cứng ngoài để lưu</span>'}
      <input id="bkDest" value="${other ? other.d + ":\\WinAIO_SaoLuu" : ""}" placeholder="D:\\WinAIO_SaoLuu"><button class="btn sm" id="bkPick">📂</button></div>
    <div class="cgrid">
      <div class="tcard wide2" style="--ac:#0f8fd8"><div class="sh"><span class="si">🗂️</span><div><b>THƯ MỤC NGƯỜI DÙNG</b><small>Desktop, Tài liệu, Tải về, Ảnh, Video, Nhạc của ${esc(BK.pc)}</small></div></div>
        <div class="udl">${BK.dirs.map(d => `<label class="clr"><input type="checkbox" data-k="${d.key}"${d.exists && d.key !== "Downloads" ? " checked" : ""}${d.exists ? "" : " disabled"}>
          <span class="cli">${d.ic}</span><span class="clx"><b>${d.name}</b><small>${esc(d.path)}</small></span><span class="cls">${hs(d.size)}</span></label>`).join("")}</div>
        <div class="row-acts"><span class="cnt">Đã chọn: <b id="udSum"></b></span><span class="sp"></span><button class="btn" id="udRes">♻ Khôi phục...</button><button class="btn red shine" id="udGo">💾 Sao lưu</button></div></div>
      <div class="tcard" style="--ac:#0068ff"><div class="sh"><span class="si">💬</span><div><b>ZALO PC</b><small>Tin nhắn, ảnh, file đã nhận</small></div></div><div id="zlBody"><div class="logl"><span class="spin"></span></div></div></div>
      <div class="tcard wide2" style="--ac:#d97706"><div class="sh"><span class="si">🌐</span><div><b>TRÌNH DUYỆT</b><small>Dấu trang, tiện ích, mật khẩu, lịch sử, cài đặt (bỏ cache cho nhẹ)</small></div></div><div id="brBody"></div></div>
      <div class="tcard" style="--ac:#16a34a"><div class="sh"><span class="si">👥</span><div><b>ZALO NHIỀU TÀI KHOẢN</b><small>Mỗi tài khoản 1 cửa sổ Zalo riêng, dữ liệu tách biệt</small></div></div><div id="zmBody"></div></div></div>`;
  const W = $("backwrap");
  W.querySelectorAll("[data-d]").forEach(c => c.onclick = () => { $("bkDest").value = c.dataset.d + ":\\WinAIO_SaoLuu"; });
  $("bkPick").onclick = async () => { const p = await api("pick_folder_abs"); if (p) $("bkDest").value = p; };
  const udSum = () => { $("udSum").textContent = hs(BK.dirs.filter(d => W.querySelector(`input[data-k="${d.key}"]`).checked).reduce((s, d) => s + d.size, 0)); };
  W.querySelectorAll("input[data-k]").forEach(c => c.onchange = udSum); udSum();
  $("udGo").onclick = async () => {
    const keys = [...W.querySelectorAll("input[data-k]:checked")].map(x => x.dataset.k);
    if (!keys.length) return toast("Chưa chọn thư mục", "err"); if (!destVal()) return toast("Chọn nơi lưu trước", "err");
    const r = await runJob("backup_user", "Sao lưu thư mục người dùng", [keys, destVal()]);
    if (r.ok) okDone(r.result);
  };
  $("udRes").onclick = async () => {
    const p = await pickOrAsk("Thư mục bản sao lưu (SaoLuu_...)"); if (!p) return;
    if (!(await confirmBox("Khôi phục thư mục người dùng", `Chép dữ liệu từ\n${p}\nvề Desktop, Tài liệu, Ảnh... của máy này?\nFile trùng tên đang có sẽ được giữ nguyên.`, "♻ Khôi phục", false))) return;
    const r = await runJob("restore_user", "Khôi phục thư mục người dùng", [p]); if (r.ok) toast(r.result.text);
  };
  zlLoad(); brLoad();
}
async function pickOrAsk(label) {
  let p = await api("pick_folder_abs");
  if (!p && !window.pywebview) p = await promptBox("Chọn thư mục", label + ":", "");
  return p;
}
function okDone(res) {
  dialog({title: "Xong", body: `<div class="okbox">✔ ${esc(res.text)}</div>`,
    buttons: [{text: "📂 Mở thư mục", click: () => { api("open_folder", res.dest); return true; }}, {text: "OK", cls: "red", def: true}]});
}
async function zlLoad() {
  const z = await m("zalo_info");
  $("zlBody").innerHTML = !z.installed ? '<div class="logl">Máy chưa cài Zalo PC.</div>' :
    `<div class="kv"><div class="k">Dữ liệu</div><div class="v">${hs(z.data)}</div><div class="k">File đã nhận</div><div class="v">${hs(z.files)}</div>
      <div class="k">Trạng thái</div><div class="v">${z.running ? pill("Đang mở", "t-skip") : pill("Đã tắt", "t-done")}</div></div>
     <label class="ck"><input type="checkbox" id="zlClose" checked> Tự tắt Zalo trước khi sao lưu / khôi phục</label>
     <div class="row-acts"><button class="btn" id="zlRes">♻ Khôi phục...</button><button class="btn red shine" id="zlGo">💾 Sao lưu Zalo</button></div>`;
  if ($("zlGo")) {
    $("zlGo").onclick = async () => { if (!destVal()) return toast("Chọn nơi lưu trước", "err");
      const r = await runJob("zalo_backup", "Sao lưu Zalo", [destVal(), $("zlClose").checked]); if (r.ok) okDone(r.result); zlLoad(); };
    $("zlRes").onclick = async () => { const p = await pickOrAsk("Thư mục bản sao lưu Zalo (Zalo_...)"); if (!p) return;
      if (!(await confirmBox("Khôi phục Zalo", "Thay dữ liệu Zalo trên máy bằng bản sao lưu này?\nDữ liệu hiện tại được giữ lại (đổi tên), không bị xóa.", "♻ Khôi phục", false))) return;
      const r = await runJob("zalo_restore", "Khôi phục Zalo", [p, true]); if (r.ok) toast(r.result.text); zlLoad(); };
  }
  $("zmBody").innerHTML = `${(z.profiles || []).map(p => `<div class="zmr"><span>👤 <b>${esc(p.name)}</b> <em>${hs(p.size)}</em></span><span class="sp"></span>
      <button class="btn sm green" data-zo="${esc(p.name)}">▶ Mở</button><button class="btn sm out" data-zd="${esc(p.name)}">✕</button></div>`).join("") || '<div class="logl">Chưa có tài khoản phụ nào.</div>'}
    <div class="row2" style="margin-top:10px"><input id="zmName" placeholder="Tên tài khoản (VD: Shop, Công ty)"><button class="btn green" id="zmAdd">＋ Mở Zalo mới</button></div>
    <div class="logl">Zalo chính vẫn dùng bình thường. Mỗi tài khoản phụ đăng nhập 1 lần, dữ liệu lưu trong Data\\ZaloTaiKhoan.</div>`;
  $("zmAdd").onclick = async () => { const n = $("zmName").value.trim(); if (!n) return toast("Nhập tên tài khoản", "err");
    const r = await m("zalo_open", n); if (r) return errBox("Zalo nhiều tài khoản", r); toast("Đang mở Zalo cho tài khoản " + n); setTimeout(zlLoad, 1500); };
  $("zmBody").onclick = async e => {
    const o = e.target.closest("[data-zo]"), d = e.target.closest("[data-zd]");
    if (o) { const r = await m("zalo_open", o.dataset.zo); r ? errBox("Zalo", r) : toast("Đang mở Zalo: " + o.dataset.zo); }
    if (d && await confirmBox("Xóa tài khoản phụ", `Xóa dữ liệu Zalo của "${d.dataset.zd}" (tin nhắn lưu trên máy của tài khoản này)?`, "🗑 Xóa")) { await m("zalo_profile_delete", d.dataset.zd); zlLoad(); }
  };
}
async function brLoad() {
  const B = await m("browsers_info");
  $("brBody").innerHTML = `<div class="brl">${B.map(b => `<label class="clr${b.found ? "" : " off"}"><input type="checkbox" data-b="${b.id}"${b.found ? " checked" : " disabled"}>
      <span class="clx"><b>${esc(b.name)}</b><small>${b.found ? `${b.profiles} hồ sơ${b.running ? " · đang mở" : ""}` : "chưa cài"}</small></span></label>`).join("")}</div>
    <label class="ck"><input type="checkbox" id="brClose" checked> Tự tắt trình duyệt trước khi sao lưu / khôi phục</label>
    <div class="row-acts"><span class="logl grow">Mật khẩu đã lưu chỉ dùng được khi khôi phục trên cùng tài khoản Windows.</span>
      <button class="btn" id="brRes">♻ Khôi phục...</button><button class="btn red shine" id="brGo">💾 Sao lưu trình duyệt</button></div>`;
  $("brGo").onclick = async () => {
    const ids = [...$("brBody").querySelectorAll("input[data-b]:checked")].map(x => x.dataset.b);
    if (!ids.length) return toast("Chưa chọn trình duyệt", "err"); if (!destVal()) return toast("Chọn nơi lưu trước", "err");
    const r = await runJob("browser_backup", "Sao lưu trình duyệt", [ids, destVal(), $("brClose").checked]); if (r.ok) okDone(r.result); brLoad(); };
  $("brRes").onclick = async () => { const p = await pickOrAsk("Thư mục bản sao lưu trình duyệt (TrinhDuyet_...)"); if (!p) return;
    if (!(await confirmBox("Khôi phục trình duyệt", "Thay hồ sơ trình duyệt trên máy bằng bản sao lưu này?\nHồ sơ hiện tại được giữ lại (đổi tên), không bị xóa.", "♻ Khôi phục", false))) return;
    const r = await runJob("browser_restore", "Khôi phục trình duyệt", [p, $("brClose").checked]); if (r.ok) toast(r.result.text); brLoad(); };
}

/* =============================================================== KHO ISO WIN */
function isoShow() {
  const W = $("isowrap");
  if (W.dataset.ok) return;
  W.dataset.ok = 1;
  const langs = (INIT.iso_langs || ["English"]).map(l => `<option>${esc(l)}</option>`).join("");
  const VER = [["11", "Windows 11", "Bản mới nhất · Home / Pro / Education", "🪟"], ["10", "Windows 10", "22H2 · Home / Pro / Education", "🪟"]];
  W.innerHTML = `<div class="tcard isosec" style="--ac:#0f8fd8"><div class="sh"><span class="si">💿</span><div><b>TẢI ISO WINDOWS</b>
        <small>Chọn bản cần tải rồi bấm Tải - tool tự lấy link gốc của Microsoft và tải về, không phải mở web</small></div></div>
      <div class="isover">${VER.map((v, i) => `<label class="isov${i ? "" : " on"}"><input type="radio" name="isoW" value="${v[0]}"${i ? "" : " checked"}>
        <span class="ti">${v[3]}</span><span><b>${v[1]}</b><small>${v[2]}</small></span></label>`).join("")}</div>
      <div class="isoopt">
        <label>Ngôn ngữ <select id="isoLang">${langs}</select></label>
        <label>Kiến trúc <select id="isoArch"><option value="x64">64-bit (x64)</option></select></label>
        <label class="grow">Lưu vào <span class="row2"><input id="isoDest" placeholder="Data\\ISO (kế bên tool)"><button class="btn sm" id="isoDPick">📂</button></span></label>
      </div>
      <div class="row-acts"><span class="logl grow">File ISO khoảng 5 - 7 GB. Đang tải bị ngắt / bấm Dừng thì lần sau bấm Tải là tải tiếp từ chỗ dừng.
        Windows tiếng Việt: chọn English rồi cài gói ngôn ngữ Tiếng Việt trong Cài đặt.</span>
        <button class="btn" id="isoLink">🔗 Chỉ lấy link (dán vào IDM)</button><button class="btn red shine" id="isoGo">⬇ Tải ISO</button></div>
      <div id="isoDone"></div></div>
    <div class="tcard isosec" style="--ac:#7c3aed"><div class="sh"><span class="si">🌐</span><div><b>MASSGRAVE.DEV</b>
        <small>Bấm để mở trang tải của massgrave.dev - file lưu ở máy chủ bên thứ ba, tải xong nên kiểm tra SHA-256</small></div></div>
      <div class="isogrid">${(INIT.iso_mg || []).map(it => `<button class="tbtn isob" data-url="${esc(it.url)}" title="${esc(it.url)}"><span class="ti">${esc(it.icon)}</span>
        <span class="tt"><b>${esc(it.name)}</b>${it.note ? `<small>${esc(it.note)}</small>` : ""}</span></button>`).join("")}</div></div>
    <div class="tcard isosec" style="--ac:#d97706"><div class="sh"><span class="si">🔐</span><div><b>KIỂM TRA FILE ISO (SHA-256)</b><small>Tính mã SHA-256 rồi so với mã công bố - trùng là file nguyên gốc, không bị sửa</small></div></div>
      <div class="row2"><input id="isoFile" placeholder="Đường dẫn file .iso"><button class="btn sm" id="isoPick">📂 Chọn file</button><button class="btn red shine" id="isoHash">🔐 Kiểm tra SHA-256</button></div>
      <div class="row2" style="margin-top:8px"><input id="isoExpect" placeholder="Dán mã SHA-256 công bố để so (không bắt buộc)"></div>
      <div id="isoRes"></div></div>`;
  W.querySelectorAll("[data-url]").forEach(b => b.onclick = () => { api("quick", b.dataset.url); toast("🌐 Đang mở " + b.querySelector("b").textContent); });
  const ver = () => W.querySelector('input[name="isoW"]:checked').value;
  const setArch = () => { $("isoArch").innerHTML = ver() === "10" ? '<option value="x64">64-bit (x64)</option><option value="x86">32-bit (x86)</option>' : '<option value="x64">64-bit (x64)</option>'; };
  W.querySelectorAll('input[name="isoW"]').forEach(r => r.onchange = () => { W.querySelectorAll(".isov").forEach(l => l.classList.toggle("on", l.contains(W.querySelector('input[name="isoW"]:checked')))); setArch(); });
  $("isoDPick").onclick = async () => { const p = await api("pick_folder_abs"); if (p) $("isoDest").value = p; };
  const args = () => [ver(), $("isoLang").value, $("isoArch").value, $("isoDest").value.trim()];
  $("isoGo").onclick = async () => {
    const a = args(), r = await runJob("iso_download", `Tải Windows ${a[0]} · ${a[1]} · ${a[2]}`, a);
    if (!r.ok) return;
    const x = r.result;
    $("isoDone").innerHTML = `<div class="okbox">✔ ${esc(x.text)} (${hs(x.size)}) <button class="btn sm" data-of="${esc(x.dest)}">📂 Mở thư mục</button>
      <button class="btn sm" id="isoChk">🔐 Kiểm tra SHA-256</button></div>`;
    $("isoDone").querySelector("[data-of]").onclick = e => api("open_folder", e.target.dataset.of);
    $("isoChk").onclick = () => { $("isoFile").value = x.path; $("isoHash").click(); };
  };
  $("isoLink").onclick = async () => {
    const a = args(); a[3] = "__link__";
    const r = await runJob("iso_download", `Lấy link Windows ${a[0]} · ${a[1]}`, a);
    if (!r.ok) return;
    copyLocal(r.result.url);
    $("isoDone").innerHTML = `<div class="okbox">✔ Đã chép link ${esc(r.result.name)} - dán vào IDM / trình duyệt (link dùng được 24 giờ).</div>`;
  };
  $("isoPick").onclick = async () => { const p = await api("pick_file_abs"); if (p) $("isoFile").value = p; };
  $("isoHash").onclick = async () => {
    const p = $("isoFile").value.trim(); if (!p) return toast("Chọn file ISO trước", "err");
    const r = await runJob("sha256_file", "Kiểm tra SHA-256", [p]);
    if (!r.ok) return;
    const x = r.result, exp = $("isoExpect").value.trim().toUpperCase().replace(/\s+/g, "");
    const cmp = !exp ? "" : exp === x.sha256 ? '<div class="okbox">✔ TRÙNG KHỚP - file đúng bản gốc.</div>' : '<div class="warnbox">✖ KHÔNG KHỚP - file bị lỗi khi tải hoặc không phải bản gốc. Nên tải lại.</div>';
    $("isoRes").innerHTML = `<div class="kv" style="margin-top:10px"><div class="k">File</div><div class="v">${esc(x.name)} · ${hs(x.size)}</div>
      <div class="k">SHA-256</div><div class="v"><code class="hash">${esc(x.sha256)}</code> <button class="btn sm" id="isoCopy">📋 Chép</button></div></div>${cmp}`;
    $("isoCopy").onclick = () => { copyLocal(x.sha256); toast("Đã chép mã SHA-256"); };
  };
}

/* =============================================================== WEB (nút mở trang web hay dùng) */
let WEB = [];
async function webShow() {
  WEB = await api("web_list");
  const W = $("webwrap"), groups = [...new Set(WEB.map(w => w.grp || "HAY DÙNG"))];
  const colors = ["#0f8fd8", "#16a34a", "#d97706", "#7c3aed", "#e0262a", "#0891b2"];
  W.innerHTML = (groups.length ? groups : ["HAY DÙNG"]).map((g, gi) => `<div class="tcard isosec" style="--ac:${colors[gi % colors.length]}">
      <div class="sh"><span class="si">🌐</span><div><b>${esc(g)}</b><small>${WEB.filter(w => (w.grp || "HAY DÙNG") === g).length} trang</small></div>
        <span class="sp"></span><button class="btn sm adm" data-addg="${esc(g)}">＋ Thêm link</button></div>
      <div class="webgrid">${WEB.filter(w => (w.grp || "HAY DÙNG") === g).map(w => `<div class="webi" data-id="${w.id}">
        <button class="tbtn webb${w.url ? "" : " wempty"}" data-open="${w.id}" title="${esc(w.url || "Nút trống - bật Admin, bấm ✎ để gắn link")}"><span class="ti">${esc(w.icon || "🌐")}</span>
          <span class="tt"><b>${esc(w.name || (w.url ? w.url.replace(/^https?:\/\/(www\.)?/, "").split("/")[0] : "(trống)"))}</b><small>${w.url ? esc(w.url.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")) : "chưa có link"}</small></span></button>
        <span class="webed adm"><button class="ed xs" data-mv="-1" title="Lên trước">◀</button><button class="ed xs" data-mv="1" title="Ra sau">▶</button>
          <button class="ed xs" data-ed="1" title="Sửa">✎</button></span></div>`).join("") || '<div class="logl">(chưa có link)</div>'}</div></div>`).join("")
    + `<div class="row-acts adm"><span class="sp"></span><button class="btn green" data-addg="">＋ Thêm nhóm / link mới</button></div>
       <div class="logl nadm">Bật Admin (🔒 góc trên) để thêm, sửa, xóa link.</div>`;
  W.onclick = async e => {
    const o = e.target.closest("[data-open]"), a = e.target.closest("[data-addg]"), mv = e.target.closest("[data-mv]"), ed = e.target.closest("[data-ed]");
    if (o) { const w = WEB.find(x => x.id === +o.dataset.open); if (w && w.url) { api("quick", w.url); toast("🌐 Đang mở " + w.name); } else toast("Link này chưa có địa chỉ - Admin bấm ✎ để thêm", "err"); return; }
    if (a) return webEdit({grp: a.dataset.addg});
    const id = +(e.target.closest(".webi") || {dataset: {}}).dataset.id;
    if (mv) { if (!(await api("web_move", id, +mv.dataset.mv))) toast("Hết chỗ để di chuyển", "err"); return webShow(); }
    if (ed) return webEdit(WEB.find(x => x.id === id));
  };
}
async function webEdit(w) {
  w = w || {};
  const groups = [...new Set(WEB.map(x => x.grp))];
  const r = await dialog({title: w.id ? "Sửa link web" : "Thêm link web", width: 560, body: `
      <div class="frm"><label>Biểu tượng <input id="wIc" value="${esc(w.icon || "🌐")}" style="width:80px"></label>
      <label>Tên nút <input id="wNm" value="${esc(w.name || "")}" placeholder="VD: Ngân hàng"></label>
      <label>Địa chỉ web <input id="wUrl" value="${esc(w.url || "")}" placeholder="https://..."></label>
      <label>Nhóm <input id="wGr" list="wGrL" value="${esc(w.grp || "HAY DÙNG")}" placeholder="HAY DÙNG"><datalist id="wGrL">${groups.map(g => `<option value="${esc(g)}">`).join("")}</datalist></label>
      <div class="logl">Gõ tên nhóm mới để tạo nhóm mới. Biểu tượng là emoji (Win + . để chọn).</div><div class="err"></div></div>`,
    left: w.id ? '<button class="btn sm out" id="wDel">🗑 Xóa</button>' : "",
    buttons: [{text: "Hủy", value: null}, {text: "💾 Lưu", cls: "red", def: true, click: c => {
      const url = c.q("#wUrl").value.trim(); if (!url) { c.err && c.err("Nhập địa chỉ web"); return false; }
      return {id: w.id, icon: c.q("#wIc").value, name: c.q("#wNm").value, url, grp: c.q("#wGr").value}; }}],
    onOpen: c => { const d = c.q("#wDel"); if (d) d.onclick = async () => {
      if (await confirmBox("Xóa link", `Xóa "${w.name}"?`, "🗑 Xóa")) { await api("web_delete", w.id); c.close(null); toast("Đã xóa"); webShow(); } }; }});
  if (!r) return;
  await api("web_save", r); toast("Đã lưu link"); webShow();
}


/* =============================================================== CẬP NHẬT APP (winget upgrade) */
let UP = null, upSel = new Set();
async function upLoad(force) {
  const P = $("mp-upgrade");
  P.innerHTML = `<div class="mbar"><button class="btn" id="upChk">⟳ Kiểm tra bản mới</button>
      <button class="btn" id="upSelB">⬆ Cập nhật mục đã chọn</button><button class="btn red shine" id="upAll">⬆⬆ Cập nhật tất cả</button>
      <span class="cnt" id="upCnt"></span><span class="sp"></span>⌕ <input type="search" id="upQ" placeholder="tìm..." style="width:200px"></div>
    <div id="upTbl">${tbl([["Tên"]], "", UP ? "" : 'Bấm "⟳ Kiểm tra bản mới" để hỏi winget phần mềm nào trên máy có phiên bản mới')}</div>
    <div class="logl">Kiểm tra mọi phần mềm đã cài trên máy (không chỉ cài từ tool) mà kho winget có bản mới hơn. Cập nhật chạy im lặng; nên đóng phần mềm đó trước khi cập nhật.</div>`;
  $("upChk").onclick = () => upCheck();
  $("upQ").oninput = upRender;
  $("upSelB").onclick = () => upRun(UP ? UP.filter(x => upSel.has(x.id)) : []);
  $("upAll").onclick = () => upRun(UP || []);
  if (UP) upRender(); else upCheck();
}
async function upCheck() {
  const r = await runJob("wg_upgrades", "Kiểm tra phần mềm có bản mới", []);
  if (!r.ok) return;
  UP = r.result; upSel = new Set(UP.map(x => x.id));
  api("set_upg_n", UP.length); setUpgBadge(UP.length);
  upRender();
}
function upRender() {
  if (!UP) return;
  const q = norm($("upQ").value), L = UP.filter(x => !q || norm(x.name + " " + x.id).includes(q));
  $("upCnt").textContent = UP.length ? `${UP.length} phần mềm có bản mới · đã chọn ${upSel.size}` : "";
  $("upTbl").innerHTML = tbl([["", "34px"], ["Phần mềm"], ["ID winget", "24%"], ["Đang dùng", "130px"], ["Bản mới", "130px"], ["", "120px"]],
    L.map(x => `<tr data-id="${esc(x.id)}" class="${upSel.has(x.id) ? "sel" : ""}"><td><span class="chk${upSel.has(x.id) ? " on" : ""}"></span></td>
      <td><b>${esc(x.name)}</b></td><td class="path">${esc(x.id)}</td><td>${esc(x.ver)}</td>
      <td><span class="pill t-new">${esc(x.new)}</span></td><td><button class="btn sm green" data-up="1">⬆ Cập nhật</button></td></tr>`).join(""),
    "✔ Tất cả phần mềm đã là bản mới nhất");
  $("upTbl").querySelector("tbody").onclick = e => {
    const tr = e.target.closest("tr[data-id]"); if (!tr) return;
    const x = UP.find(u => u.id === tr.dataset.id);
    if (e.target.closest("[data-up]")) return upRun([x]);
    upSel.has(x.id) ? upSel.delete(x.id) : upSel.add(x.id); upRender();
  };
}
async function upRun(list) {
  if (!list.length) return toast("Chưa chọn phần mềm nào", "err");
  if (list.length > 1 && !(await confirmBox("Cập nhật phần mềm", `Cập nhật ${list.length} phần mềm?\n${list.map(x => `• ${x.name}: ${x.ver} → ${x.new}`).join("\n")}\n\nNên đóng các phần mềm này trước.`, "⬆ Cập nhật", false))) return;
  const r = await runJob("wg_upgrade", list.length > 1 ? `Cập nhật ${list.length} phần mềm` : `Cập nhật ${list[0].name}`, [list]);
  if (!r.ok) return;
  toast(r.result.text, r.result.errs.length ? "err" : "");
  if (r.result.errs.length) errBox("Có phần mềm chưa cập nhật được", r.result.errs.join("\n"));
  UP = UP.filter(x => !r.result.done.includes(x.id)); r.result.done.forEach(id => upSel.delete(id));
  api("set_upg_n", UP.length); setUpgBadge(UP.length); upRender();
}
