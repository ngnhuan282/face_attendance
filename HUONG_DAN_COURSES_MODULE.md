# Hướng Dẫn Sử Dụng Module Quản Lý Học Phần (Courses)

## Tổng Quan
Module Courses cung cấp các tính năng quản lý học phần, lớp học phần, và đăng ký sinh viên cho hệ thống Điểm Danh EduFace.

## Các Tính Năng Chính

### 1. Quản Lý Học Phần (Courses)
**Đường dẫn:** `/courses/`

#### Danh Sách Học Phần
- Hiển thị tất cả học phần trong hệ thống
- Tìm kiếm theo mã hoặc tên học phần
- Phân trang 10 mục/trang
- Hiển thị: Mã, Tên, Ngành, Tín chỉ, Số lớp

**Hành động:**
- **Chỉnh sửa:** Sửa tên, tín chỉ, mô tả (mã không được thay đổi)
- **Xóa:** Xóa học phần (chỉ khi không có lớp nào)

#### Tạo Học Phần Mới
**Đường dẫn:** `/courses/create/`

Nhập các thông tin:
- **Ngành** (bắt buộc): Chọn từ danh sách ngành có sẵn
- **Mã Học Phần** (bắt buộc): Ví dụ INT101, PYTHON101 (duy nhất)
- **Tên Học Phần** (bắt buộc): Ví dụ "Lập Trình Python"
- **Tín Chỉ**: Mặc định 3 tín chỉ
- **Mô Tả**: Thông tin thêm về học phần

### 2. Quản Lý Lớp Học Phần (Course Classes)
**Đường dẫn:** `/courses/classes/`

#### Danh Sách Lớp Học Phần
- Hiển thị tất cả lớp học phần
- Tìm kiếm theo mã lớp hoặc tên học phần
- Lọc theo học kỳ
- Hiển thị: Mã lớp, Học phần, Học kỳ, Giảng viên, Sĩ số, Sĩ số tối đa

**Hành động:**
- **Xem chi tiết:** Xem danh sách sinh viên đã đăng ký
- **Chỉnh sửa:** Thay đổi giảng viên, sĩ số, số buổi
- **Xóa:** Xóa lớp (chỉ khi không có sinh viên nào)

#### Tạo Lớp Học Phần Mới
**Đường dẫn:** `/courses/classes/create/`

Nhập các thông tin:
- **Học Phần** (bắt buộc): Chọn từ danh sách
- **Học Kỳ** (bắt buộc): Chọn học kỳ
- **Giảng Viên** (bắt buộc): Chọn giảng viên
- **Mã Lớp** (bắt buộc): Ví dụ INT101.01, INT101.02 (duy nhất trong mỗi học kỳ)
- **Sĩ Số Tối Đa**: Mặc định 40 sinh viên
- **Tổng Số Buổi**: Mặc định 15 buổi

#### Chi Tiết Lớp Học Phần
**Đường dẫn:** `/courses/classes/<id>/`

Hiển thị:
- Thông tin lớp: Mã, Tên học phần, Học kỳ, Tín chỉ, Giảng viên, Số buổi
- Danh sách sinh viên đã đăng ký với các cột:
  - Mã sinh viên
  - Họ tên
  - Lớp sinh hoạt
  - Ngành
  - Ngày đăng ký
  - Trạng thái
  - Hành động (xóa)

**Công cụ:**
- Tìm kiếm sinh viên
- Import CSV để thêm nhiều sinh viên cùng lúc

### 3. Quản Lý Đăng Ký Học Phần (Enrollment)
**Đường dẫn:** `/courses/classes/<id>/enrollments/`

#### Danh Sách Đăng Ký
Hiển thị tất cả sinh viên đã đăng ký lớp học phần với:
- Thông tin chi tiết sinh viên (MSSV, họ tên, lớp, ngành, email)
- Ngày đăng ký
- Trạng thái (Đang học / Nghỉ học)
- Nút xóa sinh viên khỏi lớp

