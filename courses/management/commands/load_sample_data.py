from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import datetime, timedelta
from academics.models import Faculty, Department, AcademicYear, Semester
from accounts.models import Teacher
from students.models import StudentClass, Student
from courses.models import Course, CourseClass, Enrollment
from schedules.models import Room

class Command(BaseCommand):
    help = 'Load sample data for EduFace system'

    def handle(self, *args, **options):
        self.stdout.write("Loading sample data...")
        
        # ===================== Faculty & Department =====================
        self.stdout.write("Creating Faculty and Departments...")
        
        faculty_cntt, _ = Faculty.objects.get_or_create(
            code='CNTT',
            defaults={'name': 'Khoa Công Nghệ Thông Tin'}
        )
        
        dept_cntt, _ = Department.objects.get_or_create(
            code='CNTT',
            faculty=faculty_cntt,
            defaults={'name': 'Chuyên ngành Công Nghệ Thông Tin'}
        )
        
        # Create more departments
        dept_tm, _ = Department.objects.get_or_create(
            code='TM',
            faculty=faculty_cntt,
            defaults={'name': 'Chuyên ngành Toán Học'}
        )
        
        dept_vl, _ = Department.objects.get_or_create(
            code='VL',
            faculty=faculty_cntt,
            defaults={'name': 'Chuyên ngành Vật Lý'}
        )
        
        dept_hh, _ = Department.objects.get_or_create(
            code='HH',
            faculty=faculty_cntt,
            defaults={'name': 'Chuyên ngành Hóa Học'}
        )
        
        # ===================== Academic Year & Semester =====================
        self.stdout.write("Creating Academic Years and Semesters...")
        
        now = timezone.now().date()
        academic_year, _ = AcademicYear.objects.get_or_create(
            name='2024-2025',
            defaults={
                'start_date': datetime(2024, 9, 1).date(),
                'end_date': datetime(2025, 8, 31).date(),
                'is_active': True
            }
        )
        
        semester1, _ = Semester.objects.get_or_create(
            academic_year=academic_year,
            semester_num=1,
            defaults={
                'start_date': datetime(2024, 9, 1).date(),
                'end_date': datetime(2024, 12, 31).date(),
                'is_active': True
            }
        )
        
        semester2, _ = Semester.objects.get_or_create(
            academic_year=academic_year,
            semester_num=2,
            defaults={
                'start_date': datetime(2025, 1, 15).date(),
                'end_date': datetime(2025, 5, 31).date(),
                'is_active': False
            }
        )
        
        # ===================== Teachers =====================
        self.stdout.write("Creating Teachers...")
        
        # Create users for teachers
        user1, _ = User.objects.get_or_create(
            username='gv001',
            defaults={
                'first_name': 'Nguyễn',
                'last_name': 'Văn A',
                'email': 'nguyenvana@edu.vn'
            }
        )
        
        user2, _ = User.objects.get_or_create(
            username='gv002',
            defaults={
                'first_name': 'Trần',
                'last_name': 'Thị B',
                'email': 'tranthib@edu.vn'
            }
        )
        
        # Set password
        if not user1.check_password('password123'):
            user1.set_password('password123')
            user1.save()
        
        if not user2.check_password('password123'):
            user2.set_password('password123')
            user2.save()
        
        teacher1, _ = Teacher.objects.get_or_create(
            user=user1,
            defaults={
                'department': dept_cntt,
                'teacher_id': 'GV001',
                'phone': '0912345678'
            }
        )
        
        teacher2, _ = Teacher.objects.get_or_create(
            user=user2,
            defaults={
                'department': dept_cntt,
                'teacher_id': 'GV002',
                'phone': '0987654321'
            }
        )
        
        # ===================== Student Classes =====================
        self.stdout.write("Creating Student Classes...")
        
        sc1, _ = StudentClass.objects.get_or_create(
            class_code='DHKTPM22A',
            defaults={
                'department': dept_cntt,
                'class_name': 'Công Nghệ Thông Tin K22A',
                'intake_year': 2022
            }
        )
        
        sc2, _ = StudentClass.objects.get_or_create(
            class_code='DHKTPM22B',
            defaults={
                'department': dept_cntt,
                'class_name': 'Công Nghệ Thông Tin K22B',
                'intake_year': 2022
            }
        )
        
        # ===================== Students =====================
        self.stdout.write("Creating Students...")
        
        student_data = [
            ('SV220001', 'Lê Minh Tuấn', sc1),
            ('SV220002', 'Phạm Thu Hằng', sc1),
            ('SV220003', 'Ngô Sỹ Hùng', sc1),
            ('SV220004', 'Đinh Hương Giang', sc1),
            ('SV220005', 'Vũ Đạo Duy', sc1),
            ('SV220006', 'Trương Quỳnh Như', sc2),
            ('SV220007', 'Hoàng Minh Khôi', sc2),
            ('SV220008', 'Tô Thị Ngọc Tuyết', sc2),
            ('SV220009', 'Bùi Anh Tuấn', sc2),
            ('SV220010', 'Đặng Thu Phương', sc2),
        ]
        
        students = []
        for student_id, full_name, student_class in student_data:
            student, _ = Student.objects.get_or_create(
                student_id=student_id,
                defaults={
                    'student_class': student_class,
                    'full_name': full_name,
                    'email': f"{student_id.lower()}@student.edu.vn",
                    'is_active': True
                }
            )
            students.append(student)
        
        # ===================== Rooms =====================
        self.stdout.write("Creating Rooms...")
        
        rooms_data = [
            ('A101', 'Tòa A', 40, True),
            ('A102', 'Tòa A', 40, True),
            ('A201', 'Tòa A', 35, False),
            ('A202', 'Tòa A', 40, False),
            ('B101', 'Tòa B', 50, True),
            ('B102', 'Tòa B', 40, True),
            ('C101', 'Tòa C', 30, False),
        ]
        
        rooms_dict = {}
        for room_code, building, capacity, has_camera in rooms_data:
            room, _ = Room.objects.get_or_create(
                room_code=room_code,
                defaults={
                    'building': building,
                    'capacity': capacity,
                    'has_camera': has_camera
                }
            )
            rooms_dict[room_code] = room
        
        # ===================== Courses =====================
        self.stdout.write("Creating Courses...")
        
        courses_data = [
            ('INT101', 'Lập Trình Python', 3, 'A101'),
            ('INT102', 'Cấu Trúc Dữ Liệu và Giải Thuật', 3, 'A102'),
            ('INT103', 'Hệ Quản Trị Cơ Sở Dữ Liệu', 3, 'A201'),
            ('INT104', 'Lập Trình Web (PHP)', 3, 'A202'),
            ('INT105', 'Công Nghệ Phần Mềm', 3, 'B101'),
        ]
        
        courses = []
        teachers_list = [teacher1, teacher2]
        for idx, (course_code, course_name, credits, room_code) in enumerate(courses_data):
            course, _ = Course.objects.get_or_create(
                course_code=course_code,
                defaults={
                    'department': dept_cntt,
                    'room': rooms_dict.get(room_code),
                    'course_name': course_name,
                    'credits': credits,
                    'description': f'Môn học: {course_name}'
                }
            )
            courses.append(course)
        
        # ===================== Course Classes =====================
        self.stdout.write("Creating Course Classes...")
        
        # INT101 - 2 classes
        cc1, _ = CourseClass.objects.get_or_create(
            course=courses[0],
            semester=semester1,
            class_code='INT101.01',
            defaults={
                'teacher': teacher1,
                'max_students': 40,
                'total_sessions': 15
            }
        )
        
        cc2, _ = CourseClass.objects.get_or_create(
            course=courses[0],
            semester=semester1,
            class_code='INT101.02',
            defaults={
                'teacher': teacher2,
                'max_students': 40,
                'total_sessions': 15
            }
        )
        
        # INT102 - 1 class
        cc3, _ = CourseClass.objects.get_or_create(
            course=courses[1],
            semester=semester1,
            class_code='INT102.01',
            defaults={
                'teacher': teacher1,
                'max_students': 40,
                'total_sessions': 15
            }
        )
        
        # INT103 - 1 class
        cc4, _ = CourseClass.objects.get_or_create(
            course=courses[2],
            semester=semester1,
            class_code='INT103.01',
            defaults={
                'teacher': teacher2,
                'max_students': 35,
                'total_sessions': 15
            }
        )
        
        # INT104 - semester 2
        cc5, _ = CourseClass.objects.get_or_create(
            course=courses[3],
            semester=semester2,
            class_code='INT104.01',
            defaults={
                'teacher': teacher1,
                'max_students': 40,
                'total_sessions': 15
            }
        )
        
        # ===================== Enrollments =====================
        self.stdout.write("Creating Enrollments...")
        
        # Students enroll in INT101.01
        enrollment_groups = [
            (cc1, students[0:5]),      # 5 students in INT101.01
            (cc2, students[5:10]),     # 5 students in INT101.02
            (cc3, students[0:7]),      # 7 students in INT102.01
            (cc4, students[3:9]),      # 6 students in INT103.01
        ]
        
        for course_class, student_list in enrollment_groups:
            for student in student_list:
                Enrollment.objects.get_or_create(
                    course_class=course_class,
                    student=student,
                    defaults={'is_active': True}
                )
        
        self.stdout.write(self.style.SUCCESS("Successfully loaded sample data!"))
        self.stdout.write(self.style.SUCCESS(f"  - {Faculty.objects.count()} Faculty"))
        self.stdout.write(self.style.SUCCESS(f"  - {Department.objects.count()} Department"))
        self.stdout.write(self.style.SUCCESS(f"  - {AcademicYear.objects.count()} Academic Years"))
        self.stdout.write(self.style.SUCCESS(f"  - {Semester.objects.count()} Semesters"))
        self.stdout.write(self.style.SUCCESS(f"  - {Teacher.objects.count()} Teachers"))
        self.stdout.write(self.style.SUCCESS(f"  - {Room.objects.count()} Rooms"))
        self.stdout.write(self.style.SUCCESS(f"  - {StudentClass.objects.count()} Student Classes"))
        self.stdout.write(self.style.SUCCESS(f"  - {Student.objects.count()} Students"))
        self.stdout.write(self.style.SUCCESS(f"  - {Course.objects.count()} Courses"))
        self.stdout.write(self.style.SUCCESS(f"  - {CourseClass.objects.count()} Course Classes"))
        self.stdout.write(self.style.SUCCESS(f"  - {Enrollment.objects.count()} Enrollments"))
