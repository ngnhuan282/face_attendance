import os
import re
import sys
import random
import datetime
import pandas as pd
import json
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
    # 2. POPULATE ACADEMIC YEARS & SEMESTERS (Strictly >= 30 rows each)
    # -------------------------------------------------------------
    print("Generating Academic Years and Semesters...")
    # Generate 30 Academic Years (from 1996-1997 to 2025-2026)
    start_year = 1996
    academic_years = []
    semesters = []
    
    for i in range(30):
        year_start = start_year + i
        year_end = year_start + 1
        year_name = f"{year_start} - {year_end}"
        is_active = (year_name == "2025 - 2026")
        
        ay = AcademicYear.objects.create(
            name=year_name,
            start_date=datetime.date(year_start, 9, 1),
            end_date=datetime.date(year_end, 7, 31),
            is_active=is_active
        )
        academic_years.append(ay)
        
        # Create semesters for each academic year to satisfy >= 30 semesters
        # semester 1: Sep 1 to Jan 31
        s1 = Semester.objects.create(
            academic_year=ay,
            semester_num=1,
            start_date=datetime.date(year_start, 9, 1),
            end_date=datetime.date(year_start + 1, 1, 31),
            is_active=False
        )
        # semester 2: Feb 1 to Jun 30
        is_active_semester = (year_name == "2025 - 2026") # Active for current semester
        s2 = Semester.objects.create(
            academic_year=ay,
            semester_num=2,
            start_date=datetime.date(year_start + 1, 2, 1),
            end_date=datetime.date(year_start + 1, 6, 30),
            is_active=is_active_semester
        )
        semesters.extend([s1, s2])
        
    print(f"Created {AcademicYear.objects.count()} Academic Years.")
    print(f"Created {Semester.objects.count()} Semesters.")
    active_semester = Semester.objects.get(academic_year__name="2025 - 2026", semester_num=2)
    print(f"Active semester set to: {active_semester}")

    # -------------------------------------------------------------
    # 3. POPULATE FACULTIES & DEPARTMENTS (Strictly >= 30 rows each)
    # -------------------------------------------------------------
    print("Generating Faculties and Departments...")
    
    # 30 unique SGU-style Faculties
    sgu_faculties = [
        ("CNTT", "Công nghệ Thông tin"),
        ("TOAN", "Toán - Ứng dụng"),
        ("TCKT", "Tài chính - Kế toán"),
        ("TVVP", "Thư viện - Văn phòng"),
        ("VHDL", "Văn hóa và Du lịch"),
        ("NGNN", "Ngoại ngữ"),
        ("GDCT", "Giáo dục Chính trị"),
        ("GDMN", "Giáo dục Mầm non"),
        ("GDTH", "Giáo dục Tiểu học"),
        ("LUAT", "Luật"),
        ("MT", "Môi trường"),
        ("NT", "Nghệ thuật"),
        ("QTKD", "Quản trị Kinh doanh"),
        ("VLCN", "Vật lý - Công nghệ kỹ thuật"),
        ("HOA", "Hóa học"),
        ("SINH", "Sinh học"),
        ("NV", "Ngữ văn"),
        ("LS", "Lịch sử"),
        ("DL", "Địa lý"),
        ("GDTC", "Giáo dục Thể chất"),
        ("MTH", "Mỹ thuật"),
        ("AMN", "Âm nhạc"),
        ("YHOC", "Y học"),
        ("DUOC", "Dược học"),
        ("RHM", "Răng Hàm Mặt"),
        ("DD", "Điều dưỡng"),
        ("DDT", "Công nghệ kỹ thuật Điện - Điện tử"),
        ("QLDT", "Quản lý Đô thị"),
        ("CTXH", "Công tác Xã hội"),
        ("GDDB", "Giáo dục Đặc biệt")
    ]
    
    faculty_map = {}
    for code, name in sgu_faculties:
        fac = Faculty.objects.create(code=code, name=name)
        faculty_map[name] = fac

    # 35 unique SGU-style Departments (majors) mapped to the faculties
    sgu_departments = [
        ("CNTT", "KTPM", "Kỹ thuật phần mềm"),
        ("CNTT", "KHMT", "Khoa học máy tính"),
        ("CNTT", "HTTT", "Hệ thống thông tin"),
        ("CNTT", "ATTT", "An toàn thông tin"),
        ("CNTT", "CNTT", "Công nghệ thông tin"),
        ("TOAN", "SPTOAN", "Sư phạm Toán học"),
        ("TOAN", "TOANUD", "Toán ứng dụng"),
        ("TCKT", "KTOAN", "Kế toán"),
        ("TCKT", "KTOANUD", "Kiểm toán"),
        ("TCKT", "TCNH", "Tài chính - Ngân hàng"),
        ("TVVP", "QTVP", "Quản trị văn phòng"),
        ("TVVP", "KHTV", "Khoa học thư viện"),
        ("VHDL", "VNH", "Việt Nam học"),
        ("VHDL", "QTDL", "Quản trị dịch vụ du lịch và lữ hành"),
        ("NGNN", "SPTA", "Sư phạm Tiếng Anh"),
        ("NGNN", "NNA", "Ngôn ngữ Anh"),
        ("NGNN", "NNTQ", "Ngôn ngữ Trung Quốc"),
        ("NGNN", "NNN", "Ngôn ngữ Nhật"),
        ("NV", "SPNV", "Sư phạm Ngữ văn"),
        ("NV", "VH", "Văn học"),
        ("VLCN", "SPVL", "Sư phạm Vật lý"),
        ("VLCN", "DTVT", "Công nghệ kỹ thuật điện tử - viễn thông"),
        ("HOA", "SPHOA", "Sư phạm Hóa học"),
        ("HOA", "CNKTH", "Công nghệ kỹ thuật hóa học"),
        ("SINH", "SPSINH", "Sư phạm Sinh học"),
        ("SINH", "SHHUD", "Sinh học ứng dụng"),
        ("DL", "SPDL", "Sư phạm Địa lý"),
        ("LS", "SPLS", "Sư phạm Lịch sử"),
        ("GDMN", "SPGDMN", "Sư phạm Giáo dục mầm non"),
        ("GDTH", "SPGDTH", "Sư phạm Giáo dục tiểu học"),
        ("LUAT", "LUAT", "Luật"),
        ("MT", "KHMTG", "Khoa học môi trường"),
        ("QTKD", "QTKD", "Quản trị kinh doanh"),
        ("QTKD", "KDXT", "Kinh doanh quốc tế"),
        ("GDDB", "GDDB", "Giáo dục đặc biệt")
    ]
    
    department_map = {}
    for fac_code, dep_code, dep_name in sgu_departments:
        # Find matching faculty
        fac_obj = Faculty.objects.get(code=fac_code)
        dep = Department.objects.create(
            faculty=fac_obj,
            code=dep_code,
            name=dep_name
        )
        department_map[dep_name] = dep
        
    print(f"Created {Faculty.objects.count()} Faculties.")
    print(f"Created {Department.objects.count()} Departments.")

    # -------------------------------------------------------------
    # 4. POPULATE TEACHERS (Strictly >= 30 rows, Fictional Names)
    # -------------------------------------------------------------
    print("Generating Fictional Teachers...")
    
    last_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
    mid_names = ["Văn", "Thị", "Hồng", "Minh", "Quốc", "Gia", "Thanh", "Anh", "Đức", "Duy", "Hữu", "Khánh", "Ngọc", "Xuân", "Hoài"]
    first_names = ["Tuấn", "Hương", "Nam", "Lan", "Hải", "Vy", "Phong", "Trang", "Sơn", "Linh", "Khang", "Hà", "Đạt", "Yến", "Hoàng", "Phương", "Sang", "Bảo", "Duy", "Tín", "Khoa", "Dũng", "Tùng", "Phúc", "Thảo"]
    
    def generate_vietnamese_name():
        ln = random.choice(last_names)
        mn = random.choice(mid_names)
        fn = random.choice(first_names)
        return f"{ln} {mn} {fn}"
        
    departments_list = list(Department.objects.all())
    teachers = []
    
    # Create 35 unique fictional teachers
    for i in range(1, 36):
        teacher_id = f"GV{i:04d}"
        full_name = generate_vietnamese_name()
        name_parts = full_name.split()
        first_name = name_parts[-1]
        last_name = " ".join(name_parts[:-1])
        
        # Create User
        username = f"gv_{i:02d}"
        email = f"teacher_{i:02d}@sgu.edu.vn"
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password("123456")
        )
        # Assign to GiangVien group
        from accounts.constants import TEACHER_GROUP_NAME
        gv_group, _ = Group.objects.get_or_create(name=TEACHER_GROUP_NAME)
        user.groups.add(gv_group)
        
        # Assign to random department
        dep = random.choice(departments_list)
        
        # Generate fake phone number
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
    # 5. POPULATE ROOMS (Strictly >= 30 rows)
    # -------------------------------------------------------------
    print("Generating Rooms from DKMH data...")
    
    # Load raw text from dkmh_all_lines.txt
    dkmh_file = 'dkmh_all_lines.txt'
    with open(dkmh_file, 'r', encoding='utf-8') as f:
        dkmh_text = f.read()
        
    # Find all rooms matching C.[A-Z0-9]+ or 1.[A-Z0-9]+ or TTSP[0-9]+
    room_pattern = re.compile(r'\b(C\.[A-Z0-9]+|1\.[A-Z0-9]+|TTSP\d+)\b')
    parsed_room_codes = sorted(list(set(room_pattern.findall(dkmh_text))))
    
    room_objects = {}
    for code in parsed_room_codes:
        # Determine building (e.g. C or 1 or TTSP)
        building = ""
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
        
    # Ensure we have at least 30 rooms (if parsed rooms are fewer)
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
    # 6. POPULATE STUDENT CLASSES (Strictly >= 30 rows)
    # -------------------------------------------------------------
    print("Generating Student Classes...")
    
    # We will generate classes for several departments
    # Format: D<DEP_CODE>23A (D: Đại học, 23: intake year, A: Class A)
    # E.g., DKP1231, DKP1232, DCT1231, DKT1231
    student_classes = {}
    intake_years = [2022, 2023, 2024, 2025]
    
    class_index = 1
    for dep in departments_list:
        for intake in intake_years:
            class_code = f"D{dep.code}{str(intake)[2:]}A"
            # Ensure unique
            if class_code not in student_classes:
                sc = StudentClass.objects.create(
                    department=dep,
                    class_code=class_code,
                    class_name=f"Lớp {dep.name} khóa {intake}"[:50],
                    intake_year=intake
                )
                student_classes[class_code] = sc
                class_index += 1
                
    # Ensure at least 30 classes
    classes_count = StudentClass.objects.count()
    print(f"Created {classes_count} Student Classes.")

    # -------------------------------------------------------------
    # 7. POPULATE STUDENTS (Real MSSV, Names, DOBs from Excel, FAKE Phones)
    # -------------------------------------------------------------
    print("Reading and parsing dssv.xlsx...")
    
    # Sheet to Major mapping
    # Major name in sheet -> Department object in db
    major_normalization = {
        "Kỹ thuật phần mềm": "Kỹ thuật phần mềm",
        "Công nghệ thông tin": "Công nghệ thông tin",
        "Việt Nam học": "Việt Nam học",
        "Sư phạm Toán học": "Sư phạm Toán học",
        "Quản trị văn phòng": "Quản trị văn phòng",
        "Kế toán": "Kế toán"
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
    
    students_created = 0
    
    for sheet in sheets_to_process:
        df = excel_file.parse(sheet)
        # Standardize columns
        df.columns = [str(c).strip() for c in df.columns]
        
        # Verify columns exist
        if 'Mã SV' not in df.columns or 'Tên' not in df.columns:
            print(f"Skipping sheet {sheet} due to missing columns.")
            continue
            
        print(f"Processing sheet {sheet} ({len(df)} rows)...")
        
        # Take up to 40 students per sheet to keep database populated but clean
        df_subset = df.head(40)
        
        for idx, row in df_subset.iterrows():
            if pd.isnull(row['Mã SV']):
                continue
                
            # Parse student id
            sv_id_str = str(row['Mã SV']).strip().split('.')[0]
            if not sv_id_str.isdigit():
                continue
                
            # Full name
            last_name_val = row.get('Họ lót', '')
            first_name_val = row.get('Tên', '')
            full_name = f"{last_name_val} {first_name_val}".strip()
            if not full_name:
                continue
                
            # DOB
            dob = parse_dob(row.get('Ngày sinh', None))
            
            # Map to major / department
            raw_major = str(row.get('Tên ngành', '')).strip()
            major_name = major_normalization.get(raw_major, "Công nghệ thông tin")
            dep_obj = department_map.get(major_name, department_map["Công nghệ thông tin"])
            
            # Find or create a matching student class for this major and student's cohort year
            # Cohort year can be deduced from MSSV, e.g. 3123... means 2023
            cohort_year = 2023
            if len(sv_id_str) >= 4:
                cohort_code = sv_id_str[2:4]
                if cohort_code.isdigit():
                    cohort_year = 2000 + int(cohort_code)
                    
            class_code = f"D{dep_obj.code}{str(cohort_year)[2:]}A"
            sc_obj = student_classes.get(class_code)
            if not sc_obj:
                sc_obj = StudentClass.objects.create(
                    department=dep_obj,
                    class_code=class_code,
                    class_name=f"Lớp {dep_obj.name} khóa {cohort_year}"[:50],
                    intake_year=cohort_year
                )
                student_classes[class_code] = sc_obj
                
            # FAKE phone number (DO NOT use from sheet)
            fake_phone = f"09{random.randint(10000000, 99999999)}"
            
            # Email
            email = f"{sv_id_str}@student.sgu.edu.vn"
            
            # Avoid duplicate student_id
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
                students_created += 1

    print(f"Created {Student.objects.count()} Students.")

    # -------------------------------------------------------------
    # 8. POPULATE COURSES (Strictly >= 30 rows, from DKMH data)
    # -------------------------------------------------------------
    print("Generating Courses from DKMH data...")
    
    # We parsed 34 unique courses previously. Let's write the parsing block in the script.
    lines = dkmh_text.split('\n')
    parsed_courses = {}
    
    course_pattern = re.compile(r'^(8\d{5})\s+(.+)$')
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
            parsed_courses[code] = {
                "course_code": code,
                "course_name": name,
                "credits": 3 # default
            }
            current_course_code = code
            continue
            
        m_cred = credits_pattern.match(line)
        if m_cred and current_course_code:
            credits_num = int(m_cred.group(1))
            parsed_courses[current_course_code]["credits"] = credits_num
            current_course_code = None
            
    # Also handle some lines with STT prefix (e.g. "28 841068 Hệ thống thông tin doanh nghiệp...")
    for line in lines:
        line = line.strip()
        m_stt = re.search(r'^\d+\s+(8\d{5})\s+([A-Za-đĐâÂêÊôÔưƯơƠíÍúÚýÝáÁàÀảẢãÃạẠéÉèÈẻẺẽẼẹẸíÍìÌỉỈĩĨịỊóÓòÒỏỎõÕọỌúÚùÙủỦũŨụỤýÝỳỲỷỶỹỸỵYăĂắẮằẰẳẲẵẴặẶâÂấẤầẦẩẨẫẪậẬêÊếẾềỀểỂễỄệỆôÔốỐồỒổỔỗỖộỘơƠớỚờỜởỞỡỠợỢưƯứỨừỪửỬữỮựỰa-zA-Z\s\(\),/\-]+)\s+(\d)\s+(\d{2,3})\b', line)
        if m_stt:
            code = m_stt.group(1)
            name = m_stt.group(2).strip()
            cred = int(m_stt.group(3))
            if code not in parsed_courses:
                parsed_courses[code] = {
                    "course_code": code,
                    "course_name": name,
                    "credits": cred
                }
                
    # Create the Course records
    course_instances = {}
    for code, info in parsed_courses.items():
        # Map course to a relevant department in SGU
        # E.g. default to "Công nghệ thông tin"
        dep = department_map["Công nghệ thông tin"]
        
        # Check course name to map logically
        if "Toán" in info["course_name"]:
            dep = department_map["Sư phạm Toán học"]
        elif "Kế toán" in info["course_name"] or "Tài chính" in info["course_name"]:
            dep = department_map["Kế toán"]
        elif "văn phòng" in info["course_name"] or "thư viện" in info["course_name"]:
            dep = department_map["Quản trị văn phòng"]
        elif "Du lịch" in info["course_name"] or "Việt Nam học" in info["course_name"]:
            dep = department_map["Việt Nam học"]
            
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
    # 9. POPULATE COURSE CLASSES (Strictly >= 30 rows, from DKMH data)
    # -------------------------------------------------------------
    print("Generating Course Classes...")
    
    # We will parse class codes and sizes from DKMH text
    # Schedule line: <Thứ> <Tiết BĐ> <Số tiết> <Phòng> <Lớp> <Tuần học>
    # E.g., "4 6 2 C.E402 DKP1241 1234567---12-------------"
    # Or "2 6 3 C.E403 DCT1243 1234567---12-------------"
    class_pattern = re.compile(r'\b([A-Z]{3}\d{4})\b')
    
    parsed_classes = []
    
    current_code = None
    current_siso = 40
    
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
            
        # Check for class code and room code
        m_class = class_pattern.search(line)
        m_room = room_pattern.search(line)
        
        if m_class and m_room and current_code:
            c_code = m_class.group(1)
            r_code = m_room.group(1)
            
            class_key = (current_code, c_code)
            if class_key not in [(pc["course_code"], pc["class_code"]) for pc in parsed_classes]:
                parsed_classes.append({
                    "course_code": current_code,
                    "class_code": c_code,
                    "max_students": current_siso,
                    "room_code": r_code
                })
                
    # Also handle some lines with STT prefix
    for line in lines:
        line = line.strip()
        m_stt = re.search(r'^\d+\s+(8\d{5})\s+([A-Za-đ\s]+[0-9]*)\s+\d\s+(\d{2,3})\s+.+?\s+(\d+)\s+(\d+)\s+([A-Z0-9.]+)\s+([A-Z]{3}\d{4})', line)
        if m_stt:
            course_code = m_stt.group(1)
            siso = int(m_stt.group(3))
            room_code = m_stt.group(6)
            class_code = m_stt.group(7)
            class_key = (course_code, class_code)
            if class_key not in [ (pc["course_code"], pc["class_code"]) for pc in parsed_classes ]:
                parsed_classes.append({
                    "course_code": course_code,
                    "class_code": class_code,
                    "max_students": siso,
                    "room_code": room_code
                })
                
    # Create the CourseClass records
    class_instances = []
    teachers_list = list(Teacher.objects.all())
    
    # We will create CourseClasses for the active semester (Semester 2 of 2025-2026)
    for idx, pc in enumerate(parsed_classes):
        course_obj = course_instances.get(pc["course_code"])
        if not course_obj:
            continue
            
        # Check if already exists in DB to prevent IntegrityError
        if CourseClass.objects.filter(course=course_obj, semester=active_semester, class_code=pc["class_code"]).exists():
            continue
            
        # Get random teacher
        t_obj = random.choice(teachers_list)
        
        # Room
        r_code = pc["room_code"]
        r_obj = room_objects.get(r_code)
        
        cc = CourseClass.objects.create(
            course=course_obj,
            semester=active_semester,
            teacher=t_obj,
            class_code=pc["class_code"],
            max_students=pc["max_students"],
            total_sessions=15 # standard
        )
        class_instances.append(cc)
        
    # Ensure at least 30 course classes
    classes_count = CourseClass.objects.count()
    if classes_count < 30:
        print("Fewer than 30 classes parsed, generating mock classes...")
        courses_list = list(Course.objects.all())
        for idx in range(classes_count + 1, 35):
            c_obj = random.choice(courses_list)
            t_obj = random.choice(teachers_list)
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
    # 10. POPULATE ENROLLMENTS (Strictly >= 30 rows, using students)
    # -------------------------------------------------------------
    print("Generating Enrollments...")
    
    students_list = list(Student.objects.all())
    course_classes_list = list(CourseClass.objects.all())
    
    enrollment_count = 0
    
    # Enroll each student in 3-5 random course classes
    for student in students_list:
        # Get random sample of course classes
        num_classes = random.randint(3, 5)
        selected_classes = random.sample(course_classes_list, min(num_classes, len(course_classes_list)))
        
        for cc in selected_classes:
            # Check unique together
            if not Enrollment.objects.filter(course_class=cc, student=student).exists():
                Enrollment.objects.create(
                    course_class=cc,
                    student=student,
                    is_active=True
                )
                enrollment_count += 1
                
    print(f"Created {Enrollment.objects.count()} Enrollments.")
    print("Database population completed successfully!")

if __name__ == '__main__':
    run()
