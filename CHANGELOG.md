# Nhật ký thay đổi

## v5.2
- Bỏ tab Claude (mục Khác). Phiên đăng nhập Claude mà bản 5.0 / 5.1 đã tạo trên máy (%LOCALAPPDATA%\WinAIO\Claude) được tự xóa khi mở bản này.

## v5.1
- Tab Claude: bỏ nút "Xem gói & mức dùng". Cửa sổ Claude giờ ưu tiên mở bằng Google Chrome (chế độ ứng dụng, không thanh địa chỉ), máy không có Chrome thì dùng Microsoft Edge; mỗi trình duyệt một hồ sơ riêng trong %LOCALAPPDATA%\WinAIO\Claude, không đụng tới Chrome / Edge đang dùng. Đăng xuất & xóa phiên đóng được cả cửa sổ Chrome lẫn Edge của tool.

## v5.0
- Mục Khác: thêm tab 🤖 Claude
  + Mở app Claude: mở app Claude máy tính (đang chạy thì đưa lên trước), dùng đúng tài khoản đang đăng nhập trong app. Máy chưa cài thì mở trang tải claude.ai/download.
  + Cửa sổ Claude: mở claude.ai trong cửa sổ riêng (Microsoft Edge chế độ ứng dụng). Đăng nhập 1 lần, lần sau tự vào.
  + Gói & mức sử dụng: mở thẳng trang Usage của Claude (gói đang dùng, mức đã dùng).
  + Đăng xuất & xóa phiên: đóng cửa sổ Claude của tool, xóa sạch phiên đăng nhập trên máy đó.
  + Riêng tư: phiên đăng nhập chỉ lưu trên máy đó (%LOCALAPPDATA%\WinAIO\Claude), không nằm trong thư mục Data, không lên GitHub, không vào file sao lưu của tool. Tool không lưu tài khoản, mật khẩu hay dự án.
  + App Claude và cửa sổ Claude được mở bằng quyền người dùng thường (dù tool đang chạy quyền Admin) để đăng nhập, kéo thả file bình thường.

## v4.9
- Kho bộ cài WIN: xếp lại 4 công cụ từ trái qua phải: Ventoy · Rufus · AVL Win Master · Anhdv Boot.
- Thông tin & khởi động › Lưu trữ: ổ nào đang bị KHÓA BitLocker hiện cảnh báo đỏ (khung cảnh báo + dòng ổ màu đỏ "ĐANG KHÓA BITLOCKER"); ổ mã hóa BitLocker đang mở khóa có biểu tượng 🔐.

## v4.8
- Bỏ giao diện Robot AI, chỉ giữ giao diện Mặc định · Sáng (bỏ luôn nút ◐ Giao diện; máy đang dùng Robot AI tự về giao diện Sáng).
- Khởi động đặc biệt: nút "Chọn ổ khởi động" đổi biểu tượng thành USB.
- Bảo trì Windows › Tiện ích nhanh: bỏ nhóm "Microsoft Defender" (các chức năng Defender vẫn ở thẻ Defender).
- Kho bộ cài WIN: làm lại thành 1 thẻ "Công cụ USB boot & cài Win" gồm 4 ô gọn: Rufus · AVL Win Master · Anhdv Boot · Ventoy. Mỗi ô có mô tả ngắn, nhãn (Miễn phí / 🔑 Cần KEY bản quyền / ⚠ Format phân vùng cài), nút 🌐 trang chủ và nút Tải & mở. Ô Ventoy bấm "Tạo USB Ventoy" mới mở phần chọn USB / cài Ventoy / chép ISO.

## v4.7
- Giao diện mới "Robot AI" (máy móc · robot · AI), là giao diện mặc định: nền thép tối có lưới mạch, khung HUD có vạch góc phát sáng, nút kim loại góc vát, nút chính màu xanh năng lượng, chữ kiểu máy (Bahnschrift / Consolas), logo lục giác. Nút "◐ Giao diện" chọn Robot AI hoặc Mặc định · Sáng (giữ nguyên như cũ); bỏ các giao diện Mặc định · Tối, Giao diện 01.
- Gộp 3 tab Quản lý, Tiện ích Windows, Sửa lỗi & thiết lập thành 1 tab "Bảo trì Windows", chia 2 nhóm thẻ con:
  + WINDOWS: Tiện ích nhanh · Sửa lỗi & thiết lập · Chạy cùng Win · Driver · Defender
  + PHẦN MỀM: Gỡ tận gốc · MS Store · Cập nhật app (vẫn hiện số app có bản mới)
- Đổi tên "Kho iOS" thành "Kho Firmware iOS".
- Kho bộ cài WIN: thêm ghi chú 🔑 "Cần KEY bản quyền" cho Anhdv Boot Tool (Premium) và AVL Win Master.

