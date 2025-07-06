# Hướng dẫn cài đặt ClamAV trên Windows

## PHẦN 1: CÀI CLAMSCAN TỪ WEB

1. Truy cập trang tải về ClamAV:  
   https://www.clamav.net/downloads  
2. Chọn **Windows** → tải về file `clamav-1.4.3.win.x64.zip`.  
3. Giải nén và lưu ở ví dụ:  C:\Users\tn421\Downloads\clamav-1.4.3.win.x64\clamav-1.4.3.win.x64
4. Vào thư mục `conf_examples`, chọn 2 file cấu hình mẫu, **copy** và **paste** vào thư mục cài đặt ở trên.  
5. Đổi tên 2 file đó để xóa phần đuôi `.sample`.  
6. Mở 2 file vừa đổi tên bằng bất cứ text editor nào, xóa dòng có chứa chữ `Example:` (thường là dòng số 8).  
7. Mở **CMD**, chạy:
cd C:\Users\tn421\Downloads\clamav-1.4.3.win.x64\clamav-1.4.3.win.x64
8. Chạy lệnh cập nhật cơ sở dữ liệu:
freshclam.exe → Đợi tải xong (khoảng vài chục giây).

## PHẦN 2: CÀI CLAMDSCAN (daemon) ĐỂ QUÉT SIÊU NHANH

1. Tại sao nên dùng clamd thay vì clamscan?
- clamscan: mỗi lần khởi chạy phải load toàn bộ cơ sở dữ liệu (~8 triệu mẫu) và khởi tạo engine, mất từ 10–60 giây cho mỗi file.

- clamd: chạy như một dịch vụ daemon, giữ sẵn cơ sở dữ liệu và engine trong RAM, cho phép quét gần như tức thì (~0.1–0.5 giây) qua socket/TCP.
2.Thiết lập clamd trên Windows
Bước 1: Chỉnh sửa clamd.conf
Mở file clamd.conf, bỏ comment (#) và sửa/ thêm các dòng sau:
# Mở TCP daemon trên localhost:3310
TCPSocket 3310
TCPAddr 127.0.0.1

# Đường dẫn file log (phải ghi được)
LogFile "C:\\Users\\tn421\\Downloads\\clamav-1.4.3.win.x64\\clamd.log"
LogTime yes
LogFileMaxSize 5M

# Thư mục cơ sở dữ liệu (nếu không muốn dùng mặc định)
DatabaseDirectory "C:\\Users\\tn421\\Downloads\\clamav-1.4.3.win.x64\\database"

# File lưu PID (tùy chọn)
PidFile "C:\\Users\\tn421\\Downloads\\clamav-1.4.3.win.x64\\clamd.pid"

# Chạy foreground để debug (hoặc bỏ nếu muốn chạy nền)
Foreground yes

# (Tùy chọn) Tắt các bộ quét nặng để tăng tốc:
ScanOLE2 no
ScanPDF no
ScanSWF no
ScanHTML no
ScanMail no
ScanArchive no
ScanImage no

# Không log các file sạch
LogClean no
Bước 2: Tạo thư mục database và cập nhật chữ ký
mkdir "C:\Users\tn421\Downloads\clamav-1.4.3.win.x64\database"
freshclam.exe --datadir="C:\Users\tn421\Downloads\clamav-1.4.3.win.x64\database"
Bước 3: Khởi động clamd
clamd.exe --config-file="clamd.conf"

