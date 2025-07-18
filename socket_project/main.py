from client.ftp_client import FTPSession
import shlex
def main():
    print("=== 📡 FTP CLIENT (socket thuần + TLS) ===")
    ftp = FTPSession()
    connected = False

    while True:
        try:
            line = input("ftp> ").strip()
            if not line:
                continue

            parts = line.split()
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
                if connected:
                    ftp.status()
                else:
                    print("⚠️ Vui lòng kết nối trước (dùng 'open').")
            elif cmd == "passive":
                if connected:
                    ftp.passive()
                else:
                    print("⚠️ Vui lòng kết nối trước (dùng 'open').")
            elif cmd in ("help", "?"):
                ftp.help()
            elif not connected:
                print("⚠️ Vui lòng dùng lệnh 'open' để kết nối trước.")
            elif cmd in ("ls", "dir"):
                ftp.list()
            elif cmd == "pwd":
                ftp.pwd()
            elif cmd =="prompt":
                ftp.prompt()
            elif cmd == "cd" and args:
                path = ' '.join(args)  # Ghép lại các phần bị tách bởi dấu cách
                ftp.cwd(path)
            elif cmd == "mkdir" and args:
                path= ' '.join(args)
                ftp.mkd(path)
            elif cmd == "rmdir" and args:
                path= ' '.join(args)
                ftp.rmd(path)
            elif line.startswith("rename ") or line.startswith("rn "):
                try:
                    parts = shlex.split(line)
                except ValueError as e:
                    print(f"❌ Lỗi cú pháp rename: {e}")
                    continue

                cmd = parts[0].lower()
                args = parts[1:]

                if len(args) != 2:
                    print("❌ Cú pháp đúng: rename \"tên cũ\" \"tên mới\"")
                else:
                    ftp.rn(args[0], args[1])
                continue  # quan trọng: bỏ qua xử lý lệnh thông thường bên dưới
            elif cmd == "delete" and args:
                path = ' '.join(args)
                ftp.delete_file(path)
            elif cmd == "get" and args:
                path = ' '.join(args)
                ftp.download_ftp(path)
            elif cmd == "put" and args:
                path = ' '.join(args)
                ftp.upload_ftp(path)
            elif cmd == "mget" and len(args) == 1:
                ftp.mget(args[0])
            elif cmd == "mput" and len(args) == 1:
                ftp.mput(args[0])
            else:
                print("⚠️ Lệnh không hợp lệ. Dùng 'help' để xem danh sách lệnh.")
        except Exception as e:
            print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()

