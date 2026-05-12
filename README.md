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
├── config/                 # Cấu hình Django (settings, urls, wsgi)
├── academics/              # Khoa, Ngành, Năm học, Học kỳ
├── accounts/               # Tài khoản, Giảng viên, phân quyền
├── students/               # Sinh viên, Lớp sinh hoạt
├── courses/                # Học phần, Lớp học phần, Đăng ký
├── schedules/              # Phòng học, Lịch học từng buổi
├── attendance/             # Buổi điểm danh, Bản ghi điểm danh
├── notifications/          # Cảnh báo vắng mặt > 20%
├── reports/                # Thống kê, xuất Excel báo cáo
├── recognition/            # Module AI nhận diện khuôn mặt
│   ├── face_detector.py    # Phát hiện khuôn mặt từ frame
│   ├── face_encoder.py     # Encode ảnh SV → vector 128 chiều
│   ├── face_matcher.py     # So khớp khuôn mặt realtime
│   └── utils.py            # Load/save encodings.pkl
├── templates/              # HTML templates (base.html + từng app)
├── static/                 # CSS, JS, hình ảnh tĩnh
├── media/                  # Ảnh upload (không commit lên Git)
│   ├── student_photos/     # Ảnh khuôn mặt sinh viên
│   └── encodings/          # File encodings.pkl
├── .env                    # Biến môi trường (không commit)
├── .gitignore
├── manage.py
└── requirements.txt
```

---

## 🗄️ Cấu Trúc Database

Hệ thống gồm **10 bảng** chia thành 7 app, theo đúng thứ tự phụ thuộc.

### academics — Học thuật cốt lõi

**Faculty** (Khoa)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | Django tự tạo |
| code | CharField(10) | UNIQUE, NOT NULL | Mã khoa — VD: CNTT |
| name | CharField(100) | NOT NULL | Tên khoa |

**Department** (Ngành)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| faculty_id | ForeignKey | FK → Faculty | Thuộc khoa nào |
| code | CharField(10) | UNIQUE | Mã ngành — VD: KTPM |
| name | CharField(100) | NOT NULL | Tên ngành |

**AcademicYear** (Năm học)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| name | CharField(20) | UNIQUE | VD: 2024-2025 |
| start_date | DateField | NOT NULL | Ngày bắt đầu |
| end_date | DateField | NOT NULL | Ngày kết thúc |
| is_active | BooleanField | default=False | Năm học hiện tại |

**Semester** (Học kỳ)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| academic_year_id | ForeignKey | FK → AcademicYear | |
| semester_num | IntegerField | NOT NULL | 1=HK1, 2=HK2, 3=HK Hè |
| start_date | DateField | NOT NULL | |
| end_date | DateField | NOT NULL | |
| is_active | BooleanField | default=False | |
> UNIQUE TOGETHER: (academic_year, semester_num)

---

### accounts — Tài khoản người dùng

**Teacher** (Giảng viên — mở rộng User Django)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| user_id | OneToOneField | FK → User, UNIQUE | 1 tài khoản = 1 GV |
| department_id | ForeignKey | FK → Department | Giảng dạy ngành nào |
| teacher_id | CharField(20) | UNIQUE | Mã giảng viên |
| phone | CharField(15) | blank=True | |
| avatar | ImageField | null=True | Ảnh đại diện |

---

### students — Sinh viên

**StudentClass** (Lớp sinh hoạt)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| department_id | ForeignKey | FK → Department | Thuộc ngành nào |
| class_code | CharField(20) | UNIQUE | VD: DHKTPM17A |
| class_name | CharField(50) | NOT NULL | Tên lớp |
| intake_year | IntegerField | NOT NULL | Năm nhập học |

**Student** (Sinh viên)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| student_class_id | ForeignKey | FK → StudentClass | Lớp sinh hoạt |
| student_id | CharField(20) | UNIQUE | MSSV |
| full_name | CharField(100) | NOT NULL | Họ tên đầy đủ |
| date_of_birth | DateField | null=True | Ngày sinh |
| email | EmailField | blank=True | |
| phone | CharField(15) | blank=True | |
| photo | ImageField | null=True | **Ảnh khuôn mặt để encode** |
| is_active | BooleanField | default=True | Đang học hay đã nghỉ |
| created_at | DateTimeField | auto_now_add | Ngày tạo hồ sơ |

---

### courses — Học phần & Lớp học phần

**Course** (Học phần / Môn học)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| department_id | ForeignKey | FK → Department | |
| course_code | CharField(20) | UNIQUE | VD: DHKTPM001 |
| course_name | CharField(200) | NOT NULL | Tên học phần |
| credits | IntegerField | default=3 | Số tín chỉ |
| description | TextField | blank=True | |

**CourseClass** (Lớp học phần)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| course_id | ForeignKey | FK → Course | |
| semester_id | ForeignKey | FK → Semester | |
| teacher_id | ForeignKey | FK → Teacher | Giảng viên phụ trách |
| class_code | CharField(30) | NOT NULL | VD: DHKTPM17A_HP1 |
| max_students | IntegerField | default=40 | Sĩ số tối đa |
| total_sessions | IntegerField | default=15 | Tổng số buổi học |
> UNIQUE TOGETHER: (course, semester, class_code)

**Enrollment** (Đăng ký học phần)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| course_class_id | ForeignKey | FK → CourseClass | |
| student_id | ForeignKey | FK → Student | |
| enrolled_at | DateTimeField | auto_now_add | Ngày đăng ký |
| is_active | BooleanField | default=True | Còn học hay đã hủy |
> UNIQUE TOGETHER: (course_class, student)

---

### schedules — Lịch học

**Room** (Phòng học)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| room_code | CharField(20) | UNIQUE | VD: A101 |
| building | CharField(50) | blank=True | Tòa nhà |
| capacity | IntegerField | default=40 | Sức chứa |
| has_camera | BooleanField | default=False | Có camera điểm danh |

**Schedule** (Lịch học từng buổi)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| course_class_id | ForeignKey | FK → CourseClass | |
| room_id | ForeignKey | FK → Room, null=True | |
| day_of_week | IntegerField | NOT NULL | 2=Thứ 2 ... 8=CN |
| start_period | IntegerField | NOT NULL | Tiết bắt đầu (1-15) |
| end_period | IntegerField | NOT NULL | Tiết kết thúc (1-15) |
| date | DateField | NOT NULL | Ngày học cụ thể |
| session_number | IntegerField | NOT NULL | Buổi thứ mấy (1-15) |
> UNIQUE TOGETHER: (course_class, date)

---

### attendance — Điểm danh

**AttendanceSession** (Buổi điểm danh)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| course_class_id | ForeignKey | FK → CourseClass | |
| schedule_id | OneToOneField | FK → Schedule, null=True | |
| created_by_id | ForeignKey | FK → User | GV tạo buổi này |
| started_at | DateTimeField | auto_now_add | Bắt đầu lúc mấy giờ |
| ended_at | DateTimeField | null=True | Kết thúc lúc mấy giờ |
| status | CharField(10) | default=open | open / closed |
| note | TextField | blank=True | |

**AttendanceRecord** (Bản ghi điểm danh từng SV)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| session_id | ForeignKey | FK → AttendanceSession | |
| student_id | ForeignKey | FK → Student | |
| status | CharField(10) | default=absent | present / absent / late |
| method | CharField(10) | default=face | face / manual |
| confidence | FloatField | default=0.0 | Độ chính xác 0.0 → 1.0 |
| timestamp | DateTimeField | null=True | Thời điểm nhận diện |
| note | CharField(200) | blank=True | |
> UNIQUE TOGETHER: (session, student) — mỗi SV chỉ 1 bản ghi / buổi

---

### notifications — Cảnh báo

**Notification** (Cảnh báo vắng mặt)
| Field | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | AutoField | PK | |
| student_id | ForeignKey | FK → Student | |
| course_class_id | ForeignKey | FK → CourseClass | |
| noti_type | CharField(20) | NOT NULL | absent_warning / absent_danger |
| absent_count | IntegerField | NOT NULL | Số buổi vắng |
| total_sessions | IntegerField | NOT NULL | Tổng số buổi đã học |
| absent_percent | FloatField | NOT NULL | Tỉ lệ vắng (%) |
| is_read | BooleanField | default=False | GV đã đọc chưa |
| created_at | DateTimeField | auto_now_add | |

---

### Quan hệ giữa các bảng

| Quan hệ | Loại | Ghi chú |
|---|---|---|
| Faculty → Department | 1-N | 1 khoa có nhiều ngành |
| AcademicYear → Semester | 1-N | 1 năm học tối đa 3 học kỳ |
| Department → StudentClass | 1-N | 1 ngành có nhiều lớp sinh hoạt |
| StudentClass → Student | 1-N | 1 lớp có nhiều sinh viên |
| User → Teacher | 1-1 | 1 tài khoản = 1 giảng viên |
| Course → CourseClass | 1-N | 1 học phần mở nhiều lớp / học kỳ |
| CourseClass ↔ Student | N-N | Qua bảng Enrollment |
| CourseClass → Schedule | 1-N | 1 lớp HP có tối đa 15 buổi lịch |
| Schedule → AttendanceSession | 1-1 | 1 buổi lịch = 1 buổi điểm danh |
| AttendanceSession → AttendanceRecord | 1-N | Mỗi SV 1 bản ghi / buổi |

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

| Họ tên |</br>
|---|---|---| </br>
Nguyễn Văn Nhuận </br>
Vũ Hoàng </br>
Phạm Minh Hoàng </br>
Võ Ngọc Nguyên </br>

---

## 📄 Giấy Phép

Đồ án môn học — Ngôn ngữ lập trình Python </br>
Trường Đại học Sài Gòn — Khoa Công nghệ Thông tin
