import socket
import re
import os
import time
import fnmatch
import glob
import shutil
from config import FTP_HOST, FTP_PORT, FTP_USER, FTP_PASS, CLAMAV_HOST, CLAMAV_PORT

class FTPSession:
    def __init__(self):
        self.ctrl = None
        self.ctrl_file = None
        self.current_dir = ""
        self.local_current_dir = os.getcwd()
        self.prompt_confirm = True
        self.passive_mode = True
        self.transfer_mode = "binary"  # Mặc định là binary mode

    def connect_ftp(self):
        if self.ctrl:
            print("⚠️ Đã kết nối tới FTP server. Vui lòng 'close' trước khi kết nối lại.")
            return

        # Kết nối control socket
        self.ctrl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ctrl.connect((FTP_HOST, FTP_PORT))
        self.ctrl_file = self.ctrl.makefile('r', encoding='utf-8')
        
        # Đọc phản hồi chào mừng
        print(self._get_response())
        
        # Đăng nhập
        self._send_cmd(f"USER {FTP_USER}")
        self._get_response()
        self._send_cmd(f"PASS {FTP_PASS}")
        self._get_response()
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
        return lines[-1]

    def _setup_passive(self):
        """Thiết lập kết nối passive và trả về (ip, port)"""
        self._send_cmd("PASV")
        resp = self._get_response()
        m = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', resp)
        if not m:
            raise Exception(f"Không thể phân tích PASV response: {resp}")
        nums = list(map(int, m.groups()))
        ip = ".".join(map(str, nums[:4]))
        port = nums[4] * 256 + nums[5]
        return (ip, port)

    def list(self, path=""):
        if self.passive_mode:
            ip, port = self._setup_passive()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))
        else:
            # Active mode (không được khuyến nghị)
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.bind(('0.0.0.0', 0))
            data_sock.listen(1)
            ip, port = data_sock.getsockname()
            self._send_cmd(f"PORT {','.join(ip.split('.') + [str(port // 256), str(port % 256)])}")
            self._get_response()

        # Yêu cầu danh sách
        cmd = "LIST" if not path else f"LIST {path}"
        self._send_cmd(cmd)
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Lỗi mở kênh dữ liệu: {resp}")
            data_sock.close()
            return

        # Đọc dữ liệu
        if self.passive_mode:
            conn = data_sock
        else:
            conn, addr = data_sock.accept()
        
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        
        conn.close()
        if not self.passive_mode:
            data_sock.close()

        print("=== DANH SÁCH ===")
        print(data.decode('utf-8', errors='replace'))
        self._get_response()

    def pwd(self):
        self._send_cmd("PWD")
        resp = self._get_response()
        m = re.search(r'"(.+?)"', resp)
        self.current_dir = m.group(1) if m else "/"
        print(f"📂 Thư mục hiện tại: {self.current_dir}")

    def cwd(self, path):
        if path == "..":
            self._send_cmd("CDUP")
        else:
            self._send_cmd(f"CWD {path}")
        
        resp = self._get_response()
        if resp.startswith('250'):
            self.pwd()  # Cập nhật thư mục hiện tại
        else:
            print(f"❌ Lỗi CWD: {resp}")

    def lcd(self, path):
        """Thay đổi thư mục cục bộ"""
        try:
            os.chdir(path)
            self.local_current_dir = os.getcwd()
            print(f"📂 Thư mục cục bộ hiện tại: {self.local_current_dir}")
        except Exception as e:
            print(f"❌ Không thể thay đổi thư mục: {str(e)}")

    def mkdir(self, folder):
        self._send_cmd(f"MKD {folder}")
        resp = self._get_response()
        if resp.startswith('257'):
            print(f"✅ Đã tạo thư mục: {folder}")
        else:
            print(f"❌ Lỗi MKD: {resp}")

    def rmdir(self, folder):
        self._send_cmd(f"RMD {folder}")
        resp = self._get_response()
        if resp.startswith('250'):
            print(f"✅ Đã xóa thư mục: {folder}")
        else:
            print(f"❌ Lỗi RMD: {resp}")

    def delete(self, filename):
        self._send_cmd(f"DELE {filename}")
        resp = self._get_response()
        if resp.startswith('250'):
            print(f"✅ Đã xóa file: {filename}")
        else:
            print(f"❌ Lỗi DELE: {resp}")

    def rename(self, old_name, new_name):
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
        print(f"💻 Thư mục cục bộ: {self.local_current_dir}")
        print(f"🛁 Chế độ passive: {'BẬT' if self.passive_mode else 'TẮT'}")
        print(f"📦 Chế độ truyền: {self.transfer_mode.upper()}")
        print(f"📢 Chế độ xác nhận: {'BẬT' if self.prompt_confirm else 'TẮT'}")
        print(f"📡 Địa chỉ server: {FTP_HOST}:{FTP_PORT}")
        print(f"👤 Người dùng: {FTP_USER}")

    def passive(self, mode=None):
        if mode is None:
            self.passive_mode = not self.passive_mode
        else:
            self.passive_mode = mode.lower() == 'on'
        
        status = "BẬT" if self.passive_mode else "TẮT"
        print(f"✅ Đã {status} chế độ passive")

    def set_transfer_mode(self, mode):
        mode = mode.lower()
        if mode in ["ascii", "binary"]:
            self.transfer_mode = mode
            self._send_cmd(f"TYPE {mode.upper()[0]}")
            self._get_response()
            print(f"✅ Đã chuyển sang chế độ {mode.upper()}")
        else:
            print("❌ Chế độ không hợp lệ. Chọn 'ascii' hoặc 'binary'")

    def prompt(self, mode=None):
        if mode is None:
            self.prompt_confirm = not self.prompt_confirm
        else:
            self.prompt_confirm = mode.lower() == 'on'
        
        status = "BẬT" if self.prompt_confirm else "TẮT"
        print(f"✅ Đã {status} chế độ xác nhận")

    def download_ftp(self, remote_filename, local_filename=None):
        if not self.ctrl:
            print("❌ Chưa kết nối tới server. Hãy dùng lệnh 'open' trước.")
            return

        local_filename = local_filename or os.path.basename(remote_filename)
        local_path = os.path.join(self.local_current_dir, local_filename)

        if self.passive_mode:
            ip, port = self._setup_passive()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))
        else:
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.bind(('0.0.0.0', 0))
            data_sock.listen(1)
            ip, port = data_sock.getsockname()
            self._send_cmd(f"PORT {','.join(ip.split('.') + [str(port // 256), str(port % 256)])}")
            self._get_response()

        self._send_cmd(f"RETR {remote_filename}")
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Server từ chối tải file: {resp}")
            return

        if self.passive_mode:
            conn = data_sock
        else:
            conn, addr = data_sock.accept()

        start_time = time.time()
        total_bytes = 0
        
        try:
            with open(local_path, 'wb') as f:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_bytes += len(chunk)
        except Exception as e:
            print(f"❌ Lỗi khi ghi file: {str(e)}")
            if os.path.exists(local_path):
                os.remove(local_path)
        
        conn.close()
        if not self.passive_mode:
            data_sock.close()

        transfer_time = time.time() - start_time
        resp = self._get_response()
        
        if resp.startswith('226'):
            print(f"✅ Tải thành công: {remote_filename} → {local_path}")
            print(f"📊 Kích thước: {total_bytes} bytes | "
                f"Thời gian: {transfer_time:.2f}s | "
                f"Tốc độ: {total_bytes/transfer_time/1024:.2f} KB/s")
        else:
            print(f"❌ Lỗi khi tải file: {resp}")

    def upload_ftp(self, local_filename, remote_filename=None):
        # Kiểm tra file cục bộ
        local_path = os.path.join(self.local_current_dir, local_filename)
        if not os.path.exists(local_path):
            print(f"❌ File cục bộ không tồn tại: {local_path}")
            return False
            
        # Quét virus
        print(f"🔍 Đang quét virus: {local_filename}")
        if not self.scan_with_clamav(local_path):
            print("🔴 KHÔNG thể upload do file chứa virus hoặc lỗi quét!")
            return False
            
        if not self.ctrl:
            print("❌ Chưa kết nối tới server. Hãy dùng lệnh 'open' trước.")
            return False

        remote_filename = remote_filename or os.path.basename(local_filename)

        if self.passive_mode:
            ip, port = self._setup_passive()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))
        else:
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.bind(('0.0.0.0', 0))
            data_sock.listen(1)
            ip, port = data_sock.getsockname()
            self._send_cmd(f"PORT {','.join(ip.split('.') + [str(port // 256), str(port % 256)])}")
            self._get_response()

        self._send_cmd(f"STOR {remote_filename}")
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Server từ chối upload file: {resp}")
            return False

        if self.passive_mode:
            conn = data_sock
        else:
            conn, addr = data_sock.accept()

        start_time = time.time()
        total_bytes = 0
        
        try:
            with open(local_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    conn.sendall(chunk)
                    total_bytes += len(chunk)
        except Exception as e:
            print(f"❌ Lỗi khi đọc file: {str(e)}")
        
        conn.close()
        if not self.passive_mode:
            data_sock.close()

        transfer_time = time.time() - start_time
        resp = self._get_response()
        
        if resp.startswith('226'):
            print(f"✅ Upload thành công: {local_path} → {remote_filename}")
            print(f"📊 Kích thước: {total_bytes} bytes | "
                f"Thời gian: {transfer_time:.2f}s | "
                f"Tốc độ: {total_bytes/transfer_time/1024:.2f} KB/s")
            return True
        else:
            print(f"❌ Lỗi khi upload file: {resp}")
            return False

    def scan_with_clamav(self, file_path):
        """Kết nối tới ClamAV Agent"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((CLAMAV_HOST, CLAMAV_PORT))
                
                # Gửi tên file
                s.sendall(os.path.basename(file_path).encode() + b"\n")
                
                # Gửi nội dung file
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        s.sendall(chunk)
                
                # Đánh dấu kết thúc
                s.sendall(b"===SCAN_DONE===")
                
                # Nhận kết quả
                return s.recv(1024) == b'OK'
        except Exception as e:
            print(f"❌ Lỗi quét virus: {str(e)}")
            return False

    def mget(self, pattern):
        """Tải nhiều file từ server"""
        if not self.ctrl:
            print("❌ Chưa kết nối tới server. Hãy dùng lệnh 'open' trước.")
            return

        # Lấy danh sách file
        files = self._get_file_list()
        matched_files = fnmatch.filter(files, pattern)
        
        if not matched_files:
            print(f"🔍 Không tìm thấy file nào khớp: {pattern}")
            return
        
        print(f"🔍 Tìm thấy {len(matched_files)} file:")
        for i, f in enumerate(matched_files, 1):
            print(f"  {i}. {f}")
        
        # Xác nhận với người dùng
        if self.prompt_confirm:
            confirm = input("Bạn có muốn tải tất cả? (y/n): ").lower()
            if confirm != 'y':
                print("⏩ Đã hủy tải")
                return
        
        # Tải từng file
        success = 0
        for file in matched_files:
            try:
                print(f"⬇️  Đang tải: {file}")
                self.download_ftp(file)
                success += 1
            except Exception as e:
                print(f"❌ Lỗi khi tải {file}: {str(e)}")
        
        print(f"✅ Đã tải thành công {success}/{len(matched_files)} file")

    def mput(self, pattern):
        """Upload nhiều file lên server"""
        # Tìm file cục bộ
        matched_files = glob.glob(os.path.join(self.local_current_dir, pattern))
        matched_files = [f for f in matched_files if os.path.isfile(f)]
        
        if not matched_files:
            print(f"🔍 Không tìm thấy file nào khớp: {pattern}")
            return
        
        print(f"🔍 Tìm thấy {len(matched_files)} file:")
        for i, f in enumerate(matched_files, 1):
            print(f"  {i}. {os.path.basename(f)}")
        
        # Xác nhận với người dùng
        if self.prompt_confirm:
            confirm = input("Bạn có muốn upload tất cả? (y/n): ").lower()
            if confirm != 'y':
                print("⏩ Đã hủy upload")
                return
        
        # Upload từng file
        success = 0
        for file in matched_files:
            try:
                print(f"⬆️  Đang upload: {os.path.basename(file)}")
                if self.upload_ftp(os.path.basename(file)):
                    success += 1
            except Exception as e:
                print(f"❌ Lỗi khi upload {file}: {str(e)}")
        
        print(f"✅ Đã upload thành công {success}/{len(matched_files)} file")

    def _get_file_list(self):
        """Lấy danh sách file từ server"""
        if self.passive_mode:
            ip, port = self._setup_passive()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))
        else:
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.bind(('0.0.0.0', 0))
            data_sock.listen(1)
            ip, port = data_sock.getsockname()
            self._send_cmd(f"PORT {','.join(ip.split('.') + [str(port // 256), str(port % 256)])}")
            self._get_response()

        self._send_cmd("NLST")
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Lỗi lấy danh sách file: {resp}")
            return []

        if self.passive_mode:
            conn = data_sock
        else:
            conn, addr = data_sock.accept()

        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        
        conn.close()
        if not self.passive_mode:
            data_sock.close()

        self._get_response()
        return data.decode('utf-8').splitlines()

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
          lcd <path> - Thay đổi thư mục cục bộ
          pwd        - Xem thư mục hiện tại trên server
          mkdir <dir>- Tạo thư mục mới
          rmdir <dir>- Xóa thư mục
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
        
        ===========================================================
        """)

    def quit(self):
        self.close()
        print("👋 Đã thoát chương trình")
        exit(0)