## v4.6
- Kho bộ cài WIN: thêm thẻ Anhdv Boot Tool. Mỗi lần bấm "Tải & mở", tool hỏi máy chủ cập nhật của chính Anhdv (api.anhdv.top) lấy số bản mới nhất (hiện 26.5.3), tải đúng file AnhdvBootTool.exe bản đó vào Data\Tools\AnhdvBootTool, kiểm tra sha256 rồi mở bằng quyền Admin. Bản cũ tự xóa; đã có bản mới nhất thì mở luôn không tải lại.

## v4.5
- Kho bộ cài WIN: AVL Win Master. Kho bộ cài MAC: macUSB, Apple Configurator 2.

## v4.4
- Transub-Player: tải bản portable (.zip) thay bộ cài; tự mở đúng exe chính của bản portable.

## v4.3
- Giao diện 01: tab Thông tin & khởi động làm lại theo hình mẫu (thẻ màu riêng, hình minh họa 3D, icon Mở nhanh có ô màu).

## v4.2
- Thêm "Giao diện 01" (Navy / Xanh trắng: kính mờ, viền neon, icon 3D); nút ◐ Giao diện chọn giữa Mặc định và Giao diện 01.

## v4.1
- Bộ nút mặc định + tab Web mặc định theo file sao lưu mới của Duy Anh (24/11/2026 22:24).

## v4.0
- Nhóm TTS & SUB: CIT Voice Studio, Subtitle Translator, LaziBook, VieNeu-TTS.

## v3.9
- Nút Transub-Player (nhóm Đa phương tiện).

## v3.8
- Bộ nút mặc định + tab Web mặc định theo file sao lưu mới của Duy Anh (24/11/2026 17:18).

## v3.7
- Bộ nút mặc định + tab Web mặc định theo file sao lưu của Duy Anh (24/11/2026).

## v3.6
- HiBit Uninstaller về nhóm UNINSTALLER TOOL; 3uTools chuyển sang tab Kho iOS.

## v3.5
- Nút 3uTools (64-bit) luôn lấy bản mới nhất trên 3u.com; nguồn page:.

## v3.4
- Sửa: nút WPS Utility / 360 Remover giải nén được file rar có mật khẩu.

## v3.3
- Nút WPS Utility / 360 Remover lấy file .rar trong kho Codeberg; tự giải nén .rar / .7z.

## v3.2
- Nhóm UNINSTALLER TOOL (WPS Utility, 360 Remover, 360 Security Uninstaller, Avast Clear); nút PicView tự đặt làm trình xem ảnh mặc định; nguồn codeberg:.

## v3.1
- Nút Tiện ích văn phòng (luôn tải bản mới nhất).

## v3.0
- MS Office: Office 365 đủ biến thể, ODT mới nhất, Gỡ Office tận gốc, Bản quyền Office / Windows (key, điện thoại, OEM, đổi Volume, dọn crack), Thiết lập Office cho văn bản Việt Nam.

## v2.9
- Vòng GPU (VRAM đang dùng) thay vòng nhiệt độ CPU; nút Tải & mở Rufus trong Kho bộ cài WIN.

## v2.8
- Kho driver IRST, bộ font chữ đầy đủ gắn sẵn, nút Tiện ích cài Win dạo (bản mới nhất), đổi tên Kho bộ cài MAC.

## v2.7
- Đổi tên Kho bộ cài WIN; thêm Kho bộ cài Mac (bộ cài macOS từ máy chủ Apple) và Kho iOS (IPSW theo ipsw.me).

## v2.6
- Sửa lỗi Windows 1 chạm, Dọn Win 11, Thiết lập máy mới, font tiếng Việt, hồ sơ cài đặt, chuyển phần mềm sang Win mới, USB boot Ventoy, Driver, nhiệt độ CPU, test hiệu năng; tối ưu tốc độ giao diện.

## v2.5
- Quản lý › Cập nhật app: kiểm tra & cập nhật phần mềm đã cài qua winget, số báo trên menu.

## v2.4.2
- Cài mới: nhóm CRACK với 3 nút trống; cập nhật không xóa link đã gắn trong nút.

## v2.4.1
- Tab Web mặc định 12 nút trống để tự gắn link.

## v2.4
- Tab Web: nút mở trang web hay dùng, Admin thêm / sửa / xóa / đổi chỗ.

## v2.3.2
- Kho ISO Win: thêm lại các nút mở trang massgrave.dev theo từng bản Windows.

## v2.3.1
- Kho ISO Win: chọn bản rồi tải thẳng trong tool (link gốc Microsoft, có %, tải tiếp), lấy link cho IDM.

## v2.3
- Tab Kho ISO Win (massgrave.dev + Microsoft), kiểm tra SHA-256 ISO; thêm ONLYOFFICE.

## v2.2.2
- Danh sách mặc định theo cách đã sắp (5 cột); nhóm Tự thêm (IDM, Adobe Reader); xóa nguồn link crack.

