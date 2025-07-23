from ftp_client import FTPSession
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
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "open":
            ftp.connect_ftp()
        elif cmd == "close":
            ftp.close()
        elif cmd == "ls":
            ftp.list(args)
        elif cmd == "cd":
            if args:
                ftp.cwd(args)
            else:
                print("❌ Cần đường dẫn cho cd")
        elif cmd == "lcd":
            if args:
                ftp.lcd(args)
            else:
                print("❌ Cần đường dẫn cho lcd")
        elif cmd == "pwd":
            ftp.pwd()
        elif cmd == "mkdir":
            if args:
                ftp.mkdir(args)
            else:
                print("❌ Cần tên thư mục cho mkdir")
        elif cmd == "rmdir":
            if args:
                ftp.rmdir(args)
            else:
                print("❌ Cần tên thư mục cho rmdir")
        elif cmd == "delete":
            if args:
                ftp.delete(args)
            else:
                print("❌ Cần tên file cho delete")
        elif cmd == "rename":
            if args:
                rename_args = args.split(maxsplit=1)
                if len(rename_args) == 2:
                    ftp.rename(rename_args[0], rename_args[1])
                else:
                    print("❌ Cần tên cũ và tên mới cho rename")
            else:
                print("❌ Cần tên cũ và tên mới cho rename")
        elif cmd == "get":
            if args:
                ftp.download_ftp(args)
            else:
                print("❌ Cần tên file cho get")
        elif cmd == "put":
            if args:
                ftp.upload_ftp(args)
            else:
                print("❌ Cần tên file cho put")
        elif cmd == "mget":
            if args:
                ftp.mget(args)
            else:
                print("❌ Cần mẫu file cho mget")
        elif cmd == "mput":
            if args:
                ftp.mput(args)
            else:
                print("❌ Cần mẫu file cho mput")
        elif cmd == "ascii":
            ftp.set_transfer_mode("ascii")
        elif cmd == "binary":
            ftp.set_transfer_mode("binary")
        elif cmd == "passive":
            if args:
                ftp.passive(args)
            else:
                ftp.passive()
        elif cmd == "prompt":
            if args:
                ftp.prompt(args)
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
