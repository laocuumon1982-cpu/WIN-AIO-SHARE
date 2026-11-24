/* Win AIO by Duy Anh - v2.7: Kho bộ cài Mac + Kho iOS (IPSW) */
const fsize = n => n ? hs(n) : "—";
const linkBtn = url => `<button class="btn sm" data-link="${esc(url)}" title="Chép link để dán vào IDM / trình duyệt">🔗 Link</button>`;
function bindLinks(el) {
  el.addEventListener("click", e => { const b = e.target.closest("[data-link]"); if (b) { copyLocal(b.dataset.link); toast("Đã chép link - dán vào IDM / trình duyệt"); } });
}
async function dlDone(r) {
  if (!r.ok) return;
  dialog({title: "Tải xong", width: 640, body: `<div class="okbox">✔ ${esc(r.result.text)}</div>`,
    buttons: [{text: "📂 Mở thư mục", click: () => { api("open_folder", r.result.dest); return true; }}, {text: "OK", cls: "red", def: true}]});
}

/* =============================================================== KHO BỘ CÀI MAC */
let MAC = null, macFam = "", macAll = false;
async function macShow(force) {
  const W = $("macwrap");
  if (W.dataset.ok && !force) return;
  W.dataset.ok = 1;
  W.innerHTML = `<div class="tcard isosec" style="--ac:#6b7280"><div class="sh"><span class="si">🍎</span><div><b>TẢI BỘ CÀI macOS</b>
      <small>Giống trình tải của macUSB: lấy thẳng từ máy chủ Apple (danh mục Software Update + trang hỗ trợ Apple) - không qua web trung gian</small></div>
      <span class="sp"></span><button class="btn sm" id="macRef">⟳ Làm mới danh sách</button></div>
    <div class="isoopt"><label class="grow">Lưu vào <span class="row2"><input id="macDest" placeholder="Data\\macOS (kế bên tool)"><button class="btn sm" id="macPick">📂</button></span></label>
      <label class="ck" style="align-self:end"><input type="checkbox" id="macAllV"${macAll ? " checked" : ""}> Hiện cả bản cũ của từng đời</label></div>
    <div id="macFams" class="macfams"></div><div id="macTbl"><div class="empty"><span class="spin"></span> Đang đọc danh mục bộ cài của Apple...</div></div></div>
    <div class="tcard isosec" style="--ac:#0f8fd8"><div class="sh"><span class="si">💡</span><div><b>DÙNG FILE ĐÃ TẢI THẾ NÀO?</b><small>Bộ cài macOS chỉ tạo USB được trên máy Mac</small></div></div>
      <ul class="flist"><li><b>macOS 11 trở lên</b> (InstallAssistant.pkg): chép sang Mac, mở file → có "Install macOS ..." trong Applications → dùng <b>macUSB</b> (hoặc lệnh createinstallmedia) tạo USB.</li>
        <li><b>macOS 10.7 - 10.12</b> (.dmg của Apple): mở .dmg, chạy gói cài bên trong → có ứng dụng cài đặt → macUSB tạo USB.</li>
        <li><b>macOS 10.13 - 10.15</b>: Apple chia 3 file, tool tải đủ vào 1 thư mục → chép cả thư mục sang Mac để ráp (macUSB tự ráp khi dùng trình tải của nó).</li>
        <li>Dung lượng lớn (5 - 17 GB) - đang tải bị ngắt / bấm Dừng thì bấm Tải lại là tải tiếp. Có thể bấm 🔗 Link để tải bằng IDM.</li></ul></div>`;
  $("macRef").onclick = () => macLoad(true);
  $("macPick").onclick = async () => { const p = await api("pick_folder_abs"); if (p) $("macDest").value = p; };
  $("macAllV").onchange = e => { macAll = e.target.checked; macRender(); };
  bindLinks(W);
  $("macTbl").onclick = async e => {
    const b = e.target.closest("[data-dl]"); if (!b) return;
    const it = MAC.find(x => x.id === b.dataset.dl);
    const r = await runJob("mac_download", `Tải ${it.name} ${it.version}`, [it.id, $("macDest").value.trim()]); dlDone(r);
  };
  $("macFams").onclick = e => { const c = e.target.closest("[data-fam]"); if (!c) return; macFam = macFam === c.dataset.fam ? "" : c.dataset.fam; macRender(); };
  macLoad(false);
}
async function macLoad(refresh) {
  if (MAC && !refresh) return macRender();
  const r = await runJob("mac_list", "Đọc danh mục bộ cài macOS của Apple", [refresh]);
  if (!r.ok) { $("macTbl").innerHTML = '<div class="warnbox">Không đọc được danh mục của Apple. Kiểm tra mạng rồi bấm ⟳ Làm mới.</div>'; return; }
  MAC = r.result; macRender();
}
function macRender() {
  if (!MAC) return;
  const fams = [...new Set(MAC.map(x => x.family))];
  const latest = f => MAC.find(x => x.family === f);
  $("macFams").innerHTML = fams.map(f => { const x = latest(f);
    return `<label class="isov${macFam === f ? " on" : ""}" data-fam="${esc(f)}"><span class="ti">🍎</span><span><b>${esc(f)}</b><small>${esc(x.version)}${x.build ? " · " + esc(x.build) : ""}${x.size ? " · " + hs(x.size) : ""}</small></span></label>`; }).join("");
  let L = MAC.filter(x => !macFam || x.family === macFam);
  if (!macAll && !macFam) L = fams.map(latest);
  const kind = x => x.kind === "pkg" ? pill("InstallAssistant.pkg", "t-done") : x.kind === "dmg" ? pill("Ảnh .dmg của Apple", "t-new") : pill("3 file (ráp trên Mac)", "t-skip");
  $("macTbl").innerHTML = tbl([["Hệ điều hành"], ["Phiên bản", "110px"], ["Build", "100px"], ["Ngày", "100px"], ["Dung lượng", "100px"], ["Dạng", "190px"], ["", "170px"]],
    L.map(x => `<tr><td><b>${esc(x.name)}</b></td><td>${esc(x.version)}</td><td>${esc(x.build || "—")}</td><td>${esc(x.date || "")}</td><td>${fsize(x.size)}</td>
      <td>${kind(x)}</td><td>${x.files.length === 1 ? linkBtn(x.files[0].url) : ""} <button class="btn sm red" data-dl="${esc(x.id)}">⬇ Tải</button></td></tr>`).join(""),
    "Không có bộ cài nào");
}

