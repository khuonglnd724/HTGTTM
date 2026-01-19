# Tạo môi trường ảo (virtual environment)
Trước khi cài dependencies, tạo và kích hoạt virtual environment để không ảnh hưởng hệ thống:

Windows (PowerShell):
```powershell
python -m venv venv
.\n+venv\Scripts\Activate.ps1
```

Windows (cmd.exe):
```cmd
python -m venv venv
venv\Scripts\activate
```

Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

# bước 1 — cài Python packages
Sau khi đã kích hoạt `venv`, nâng pip và cài dependencies:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

# Lưu ý hệ thống
- Trên Windows/Linux bạn cần cài đặt FFmpeg (hệ thống) để hỗ trợ phát/ghi video; `imageio-ffmpeg` sẽ dùng binary FFmpeg.
- Nếu muốn sử dụng GPU (CUDA) cho PyTorch/YOLO, cài PyTorch phù hợp với CUDA của bạn trước khi `pip install -r requirements.txt` hoặc cài lại wheel tương ứng. Xem hướng dẫn tại https://pytorch.org/get-started/locally/ .

# bước 2 — chạy server
```powershell
python run_server.py
```

# Kiểm tra nhanh
- Sau khi cài dependencies, chạy server và mở http://localhost:5000
- Nếu chọn model lớn (ví dụ `yolov8x`) hãy đảm bảo file weights `yolov8x.pt` có trong thư mục gốc hoặc cài đặt ultralytics sẽ tự tải weights khi cần.