#### Thêm Sinh Viên Thủ Công
Có thể thêm sinh viên lần lượt thông qua form (nếu cung cấp)

**Kiểm tra tự động:**
- Sinh viên tồn tại
- Sinh viên chưa đăng ký lớp này
- Lớp vẫn còn chỗ trống

#### Import Danh Sách Từ CSV
**Đường dẫn:** `/courses/classes/<id>/enrollments/import/`

**Định dạng file CSV:**
```
student_code
SV220001
SV220002
SV220003
```

**Hướng dẫn:**
1. Download template CSV từ trang import
2. Mở file bằng Excel hoặc text editor
3. Nhập mã sinh viên (MSSV) trên mỗi dòng
4. Lưu file với định dạng CSV (Comma-Separated Values)
5. Upload file lên hệ thống

**Kiểm tra trong quá trình import:**
- Kiểm tra mã sinh viên có tồn tại không
- Kiểm tra sinh viên chưa đăng ký lớp này
- Kiểm tra lớp còn chỗ trống không
- Báo lỗi chi tiết cho từng dòng

**Kết quả:**
Hiển thị số sinh viên import thành công và danh sách lỗi (nếu có)

## Quy Tắc Kinh Doanh

### Ràng Buộc Dữ Liệu
- **Mã học phần:** Duy nhất toàn bộ hệ thống
- **Mã lớp:** Duy nhất trong mỗi học phần + học kỳ
- **Đăng ký sinh viên:** Mỗi sinh viên chỉ được đăng ký 1 lần/lớp

### Điều Kiện Xóa
- **Học phần:** Chỉ xóa được nếu không có lớp nào
- **Lớp:** Chỉ xóa được nếu không có sinh viên nào
- **Sinh viên:** Có thể xóa khỏi lớp bất cứ lúc nào

### Kiểm Soát Truy Cập
- **Admin:** Có toàn bộ quyền (tạo, sửa, xóa)
- **Giảng Viên:** Chỉ xem danh sách, không được chỉnh sửa

## Giao Diện

### Thiết Kế
- Tuân thủ thiết kế admin_base.html
- Sidebar xanh lá cây (EduFace theme)
- Stat cards hiển thị dữ liệu tổng hợp
- Bảng dữ liệu với action buttons

### Thanh Công Cụ
- **Tìm kiếm:** Theo mã hoặc tên
- **Lọc:** Theo học kỳ, ngành, v.v.
- **Nút Thêm:** Để tạo mới
- **Phân Trang:** 10-15 mục/trang

## Báo Lỗi Thường Gặp

| Lỗi | Nguyên Nhân | Giải Pháp |
|-----|-----------|---------|
| "Mã học phần đã tồn tại" | Mã học phần bị trùng | Kiểm tra lại mã, sử dụng mã khác |
| "Lớp đã đầy" | Sĩ số vượt quá max_students | Tăng sĩ số tối đa hoặc tạo lớp mới |
| "Sinh viên đã đăng ký" | Sinh viên bị trùng đăng ký | Xóa đăng ký cũ rồi thêm lại |
| Lỗi import CSV | File không đúng format | Đảm bảo file CSV có cột "student_code" |

## Câu Hỏi Thường Gặp

**Q: Tôi có thể sửa mã học phần không?**
A: Không, mã học phần là duy nhất và không thể thay đổi sau khi tạo.

**Q: Làm sao xóa lớp mà còn sinh viên?**
A: Phải xóa hết sinh viên khỏi lớp trước, rồi mới xóa được lớp.

**Q: Có thể import CSV với các cột bổ sung không?**
A: Có, nhưng hệ thống chỉ đọc cột "student_code". Các cột khác sẽ bị bỏ qua.

**Q: Format ngày tháng trong import CSV?**
A: Không cần ngày tháng, chỉ cần mã sinh viên (student_code).
