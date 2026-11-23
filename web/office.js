/* Win AIO by Duy Anh - v3.0: MS Office - Gỡ tận gốc, Bản quyền Office / Windows (key của khách), Thiết lập Office cho văn bản Việt Nam */
const outBox = (title, r) => dialog({title, width: 720, body: `<div class="${r.ok === false ? "warnbox" : "okbox"}">${r.ok === false ? "✖" : "✔"} ${esc(r.text || "")}</div>` +
  (r.out ? `<details class="mt"${r.ok === false ? " open" : ""}><summary>Xem chi tiết</summary><pre class="pout">${esc(r.out)}</pre></details>` : ""),
  buttons: [{text: "OK", cls: "red", def: true}]});

/* ------------------------------------------------ Gỡ Office tận gốc */
async function offRemoveBox() {
  const S = await m("off_scan");
  const li = a => a.length ? a.map(x => `<div>● ${esc(x)}</div>`).join("") : '<div class="logl" style="margin:0">Không thấy</div>';
  const r = await dialog({title: "🗑 Gỡ Microsoft Office", width: 680, body: `
    <div class="msg">Xóa sạch Microsoft Office đang có trên máy - nhanh và tận gốc. Nên gỡ trước khi cài bản khác.</div>
    <div class="rmgrid mt">
      <div class="rmbox" style="--ac:#e0262a"><label class="ck"><input type="checkbox" id="rmC2r"${S.c2r.length ? " checked" : ""}> <b>Office Click-to-Run</b></label>
        <small>Microsoft 365, 2016, 2019, 2021, 2024</small>${li(S.c2r)}</div>
      <div class="rmbox" style="--ac:#d97706"><label class="ck"><input type="checkbox" id="rmMsi"${S.msi.length ? " checked" : ""}> <b>Office MSI</b></label>
        <small>Office 2007, 2010, 2013, 2016 (bản cũ)</small>${li(S.msi)}</div></div>
    <label class="ck mt"><input type="checkbox" id="rmClean" checked> Dọn tàn dư sau khi gỡ: dịch vụ, tác vụ, registry, thư mục, lối tắt, key Office cũ</label>
    <div class="logl">Tất cả Word / Excel... đang mở sẽ bị đóng - lưu tài liệu trước. Gỡ xong nên khởi động lại máy rồi mới cài bản mới.</div><div class="err"></div>`,
    buttons: [{text: "Hủy", value: null}, {text: "🗑 GỠ OFFICE", cls: "red", def: true, click: c => {
      const o = {c2r: c.q("#rmC2r").checked, msi: c.q("#rmMsi").checked, clean: c.q("#rmClean").checked};
      if (!o.c2r && !o.msi && !o.clean) { c.err("Chưa chọn mục nào"); return false; } return o; }}]});
  if (!r) return;
  const x = await runJob("off_remove", "Gỡ Microsoft Office", [r.c2r, r.msi, r.clean]);
  if (x.ok) outBox("Gỡ Microsoft Office", x.result);
}

