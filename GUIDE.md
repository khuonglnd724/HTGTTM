# Lane Violation Detection System  Hướng Dẫn Toàn Diện

## Mục Lục
1. [Giới Thiệu](#giớithiệu)
2. [Cài Đặt Nhanh](#càiđặtnhanh)
3. [Sử Dụng Hệ Thống](#sửdụnghệthống)
4. [Cấu Trúc Dự Án](#cấutrúcdựán)
5. [Tính Năng Chi Tiết](#tínhnăngchitiết)
6. [Realtime Streaming](#realtimestreaming)
7. [Cấu Hình Hệ Thống](#cấuhìnhhệthống)
8. [Web UI Hướng Dẫn](#webuihướngdẫn)
9. [API Reference](#apireference)
10. [Xử Lý Sự Cố](#xửlýsựcố)
11. [Hiệu Năng](#hiệunăng)



## Giới Thiệu

**Hệ thống nhận diện các phương tiện sai làn trong tham gia giao thông sử dụng YOLOv8 và xử lý ảnh.**

Một hệ thống hoàn chỉnh AIpowered để phát hiện phương tiện đi sai làn bằng cách sử dụng:
 **YOLOv8**  Phát hiện phương tiện thời gian thực
 **OpenCV**  Xử lý ảnh và phát hiện làn đường
 **Flask**  Web server với REST API
 **Vanilla JS**  Web UI responsive

### Tính Năng Chính
 Phát hiện phương tiện (xe hơi, xe máy, bus, xe tải)
 Phát hiện làn đường tự động
 Phát hiện vi phạm sai làn
 Theo dõi phương tiện qua các frame
 Web UI hiện đại để giám sát
 REST API đầy đủ
 Hỗ trợ GPU (NVIDIA CUDA)
 Xử lý video/ảnh/webcam
 Realtime streaming từ webcam/RTSP



## Cài Đặt Nhanh (5 Phút)

### Windows
```bash
# 1. Di chuyển đến thư mục
cd d:\ITS\CK\lane_violation_detection

# 2. Tạo virtual environment
python m venv venv
venv\Scripts\activate.bat

# 3. Cài đặt dependencies
pip install r requirements.txt
```

### Linux/Mac
```bash
# 1. Di chuyển đến thư mục
cd d:\ITS\CK\lane_violation_detection

# 2. Tạo virtual environment
python m venv venv
source venv/bin/activate

# 3. Cài đặt dependencies
pip install r requirements.txt
```

### Xác Nhận Cài Đặt
```bash
python c "import torch; import cv2; import ultralytics; print('✅ Cài đặt thành công!')"
```



## 🚀 Sử Dụng Hệ Thống

### 1. Chạy Web Server (Khuyên Dùng)
```bash
# Cách đơn giản nhất
python web_server.py

# Hoặc với port custom
python run_server.py port 8000

# Hoặc debug mode
python run_server.py debug
```

**Mở browser:**
```
http://localhost:5000
```

### 2. Sử Dụng CLI (Command Line)

#### Xử Lý Video
```bash
python main.py input data/videos/sample.mp4 output data/outputs/result.mp4
```

#### Xử Lý Webcam
```bash
python main.py input 0 output data/outputs/webcam_result.mp4
```

#### Xử Lý Ảnh
```bash
python main.py image road.jpg output road_result.jpg
```

#### Với Model Khác
```bash
# Model nhỏ  nhanh
python main.py input video.mp4 model yolov8n output result.mp4

# Model lớn  chính xác
python main.py input video.mp4 model yolov8l output result.mp4
```

#### Với Cấu Hình Custom
```bash
python main.py config configs/config.yaml input video.mp4
```



## 📁 Cấu Trúc Dự Án

```
lane_violation_detection/
│
├── 🌐 WEB SERVER
│   ├── web_server.py                 ← Chạy đơn giản
│   ├── run_server.py                 ← Chạy với option
│   └── app/
│       ├── server.py                 ← Flask app & API
│       ├── templates/index.html      ← Web UI HTML
│       └── static/
│           ├── css/style.css         ← Styling
│           └── js/
│               ├── api.js            ← API client
│               ├── ui.js             ← UI utilities
│               └── app.js            ← Main logic
│
├── 🐍 DETECTION ENGINE
│   ├── main.py                       ← CLI entry point
│   ├── test.py                       ← Test suite
│   ├── examples.py                   ← Ví dụ sử dụng
│   └── src/
│       ├── pipeline.py               ← Main pipeline
│       ├── modules/
│       │   ├── vehicle_detector.py   ← YOLO detection
│       │   ├── lane_detector.py      ← Lane detection
│       │   ├── violation_detector.py ← Violation logic
│       │   └── tracker.py            ← Vehicle tracking
│       └── utils/
│           ├── config_loader.py      ← Config management
│           ├── logger.py             ← Logging
│           ├── drawing.py            ← Visualization
│           ├── video_processor.py    ← Video I/O
│           └── analytics.py          ← Statistics
│
├── ⚙️ CONFIG
│   ├── configs/config.yaml           ← System settings
│   └── requirements.txt              ← Dependencies
│
├── 📚 DATA
│   ├── data/
│   │   ├── videos/                   ← Input videos
│   │   ├── models/                   ← YOLO models cache
│   │   └── outputs/                  ← Results
│   └── logs/                         ← Log files
│
└── 📖 THIS FILE
    └── GUIDE.md                      ← Tài liệu toàn diện
```



## 🎨 Tính Năng Chi Tiết

### 1️⃣ Vehicle Detection (Phát Hiện Phương Tiện)

**Sử dụng YOLOv8 để phát hiện các lớp phương tiện:**
 🚗 Ô tô/Xe hơi
 🏍️ Xe máy/Motor
 🚌 Xe buýt
 🚚 Xe tải

**Các tính năng:**
 Realtime detection (100+ FPS with GPU)
 Configurable confidence threshold
 Class filtering
 GPU acceleration support

### 2️⃣ Lane Detection (Phát Hiện Làn Đường)

**Quy trình:**
1. Tiền xử lý (Gaussian blur, CLAHE)
2. Edge detection (Canny)
3. ROI masking (Region of Interest)
4. Hough transform (phát hiện đường thẳng)
5. Lane boundary extraction

**Kết quả:**
 Xác định ranh giới làn trái/phải
 Số lượng làn phát hiện
 Các điểm ranh giới chính xác

### 3️⃣ Violation Detection (Phát Hiện Vi Phạm)

**Cách hoạt động:**
 Kiểm tra tâm và hộp phương tiện so với ranh giới làn
 Tính điểm vi phạm (0.0  1.0)
 Theo dõi lịch sử vi phạm per vehicle
 Cooldown mechanism để tránh cảnh báo trùng lặp

**Thông tin vi phạm:**
 Track ID của phương tiện
 Mức độ vi phạm
 Số lần vi phạm liên tiếp
 Thông tin chi tiết detection

### 4️⃣ Vehicle Tracking (Theo Dõi Phương Tiện)

**Thuật toán:**
 Centroidbased tracking
 Persistent vehicle IDs across frames
 Trajectory recording
 Lost track management

### 5️⃣ Analytics (Thống Kê)

**Thông tin thu thập:**
 Số frame xử lý
 FPS (frame per second)
 Tổng phương tiện phát hiện
 Tổng vi phạm
 Tỷ lệ vi phạm
 Thời gian xử lý

### 6️⃣ Web UI (Giao Diện Web)

**Chức năng:**
 📤 Upload video/ảnh (drag & drop)
 🔄 Giám sát xử lý thời gian thực
 📊 Dashboard thống kê
 ⚙️ Cấu hình hệ thống
 📥 Download kết quả



## ⚙️ Cấu Hình Hệ Thống

### Tệp Cấu Hình: `configs/config.yaml`

```yaml
# ==================== YOLO CONFIGURATION ====================
yolo:
  model_name: "yolov8m"           # Kích thước model
  confidence_threshold: 0.5       # Ngưỡng tin cậy (01)
  iou_threshold: 0.45             # IoU threshold
  device: "cuda"                  # "cuda" (GPU) hoặc "cpu"

# ==================== LANE DETECTION ====================
lane_detection:
  method: "hough"                 # Phương pháp phát hiện
  canny_threshold1: 50            # Canny low threshold
  canny_threshold2: 150           # Canny high threshold
  hough_threshold: 50             # Hough transform threshold
  hough_min_line_length: 50       # Độ dài dòng tối thiểu
  hough_max_line_gap: 10          # Khoảng cách dòng tối đa
  roi_bottom_margin: 50           # Margin dưới cùng

# ==================== VIOLATION DETECTION ====================
violation:
  violation_threshold: 0.3        # Ngưỡng vi phạm
  consecutive_frames: 3           # Frame liên tiếp để xác định vi phạm
  cooldown_frames: 5              # Cooldown giữa các cảnh báo

# ==================== PROCESSING ====================
processing:
  input_source: "data/videos/sample.mp4"
  output_path: "data/outputs/result.mp4"
  frame_skip: 1                   # Xử lý mỗi N frame (1=all)
  draw_trajectories: true         # Vẽ quỹ đạo
  draw_confidence: true           # Vẽ confidence scores
  save_analytics: true            # Lưu analytics report

# ==================== LOGGER ====================
logger:
  level: "INFO"                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: "logs/lane_detection.log"
  log_dir: "logs"
```

### Các Model YOLOv8 Khác Nhau

| Model | Tốc Độ | Độ Chính Xác | VRAM | FPS (GPU) | Dùng Khi |
|||||||
| **yolov8n** | ⚡ Rất Nhanh | Bình Thường | 2GB | 100+ | Cần tốc độ cao |
| **yolov8s** | ⚡ Nhanh | Tốt | 3GB | 6080 | Cân bằng tốc độ |
| **yolov8m** | ⚖️ Cân Bằng | Rất Tốt | 5GB | 3040 | **Khuyên dùng** |
| **yolov8l** | 🐢 Chậm | Xuất Sắc | 7GB | 2025 | Cần độ chính xác cao |
| **yolov8x** | 🐌 Rất Chậm | Tối Ưu | 10GB | 1520 | Cần chính xác nhất |

### Ví Dụ Cấu Hình Khác Nhau

#### Cho Máy Tính Yếu
```yaml
yolo:
  model_name: "yolov8n"
  device: "cpu"

processing:
  frame_skip: 2
```

#### Cho Máy Tính Mạnh (GPU)
```yaml
yolo:
  model_name: "yolov8l"
  confidence_threshold: 0.4
  device: "cuda"
```

#### Cho Độ Chính Xác Cao
```yaml
yolo:
  model_name: "yolov8x"
  confidence_threshold: 0.3
  device: "cuda"

lane_detection:
  canny_threshold1: 40
  canny_threshold2: 120
```

---

## Real-time Streaming

### Khởi động Streaming từ Webcam

```bash
# Trên browser, mở:
http://localhost:5000/api/stream?source=0&model=yolov8m
```

### Khởi động Streaming từ RTSP URL

```bash
# Ví dụ IP Camera
http://localhost:5000/api/stream?source=rtsp://192.168.1.100:554/stream&model=yolov8m
```

### Tùy chọn Streaming

| Parameter | Giá trị | Mô tả |
|-----------|--------|-------|
| source | 0 | Webcam mặc định |
| source | 1, 2,... | Webcam khác |
| source | rtsp://... | RTSP stream |
| model | yolov8n/s/m/l/x | Mô hình phát hiện |

### Tích hợp Streaming vào Web UI

Thêm vào HTML:

```html
<img id="stream" src="http://localhost:5000/api/stream?source=0&model=yolov8m" 
     width="100%" alt="Real-time Stream">
```

### Ví dụ Python

```python
import requests
from PIL import Image
from io import BytesIO

# Kết nối đến stream
stream_url = 'http://localhost:5000/api/stream?source=0&model=yolov8m'
response = requests.get(stream_url, stream=True)

if response.status_code == 200:
    for chunk in response.iter_content(chunk_size=1024):
        print(f"Received {len(chunk)} bytes")
```

---

## Cấu Hình Hệ Thống

### Bắt Đầu Web Server

```bash
python web_server.py
# Hoặc: python run_server.py
```

Mở browser: `http://localhost:5000`

### Các Tính Năng Web UI

#### 1. Upload Tab (📤 Tải Lên)
 Kéo thả (drag & drop) hoặc click để chọn file
 Hỗ trợ: MP4, AVI, MOV, MKV (video), JPEG, PNG (ảnh)
 Tối đa: 500MB mỗi file

**Tùy chọn xử lý:**
 **YOLO Model**: Chọn model (n/s/m/l/x)
 **Confidence Threshold**: Ngưỡng tin cậy (0.11.0)
 **Draw Confidence**: Hiển thị % tin cậy
 **Draw Trajectories**: Vẽ đường đi của xe
 **Bắt đầu**: Kích hoạt xử lý

#### 2. Processing Tab (🔄 Đang Xử Lý)
 Giám sát các tác vụ đang chạy
 Thanh tiến độ theo thời gian thực
 Trạng thái (Queued, Processing, Completed, Failed)
 Tốc độ xử lý (FPS)
 Nút download kết quả

#### 3. Results Tab (📊 Kết Quả)
 Xem tất cả kết quả đã xử lý
 Lọc theo trạng thái
 Thống kê chi tiết:
   Thời gian xử lý
   FPS trung bình
   Số frame
   Số vi phạm
   Tỷ lệ vi phạm
 Download video đã xử lý

#### 4. Settings Tab (⚙️ Cấu Hình)
 Điều chỉnh tham số YOLO
 Điều chỉnh làn detection
 Chọn device (CPU/CUDA)
 Lưu cấu hình vào file

### Bàn Phím Tắt
| Phím | Chức Năng |
|||
| `1` | Tab Upload |
| `2` | Tab Processing |
| `3` | Tab Results |
| `4` | Tab Settings |



## API Reference

### REST API Endpoints

#### 1. Get Server Status
```bash
GET /api/status
```
Response:
```json
{
  "status": "online",
  "timestamp": "2026-01-04T10:00:00",
  "tasks_count": 5,
  "active_tasks": 2
}
```

#### 2. Real-time Video Stream
```bash
GET /api/stream?source=0&model=yolov8m
```
Parameters:
- source: 0 (webcam), 1, 2,... or rtsp://url
- model: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x

Returns: MJPEG video stream

#### 3. Upload File
```bash
POST /api/upload
Content-Type: multipart/form-data

file: <binary>
```
Response:
```json
{
  "filename": "video.mp4",
  "path": "data/uploads/20260102_120000_video.mp4",
  "size": 51234567
}
```

#### 4. Start Processing
```bash
POST /api/process
Content-Type: application/json

{
  "input_path": "data/uploads/video.mp4",
  "type": "video",
  "model": "yolov8m",
  "confidence_threshold": 0.5
}
```
Response:
```json
{
  "task_id": "task_0",
  "status": "processing",
  "progress": 0
}
```

#### 4. Get Task Status
```bash
GET /api/task/{task_id}
```
Response:
```json
{
  "task_id": "task_0",
  "status": "processing",
  "progress": 45,
  "start_time": "2026-01-04T10:00:00",
  "end_time": null,
  "error_message": null,
  "analytics": {
    "total_frames": 1000,
    "avg_fps": 35.2,
    "total_detections": 450,
    "total_violations": 12
  }
}
```

#### 5. List All Tasks
```bash
GET /api/tasks
```
Response:
```json
{
  "tasks": [
    {"task_id": "task_0", "status": "completed", "progress": 100, "type": "video"},
    {"task_id": "task_1", "status": "processing", "progress": 50, "type": "video"}
  ]
}
```

#### 6. Download Result
```bash
GET /api/download/{task_id}
```
Trả về file video đã xử lý

#### 7. Get Configuration
```bash
GET /api/config
```
Response:
```json
{
  "yolo": {...},
  "lane_detection": {...},
  "processing": {...}
}
```

#### 8. Update Configuration
```bash
POST /api/config
ContentType: application/json

{
  "yolo.model_name": "yolov8l",
  "yolo.device": "cuda"
}
```

### Sử Dụng API với Python
```python
import requests

# Upload file
files = {'file': open('video.mp4', 'rb')}
r = requests.post('http://localhost:5000/api/upload', files=files)
print(r.json())

# Start processing
data = {
    'input_path': r.json()['path'],
    'type': 'video',
    'model': 'yolov8m'
}
r = requests.post('http://localhost:5000/api/process', json=data)
task_id = r.json()['task_id']

# Check status
r = requests.get(f'http://localhost:5000/api/task/{task_id}')
print(r.json())

# Download result
r = requests.get(f'http://localhost:5000/api/download/{task_id}')
with open('result.mp4', 'wb') as f:
    f.write(r.content)
```

### Python Classes & Methods

#### VehicleDetector
```python
from src.modules.vehicle_detector import VehicleDetector

detector = VehicleDetector(model_name="yolov8m", device="cuda")
results = detector.detect(image)
# Results: {detections, num_detections, image_shape}
```

#### LaneDetector
```python
from src.modules.lane_detector import LaneDetector

detector = LaneDetector(canny_threshold1=50, canny_threshold2=150)
results = detector.detect_lanes(image)
boundaries = detector.get_lane_boundaries(image)
```

#### ViolationDetector
```python
from src.modules.violation_detector import ViolationDetector

detector = ViolationDetector(violation_threshold=0.3)
violations = detector.batch_detect_violations(detections, lane_boundaries)
```

#### Pipeline
```python
from src.pipeline import LaneViolationPipeline

pipeline = LaneViolationPipeline("configs/config.yaml")
results = pipeline.process_frame(frame, frame_num)
annotated = pipeline.draw_results(frame, results)
pipeline.run()  # Process entire video
```



## 🐛 Xử Lý Sự Cố

### ❌ Web Server Không Chạy
```bash
# Kiểm tra port 5000 đang sử dụng không
netstat ano | findstr :5000

# Dùng port khác
python run_server.py port 8000
```

### ❌ Module Không Tìm Thấy
```bash
pip install r requirements.txt
```

### ❌ Phát Hiện Quá Ít Phương Tiện
1. Giảm `confidence_threshold` (0.30.4 thay vì 0.5)
2. Sử dụng model lớn hơn (yolov8l, yolov8x)
3. Kiểm tra chất lượng video

### ❌ Xử Lý Chậm
1. Sử dụng model nhỏ (yolov8n, yolov8s)
2. Tăng `frame_skip` (xử lý mỗi 23 frame)
3. Bật GPU: `device: "cuda"` trong config
4. Kiểm tra: `nvidiasmi`

### ❌ Phát Hiện Làn Không Chính Xác
1. Điều chỉnh `canny_threshold1` (3050)
2. Điều chỉnh `canny_threshold2` (100200)
3. Tăng `hough_threshold` để lọc dòng yếu
4. Đảm bảo video có độ sáng tốt

### ❌ CUDA Không Khả Dụng
```bash
# Kiểm tra driver NVIDIA
nvidiasmi

# Cập nhật PyTorch
pip install torch torchvision torchaudio indexurl https://download.pytorch.org/whl/cu118

# Hoặc dùng CPU
# Sửa config.yaml: device: "cpu"
```

### ❌ Upload Không Thành Công
 Kiểm tra định dạng (MP4, AVI, MOV, MKV)
 Kiểm tra dung lượng < 500MB
 Kiểm tra dung lượng đĩa trống

### ❌ Web UI Không Load
1. Refresh browser: `Ctrl+R`
2. Xóa cache: `Ctrl+Shift+Delete`
3. Mở console: `F12`
4. Khởi động lại server



## 📈 Hiệu Năng

### Tốc Độ Xử Lý (GPU RTX 3080)

| Model | FPS | VRAM | Độ Chính Xác |
|||||
| yolov8n | 100+ | 2GB | Bình Thường |
| yolov8s | 6080 | 3GB | Tốt |
| yolov8m | 3040 | 5GB | Rất Tốt |
| yolov8l | 2025 | 7GB | Xuất Sắc |
| yolov8x | 1520 | 10GB | Tối Ưu |

### Tốc Độ Xử Lý (CPU Intel i710700K)

| Model | FPS |
|||
| yolov8n | 810 |
| yolov8s | 45 |
| yolov8m | 12 |

### Yêu Cầu Hệ Thống

| Thành Phần | Tối Thiểu | Khuyên Dùng |
||||
| CPU | 4 cores | 8 cores |
| RAM | 4GB | 8GB+ |
| GPU |  | NVIDIA RTX 30/40 |
| Storage | 20GB | 100GB+ |
| OS | Windows 10+ | Windows 10/11 |



## 📝 Các Lệnh Hữu Ích

```bash
# 1. Kích hoạt virtual environment
venv\Scripts\activate.bat

# 2. Bắt đầu web server
python web_server.py

# 3. Xử lý video từ CLI
python main.py input video.mp4 output result.mp4

# 4. Xử lý webcam
python main.py input 0 output webcam_result.mp4

# 5. Chạy kiểm tra hệ thống
python test.py mode modules

# 6. Chạy ví dụ
python examples.py

# 7. Thoát virtual environment
deactivate

# 8. Kiểm tra GPU
nvidiasmi
```



## 🎓 Ví Dụ Sử Dụng

### Ví Dụ 1: Video Xử Lý Đơn Giản
```bash
python main.py input data/videos/traffic.mp4 output data/outputs/result.mp4
```

### Ví Dụ 2: Dùng Model Chính Xác Cao
```bash
python main.py input video.mp4 model yolov8l output result.mp4
```

### Ví Dụ 3: Xử Lý Nhanh (Máy Yếu)
```bash
python main.py input video.mp4 model yolov8n output result.mp4
```

### Ví Dụ 4: Webcam Realtime
```bash
python main.py input 0 output webcam_result.mp4
```

### Ví Dụ 5: Custom Configuration
```bash
python main.py config configs/config.yaml input video.mp4
```

### Ví Dụ 6: Xử Lý Ảnh
```bash
python main.py image road.jpg output road_result.jpg
```



## 🎉 Bước Tiếp Theo

1. ✅ Cài đặt: `pip install r requirements.txt`
2. ✅ Chạy: `python web_server.py`
3. ✅ Mở: `http://localhost:5000`
4. ✅ Tải: Kéo thả video
5. ✅ Giám sát: Xem tiến độ
6. ✅ Tải xuống: Lấy kết quả



## 📞 Hỗ Trợ

 ✅ Kiểm tra logs: `logs/lane_detection.log`
 ✅ Xem ví dụ: `examples.py`
 ✅ Chạy test: `test.py`
 ✅ Kiểm tra config: `configs/config.yaml`



## 📝 Thông Tin Phiên Bản

 **Phiên Bản**: 1.0
 **Cập Nhật**: January 2, 2026
 **Trạng Thái**: ✅ Hoàn chỉnh & Sản xuất sẵn sàng
 **Giấy Phép**: MIT



**Chúc Bạn Sử Dụng Thành Công!** 🚀

