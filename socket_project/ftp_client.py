import socket
import ssl
import re
import os
import time
import fnmatch
from client.config import FTP_HOST, FTP_PORT, FTP_USER, FTP_PASS, CLAMAV_HOST, CLAMAV_PORT

class FTPSession:
    def __init__(self):
        # Thiết lập SSL/TLS context
        self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
        self.context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

        self.ctrl = None
        self.ctrl_file = None
        self.current_dir = ""
        self.prompt_confirm = True

    def connect_ftp(self):
        if self.ctrl:
            print("⚠️ Đã kết nối tới FTP server. Vui lòng 'close' trước khi kết nối lại.")
            return

        # Kết nối control socket và thực hiện AUTH TLS
        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw.connect((FTP_HOST, FTP_PORT))
        print(raw.recv(1024).decode().strip())

        raw.sendall(b'AUTH TLS\r\n')
        print(raw.recv(1024).decode().strip())

        self.ctrl = self.context.wrap_socket(raw, server_hostname=FTP_HOST, do_handshake_on_connect=True)
        self.ctrl_file = self.ctrl.makefile('r', encoding='utf-8')

        # Đăng nhập
        self._send_cmd(f"USER {FTP_USER}")
        self._get_response()
        self._send_cmd(f"PASS {FTP_PASS}")
        self._get_response()

        # Thiết lập bảo mật dữ liệu
        self._send_cmd("PBSZ 0")
        self._get_response()
        self._send_cmd("PROT P")
        self._get_response()

    def close(self):
        if self.ctrl:
            self._send_cmd("QUIT")
            self._get_response()
            self.ctrl.close()
            self.ctrl = None
            self.ctrl_file = None
            self.current_dir = ""  # Reset current_dir khi đóng kết nối
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

    def list(self):
        # Dùng EPSV + TLS session reuse cho kênh dữ liệu
        self._send_cmd("EPSV")
        resp = self._get_response()
        m = re.search(r"\(\|\|\|(\d+)\|\)", resp)
        if not m:
            print(f"⚠️ Không thể phân tích EPSV: {resp}")
            return
        port = int(m.group(1))

        data_raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_raw.connect((FTP_HOST, port))
        data_sock = self.context.wrap_socket(
            data_raw,
            server_hostname=FTP_HOST,
            session=self.ctrl.session,
            do_handshake_on_connect=True
        )

        # Yêu cầu danh sách
        self._send_cmd("LIST")
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Lỗi mở kênh dữ liệu: {resp}")
            data_sock.close()
            return

        # Đọc dữ liệu
        data = b""
        while True:
            chunk = data_sock.recv(4096)
            if not chunk:
                break
            data += chunk
        data_sock.close()

        print("=== DANH SÁCH ===")
        print(data.decode('utf-8', errors='replace'))
        self._get_response()

    def pwd(self):
        self._send_cmd("PWD")
        resp = self._get_response()
        m = re.search(r'"(.+?)"', resp)
        self.current_dir = m.group(1) if m else self.current_dir
        print(f"📂 Thư mục hiện tại: {self.current_dir or '/'}")

    def cwd(self, path):
        self._send_cmd(f"CWD {path}")
        resp = self._get_response()
        if resp.startswith('250'):
            # Cập nhật current_dir tương đối
            if path == '..':
                self.current_dir = '/'.join(self.current_dir.strip('/').split('/')[:-1])
            elif self.current_dir:
                self.current_dir = f"{self.current_dir}/{path.strip('/')}"
            else:
                self.current_dir = path.strip('/')
            print(f"✅ Đã chuyển đến: {self.current_dir}")
        else:
            print(f"❌ Lỗi CWD: {resp}")

    def mkd(self, folder):
        self._send_cmd(f"MKD {folder}")
        resp = self._get_response()
        if resp.startswith('257'):
            print(f"✅ Đã tạo thư mục: {folder}")
        else:
            print(f"❌ Lỗi MKD: {resp}")

    def rn(self, old_name, new_name):
        self._send_cmd(f"RNFR {old_name}")
        resp = self._get_response()
        if not resp.startswith('350'):
            print(f"❌ Lỗi RNFR: {resp}")
            return
        self._send_cmd(f"RNTO {new_name}")
        resp = self._get_response()
        if resp.startswith('250'):
            print(f"✅ Đổi tên {old_name} → {new_name}")
        else:
            print(f"❌ Lỗi RNTO: {resp}")

    def status(self):
        print(f"🌐 Đã kết nối: {'✅' if self.ctrl else '❌'}")
        print(f"📂 Thư mục hiện tại: {self.current_dir or '/'}")
        print(f"🛁 Chế độ passive: Đang được sử dụng mặc định qua EPSV (không tắt được trong phiên bản này)")
        print(f"🔒 TLS session reuse: {'✅' if self.ctrl and hasattr(self.ctrl, 'session') else '❌'}")
        print(f"📢 Chế độ xác nhận khi mget/mput: {'BẬT' if self.prompt_confirm else 'TẮT'}")
        print(f"📦 Địa chỉ server: {FTP_HOST}:{FTP_PORT}")
        print(f"👤 Người dùng: {FTP_USER}")
    def passive(self):
        print("ℹ️ Chế độ passive đang được dùng mặc định qua EPSV (không thể tắt trong phiên bản này).")

    def help(self):
                print("""
        =================== TRỢ GIÚP CÁC LỆNH FTP ===================

        Lệnh kết nối và trạng thái:
        open               - Kết nối tới FTP server sử dụng TLS bảo mật.
        close              - Ngắt kết nối khỏi server.
        status             - Hiển thị thông tin kết nối hiện tại và trạng thái bảo mật.

        Cài đặt chế độ:
        passive [on|off]   - Bật hoặc tắt chế độ truyền dữ liệu Passive (khuyên dùng).
        prompt [on|off]    - Bật hoặc tắt xác nhận khi dùng mget/mput nhiều file.

        Điều hướng thư mục:
        pwd                - In ra thư mục hiện tại trên server.
        cd <dir>           - Chuyển sang thư mục <dir>.
        ls                 - Liệt kê danh sách file và thư mục hiện tại.
        mkdir <name>       - Tạo thư mục mới trên server.
        rmdir <name>       - Xoá thư mục (và mọi thứ bên trong, nếu có). [bí danh: rmd]

        Xử lý file:
        get <file>         - Tải 1 file từ server về máy cục bộ.
        put <file>         - Tải 1 file từ máy lên server (sẽ được quét virus).
        mget <pattern>     - Tải nhiều file (ví dụ: *.txt hoặc a*) với xác nhận.
        mput <pattern>     - Upload nhiều file với xác nhận và quét virus.
        delete <file>      - Xoá file khỏi server.
        rename <old> <new> - Đổi tên file hoặc thư mục.

        Khác:
        quit               - Thoát chương trình FTP.
        help, ?            - Hiển thị bảng trợ giúp này.

        =============================================================
        Gợi ý:
        - Bạn có thể dùng các ký tự đại diện như *.txt để xử lý nhiều file.
        - Hãy dùng 'prompt off' nếu bạn không muốn bị hỏi mỗi lần với mget/mput.
        - Luôn kiểm tra trạng thái bằng lệnh 'status' trước khi tải hay upload.
        """)

   
    def delete_file(self, filename):
        # Kiểm tra xem file có tồn tại bằng LIST
        self._send_cmd("EPSV")
        resp = self._get_response()
        m = re.search(r"\(\|\|\|(\d+)\|\)", resp)
        if not m:
            print(f"⚠️ Không thể phân tích EPSV: {resp}")
            return
        port = int(m.group(1))

        data_raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_raw.connect((FTP_HOST, port))
        data_sock = self.context.wrap_socket(
            data_raw,
            server_hostname=FTP_HOST,
            session=self.ctrl.session,
            do_handshake_on_connect=True
        )

        self._send_cmd("LIST")
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Lỗi mở kênh dữ liệu: {resp}")
            data_sock.close()
            return

        data = b""
        while True:
            chunk = data_sock.recv(4096)
            if not chunk:
                break
            data += chunk
        data_sock.close()
        self._get_response()

        # Kiểm tra xem file có tồn tại và là file thường không
        found = False
        for line in data.decode(errors="replace").splitlines():
            parts = line.split()
            if len(parts) < 9:
                continue
            name = " ".join(parts[8:])
            if name == filename:
                if line.startswith("d"):
                    print(f"❌ '{filename}' là thư mục. Hãy dùng lệnh rmdir để xóa.")
                    return
                found = True
                break

        if not found:
            print(f"❌ File '{filename}' không tồn tại trong thư mục hiện tại.")
            return

        # Thực hiện lệnh xóa
        self._send_cmd(f"DELE {filename}")
        resp = self._get_response()
        if resp.startswith("250"):
            print(f"✅ Đã xóa file: {filename}")
        else:
            print(f"❌ Không thể xóa file '{filename}': {resp}")

    def rmd(self, folder):
        print(f"📁 Đang xóa thư mục (đệ quy): {folder}")

        # Gửi CWD và kiểm tra phản hồi
        self._send_cmd(f"CWD {folder}")
        resp = self._get_response()
        if not resp.startswith("250"):
            print(f"❌ Không thể vào thư mục '{folder}': {resp}")
            return

        # Lấy danh sách nội dung thư mục
        self._send_cmd("EPSV")
        resp = self._get_response()
        m = re.search(r"\(\|\|\|(\d+)\|\)", resp)
        if not m:
            print(f"⚠️ Không thể phân tích EPSV khi xóa {folder}: {resp}")
            self._send_cmd("CWD ..")  # Quay lại nếu cần
            self._get_response()
            return
        port = int(m.group(1))

        try:
            data_raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_raw.settimeout(10)
            data_raw.connect((FTP_HOST, port))
            data_sock = self.context.wrap_socket(
                data_raw,
                server_hostname=FTP_HOST,
                session=self.ctrl.session,
                do_handshake_on_connect=True
            )

            self._send_cmd("LIST")
            resp = self._get_response()
            if not resp.startswith("150"):
                print(f"❌ Lỗi mở kênh dữ liệu: {resp}")
                data_sock.close()
                self._send_cmd("CWD ..")
                self._get_response()
                return

            data = b""
            while True:
                chunk = data_sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            data_sock.close()
            self._get_response()
        except Exception as e:
            print(f"⚠️ Lỗi khi lấy danh sách thư mục: {e}")
            self._send_cmd("CWD ..")
            self._get_response()
            return

        # Xử lý từng mục trong thư mục
        for line in data.decode(errors="replace").splitlines():
            parts = line.split()
            if len(parts) < 9:
                continue
            name = " ".join(parts[8:])
            if line.startswith("d"):
                self.rmd(name)
            else:
                self._send_cmd(f"DELE {name}")
                self._get_response()
                print(f"🗑️ Đã xóa file: {name}")

        # Quay lại thư mục cha và xóa thư mục hiện tại
        self._send_cmd("CWD ..")
        self._get_response()

        self._send_cmd(f"RMD {folder}")
        resp = self._get_response()
        if resp.startswith("250"):
            print(f"✅ Đã xóa thư mục: {folder}")
        else:
            print(f"❌ Không thể xóa thư mục: {folder}: {resp}")

    def download_ftp(self, remote_filename, local_filename=None):
        """
        Tải file từ FTP server xuống máy cục bộ
        :param remote_filename: Tên file trên server (có thể là đường dẫn tương đối/ tuyệt đối)
        :param local_filename: Tên file lưu trữ cục bộ (mặc định giống remote_filename)
        """
        if not self.ctrl:
            print("❌ Chưa kết nối tới server. Hãy dùng lệnh 'open' trước.")
            return

        # Xác định tên file cục bộ
        local_filename = local_filename or os.path.basename(remote_filename)

        # Thiết lập kết nối dữ liệu qua EPSV
        self._send_cmd("EPSV")
        resp = self._get_response()
        match = re.search(r"\(\|\|\|(\d+)\|\)", resp)
        if not match:
            print(f"❌ Không phân tích được cổng từ EPSV: {resp}")
            return
        data_port = int(match.group(1))

        # Gửi lệnh tải file
        self._send_cmd(f"RETR {remote_filename}")
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Server từ chối tải file: {resp}")
            return

        # Thiết lập kênh dữ liệu SSL với session reuse
        try:
            # Tạo socket dữ liệu thô
            data_sock_raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock_raw.connect((FTP_HOST, data_port))
            
            # Bọc socket bằng SSL context, tái sử dụng session
            data_sock = self.context.wrap_socket(
                data_sock_raw,
                server_hostname=FTP_HOST,
                session=self.ctrl.session  # Quan trọng: tái sử dụng session TLS
            )
            
            # Nhận dữ liệu và ghi vào file
            start_time = time.time()
            total_bytes = 0
            
            with open(local_filename, 'wb') as f:
                while True:
                    chunk = data_sock.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_bytes += len(chunk)
            
            # Đóng kết nối dữ liệu
            data_sock.close()
            
            # Xác nhận hoàn thành từ server
            transfer_time = time.time() - start_time
            self._get_response()  # Nhận phản hồi 226 Transfer complete
            
            print(f"✅ Tải thành công: {remote_filename} → {local_filename}")
            print(f"📊 Kích thước: {total_bytes} bytes | "
                f"Thời gian: {transfer_time:.2f}s | "
                f"Tốc độ: {total_bytes/transfer_time/1024:.2f} KB/s")

        except Exception as e:
            print(f"❌ Lỗi trong quá trình tải file: {str(e)}")
            # Xóa file cục bộ nếu tải thất bại
            if os.path.exists(local_filename):
                os.remove(local_filename)
    def prompt(self, *args):
        if not args:
            # Đảo trạng thái nếu không có tham số
            self.prompt_confirm = not self.prompt_confirm
        else:
            # Xử lý tham số
            arg = args[0].lower()
            if arg == 'on':
                self.prompt_confirm = True
            elif arg == 'off':
                self.prompt_confirm = False
            else:
                print("❌ Lệnh không hợp lệ. Dùng 'prompt on' hoặc 'prompt off'")
                return
        
        status = "BẬT" if self.prompt_confirm else "TẮT"
        print(f"✅ Đã {status} chế độ xác nhận khi dùng lệnh mget")
    def mget(self, pattern):
        """
        Tải nhiều file từ server dựa trên pattern (ví dụ: *.txt, a*)
        Xác nhận từng file nếu prompt_confirm=True
        """
        if not self.ctrl:
            print("❌ Chưa kết nối tới server. Hãy dùng lệnh 'open' trước.")
            return

        # Bước 1: Lấy danh sách file từ server
        files = self._get_file_list()
        if files is None:
            return

        # Bước 2: Lọc file theo pattern
        matched_files = fnmatch.filter(files, pattern)
        if not matched_files:
            print(f"🔍 Không tìm thấy file nào khớp với pattern: {pattern}")
            return

        print(f"🔍 Tìm thấy {len(matched_files)} file khớp pattern:")
        for i, filename in enumerate(matched_files, 1):
            print(f"  {i}. {filename}")

        # Bước 3: Tải từng file với xác nhận riêng
        success_count = 0
        for filename in matched_files:
            try:
                if self.prompt_confirm:
                    confirm = input(f"Bạn có muốn tải file '{filename}'? (y/n/a): ")
                    if confirm.lower() == 'n':
                        print(f"⏩ Đã bỏ qua file: {filename}")
                        continue
                    if confirm.lower() == 'a':  # Chọn 'a' để tải tất cả không hỏi lại
                        self.prompt_confirm = False
                        
                print(f"⬇️  Đang tải: {filename}")
                self.download_ftp(filename)
                success_count += 1
            except Exception as e:
                print(f"❌ Lỗi khi tải {filename}: {str(e)}")
        
        print(f"✅ Đã tải thành công {success_count}/{len(matched_files)} file")

    def _get_file_list(self):
            """Hàm nội bộ để lấy danh sách file từ server"""
            # Thiết lập kênh dữ liệu qua EPSV
            self._send_cmd("EPSV")
            resp = self._get_response()
            m = re.search(r"\(\|\|\|(\d+)\|\)", resp)
            if not m:
                print(f"⚠️ Không thể phân tích EPSV: {resp}")
                return None
            port = int(m.group(1))

            data_raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_raw.connect((FTP_HOST, port))
            data_sock = self.context.wrap_socket(
                data_raw,
                server_hostname=FTP_HOST,
                session=self.ctrl.session,
                do_handshake_on_connect=True
            )

            # Yêu cầu danh sách file
            self._send_cmd("LIST")
            resp = self._get_response()
            if not resp.startswith('150'):
                print(f"❌ Lỗi mở kênh dữ liệu: {resp}")
                data_sock.close()
                return None

            # Đọc dữ liệu danh sách
            data = b""
            while True:
                chunk = data_sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            data_sock.close()
            self._get_response()

            # Phân tích danh sách file
            file_list = []
            for line in data.decode('utf-8', errors='replace').splitlines():
                parts = line.split()
                if len(parts) < 9:
                    continue
                filename = " ".join(parts[8:])
                # Bỏ qua thư mục (bắt đầu bằng 'd')
                if not line.startswith('d'):
                    file_list.append(filename)
            
            return file_list
    def scan_with_clamav(self, file_path):
            """Kết nối tới ClamAV Agent local"""
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(('127.0.0.1', 9001))
                    
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
                print(f"Lỗi quét virus: {str(e)}")
                return False
    def upload_ftp(self, local_filename, remote_filename=None):
        """
        Upload file lên server (BẮT BUỘC quét virus trước)
        Giữ nguyên toàn bộ chức năng upload cũ + tích hợp quét virus
        """
        # --- PHẦN KIỂM TRA VIRUS MỚI THÊM ---
        print(f"🔍 Đang quét virus cho file: {local_filename}")
        if not self.scan_with_clamav(local_filename):
            print("🔴 KHÔNG thể upload do file chứa virus hoặc lỗi quét!")
            return False
        print("🟢 File an toàn, bắt đầu upload...")
        
        # --- GIỮ NGUYÊN PHẦN UPLOAD FTP CŨ ---
        if not self.ctrl:
            print("❌ Chưa kết nối tới server. Hãy dùng lệnh 'open' trước.")
            return False

        if not os.path.exists(local_filename):
            print(f"❌ File cục bộ không tồn tại: {local_filename}")
            return False
            
        remote_filename = remote_filename or os.path.basename(local_filename)

        self._send_cmd("EPSV")
        resp = self._get_response()
        match = re.search(r"\(\|\|\|(\d+)\|\)", resp)
        if not match:
            print(f"❌ Không phân tích được cổng từ EPSV: {resp}")
            return False
        data_port = int(match.group(1))

        self._send_cmd(f"STOR {remote_filename}")
        resp = self._get_response()
        if not resp.startswith('150'):
            print(f"❌ Server từ chối upload file: {resp}")
            return False

        try:
            data_sock_raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock_raw.connect((FTP_HOST, data_port))
            data_sock = self.context.wrap_socket(
                data_sock_raw,
                server_hostname=FTP_HOST,
                session=self.ctrl.session
            )
            
            start_time = time.time()
            total_bytes = 0
            
            with open(local_filename, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    data_sock.sendall(chunk)
                    total_bytes += len(chunk)
            
            data_sock.close()
            transfer_time = time.time() - start_time
            self._get_response()
            
            print(f"✅ Upload thành công: {local_filename} → {remote_filename}")
            print(f"📊 Kích thước: {total_bytes} bytes | "
                f"Thời gian: {transfer_time:.2f}s | "
                f"Tốc độ: {total_bytes/transfer_time/1024:.2f} KB/s")
            return True

        except Exception as e:
            print(f"❌ Lỗi upload: {str(e)}")
            self._send_cmd(f"DELE {remote_filename}")
            self._get_response()
            return False
    def mput(self, pattern):
        """
        Upload nhiều file từ máy cục bộ lên server dựa trên pattern (ví dụ: *.txt, a*)
        - Tự động quét virus cho từng file
        - Xác nhận từng file nếu prompt_confirm=True
        """
        if not self.ctrl:
            print("❌ Chưa kết nối tới server. Hãy dùng lệnh 'open' trước.")
            return

        # Bước 1: Tìm file cục bộ khớp pattern
        import glob
        matched_files = glob.glob(pattern)
        matched_files = [f for f in matched_files if os.path.isfile(f)]  # Chỉ lấy file, bỏ thư mục
        
        if not matched_files:
            print(f"🔍 Không tìm thấy file cục bộ nào khớp pattern: {pattern}")
            return

        print(f"🔍 Tìm thấy {len(matched_files)} file khớp pattern:")
        for i, filename in enumerate(matched_files, 1):
            print(f"  {i}. {filename}")

        # Bước 2: Upload từng file với xác nhận
        success_count = 0
        for local_file in matched_files:
            try:
                # Xác nhận với người dùng nếu cần
                if self.prompt_confirm:
                    confirm = input(f"Bạn có muốn upload file '{local_file}'? (y/n/a): ")
                    if confirm.lower() == 'n':
                        print(f"⏩ Đã bỏ qua file: {local_file}")
                        continue
                    if confirm.lower() == 'a':  # Tắt xác nhận cho các file sau
                        self.prompt_confirm = False
                
                # Thực hiện upload (sử dụng hàm upload_ftp hiện có)
                if self.upload_ftp(local_file):
                    success_count += 1
                    
            except Exception as e:
                print(f"❌ Lỗi khi upload {local_file}: {str(e)}")
        
        print(f"✅ Đã upload thành công {success_count}/{len(matched_files)} file")
