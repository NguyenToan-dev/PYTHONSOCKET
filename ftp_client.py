import socket
import re
import os
import time
import fnmatch
import glob
from client.config import FTP_HOST, FTP_PORT, FTP_USER, FTP_PASS, CLAMAV_HOST, CLAMAV_PORT
from typing import Optional, List

class FTPSession:
    def __init__(self):
        self.ctrl = None
        self.ctrl_file = None
        self.current_dir = ""
        self.local_current_dir = os.getcwd()
        self.prompt_confirm = True
        self.passive_mode = True
        self.transfer_mode = "binary"  # Mặc định là binary mode

    def _check_connection(self) -> bool:
        """Kiểm tra xem đã kết nối tới FTP server chưa."""
        if not self.ctrl:
            print("❌ Chưa kết nối tới server. Hãy dùng lệnh 'open' trước.")
            return False
        return True

    def connect_ftp(self):
        if self.ctrl:
            print("⚠️ Đã kết nối tới FTP server. Vui lòng 'close' trước khi kết nối lại.")
            return

        # Kết nối control socket
        self.ctrl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ctrl.connect((FTP_HOST, FTP_PORT))
        self.ctrl_file = self.ctrl.makefile('r', encoding='utf-8')
        print(f"<<< {self._get_response()}")  # Đọc phản hồi chào mừng

        # Đăng nhập
        self._send_cmd(f"USER {FTP_USER}")
        self._get_response()
        self._send_cmd(f"PASS {FTP_PASS}")
        self._get_response()
        self.set_transfer_mode(self.transfer_mode)
        self.pwd()  # Cập nhật thư mục hiện tại

    def close(self):
        if self.ctrl:
            self._send_cmd("QUIT")
            self._get_response()
            self.ctrl.close()
            self.ctrl = None
            self.ctrl_file = None
            self.current_dir = ""
            print("✅ Đã đóng kết nối FTP")
        else:
            print("⚠️ Không có kết nối FTP nào để đóng.")

    def _send_cmd(self, cmd: str):
        print(f">>> {cmd}")
        self.ctrl.sendall((cmd + "\r\n").encode())

    def _get_response(self) -> str:
        lines = []
        while True:
            line = self.ctrl_file.readline().strip()
            print(f"<<< {line}")
            lines.append(line)
            if re.match(r'^\d{3} ', line):
                break
        return '\n'.join(lines)

    def _setup_passive(self) -> tuple[str, int]:
        """Thiết lập kết nối passive và trả về (ip, port)."""
        self._send_cmd("PASV")
        resp = self._get_response()
        m = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', resp)
        if not m:
            raise RuntimeError(f"PASV parse failed: {resp}")
        nums = list(map(int, m.groups()))
        ip = ".".join(map(str, nums[:4]))
        port = nums[4] * 256 + nums[5]
        return (ip, port)

    def _open_active_listener(self) -> socket.socket:
        """Mở listener cho Active Mode, gửi PORT."""
        local_ip = '127.0.0.1' if FTP_HOST in ('127.0.0.1', 'localhost') else self.ctrl.getsockname()[0]
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind((local_ip, 0))
        listener.listen(1)
        ip, port = listener.getsockname()
        octets = ip.split('.')
        p1, p2 = divmod(port, 256)
        self._send_cmd(f"PORT {','.join(octets)},{p1},{p2}")
        resp = self._get_response()
        if not resp.startswith('200'):
            listener.close()
            raise RuntimeError(f"PORT failed: {resp}")
        return listener

    def _transfer_command(self, cmd: str, write_func=None) -> bytes:
        """Thực hiện lệnh truyền dữ liệu RETR/STOR/LIST/NLST."""
        if not self._check_connection():
            return b""
        if self.passive_mode:
            ip, port = self._setup_passive()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))
        else:
            listener = self._open_active_listener()

        self._send_cmd(cmd)
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ {cmd} failed: {resp}")
            if not self.passive_mode:
                listener.close()
            return b""

        if not self.passive_mode:
            listener.settimeout(10)
            try:
                conn, _ = listener.accept()
                data_sock = conn
            except socket.timeout:
                listener.close()
                raise RuntimeError("Timeout waiting for active mode connection")
            finally:
                listener.close()

        buffer = b""
        try:
            while True:
                chunk = data_sock.recv(4096)
                if not chunk:
                    break
                if write_func:
                    write_func(chunk)
                else:
                    buffer += chunk
        finally:
            try:
                data_sock.shutdown(socket.SHUT_WR)
                data_sock.close()
            except Exception as e:
                print(f"⚠️ Lỗi khi đóng socket dữ liệu: {str(e)}")

        self._get_response()
        return buffer

    def list(self, path: str = ""):
        if not self._check_connection():
            return
        cmd = "LIST" if not path else f"LIST {path}"
        data = self._transfer_command(cmd)
        if data:
            print("=== DANH SÁCH ===")
            print(data.decode('utf-8', errors='replace'))

    def pwd(self):
        if not self._check_connection():
            return
        self._send_cmd("PWD")
        resp = self._get_response()
        m = re.search(r'"(.+?)"', resp)
        self.current_dir = m.group(1) if m else "/"
        print(f"📂 Thư mục hiện tại: {self.current_dir}")

    def cwd(self, path: str):
        if not self._check_connection():
            return
        if path == "..":
            self._send_cmd("CDUP")
        else:
            self._send_cmd(f"CWD {path}")
        resp = self._get_response()
        if resp.startswith('250'):
            self.pwd()
        else:
            print(f"❌ Lỗi CWD: {resp}")

    def rmdir(self, folder: str, max_retries=3, retry_delay=5):
        if not self._check_connection():
            print(f"❌ Chưa kết nối tới server để xóa thư mục: {folder}")
            return
        print(f"📁 Đang xóa thư mục (đệ quy): {folder}")
        for attempt in range(max_retries):
            try:
                # Thử vào thư mục
                self._send_cmd(f"CWD {folder}")
                resp = self._get_response()
                if not resp.startswith("250"):
                    print(f"❌ Không thể vào thư mục '{folder}': {resp}")
                    return
                # Lấy danh sách nội dung
                data = self._transfer_command("LIST")
                if not data:
                    # Thư mục rỗng, quay lại và xóa
                    self._send_cmd("CWD ..")
                    self._get_response()
                    self._send_cmd(f"RMD {folder}")
                    resp = self._get_response()
                    if resp.startswith("250"):
                        print(f"✅ Đã xóa thư mục: {folder}")
                    else:
                        print(f"❌ Không thể xóa thư mục: {folder}: {resp}")
                    return

                # Xử lý từng mục
                for line in data.decode('utf-8', errors='replace').splitlines():
                    parts = line.split()
                    if len(parts) < 9:
                        continue
                    name = ' '.join(parts[8:])
                    if name in (".", ".."):
                        continue
                    if line.startswith("d"):  # Thư mục
                        self.rmdir(name, max_retries, retry_delay)  # Gọi đệ quy
                    else:  # File
                        self.delete(name)  # Sử dụng hàm delete

                # Quay lại thư mục cha và xóa thư mục
                self._send_cmd("CWD ..")
                self._get_response()
                self._send_cmd(f"RMD {folder}")
                resp = self._get_response()
                if resp.startswith("250"):
                    print(f"✅ Đã xóa thư mục: {folder}")
                    return
                else:
                    print(f"❌ Không thể xóa thư mục: {folder}: {resp}")
                    raise RuntimeError(f"RMD failed: {resp}")

            except (socket.error, RuntimeError) as e:
                print(f"⚠️ Lỗi lần thử {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"🔄 Thử lại sau {retry_delay}s...")
                    time.sleep(retry_delay)
                    if not self._check_connection():
                        print(f"❌ Mất kết nối, không thể xóa thư mục: {folder}")
                        return
                else:
                    print(f"❌ Xóa thư mục thất bại sau {max_retries} lần thử: {folder}")
                    return

    def mkdir(self, folder: str):
        if not self._check_connection():
            return
        self._send_cmd(f"MKD {folder}")
        resp = self._get_response()
        if resp.startswith('257'):
            print(f"✅ Đã tạo thư mục: {folder}")
        else:
            print(f"❌ Lỗi MKD: {resp}")


    def remove_directory_recursive(self, folder_name: str):
        """Hàm dự phòng, gọi rmdir để tương thích với mã cũ."""
        self.rmdir(folder_name)

    def delete(self, filename: str):
        if not self._check_connection():
            return
        self._send_cmd(f"DELE {filename}")
        resp = self._get_response()
        if resp.startswith('250'):
            print(f"✅ Đã xóa file: {filename}")
        else:
            print(f"❌ Lỗi DELE: {resp}")

    def rename(self, old_name: str, new_name: str):
        if not self._check_connection():
            return
        self._send_cmd(f"RNFR {old_name}")
        resp = self._get_response()
        if not resp.startswith('350'):
            print(f"❌ Lỗi RNFR: {resp}")
            return
        self._send_cmd(f"RNTO {new_name}")
        resp = self._get_response()
        if resp.startswith('250'):
            print(f"✅ Đã đổi tên {old_name} → {new_name}")
        else:
            print(f"❌ Lỗi RNTO: {resp}")

    def status(self):
        print(f"🌐 Đã kết nối: {'✅' if self.ctrl else '❌'}")
        print(f"📂 Thư mục hiện tại: {self.current_dir}")
        print(f"🛁 Chế độ passive: {'BẬT' if self.passive_mode else 'TẮT'}")
        print(f"📦 Chế độ truyền: {self.transfer_mode.upper()}")
        print(f"📢 Chế độ xác nhận: {'BẬT' if self.prompt_confirm else 'TẮT'}")
        print(f"📡 Địa chỉ server: {FTP_HOST}:{FTP_PORT}")
        print(f"👤 Người dùng: {FTP_USER}")

    def passive(self, mode: Optional[str] = None):
        if mode is None:
            self.passive_mode = not self.passive_mode
        else:
            self.passive_mode = mode.lower() == 'on'
        status = "BẬT" if self.passive_mode else "TẮT"
        print(f"✅ Đã {status} chế độ passive")

    def set_transfer_mode(self, mode: str):
        if not self._check_connection():
            return
        mode = mode.lower()
        if mode not in ["ascii", "binary"]:
            print("❌ Chế độ không hợp lệ. Chọn 'ascii' hoặc 'binary'")
            return
        self.transfer_mode = mode
        type_code = "A" if mode == "ascii" else "I"
        self._send_cmd(f"TYPE {type_code}")
        resp = self._get_response()
        if resp.startswith('200'):
            print(f"✅ Đã chuyển sang chế độ {mode.upper()}")
        else:
            print(f"❌ Lỗi khi chuyển chế độ: {resp}")

    def prompt(self, mode: Optional[str] = None):
        if mode is None:
            self.prompt_confirm = not self.prompt_confirm
        else:
            self.prompt_confirm = mode.lower() == 'on'
        status = "BẬT" if self.prompt_confirm else "TẮT"
        print(f"✅ Đã {status} chế độ xác nhận")

    def download_ftp(self, remote_filename: str, local_filename: Optional[str] = None):
        if not self._check_connection():
            return
        local_filename = local_filename or os.path.basename(remote_filename)
        local_path = os.path.join(self.local_current_dir, local_filename)
        start_time = time.time()
        total_bytes = 0

        try:
            mode = 'wb' if self.transfer_mode == "binary" else 'w'
            encoding = None if self.transfer_mode == "binary" else 'utf-8'
            with open(local_path, mode, encoding=encoding) as f:
                def write_func(chunk):
                    if self.transfer_mode == "ascii":
                        chunk = chunk.decode('utf-8', errors='replace').replace('\r\n', '\n')
                    f.write(chunk)
                data = self._transfer_command(f"RETR {remote_filename}", write_func=write_func)
                total_bytes = os.path.getsize(local_path) if os.path.exists(local_path) else 0
        except Exception as e:
            print(f"❌ Lỗi khi tải file: {str(e)}")
            if os.path.exists(local_path):
                os.remove(local_path)
            return

        transfer_time = time.time() - start_time
        print(f"✅ Tải thành công: {remote_filename} → {local_path}")
        print(f"📊 Kích thước: {total_bytes} bytes | "
              f"Thời gian: {transfer_time:.2f}s | "
              f"Tốc độ: {total_bytes/transfer_time/1024:.2f} KB/s" if transfer_time > 0 else "")

    def upload_ftp(self, local_filename: str, remote_filename: Optional[str] = None) -> bool:
        local_path = os.path.join(self.local_current_dir, local_filename)
        if not os.path.exists(local_path):
            print(f"❌ File cục bộ không tồn tại: {local_path}")
            return False

        print(f"🔍 Đang quét virus: {local_filename}")
        if not self.scan_with_clamav(local_path):
            print("🔴 KHÔNG thể upload do file chứa virus hoặc lỗi quét!")
            return False

        if not self._check_connection():
            return False

        remote_filename = remote_filename or os.path.basename(local_filename)
        start_time = time.time()
        total_bytes = 0

        if self.passive_mode:
            ip, port = self._setup_passive()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))
        else:
            listener = self._open_active_listener()

        self._send_cmd(f"STOR {remote_filename}")
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Server từ chối upload file: {resp}")
            if not self.passive_mode:
                listener.close()
            return False

        if not self.passive_mode:
            listener.settimeout(10)
            try:
                conn, _ = listener.accept()
                data_sock = conn
            except socket.timeout:
                listener.close()
                raise RuntimeError("Timeout waiting for active mode connection")
            finally:
                listener.close()

        try:
            mode = 'rb' if self.transfer_mode == "binary" else 'r'
            encoding = None if self.transfer_mode == "binary" else 'utf-8'
            with open(local_path, mode, encoding=encoding) as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    if self.transfer_mode == "ascii":
                        chunk = chunk.replace('\n', '\r\n').encode('utf-8', errors='replace')
                    else:
                        chunk = chunk if isinstance(chunk, bytes) else chunk.encode('utf-8')
                    data_sock.sendall(chunk)
                    total_bytes += len(chunk)
        except Exception as e:
            print(f"❌ Lỗi khi đọc file: {str(e)}")
            data_sock.close()
            return False
        finally:
            try:
                data_sock.shutdown(socket.SHUT_WR)
                data_sock.close()
            except Exception as e:
                print(f"⚠️ Lỗi khi đóng socket dữ liệu: {str(e)}")

        transfer_time = time.time() - start_time
        resp = self._get_response()
        if resp.startswith('226'):
            print(f"✅ Upload thành công: {local_path} → {remote_filename}")
            print(f"📊 Kích thước: {total_bytes} bytes | "
                  f"Thời gian: {transfer_time:.2f}s | "
                  f"Tốc độ: {total_bytes/transfer_time/1024:.2f} KB/s" if transfer_time > 0 else "")
            return True
        else:
            print(f"❌ Lỗi khi upload file: {resp}")
            return False

    def scan_with_clamav(self, file_path: str) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((CLAMAV_HOST, CLAMAV_PORT))
                s.sendall(os.path.basename(file_path).encode('utf-8') + b"\n")
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        s.sendall(chunk)
                s.sendall(b"===SCAN_DONE===\n")
                s.settimeout(10)
                response = s.recv(1024).decode('utf-8').strip()
                if response == 'OK':
                    print("✅ File sạch, không chứa virus")
                    return True
                else:
                    print(f"🔴 File có vấn đề: {response}")
                    return False
        except Exception as e:
            print(f"❌ Lỗi quét virus: {str(e)}")
            return False

    def mget(self, pattern: str):
        if not self._check_connection():
            return
        files = self._get_file_list()
        matched_files = fnmatch.filter(files, pattern)
        if not matched_files:
            print(f"🔍 Không tìm thấy file nào khớp: {pattern}")
            return
        print(f"🔍 Tìm thấy {len(matched_files)} file:")
        for i, f in enumerate(matched_files, 1):
            print(f"  {i}. {f}")
        if self.prompt_confirm:
            confirm = input("Bạn có muốn tải tất cả? (y/n): ").lower()
            if confirm != 'y':
                print("⏩ Đã hủy tải")
                return
        success = 0
        for file in matched_files:
            try:
                print(f"⬇️  Đang tải: {file}")
                self.download_ftp(file)
                success += 1
            except Exception as e:
                print(f"❌ Lỗi khi tải {file}: {str(e)}")
        print(f"✅ Đã tải thành công {success}/{len(matched_files)} file")

    def mput(self, pattern: str):
        matched_files = glob.glob(os.path.join(self.local_current_dir, pattern))
        matched_files = [f for f in matched_files if os.path.isfile(f)]
        if not matched_files:
            print(f"🔍 Không tìm thấy file nào khớp: {pattern}")
            return
        print(f"🔍 Tìm thấy {len(matched_files)} file:")
        for i, f in enumerate(matched_files, 1):
            print(f"  {i}. {os.path.basename(f)}")
        if self.prompt_confirm:
            confirm = input("Bạn có muốn upload tất cả? (y/n): ").lower()
            if confirm != 'y':
                print("⏩ Đã hủy upload")
                return
        success = 0
        for file in matched_files:
            try:
                print(f"⬆️  Đang upload: {os.path.basename(file)}")
                if self.upload_ftp(os.path.basename(file)):
                    success += 1
            except Exception as e:
                print(f"❌ Lỗi khi upload {file}: {str(e)}")
        print(f"✅ Đã upload thành công {success}/{len(matched_files)} file")

    def _get_file_list(self) -> List[str]:
        if not self._check_connection():
            return []
        data = self._transfer_command("NLST")
        return data.decode('utf-8', errors='replace').splitlines()

    def help(self):
        print("""
        =================== TRỢ GIÚP FTP CLIENT ===================
        
        Kết nối:
          open       - Kết nối tới FTP server
          close      - Đóng kết nối
          quit/bye   - Thoát chương trình
        
        Thư mục & File:
          ls [path]  - Liệt kê nội dung thư mục
          cd <path>  - Thay đổi thư mục trên server
          pwd        - Xem thư mục hiện tại trên server
          mkdir <dir>- Tạo thư mục mới
          rmdir <dir>- Xóa thư mục và toàn bộ nội dung
          delete <f> - Xóa file
          rename <o> <n> - Đổi tên file/thư mục
        
        Truyền file:
          get <file> - Tải file từ server
          put <file> - Upload file lên server (có quét virus)
          mget <pat> - Tải nhiều file (vd: *.txt)
          mput <pat> - Upload nhiều file
        
        Cài đặt:
          ascii      - Chuyển sang chế độ truyền văn bản
          binary     - Chuyển sang chế độ truyền nhị phân
          passive [on|off] - Bật/tắt chế độ passive
          prompt [on|off] - Bật/tắt xác nhận khi mget/mput
          status     - Xem trạng thái hiện tại
        
        Khác:
          help/?     - Hiển thị trợ giúp này
        
        Lưu ý: Cần 'open' để kết nối trước khi sử dụng các lệnh liên quan đến server.
        ===========================================================
        """)

    def quit(self):
        self.close()
        print("👋 Đã thoát chương trình")
        exit(0)