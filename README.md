# 🛡️ Secure FTP Client with Virus Scanning via ClamAVAgent

## 📚 Course Info
- **Môn học**: Mạng máy tính
- **Lớp**: 24C10
- **Nhóm thực hiện**:
  - Nguyễn Khánh Toàn – MSSV: 24127252
  - Nguyễn Tiến Cường – MSSV: 24127337

---

## 🔎 Overview

Dự án mô phỏng hệ thống truyền file an toàn, nơi mọi file cần được quét virus bằng ClamAV trước khi được upload lên FTP Server. Hệ thống gồm:

- **FTP Client**: Chương trình chính, cung cấp các lệnh FTP-like.
- **ClamAVAgent**: Dịch vụ quét virus hoạt động qua socket.
- **FTP Server**: Máy chủ nhận file sạch để lưu trữ.

---

## ⚙️ Thành phần hệ thống

### 1. `ftp_client.py`
- Giao tiếp với FTP Server và ClamAVAgent.
- Hỗ trợ các lệnh như `ls`, `cd`, `put`, `mput`, `get`, `mget`, v.v.
- Tất cả các lệnh upload phải qua quét ClamAV trước.

### 2. `clamav_agent.py`
- Chạy như một server nhận file từ client.
- Dùng `clamscan` để quét virus.
- Gửi kết quả `OK` hoặc `INFECTED` về cho FTP Client.

### 3. FTP Server
- Dùng phần mềm như FileZilla Server.
- Chỉ nhận file nếu đã qua kiểm duyệt từ ClamAVAgent.

---

## 🏗️ Cài đặt và cấu hình

### 🔹 Cài đặt ClamAV trên Windows

1. Truy cập trang:
   👉 [https://www.clamav.net/downloads](https://www.clamav.net/downloads)

2. Trong mục **ClamAV for Windows**, tải file `.zip` có tên như:

3. Giải nén vào thư mục ví dụ:

4. **Cập nhật biến môi trường PATH**:
- Mở **Start** → gõ `Environment Variables`
- Chọn **Edit the system environment variables**
- Trong cửa sổ System Properties, chọn **Environment Variables**
- Trong phần **System variables**, chọn `Path` → **Edit** → **New**
- Thêm đường dẫn:
  ```
  D:\ClamAV
  ```

5. **Kiểm tra cài đặt**:
- Mở lại **Command Prompt**
- Gõ:
  ```
  clamscan --version
  ```
- Nếu hiện ra phiên bản ClamAV → bạn đã cài đặt thành công!

---
### 🛠️🔹 Tải ClamAV Database (tải nếu muốn scan file được)

#### 🔧 Bước 1: Tạo thư mục chứa database

Tạo thư mục theo đường dẫn: D:\clamav-1.4.3.win.x64\clamav-1.4.3.win.x64\database

> 📁 Đây là nơi ClamAV sẽ tìm các file `*.cvd` chứa dữ liệu virus.

---

#### 🌐 Bước 2: Tải các file cơ sở dữ liệu

Truy cập từng liên kết dưới đây để tải về 3 file cần thiết:

| Tên file      | Link tải xuống                                               |
|---------------|--------------------------------------------------------------|
| `main.cvd`    | https://database.clamav.net/main.cvd                         |
| `daily.cvd`   | https://database.clamav.net/daily.cvd                        |
| `bytecode.cvd`| https://database.clamav.net/bytecode.cvd                     |

#### 👉 Cách tải:
- Mở từng link trên trong trình duyệt.
- Nhấn **chuột phải** → **Save As...**
- Chọn thư mục `database` đã tạo ở bước trên để lưu lại.

---

✅ Sau khi tải xong, bạn đã có đầy đủ dữ liệu để `clamscan` hoạt động mà không cần kết nối mạng.

> 💡 *Gợi ý:* Nếu ClamAV không tự phát hiện thư mục database, bạn có thể thêm tùy chọn `--datadir` khi chạy `clamscan`, ví dụ:
clamscan --datadir="D:\clamav-1.4.3.win.x64\clamav-1.4.3.win.x64\database" file.txt

---


### 🔹 FTP Server
- Cài đặt FileZilla Server.
- Tạo user và cấp quyền thư mục.
- Kích hoạt chế độ Passive nếu cần (mport).

---


## 🚀 Cách chạy hệ thống

### Bước 1: Chạy ClamAVAgent
powershell: python clamav_agent.py
### Bước 2: Chạy server
powershell: python server.py
### Bước 3: Chạy ftp_client
powershell: python ftp_client.py

### Ví dụ lệnh FTP Client:
open 127.0.0.1 21
ls
cd /upload
put file.pdf        # → Gửi tới ClamAVAgent → Nếu OK → Upload
mput *.txt          # → Quét từng file → Chỉ upload file sạch
get report.docx
status
quit



📐 Sơ đồ kiến trúc hệ thống:
+---------------------+
|     FTP Client      | <------- User command
|  (ftp_client.py)    |
+----------+----------+
           |
   Gửi file để quét virus
           |
           v
+---------------------+
|    ClamAVAgent      |
|  (clamav_agent.py)  |
+----------+----------+
           |
   Kết quả OK / INFECTED
           |
           v
+---------------------+
|     FTP Server      |
|  (FileZilla/vsftpd) |
+---------------------+

📜 Các lệnh được hỗ trợ
📁 File và thư mục
+ ls – Liệt kê file/thư mục trên server

+ cd – Đổi thư mục

+ pwd – Hiển thị thư mục hiện tại

+ mkdir, rmdir – Tạo/Xoá thư mục

+ delete – Xoá file

+ rename – Đổi tên file

⬇️⬆️ Tải lên / Tải xuống
+ put, mput – Upload 1 hay nhiều file (phải quét virus)

+ get, mget – Tải file từ server

+ prompt – Bật/tắt xác nhận khi dùng mget, mput

🧭 Quản lý phiên
+ ascii / binary – Chế độ truyền file

+ status – Xem trạng thái kết nối

+ passive – Bật/tắt chế độ passive

+ open, close, quit, help

