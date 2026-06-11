# 📘 Hướng dẫn chạy script `populate_sgu_data`

Script này sẽ tự động tạo toàn bộ dữ liệu mẫu cho hệ thống điểm danh SGU,
bao gồm: năm học, học kỳ, khoa, ngành, giáo viên, phòng học, lớp sinh viên,
sinh viên, học phần, lớp học phần và đăng ký học phần.

---

## ⚠️ Lưu ý quan trọng trước khi chạy

> Script sẽ **XÓA TOÀN BỘ DỮ LIỆU CŨ** trong database trước khi tạo mới.
> Hãy chắc chắn bạn đã backup nếu cần.

---

## 📋 Yêu cầu

- Python 3.10+
- Virtual environment đã được tạo (`venv/`)
- Database đã được migrate
- Hai file dữ liệu nguồn nằm trong **thư mục gốc** project (`D:\Python Projects\face_attendance\`):
  - `dkmh_all_lines.txt` — dữ liệu đăng ký môn học
  - `dssv.xlsx` — danh sách sinh viên

---

## 🚀 Các bước thực hiện

### Bước 1 — Kích hoạt Virtual Environment

Mở terminal tại thư mục gốc project và chạy:

```powershell
venv\Scripts\activate
```

Sau khi thành công, dòng lệnh sẽ hiện:
```
(venv) PS D:\Python Projects\face_attendance>
```

---

### Bước 2 — Cài `django-extensions` vào venv

> ⚠️ Phải dùng `venv\Scripts\pip` để cài đúng vào venv, không phải `pip` hệ thống.

```powershell
venv\Scripts\pip install django-extensions
```

---

### Bước 3 — Thêm `django_extensions` vào `INSTALLED_APPS`

Mở file `config/settings.py`, tìm danh sách `INSTALLED_APPS` và thêm dòng sau vào cuối:

```python
INSTALLED_APPS = [
    ...
    'reports',
    'django_extensions',   # ← thêm dòng này
]
```

---

### Bước 4 — Chạy migrate (nếu chưa chạy)

```powershell
python manage.py migrate
```

---

### Bước 5 — Chạy script populate

```powershell
python manage.py runscript populate_sgu_data
```

Quá trình chạy sẽ in ra log từng bước, ví dụ:

```
Starting database population script with Saigon University (SGU) data...
Clearing existing database records in correct order...
Existing data cleared.
Creating admin account...
Admin account created: admin / admin123
Generating Academic Years and Semesters...
Created 3 Academic Years.
Created 6 Semesters.
...
Database population completed successfully!
```

---

## ✅ Kết quả sau khi chạy

| Dữ liệu | Thông tin |
|---|---|
| Tài khoản Admin | `admin` / `admin123` |
| Tài khoản Giáo viên | `gv_01` → `gv_35` / password: `123456` |
| Năm học | Từ **2023-2024** đến năm hiện tại |
| Số ngành | **38 ngành** chính thức của SGU |
| Số khoa | **12 khoa** |

---

## ❓ Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách fix |
|---|---|---|
| `No module named 'django'` | Chưa kích hoạt venv | Chạy `venv\Scripts\activate` |
| `Unknown command: 'runscript'` | Chưa cài `django-extensions` hoặc chưa thêm vào `INSTALLED_APPS` | Làm Bước 2 và Bước 3 |
| `No module named 'django_extensions'` | Cài nhầm vào Python hệ thống | Dùng `venv\Scripts\pip install django-extensions` |
| `FileNotFoundError: dkmh_all_lines.txt` | File không nằm đúng thư mục | Đặt file vào thư mục gốc project |
| `FileNotFoundError: dssv.xlsx` | File không nằm đúng thư mục | Đặt file vào thư mục gốc project |
