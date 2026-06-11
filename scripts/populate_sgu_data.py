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
from schedules.models import Room
from courses.models import Course, CourseClass, Enrollment

def run():
    print("Starting database population script with Saigon University (SGU) data...")

    # -------------------------------------------------------------
    # 1. CLEAN EXISTING DATA
    # -------------------------------------------------------------
    print("Clearing existing database records in correct order...")
    Enrollment.objects.all().delete()
    CourseClass.objects.all().delete()
    Course.objects.all().delete()
    Student.objects.all().delete()
    StudentClass.objects.all().delete()

    # Clear teachers and their User accounts (GV-prefixed usernames or linked to Teacher)
    User.objects.filter(username__startswith='gv_').delete()
    Teacher.objects.all().delete()

    Department.objects.all().delete()
    Faculty.objects.all().delete()
    Room.objects.all().delete()
    Semester.objects.all().delete()
    AcademicYear.objects.all().delete()
    print("Existing data cleared.")

    # -------------------------------------------------------------
    # 2. CREATE / ENSURE ADMIN ACCOUNT
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
    #    38 official SGU majors as provided
    # -------------------------------------------------------------
    print("Generating Faculties and Departments...")

    # Group the 38 majors into sensible faculties
    sgu_faculties = [
        ("SPTN",  "Khoa Sư phạm Tự nhiên"),
        ("SPXH",  "Khoa Sư phạm Xã hội"),
        ("SPNT",  "Khoa Sư phạm Nghệ thuật"),
        ("GDCB",  "Khoa Giáo dục Cơ bản"),
        ("KTKT",  "Khoa Kinh tế - Kế toán"),
        ("LUAT",  "Khoa Luật"),
        ("MT",    "Khoa Môi trường"),
        ("QLGD",  "Khoa Quản lý Giáo dục"),
        ("XHNV",  "Khoa Xã hội & Nhân văn"),
        ("TVTT",  "Khoa Thông tin - Thư viện"),
        ("CNTT",  "Khoa Công nghệ Thông tin"),
        ("KTDDT", "Khoa Kỹ thuật Điện - Điện tử"),
    ]

    faculty_map = {}
    for code, name in sgu_faculties:
        fac = Faculty.objects.create(code=code, name=name)
        faculty_map[code] = fac

    # 38 SGU departments (majors) as officially listed
    # (faculty_code, major_code, major_name)
    sgu_departments = [
        # --- Sư phạm Tự nhiên ---
        ("SPTN",  "DTO",  "SP Toán"),
        ("SPTN",  "DLI",  "SP Vật lí"),
        ("SPTN",  "DHO",  "SP Hóa"),
        ("SPTN",  "DSI",  "SP Sinh học"),
        ("SPTN",  "DKH",  "Sư phạm Khoa học tự nhiên"),
        ("SPTN",  "DTU",  "Toán ứng dụng"),

        # --- Sư phạm Xã hội ---
        ("SPXH",  "DVA",  "SP Ngữ văn"),
        ("SPXH",  "DSU",  "SP Lịch sử"),
        ("SPXH",  "DDI",  "SP Địa lý"),
        ("SPXH",  "DLD",  "Sư phạm Lịch sử – Địa lý"),
        ("SPXH",  "DGD",  "Giáo dục Chính trị"),

        # --- Sư phạm Ngoại ngữ ---
        ("SPXH",  "DSA",  "SP Tiếng Anh"),
        ("SPXH",  "DAN",  "Ngôn ngữ Anh"),

        # --- Sư phạm Nghệ thuật ---
        ("SPNT",  "DNH",  "SP Âm nhạc"),
        ("SPNT",  "DMI",  "SP Mỹ thuật"),
        ("SPNT",  "DNA",  "Thanh nhạc"),

        # --- Giáo dục Cơ bản ---
        ("GDCB",  "DGT",  "Giáo dục Tiểu học"),
        ("GDCB",  "DGM",  "Giáo dục Mầm non"),

        # --- Kinh tế - Kế toán ---
        ("KTKT",  "DKE",  "Kế toán"),
        ("KTKT",  "DQK",  "Quản trị kinh doanh"),
        ("KTKT",  "DKQ",  "Kinh doanh quốc tế"),
        ("KTKT",  "DTN",  "Tài chính – Ngân hàng"),

        # --- Luật ---
        ("LUAT",  "DLU",  "Luật"),

        # --- Môi trường ---
        ("MT",    "DKM",  "Khoa học môi trường"),
        ("MT",    "DCM",  "Công nghệ Kĩ thuật Môi trường"),

        # --- Quản lý Giáo dục ---
        ("QLGD",  "DQG",  "Quản lý Giáo dục"),

        # --- Xã hội & Nhân văn ---
        ("XHNV",  "DTL",  "Tâm lí học"),
        ("XHNV",  "DVI",  "Việt Nam học"),
        ("XHNV",  "DQT",  "Quốc tế học"),

        # --- Thông tin - Thư viện ---
        ("TVTT",  "DQV",  "Quản trị văn phòng"),
        ("TVTT",  "DTT",  "Thông tin – Thư viện"),
        ("TVTT",  "DKV",  "Khoa học Thư viện"),

        # --- Công nghệ Thông tin ---
        ("CNTT",  "DCT",  "Công nghệ thông tin"),
        ("CNTT",  "DKP",  "Kỹ thuật phần mềm"),

        # --- Kỹ thuật Điện - Điện tử ---
        ("KTDDT", "DDE",  "Kĩ thuật điện"),
        ("KTDDT", "DDV",  "Kĩ thuật Điện tử – viễn thông"),
        ("KTDDT", "DKD",  "Công nghệ Kĩ thuật điện, điện tử"),
        ("KTDDT", "DCV",  "Công nghệ KT điện tử – viễn thông"),
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
            first_name=first_name,
            last_name=last_name,
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
    # 6. POPULATE ROOMS (from dkmh_all_lines.txt, min 30)
    # -------------------------------------------------------------
    print("Generating Rooms from DKMH data...")

    dkmh_file = 'dkmh_all_lines.txt'
    with open(dkmh_file, 'r', encoding='utf-8') as f:
        dkmh_text = f.read()

    room_pattern = re.compile(r'\b(C\.[A-Z0-9]+|1\.[A-Z0-9]+|TTSP\d+)\b')
    parsed_room_codes = sorted(list(set(room_pattern.findall(dkmh_text))))

    room_objects = {}
    for code in parsed_room_codes:
        if code.startswith("C."):
            building = "Khu C"
        elif code.startswith("1."):
            building = "Khu 1"
        else:
            building = "Thực tập"

        r = Room.objects.create(
            room_code=code,
            building=building,
            capacity=random.choice([40, 50, 80, 100, 120]),
            has_camera=random.choice([True, False])
        )
        room_objects[code] = r

    # Pad to at least 30 rooms
    rooms_count = Room.objects.count()
    if rooms_count < 30:
        for idx in range(rooms_count + 1, 35):
            code = f"C.E{idx:02d}"
            r = Room.objects.create(
                room_code=code,
                building="Khu C",
                capacity=50,
                has_camera=False
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

    # Map major names from Excel sheets to department codes
    major_to_dep_code = {
        "Kỹ thuật phần mềm":   "DKP",
        "Công nghệ thông tin":  "DCT",
        "Việt Nam học":         "DVI",
        "Sư phạm Toán học":    "DTO",
        "SP Toán":              "DTO",
        "Quản trị văn phòng":   "DQV",
        "Kế toán":              "DKE",
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

    excel_file = pd.ExcelFile('dssv.xlsx')
    sheets_to_process = [s for s in excel_file.sheet_names if s not in ["TheDuc", "Sheet1"]]

    for sheet in sheets_to_process:
        df = excel_file.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]

        if 'Mã SV' not in df.columns or 'Tên' not in df.columns:
            print(f"Skipping sheet {sheet} due to missing columns.")
            continue

        print(f"Processing sheet {sheet} ({len(df)} rows)...")
        df_subset = df.head(40)

        for _, row in df_subset.iterrows():
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
            dep_code = major_to_dep_code.get(raw_major, "DCT")
            dep_obj  = department_map.get(dep_code, department_map["DCT"])

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
                Student.objects.create(
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
    # 9. POPULATE COURSES (from DKMH data)
    # -------------------------------------------------------------
    print("Generating Courses from DKMH data...")

    lines = dkmh_text.split('\n')
    parsed_courses = {}

    course_pattern  = re.compile(r'^(8\d{5})\s+(.+)$')
    credits_pattern = re.compile(r'^(\d)\s+(\d{2,3})\s+(.+)\s+(\d+)$')

    current_course_code = None
    for line in lines:
        line = line.strip()
        if not line:
            continue

        m_course = course_pattern.match(line)
        if m_course:
            code = m_course.group(1)
            name = m_course.group(2)
            parsed_courses[code] = {"course_code": code, "course_name": name, "credits": 3}
            current_course_code = code
            continue

        m_cred = credits_pattern.match(line)
        if m_cred and current_course_code:
            parsed_courses[current_course_code]["credits"] = int(m_cred.group(1))
            current_course_code = None

    # Also handle STT-prefixed lines
    for line in lines:
        line = line.strip()
        m_stt = re.search(
            r'^\d+\s+(8\d{5})\s+([A-Za-đĐâÂêÊôÔưƯơƠíÍúÚýÝáÁàÀảẢãÃạẠéÉèÈẻẺẽẼẹẸíÍìÌỉỈĩĨịỊóÓòÒỏỎõÕọỌúÚùÙủỦũŨụỤýÝỳỲỷỶỹỸỵYăĂắẮằẰẳẲẵẴặẶâÂấẤầẦẩẨẫẪậẬêÊếẾềỀểỂễỄệỆôÔốỐồỒổỔỗỖộỘơƠớỚờỜởỞỡỠợỢưƯứỨừỪửỬữỮựỰa-zA-Z\s\(\),/\-]+)\s+(\d)\s+(\d{2,3})\b',
            line
        )
        if m_stt:
            code = m_stt.group(1)
            name = m_stt.group(2).strip()
            cred = int(m_stt.group(3))
            if code not in parsed_courses:
                parsed_courses[code] = {"course_code": code, "course_name": name, "credits": cred}

    # Create Course records, mapping to appropriate department
    course_instances = {}
    default_dep = department_map["DCT"]

    for code, info in parsed_courses.items():
        dep = default_dep
        name_lower = info["course_name"].lower()
        if "toán" in name_lower:
            dep = department_map.get("DTO", default_dep)
        elif "kế toán" in name_lower or "tài chính" in name_lower:
            dep = department_map.get("DKE", default_dep)
        elif "văn phòng" in name_lower or "thư viện" in name_lower:
            dep = department_map.get("DQV", default_dep)
        elif "du lịch" in name_lower or "việt nam học" in name_lower:
            dep = department_map.get("DVI", default_dep)
        elif "kỹ thuật phần mềm" in name_lower:
            dep = department_map.get("DKP", default_dep)

        c = Course.objects.create(
            department=dep,
            course_code=code,
            course_name=info["course_name"],
            credits=info["credits"],
            description=f"Học phần {info['course_name']} trường Đại học Sài Gòn."
        )
        course_instances[code] = c

    print(f"Created {Course.objects.count()} Courses.")

    # -------------------------------------------------------------
    # 10. POPULATE COURSE CLASSES (from DKMH data, min 30)
    # -------------------------------------------------------------
    print("Generating Course Classes...")

    class_pattern = re.compile(r'\b([A-Z]{3}\d{4})\b')

    parsed_classes = []
    current_code  = None
    current_siso  = 40

    for line in lines:
        line = line.strip()
        if not line:
            continue

        m_course = course_pattern.match(line)
        if m_course:
            current_code = m_course.group(1)
            continue

        m_cred = credits_pattern.match(line)
        if m_cred:
            current_siso = int(m_cred.group(2))
            continue

        m_class = class_pattern.search(line)
        m_room  = room_pattern.search(line)
        if m_class and m_room and current_code:
            c_code = m_class.group(1)
            r_code = m_room.group(1)
            class_key = (current_code, c_code)
            if class_key not in [(pc["course_code"], pc["class_code"]) for pc in parsed_classes]:
                parsed_classes.append({
                    "course_code":  current_code,
                    "class_code":   c_code,
                    "max_students": current_siso,
                    "room_code":    r_code
                })

    # STT-prefixed class lines
    for line in lines:
        line = line.strip()
        m_stt = re.search(
            r'^\d+\s+(8\d{5})\s+([A-Za-đ\s]+[0-9]*)\s+\d\s+(\d{2,3})\s+.+?\s+(\d+)\s+(\d+)\s+([A-Z0-9.]+)\s+([A-Z]{3}\d{4})',
            line
        )
        if m_stt:
            course_code = m_stt.group(1)
            siso        = int(m_stt.group(3))
            room_code   = m_stt.group(6)
            class_code  = m_stt.group(7)
            class_key   = (course_code, class_code)
            if class_key not in [(pc["course_code"], pc["class_code"]) for pc in parsed_classes]:
                parsed_classes.append({
                    "course_code":  course_code,
                    "class_code":   class_code,
                    "max_students": siso,
                    "room_code":    room_code
                })

    # Create CourseClass records
    class_instances  = []
    teachers_list    = list(Teacher.objects.all())

    for pc in parsed_classes:
        course_obj = course_instances.get(pc["course_code"])
        if not course_obj:
            continue
        if CourseClass.objects.filter(course=course_obj, semester=active_semester, class_code=pc["class_code"]).exists():
            continue

        t_obj = random.choice(teachers_list)
        r_obj = room_objects.get(pc["room_code"])

        cc = CourseClass.objects.create(
            course=course_obj,
            semester=active_semester,
            teacher=t_obj,
            class_code=pc["class_code"],
            max_students=pc["max_students"],
            total_sessions=15
        )
        class_instances.append(cc)

    # Pad to at least 30 course classes
    if CourseClass.objects.count() < 30:
        print("Fewer than 30 classes parsed, generating mock classes...")
        courses_list = list(Course.objects.all())
        existing_count = CourseClass.objects.count()
        for idx in range(existing_count + 1, 35):
            c_obj      = random.choice(courses_list)
            t_obj      = random.choice(teachers_list)
            class_code = f"DKP{idx:02d}M"
            cc = CourseClass.objects.create(
                course=c_obj,
                semester=active_semester,
                teacher=t_obj,
                class_code=class_code,
                max_students=50,
                total_sessions=15
            )
            class_instances.append(cc)

    print(f"Created {CourseClass.objects.count()} Course Classes.")

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
