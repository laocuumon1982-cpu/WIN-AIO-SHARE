/* Win AIO by Duy Anh - v2.6: Sửa lỗi & thiết lập, Hồ sơ cài đặt, Chuyển phần mềm sang Win mới, Driver, USB boot Ventoy, Test hiệu năng */
const doneBox = (title, res) => dialog({title, width: 640, body: `<div class="okbox">✔ ${esc(res.text || "Xong")}</div>` +
    (res.out ? `<details class="mt"><summary>Xem chi tiết</summary><pre class="pout">${esc(res.out)}</pre></details>` : "") +
    (res.errs && res.errs.length ? `<div class="warnbox">${res.errs.map(esc).join("<br>")}</div>` : ""),
  buttons: [{text: "OK", cls: "red", def: true}]});
async function jobBox(name, label, args, confirmText) {
  if (confirmText && !(await confirmBox(label, confirmText, "▶ Chạy", false))) return null;
  const r = await runJob(name, label, args || []);
  if (r.ok) doneBox(label, r.result);
  return r.ok ? r.result : null;
}
const card = (ic, color, title, sub, body, wide) => `<div class="tcard${wide ? " wide2" : ""}" style="--ac:${color}"><div class="sh"><span class="si">${ic}</span>
  <div><b>${esc(title)}</b><small>${esc(sub)}</small></div></div>${body}</div>`;
const tb = (id, ic, t, s, extraCls) => `<button class="tbtn${extraCls ? " " + extraCls : ""}" id="${id}"><span class="ti">${ic}</span><span class="tt"><b>${esc(t)}</b>${s ? `<small>${esc(s)}</small>` : ""}</span></button>`;