/* ------------------------------------------------ Bản quyền Office / Windows */
async function licBox(kind) {
  kind = kind || "office";
  let st = null;
  const body = () => `<div class="ltabs"><button class="btn sm${kind === "office" ? " red" : ""}" data-lk="office">🏢 Office</button>
      <button class="btn sm${kind === "windows" ? " red" : ""}" data-lk="windows">🪟 Windows</button>
      <span class="sp"></span><span class="logl" style="margin:0">Chỉ kích hoạt bằng key bản quyền của khách - không có bẻ khóa</span></div>
    <div class="licst"><b>Trạng thái hiện tại</b> <button class="btn sm" id="lsRef">⟳</button><pre class="pout" id="lsOut">Đang đọc...</pre></div>
    <div class="licsec"><b>1. Nhập key, kích hoạt online</b>
      <div class="row2"><input id="lkKey" placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX" maxlength="29" style="font-family:monospace;flex:1">
        ${kind === "windows" ? '<button class="btn sm" id="lkOem" title="Máy bán kèm Windows bản quyền có key trong BIOS">🔎 Lấy key OEM trong BIOS</button>' : ""}
        <button class="btn red" id="lkGo">🔑 Kích hoạt</button></div></div>
    <div class="licsec"><b>2. Kích hoạt qua điện thoại (không có mạng / key hết lượt online)</b>
      <div class="row2"><button class="btn sm" id="liIid">① Lấy Installation ID</button><input id="liOut" readonly placeholder="Installation ID hiện ở đây - đọc cho tổng đài Microsoft hoặc nhập vào trang kích hoạt" style="flex:1;font-family:monospace">
        <button class="btn sm" id="liCp">⧉</button></div>
      <div class="row2 mt"><input id="lcCid" placeholder="② Dán Confirmation ID (48 số) Microsoft đưa" style="flex:1;font-family:monospace"><button class="btn green" id="lcGo">✓ Kích hoạt bằng CID</button></div></div>
    <div class="licsec"><b>3. Dọn trước khi nhập key</b><div class="row2">
      ${kind === "office" ? '<button class="btn sm" id="ckChk">🔍 Kiểm tra crack KMS / Ohook</button><button class="btn sm" id="ckClr">🧹 Dọn crack KMS / Ohook</button>'
        : '<button class="btn sm" id="wcClr">🧹 Gỡ key Windows + xóa cấu hình KMS</button>'}</div>
      <div class="logl">Máy từng dùng KMSpico, KMSAuto, Ohook... thì key bản quyền thật thường không vào được - dọn trước rồi nhập key.</div></div>`;
  await dialog({title: "🔑 Bản quyền Office / Windows", width: 820, body: `<div id="licB">${body()}</div>`, buttons: [{text: "Đóng", value: null}],
    onOpen: c => {
      const load = async () => { c.q("#lsOut").textContent = "Đang đọc..."; st = await m("lic_status", kind); c.q("#lsOut").textContent = st.out; };
      const bind = () => {
        c.q("#licB").querySelectorAll("[data-lk]").forEach(b => b.onclick = () => { kind = b.dataset.lk; c.q("#licB").innerHTML = body(); bind(); load(); });
        c.q("#lsRef").onclick = load;
        c.q("#lkGo").onclick = async () => {
          const k = c.q("#lkKey").value.trim(); if (!k) return toast("Nhập key trước", "err");
          const r = await runJob("lic_key", "Kích hoạt " + (kind === "office" ? "Office" : "Windows"), [kind, k]); if (!r.ok) return;
          if (r.result.need_volume) {
            if (await confirmBox("Đổi Office sang Volume", r.result.text + "\n\nTool sẽ tải ODT của Microsoft, cài lại Office kênh Volume (giữ nguyên ứng dụng, 5 - 15 phút, cần mạng) rồi nhập key và kích hoạt.", "🔁 Đổi sang Volume rồi nhập key", false)) {
              const v = await runJob("to_volume", "Đổi Office sang Volume", [k]); if (v.ok) outBox("Đổi Office sang Volume", v.result);
            }
          } else outBox("Kích hoạt " + (kind === "office" ? "Office" : "Windows"), r.result);
          load();
        };
        const oem = c.q("#lkOem");
        if (oem) oem.onclick = async () => { const r = await m("lic_oem");
          if (!r.key) return toast("Máy này không có key Windows OEM trong BIOS", "err");
          c.q("#lkKey").value = r.key; toast("Đã lấy key OEM: " + (r.desc || "")); };
        c.q("#liIid").onclick = async () => { c.q("#liOut").value = "Đang lấy...";
          const r = await m("lic_iid", kind, c.q("#lkKey").value.trim());
          c.q("#liOut").value = r.iid || ""; if (!r.ok) outBox("Lấy Installation ID", {ok: false, text: "Không lấy được Installation ID", out: r.out}); };
        c.q("#liCp").onclick = () => { if (c.q("#liOut").value) { copyLocal(c.q("#liOut").value); toast("Đã chép Installation ID"); } };
        c.q("#lcGo").onclick = async () => { const r = await runJob("lic_cid", "Kích hoạt bằng Confirmation ID", [kind, c.q("#lcCid").value]);
          if (r.ok) { outBox("Kích hoạt qua điện thoại", r.result); load(); } };
        const chk = c.q("#ckChk");
        if (chk) chk.onclick = async () => { const r = await m("crack_check");
          outBox("Kiểm tra crack Office", {ok: !r.found, text: r.found ? "Phát hiện dấu vết kích hoạt lậu:" : "Không thấy dấu vết KMS lậu / Ohook.", out: r.items.join("\n")}); };
        const clr = c.q("#ckClr");
        if (clr) clr.onclick = async () => { if (!(await confirmBox("Dọn crack Office", "Xóa máy chủ KMS, key KMS giả, tệp Ohook, cache giấy phép của Office?\nOffice sẽ về trạng thái chưa kích hoạt - nhập key bản quyền sau đó.", "🧹 Dọn"))) return;
          const r = await runJob("crack_clear", "Dọn crack Office", []); if (r.ok) { outBox("Dọn crack Office", r.result); load(); } };
        const wc = c.q("#wcClr");
        if (wc) wc.onclick = async () => { if (!(await confirmBox("Gỡ key Windows", "Gỡ key Windows đang cài và xóa cấu hình máy chủ KMS?\nWindows sẽ về trạng thái chưa kích hoạt cho tới khi nhập key mới.", "🧹 Gỡ key"))) return;
          const r = await runJob("win_clear_key", "Gỡ key Windows", []); if (r.ok) { outBox("Gỡ key Windows", r.result); load(); } };
      };
      bind(); load();
    }});
}

