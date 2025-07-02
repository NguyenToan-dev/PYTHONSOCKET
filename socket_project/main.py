from client.ftp_client import (
    list_files,
    change_directory,
    make_directory,
    remove_directory_recursive,
    delete_file,
    rename_file,
    print_working_directory,
    download_file,
    upload_file,
    mget_files,
    mput_files,
    toggle_prompt,
)

def main():
    print("=== Chào mừng đến với FTP Client ===")
    while True:
        cmd = input("ftp> ").strip()
        if not cmd:
            continue

        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:]

        try:
            if command == "ls":
                list_files()
            elif command == "pwd":
                print_working_directory()
            elif command == "cd":
                if len(args) != 1:
                    print("⚠️ Dùng: cd <thư mục>")
                    continue
                change_directory(args[0])
                print(f"✅ Đã chuyển vào thư mục '{args[0]}'")
            elif command == "mkdir":
                if len(args) != 1:
                    print("⚠️ Dùng: mkdir <tên thư mục>")
                    continue
                make_directory(args[0])
            elif command == "rmdir":
                if len(args) != 1:
                    print("⚠️ Dùng: rmdir <tên thư mục>")
                    continue
                remove_directory_recursive(args[0])
            elif command == "delete":
                if len(args) != 1:
                    print("⚠️ Dùng: delete <tên file>")
                    continue
                delete_file(args[0])
            elif command == "rename":
                if len(args) != 2:
                    print("⚠️ Dùng: rename <tên cũ> <tên mới>")
                    continue
                rename_file(args[0], args[1])
            elif command in ("get", "recv"):
                if len(args) != 1:
                    print("⚠️ Dùng: get <tên file>")
                    continue
                download_file(args[0])
            elif command == "put":
                if len(args) != 1:
                    print("⚠️ Dùng: put <đường dẫn file local>")
                    continue
                upload_file(args[0])
            elif command == "mget":
                if len(args) != 1:
                    print("⚠️ Dùng: mget <mẫu>")
                    continue
                mget_files(args[0])
            elif command == "mput":
                if len(args) != 1:
                    print("⚠️ Dùng: mput <mẫu>")
                    continue
                mput_files(args[0])
            elif command == "prompt":
                toggle_prompt()
            elif command in ("quit", "exit", "bye"):
                print("👋 Tạm biệt!")
                break
            else:
                print("⚠️ Lệnh không hợp lệ. Dùng ls, cd <thư mục>, pwd, mkdir <tên>, rmdir <tên>, delete <file>, rename <cũ> <mới>, get <file>, put <file>, mget <pattern>, mput <pattern>, prompt, quit")
        except Exception as e:
            print(f"❌ Lỗi khi thực hiện lệnh: {e}")

if __name__ == "__main__":
    main()
