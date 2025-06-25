### === ftp_client.py ===
import socket
import os

FTP_SERVER_HOST = '127.0.0.1'
FTP_SERVER_PORT = 2121
CLAMAV_AGENT_HOST = '127.0.0.1'
CLAMAV_AGENT_PORT = 3310
BUFFER_SIZE = 4096

def scan_file_with_clamav(file_path):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clamav_sock:
            clamav_sock.connect((CLAMAV_AGENT_HOST, CLAMAV_AGENT_PORT))
            with open(file_path, 'rb') as f:
                while chunk := f.read(BUFFER_SIZE):
                    clamav_sock.sendall(chunk)
            clamav_sock.shutdown(socket.SHUT_WR)
            return clamav_sock.recv(BUFFER_SIZE).decode().strip()
    except Exception as e:
        print(f"ClamAV scan error: {e}")
        return "ERROR"

def put(sock, filename):
    if not os.path.isfile(filename):
        print(f"File not found: {filename}")
        return

    print(f"Scanning {filename}...")
    result = scan_file_with_clamav(filename)
    if result != "OK":
        print(f"File rejected: {result}")
        return

    sock.sendall(f"put {os.path.basename(filename)}".encode())
    with open(filename, 'rb') as f:
        while chunk := f.read(BUFFER_SIZE):
            sock.sendall(chunk)
    sock.sendall(b"EOF")
    print(sock.recv(BUFFER_SIZE).decode())

def get(sock, filename):
    sock.sendall(f"get {filename}".encode())
    with open(filename, 'wb') as f:
        while True:
            data = sock.recv(BUFFER_SIZE)
            if data == b"EOF":
                break
            f.write(data)
    print(f"Downloaded {filename}")

def ls(sock):
    sock.sendall(b"ls")
    print(sock.recv(BUFFER_SIZE).decode())

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ftp_sock:
        ftp_sock.connect((FTP_SERVER_HOST, FTP_SERVER_PORT))
        print("Connected to FTP server.")
        while True:
            cmd = input("ftp> ").strip().split()
            if not cmd:
                continue
            if cmd[0] == 'put' and len(cmd) == 2:
                put(ftp_sock, cmd[1])
            elif cmd[0] == 'get' and len(cmd) == 2:
                get(ftp_sock, cmd[1])
            elif cmd[0] == 'ls':
                ls(ftp_sock)
            elif cmd[0] in ('quit', 'exit'):
                ftp_sock.sendall(b"quit")
                break
            else:
                print("Unknown command.")

if __name__ == "__main__":
    main()
