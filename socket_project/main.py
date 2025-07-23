from ftp_client import FTPSession
import shlex
import os

def main():
    print("=== 📡 FTP CLIENT (Plain FTP + ClamAV) ===")
    ftp = FTPSession()
    connected = False

    while True:
        try:
            line = input("ftp> ").strip()
            if not line:
                continue

            # Sử dụng shlex.split để xử lý đường dẫn có khoảng trắng
            try:
                parts = shlex.split(line)
            except ValueError as e:
                print(f"❌ Lỗi cú pháp: {e}")
                continue

            if not parts:
                continue

            cmd = parts[0].lower()
            args = parts[1:]

            if cmd == "open":
                ftp.connect_ftp()
                connected = True
            elif cmd == "close":
                if connected:
                    ftp.close()
                    connected = False
                else:
                    print("⚠️ Bạn chưa kết nối.")
            elif cmd in ("quit", "exit", "bye"):
                if connected:
                    ftp.close()
                print("👋 Đã thoát FTP client.")
                break
            elif cmd == "status":
                ftp.status()
            elif cmd == "passive":
                if args:
                    ftp.passive(args[0])
                else:
                    ftp.passive()
            elif cmd in ("help", "?"):
                ftp.help()
            elif not connected:
                print("⚠️ Vui lòng dùng lệnh 'open' để kết nối trước.")
            elif cmd in ("ls", "dir"):
                if args:
                    ftp.list(' '.join(args))
                else:
                    ftp.list()
            elif cmd == "pwd":
                ftp.pwd()
            elif cmd == "prompt":
                if args:
                    ftp.prompt(args[0])
                else:
                    ftp.prompt()
            elif cmd == "cd" and args:
                path = ' '.join(args)
                ftp.cwd(path)
            elif cmd == "lcd" and args:
                path = ' '.join(args)
                ftp.lcd(path)
            elif cmd == "mkdir" and args:
                path = ' '.join(args)
                ftp.mkdir(path)
            elif cmd == "rmdir" and args:
                path = ' '.join(args)
                ftp.rmdir(path)
            elif cmd == "delete" and args:
                path = ' '.join(args)
                ftp.delete(path)
            elif cmd == "rename" and len(args) == 2:
                ftp.rename(args[0], args[1])
            elif cmd == "get" and args:
                remote_file = args[0]
                local_file = args[1] if len(args) > 1 else None
                ftp.download_ftp(remote_file, local_file)
            elif cmd == "put" and args:
                local_file = args[0]
                remote_file = args[1] if len(args) > 1 else None
                ftp.upload_ftp(local_file, remote_file)
            elif cmd == "mget" and args:
                pattern = ' '.join(args)
                ftp.mget(pattern)
            elif cmd == "mput" and args:
                pattern = ' '.join(args)
                ftp.mput(pattern)
            elif cmd == "ascii":
                ftp.set_transfer_mode("ascii")
            elif cmd == "binary":
                ftp.set_transfer_mode("binary")
            else:
                print("⚠️ Lệnh không hợp lệ. Dùng 'help' để xem danh sách lệnh.")
        except Exception as e:
            print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()