/* =============================================================== SỬA LỖI & THIẾT LẬP */
function fixShow() {
  const W = $("fixwrap");
  if (W.dataset.ok) return setupLoad();
  W.dataset.ok = 1;
  W.innerHTML = `<div class="cgrid fixgrid">
    ${card("🩺", "#e0262a", "SỬA LỖI WINDOWS 1 CHẠM", "Chạy bằng công cụ có sẵn của Windows · nên cắm mạng · mỗi lệnh 5 - 30 phút", `<div class="tgrid2">
      ${tb("fxAll", "🩺", "Sửa tất cả file hệ thống", "DISM RestoreHealth rồi SFC /scannow", "hot wide")}
      ${tb("fxSfc", "🧾", "SFC /scannow", "Kiểm tra, sửa file hệ thống")}${tb("fxDism", "🧱", "DISM RestoreHealth", "Sửa kho thành phần Windows")}
      ${tb("fxWu", "🔄", "Reset Windows Update", "Update kẹt, báo lỗi, tải mãi không xong")}${tb("fxStore", "🛍️", "Reset Microsoft Store", "Store không mở, không tải được app")}
      ${tb("fxPr", "🖨️", "Sửa lỗi chia sẻ máy in", "Lỗi 0x0000011b · 0x00000709 · 0x00000bcb", "wide")}</div>`)}
    ${card("✨", "#7c3aed", "DỌN WIN 11 CHO GỌN", "Tắt các thứ khách hay khó chịu · có nút bật lại", `<ul class="flist">
        <li>Tắt <b>Copilot</b> và nút Copilot trên thanh tác vụ</li><li>Tắt <b>Recall</b> (chụp màn hình lưu lại)</li>
        <li>Tắt <b>quảng cáo, gợi ý</b> trong Start menu, màn hình khóa, tự cài app quảng cáo</li><li>Tắt <b>Widgets</b> (tin tức, thời tiết)</li>
        <li>Tắt <b>gửi dữ liệu chẩn đoán</b>, quảng cáo cá nhân hóa, gợi ý Bing khi tìm kiếm</li></ul>
      <div class="row-acts"><button class="btn" id="tdOff">↩ Bật lại như cũ</button><span class="sp"></span><button class="btn red shine" id="tdOn">✨ Dọn Win 11 cho gọn</button></div>
      <div class="logl">Dùng được cả Win 10 (các mục Win 10 không có sẽ bỏ qua). Thanh tác vụ sẽ chớp 1 lần (khởi động lại Explorer).</div>`)}
    ${card("🖥️", "#0f8fd8", "THIẾT LẬP MÁY MỚI", "Đổi tên máy, tài khoản, mật khẩu đăng nhập, trình duyệt, bộ gõ", '<div id="suBody"><div class="logl"><span class="spin"></span> Đang đọc...</div></div>', true)}
    ${card("🔤", "#d97706", "BỘ FONT TIẾNG VIỆT", "VNI, TCVN3 (.VnTime...), Unicode - cài thẳng vào Windows, bỏ qua font đã có", `
      <div class="frm"><label>Link tải bộ font (.zip) <span class="row2"><input id="ftUrl" placeholder="Admin dán link tải thẳng file .zip bộ font"><button class="btn sm adm" id="ftSave">💾 Lưu link</button></span></label></div>
      <div class="row-acts"><button class="btn" id="ftFile">📦 Cài từ file .zip / font</button><button class="btn" id="ftDir">📂 Cài từ thư mục</button><span class="sp"></span>
        <button class="btn red shine" id="ftGo">⬇ Tải &amp; cài từ link</button></div>
      <div class="logl">Tool không kèm sẵn font (font VNI / TCVN3 có bản quyền của hãng). Chép bộ font của bạn vào USB / Google Drive rồi gắn link 1 lần, lần sau bấm là cài.
        Link Google Drive phải là link tải thẳng (drive.usercontent.google.com/download?id=...&export=download&confirm=t).</div>`)}
  </div>`;
  const J = (id, name, label, txt, args) => { $(id).onclick = () => jobBox(name, label, args, txt); };
  J("fxAll", "fix_all", "Sửa tất cả file hệ thống (DISM + SFC)", "Chạy DISM RestoreHealth rồi SFC /scannow?\nMất khoảng 15 - 40 phút, máy vẫn dùng được trong lúc chạy. Nên cắm mạng.");
  J("fxSfc", "fix_sfc", "SFC /scannow", "Kiểm tra và sửa file hệ thống Windows (10 - 20 phút)?");
  J("fxDism", "fix_dism", "DISM RestoreHealth", "Sửa kho thành phần Windows bằng file từ Windows Update (10 - 30 phút, cần mạng)?");
  J("fxWu", "fix_wu", "Reset Windows Update", "Dừng dịch vụ Update, xóa bộ nhớ đệm tải về (SoftwareDistribution, catroot2) rồi chạy lại?\nLịch sử cập nhật trong Cài đặt sẽ trống, các bản đã cài vẫn giữ nguyên.");
  J("fxStore", "fix_store", "Reset Microsoft Store", "Đặt lại và đăng ký lại Microsoft Store?");
  J("fxPr", "fix_printer", "Sửa lỗi chia sẻ máy in", "Sửa lỗi kết nối máy in chia sẻ 0x0000011b / 0x00000709?\nChạy trên CẢ máy chủ (máy cắm máy in) và máy con.\n(Hạ mức bảo mật RPC của dịch vụ in về như trước bản vá 2021 - chỉ dùng trong mạng nội bộ tin cậy.)");
  $("tdOn").onclick = () => jobBox("win11_tidy", "Dọn Win 11 cho gọn", [true], "Tắt Copilot, Recall, quảng cáo Start menu, Widgets, gửi dữ liệu chẩn đoán?");
  $("tdOff").onclick = () => jobBox("win11_tidy", "Bật lại Win 11 như cũ", [false], "Bật lại các mục như mặc định của Windows?");
  api("font_cfg").then(u => { $("ftUrl").value = u || ""; });
  $("ftSave").onclick = async () => { await api("font_cfg", $("ftUrl").value); toast("Đã lưu link bộ font"); };
  $("ftGo").onclick = () => { const u = $("ftUrl").value.trim(); if (!u) return toast("Chưa có link - Admin dán link bộ font rồi bấm Lưu", "err"); jobBox("font_install", "Cài bộ font tiếng Việt", [u]); };
  $("ftFile").onclick = async () => { const p = await api("pick_file_abs"); if (p) jobBox("font_install", "Cài font", [p]); };
  $("ftDir").onclick = async () => { const p = await api("pick_folder_abs"); if (p) jobBox("font_install", "Cài font từ thư mục", [p]); };
  setupLoad();
}
async function setupLoad() {
  const B = $("suBody"); if (!B) return;
  const s = await m("setup_info");
  const users = s.users || [];
  B.innerHTML = `<div class="sugrid">
    <div class="sur"><span class="sul">🏷️ Tên máy</span><input id="suPc" value="${esc(s.pc)}" maxlength="15"><button class="btn sm" id="suPcGo">✓ Đổi tên</button></div>
    <div class="sur"><span class="sul">👤 Tạo tài khoản</span><input id="suUn" placeholder="Tên (VD: KeToan)" maxlength="20"><input id="suUp" type="password" placeholder="Mật khẩu (để trống = không mật khẩu)">
      <label class="ck"><input type="checkbox" id="suUa"> Quản trị</label><button class="btn sm green" id="suUGo">＋ Tạo</button></div>
    <div class="sur"><span class="sul">🔓 Bỏ mật khẩu</span><select id="suNp">${users.map(u => `<option value="${esc(u.name)}">${esc(u.name)}${u.admin ? " (quản trị)" : ""}${u.pw ? "" : " · không mật khẩu"}</option>`).join("")}</select>
      <button class="btn sm" id="suNpGo">🔓 Bỏ mật khẩu đăng nhập</button><button class="btn sm" id="suNet" title="Tự đăng nhập tài khoản Microsoft / có mật khẩu">⚙ netplwiz</button></div>
    <div class="sur"><span class="sul">🌐 Trình duyệt</span><button class="btn sm" id="suBr">${s.chrome ? "⭐ Đặt Chrome làm mặc định" : "⚙ Mở Ứng dụng mặc định"}</button>
      <span class="logl" style="margin:0">${s.chrome ? "Windows bắt buộc bấm xác nhận 1 lần trong Cài đặt" : "Máy chưa cài Chrome"}</span></div>
    <div class="sur"><span class="sul">⌨️ UniKey</span><label class="ck"><input type="checkbox" id="suUk"${s.unikey_auto ? " checked" : ""}${s.unikey ? "" : " disabled"}> Chạy cùng Windows</label>
      <span class="logl path" style="margin:0" title="${esc(s.unikey)}">${s.unikey ? esc(s.unikey) : "Chưa cài UniKey - cài ở tab Cài phần mềm"}</span></div></div>
    <div class="logl">Đổi tên máy cần khởi động lại. Bỏ mật khẩu chỉ làm được với tài khoản cục bộ (không phải tài khoản Microsoft).</div>`;
  const done = (r, ok) => { if (r) return errBox("Thiết lập máy", r); toast(ok); setupLoad(); };
  $("suPcGo").onclick = async () => { const n = $("suPc").value.trim();
    if (!(await confirmBox("Đổi tên máy", `Đổi tên máy thành "${n}"?\nCần khởi động lại để áp dụng.`, "✓ Đổi tên", false))) return;
    done(await m("setup_rename", n), "Đã đổi tên máy - khởi động lại để áp dụng"); };
  $("suUGo").onclick = async () => done(await m("setup_user", $("suUn").value, $("suUp").value, $("suUa").checked), "Đã tạo tài khoản " + $("suUn").value);
  $("suNpGo").onclick = async () => { const u = $("suNp").value; if (!u) return;
    if (!(await confirmBox("Bỏ mật khẩu đăng nhập", `Bỏ mật khẩu của tài khoản "${u}"?\nAi mở máy cũng vào thẳng Windows được.`, "🔓 Bỏ mật khẩu"))) return;
    done(await m("setup_nopass", u), "Đã bỏ mật khẩu " + u); };
  $("suNet").onclick = () => api("quick", "netplwiz");
  $("suBr").onclick = async () => toast(await m("setup_browser"));
  $("suUk").onchange = async e => done(await m("setup_unikey", e.target.checked), e.target.checked ? "UniKey sẽ chạy cùng Windows" : "Đã tắt UniKey chạy cùng Windows");
}

