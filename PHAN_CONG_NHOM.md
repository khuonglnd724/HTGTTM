# PHÂN CÔNG CÔNG VIỆC DỰ ÁN
## Hệ Thống Phát Hiện Vi Phạm Làn Giao Thông Thông Minh

**Ngày bắt đầu:** 23/01/2026  
**Công nghệ:** Python (Flask, OpenCV, YOLOv8), JavaScript (Vanilla JS), HTML/CSS

---

## 📊 TỔNG QUAN DỰ ÁN

### Mô tả
Hệ thống AI phát hiện vi phạm làn giao thông sử dụng:
- **Computer Vision:** YOLOv8 để phát hiện phương tiện
- **Deep Learning:** PyTorch để training model
- **Image Processing:** OpenCV để xử lý video/hình ảnh
- **Web Framework:** Flask để xây dựng web server
- **Frontend:** Vanilla JavaScript với Chart.js

### Cấu trúc dự án
```
├── src/                    # Backend AI modules
│   ├── modules/           # Core AI modules
│   │   ├── vehicle_detector.py    # YOLOv8 phát hiện xe
│   │   ├── lane_detector.py       # Phát hiện làn đường
│   │   ├── violation_detector.py  # Phát hiện vi phạm
│   │   └── tracker.py             # Tracking xe qua frames
│   ├── utils/             # Utilities
│   │   ├── video_processor.py     # Xử lý video
│   │   ├── zone_manager.py        # Quản lý vùng giám sát
│   │   ├── analytics.py           # Thống kê dữ liệu
│   │   └── drawing.py             # Vẽ annotations
│   └── pipeline.py        # Main processing pipeline
├── app/                   # Web application
│   ├── server.py          # Flask REST API (24 endpoints)
│   ├── static/            # Frontend assets
│   │   ├── js/           # JavaScript modules
│   │   └── css/          # Stylesheets
│   └── templates/         # HTML templates
├── configs/               # Configuration files
└── data/                  # Data storage
```

### Tính năng chính
1. ✅ Upload video và extract frame để vẽ zones
2. ✅ Vẽ và quản lý zones (vùng giám sát) trên canvas
3. ✅ Xử lý video real-time với YOLOv8
4. ✅ Phát hiện vi phạm làn đường
5. ✅ Tracking phương tiện qua frames
6. ✅ Dashboard thống kê real-time (6 stat cards)
7. ✅ Export báo cáo (PDF, CSV, ZIP hình ảnh, ZIP video clips)
8. ✅ Dark mode UI
9. ✅ Auto-load violations sau 5s upload
10. ✅ Video clip extraction (5s mỗi vi phạm)

---

## 👥 PHÂN CÔNG CHI TIẾT

### **THÀNH VIÊN 1: TRƯỞNG NHÓM - AI/ML ENGINEER**
**Vai trò:** Kiến trúc sư AI, quản lý dự án

#### Nhiệm vụ chính:
1. **Core AI Pipeline** (40%)
   - ✅ Hoàn thiện `src/pipeline.py` (539 dòng)
   - ✅ Tích hợp các modules (vehicle, lane, violation, tracker)
   - ✅ Optimize processing performance (frame skip, batch processing)
   - 🔄 Cải thiện accuracy của model
   - 📝 Viết unit tests cho pipeline

2. **Vehicle Detection Module** (30%)
   - ✅ YOLOv8 integration (`src/modules/vehicle_detector.py`)
   - ✅ Multi-device support (CPU/CUDA)
   - ✅ Half-precision inference (FP16)
   - 🔄 Fine-tune model cho traffic Vietnam
   - 📝 Benchmark các model versions (yolov8n/s/m/l/x)

3. **Project Management** (30%)
   - 📋 Review code của các thành viên
   - 📄 Viết technical documentation
   - 🐛 Debug integration issues
   - 📊 Báo cáo tiến độ cho giảng viên

#### Deliverables:
- [ ] Pipeline tối ưu với accuracy > 85%
- [ ] Documentation đầy đủ (README, GUIDE)
- [ ] Test suite coverage > 70%
- [ ] Performance report (FPS, memory usage)

