# Win AIO by Duy Anh

Bộ tiện ích cài Win, cài phần mềm, thiết lập Windows, test laptop / PC, tắt máy khẩn cấp và tháo ổ USB an toàn. Chỉ 1 file exe portable.

Tải bản mới nhất ở mục **Releases** (`Win-AIO-by-Duy-Anh.exe`). Trong tool có nút **⟳ Cập nhật**.

- Mở tool không cần mật khẩu. Nút **🔒 Admin** (mật khẩu mặc định `admin`) mở chế độ sửa nút: đổi tên, đổi link nguồn app, thêm / xóa nút và nhóm.
- Thư mục `Data` kế bên exe chỉ được tạo khi tải app, sửa nút hoặc đổi cài đặt. Bên trong: `winaio.db` (danh sách nút + nhật ký), `config.json` (cài đặt), `Downloads`, `Backup`.
- Bỏ file cài offline vào thư mục `Soft` kế bên exe, rồi đặt nguồn nút dạng `Soft\ten file.exe`.

Chi tiết: xem `HUONG_DAN.txt`. Build: đẩy tag `vX.Y` lên GitHub, workflow tự đóng gói và phát hành.
