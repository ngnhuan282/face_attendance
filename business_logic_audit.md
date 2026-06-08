# Báo Cáo Kiểm Tra Logic Nghiệp Vụ - Hệ Thống Điểm Danh EduFace

Bản báo cáo này tổng hợp kết quả phân tích, đánh giá toàn bộ logic nghiệp vụ (business logic) của các module trong hệ thống **EduFace** (Điểm danh sinh viên bằng nhận diện khuôn mặt). Qua quá trình kiểm tra mã nguồn từ các file models, views, signals và services, chúng tôi đã phát hiện một số lỗ hổng logic nghiệp vụ và các nút thắt cổ chai về mặt hiệu năng.

---

## 1. Chi Tiết Đánh Giá Theo Từng Module

### 1.1. Module Học Thuật Cốt Lõi (`academics`)
* **Chức năng:** Quản lý Khoa (`Faculty`), Ngành (`Department`), Năm học (`AcademicYear`), và Học kỳ (`Semester`).
* **Quy tắc nghiệp vụ:**
  - Một `Semester` thuộc về một `AcademicYear`.
  - Có ràng buộc duy nhất (Unique) đối với tổ hợp `(academic_year, semester_num)`.
* **Vấn đề phát hiện:**
  - **Thiếu logic đồng bộ trạng thái kích hoạt:** Trường `is_active` trên `AcademicYear` và `Semester` có thể được bật `True` đồng thời cho nhiều bản ghi thông qua trang Admin mà không có kiểm tra hay tự động vô hiệu hóa các học kỳ/năm học cũ. Điều này dẫn đến sự không đồng nhất khi truy vấn học kỳ hiện tại (các hàm lấy `.filter(is_active=True).first()` sẽ trả về không nhất quán tùy thuộc vào thứ tự sắp xếp của cơ sở dữ liệu).

### 1.2. Module Quản Lý Tài Khoản (`accounts`)
* **Chức năng:** Đăng nhập, phân quyền Admin/Giảng viên và quản lý hồ sơ Giảng viên (`Teacher`).
* **Quy tắc nghiệp vụ:**
  - Sử dụng Django Groups (`Admin`, `Giảng viên`) kết hợp Middleware để phân quyền.
  - Giảng viên chỉ được xem các lớp học phần và danh sách sinh viên thuộc lớp mình dạy.
* **Vấn đề phát hiện:**
  - **Lỗi chuyển đổi Role (Role Transition Cascade Error):** Khi chỉnh sửa tài khoản (`account_edit`) chuyển vai trò từ Giảng viên sang Admin, hệ thống sẽ xóa hồ sơ `Teacher` tương ứng (`Teacher.objects.filter(user=user).delete()`). Tuy nhiên, do `CourseClass.teacher` sử dụng `on_delete=models.PROTECT`, nếu giảng viên đó đang được phân công dạy bất kỳ lớp học phần nào, việc xóa này sẽ kích hoạt ngoại lệ `ProtectedError` từ cơ sở dữ liệu. Mặc dù ngoại lệ được bắt và hiển thị lỗi trên form, giao diện người dùng chưa cảnh báo trước cho Admin về các lớp học phần bị ảnh hưởng.

### 1.3. Module Quản Lý Sinh Viên (`students`)
* **Chức năng:** Quản lý Hồ sơ sinh viên (`Student`) và Lớp sinh hoạt (`StudentClass`).
* **Quy tắc nghiệp vụ:**
  - Sinh viên thuộc về một lớp sinh hoạt (có thể để trống). MSSV (`student_id`) phải là duy nhất.
  - Lớp sinh hoạt chỉ được xóa khi không còn sinh viên nào thuộc lớp đó.
  - Hỗ trợ Import hàng loạt sinh viên từ file CSV.
* **Vấn đề phát hiện:**
  - **Lỗi Transaction Poisoning trong Import CSV (Nghiêm Trọng):** Xem chi tiết tại Mục 2.1.
  - **Logic xóa sinh viên khỏi lớp sinh hoạt:** Khi xóa sinh viên khỏi lớp sinh hoạt (`studentclass_remove_student`), hệ thống đặt `student_class = None` mà không xóa sinh viên khỏi hệ thống. Đây là thiết kế hợp lý, tuy nhiên cần làm rõ xem sinh viên không có lớp sinh hoạt có được phép tham gia điểm danh hay không (hiện tại hệ thống vẫn cho phép).

