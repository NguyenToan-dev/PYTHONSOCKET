#clam_agent.py
import socket
import subprocess
import os

HOST = '0.0.0.0'
PORT = 9001
BUFFER_SIZE = 4096
SCAN_DIR = 'clamav_temp'
CLAMDSCAN_PATH = r"C:\Users\tn421\Downloads\clamav-1.4.3.win.x64\clamav-1.4.3.win.x64\clamdscan.exe"

if not os.path.exists(SCAN_DIR):
    os.makedirs(SCAN_DIR)

print("[AGENT] ClamAVAgent using clamdscan...")

def recv_filename(conn):
    filename = b""
    while True:
        ch = conn.recv(1)
        if not ch or ch == b"\n":
            break
        filename += ch
    return filename.decode().strip()

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

        print(f"[AGENT] File received: {filename}")

        # Scan using clamdscan
        result = subprocess.run([CLAMDSCAN_PATH, filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        print(f"[AGENT] Scan output:\n{output}")

        if 'Infected files: 0' in output:
            conn.sendall(b'OK')
        else:
            conn.sendall(b'INFECTED')

        os.remove(filepath)

    except Exception as e:
        print(f"[ERROR] {e}")
        try:
            conn.sendall(b'ERROR')
        except:
            pass
    finally:
        conn.close()

def start_agent():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[AGENT] ClamAVAgent listening on {HOST}:{PORT}...")

        while True:
            conn, addr = server.accept()
            print(f"[AGENT] Connection from {addr}")
            handle_client(conn)

if __name__ == '__main__':
    start_agent()