#### Files chịu trách nhiệm:
- `src/pipeline.py`
- `src/modules/vehicle_detector.py`
- `src/modules/tracker.py`
- `configs/config.yaml`
- `README.md`, `GUIDE.md`

---

### **THÀNH VIÊN 2: COMPUTER VISION SPECIALIST**
**Vai trò:** Chuyên gia xử lý ảnh và phát hiện vi phạm

#### Nhiệm vụ chính:
1. **Lane Detection** (40%)
   - ✅ Classic CV approach (`src/modules/lane_detector.py`)
   - ✅ Canny edge detection + Hough transform
   - 🔄 Improve lane detection accuracy
   - 🔄 Handle các điều kiện ánh sáng khác nhau
   - 📝 Test với nhiều loại đường khác nhau

2. **Violation Detection Logic** (35%)
   - ✅ Zone-based violation detection (`src/modules/violation_detector.py`)
   - ✅ Vehicle tracking history
   - ✅ Confidence scoring
   - 🔄 Reduce false positives
   - 📝 Implement violation confirmation logic (multiple frames)

3. **Image Processing Utils** (25%)
   - ✅ Drawing utilities (`src/utils/drawing.py`)
   - ✅ Video processing (`src/utils/video_processor.py`)
   - 🔄 Optimize codec compatibility
   - 🔄 Add video quality settings
   - 📝 Handle edge cases (corrupted frames, etc.)

#### Deliverables:
- [ ] Lane detection với accuracy > 80%
- [ ] Violation detection với false positive rate < 10%
- [ ] Video output với quality settings
- [ ] Test cases cho edge scenarios

#### Files chịu trách nhiệm:
- `src/modules/lane_detector.py`
- `src/modules/violation_detector.py`
- `src/utils/video_processor.py`
- `src/utils/drawing.py`

---

### **THÀNH VIÊN 3: BACKEND DEVELOPER**
**Vai trò:** Flask API và business logic

#### Nhiệm vụ chính:
1. **REST API Endpoints** (45%)
   - ✅ Flask server với 24 endpoints (`app/server.py`)
   - ✅ File upload và preview generation
   - ✅ Task management (queue, processing, completed)
   - ✅ Zones CRUD operations
   - ✅ Export endpoints (CSV, PDF, ZIP)
   - 🔄 Add authentication/authorization
   - 🔄 Optimize large file handling
   - 📝 API documentation (Swagger/OpenAPI)

2. **Data Management** (30%)
   - ✅ Zone manager (`src/utils/zone_manager.py`)
   - ✅ Analytics collector (`src/utils/analytics.py`)
   - 🔄 Database integration (SQLite/PostgreSQL)
   - 🔄 Data persistence và caching
   - 📝 Migration scripts

3. **Export & Reporting** (25%)
   - ✅ Video clip extraction (5s segments)
   - ✅ PDF generation với high quality images
   - ✅ CSV export với metadata
   - 🔄 Excel export with charts
   - 🔄 Email notification system
   - 📝 Report templates

#### Deliverables:
- [ ] Stable API với error handling
- [ ] Complete API documentation
- [ ] Database schema và migrations
- [ ] Export system với multiple formats

#### Files chịu trách nhiệm:
- `app/server.py` (1000+ dòng)
- `src/utils/zone_manager.py`
- `src/utils/analytics.py`
- `src/utils/config_loader.py`
- `src/utils/logger.py`

---

### **THÀNH VIÊN 4: FRONTEND DEVELOPER**
**Vai trò:** UI/UX và JavaScript development

#### Nhiệm vụ chính:
1. **Core JavaScript Modules** (40%)
   - ✅ App orchestration (`app/static/js/app.js` - 563 dòng)
   - ✅ UI utilities (`app/static/js/ui.js` - 514 dòng)
   - ✅ API client (`app/static/js/api.js`)
   - 🔄 Refactor to modern ES6+ modules
   - 🔄 Add error boundaries
   - 📝 JSDoc documentation

2. **Zone Editor** (30%)
   - ✅ Canvas-based zone drawing (`app/static/js/zones.js`)
   - ✅ Polygon creation/editing
   - ✅ Rescaling cho video resolution
   - 🔄 Add undo/redo functionality
   - 🔄 Improve UX (snap to grid, guidelines)
   - 📝 User guide cho zone editor

