# Win AIO by Duy Anh

Bộ tiện ích cài Win, cài phần mềm, thiết lập Windows, quản lý khởi động / gỡ tận gốc / Defender, dọn dẹp, sao lưu (thư mục người dùng, Zalo, trình duyệt), test laptop / PC, tắt máy khẩn cấp và tháo ổ USB an toàn. Chỉ 1 file exe portable.

Tải bản mới nhất ở mục **Releases** (`Win-AIO-by-Duy-Anh.exe`). Trong tool có nút **⟳ Cập nhật**.

**Không cần USB — mở PowerShell trên máy bất kỳ và gõ 1 dòng:**

```powershell
irm https://raw.githubusercontent.com/laocuumon1982-cpu/WIN-AIO-SHARE/main/aio.ps1 | iex
```

Lệnh tự tải bản mới nhất về `%LOCALAPPDATA%\WinAIO` rồi mở tool (bấm Yes ở hộp UAC). Chạy lại lần sau chỉ tải khi có bản mới.

- Mở tool không cần mật khẩu. Nút **🔒 Admin** (mật khẩu mặc định `HP360`) mở chế độ sửa nút: đổi tên, đổi link nguồn app, thêm / xóa nút và nhóm.
- Thư mục `Data` kế bên exe chỉ được tạo khi tải app, sửa nút hoặc đổi cài đặt. Bên trong: `winaio.db` (danh sách nút + nhật ký), `config.json` (cài đặt), `Downloads`, `Backup`.
- Bỏ file cài offline vào thư mục `Soft` kế bên exe, rồi đặt nguồn nút dạng `Soft\ten file.exe`.

Chi tiết: xem `HUONG_DAN.txt`. Build: đẩy tag `vX.Y` lên GitHub, workflow tự đóng gói và phát hành.
