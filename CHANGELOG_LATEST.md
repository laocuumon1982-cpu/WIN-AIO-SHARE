Win AIO by Duy Anh v5.6

- Đổi tên tab "Bảo trì Windows" thành "Thiết lập Windows" (nội dung giữ nguyên).

v5.5:
- Test máy MAC › Cách dùng trên máy Mac: thêm cách mở SoiMac bằng web https://laocuumon1982-cpu.github.io/SoiMac/ (nút 📋 Chép link, 🌐 Mở thử); cách mở từ USB vẫn giữ (không cần mạng).

v5.4:
- Đổi tên tab "Test máy" thành "Test máy WIN".
- Thêm tab "Test máy MAC" với SoiMac - trang kiểm tra Mac cũ trước khi mua (5 bước: chọn máy theo đời kèm lỗi hay gặp · kiểm tra ngoài, iCloud, MDM · lệnh Terminal · test màn hình, bàn phím, trackpad, loa, camera / mic · kết quả % và báo cáo):
  + Chép SoiMac.html ra USB bằng 1 nút (tự tìm USB / ổ rời), hoặc chọn thư mục khác.
  + Xem trước SoiMac trên máy Windows.
  + Hướng dẫn mở trên Mac bằng Safari (không cần cài, không cần mạng).

v5.3:
- Cài phần mềm: bỏ nút WPS Office. Tách nhóm văn phòng thành 4 nhóm, thứ tự trên xuống:
  + MICROSOFT OFFICE: MS Office, Tiện ích văn phòng
  + ARTCRAFT OFFICE: WordCraft, GridCraft, DeckCraft
  + OFFICE: LibreOffice, OnlyOffice (đổi tên từ ONLYOFFICE)
  + VĂN PHÒNG - PDF: Foxit PDF Reader, Sumatra PDF, Notepad++
  Máy đang dùng bản cũ tự đổi theo khi mở bản mới (các nút khác giữ nguyên).

v5.2:
- Bỏ tab Claude (mục Khác). Phiên đăng nhập Claude mà bản 5.0 / 5.1 đã tạo trên máy (%LOCALAPPDATA%\WinAIO\Claude) được tự xóa khi mở bản này.

v5.1:
- Tab Claude: bỏ nút "Xem gói & mức dùng". Cửa sổ Claude giờ ưu tiên mở bằng Google Chrome (chế độ ứng dụng, không thanh địa chỉ), máy không có Chrome thì dùng Microsoft Edge; mỗi trình duyệt một hồ sơ riêng trong %LOCALAPPDATA%\WinAIO\Claude, không đụng tới Chrome / Edge đang dùng. Đăng xuất & xóa phiên đóng được cả cửa sổ Chrome lẫn Edge của tool.

v5.0:
- Mục Khác: thêm tab 🤖 Claude
  + Mở app Claude: mở app Claude máy tính (đang chạy thì đưa lên trước), dùng đúng tài khoản đang đăng nhập trong app. Máy chưa cài thì mở trang tải claude.ai/download.
  + Cửa sổ Claude: mở claude.ai trong cửa sổ riêng (Microsoft Edge chế độ ứng dụng). Đăng nhập 1 lần, lần sau tự vào.
  + Gói & mức sử dụng: mở thẳng trang Usage của Claude (gói đang dùng, mức đã dùng).
  + Đăng xuất & xóa phiên: đóng cửa sổ Claude của tool, xóa sạch phiên đăng nhập trên máy đó.
  + Riêng tư: phiên đăng nhập chỉ lưu trên máy đó (%LOCALAPPDATA%\WinAIO\Claude), không nằm trong thư mục Data, không lên GitHub, không vào file sao lưu của tool. Tool không lưu tài khoản, mật khẩu hay dự án.
  + App Claude và cửa sổ Claude được mở bằng quyền người dùng thường (dù tool đang chạy quyền Admin) để đăng nhập, kéo thả file bình thường.

v4.9:
- Kho bộ cài WIN: xếp lại 4 công cụ từ trái qua phải: Ventoy · Rufus · AVL Win Master · Anhdv Boot.
- Thông tin & khởi động › Lưu trữ: ổ nào đang bị KHÓA BitLocker hiện cảnh báo đỏ (khung cảnh báo + dòng ổ màu đỏ "ĐANG KHÓA BITLOCKER"); ổ mã hóa BitLocker đang mở khóa có biểu tượng 🔐.

v4.8:
- Bỏ giao diện Robot AI, chỉ giữ giao diện Mặc định · Sáng (bỏ luôn nút ◐ Giao diện; máy đang dùng Robot AI tự về giao diện Sáng).
- Khởi động đặc biệt: nút "Chọn ổ khởi động" đổi biểu tượng thành USB.
- Bảo trì Windows › Tiện ích nhanh: bỏ nhóm "Microsoft Defender" (các chức năng Defender vẫn ở thẻ Defender).
- Kho bộ cài WIN: làm lại thành 1 thẻ "Công cụ USB boot & cài Win" gồm 4 ô gọn: Rufus · AVL Win Master · Anhdv Boot · Ventoy. Mỗi ô có mô tả ngắn, nhãn (Miễn phí / 🔑 Cần KEY bản quyền / ⚠ Format phân vùng cài), nút 🌐 trang chủ và nút Tải & mở. Ô Ventoy bấm "Tạo USB Ventoy" mới mở phần chọn USB / cài Ventoy / chép ISO.