/* =============================================================== HỒ SƠ CÀI ĐẶT (preset) */
let PRE = [];
async function presetBox() {
  PRE = await api("preset_list");
  const allApps = new Map(); G.forEach(g => g.apps.forEach(a => allApps.set(norm(a.name), a)));
  const toolName = id => (INIT.tools.find(t => t.id === id) || {}).label || id;
  const body = () => `<div class="msg">Bấm <b>▶ Cài</b> để cài toàn bộ phần mềm + chạy tiện ích Windows của hồ sơ, không cần chọn từng nút.</div>
    <div class="prelist">${PRE.map(p => { const miss = p.apps.filter(n => !allApps.has(norm(n)));
      return `<div class="prei" data-id="${p.id}"><span class="pric">${esc(p.icon || "📋")}</span><div class="prx"><b>${esc(p.name)}</b>
        <small>📦 ${p.apps.length} phần mềm: ${esc(p.apps.join(", "))}${miss.length ? ` <em class="bad">(không thấy nút: ${esc(miss.join(", "))})</em>` : ""}</small>
        <small>🧰 ${esc(p.tools.map(toolName).join(" · ") || "không chạy tiện ích")}${p.opts.tidy ? " · ✨ Dọn Win 11" : ""}${p.opts.fonts ? " · 🔤 Cài font" : ""}</small></div>
        <button class="btn sm adm" data-pe="${p.id}">✎</button><button class="btn red shine" data-pr="${p.id}">▶ Cài</button></div>`; }).join("") || '<div class="logl">Chưa có hồ sơ nào.</div>'}</div>`;
  await dialog({title: "📋 Hồ sơ cài đặt", width: 860, body: `<div id="preB">${body()}</div>`,
    left: '<button class="btn sm green adm" id="preAdd">＋ Thêm hồ sơ</button>',
    buttons: [{text: "Đóng", value: null}],
    onOpen: c => {
      c.q("#preAdd").onclick = async () => { if (await presetEdit({})) { PRE = await api("preset_list"); c.q("#preB").innerHTML = body(); } };
      c.q("#preB").onclick = async e => {
        const r = e.target.closest("[data-pr]"), ed = e.target.closest("[data-pe]");
        if (r) { const p = PRE.find(x => x.id === +r.dataset.pr);
          if (!(await confirmBox("Cài hồ sơ " + p.name, `Cài ${p.apps.length} phần mềm và chạy ${p.tools.length} tiện ích Windows${p.opts.tidy ? ", dọn Win 11" : ""}${p.opts.fonts ? ", cài font tiếng Việt" : ""}?\n\n${p.apps.map(n => "• " + n).join("\n")}`, "▶ Cài hồ sơ", false))) return;
          c.close(null); const x = await runJob("preset_run", "Hồ sơ: " + p.name, [p.id]); if (x.ok) doneBox("Hồ sơ: " + p.name, x.result); }
        if (ed && await presetEdit(PRE.find(x => x.id === +ed.dataset.pe))) { PRE = await api("preset_list"); c.q("#preB").innerHTML = body(); }
      };
    }});
}
async function presetEdit(p) {
  p = Object.assign({name: "", icon: "📋", apps: [], tools: [], opts: {}}, p || {});
  const sel = new Set(p.apps.map(norm)), tsel = new Set(p.tools);
  const groups = [];
  INIT.tools.forEach(t => { let g = groups.find(x => x.n === t.group); if (!g) groups.push(g = {n: t.group, items: []}); g.items.push(t); });
  const r = await dialog({title: p.id ? "Sửa hồ sơ " + p.name : "Thêm hồ sơ cài đặt", width: 980, body: `
    <div class="row2"><input id="peIc" value="${esc(p.icon)}" style="width:70px"><input id="peNm" value="${esc(p.name)}" placeholder="Tên hồ sơ (VD: Máy văn phòng)"></div>
    <div class="pecols"><div><h5>📦 PHẦN MỀM</h5><div class="pebox">${G.map(g => `<div class="peg"><b>${esc(g.name)}</b>${g.apps.map(a => `<label class="ck"><input type="checkbox" data-an="${esc(a.name)}"${sel.has(norm(a.name)) ? " checked" : ""}> ${esc(a.name)}</label>`).join("")}</div>`).join("")}</div></div>
      <div><h5>🧰 TIỆN ÍCH WINDOWS</h5><div class="pebox">${groups.filter(g => !/BẢN QUYỀN|BITLOCKER/.test(g.n)).map(g => `<div class="peg"><b>${esc(g.n)}</b>${g.items.filter(t => t.kind !== "open" && !t.fn).map(t => `<label class="ck"><input type="checkbox" data-tid="${t.id}"${tsel.has(t.id) ? " checked" : ""}> ${esc(t.label)}</label>`).join("")}</div>`).join("")}
        <div class="peg"><b>KHÁC</b><label class="ck"><input type="checkbox" id="peTd"${p.opts.tidy ? " checked" : ""}> ✨ Dọn Win 11 cho gọn</label>
          <label class="ck"><input type="checkbox" id="peFt"${p.opts.fonts ? " checked" : ""}> 🔤 Cài bộ font tiếng Việt (link Admin đã gắn)</label></div></div></div></div><div class="err"></div>`,
    left: p.id ? '<button class="btn sm out" id="peDel">🗑 Xóa hồ sơ</button>' : "",
    buttons: [{text: "Hủy", value: null}, {text: "💾 Lưu hồ sơ", cls: "red", def: true, click: c => {
      const name = c.q("#peNm").value.trim(); if (!name) { c.err("Nhập tên hồ sơ"); return false; }
      return {id: p.id, name, icon: c.q("#peIc").value, apps: [...c.el.querySelectorAll("[data-an]:checked")].map(x => x.dataset.an),
        tools: [...c.el.querySelectorAll("[data-tid]:checked")].map(x => x.dataset.tid), opts: {tidy: c.q("#peTd").checked, fonts: c.q("#peFt").checked}}; }}],
    onOpen: c => { const d = c.q("#peDel"); if (d) d.onclick = async () => { if (await confirmBox("Xóa hồ sơ", `Xóa hồ sơ "${p.name}"?`, "🗑 Xóa")) { await api("preset_delete", p.id); c.close(true); } }; }});
  if (r === true) return true;
  if (!r) return false;
  await api("preset_save", r); toast("Đã lưu hồ sơ " + r.name); return true;
}
document.addEventListener("DOMContentLoaded", function addPresetBtn() {
  const go = document.getElementById("bGo"); if (!go) return;
  const b = document.createElement("button"); b.className = "btn"; b.id = "bPreset"; b.innerHTML = "📋 Hồ sơ cài đặt";
  b.title = "Cài cả bộ phần mềm + tinh chỉnh Windows cho Máy văn phòng / Máy kế toán / Máy game..."; b.onclick = presetBox;
  go.parentElement.insertBefore(b, go);
});

