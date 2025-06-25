import socket
import tempfile
import subprocess
import os

AGENT_HOST = '127.0.0.1'
AGENT_PORT = 3310
BUFFER_SIZE = 4096

def scan_with_clamav(file_path):
    try:
        result = subprocess.run(['clamscan', file_path], capture_output=True, text=True, timeout=10)
        print("ClamAV Output:\n", result.stdout)  # Debug
        if ": OK" in result.stdout:
            return "OK"
        elif ": Infected" in result.stdout or "FOUND" in result.stdout:
            return "INFECTED"
        else:
            return "UNKNOWN"
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout"
    except Exception as e:
        print(f"Error scanning: {e}")
        return "ERROR"

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((AGENT_HOST, AGENT_PORT))
        server_sock.listen(5)
        print(f"ClamAV Agent listening on {AGENT_HOST}:{AGENT_PORT}")

        while True:
            client_sock, addr = server_sock.accept()
            with client_sock:
                print(f"Scanning file from {addr}")
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    while True:
                        chunk = client_sock.recv(BUFFER_SIZE)
                        if not chunk:
                            break
                        tmp.write(chunk)
                    tmp.flush()
                    file_path = tmp.name

                print(f"Saved to {file_path}")
                result = scan_with_clamav(file_path)
                print(f"Scan result: {result}")
                client_sock.sendall(result.encode())
                os.remove(file_path)

if __name__ == "__main__":
    main()