3. **Dashboard & Charts** (30%)
   - ✅ Real-time dashboard (`app/static/js/dashboard.js` - 403 dòng)
   - ✅ Chart.js integration (6 stat cards)
   - ✅ Top violations và vehicles
   - 🔄 Add more chart types (line, pie)
   - 🔄 Real-time updates via WebSocket
   - 📝 Dashboard customization

#### Deliverables:
- [ ] Responsive UI cho mobile/tablet
- [ ] Zone editor với advanced features
- [ ] Dashboard với real-time updates
- [ ] JavaScript test coverage > 60%

#### Files chịu trách nhiệm:
- `app/static/js/app.js`
- `app/static/js/ui.js`
- `app/static/js/zones.js`
- `app/static/js/dashboard.js`
- `app/static/js/api.js`

---

### **THÀNH VIÊN 5: UI/UX DESIGNER & QA**
**Vai trò:** Design và quality assurance

#### Nhiệm vụ chính:
1. **UI Design & Styling** (40%)
   - ✅ Modern dark theme (`app/static/css/style.css` - 1430 dòng)
   - ✅ Responsive grid layout
   - ✅ Stat cards với gradients
   - 🔄 Design system documentation
   - 🔄 Accessibility improvements (WCAG)
   - 🔄 Light theme variant
   - 📝 UI component library

2. **HTML Templates** (25%)
   - ✅ Main template (`app/templates/index.html` - 699 dòng)
   - ✅ 8 sections (dashboard, upload, zones, etc.)
   - 🔄 Separate templates cho each section
   - 🔄 Add loading states
   - 🔄 Error pages (404, 500)
   - 📝 Template documentation

3. **Quality Assurance** (35%)
   - 🧪 Manual testing toàn bộ features
   - 🧪 Browser compatibility testing
   - 🧪 Performance testing (lighthouse)
   - 🐛 Bug reporting và tracking
   - 📝 Test cases documentation
   - 📝 User acceptance testing (UAT)

#### Deliverables:
- [ ] Polished UI với consistent design
- [ ] Accessibility report (WCAG AA)
- [ ] Test report với bug list
- [ ] User manual với screenshots

#### Files chịu trách nhiệm:
- `app/static/css/style.css`
- `app/templates/index.html`
- Test documentation
- User manual

---

## 📅 TIMELINE & MILESTONES

### **Sprint 1 (Tuần 1-2): Foundation**
- [ ] **TN1:** Pipeline integration hoàn chỉnh
- [ ] **TN2:** Lane & violation detection stable
- [ ] **TN3:** REST API đầy đủ 24 endpoints
- [ ] **TN4:** Frontend modules working
- [ ] **TN5:** Basic UI completed

**Mục tiêu:** Hệ thống chạy end-to-end (upload → process → view results)

### **Sprint 2 (Tuần 3-4): Enhancement**
- [ ] **TN1:** Model optimization (accuracy, speed)
- [ ] **TN2:** Advanced CV algorithms
- [ ] **TN3:** Database integration, caching
- [ ] **TN4:** Zone editor improvements
- [ ] **TN5:** UI polish, responsive design

**Mục tiêu:** Production-ready với performance tốt

### **Sprint 3 (Tuần 5-6): Testing & Documentation**
- [ ] **Tất cả:** Integration testing
- [ ] **Tất cả:** Bug fixes
- [ ] **TN1 + TN3:** Technical documentation
- [ ] **TN5:** User manual, test report
- [ ] **Trưởng nhóm:** Final presentation slides

**Mục tiêu:** Hoàn thiện báo cáo và demo

---

## 🎯 KẾT QUẢ MỘT VÀI

### Metrics đánh giá:
1. **Accuracy:** Detection accuracy > 85%
2. **Performance:** Processing speed > 15 FPS
3. **Code Quality:** Test coverage > 70%
4. **UI/UX:** Lighthouse score > 80
5. **Documentation:** Đầy đủ README, GUIDE, API docs