/* =============================================================== CHUYỂN PHẦN MỀM SANG WIN MỚI (trong tab Sao lưu) */
function addAppMove() {
  const grid = $("backwrap").querySelector(".cgrid"); if (!grid || $("amBody")) return;
  grid.insertAdjacentHTML("beforeend", card("🚚", "#7c3aed", "CHUYỂN PHẦN MỀM SANG WIN MỚI", "Lưu danh sách phần mềm đang cài (winget export) vào USB · cài Win xong bấm là cài lại hết", `<div id="amBody">
    <div class="row-acts"><span class="logl grow" style="margin:0">Bước 1 (máy cũ): lưu danh sách vào ô "Nơi lưu" ở trên (nên là USB).</span><button class="btn red shine" id="amExp">💾 Lưu danh sách phần mềm</button></div>
    <div class="row-acts"><span class="logl grow" style="margin:0">Bước 2 (Win mới): mở tool từ USB, chọn file PhanMem_....json.</span><button class="btn green" id="amImp">⬇ Cài lại từ danh sách...</button></div>
    <div class="logl">Chỉ chuyển được phần mềm có trong kho winget (Chrome, Zalo, UniKey, 7-Zip, VLC...). Dữ liệu, tài khoản đăng nhập không đi theo - dùng các mục sao lưu khác.</div></div>`, true));
  $("amExp").onclick = async () => { if (!destVal()) return toast("Chọn nơi lưu trước", "err");
    const r = await runJob("apps_export", "Lưu danh sách phần mềm", [destVal()]); if (r.ok) okDone(r.result); };
  $("amImp").onclick = async () => {
    const p = await api("pick_file_abs"); if (!p) return;
    let ids; try { ids = await m("apps_list_file", p); } catch (e) { return; }
    const r = await dialog({title: "Cài lại phần mềm", width: 640, body: `<div class="msg">File có ${ids.length} phần mềm. Bỏ tick phần mềm không muốn cài:</div>
      <div class="lolist">${ids.map(i => `<label class="ck lo st"><input type="checkbox" data-pk="${esc(i)}" checked> <span class="lp">${esc(i)}</span></label>`).join("")}</div>`,
      buttons: [{text: "Hủy", value: null}, {text: "⬇ Cài lại", cls: "red", def: true, click: c => [...c.el.querySelectorAll("[data-pk]:checked")].map(x => x.dataset.pk)}]});
    if (!r || !r.length) return;
    const x = await runJob("apps_import", `Cài lại ${r.length} phần mềm`, [p, r]); if (x.ok) doneBox("Cài lại phần mềm", x.result);
  };
}
{ const _bs = backShow; backShow = async function () { await _bs(); addAppMove(); }; }