/* =============================================================== KHO iOS (IPSW) */
let IDEV = null, iCat = "iPhone", iDev = null, iSigned = false;
async function iosShow() {
  const W = $("ioswrap");
  if (W.dataset.ok) return;
  W.dataset.ok = 1;
  W.innerHTML = `<div class="tcard isosec" style="--ac:#0f8fd8"><div class="sh"><span class="si">📱</span><div><b>FIRMWARE iOS / iPadOS / macOS (IPSW)</b>
      <small>Danh sách theo ipsw.me · file tải thẳng từ máy chủ Apple · dùng để khôi phục (Restore) bằng iTunes / Finder / 3uTools</small></div></div>
    <div class="isoopt"><label>Loại <span class="row2" id="iCats"></span></label>
      <label class="grow">Tìm máy <input type="search" id="iQ" placeholder="VD: 15 Pro Max, iPad Air, iPhone15,2..."></label>
      <label class="grow">Lưu vào <span class="row2"><input id="iDest" placeholder="Data\\iOS (kế bên tool)"><button class="btn sm" id="iPick">📂</button></span></label></div>
    <div class="idevs" id="iDevs"><div class="empty"><span class="spin"></span> Đang tải danh sách thiết bị...</div></div></div>
    <div class="tcard isosec" style="--ac:#e0262a"><div class="sh"><span class="si">📲</span><div><b>3uTools (64-bit)</b>
      <small>Quản lý iPhone / iPad, flash / khôi phục iOS, sao lưu, kiểm tra máy - luôn lấy bản mới nhất trên trang chủ 3u.com</small></div>
      <span class="sp"></span><button class="btn red shine" id="i3u">⬇ Tải &amp; cài 3uTools</button></div></div>
    <div class="tcard isosec" style="--ac:#16a34a" id="iFwC" hidden><div class="sh"><span class="si">📦</span><div><b id="iFwT"></b><small id="iFwS"></small></div>
      <span class="sp"></span><label class="ck"><input type="checkbox" id="iSig"> Chỉ bản Apple còn ký (cài được)</label></div><div id="iFw"></div>
      <div class="logl">Chỉ bản <b>CÒN KÝ</b> mới khôi phục được bằng iTunes / Finder. Bản hết ký chỉ để lưu trữ. Khôi phục: giữ Shift (Windows) / Option (Mac) rồi bấm Restore trong iTunes / Finder, chọn file .ipsw.</div></div>`;
  $("i3u").onclick = async () => { const r = await runJob("tools3u_run", "Tải & cài 3uTools", []); if (r.ok) toast(r.result.text); };
  $("iPick").onclick = async () => { const p = await api("pick_folder_abs"); if (p) $("iDest").value = p; };
  let qt; $("iQ").oninput = () => { clearTimeout(qt); qt = setTimeout(iDevRender, 120); };
  $("iSig").onchange = e => { iSigned = e.target.checked; iFwRender(); };
  $("iCats").onclick = e => { const c = e.target.closest("[data-cat]"); if (!c) return; iCat = c.dataset.cat; iDevRender(); };
  $("iDevs").onclick = e => { const d = e.target.closest("[data-dev]"); if (d) iFwLoad(d.dataset.dev); };
  bindLinks(W);
  $("iFw").onclick = async e => {
    const b = e.target.closest("[data-idl]"); if (!b) return;
    const f = iDev.fw[+b.dataset.idl];
    if (!f.signed && !(await confirmBox("Bản đã hết ký", `iOS ${f.version} (${f.build}) Apple đã ngừng ký - không dùng để khôi phục máy được.\nVẫn tải về để lưu trữ?`, "⬇ Vẫn tải", false))) return;
    const r = await runJob("ios_download", `Tải ${iDev.name} · ${f.version} (${f.build})`, [f.url, $("iDest").value.trim()]); dlDone(r);
  };
  try { IDEV = await m("ios_devices"); } catch (e) { $("iDevs").innerHTML = '<div class="warnbox">Không đọc được danh sách thiết bị từ ipsw.me. Kiểm tra mạng rồi mở lại tab.</div>'; W.dataset.ok = ""; return; }
  iDevRender();
}
function iDevRender() {
  const cats = [...new Set(IDEV.map(d => d.cat))];
  const ic = {"iPhone": "📱", "iPad": "📲", "iPod": "🎵", "Apple TV": "📺", "HomePod": "🔊", "Mac (Apple Silicon)": "💻", "Apple Watch": "⌚", "Khác": "🧩"};
  $("iCats").innerHTML = cats.map(c => `<button class="btn sm${c === iCat ? " red" : ""}" data-cat="${esc(c)}">${ic[c] || "▫"} ${esc(c)}</button>`).join("");
  const q = norm($("iQ").value);
  const L = IDEV.filter(d => q ? norm(d.name + " " + d.id).includes(q) : d.cat === iCat);
  $("iDevs").innerHTML = L.map(d => `<button class="tbtn idev${iDev && iDev.id === d.id ? " hot" : ""}" data-dev="${esc(d.id)}"><span class="ti">${ic[d.cat] || "▫"}</span>
    <span class="tt"><b>${esc(d.name)}</b><small>${esc(d.id)}</small></span></button>`).join("") || '<div class="logl">Không thấy máy nào.</div>';
}
async function iFwLoad(id) {
  $("iFwC").hidden = false; $("iFwT").textContent = id; $("iFwS").textContent = "";
  $("iFw").innerHTML = '<div class="empty"><span class="spin"></span> Đang tải danh sách firmware...</div>';
  try { iDev = await m("ios_firmwares", id); } catch (e) { $("iFw").innerHTML = '<div class="warnbox">Không đọc được firmware của máy này.</div>'; return; }
  iDevRender(); iFwRender();
  $("iFwC").scrollIntoView({behavior: "smooth", block: "start"});
}
function iFwRender() {
  if (!iDev) return;
  $("iFwT").textContent = `${iDev.name} (${iDev.id})`;
  const ns = iDev.fw.filter(f => f.signed).length;
  $("iFwS").textContent = `${iDev.fw.length} bản firmware · ${ns} bản Apple còn ký`;
  $("iFw").innerHTML = tbl([["Phiên bản"], ["Build", "110px"], ["Ngày", "110px"], ["Dung lượng", "110px"], ["Trạng thái", "130px"], ["", "170px"]],
    iDev.fw.map((f, i) => iSigned && !f.signed ? "" : `<tr class="${f.signed ? "" : "dim"}"><td><b>${esc(f.version)}</b></td><td>${esc(f.build)}</td><td>${esc(f.date)}</td>
      <td>${fsize(f.size)}</td><td>${f.signed ? pill("CÒN KÝ", "t-done") : pill("Hết ký", "t-skip")}</td>
      <td>${linkBtn(f.url)} <button class="btn sm ${f.signed ? "red" : ""}" data-idl="${i}">⬇ Tải</button></td></tr>`).join(""), "Không có firmware");
}
