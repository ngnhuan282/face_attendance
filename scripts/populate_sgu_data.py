import os
import re
import sys
import random
import datetime
import pandas as pd
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password

# Import Django models
from academics.models import Faculty, Department, AcademicYear, Semester
from accounts.models import Teacher
from students.models import StudentClass, Student
from schedules.models import Room, Schedule
from courses.models import Course, CourseClass, Enrollment

def run():
    print("Starting database population script with Saigon University (SGU) data...")

    # -------------------------------------------------------------
    # 1. CLEAN EXISTING DATA
    # -------------------------------------------------------------
    print("Clearing existing database records in correct order...")
    from accounts.models import RolePermission
    RolePermission.objects.all().delete()
    Enrollment.objects.all().delete()
    CourseClass.objects.all().delete()
    Course.objects.all().delete()
    # Clear students and their User accounts
    User.objects.filter(student__isnull=False).delete()   # users linked to a Student
    # Also delete orphaned student users (MSSV = all-digit username) left from a previous crashed run
    User.objects.filter(
        username__regex=r'^\d+$', is_superuser=False, is_staff=False
    ).delete()
    Student.objects.all().delete()
    StudentClass.objects.all().delete()

    # Clear teachers and their User accounts (GV-prefixed usernames or linked to Teacher)
    User.objects.filter(teacher__isnull=False).delete()
    User.objects.filter(username__startswith='gv_').delete()
    Teacher.objects.all().delete()

    Department.objects.all().delete()
    Faculty.objects.all().delete()
    Room.objects.all().delete()
    Schedule.objects.all().delete()
    Semester.objects.all().delete()
    AcademicYear.objects.all().delete()
    print("Existing data cleared.")

    # -------------------------------------------------------------
    # 2. INIT ROLE PERMISSIONS
    # -------------------------------------------------------------
    print("Initializing Role Permissions...")
    from accounts.models import RolePermission
    from accounts.middleware import _DEFAULT_PERMS

    for role_name, perms in _DEFAULT_PERMS.items():
        RolePermission.objects.create(role=role_name, permissions=perms)
    print("Role permissions initialized.")

    # -------------------------------------------------------------
    # 3. CREATE / ENSURE ADMIN ACCOUNT
    # -------------------------------------------------------------
    print("Creating admin account...")
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@sgu.edu.vn',
            password='admin123',
            first_name='Admin',
            last_name='SGU'
        )
        print("Admin account created: admin / admin123")
    else:
        admin_user = User.objects.get(username='admin')
        admin_user.set_password('admin123')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print("Admin account updated: admin / admin123")

    # -------------------------------------------------------------
    # 3. POPULATE ACADEMIC YEARS & SEMESTERS (from 2023 to present)
    # -------------------------------------------------------------
    print("Generating Academic Years and Semesters...")

    current_year = datetime.date.today().year
    # Build list of academic years from 2023-2024 up to the current academic year
    # Academic year X-(X+1): starts Sep of year X, ends Jul of year X+1
    start_year = 2023
    # Determine the last academic year that has started
    # If current month >= 9 (Sep), the academic year X-(X+1) has started where X = current_year
    # Otherwise, the latest started academic year is (current_year-1)-current_year
    today = datetime.date.today()
    if today.month >= 9:
        last_ay_start = today.year
    else:
        last_ay_start = today.year - 1

    academic_years = []
    semesters = []

    for year_start in range(start_year, last_ay_start + 1):
        year_end = year_start + 1
        year_name = f"{year_start} - {year_end}"
        is_active = (year_start == last_ay_start)

        ay = AcademicYear.objects.create(
            name=year_name,
            start_date=datetime.date(year_start, 9, 1),
            end_date=datetime.date(year_end, 7, 31),
            is_active=is_active
        )
        academic_years.append(ay)

        # Semester 1: Sep 1 – Jan 31
        s1_active = is_active and today.month >= 9
        s1 = Semester.objects.create(
            academic_year=ay,
            semester_num=1,
            start_date=datetime.date(year_start, 9, 1),
            end_date=datetime.date(year_end, 1, 31),
            is_active=s1_active
        )

        # Semester 2: Feb 1 – Jun 30
        s2_active = is_active and today.month < 9
        s2 = Semester.objects.create(
            academic_year=ay,
            semester_num=2,
            start_date=datetime.date(year_end, 2, 1),
            end_date=datetime.date(year_end, 6, 30),
            is_active=s2_active
        )

        semesters.extend([s1, s2])

    print(f"Created {AcademicYear.objects.count()} Academic Years.")
    print(f"Created {Semester.objects.count()} Semesters.")

    # Determine active semester
    active_semester = Semester.objects.filter(is_active=True).first()
    if not active_semester:
        # Fallback: use the latest semester 2
        active_semester = semesters[-1]
        active_semester.is_active = True
        active_semester.save()
    print(f"Active semester: {active_semester}")

    # -------------------------------------------------------------
    # 4. POPULATE FACULTIES & DEPARTMENTS
    #    Chỉ 5 khoa được yêu cầu
    # -------------------------------------------------------------
    print("Generating Faculties and Departments...")

    sgu_faculties = [
        ("CNTT",  "Khoa Công nghệ Thông tin"),
        ("KTTC",  "Khoa Kế toán - Tài chính"),
        ("TUD",   "Khoa Toán - Ứng dụng"),
        ("VNH",   "Khoa Việt Nam học"),
    ]

    faculty_map = {}
    for code, name in sgu_faculties:
        fac = Faculty.objects.create(code=code, name=name)
        faculty_map[code] = fac

    # Các ngành thuộc 4 khoa
    sgu_departments = [
        # --- Công nghệ Thông tin ---
        ("CNTT", "DCT",  "Công nghệ thông tin"),
        ("CNTT", "DKP",  "Kỹ thuật phần mềm"),

        # --- Kế toán - Tài chính ---
        ("KTTC", "DKT",  "Kế toán"),
        ("KTTC", "DTC",  "Tài chính ngân hàng"),

        # --- Toán - Ứng dụng ---
        ("TUD", "DTU",   "Toán ứng dụng"),

        # --- Việt Nam học ---
        ("VNH", "DVN",   "Việt Nam học"),
    ]

    department_map = {}   # code -> Department object
    department_name_map = {}  # name -> Department object
    for fac_code, dep_code, dep_name in sgu_departments:
        fac_obj = faculty_map[fac_code]
        dep = Department.objects.create(
            faculty=fac_obj,
            code=dep_code,
            name=dep_name
        )
        department_map[dep_code] = dep
        department_name_map[dep_name] = dep

    print(f"Created {Faculty.objects.count()} Faculties.")
    print(f"Created {Department.objects.count()} Departments.")


    # -------------------------------------------------------------
    # 5. POPULATE TEACHERS (35 fictional teachers)
    # -------------------------------------------------------------
    print("Generating Fictional Teachers...")

    last_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
    mid_names  = ["Văn", "Thị", "Hồng", "Minh", "Quốc", "Gia", "Thanh", "Anh", "Đức", "Duy", "Hữu", "Khánh", "Ngọc", "Xuân", "Hoài"]
    first_names = ["Tuấn", "Hương", "Nam", "Lan", "Hải", "Vy", "Phong", "Trang", "Sơn", "Linh", "Khang", "Hà", "Đạt", "Yến", "Hoàng", "Phương", "Sang", "Bảo", "Duy", "Tín", "Khoa", "Dũng", "Tùng", "Phúc", "Thảo"]

    def generate_vietnamese_name():
        return f"{random.choice(last_names)} {random.choice(mid_names)} {random.choice(first_names)}"

    departments_list = list(Department.objects.all())
    teachers = []

    from accounts.constants import TEACHER_GROUP_NAME
    gv_group, _ = Group.objects.get_or_create(name=TEACHER_GROUP_NAME)

    for i in range(1, 36):
        teacher_id = f"GV{i:04d}"
        full_name  = generate_vietnamese_name()
        name_parts = full_name.split()
        first_name = name_parts[-1]
        last_name  = " ".join(name_parts[:-1])

        username = f"gv_{i:02d}"
        email    = f"teacher_{i:02d}@sgu.edu.vn"
        user = User.objects.create(
            username=username,
            email=email,
            first_name=last_name,
            last_name=first_name,
            password=make_password("123456")
        )
        user.groups.add(gv_group)

        dep   = random.choice(departments_list)
        phone = f"09{random.randint(10000000, 99999999)}"

        teacher = Teacher.objects.create(
            user=user,
            department=dep,
            teacher_id=teacher_id,
            phone=phone
        )
        teachers.append(teacher)

    print(f"Created {Teacher.objects.count()} Teachers (Users).")

    # -------------------------------------------------------------
    # 6. POPULATE ROOMS
    #    Cơ sở: 1, 2, C  |  Khu (tòa nhà): A, B, C, D, E
    #    Mã phòng: <campus>.<building><room_num>
    # -------------------------------------------------------------
    print("Generating sample Rooms...")

    campuses  = ['1', '2', 'C']
    buildings = ['A', 'B', 'C', 'D', 'E']
    room_objects = {}

    for campus in campuses:
        for building in buildings:
            for room_num in range(1, 7):   # 6 phòng mỗi khu → 3×5×6 = 90 phòng
                code = f"{campus}.{building}{room_num:03d}"
                r = Room.objects.create(
                    room_code=code,
                    building=f"Khu {building}",
                    campus=campus,
                    capacity=random.choice([40, 50, 60, 80, 100]),
                    has_camera=random.choice([True, True, False])  # 2/3 có camera
                )
                room_objects[code] = r

    print(f"Created {Room.objects.count()} Rooms.")


    # -------------------------------------------------------------
    # 7. POPULATE STUDENT CLASSES
    #    Format: {dep_code}12{last_digit_year}{class_num}
    #    Ví dụ: DCT1231 = ngành DCT, năm 2023, lớp sinh hoạt 1
    #           DCT1232 = ngành DCT, năm 2023, lớp sinh hoạt 2
    # -------------------------------------------------------------
    print("Generating Student Classes...")

    student_classes = {}
    intake_years = list(range(2023, today.year + 1))
    classes_per_year = 2   # số lớp sinh hoạt mỗi ngành/năm

    for dep in departments_list:
        for intake in intake_years:
            year_digit = str(intake)[-1]   # 2023 -> '3'
            for class_num in range(1, classes_per_year + 1):
                class_code = f"{dep.code}12{year_digit}{class_num}"
                if class_code not in student_classes:
                    sc = StudentClass.objects.create(
                        department=dep,
                        class_code=class_code,
                        class_name=f"Lớp {dep.name} {intake} - Lớp {class_num}"[:50],
                        intake_year=intake
                    )
                    student_classes[class_code] = sc

    print(f"Created {StudentClass.objects.count()} Student Classes.")

    # -------------------------------------------------------------
    # 8. POPULATE STUDENTS (from dssv.xlsx)
    # -------------------------------------------------------------
    print("Reading and parsing dssv.xlsx...")

    # Map major names from Excel sheets to department codes (5 khoa)
    major_to_dep_code = {
        "Công nghệ thông tin":                   "DCT",
        "Kỹ thuật phần mềm":                     "DKP",
        "Kế toán":                               "DKT",
        "Tài chính ngân hàng":                   "DTC",
        "Tài chính - Ngân hàng":                 "DTC",
        "Toán ứng dụng":                         "DTU",
        "Việt Nam học":                          "DVN",
    }

    def parse_dob(val):
        if pd.isnull(val):
            return datetime.date(2005, 1, 1)
        if isinstance(val, (datetime.datetime, datetime.date)):
            return val if isinstance(val, datetime.date) else val.date()
        val_str = str(val).strip()
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
            try:
                return datetime.datetime.strptime(val_str, fmt).date()
            except ValueError:
                continue
        return datetime.date(2005, 1, 1)

    from accounts.constants import STUDENT_GROUP_NAME
    sv_group, _ = Group.objects.get_or_create(name=STUDENT_GROUP_NAME)

    excel_file = pd.ExcelFile('dssv.xlsx')

    # Chỉ xử lý sheet thuộc các khoa:
    # CNTT, Kế toán, Tài chính, Toán, Việt Nam học
    ALLOWED_SHEET_KEYWORDS = [
        'cntt', 'ketoan', 'taichinh', 'toan', 'vietnam'
    ]

    def sheet_is_allowed(sheet_name: str) -> bool:
        name_lower = sheet_name.lower().replace(' ', '').replace(',', '')
        return any(kw in name_lower for kw in ALLOWED_SHEET_KEYWORDS)

    all_sheets = excel_file.sheet_names
    sheets_to_process = [
        s for s in all_sheets
        if s not in ["TheDuc", "Sheet1"] and sheet_is_allowed(s)
    ]
    print(f"Sheets to process: {sheets_to_process}")

    dep_student_count = {}

    for sheet in sheets_to_process:
        df = excel_file.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]

        if 'Mã SV' not in df.columns or 'Tên' not in df.columns:
            print(f"Skipping sheet {sheet} due to missing columns.")
            continue

        print(f"Processing sheet {sheet} ({len(df)} rows)...")

        for _, row in df.iterrows():
            if pd.isnull(row['Mã SV']):
                continue

            sv_id_str = str(row['Mã SV']).strip().split('.')[0]
            if not sv_id_str.isdigit():
                continue

            last_name_val  = row.get('Họ lót', '')
            first_name_val = row.get('Tên', '')
            full_name = f"{last_name_val} {first_name_val}".strip()
            if not full_name:
                continue

            dob = parse_dob(row.get('Ngày sinh', None))

            raw_major = str(row.get('Tên ngành', '')).strip()
            dep_code = major_to_dep_code.get(raw_major)   # None nếu không thuộc các khoa quy định
            if dep_code is None:
                continue   # bỏ qua sinh viên ngành khác
                
            # Kiểm tra giới hạn số lượng sinh viên
            limit = 0
            if dep_code in ["DCT", "DKP"]:
                limit = 100
            elif dep_code in ["DKT", "DTC", "DTU", "DVN"]:
                limit = 50
                
            if dep_student_count.get(dep_code, 0) >= limit:
                continue
                
            dep_student_count[dep_code] = dep_student_count.get(dep_code, 0) + 1
            
            dep_obj = department_map.get(dep_code, department_map["DCT"])

            # Cohort year from MSSV digits 3-4 (e.g. 3123… → 2023)
            cohort_year = 2023
            if len(sv_id_str) >= 4:
                cohort_code = sv_id_str[2:4]
                if cohort_code.isdigit():
                    cohort_year = 2000 + int(cohort_code)
            # Clamp cohort year to 2023+ for student classes created above
            cohort_year = max(cohort_year, 2023)

            # Assign to class 1 by default; format: DCT1231
            year_digit = str(cohort_year)[-1]
            class_code = f"{dep_obj.code}12{year_digit}1"
            sc_obj = student_classes.get(class_code)
            if not sc_obj:
                sc_obj = StudentClass.objects.create(
                    department=dep_obj,
                    class_code=class_code,
                    class_name=f"Lớp {dep_obj.name} {cohort_year} - Lớp 1"[:50],
                    intake_year=cohort_year
                )
                student_classes[class_code] = sc_obj

            fake_phone = f"09{random.randint(10000000, 99999999)}"
            email = f"{sv_id_str}@student.sgu.edu.vn"

            if not Student.objects.filter(student_id=sv_id_str).exists():
                # Skip nếu username đã tồn tại (tránh IntegrityError)
                if User.objects.filter(username=sv_id_str).exists():
                    continue

                # Use MSSV as username, password = 123456
                student_user = User.objects.create(
                    username=sv_id_str,
                    email=email,
                    first_name=last_name_val,
                    last_name=first_name_val,
                    password=make_password("123456")
                )
                student_user.groups.add(sv_group)

                Student.objects.create(
                    user=student_user,
                    student_class=sc_obj,
                    student_id=sv_id_str,
                    full_name=full_name,
                    date_of_birth=dob,
                    email=email,
                    phone=fake_phone,
                    is_active=True
                )

    print(f"Created {Student.objects.count()} Students.")

    # -------------------------------------------------------------
    # 9. POPULATE COURSES (hardcoded sample courses cho 5 khoa)
    # -------------------------------------------------------------
    print("Generating Courses...")

    sample_courses = [
        # CNTT
        ("DCT", "810001", "Nhập môn lập trình",          3),
        ("DCT", "810002", "Cấu trúc dữ liệu và giải thuật", 3),
        ("DCT", "810003", "Cơ sở dữ liệu",               3),
        ("DCT", "810004", "Lập trình hướng đối tượng",   3),
        ("DCT", "810005", "Mạng máy tính",                3),
        ("DKP", "810011", "Kỹ thuật phần mềm",           3),
        ("DKP", "810012", "Kiểm thử phần mềm",           2),
        ("DKP", "810013", "Lập trình Web",                3),
        ("DKP", "810014", "Phát triển ứng dụng di động", 3),
        # Kế toán (DKT)
        ("DKT", "820001", "Nguyên lý kế toán", 3),
        ("DKT", "820002", "Kế toán tài chính", 3),
        ("DKT", "820003", "Kế toán quản trị", 3),
        # Tài chính ngân hàng (DTC)
        ("DTC", "830001", "Tài chính doanh nghiệp", 3),
        ("DTC", "830002", "Tiền tệ ngân hàng", 3),
        ("DTC", "830003", "Thị trường chứng khoán", 3),
        # Toán ứng dụng (DTU)
        ("DTU", "840001", "Đại số tuyến tính", 3),
        ("DTU", "840002", "Giải tích 1", 3),
        ("DTU", "840003", "Xác suất thống kê", 3),
        # Việt Nam học (DVN)
        ("DVN", "850001", "Cơ sở văn hóa Việt Nam", 3),
        ("DVN", "850002", "Lịch sử văn minh Việt Nam", 3),
        ("DVN", "850003", "Địa lý du lịch Việt Nam", 3),
        # Đại cương (dùng chung)
        ("DCT", "800001", "Toán cao cấp",                3),
        ("DCT", "800002", "Vật lý đại cương",            3),
        ("DCT", "800003", "Tiếng Anh 1",                 3),
        ("DCT", "800004", "Tiếng Anh 2",                 3),
        ("DCT", "800005", "Giáo dục thể chất",           2),
    ]

    course_instances = {}
    for dep_code, course_code, course_name, credits in sample_courses:
        dep = department_map.get(dep_code, department_map["DCT"])
        if not Course.objects.filter(course_code=course_code).exists():
            c = Course.objects.create(
                department=dep,
                course_code=course_code,
                course_name=course_name,
                credits=credits,
                description=f"Học phần {course_name} – Trường Đại học Sài Gòn."
            )
            course_instances[course_code] = c

    print(f"Created {Course.objects.count()} Courses.")


    # -------------------------------------------------------------
    # 10. POPULATE COURSE CLASSES (tạo mẫu từ danh sách courses)
    # -------------------------------------------------------------
    print("Generating Course Classes...")

    teachers_list    = list(Teacher.objects.all())
    rooms_list       = list(Room.objects.all())
    class_instances  = []
    courses_list     = list(Course.objects.all())

    # Tạo 2–3 lớp học phần cho mỗi học phần
    # Mã lớp HP giống lớp sinh hoạt: {dep_code}12{last_digit_year}{class_num:02d}
    # Ví dụ: DCT12501, DCT12502...
    ay_year = active_semester.academic_year.name.split('-')[0].strip()   # "2025 - 2026" -> "2025"
    year_digit = ay_year[-1]   # 2025 -> '5'
    
    dep_class_counter = {}
    
    for course_obj in courses_list:
        num_classes = random.randint(2, 3)
        dep_code = course_obj.department.code
        if dep_code not in dep_class_counter:
            dep_class_counter[dep_code] = 1
            
        for _ in range(num_classes):
            cls_idx = dep_class_counter[dep_code]
            class_code = f"{dep_code}12{year_digit}{cls_idx}"
            dep_class_counter[dep_code] += 1
            
            if CourseClass.objects.filter(course=course_obj, semester=active_semester, class_code=class_code).exists():
                continue
            t_obj = random.choice(teachers_list)
            cc = CourseClass.objects.create(
                course=course_obj,
                semester=active_semester,
                teacher=t_obj,
                class_code=class_code,
                max_students=1000,
                total_sessions=15
            )
            class_instances.append(cc)

            # --- Sinh thời khóa biểu (15 buổi) ---
            # Để thuận tiện test, ngày bắt đầu sẽ là ngày 1 của tháng hiện tại
            today = datetime.date.today()
            test_start_date = datetime.date(today.year, today.month, 1)
            
            c_room = random.choice(rooms_list)
            dow = random.randint(2, 7)
            start_p = random.choice([1, 4, 7]) # Chỉ lấy 1, 4, 7 để không bị trùng giờ và không vượt tiết 10
            end_p = start_p + 2
            
            # Tính ngày của buổi học đầu tiên
            delta_days = (dow - 1) - test_start_date.weekday()
            if delta_days < 0:
                delta_days += 7
            first_date = test_start_date + datetime.timedelta(days=delta_days)
            
            for s_idx in range(1, 16):
                s_date = first_date + datetime.timedelta(weeks=(s_idx - 1))
                
                # Bỏ qua điều kiện s_date > sem_end để test đủ 15 tuần kể từ tháng hiện tại
                Schedule.objects.create(
                    course_class=cc,
                    room=c_room,
                    day_of_week=dow,
                    start_period=start_p,
                    end_period=end_p,
                    date=s_date,
                    session_number=s_idx
                )

    print(f"Created {CourseClass.objects.count()} Course Classes.")
    print(f"Created {Schedule.objects.count()} Schedules.")


    # -------------------------------------------------------------
    # 11. POPULATE ENROLLMENTS (3-5 course classes per student)
    # -------------------------------------------------------------
    print("Generating Enrollments...")

    students_list       = list(Student.objects.all())
    course_classes_list = list(CourseClass.objects.all())

    for student in students_list:
        num_classes     = random.randint(3, 5)
        selected_classes = random.sample(course_classes_list, min(num_classes, len(course_classes_list)))
        for cc in selected_classes:
            if not Enrollment.objects.filter(course_class=cc, student=student).exists():
                Enrollment.objects.create(
                    course_class=cc,
                    student=student,
                    is_active=True
                )

    print(f"Created {Enrollment.objects.count()} Enrollments.")
    print("Database population completed successfully!")

if __name__ == '__main__':
    run()
