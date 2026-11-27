Win AIO by Duy Anh v5.15

- Tiện ích cài Win dạo: mở tool xong tự tìm hộp nhập mật khẩu (kể cả cửa sổ con), điền mật khẩu rồi bấm nút OK để vào thẳng tool (không thấy nút OK thì nhấn Enter); kết quả ghi vào nhật ký.
- Nhật ký: nút "🧹 Xóa nhật ký cũ" (không cần Admin) - chọn xóa cũ giữ lại hôm nay, hoặc xóa sạch tất cả.
- Bỏ tab Web.
- Nhóm UNINSTALLER TOOL: thêm nút Office Macro Cleaner (Yansuo, bản Portable mới nhất từ Codeberg, tự giải nén mật khẩu 123 rồi mở).

v5.14:
- Kho Firmware iOS: thêm thẻ "iTunes (64-bit)" - nút Tải & cài iTunes luôn lấy bản 64-bit mới nhất từ Apple (đã có đúng bản thì dùng lại) rồi mở bộ cài.
- Nhóm UNINSTALLER TOOL: bỏ nút 360 Total Security Remover và WPS Office Utility & Cleaner; thêm nút Total Cleaner (Google Drive, tự giải nén mật khẩu 123 rồi mở).
- File .zip có mật khẩu giờ giải nén bằng 7-Zip / WinRAR (máy chưa có thì tự cài 7-Zip).
- Tiện ích cài Win dạo: tải bản mới nhất, mở tool xong tự nhập mật khẩu và bấm Enter.

v5.13:
- Thanh bên: mục CÀI ĐẶT chia 3 nhóm:
  + WINDOWS: Cài phần mềm WIN (đổi tên từ Cài phần mềm) · Kho bộ cài WIN
  + MACOS: Cài phần mềm MAC (đổi tên từ Kho phần mềm Mac) · Kho bộ cài MAC
  + iOS: Kho Firmware iOS
- Nhóm ACTIVE: thêm nút "MS Office MacOS" (chưa có link - Admin bấm ✎ để thêm).

v5.12:
- Thêm tab "Kho phần mềm Mac" (dưới Kho bộ cài MAC), thẻ con "MS Office for macOS": bộ cài Office cho Mac chính chủ Microsoft, mỗi bản ghi rõ dùng cho macOS nào:
  + Mới nhất (Microsoft 365 / Office 2024 / 2021): macOS 14 Sonoma trở lên - có thêm từng app Word, Excel, PowerPoint, Outlook, OneNote
  + 16.101: macOS 13 Ventura · 16.88: macOS 12 Monterey · 16.77: macOS 11 Big Sur · 16.66: macOS 10.15 Catalina · 16.54: macOS 10.14 Mojave · 16.43: macOS 10.13 High Sierra
  + Mỗi bản có nút tải bộ Office và bộ Office + Teams (lưu vào Data\Kho Mac\MS Office để chép sang Mac), nút 📋 chép link để mở bằng Safari trên Mac.
  + Cần tài khoản Microsoft 365 hoặc key Office bản quyền để kích hoạt.

v5.11:
- Tối ưu chạy ổn định và nhanh hơn:
  + Mở tool: đọc thông tin máy chạy song song với kiểm tra mạng (máy mất mạng không phải chờ thêm ~6 giây mới hiện thông tin máy).
  + Lệnh chạy quá thời gian hoặc máy thiếu chương trình (winget, PowerShell...) không còn làm hỏng chức năng đang chạy, chỉ báo lỗi rõ ràng; lệnh lỡ hỏi Y/N không còn treo.
  + PowerShell gọi theo đường dẫn đầy đủ trong Windows (máy có PATH bị hỏng vẫn chạy).
  + Trang Nguồn & Ổ USB: chỉ quét lại ổ khi cắm / rút ổ hoặc sau 30 giây (trước đây mở PowerShell 6 giây / lần) - nhẹ máy hơn hẳn; nút ⟳ Làm mới vẫn quét ngay.
  + Vòng cập nhật trạng thái không bị dồn lệnh khi máy đang bận.
  + Dữ liệu (SQLite) ghi nhanh hơn trên USB / ổ chậm.
  + Sửa cảnh báo cú pháp có thể thành lỗi ở Python bản mới.

v5.10:
- Cài phần mềm: vị trí nhóm cố định theo hình mẫu (5 cột, kiểu Tự vừa màn hình):
  + Cột 1: MICROSOFT OFFICE · ARTCRAFT OFFICE · OFFICE · VĂN PHÒNG - PDF · BỘ GÕ TIẾNG VIỆT
  + Cột 2: TRÌNH DUYỆT WEB · HỖ TRỢ TỪ XA · NHẮN TIN - HỌP
  + Cột 3: ĐA PHƯƠNG TIỆN · TTS & SUB · UNINSTALLER TOOL
  + Cột 4: GIẢ LẬP ANDROID · LẬP TRÌNH · THƯ VIỆN HỆ THỐNG
  + Cột 5: NÉN - GIẢI NÉN · TIỆN ÍCH · ACTIVE · KHO PHẦN MỀM (2 nhóm cuối chỉ hiện khi đăng nhập đầy đủ)
- GitHub chỉ giữ bản mới nhất: mỗi lần phát hành bản mới, các bản cũ tự bị xóa.

v5.9:
- Bắt buộc dùng bản mới nhất: nhập đúng mật khẩu xong, tool luôn kiểm tra bản mới trên GitHub. Có bản mới thì tự tải, thay file exe và mở lại - chưa cập nhật xong thì không vào được tool (khóa cả phía chương trình). Không kiểm tra được (mất mạng) thì báo và có nút Thử lại.
- Kiểm tra bản mới có đường dự phòng khi API GitHub chặn (quá 60 lần / giờ trên 1 mạng): đọc thẳng trang Releases.

v5.8:
- Đăng nhập 2 mức:
  + Mật khẩu thường: vào tool nhưng ẩn nhóm ACTIVE và KHO PHẦN MỀM ở tab Cài phần mềm (ẩn từ phía chương trình, không chỉ giấu trên giao diện); không xuất / nhập / khôi phục danh sách nút.
  + Mật khẩu đầy đủ: mở full, thấy mọi nhóm.
  + Đang ở mức thường mà mở 🔒 Admin hoặc tab Cài đặt bằng mật khẩu đầy đủ thì tool chuyển sang mức đầy đủ và hiện luôn 2 nhóm bị ẩn.

v5.7:
- Mở tool phải nhập mật khẩu Admin (không có gợi ý mật khẩu). Nhập sai báo "Mật khẩu không đúng"; chưa đăng nhập thì mọi chức năng của tool đều bị khóa.
- Đăng nhập xong tool tự kiểm tra bản mới trên GitHub: có bản mới là tự tải, thay file exe và mở lại luôn (dữ liệu Data giữ nguyên).
- Vào tab Cài đặt luôn hỏi lại mật khẩu Admin (cùng mật khẩu lúc mở tool).
- Bỏ mục đổi mật khẩu trong Cài đặt; máy đã đổi mật khẩu ở bản cũ được đưa về mật khẩu mặc định.

v5.6:
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
