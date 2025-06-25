### === ftp_server.py ===
import socket
import threading
import os

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 2121
BUFFER_SIZE = 4096
STORAGE_DIR = 'server_files'

os.makedirs(STORAGE_DIR, exist_ok=True)

def handle_client(sock, addr):
    print(f"Client connected: {addr}")
    try:
        while True:
            data = sock.recv(BUFFER_SIZE).decode().strip()
            if not data:
                break

            parts = data.split()
            cmd = parts[0].lower()

            if cmd == 'ls':
                files = os.listdir(STORAGE_DIR)
                sock.sendall("\n".join(files).encode() if files else b"(empty)")

            elif cmd == 'put' and len(parts) == 2:
                filename = parts[1]
                filepath = os.path.join(STORAGE_DIR, filename)
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = sock.recv(BUFFER_SIZE)
                        if chunk == b"EOF":
                            break
                        f.write(chunk)
                sock.sendall(f"Upload of {filename} complete.".encode())

            elif cmd == 'get' and len(parts) == 2:
                filename = parts[1]
                filepath = os.path.join(STORAGE_DIR, filename)
                if not os.path.exists(filepath):
                    sock.sendall(f"File not found: {filename}".encode())
                else:
                    with open(filepath, 'rb') as f:
                        while chunk := f.read(BUFFER_SIZE):
                            sock.sendall(chunk)
                    sock.sendall(b"EOF")

            elif cmd == 'quit':
                break
            else:
                sock.sendall(b"Invalid command.")
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        sock.close()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind((SERVER_HOST, SERVER_PORT))
        server_sock.listen(5)
        print(f"FTP Server listening on {SERVER_HOST}:{SERVER_PORT}")

        while True:
            client_sock, addr = server_sock.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == "__main__":
    main()