/* =============================================================== USB BOOT VENTOY (trong Kho ISO) */
function addVentoy() {
  const W = $("isowrap"); if (!W.dataset.ok || $("vtBody")) return;
  const first = W.querySelector(".isosec");
  first.insertAdjacentHTML("afterend", `<div class="tcard isosec" style="--ac:#b45309"><div class="sh"><span class="si">🔧</span><div><b>RUFUS</b>
      <small>Tạo USB cài Win / Linux từ file ISO (mỗi USB 1 bộ cài) · tải bản portable mới nhất chính chủ (rufus.ie), mở lên dùng ngay</small></div>
      <span class="sp"></span><button class="btn red shine" id="rfGo">⬇ Tải &amp; mở Rufus</button></div></div>
    <div class="tcard isosec" style="--ac:#16a34a"><div class="sh"><span class="si">🔌</span><div><b>TẠO USB BOOT (VENTOY)</b>
      <small>Tool tự tải Ventoy bản mới nhất, cài vào USB, chép ISO vào - 1 USB chứa được nhiều ISO, chọn lúc boot</small></div><span class="sp"></span><button class="btn sm" id="vtRef">⟳ Làm mới</button></div>
    <div id="vtBody"><div class="logl"><span class="spin"></span> Đang tìm USB...</div></div></div>`);
  $("vtRef").onclick = vtLoad; vtLoad();
  $("rfGo").onclick = async () => { const r = await runJob("rufus_run", "Tải & mở Rufus", []); if (r.ok) toast(r.result.text); };
}
async function vtLoad() {
  const B = $("vtBody");
  const [U, I] = await Promise.all([m("usb_disks"), m("iso_files")]);
  B.innerHTML = !U.length ? '<div class="warnbox">Chưa thấy USB nào. Cắm USB (8 GB trở lên) rồi bấm ⟳ Làm mới.</div>' : `
    <div class="vtl">${U.map((u, i) => `<label class="isov${i ? "" : " on"}"><input type="radio" name="vtU" value="${u.num}"${i ? "" : " checked"}><span class="ti">${u.ventoy ? "✅" : "🔌"}</span>
      <span><b>${esc(u.model)}</b><small>Ổ số ${u.num} · ${hs(u.size)}${u.letters ? " · " + esc(u.letters) + ":" : ""}${u.ventoy ? " · ĐÃ CÓ VENTOY" : ""}</small></span></label>`).join("")}</div>
    <div class="row-acts"><label class="ck"><input type="checkbox" id="vtGpt"> Kiểu GPT (máy mới chỉ UEFI) - mặc định MBR boot được cả máy cũ</label><span class="sp"></span>
      <button class="btn red shine" id="vtGo">🔌 Cài Ventoy vào USB (XÓA SẠCH USB)</button></div>
    <div class="row2 mt"><select id="vtIso">${I.map(f => `<option value="${esc(f.path)}">${esc(f.name)} · ${hs(f.size)}</option>`).join("")}<option value="">📂 Chọn file ISO khác...</option></select>
      <button class="btn green" id="vtCp">📀 Chép ISO vào USB Ventoy</button></div>
    <div class="logl">Đã có Ventoy thì chỉ cần chép ISO (không xóa dữ liệu khác trên USB). File ISO tải ở trên nằm sẵn trong danh sách.</div>`;
  if (!U.length) return;
  B.querySelectorAll('input[name="vtU"]').forEach(r => r.onchange = () => B.querySelectorAll(".isov").forEach(l => l.classList.toggle("on", l.contains(B.querySelector('input[name="vtU"]:checked')))));
  const cur = () => U.find(u => u.num === +B.querySelector('input[name="vtU"]:checked').value);
  $("vtGo").onclick = async () => {
    const u = cur();
    const ok = await dialog({title: "⚠ XÓA SẠCH USB", width: 560, body: `<div class="warnbox">Toàn bộ dữ liệu trên <b>${esc(u.model)}</b> (${hs(u.size)}${u.letters ? ", ổ " + esc(u.letters) + ":" : ""}) sẽ bị <b>XÓA VĨNH VIỄN</b>.</div>
      <div class="msg">Gõ <b>XOA</b> để xác nhận:</div><input id="vtCf" style="width:100%;margin-top:6px"><div class="err"></div>`,
      buttons: [{text: "Hủy", value: false}, {text: "🔌 Xóa và cài Ventoy", cls: "red", def: true, click: c => { if (c.q("#vtCf").value.trim().toUpperCase() !== "XOA") { c.err("Gõ đúng chữ XOA"); return false; } return true; }}]});
    if (!ok) return;
    const r = await runJob("ventoy_install", "Cài Ventoy vào " + u.model, [u.num, $("vtGpt").checked]);
    if (r.ok) { doneBox("USB boot", r.result); vtLoad(); }
  };
  $("vtCp").onclick = async () => {
    const u = cur(); let iso = $("vtIso").value;
    if (!u.ventoy) return toast("USB này chưa có Ventoy - bấm Cài Ventoy trước", "err");
    if (!iso) { iso = await api("pick_file_abs"); if (!iso) return; }
    const letter = (u.letters || "").split(",")[0];
    const r = await runJob("ventoy_copy", "Chép ISO vào USB", [iso, letter]); if (r.ok) doneBox("USB boot", r.result);
  };
}
/* =============================================================== KHO DRIVER IRST (trong Kho bộ cài WIN) */
function addIrst() {
  const W = $("isowrap"); if (!W.dataset.ok || $("irBody")) return;
  const vt = $("vtBody").closest(".isosec");
  vt.insertAdjacentHTML("afterend", `<div class="tcard isosec" style="--ac:#0f62fe"><div class="sh"><span class="si">💾</span><div><b>KHO DRIVER IRST (Intel RST / VMD)</b>
      <small>Máy Intel đời 11 trở lên lúc cài Win không thấy ổ cứng → chép driver vào USB cài Win, bấm "Load driver"</small></div></div>
    <div id="irBody"><div class="logl"><span class="spin"></span> Đang kiểm tra CPU...</div></div></div>`);
  irLoad();
}
async function irLoad() {
  const B = $("irBody");
  const [I, U] = await Promise.all([m("irst_info"), m("usb_disks")]);
  const usb = U.flatMap(u => (u.letters || "").split(",").filter(Boolean).map(l => ({l, n: u.model})));
  B.innerHTML = `<div class="${I.need ? "warnbox" : "okbox"}">${I.need ? "⚠" : "✔"} Máy này: <b>${esc(I.cpu || "không rõ CPU")}</b> -
      ${I.need ? `<b>CẦN driver IRST</b> khi cài lại Win (Intel ${I.gen === "Ultra" ? "Core Ultra" : "đời " + I.gen})` : "không cần driver IRST (chỉ máy Intel đời 11 trở lên mới cần)"}</div>
    <div class="isoopt"><label class="grow">Giải nén vào <select id="irDest"><option value="">📁 Thư mục Data\\Driver (kế bên tool)</option>
      ${usb.map(x => `<option value="${esc(x.l)}:\\">🔌 USB ${esc(x.l)}: (${esc(x.n)}) - gốc USB</option>`).join("")}<option value="?">📂 Chọn thư mục khác...</option></select></label></div>
    <div class="vtl">${I.list.map(x => `<div class="isov${x.fit ? " on" : ""}"><span class="ti">💾</span><span class="grow"><b>Intel RST ${esc(x.ver)}</b>
      <small>${esc(x.gen)}${x.fit ? " · ✅ HỢP MÁY NÀY" : ""}</small></span><button class="btn sm red" data-ir="${esc(x.file)}">⬇ Tải</button></div>`).join("")}</div>
    <div class="row-acts"><span class="logl grow" style="margin:0">Đã có file IntelRstVmd_....zip? Giải nén thẳng vào USB:</span><button class="btn sm" id="irLocal">📦 Chọn file .zip...</button></div>
    <div class="logl">Không chắc đời CPU: chép cả 2 bản vào USB, lúc Load driver thử bản mới trước. Máy AMD không cần driver này.</div>`;
  const dest = async () => { let d = $("irDest").value; if (d === "?") { d = await api("pick_folder_abs"); if (!d) return null; } return d; };
  B.onclick = async e => {
    const b = e.target.closest("[data-ir]"); if (!b) return;
    const d = await dest(); if (d === null) return;
    const r = await runJob("irst_get", "Driver IRST " + b.dataset.ir.replace(/^IntelRstVmd_|\.zip$/g, ""), [b.dataset.ir, d]); if (r.ok) dlDone(r);
  };
  $("irLocal").onclick = async () => { const p = await api("pick_file_abs"); if (!p) return; const d = await dest(); if (d === null) return;
    const r = await runJob("irst_get", "Giải nén driver IRST", ["", d, p]); if (r.ok) dlDone(r); };
}
{ const _is = isoShow; isoShow = function () { _is(); addVentoy(); addIrst(); }; }

