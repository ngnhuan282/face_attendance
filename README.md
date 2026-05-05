# 🎓 Hệ Thống Điểm Danh Sinh Viên Bằng Nhận Diện Khuôn Mặt

Ứng dụng web Django tích hợp nhận diện khuôn mặt realtime qua webcam, tự động điểm danh sinh viên và thống kê báo cáo chuyên cần.

---

## 📋 Yêu Cầu Hệ Thống

| Thành phần | Phiên bản |
|---|---|
| Python | 3.11.x |
| Django | 4.2.x hoặc 5.x |
| Webcam | Bắt buộc để điểm danh realtime |
| OS | Windows 10/11 (64-bit) |

---

## ⚙️ Hướng Dẫn Cài Đặt

### Bước 1 — Clone project về máy

```bash
git clone https://github.com/<your-username>/face_attendance.git
cd face_attendance
```

### Bước 2 — Cài Python 3.11

> ⚠️ Bắt buộc dùng Python **3.11** — các phiên bản khác (đặc biệt 3.12, 3.13) chưa tương thích với `dlib`.

Tải tại: https://www.python.org/downloads/release/python-3119/
- Chọn **Windows installer (64-bit)**
- Tick ✅ **Add Python 3.11 to PATH** trước khi cài

### Bước 3 — Tạo và kích hoạt virtual environment

```bash
# Tạo venv bằng Python 3.11
py -3.11 -m venv venv

# Kích hoạt (Windows PowerShell)
venv\Scripts\activate

# Kích hoạt (Windows CMD)
venv\Scripts\activate.bat

# Kiểm tra — phải ra 3.11.x
python --version
```

> 💡 Nếu PowerShell báo lỗi untrusted publisher, chạy lệnh sau với quyền Admin:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Bước 4 — Cài dlib (bắt buộc làm trước)

`dlib` không cài được bình thường trên Windows, cần tải file `.whl` có sẵn:

1. Tải file wheel tại link sau:
   ```
   https://github.com/z-mahmud22/Dlib_Windows_Python3.x/blob/main/dlib-19.24.1-cp311-cp311-win_amd64.whl
   ```
   Bấm **Download raw file** (icon tải góc phải màn hình)

2. Cài từ file vừa tải (thay đường dẫn cho đúng):
   ```bash
   pip install C:\Users\<your-name>\Downloads\dlib-19.24.1-cp311-cp311-win_amd64.whl
   ```

3. Kiểm tra:
   ```bash
   python -c "import dlib; print('dlib OK:', dlib.__version__)"
   ```

### Bước 5 — Cài các thư viện còn lại

```bash
pip install -r requirements.txt
```

Kiểm tra face_recognition hoạt động:
```bash
python -c "import face_recognition; print('face_recognition OK!')"
```

### Bước 6 — Tạo file .env

Tạo file `.env` trong thư mục gốc (cùng cấp với `manage.py`):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

> 💡 Tạo SECRET_KEY ngẫu nhiên bằng lệnh:
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### Bước 7 — Tạo cấu trúc thư mục media

```bash
mkdir media
mkdir media\student_photos
mkdir media\encodings
```

### Bước 8 — Khởi tạo database

```bash
python manage.py migrate
```

### Bước 9 — Tạo tài khoản admin

```bash
python manage.py createsuperuser
```

Nhập theo hướng dẫn:
```
Username: admin
Email: admin@example.com
Password: ********
```

### Bước 10 — Chạy server

```bash
python manage.py runserver
```

Mở trình duyệt và truy cập:
- 🌐 Trang chủ: http://127.0.0.1:8000
- 🔧 Trang admin: http://127.0.0.1:8000/admin

---

## 📁 Cấu Trúc Project

```
face_attendance/
├── config/                 # Cấu hình Django (settings, urls)
├── accounts/               # App đăng nhập giảng viên
├── students/               # App quản lý sinh viên
├── attendance/             # App điểm danh realtime
├── reports/                # App báo cáo thống kê
├── recognition/            # Module AI nhận diện khuôn mặt
│   ├── face_detector.py    # Phát hiện khuôn mặt
│   ├── face_encoder.py     # Encode khuôn mặt → vector
│   └── face_matcher.py     # So khớp khuôn mặt
├── templates/              # HTML templates
├── static/                 # CSS, JS, hình ảnh tĩnh
├── media/                  # Ảnh upload (không commit)
│   ├── student_photos/     # Ảnh khuôn mặt sinh viên
│   └── encodings/          # File encodings.pkl
├── .env                    # Biến môi trường (không commit)
├── .gitignore
├── manage.py
└── requirements.txt
```

---

## 🚀 Hướng Dẫn Sử Dụng

### Thêm sinh viên mới
1. Đăng nhập vào hệ thống
2. Vào **Quản lý sinh viên** → **Thêm sinh viên**
3. Nhập thông tin và upload ảnh khuôn mặt rõ nét
4. Hệ thống tự động encode khuôn mặt

### Điểm danh
1. Vào **Điểm danh** → chọn môn học và buổi học
2. Bấm **Bắt đầu điểm danh** — webcam sẽ khởi động
3. Sinh viên đưa khuôn mặt vào camera
4. Bấm **Space** hoặc để hệ thống tự nhận diện
5. Bấm **Kết thúc** khi hoàn tất

### Xem báo cáo
1. Vào **Báo cáo** → chọn lớp / môn / khoảng thời gian
2. Xem tỉ lệ chuyên cần, danh sách vắng mặt
3. Xuất file Excel nếu cần

---

## 🛠️ Thư Viện Sử Dụng

| Thư viện | Mục đích |
|---|---|
| Django | Web framework chính |
| face-recognition | Nhận diện khuôn mặt |
| dlib | Thư viện hỗ trợ face-recognition |
| opencv-python | Xử lý ảnh, bật webcam |
| Pillow | Xử lý ảnh upload |
| openpyxl | Xuất báo cáo Excel |
| python-dotenv | Đọc file .env |

---

## ❗ Lỗi Thường Gặp

**`ModuleNotFoundError: No module named 'django'`**
→ Chưa kích hoạt venv. Chạy `venv\Scripts\activate` trước.

**`Failed building wheel for dlib`**
→ Cài qua file `.whl` theo Bước 4, không cài trực tiếp qua pip.

**`No such file or directory: manage.py`**
→ Tạo project sai cách. Phải có dấu chấm: `django-admin startproject config .`

**Webcam không bật được**
→ Kiểm tra app khác đang dùng webcam, hoặc thử đổi index camera: `cv2.VideoCapture(1)`

---

## 👥 Thành Viên Nhóm

| Họ tên | MSSV | Vai trò |
|---|---|---|
| Nguyễn Văn Nhuận |
| Vũ Hoàng |
| Phạm Minh Hoàng |
| Võ Ngọc Nguyên |

---

## 📄 Giấy Phép

Đồ án môn học — Ngôn ngữ lập trình Python
Trường Đại học Sài Gòn — Khoa Công nghệ Thông tin