### 1.4. Module Quản Lý Học Phần & Đăng Ký (`courses`)
* **Chức năng:** Quản lý Học phần (`Course`), Lớp học phần (`CourseClass`), và Đăng ký học phần (`Enrollment`).
* **Quy tắc nghiệp vụ:**
  - Học phần chỉ được xóa nếu không có lớp học phần nào hoạt động và không có đăng ký nào.
  - Lớp học phần chỉ được xóa khi chưa có sinh viên đăng ký.
  - Ràng buộc sĩ số tối đa (`max_students`): Khi đăng ký thủ công hoặc import, hệ thống phải kiểm tra sĩ số hiện tại.
* **Vấn đề phát hiện:**
  - **Lỗi Transaction Poisoning khi Import Đăng ký (Nghiêm Trọng):** Tương tự như bên sinh viên, import CSV đăng ký lớp học phần cũng bị lỗi quản lý giao dịch cơ sở dữ liệu.
  - **Race Condition khi kiểm tra Sĩ số tối đa:** Khi hai yêu cầu đăng ký cho cùng một lớp học phần xảy ra đồng thời khi lớp chỉ còn 1 chỗ trống, cả hai yêu cầu đều đọc `current_count < max_students` và thực hiện ghi đè vượt quá giới hạn sĩ số.

### 1.5. Module Lịch Học & Phòng Học (`schedules`)
* **Chức năng:** Quản lý Lịch học theo buổi (`Schedule`) và Phòng học (`Room`).
* **Quy tắc nghiệp vụ:**
  - Tự động tạo lịch học hàng loạt theo tuần (`schedule_create_bulk`).
  - Kiểm tra trùng lịch: Trùng phòng học hoặc trùng buổi học của lớp học phần trên cùng một ngày.
* **Vấn đề phát hiện:**
  - **Trùng lịch Giảng viên (Lỗ hổng nghiệp vụ):** Xem chi tiết tại Mục 2.4. Hệ thống hiện tại hoàn toàn bỏ qua việc kiểm tra xem Giảng viên phụ trách lớp học phần đó có bị trùng lịch dạy ở một lớp học phần khác tại cùng thời điểm hay không.

### 1.6. Module Điểm Danh Realtime (`attendance`)
* **Chức năng:** Tạo buổi điểm danh (`AttendanceSession`), nhận diện khuôn mặt qua camera và ghi nhận kết quả điểm danh (`AttendanceRecord`).
* **Quy tắc nghiệp vụ:**
  - Điểm danh tự động qua webcam / hình ảnh tải lên hoặc chỉnh sửa thủ công bởi giảng viên.
  - Độ chính xác được tính dựa trên khoảng cách vector khuôn mặt (face distance).
* **Vấn đề phát hiện:**
  - **Logic ghi đè trạng thái điểm danh thủ công:** Nếu giảng viên đã đánh dấu một sinh viên là "Đi trễ" (late) hoặc "Vắng" (absent) một cách thủ công, khi webcam quét qua khuôn mặt sinh viên đó, hệ thống sẽ tự động cập nhật trạng thái thành "Có mặt" (present) thông qua hàm `_record_face_attendance`. Điều này làm mất hiệu lực đánh giá thủ công của giảng viên (ví dụ sinh viên đi trễ quá giờ nhưng sau đó vẫn được camera nhận diện là đi học bình thường).

### 1.7. Module Cảnh Báo & Báo Cáo (`notifications` & `reports`)
* **Chức năng:** Pre-compute thống kê chuyên cần (`AttendanceReport`), gửi thông báo (`Notification`) khi tỉ lệ vắng vượt mức (cảnh báo > 20%, nguy hiểm > 40%).
* **Quy tắc nghiệp vụ:**
  - Báo cáo chuyên cần được tự động cập nhật sau khi buổi điểm danh kết thúc thông qua Django signals.
  - Cảnh báo được tự động tạo hoặc xóa dựa trên kết quả tính toán lại tỉ lệ vắng.
* **Vấn đề phát hiện:**
  - **Lỗi tính sai tỉ lệ chuyên cần cho Sinh viên đăng ký muộn (Nghiêm Trọng):** Xem chi tiết tại Mục 2.2.

---

## 2. Các Lỗi Nghiệp Vụ & Hiệu Năng Nghiêm Trọng

