import subprocess
import shlex
import os
from client.config import FTP_HOST, FTP_PORT, FTP_USER, FTP_PASS
import fnmatch
import time
current_dir = ""  # Thư mục hiện tại trên server
prompt_confirm = True  # Xác nhận khi dùng mget/mput

FTPS_OPTIONS = "-k --ssl-reqd --ftp-pasv"  # Mã hóa dữ liệu, Passive Mode

def build_url():
    if current_dir:
        return f'ftp://{FTP_HOST}:{FTP_PORT}/{current_dir}/'
    return f'ftp://{FTP_HOST}:{FTP_PORT}/'

def list_files():
    url = build_url()
    cmd = f'curl {FTPS_OPTIONS} --user "{FTP_USER}:{FTP_PASS}" "{url}"'
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, encoding="utf-8")
    if proc.returncode:
        print("❌ Lỗi khi liệt kê file:", proc.stderr.strip().splitlines()[-1])
    else:
        print(f"=== DANH SÁCH FILE TRONG '{current_dir or '/'}' ===")
        print(proc.stdout.strip())

def change_directory(path):
    global current_dir
    if path == "..":
        current_dir = "/".join(current_dir.strip("/").split("/")[:-1])
    elif current_dir:
        current_dir = f"{current_dir}/{path.strip('/')}"
    else:
        current_dir = path.strip("/")

def print_working_directory():
    print(f"📂 Thư mục hiện tại: {current_dir or '/'}")

def make_directory(folder_name):
    url = build_url()
    full_path = f"{current_dir}/{folder_name}" if current_dir else folder_name
    cmd = f'curl {FTPS_OPTIONS} --user "{FTP_USER}:{FTP_PASS}" -Q "MKD {full_path}" "{url}"'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode:
        print(f"❌ Không thể tạo thư mục '{full_path}':", proc.stderr.strip().splitlines()[-1])
    else:
        print(f"✅ Đã tạo thư mục '{full_path}'")

def delete_file(file_name):
    url = build_url()
    full_path = f"{current_dir}/{file_name}" if current_dir else file_name
    cmd = f'curl {FTPS_OPTIONS} --user "{FTP_USER}:{FTP_PASS}" -Q "DELE {full_path}" "{url}"'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode:
        print(f"❌ Không thể xóa file '{full_path}':", proc.stderr.strip().splitlines()[-1])
    else:
        print(f"✅ Đã xóa file '{full_path}'")