v4.7:
- Giao diện mới "Robot AI" (máy móc · robot · AI), là giao diện mặc định: nền thép tối có lưới mạch, khung HUD có vạch góc phát sáng, nút kim loại góc vát, nút chính màu xanh năng lượng, chữ kiểu máy (Bahnschrift / Consolas), logo lục giác. Nút "◐ Giao diện" chọn Robot AI hoặc Mặc định · Sáng (giữ nguyên như cũ); bỏ các giao diện Mặc định · Tối, Giao diện 01.
- Gộp 3 tab Quản lý, Tiện ích Windows, Sửa lỗi & thiết lập thành 1 tab "Bảo trì Windows", chia 2 nhóm thẻ con:
  + WINDOWS: Tiện ích nhanh · Sửa lỗi & thiết lập · Chạy cùng Win · Driver · Defender
  + PHẦN MỀM: Gỡ tận gốc · MS Store · Cập nhật app (vẫn hiện số app có bản mới)
- Đổi tên "Kho iOS" thành "Kho Firmware iOS".
- Kho bộ cài WIN: thêm ghi chú 🔑 "Cần KEY bản quyền" cho Anhdv Boot Tool (Premium) và AVL Win Master.

v4.6:
- Kho bộ cài WIN: thêm thẻ Anhdv Boot Tool. Mỗi lần bấm "Tải & mở", tool hỏi máy chủ cập nhật của chính Anhdv (api.anhdv.top) lấy số bản mới nhất (hiện 26.5.3), tải đúng file AnhdvBootTool.exe bản đó vào Data\Tools\AnhdvBootTool, kiểm tra sha256 rồi mở bằng quyền Admin. Bản cũ tự xóa; đã có bản mới nhất thì mở luôn không tải lại.

v4.5:
- Kho bộ cài WIN: thêm AVL Win Master (cài Win sạch từ Win đang chạy, WinPE, nạp driver IRST/VMD + Wi-Fi, sao lưu Win, USB cứu hộ). Bấm "Tải & mở AVL" là tool lấy bản mới nhất đúng kiến trúc máy (x64 / x86 / ARM64) từ trang chủ avlwinmaster.badinh.academy, giải nén vào Data\Tools\AVLWinMaster và mở bằng quyền Admin.
- Kho bộ cài MAC: thêm mục "Công cụ cho Mac":
  + macUSB: tải file .dmg bản mới nhất từ GitHub Kruszoneq/macUSB để chép sang Mac.
  + Apple Configurator 2: mở trang Mac App Store (app miễn phí của Apple, khôi phục Mac chip M / T2 bằng cáp USB-C).

v4.4:
- Nút Transub-Player (nhóm Đa phương tiện) đổi sang tải bản PORTABLE (.zip) trong bản phát hành mới nhất của repo Transub-Player (hiện là build-5, TransubPlayer 1.8.0). Tải xong tự giải nén và mở TransubPlayer.exe, không cần cài. Nút cũ trong máy được tự đổi link.
- Bản portable có nhiều file .exe: tool tự chọn đúng file chạy chính thay vì chỉ mở thư mục.

v4.3:
- Tab Thông tin & khởi động (Giao diện 01) làm lại giống hình mẫu: mỗi thẻ một màu riêng (CPU tím, RAM xanh dương, Card đồ họa xanh lá, Mạng cam, Hệ điều hành xanh lá, Bo mạch tím, Lưu trữ xanh), có hình minh họa 3D (chip CPU, thanh RAM, card đồ họa, Wi-Fi / mạng, màn hình, khiên bảo mật, SSD), hình máy laptop / máy bàn lớn ở đầu trang, hành tinh phát sáng sau tiêu đề.
- Mở nhanh: mỗi nút có ô icon màu nổi; Khởi động đặc biệt icon to hơn.

v4.2:
- Giao diện mới "Giao diện 01": kính mờ trong suốt (glassmorphism), viền sáng neon, icon 3D nổi, nút bo tròn. Có 2 màu: Navy (nền xanh navy đêm, viền neon) và Xanh trắng (nền xanh sáng).
- Nút "◐ Giao diện" trên cùng: chọn Mặc định · Sáng, Mặc định · Tối, Giao diện 01 · Navy, Giao diện 01 · Xanh trắng. Bấm là đổi ngay, tool nhớ lựa chọn cho lần mở sau.
- Giao diện 01: thẻ CPU, RAM, GPU, Mạng, Ổ cứng có màu riêng + hình nền lớn; khu Khởi động đặc biệt và Mở nhanh bố trí rộng, chữ to, dễ đọc; sidebar phân nhóm rõ.
- Giao diện gốc giữ nguyên tên "Mặc định", mọi chức năng và tên gọi giữ nguyên.