## v2.2.1
- Tự vừa màn hình: nút ◀ ▲ ▼ ▶ di chuyển nhóm đủ 4 hướng, chính xác; giữ nguyên cách chia cột đã sắp.

## v2.2
- Kéo thả nhóm và nút phần mềm trong tab Cài phần mềm (Admin).

## v2.1.9
- Nhóm ArtCraft Office Portable, WhatsApp, CIT Voice Studio, Subtitle Translator; nguồn github: luôn bản mới nhất; winget hỗ trợ ID Microsoft Store.

## v2.1.8
- Mật khẩu Admin mặc định HP360; thêm YouTube Downloader Pro; dọn ghi chú cũ.

## v2.1.7
- winget tải nhanh hơn (wininet, chỉ kho winget); mở tool tự kiểm tra / tự sửa ID winget, nhãn ID LỖI; tải lỗi tự làm mới kho và thử lại.

## v2.1.6
- 15 phần mềm chuyển sang winget, sửa ID AnyDesk; nhóm Kho phần mềm (Fshare, Google Drive); test màn hình toàn màn hình thật.

## v2.1.5
- Sửa lỗi cài Zalo PC (link cũ chết) -> cài bằng winget; báo lỗi mạng dễ hiểu; tự kiểm tra link tải khi build.

## v2.1.4
- Mở tool phóng to toàn màn hình, nhóm Hệ thống lên đầu menu; nút Cài phần mềm / Tiện ích tự to ra vừa khung.

## v2.1.3
- Thông tin & khởi động tự phóng to cho đầy màn hình; bảng đèn trạng thái to, không bị cắt chữ.

## v2.1.2
- Thông tin & khởi động vừa 1 màn hình; nút Cài phần mềm thoáng hơn; cột trái không phải kéo.

## v2.1.1
- Kiểu xếp "Tự vừa màn hình": nút nhỏ gọn, không phải kéo lên xuống (Cài phần mềm, Tiện ích Windows).

## v2.1
- Trang Quản lý (khởi động, gỡ tận gốc, MS Store, Defender), Dọn dẹp (rác, phân tích ổ, CapCut, macro Excel, metadata ảnh), Sao lưu (thư mục người dùng, Zalo, Zalo nhiều tài khoản, trình duyệt); xóa mũi tên shortcut; nhóm Mạng; menu gọn; tự sắp xếp nhóm.

## v2.0.2
- Sửa lỗi "invalid originating onefile parent process" sau khi tự cập nhật.

## v2.0
- Khởi động đặc biệt (BIOS, chọn ổ khởi động 1 lần, Safe Mode, Recovery); test sức khỏe ổ cứng (SMART).

## v1.9
- Tab Test máy (màn hình, cảm ứng, bàn phím, loa, micro, trackpad, webcam, pin) + phiếu kiểm tra; cập nhật từ repo WIN-AIO-SHARE.

## v1.8.1
- Sửa lỗi danh sách ổ không hiện ở v1.8 (CLIXML của PowerShell).

## v1.8
- Nhóm Microsoft Defender (bật/tắt Real-time Protection), menu chuột phải kiểu cũ / Win 11; bỏ nút Nguồn hiệu suất cao.

## v1.7
- Thanh % tải về và % cài đặt riêng; % hiện ngay trên nút đang chạy.

## v1.6
- Sắp xếp lại tab Tiện ích Windows (thẻ nhóm, nút đều 2 cột); tab Cài phần mềm nút gọn hơn.

## v1.5
- Tự kiểm tra và cập nhật winget khi mở tool (chạy ngầm); tab Hệ thống làm lại với đồng hồ CPU/RAM trực tiếp.

## v1.4
- Tự chạy lại winget khi lỗi 0x8A150002 (winget cũ), giải thích mã lỗi winget.
- Kiểu xếp Lưới (mặc định): di chuyển nhóm ◀ ▶ ▲ ▼ theo ô lưới; vẫn giữ kiểu Cột dọc.

## v1.3
- Nhóm xếp theo cột dọc (2-6 cột), Admin đổi vị trí nhóm ◀ ▲ ▼ ▶ và vị trí nút ▲▼; danh sách mặc định mới.

## v1.2
- Nút "MS Office": cài / gỡ Office 2016-2024 / 365 bằng ODT chính chủ (Online hoặc Offline), ghim Desktop, nhập key Office.

## v1.1
- Gộp Power & USB Eject (tab "Nguồn & Ổ USB"), thông tin máy chi tiết, 1 file exe (Data chỉ tạo khi cần), nút Cập nhật từ GitHub, dự phòng trình duyệt khi thiếu WebView2.

## v1.0 (bản thử)
- Giao diện kiểu PikPak Auto Save, tab Hệ thống / Cài phần mềm / Tiện ích Windows / Nhật ký / Cài đặt.
- Mở tool không cần mật khẩu; mật khẩu Admin mở nút ✎ sửa tên nút, đổi nguồn app, thêm / xóa nút và nhóm.