/* =============================================================== DRIVER (tab Quản lý) */
let DRV = [];
async function drvLoad() {
  const P = $("mp-driver");
  P.innerHTML = `<div class="mbar"><button class="btn" id="dvRef">⟳ Quét lại</button><button class="btn red shine" id="dvWu">🔎 Tìm driver qua Windows Update</button>
      <button class="btn" id="dvDm">⚙ Device Manager</button><span class="cnt" id="dvCnt"></span></div>
    <div id="dvTbl">${tbl([["Thiết bị"]], "", '<span class="spin"></span> Đang quét thiết bị...')}</div><div id="dvWuB"></div>
    <div class="logl">Danh sách thiết bị có dấu chấm than vàng trong Device Manager. Windows Update tìm được driver chính hãng cho phần lớn máy; máy cũ / main lạ dùng Snappy Driver Installer ở tab Cài phần mềm.</div>`;
  $("dvRef").onclick = drvLoad; $("dvDm").onclick = () => api("quick", "devmgmt.msc"); $("dvWu").onclick = drvWu;
  DRV = await m("drv_problems");
  $("dvCnt").textContent = DRV.length ? `${DRV.length} thiết bị lỗi / thiếu driver` : "";
  $("dvTbl").innerHTML = tbl([["Thiết bị"], ["Loại", "140px"], ["Lỗi", "230px"], ["Mã phần cứng", "32%"]],
    DRV.map(d => `<tr><td><b>${esc(d.name)}</b></td><td>${esc(d.cls || "")}</td><td>${pill(d.err, d.code === 22 ? "t-skip" : "t-err")}</td><td class="path" title="${esc(d.id)}">${esc(d.id)}</td></tr>`).join(""),
    "✔ Không có thiết bị nào lỗi hoặc thiếu driver");
}
async function drvWu() {
  const r = await runJob("drv_wu_scan", "Tìm driver qua Windows Update", []);
  if (!r.ok) return;
  const L = r.result;
  $("dvWuB").innerHTML = !L.length ? '<div class="okbox mt">✔ Windows Update không có driver nào mới / còn thiếu cho máy này.</div>' : `
    <div class="mbar mt"><b>Windows Update có ${L.length} driver:</b><span class="sp"></span><button class="btn red shine" id="dvIns">⬇ Cài driver đã chọn</button></div>
    ${tbl([["", "34px"], ["Driver"], ["Loại", "120px"], ["Ngày", "110px"], ["Dung lượng", "110px"]],
      L.map(d => `<tr><td><input type="checkbox" data-dv="${esc(d.id)}" checked></td><td><b>${esc(d.title)}</b></td><td>${esc(d.cls || "")}</td><td>${esc(d.date || "")}</td><td>${d.size ? hs(d.size) : ""}</td></tr>`).join(""))}`;
  if (!L.length) return;
  $("dvIns").onclick = async () => {
    const ids = [...$("dvWuB").querySelectorAll("[data-dv]:checked")].map(x => x.dataset.dv);
    if (!ids.length) return toast("Chưa chọn driver", "err");
    const x = await runJob("drv_wu_install", `Cài ${ids.length} driver`, [ids]);
    if (x.ok) { doneBox("Cài driver", x.result); drvLoad(); }
  };
}

