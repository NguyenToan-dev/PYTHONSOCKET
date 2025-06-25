Cách chuyển thư mục đúng trong PowerShell:
Nếu bạn muốn chuyển đến ổ D: và thư mục D:\PYTHONSOCKET\socket_project, bạn làm như sau:
powershell
Sao chép
Chỉnh sửa
D:
Set-Location "D:\PYTHONSOCKET\socket_project"
Hoặc gộp lại:

powershell
Sao chép
Chỉnh sửa
Set-Location D:\PYTHONSOCKET\socket_project