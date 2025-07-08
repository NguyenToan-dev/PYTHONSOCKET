# 🛡️ Secure FTP Client with Virus Scanning via ClamAVAgent

## 📚 Course Info

* **Môn học**: Mạng máy tính
* **Lớp**: 24C10
* **Nhóm thực hiện**:

  * Nguyễn Khánh Toàn – MSSV: 24127252
  * Nguyễn Tiến Cường – MSSV: 24127337

---

## 🔎 Overview

Dự án mô phỏng hệ thống truyền file an toàn, nơi mọi file cần được quét virus bằng ClamAV trước khi được upload lên FTP Server. Hệ thống gồm:

* **FTP Client**: Chương trình chính, cung cấp các lệnh FTP-like.
* **ClamAVAgent**: Dịch vụ quét virus hoạt động qua socket.
* **FTP Server**: Máy chủ nhận file sạch để lưu trữ.

---

## ⚙️ Thành phần hệ thống

### 1. `ftp_client.py`

* Giao tiếp với FTP Server và ClamAVAgent.
* Hỗ trợ các lệnh như `ls`, `cd`, `put`, `mput`, `get`, `mget`, v.v.
* Tất cả các lệnh upload phải qua quét ClamAV trước.

### 2. `clamav_agent.py`

* Chạy như một server nhận file từ client.
* Dùng `clamscan` để quét virus.
* Gửi kết quả `OK` hoặc `INFECTED` về cho FTP Client.

### 3. FTP Server

* Dùng phần mềm như FileZilla Server.
* Chỉ nhận file nếu đã qua kiểm duyệt từ ClamAVAgent.

---

## ⚙️ Cài đặt và cấu hình

### 🔹 <img src="https://www.clamav.net/assets/clamav-trademark.png" alt="ClamAV Logo" width="20"/> Cài đặt ClamAV trên Windows

#### Giới thiệu

ClamAV là công cụ chống virus mã nguồn mở, đa nền tảng. Hướng dẫn này sẽ giúp bạn cài đặt ClamAV trên Windows với hai chế độ:

* ClamScan: Chế độ quét cơ bản
* ClamDScan: Chế độ daemon cho tốc độ quét nhanh hơn

#### PHẦN 1: CÀI ĐẶT CLAMSCAN

##### Bước 1: Tải về ClamAV

1. Truy cập trang chủ: [https://www.clamav.net/downloads](https://www.clamav.net/downloads)
2. Chọn **Windows** → Tải file `clamav-1.4.3.win.x64.zip`

##### Bước 2: Cài đặt

1. Giải nén file:

```sh
unzip clamav-1.4.3.win.x64.zip -d C:\ClamAV
```

2. Di chuyển vào thư mục cài đặt:

```sh
cd C:\ClamAV\clamav-1.4.3.win.x64
```

##### Bước 3: Cấu hình

1. Sao chép file cấu hình mẫu từ `conf_examples` sang thư mục chính.
2. Đổi tên file:

```
clamd.conf.sample → clamd.conf
freshclam.conf.sample → freshclam.conf
```

3. Mở file và xóa dòng chứa `Example` (thường là dòng số 8).
4. Lưu lại các thay đổi.

##### Bước 4: Cập nhật cơ sở dữ liệu

```sh
cd C:\ClamAV\clamav-1.4.3.win.x64
freshclam.exe
```

(Chờ quá trình tải database hoàn tất)

#### PHẦN 2: CÀI ĐẶT CLAMDSCAN (DAEMON)

##### So sánh ClamScan và ClamD

| Tính năng           | ClamScan   | ClamD        |
| ------------------- | ---------- | ------------ |
| Thời gian khởi động | 10–60 giây | 0.1–0.5 giây |
| Tài nguyên          | Cao        | Thấp         |
| Hiệu suất           | Chậm       | Nhanh        |

##### Bước 1: Cấu hình `clamd.conf`

1. Kết nối TCP:

```
TCPSocket 3310
TCPAddr 127.0.0.1
```

2. Đường dẫn log:

```
LogFile "C:\ClamAV\clamav-1.4.3.win.x64\clamd.log"
LogTime yes
LogFileMaxSize 5M
```

3. Thư mục database:

```
DatabaseDirectory "C:\ClamAV\clamav-1.4.3.win.x64\database"
```

4. Tối ưu hiệu năng (tuỳ chọn):

```
ScanOLE2 no
ScanPDF no
ScanSWF no
```

> Đảm bảo không còn dấu `#` comment trước các dòng trên.

##### Bước 2: Cài đặt daemon

```sh
cd C:\ClamAV\clamav-1.4.3.win.x64
clamd.exe --config-file="clamd.conf"
```

Chạy đến khi xuất hiện: `Self checking every 600 seconds` là thành công.

#### PHẦN 3: CHẠY CODE

1. Mở 1 terminal:

```sh
cd đường_dẫn_tới_clamav_agent.py
python clamav_agent.py
```

2. Mở 1 terminal khác:

```sh
cd đến virtual path bạn đã set trong FileZilla
python ftp_client.py
```

---

### 🔹 FTP Server

* Cài đặt FileZilla Server.
* Tạo user và cấp quyền thư mục.
* Kích hoạt chế độ Passive nếu cần (mport).

---

## 🚀 Cách chạy hệ thống

### Bước 1: Chạy ClamAVAgent

```sh
python clamav_agent.py
```

### Bước 2: Chạy server

```sh
python server.py
```

### Bước 3: Chạy ftp\_client

```sh
python ftp_client.py
```

### Ví dụ lệnh FTP Client:

* `open 127.0.0.1 21`: Kết nối tới FTP server local
* `ls`: Liệt kê file (sau khi xác thực)
* `cd /upload`: Vào thư mục upload
* `put file.pdf`: Gửi file tới ClamAVAgent để quét trước khi upload
* `mput *.txt`: Quét từng file `.txt`, chỉ upload file sạch
* `get report.docx`: Tải file xuống
* `status`: Kiểm tra trạng thái
* `quit`: Thoát

---

## 📐 Sơ đồ kiến trúc hệ thống

```plaintext
+------------------+        +---------------------+        +--------------------+
|   FTP Client     |        |   ClamAV Server     |        |    FTP Server      |
|  (Your code)     |        | (ClamAV Agent code) |        | (e.g., FileZilla)  |
+------------------+        +---------------------+        +--------------------+
         |                          |                              |
         |----[1] Send file to scan------------------------------->|
         |                          |                              |
         |                          |--[2] Run: clamscan <file>--->|
         |                          |                              |
         |<------[3] Return scan result: OK / INFECTED-------------|
         |                          |                              |
         |---[4] If OK: Upload file via FTP----------------------->|
         |                          |                              |
```

---

## 📜 Các lệnh được hỗ trợ

### 📁 File và thư mục

* `ls` – Liệt kê file/thư mục trên server
* `cd` – Đổi thư mục
* `pwd` – Hiển thị thư mục hiện tại
* `mkdir`, `rmdir` – Tạo/Xoá thư mục
* `delete` – Xoá file
* `rename` – Đổi tên file

### ⬇️⬆️ Tải lên / Tải xuống

* `put`, `mput` – Upload 1 hay nhiều file (phải quét virus)
* `get`, `mget` – Tải file từ server
* `prompt` – Bật/tắt xác nhận khi dùng mget, mput

### 🧭 Quản lý phiên

* `ascii`, `binary` – Chế độ truyền file
* `status` – Xem trạng thái kết nối
* `passive` – Bật/tắt chế độ passive
* `open`, `close`, `quit`, `help`