def remove_directory_recursive(folder_name):
    global current_dir
    prev_dir = current_dir
    try:
        change_directory(folder_name)
    except Exception as e:
        print(f"❌ Không thể chuyển vào thư mục '{folder_name}': {e}")
        return

    url = build_url()
    cmd = f'curl {FTPS_OPTIONS} --user "{FTP_USER}:{FTP_PASS}" "{url}"'
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, encoding="utf-8")
    if proc.returncode or not proc.stdout:
        print(f"❌ Lỗi khi liệt kê thư mục '{folder_name}': {proc.stderr.strip().splitlines()[-1] if proc.stderr else 'Không thể lấy dữ liệu'}")
        current_dir = prev_dir
        return

    items = proc.stdout.strip().splitlines()
    for line in items:
        parts = line.split()
        if len(parts) < 9:
            continue
        name = " ".join(parts[8:])
        if line.startswith("d"):
            remove_directory_recursive(name)
        else:
            delete_file(name)

    current_dir = prev_dir
    full_path = f"{current_dir}/{folder_name}" if current_dir else folder_name
    cmd_rmd = f'curl {FTPS_OPTIONS} --user "{FTP_USER}:{FTP_PASS}" -Q "RMD {full_path}" "{build_url()}"'
    proc_rmd = subprocess.run(cmd_rmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    if proc_rmd.returncode:
        print(f"❌ Không thể xóa thư mục '{full_path}':", proc_rmd.stderr.strip().splitlines()[-1])
    else:
        print(f"✅ Đã xóa thư mục '{full_path}' và toàn bộ nội dung")

def rename_file(old_name, new_name):
    url = build_url()
    full_old = f"{current_dir}/{old_name}" if current_dir else old_name
    full_new = f"{current_dir}/{new_name}" if current_dir else new_name

    cmd = (
        f'curl {FTPS_OPTIONS} --user "{FTP_USER}:{FTP_PASS}" '
        f'-Q "RNFR {full_old}" -Q "RNTO {full_new}" "{url}"'
    )
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode:
        print(f"❌ Không thể đổi tên '{full_old}' thành '{full_new}':", proc.stderr.strip().splitlines()[-1])
    else:
        print(f"✅ Đã đổi tên từ '{full_old}' thành '{full_new}'")

def download_file(filename):
    url = build_url() + filename
    cmd = (
        f'curl {FTPS_OPTIONS} --retry 5 --retry-delay 2 '
        f'--connect-timeout 10 --max-time 30 '
        f'--user "{FTP_USER}:{FTP_PASS}" -o "{filename}" "{url}"'
    )

    for attempt in range(5):
        proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, encoding="utf-8")

        # Kiểm tra kỹ xem có tải thành công không
        if proc.returncode == 0 and os.path.exists(filename) and os.path.getsize(filename) > 0:
            print(f"✅ Đã tải file '{filename}' thành công sau {attempt + 1} lần thử")
            return

        print(f"⚠️ Thử lại lần {attempt + 1} do lỗi khi tải '{filename}'")
        time.sleep(1)

    # Kiểm tra lần cuối cùng, xóa file rác nếu có
    if os.path.exists(filename):
        os.remove(filename)

    print(f"❌ Không thể tải file '{filename}' sau 5 lần thử.")


def upload_file(file_path):
    if not os.path.isfile(file_path):
        print(f"❌ File '{file_path}' không tồn tại.")
        return
    file_name = os.path.basename(file_path)
    url = build_url() + file_name
    cmd = f'curl {FTPS_OPTIONS} --user "{FTP_USER}:{FTP_PASS}" -T "{file_path}" "{url}"'
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, encoding="utf-8")
    if proc.returncode:
        print(f"❌ Không thể upload file '{file_name}':", proc.stderr.strip().splitlines()[-1])
    else:
        print(f"✅ Đã upload file '{file_name}'")

def mget_files(pattern):
    url = build_url()
    cmd = f'curl {FTPS_OPTIONS} --user "{FTP_USER}:{FTP_PASS}" "{url}"'
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, encoding="utf-8")

    if proc.returncode or not proc.stdout:
        print("❌ Không thể lấy danh sách file:", proc.stderr.strip().splitlines()[-1] if proc.stderr else "Không có dữ liệu")
        return

    lines = proc.stdout.strip().splitlines()
    files = [" ".join(line.split()[8:]) for line in lines if not line.startswith("d")]
    matched_files = [f for f in files if fnmatch.fnmatch(f, pattern)]

    if not matched_files:
        print(f"⚠️ Không có file nào khớp với mẫu '{pattern}'")
        return

    for file in matched_files:
        if prompt_confirm:
            confirm = input(f"Tải '{file}'? (y/n): ").strip().lower()
            if confirm != "y":
                continue

        download_file(file)
        # Giảm tốc độ tải để tránh nghẽn hoặc server từ chối
        time.sleep(0.5)

def mput_files(pattern):
    local_files = [f for f in os.listdir() if os.path.isfile(f)]
    matched_files = [f for f in local_files if fnmatch.fnmatch(f, pattern)]

    for file in matched_files:
        if prompt_confirm:
            confirm = input(f"Upload '{file}'? (y/n): ").strip().lower()
            if confirm != "y":
                continue
        upload_file(file)

def toggle_prompt():
    global prompt_confirm
    prompt_confirm = not prompt_confirm
    print(f"✅ Đã {'bật' if prompt_confirm else 'tắt'} chế độ xác nhận khi dùng mget/mput")
