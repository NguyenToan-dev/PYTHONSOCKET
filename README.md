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

## 🏗️ Cài đặt và cấu hình

### 🔹 Cài đặt ClamAV trên Windows

1. Truy cập trang:
   👉 [https://www.clamav.net/downloads](https://www.clamav.net/downloads)

2. Tải file `.zip` (VD: `clamav-1.4.3.win.x64.zip`)

3. Giải nén vào thư mục (VD: `D:\ClamAV`)

4. **Cập nhật PATH**:

* Mở **System Environment Variables**
* Thêm `D:\ClamAV` vào `Path`

5. **Kiểm tra**:

```sh
clamscan --version
```

### 🛠️🔹 Tải ClamAV Database

Tạo thư mục database và tải 3 file:

* [`main.cvd`](https://database.clamav.net/main.cvd)
* [`daily.cvd`](https://database.clamav.net/daily.cvd)
* [`bytecode.cvd`](https://database.clamav.net/bytecode.cvd)

> Gợi ý: Dùng `--datadir` nếu ClamAV không tìm thấy database.

---

### 🔹 FTP Server

* Cài FileZilla Server
* Tạo user, cấp quyền
* Kích hoạt Passive mode (nếu cần)

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

### Lệnh mẫu:

* `open 127.0.0.1 21`
* `put file.pdf`
* `mput *.txt`
* `get report.docx`
* `status`, `quit`

---

## 📀 Sơ đồ kiến trúc hệ thống

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

## 📜 Lệnh được hỗ trợ

### 📁 File và thư mục

* `ls`, `cd`, `pwd`, `mkdir`, `rmdir`, `delete`, `rename`

### ⬇️⬆️ Truyền file

* `put`, `mput`, `get`, `mget`, `prompt`

### 🧱 Quản lý phiên

* `ascii`, `binary`, `status`, `passive`, `open`, `close`, `quit`, `help`

---

# Hướng dẫn cài đặt ClamAV trên Windows

![ClamAV Logo](https://www.clamav.net/assets/clamav-trademark.png)

## Giới thiệu

ClamAV là công cụ chống virus mã nguồn mở, đa nền tảng.

## PHẦN 1: CÀI ĐẶT CLAMSCAN

### Bước 1: Tải ClamAV

* Tải `clamav-1.4.3.win.x64.zip`

### Bước 2: Giải nén

* Vào thư mục cài: `C:\ClamAV\clamav-1.4.3.win.x64`

### Bước 3: Cấu hình

* Copy file `clamd.conf.sample`, `freshclam.conf.sample`
* Bỏ comment `Example`

### Bước 4: Cập nhật database

```sh
freshclam.exe
```

---

## PHẦN 2: CLAMDSCAN (DAEMON)

### So sánh ClamScan vs ClamD

| Tính năng           | ClamScan   | ClamD        |
| ------------------- | ---------- | ------------ |
| Thời gian khởi động | 10–60 giây | 0.1–0.5 giây |
| Tài nguyên          | Cao        | Thấp         |
| Hiệu suất           | Chậm       | Nhanh        |

### Bước 1: Cấu hình `clamd.conf`

* `TCPSocket 3310`, `TCPAddr 127.0.0.1`
* `LogFile`, `LogTime`, `DatabaseDirectory`
* Bỏ comment (#) trước các dòng quan trọng

### Bước 2: Chạy daemon

```sh
clamd.exe --config-file="clamd.conf"
```

* Chờ `Self checking every 600 seconds` xuất hiện → OK