/* ------------------------------------------------ Thiết lập Office cho văn bản Việt Nam */
let TUNE = {font: "Times New Roman", size: 14, margins: [2, 2, 3, 2], line: 1.15, after: 0, pv: true, nostart: true, nospell: true};
async function offTuneBox() {
  try { TUNE = Object.assign(TUNE, JSON.parse(localStorage.getItem("winaio_tune") || "{}")); } catch (e) { /* bỏ qua */ }
  const n = (id, v, step) => `<input id="${id}" type="number" step="${step || 0.1}" value="${v}" style="width:70px">`;
  const r = await dialog({title: "📝 Thiết lập Office", width: 680, body: `
    <div class="msg">Áp dụng cho mọi văn bản Word mới (lưu vào mẫu Normal.dotm), Excel và PowerPoint. Theo chuẩn văn bản hành chính Việt Nam (Nghị định 30/2020).</div>
    <div class="sugrid mt">
      <div class="sur"><span class="sul">📄 Khổ giấy</span><b>A4 đứng</b><span class="logl" style="margin:0">· đơn vị đo cm</span></div>
      <div class="sur"><span class="sul">📐 Lề (cm)</span>Trên ${n("tT", TUNE.margins[0])} Dưới ${n("tB", TUNE.margins[1])} Trái ${n("tL", TUNE.margins[2])} Phải ${n("tR", TUNE.margins[3])}</div>
      <div class="sur"><span class="sul">🔤 Chữ</span><select id="tF">${["Times New Roman", "Arial", "Calibri", "Tahoma"].map(f => `<option${f === TUNE.font ? " selected" : ""}>${f}</option>`).join("")}</select>
        cỡ ${n("tS", TUNE.size, 0.5)}</div>
      <div class="sur"><span class="sul">↕ Giãn dòng</span>${n("tLn", TUNE.line, 0.05)} lần · cách đoạn sau ${n("tA", TUNE.after, 1)} pt</div>
      <div class="sur"><label class="ck"><input type="checkbox" id="tPv"${TUNE.pv ? " checked" : ""}> Tắt Protected View (mở file tải về không bị khóa sửa)</label></div>
      <div class="sur"><label class="ck"><input type="checkbox" id="tNs"${TUNE.nostart ? " checked" : ""}> Bỏ màn hình Start - mở Word / Excel là vào thẳng trang trắng</label></div>
      <div class="sur"><label class="ck"><input type="checkbox" id="tSp"${TUNE.nospell ? " checked" : ""}> Tắt gạch đỏ / xanh kiểm tra chính tả tiếng Anh</label></div></div>
    <div class="logl">Đóng hết Word / Excel / PowerPoint trước khi bấm. Office phải đã mở lần đầu (đã chấp nhận điều khoản).</div>`,
    buttons: [{text: "Hủy", value: null}, {text: "✓ ÁP DỤNG", cls: "red", def: true, click: c => {
      const v = id => +c.q(id).value;
      TUNE = {font: c.q("#tF").value, size: v("#tS"), margins: [v("#tT"), v("#tB"), v("#tL"), v("#tR")], line: v("#tLn"), after: v("#tA"),
        pv: c.q("#tPv").checked, nostart: c.q("#tNs").checked, nospell: c.q("#tSp").checked};
      try { localStorage.setItem("winaio_tune", JSON.stringify(TUNE)); } catch (e) { /* bỏ qua */ }
      return TUNE; }}]});
  if (!r) return;
  const x = await runJob("off_tune", "Thiết lập Office", [r]); if (x.ok) outBox("Thiết lập Office", x.result);
}