### Tiêu chí chấm điểm (100 điểm):
- **Chức năng (40 điểm):** Đầy đủ features, ít bugs
- **Code quality (20 điểm):** Clean code, tests, comments
- **Performance (15 điểm):** Tốc độ xử lý, optimize
- **UI/UX (15 điểm):** Đẹp, dễ dùng, responsive
- **Documentation (10 điểm):** Báo cáo, hướng dẫn

---

## 📝 QUI TRÌNH LÀM VIỆC

### Daily Standup (15 phút/ngày)
- Hôm qua làm gì?
- Hôm nay làm gì?
- Có vấn đề gì cần support?

### Code Review
- Mỗi PR cần ít nhất 1 người review
- Không merge code chưa test
- Follow coding conventions

### Git Workflow
```bash
# Mỗi người tạo branch riêng
git checkout -b feature/ten-feature

# Commit thường xuyên
git add .
git commit -m "feat: mô tả ngắn gọn"

# Push và tạo PR
git push origin feature/ten-feature
```

### Branch naming:
- `feature/` - tính năng mới
- `fix/` - sửa bug
- `refactor/` - tái cấu trúc code
- `docs/` - documentation

---

## 🛠️ CÔNG CỤ & RESOURCES

### Development:
- **IDE:** VS Code với Python, JavaScript extensions
- **Python:** 3.13+ với virtual environment
- **Node.js:** 18+ cho JS tooling
- **Git:** Version control

### Libraries:
- **AI/ML:** ultralytics (YOLOv8), PyTorch, OpenCV
- **Backend:** Flask, Werkzeug, Pillow
- **Frontend:** Chart.js, Font Awesome

### Testing:
- **Python:** pytest, unittest
- **JavaScript:** Jest (nếu cần)
- **Manual:** Browser DevTools

### Documentation:
- **Markdown:** README, GUIDE
- **API:** Swagger/Postman
- **Diagrams:** draw.io, mermaid

---

## 🚀 HƯỚNG DẪN SETUP

### 1. Clone repository
```bash
git clone <repository-url>
cd HTGTTM
```

### 2. Tạo virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Cài dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Chạy server
```bash
python run_server.py
```

### 5. Mở trình duyệt
```
http://localhost:5000
```

---

## 📞 LIÊN HỆ & SUPPORT

### Họp nhóm:
- **Thời gian:** Mỗi thứ 3, thứ 5 lúc 19:00
- **Địa điểm:** Online/Offline (tùy tình hình)

### Communication:
- **Discord/Zalo:** Chat hàng ngày
- **GitHub Issues:** Track bugs và tasks
- **Google Drive:** Share documents

### Emergency contact:
- **Trưởng nhóm (TN1):** [SĐT/Email]
- **Giảng viên hướng dẫn:** [SĐT/Email]

---

## ✅ CHECKLIST HOÀN THÀNH

### Core Features:
- [x] Upload video và preview
- [x] Zone editor với canvas
- [x] Video processing với YOLOv8
- [x] Violation detection
- [x] Dashboard với stats
- [x] Export PDF/CSV/ZIP
- [x] Dark mode
- [x] Video clips export (5s)

### Advanced Features:
- [ ] Real-time streaming
- [ ] Database integration
- [ ] Authentication
- [ ] Email notifications
- [ ] Mobile app

### Documentation:
- [x] README.md
- [x] GUIDE.md
- [x] PHAN_CONG_NHOM.md
- [ ] API documentation
- [ ] User manual
- [ ] Test report

---

## 🎓 HỌC HỎI & PHÁT TRIỂN

### Mỗi thành viên nên học:
1. **TN1:** Advanced ML/DL techniques, model optimization
2. **TN2:** Computer vision algorithms, image processing
3. **TN3:** RESTful API best practices, database design
4. **TN4:** Modern JavaScript (ES6+), frontend frameworks
5. **TN5:** UI/UX principles, accessibility, testing

### Resources:
- YOLOv8 docs: https://docs.ultralytics.com/
- OpenCV tutorials: https://docs.opencv.org/
- Flask documentation: https://flask.palletsprojects.com/
- MDN Web Docs: https://developer.mozilla.org/

---

**LƯU Ý:** File này là living document, cập nhật thường xuyên theo tiến độ dự án!

**Chúc cả nhóm làm việc hiệu quả! 🚀**
