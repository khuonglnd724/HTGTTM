# Hệ Thống Phát Hiện Vi Phạm Làn Giao Thông Thông Minh

Hệ thống sử dụng YOLOv8 và computer vision để phát hiện phương tiện vi phạm làn đường trong video giao thông.

---

##  Yêu cầu hệ thống

- **Python**: 3.8 - 3.11 (khuyến nghị 3.10)
- **FFmpeg**: Cài đặt system-wide để xử lý video
  - Windows: Tải từ https://ffmpeg.org/download.html và thêm vào PATH
  - Linux: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
- **CUDA** (tùy chọn): Nếu muốn dùng GPU để xử lý nhanh hơn
  - Kiểm tra compatibility: https://pytorch.org/get-started/locally/

---

##  Hướng dẫn cài đặt

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd HTGTTM
```

### Bước 2: Tạo môi trường ảo (virtual environment)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (cmd.exe):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt Python dependencies

Sau khi đã kích hoạt virtual environment:

```bash
# Nâng cấp pip
python -m pip install --upgrade pip

# Cài đặt tất cả dependencies
pip install -r requirements.txt
```

**Dependencies chính:**
- `ultralytics`: YOLOv8 framework
- `opencv-contrib-python`: Computer vision
- `torch`, `torchvision`: Deep learning
- `Flask`: Web server
- `numpy`, `scipy`, `matplotlib`: Scientific computing

### Bước 4: Tạo cấu trúc thư mục

```bash
# Tạo các thư mục cần thiết (nếu chưa có)
mkdir -p data/uploads data/outputs/videos data/outputs/violations data/outputs/zones logs
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path data/uploads, data/outputs/videos, data/outputs/violations, data/outputs/zones, logs
```

### Bước 5: Cấu hình (tùy chọn)

File cấu hình mặc định: `configs/config.yaml`

Bạn có thể điều chỉnh các thông số:
- **YOLO model**: confidence_threshold, device (cpu/cuda)
- **Tracking**: IOU threshold, max_age
- **Lane detection**: Canny/Hough parameters
- **Processing**: frame_skip, max_resolution

---

##  Chạy ứng dụng

### Khởi động server

```bash
python run_server.py
```

Server sẽ chạy tại: **http://localhost:5000**

### Sử dụng Web UI

1. Mở trình duyệt: http://localhost:5000
2. **Tải lên** video/hình ảnh giao thông
3. **Định nghĩa vùng** (zones) cho từng làn đường
4. **Chọn loại phương tiện** được phép trong mỗi vùng
5. **Bắt đầu xử lý** và xem kết quả

---

##  Dependencies từ requirements.txt

```
ultralytics==8.0.238          # YOLOv8
opencv-contrib-python==4.8.1.78  # OpenCV with extra modules
torch==2.1.1                  # PyTorch
torchvision==0.16.1
torchaudio==2.1.1
numpy==1.24.3
scikit-learn==1.3.2
scipy==1.11.4
matplotlib==3.8.2
Pillow==10.1.0
pyyaml==6.0.1
requests==2.31.0
Flask==2.3.3                  # Web framework
Flask-CORS==4.0.0
Werkzeug==2.3.7
lapx>=0.5.2                   # Linear assignment for tracking
imageio==2.34.0
imageio-ffmpeg==0.4.9         # Video I/O
```

---

##  Cấu hình GPU (CUDA)

Nếu muốn sử dụng GPU để tăng tốc xử lý:

1. **Cài NVIDIA CUDA Toolkit** (11.8 hoặc 12.1)
2. **Cài PyTorch với CUDA**:

```bash
# Gỡ PyTorch CPU (nếu đã cài)
pip uninstall torch torchvision torchaudio

# Cài PyTorch GPU (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Hoặc CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

3. **Kiểm tra**:
```python
import torch
print(torch.cuda.is_available())  # True nếu GPU sẵn sàng
```

Xem thêm: https://pytorch.org/get-started/locally/

---

##  Cấu trúc thư mục

```
HTGTTM/
 app/                      # Flask web application
    static/              # CSS, JS, images
    templates/           # HTML templates
    server.py            # Flask routes
 configs/                 # Configuration files
    config.yaml          # Main config
 data/                    # Data directory (gitignored)
    uploads/            # User uploaded files
    outputs/            # Processing results
       videos/         # Processed videos
       violations/     # Violation snapshots
       zones/          # Zone definitions
 logs/                    # Application logs
 src/                     # Core processing modules
    detector.py         # YOLO detection
    tracker.py          # Multi-object tracking
    zone_manager.py     # Zone management
    pipeline.py         # Main processing pipeline
 requirements.txt         # Python dependencies
 run_server.py           # Application entry point
 README.md               # This file
```

---

##  Xử lý sự cố

### Lỗi: "No module named 'cv2'"
```bash
pip install opencv-contrib-python
```

### Lỗi: "FFmpeg not found"
- Cài FFmpeg system-wide và thêm vào PATH
- Hoặc: `pip install imageio-ffmpeg` (đã có trong requirements.txt)

### Lỗi: PyTorch không nhận GPU
- Kiểm tra CUDA version: `nvidia-smi`
- Cài đúng PyTorch version tương thích với CUDA

### Lỗi: Port 5000 đã được sử dụng
```bash
# Đổi port trong run_server.py hoặc kill process đang dùng port
```

### Video không phát được
- Đảm bảo FFmpeg đã được cài đặt
- Kiểm tra định dạng video (hỗ trợ: MP4, AVI, MOV)

---

##  Lưu ý

- **YOLO weights** sẽ được tự động tải xuống lần đầu chạy (khoảng 6-50MB tùy model)
- Thư mục `data/` không được commit vào git (trong .gitignore)
- Khuyến nghị dùng Python 3.10 để tránh lỗi tương thích
- Đảm bảo đủ dung lượng ổ cứng cho video output (có thể rất lớn)

---

##  Tính năng

-  Phát hiện phương tiện sử dụng YOLOv8
-  Tracking đa đối tượng với DeepSORT
-  Quản lý vùng (zones) tùy chỉnh cho từng làn
-  Phát hiện vi phạm làn đường real-time
-  Web UI thân thiện với người dùng
-  Xuất báo cáo PDF, CSV, hình ảnh vi phạm
-  Hỗ trợ xử lý batch nhiều video
-  Dashboard thống kê trực quan

---

##  Đóng góp

1. Fork repository
2. Tạo branch mới: `git checkout -b feature/TenTinhNang`
3. Commit changes: `git commit -m 'Thêm tính năng X'`
4. Push to branch: `git push origin feature/TenTinhNang`
5. Mở Pull Request

---

##  License

[Thêm thông tin license của bạn ở đây]
