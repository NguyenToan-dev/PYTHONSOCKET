# Hướng dẫn cài đặt ClamAV trên Windows

![ClamAV Logo](https://www.clamav.net/assets/clamav-trademark.png)

## Giới thiệu
ClamAV là công cụ chống virus mã nguồn mở, đa nền tảng. Hướng dẫn này sẽ giúp bạn cài đặt ClamAV trên Windows với hai chế độ:
- ClamScan: Chế độ quét cơ bản
- ClamDScan: Chế độ daemon cho tốc độ quét nhanh hơn

## PHẦN 1: CÀI ĐẶT CLAMSCAN

### Bước 1: Tải về ClamAV
1. Truy cập trang chủ: [https://www.clamav.net/downloads](https://www.clamav.net/downloads)
2. Chọn **Windows** → Tải file `clamav-1.4.3.win.x64.zip`

### Bước 2: Cài đặt

# Giải nén file
unzip clamav-1.4.3.win.x64.zip -d C:\ClamAV

# Di chuyển vào thư mục cài đặt  (giả sử là C:\ClamAV\clamav-1.4.3.win.x64)
cd C:\ClamAV\clamav-1.4.3.win.x64

### Bước 3: Cấu hình
1. Sao chép file cấu hình mẫu từ conf_examples sang thư mục chính

2. Đổi tên file (bỏ phần .sample):

3. clamd.conf.sample → clamd.conf

4. freshclam.conf.sample → freshclam.conf

5. Chỉnh sửa file cấu hình:

6. Xóa dòng chứa Example: (thường là dòng số 8)

7. Lưu các thay đổi

### Bước 4: Cập nhật cơ sở dữ liệu
1. Mở **CMD**, chạy:
cd C:\ClamAV\clamav-1.4.3.win.x64
2. Chạy lệnh cập nhật cơ sở dữ liệu:
freshclam.exe → Đợi tải xong (khoảng vài chục giây).

## PHẦN 2: CÀI ĐẶT CLAMDSCAN (DAEMON)
Tại sao nên dùng ClamD?
## So sánh ClamScan và ClamD

| Tính năng             | ClamScan      | ClamD        |
|-----------------------|---------------|--------------|
| Thời gian khởi động   | 10–60 giây    | 0.1–0.5 giây |
| Tài nguyên            | Cao           | Thấp         |
| Hiệu suất             | Chậm          | Nhanh        |

### Bước 1: Cấu hình clamd.conf
Mở file clamd.conf và chỉnh sửa các thông số sau:
# Kết nối TCP
TCPSocket 3310
TCPAddr 127.0.0.1

# Đường dẫn log
LogFile "C:\ClamAV\clamav-1.4.3.win.x64\clamd.log"
LogTime yes
LogFileMaxSize 5M

# Thư mục database
DatabaseDirectory "C:\ClamAV\clamav-1.4.3.win.x64\database"

# Tối ưu hiệu năng (tuỳ chọn)
ScanOLE2 no
ScanPDF no
ScanSWF no
-> Sao cho các phần trên không còn comment (#) trong file nữa
### Bước 2: Cài đặt
1. Mở **CMD**, chạy:
cd C:\ClamAV\clamav-1.4.3.win.x64
2. Chạy clamd.exe --config-file="clamd.conf"
3. Cho tới khi nào cmd hiện ra Self checking every 600 seconds ->Là cài đặt thành công có thể tắt cmd và sử dụng.
