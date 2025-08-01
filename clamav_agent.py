#clamav_agent.py
import socket
import subprocess
import os

HOST = '0.0.0.0'
PORT = 9001
BUFFER_SIZE = 4096
SCAN_DIR = 'clamav_temp'

# Đường dẫn đến clamdscan và daemon clamd ->NHỚ SỬA LẠI
"C:\ClamAV\clamav-1.4.3.win.x64\clamdscan.exe"
CLAMDSCAN_PATH = r"C:\ClamAV\clamav-1.4.3.win.x64\clamdscan.exe"
CLAMD_PATH = r"C:\ClamAV\clamav-1.4.3.win.x64\clamd.exe"
CLAMD_CONF = r"C:\ClamAV\clamav-1.4.3.win.x64\clamd.conf"

# ==============================
# Tự khởi động clamd ngầm nền
# ==============================
def start_clamd_background():
    try:
        subprocess.Popen(
            [CLAMD_PATH, f"--config-file={CLAMD_CONF}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print("[AGENT] ✅ Đã khởi động clamd daemon ngầm.")
    except Exception as e:
        print(f"[AGENT] ❌ Không thể khởi động clamd: {e}")

# ==============================
# Tạo thư mục nếu chưa có
# ==============================
if not os.path.exists(SCAN_DIR):
    os.makedirs(SCAN_DIR)

print("[AGENT] ClamAVAgent using clamdscan...")

# ==============================
# Nhận tên file
# ==============================
def recv_filename(conn):
    filename = b""
    while True:
        ch = conn.recv(1)
        if not ch or ch == b"\n":
            break
        filename += ch
    return filename.decode().strip()

# ==============================
# Xử lý client gửi file đến
# ==============================
def handle_client(conn):
    try:
        filename = recv_filename(conn)
        filepath = os.path.join(SCAN_DIR, filename)

        with open(filepath, 'wb') as f:
            buffer = b""
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                buffer += data
                if b"===SCAN_DONE===" in buffer:
                    f.write(buffer.split(b"===SCAN_DONE===")[0])
                    break

        print(f"[AGENT] 📥 Đã nhận file: {filename}")

        # Gọi clamdscan để quét
        result = subprocess.run([CLAMDSCAN_PATH, filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        print(f"[AGENT] 🔍 Kết quả quét:\n{output}")

        if 'Infected files: 0' in output:
            conn.sendall(b'OK')
        else:
            conn.sendall(b'INFECTED')

        os.remove(filepath)

    except Exception as e:
        print(f"[AGENT] ❌ Lỗi xử lý file: {e}")
        try:
            conn.sendall(b'ERROR')
        except:
            pass
    finally:
        conn.close()

# ==============================
# Khởi động server agent
# ==============================
def start_agent():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[AGENT] 🚀 Đang lắng nghe tại {HOST}:{PORT}...")

        while True:
            conn, addr = server.accept()
            print(f"[AGENT] 🔌 Kết nối từ {addr}")
            handle_client(conn)

# ==============================
# MAIN
# ==============================
if __name__ == '__main__':
    start_clamd_background()
    start_agent()