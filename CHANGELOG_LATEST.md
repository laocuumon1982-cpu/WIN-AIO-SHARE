Win AIO by Duy Anh v4.7

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