### 2.1. Lỗi Transaction Poisoning trong các chức năng Import CSV
* **Vị trí xảy ra:**
  - `student_import_csv` trong [students/views.py](file:///d:/Python%20Projects/face_attendance/students/views.py#L476-L539)
  - `enrollment_import` trong [courses/views.py](file:///d:/Python%20Projects/face_attendance/courses/views.py#L598-L631)
  - `enrollment_import_all` trong [courses/views.py](file:///d:/Python%20Projects/face_attendance/courses/views.py#L710-L751)
* **Mô tả chi tiết:**
  Đoạn mã xử lý import CSV được bọc trong một khối `with transaction.atomic():`. Bên trong vòng lặp đọc từng dòng CSV, hệ thống có một khối `try-except` bao quanh lệnh `.create()` để ghi lại lỗi của từng dòng và tiếp tục xử lý dòng tiếp theo:
  ```python
  with transaction.atomic():
      for row_num, row in enumerate(reader, start=2):
          try:
              Student.objects.create(...)
          except Exception as e:
              errors.append(...) # Ghi nhận lỗi nhưng không raise exception để rollback
  ```
  Trong Django, khi một khối `atomic()` gặp lỗi cơ sở dữ liệu (ví dụ: lỗi trùng khóa ngoại, giá trị null, hoặc độ dài vượt mức), transaction của cơ sở dữ liệu đó sẽ bị đánh dấu là **đã hỏng (rollback-only)**. Việc cố gắng thực hiện bất kỳ câu lệnh truy vấn nào khác (ở các vòng lặp tiếp theo như `.filter()` hay `.create()`) trong cùng khối đó sẽ ném ra ngoại lệ `TransactionManagementError` ("An error occurred in the current transaction. You can't execute queries until the end of the transaction block.").
  Điều này khiến toàn bộ các dòng CSV phía sau dòng bị lỗi đầu tiên đều bị thất bại hàng loạt, thay vì bỏ qua dòng lỗi và import tiếp các dòng hợp lệ như mong đợi của giao diện.
* **Giải pháp khắc phục:**
  Sử dụng các điểm lưu phụ (savepoint) bằng cách bọc từng lệnh ghi của mỗi dòng trong một khối `transaction.atomic()` lồng nhau:
  ```python
  with transaction.atomic():
      for row_num, row in enumerate(reader, start=2):
          try:
              with transaction.atomic():  # Tạo savepoint lồng nhau
                  Student.objects.create(...)
          except Exception as e:
              errors.append(...)
  ```

### 2.2. Lỗi logic tính tỉ lệ chuyên cần cho Sinh viên đăng ký muộn
* **Vị trí xảy ra:**
  - Hàm `compute_attendance_rate` trong [reports/services.py](file:///d:/Python%20Projects/face_attendance/reports/services.py#L22-L65)
* **Mô tả chi tiết:**
  Tỉ lệ chuyên cần và số buổi vắng của sinh viên được tính như sau:
  ```python
  closed_sessions = AttendanceSession.objects.filter(course_class=course_class, status='closed')
  total_sessions = closed_sessions.count()
  absent_count = total_sessions - present_count - late_count
  ```
  Nếu một sinh viên đăng ký vào lớp học phần trễ (ví dụ: lớp học từ tuần 1, nhưng sinh viên được thêm vào ở tuần 3 thông qua phòng đào tạo), hệ thống vẫn lấy tổng số buổi đã học của lớp (`total_sessions` bao gồm cả các buổi ở tuần 1 và tuần 2) để tính toán. Do sinh viên không có bản ghi điểm danh ở tuần 1 và 2, hệ thống tự động coi sinh viên đó **vắng mặt** các buổi này. Điều này làm tỉ lệ chuyên cần của sinh viên bị sụt giảm nghiêm trọng ngay khi vừa vào lớp và kích hoạt cảnh báo vắng sai thực tế.
* **Giải pháp khắc phục:**
  Chỉ tính điểm danh cho các buổi học diễn ra **sau hoặc cùng ngày** với thời điểm sinh viên đăng ký học phần (`enrolled_at`). Cụ thể, truy vấn các buổi học cần lọc thêm điều kiện ngày học phải lớn hơn hoặc bằng ngày đăng ký:
  ```python
  enrollment = Enrollment.objects.filter(student=student, course_class=course_class).first()
  if enrollment:
      closed_sessions = AttendanceSession.objects.filter(
          course_class=course_class,
          status='closed',
          started_at__date__gte=enrollment.enrolled_at.date() # Chỉ tính từ lúc đăng ký
      )
  ```

### 2.3. Nút thắt cổ chai hiệu năng khi cập nhật Vector nhận diện khuôn mặt
* **Vị trí xảy ra:**
  - Signal `rebuild_face_encodings` trong [students/signals.py](file:///d:/Python%20Projects/face_attendance/students/signals.py#L40-L65)
* **Mô tả chi tiết:**
  Mỗi khi thêm một sinh viên mới hoặc cập nhật ảnh khuôn mặt, hệ thống kích hoạt signal `rebuild_face_encodings` gọi đến hàm `encode_students()`.
  Hàm `encode_students()` thực hiện truy vấn **toàn bộ** sinh viên đang hoạt động trong cơ sở dữ liệu có ảnh khuôn mặt, tải từng ảnh lên, chạy qua mô hình HOG để tìm kiếm và mã hóa khuôn mặt, sau đó ghi đè lại file `encodings.pkl`.
  Do quá trình chạy mô hình AI (face_recognition / dlib) rất tốn CPU và diễn ra **đồng bộ (synchronous)** trong luồng xử lý HTTP request của Django, khi số lượng sinh viên tăng lên (chỉ cần khoảng > 50 sinh viên), HTTP request thêm sinh viên mới sẽ bị treo (timeout), gây tê liệt giao diện Admin hoặc trang Import CSV.
* **Giải pháp khắc phục:**
  1. **Tách biệt xử lý bất đồng bộ (Asynchronous Task):** Đẩy việc rebuild/update vector nhận diện vào hàng đợi công việc nền (Background Tasks / Celery / ThreadPool).
  2. **Cập nhật lũy tiến (Incremental Update):** Thay vì encode lại toàn bộ cơ sở dữ liệu, chỉ cần tải file `encodings.pkl` hiện tại lên, encode riêng sinh viên mới/sửa đổi rồi cập nhật hoặc chèn thêm vector của sinh viên đó vào file pickle hiện tại.

### 2.4. Thiếu kiểm tra trùng lịch dạy của Giảng viên
* **Vị trí xảy ra:**
  - Hàm `schedule_create_bulk` trong [schedules/views.py](file:///d:/Python%20Projects/face_attendance/schedules/views.py#L165-L250)
* **Mô tả chi tiết:**
  Khi tạo lịch học hàng loạt hoặc chỉnh sửa lịch học, hệ thống thực hiện kiểm tra trùng lịch phòng học (`room`) và trùng lịch của chính lớp học phần đó. Tuy nhiên, hệ thống **không** kiểm tra xem giảng viên phụ trách lớp học phần đó có đang bận giảng dạy một lớp học phần khác tại cùng thời điểm hay không:
  ```python
  # Thiếu kiểm tra lịch giảng viên trùng
  overlapping_teacher = Schedule.objects.filter(
      course_class__teacher=course_class.teacher,
      date=d,
      start_period__lte=end_period,
      end_period__gte=start_period
  ).first()
  ```
  Lỗ hổng này dẫn đến trường hợp một giảng viên bị xếp lịch dạy hai lớp học phần ở hai phòng khác nhau trong cùng một tiết học.
* **Giải pháp khắc phục:**
  Bổ sung thêm bước kiểm tra trùng lịch của giảng viên trong hàm `schedule_create_bulk` và `schedule_edit` tương tự như cách kiểm tra trùng phòng học.

---

## 3. Tổng Kết và Khuyến Nghị Cải Tiến

Hệ thống **EduFace** đã xây dựng một nền tảng quản lý học phần, lịch học và điểm danh bằng khuôn mặt khá tốt và có tính thực tiễn cao. Tuy nhiên, để hệ thống hoạt động ổn định và sẵn sàng đưa vào sử dụng thực tế (Production), nhóm phát triển cần ưu tiên giải quyết các vấn đề sau:

1. **Khắc phục ngay lỗi giao dịch (Transaction Poisoning)** trong các tác vụ Import CSV để đảm bảo tính năng import hoạt động ổn định.
2. **Cải tiến thuật toán tính tỉ lệ chuyên cần** bằng cách giới hạn theo ngày sinh viên bắt đầu đăng ký lớp để bảo vệ quyền lợi của sinh viên nhập học muộn.
3. **Chuyển tác vụ xử lý mã hóa khuôn mặt (Face Encoding) sang chạy nền** để tránh lỗi nghẽn/timeout hệ thống.
4. **Bổ sung ràng buộc trùng lịch dạy của Giảng viên** trong module quản lý lịch học.
5. **Cập nhật logic điểm danh camera** để tránh việc camera tự động ghi đè trạng thái "Có mặt" lên các trạng thái đặc biệt đã được giảng viên phê duyệt thủ công (như vắng có phép, hoặc đi trễ).
