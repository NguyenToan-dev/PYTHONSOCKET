from client.ftp_client import FTPSession
import shlex
import os

if __name__ == "__main__":
    print("=== 📡 FTP CLIENT (Plain FTP + ClamAV) ===")
    ftp = FTPSession()
    while True:
        command = input("ftp> ").strip()
        if not command:
            continue
        
        # Tách lệnh và đối số
        parts = shlex.split(command)
        if not parts:
            continue
        cmd = parts[0].lower()
        args = parts[1:]  # Lấy tất cả các đối số sau lệnh

        if cmd == "open":
            ftp.connect_ftp()
        elif cmd == "close":
            ftp.close()
        elif cmd == "ls":
            ftp.list(' '.join(args) if args else "")
        elif cmd == "cd":
            if args:
                ftp.cwd(' '.join(args))
            else:
                print("❌ Cần đường dẫn cho cd")
        elif cmd == "lcd":
            if args:
                try:
                    os.chdir(' '.join(args))
                    print(f"📂 Đã thay đổi thư mục cục bộ: {os.getcwd()}")
                except Exception as e:
                    print(f"❌ Lỗi lcd: {str(e)}")
            else:
                print("❌ Cần đường dẫn cho lcd")
        elif cmd == "pwd":
            ftp.pwd()
        elif cmd == "mkdir":
            if args:
                ftp.mkdir(' '.join(args))
            else:
                print("❌ Cần tên thư mục cho mkdir")
        elif cmd == "rmdir":
            if args:
                ftp.rmdir(' '.join(args))
            else:
                print("❌ Cần tên thư mục cho rmdir")
        elif cmd == "delete":
            if args:
                ftp.delete(' '.join(args))
            else:
                print("❌ Cần tên file cho delete")
        elif cmd == "rename":
            if len(args) == 2:
                ftp.rename(args[0], args[1])
            else:
                print("❌ Cần tên cũ và tên mới cho rename (ví dụ: rename \"abc xyz\" \"xyz abc\")")
        elif cmd == "get":
            if args:
                ftp.download_ftp(' '.join(args))
            else:
                print("❌ Cần tên file cho get")
        elif cmd == "put":
            if args:
                ftp.upload_ftp(' '.join(args))
            else:
                print("❌ Cần tên file cho put")
        elif cmd == "mget":
            if args:
                ftp.mget(' '.join(args))
            else:
                print("❌ Cần mẫu file cho mget")
        elif cmd == "mput":
            if args:
                ftp.mput(' '.join(args))
            else:
                print("❌ Cần mẫu file cho mput")
        elif cmd == "ascii":
            ftp.set_transfer_mode("ascii")
        elif cmd == "binary":
            ftp.set_transfer_mode("binary")
        elif cmd == "passive":
            if args:
                ftp.passive(' '.join(args))
            else:
                ftp.passive()
        elif cmd == "prompt":
            if args:
                ftp.prompt(' '.join(args))
            else:
                ftp.prompt()
        elif cmd == "status":
            ftp.status()
        elif cmd in ["help", "?"]:
            ftp.help()
        elif cmd in ["quit", "bye"]:
            ftp.quit()
        else:
            print(f"❌ Lệnh không hợp lệ: {cmd}")