/* =============================================================== TEST HIỆU NĂNG (tab Test máy) */
let PF = {};
function pfRender() {
  const B = $("tb-perf"); if (!B) return;
  const d = PF.disk, c = PF.cpu;
  const bar = (v, max, cls) => `<div class="bar"><div class="${cls}" style="width:${Math.min(100, (v || 0) / max * 100)}%"></div></div>`;
  B.innerHTML = (d ? `<div class="pfh">💽 Ổ ${esc(d.drive)}: <b>${esc(d.kind)}</b></div>${Object.values(d.res).map(x => `<div class="lbar"><span>${esc(x.name)}</span>
      ${bar(x.mbs, 3500, "b-blue")}<b>${x.mbs != null ? x.mbs.toLocaleString("vi-VN") + " MB/s" : "lỗi"}</b></div>`).join("")}` : "")
    + (c ? `<div class="pfh">🔥 CPU ${c.threads} luồng · ${c.secs} giây: nhiệt độ cao nhất <b>${c.tmax != null ? c.tmax + "°C" : "không đọc được"}</b>${c.tavg != null ? ` (TB ${c.tavg}°C)` : ""}
        · xung thấp nhất <b>${c.perf_min != null ? c.perf_min + "%" : "?"}</b> ${c.throttle ? pill("CÓ HẠ XUNG VÌ NÓNG", "t-err") : c.perf_min != null ? pill("Không hạ xung", "t-done") : ""}</div>
        <svg class="pfch" viewBox="0 0 300 70" preserveAspectRatio="none">${pfLine(c.series, "temp", 110, "#e0262a")}${pfLine(c.series, "perf", 130, "#2f7fa3")}${pfLine(c.series, "cpu", 100, "#16a34a")}</svg>
        <div class="pfleg"><span style="color:#e0262a">━ Nhiệt độ</span><span style="color:#2f7fa3">━ Xung nhịp (%)</span><span style="color:#16a34a">━ Tải CPU</span></div>` : "")
    + (!d && !c ? '<div class="logl">Đo ổ cứng mất khoảng 1 phút. Tải CPU chạy 100% mọi nhân, máy nóng là bình thường - quạt kêu to, nhiệt độ quá 95°C hoặc tụt xung mạnh là cần vệ sinh / tra keo.</div>' : "");
}
function pfLine(S, k, max, color) {
  const P = (S || []).filter(x => x[k] != null); if (P.length < 2) return "";
  const n = S[S.length - 1].s || 1;
  return `<polyline fill="none" stroke="${color}" stroke-width="1.6" vector-effect="non-scaling-stroke" points="${P.map(x => `${(x.s / n * 300).toFixed(1)},${(70 - Math.min(max, x[k]) / max * 68).toFixed(1)}`).join(" ")}"/>`;
}
async function pfDisk() {
  const dr = ($("pfDrv").value || "C").trim();
  const r = await runJob("bench_disk", "Đo tốc độ ổ " + dr, [dr]); if (r.ok) { PF.disk = r.result; pfRender(); }
}
async function pfCpu() {
  const s = +$("pfSec").value;
  if (!(await confirmBox("Test tải CPU", `Chạy 100% toàn bộ nhân CPU trong ${s} giây và theo dõi nhiệt độ, xung nhịp?\nBấm Dừng bất cứ lúc nào để dừng ngay.`, "🔥 Chạy", false))) return;
  const r = await runJob("bench_cpu", `Tải CPU ${s} giây`, [s]); if (r.ok) { PF.cpu = r.result; pfRender(); }
}
