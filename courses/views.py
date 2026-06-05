from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction, models
from django.contrib import messages
from django.core.paginator import Paginator
import csv
from io import TextIOWrapper

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required
from students.models import Student
from .models import Course, CourseClass, Enrollment


# ======================== COURSE VIEWS ========================

@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def course_list(request):
    """Danh sách học phần"""
    courses = Course.objects.all().order_by('id')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            models.Q(course_code__icontains=search_query) |
            models.Q(course_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(courses, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    from academics.models import Department
    from schedules.models import Room
    departments = Department.objects.all()
    rooms = Room.objects.all()
    
    context = {
        'active_menu': 'courses',
        'page_obj': page_obj,
        'search_query': search_query,
        'courses': courses,
        'departments': departments,
        'rooms': rooms,
    }
    return render(request, 'courses/course_list.html', context)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["GET", "POST"])
def course_create(request):
    """Tạo mới học phần"""
    if request.method == 'POST':
        try:
            from academics.models import Department
            from schedules.models import Room
            
            department_id = request.POST.get('department')
            room_id = request.POST.get('room')
            course_code = request.POST.get('course_code')
            course_name = request.POST.get('course_name')
            credits = request.POST.get('credits', 3)
            description = request.POST.get('description', '')
            
            # Validation
            if not all([department_id, course_code, course_name]):
                return JsonResponse({'error': 'Vui lòng điền đầy đủ thông tin'}, status=400)
            
            if Course.objects.filter(course_code=course_code).exists():
                return JsonResponse({'error': 'Mã học phần đã tồn tại'}, status=400)
            
            department = get_object_or_404(Department, pk=department_id)
            room = get_object_or_404(Room, pk=room_id) if room_id else None
            
            course = Course.objects.create(
                department=department,
                room=room,
                course_code=course_code,
                course_name=course_name,
                credits=int(credits),
                description=description
            )
            
            messages.success(request, f'Tạo học phần "{course_name}" thành công')
            from django.urls import reverse
            return redirect(reverse('courses:course_list') + '?page=999999')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    from academics.models import Department
    from schedules.models import Room
    departments = Department.objects.all()
    rooms = Room.objects.all()
    context = {
        'active_menu': 'courses',
        'departments': departments,
        'rooms': rooms,
    }
    return render(request, 'courses/course_form.html', context)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["GET", "POST"])
def course_edit(request, pk):
    """Chỉnh sửa học phần"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        try:
            from schedules.models import Room
            
            course.course_name = request.POST.get('course_name', course.course_name)
            course.credits = request.POST.get('credits', course.credits)
            course.description = request.POST.get('description', course.description)
            
            room_id = request.POST.get('room')
            if room_id:
                course.room = get_object_or_404(Room, pk=room_id)
            else:
                course.room = None
            
            course.save()
            
            messages.success(request, 'Cập nhật học phần thành công')
            return redirect('courses:course_list')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    from academics.models import Department
    from schedules.models import Room
    departments = Department.objects.all()
    rooms = Room.objects.all()
    
    context = {
        'active_menu': 'courses',
        'course': course,
        'is_edit': True,
        'departments': departments,
        'rooms': rooms,
    }
    return render(request, 'courses/course_form.html', context)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def course_delete(request, pk):
    """Xóa học phần"""
    from django.db.models.deletion import ProtectedError
    
    course = get_object_or_404(Course, pk=pk)
    course_name = course.course_name
    
    # Check if course has enrollments (students are enrolled)
    has_enrollments = Enrollment.objects.filter(
        course_class__course=course
    ).exists()
    
    if has_enrollments:
        return JsonResponse({
            'error': 'Không thể xóa học phần đang có sinh viên đăng ký'
        }, status=400)
    
    # Check if course has class instances
    if course.course_classes.exists():
        return JsonResponse({
            'error': 'Không thể xóa học phần đang có lớp học phần'
        }, status=400)
    
    try:
        course.delete()
        messages.success(request, f'Xóa học phần "{course_name}" thành công')
        return JsonResponse({'success': 'Xóa học phần thành công'})
    except ProtectedError:
        return JsonResponse({
            'error': 'Không thể xóa học phần (có dữ liệu liên kết)'
        }, status=400)


# ======================== COURSECLASS VIEWS ========================

@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def courseclass_list(request):
    """Danh sách lớp học phần"""
    course_classes = CourseClass.objects.select_related(
        'course', 'semester', 'teacher'
    ).all().order_by('id')
    
    # GV chỉ được xem lớp mình dạy
    if request.is_teacher_group and not request.is_admin_group:
        course_classes = course_classes.filter(teacher__user=request.user)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        course_classes = course_classes.filter(
            models.Q(class_code__icontains=search_query) |
            models.Q(course__course_name__icontains=search_query)
        )
    
    # Filter by semester
    semester_id = request.GET.get('semester')
    if semester_id:
        course_classes = course_classes.filter(semester_id=semester_id)
    
    # Pagination
    paginator = Paginator(course_classes, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    from academics.models import Semester
    from accounts.models import Teacher
    semesters = Semester.objects.all()
    courses = Course.objects.select_related('department').all()
    teachers = Teacher.objects.all()
    # Stats
    stats_classes = CourseClass.objects.all()
    if request.is_teacher_group and not request.is_admin_group:
        stats_classes = stats_classes.filter(teacher__user=request.user)
    total_capacity = stats_classes.aggregate(total=models.Sum('max_students'))['total'] or 0
    total_enrolled = Enrollment.objects.filter(is_active=True, course_class__in=stats_classes).count()
    
    context = {
        'active_menu': 'courseclasses',
        'page_obj': page_obj,
        'search_query': search_query,
        'semesters': semesters,
        'courses': courses,
        'teachers': teachers,
        'selected_semester': semester_id,
        'total_capacity': total_capacity,
        'total_enrolled': total_enrolled,
    }
    return render(request, 'courses/courseclass_list.html', context)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["GET", "POST"])
def courseclass_create(request):
    """Tạo mới lớp học phần"""
    if request.method == 'POST':
        try:
            from academics.models import Semester
            
            course_id = request.POST.get('course')
            semester_id = request.POST.get('semester')
            teacher_id = request.POST.get('teacher')
            class_code = request.POST.get('class_code')
            max_students = request.POST.get('max_students', 40)
            total_sessions = request.POST.get('total_sessions', 15)
            
            # Validation
            if not all([course_id, semester_id, teacher_id, class_code]):
                return JsonResponse({'error': 'Vui lòng điền đầy đủ thông tin'}, status=400)
            
            # Check unique constraint
            if CourseClass.objects.filter(
                course_id=course_id,
                semester_id=semester_id,
                class_code=class_code
            ).exists():
                return JsonResponse({'error': 'Lớp học phần này đã tồn tại'}, status=400)
            
            course = get_object_or_404(Course, pk=course_id)
            semester = get_object_or_404(Semester, pk=semester_id)
            from accounts.models import Teacher
            teacher = get_object_or_404(Teacher, pk=teacher_id)
            
            courseclass = CourseClass.objects.create(
                course=course,
                semester=semester,
                teacher=teacher,
                class_code=class_code,
                max_students=int(max_students),
                total_sessions=int(total_sessions)
            )
            
            messages.success(request, f'Tạo lớp học phần "{class_code}" thành công')
            from django.urls import reverse
            return redirect(reverse('courses:courseclass_list') + '?page=999999')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    courses = Course.objects.all()
    from academics.models import Semester
    from accounts.models import Teacher
    semesters = Semester.objects.all()
    teachers = Teacher.objects.all()
    
    context = {
        'active_menu': 'courseclasses',
        'courses': courses,
        'semesters': semesters,
        'teachers': teachers,
    }
    return render(request, 'courses/courseclass_form.html', context)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["GET", "POST"])
def courseclass_edit(request, pk):
    """Chỉnh sửa lớp học phần"""
    courseclass = get_object_or_404(CourseClass, pk=pk)
    
    if request.method == 'POST':
        try:
            from accounts.models import Teacher
            
            teacher_id = request.POST.get('teacher')
            max_students = request.POST.get('max_students', courseclass.max_students)
            total_sessions = request.POST.get('total_sessions', courseclass.total_sessions)
            
            if teacher_id:
                teacher = get_object_or_404(Teacher, pk=teacher_id)
                courseclass.teacher = teacher
            
            courseclass.max_students = int(max_students)
            courseclass.total_sessions = int(total_sessions)
            courseclass.save()
            
            messages.success(request, 'Cập nhật lớp học phần thành công')
            return redirect('courses:courseclass_list')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    from accounts.models import Teacher
    teachers = Teacher.objects.all()
    
    context = {
        'active_menu': 'courseclasses',
        'courseclass': courseclass,
        'teachers': teachers,
        'is_edit': True,
    }
    return render(request, 'courses/courseclass_form.html', context)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def courseclass_delete(request, pk):
    """Xóa lớp học phần"""
    courseclass = get_object_or_404(CourseClass, pk=pk)
    class_code = courseclass.class_code
    
    # Check if has enrollments
    if courseclass.enrollments.exists():
        return JsonResponse({
            'error': 'Không thể xóa lớp đang có sinh viên đăng ký'
        }, status=400)
    
    courseclass.delete()
    messages.success(request, f'Xóa lớp học phần "{class_code}" thành công')
    return JsonResponse({'success': True})


# ======================== COURSECLASS DETAIL VIEWS ========================

@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def courseclass_detail(request, pk):
    """Chi tiết lớp học phần - xem danh sách sinh viên đã đăng ký"""
    courseclass = get_object_or_404(CourseClass, pk=pk)
    
    # Get enrolled students
    enrollments = courseclass.enrollments.select_related('student').filter(is_active=True)
    
    # Search student
    search_query = request.GET.get('search', '')
    if search_query:
        enrollments = enrollments.filter(
            models.Q(student__student_id__icontains=search_query) |
            models.Q(student__full_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(enrollments, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Attendance Stats
    from attendance.models import AttendanceSession, AttendanceRecord
    
    sessions = AttendanceSession.objects.filter(course_class=courseclass).order_by('-started_at')
    
    all_records = AttendanceRecord.objects.filter(session__course_class=courseclass)
    total_records = all_records.count()
    total_present = all_records.filter(status='present').count()
    
    attendance_rate = 0
    if total_records > 0:
        attendance_rate = round((total_present / total_records) * 100, 1)
        
    for enrollment in page_obj:
        student_records = all_records.filter(student=enrollment.student)
        s_total = student_records.count()
        s_present = student_records.filter(status='present').count()
        if s_total > 0:
            enrollment.attendance_rate = round((s_present / s_total) * 100, 1)
        else:
            enrollment.attendance_rate = None
    
    context = {
        'active_menu': 'courseclasses',
        'courseclass': courseclass,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_enrolled': courseclass.enrollments.filter(is_active=True).count(),
        'attendance_rate': attendance_rate,
        'sessions': sessions,
    }
    return render(request, 'courses/courseclass_detail.html', context)


# ======================== ENROLLMENT VIEWS ========================

@group_required(ADMIN_GROUP_NAME)
def enrollment_all_list(request):
    """Danh sách tất cả đăng ký học phần (tổng hợp)"""
    enrollments = Enrollment.objects.select_related('course_class__course', 'course_class__semester', 'student').all().order_by('id')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        enrollments = enrollments.filter(
            models.Q(student__student_id__icontains=search_query) |
            models.Q(student__full_name__icontains=search_query) |
            models.Q(course_class__class_code__icontains=search_query)
        )
        
    # Pagination
    paginator = Paginator(enrollments, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    courseclasses = CourseClass.objects.select_related('course', 'semester').all().order_by('semester', 'class_code')
    students = Student.objects.filter(is_active=True).order_by('student_id')
    
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(is_active=True).count()
    
    context = {
        'active_menu': 'enrollments',
        'page_obj': page_obj,
        'search_query': search_query,
        'courseclasses': courseclasses,
        'students': students,
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
    }
    return render(request, 'courses/enrollment_all_list.html', context)


@group_required(ADMIN_GROUP_NAME)
def enrollment_list(request, courseclass_id):
    """Danh sách đăng ký học phần của lớp"""
    courseclass = get_object_or_404(CourseClass, pk=courseclass_id)
    enrollments = courseclass.enrollments.select_related('student').all()
    
    context = {
        'active_menu': 'courses',
        'courseclass': courseclass,
        'enrollments': enrollments,
    }
    return render(request, 'courses/enrollment_list.html', context)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def enrollment_add(request):
    """Thêm sinh viên vào lớp học phần"""
    try:
        courseclass_id = request.POST.get('courseclass_id')
        student_id = request.POST.get('student_id')
        
        courseclass = get_object_or_404(CourseClass, pk=courseclass_id)
        student = get_object_or_404(Student, pk=student_id)
        
        # Check if already enrolled
        if Enrollment.objects.filter(course_class=courseclass, student=student).exists():
            return JsonResponse({'error': 'Sinh viên đã đăng ký lớp này'}, status=400)
        
        # Check max students
        current_count = courseclass.enrollments.filter(is_active=True).count()
        if current_count >= courseclass.max_students:
            return JsonResponse({'error': 'Lớp đã đầy'}, status=400)
        
        enrollment = Enrollment.objects.create(
            course_class=courseclass,
            student=student,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Thêm {student.full_name} thành công',
            'enrollment_id': enrollment.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def enrollment_edit(request, enrollment_id):
    """Sửa trạng thái đăng ký học phần"""
    try:
        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
        is_active_str = request.POST.get('is_active')
        
        if is_active_str is not None:
            enrollment.is_active = (is_active_str == 'true')
            enrollment.save()
            
        messages.success(request, f'Cập nhật trạng thái sinh viên {enrollment.student.full_name} thành công')
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def enrollment_remove(request, enrollment_id):
    """Xóa sinh viên khỏi lớp học phần"""
    try:
        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
        student_name = enrollment.student.full_name
        enrollment.delete()
        
        messages.success(request, f'Xóa {student_name} khỏi lớp thành công')
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["GET", "POST"])
def enrollment_import(request, courseclass_id):
    """Import danh sách sinh viên từ file CSV"""
    courseclass = get_object_or_404(CourseClass, pk=courseclass_id)
    
    if request.method == 'POST':
        try:
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                return JsonResponse({'error': 'Chưa chọn file'}, status=400)
            
            if not csv_file.name.endswith('.csv'):
                return JsonResponse({'error': 'Vui lòng chọn file CSV'}, status=400)
            
            # Read CSV
            stream = TextIOWrapper(csv_file.file, encoding='utf-8')
            csv_reader = csv.DictReader(stream)
            
            imported_count = 0
            errors = []
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        student_code = row.get('student_code', '').strip() or row.get('student_id', '').strip()
                        
                        if not student_code:
                            errors.append(f'Dòng {row_num}: Mã sinh viên trống')
                            continue
                        
                        try:
                            student = Student.objects.get(student_id=student_code)
                        except Student.DoesNotExist:
                            errors.append(f'Dòng {row_num}: Không tìm thấy sinh viên {student_code}')
                            continue
                        
                        # Check if already enrolled
                        if Enrollment.objects.filter(course_class=courseclass, student=student).exists():
                            errors.append(f'Dòng {row_num}: {student_code} đã đăng ký')
                            continue
                        
                        # Check max students
                        current_count = courseclass.enrollments.filter(is_active=True).count()
                        if current_count >= courseclass.max_students:
                            errors.append(f'Dòng {row_num}: Lớp đã đầy')
                            continue
                        
                        Enrollment.objects.create(
                            course_class=courseclass,
                            student=student,
                            is_active=True
                        )
                        imported_count += 1
                    except Exception as e:
                        errors.append(f'Dòng {row_num}: {str(e)}')
            
            message = f'Import thành công {imported_count} sinh viên'
            if errors:
                message += f'. Có {len(errors)} lỗi'
            
            messages.success(request, message)
            return redirect('courses:enrollment_list', courseclass_id=courseclass.id)
        except Exception as e:
            return JsonResponse({'error': f'Lỗi xử lý file: {str(e)}'}, status=400)
    
    context = {
        'active_menu': 'courses',
        'courseclass': courseclass,
    }
    return render(request, 'courses/enrollment_import.html', context)


@group_required(ADMIN_GROUP_NAME)
def enrollment_export_all(request):
    """Xuất danh sách đăng ký ra file CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="danh_sach_dang_ky.csv"'
    
    # Write BOM for Excel compatibility with UTF-8
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response)
    writer.writerow(['MSSV', 'Ho Ten', 'Ma Lop HP', 'Ten Hoc Phan', 'Hoc Ky', 'Trang Thai'])
    
    enrollments = Enrollment.objects.select_related('course_class__course', 'course_class__semester', 'student').all().order_by('id')
    
    search_query = request.GET.get('search', '')
    if search_query:
        enrollments = enrollments.filter(
            models.Q(student__student_id__icontains=search_query) |
            models.Q(student__full_name__icontains=search_query) |
            models.Q(course_class__class_code__icontains=search_query)
        )
        
    for e in enrollments:
        status = 'Hoat Dong' if e.is_active else 'Da Huy'
        writer.writerow([
            e.student.student_id,
            e.student.full_name,
            e.course_class.class_code,
            e.course_class.course.course_name,
            str(e.course_class.semester),
            status
        ])
        
    return response

@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def enrollment_import_all(request):
    """Import danh sách sinh viên vào các lớp học phần từ file CSV"""
    if request.method == 'POST':
        try:
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                return JsonResponse({'error': 'Chưa chọn file'}, status=400)
            
            if not csv_file.name.endswith('.csv'):
                return JsonResponse({'error': 'Vui lòng chọn file CSV'}, status=400)
            
            from io import TextIOWrapper
            import csv
            stream = TextIOWrapper(csv_file.file, encoding='utf-8-sig')
            csv_reader = csv.DictReader(stream)
            
            imported_count = 0
            errors = []
            
            from django.db import transaction
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        student_code = row.get('student_code', '').strip() or row.get('student_id', '').strip() or row.get('MSSV', '').strip()
                        class_code = row.get('class_code', '').strip() or row.get('Ma Lop HP', '').strip()
                        
                        if not student_code or not class_code:
                            errors.append(f'Dòng {row_num}: Mã sinh viên hoặc Mã lớp trống')
                            continue
                        
                        try:
                            student = Student.objects.get(student_id=student_code)
                        except Student.DoesNotExist:
                            errors.append(f'Dòng {row_num}: Không tìm thấy SV {student_code}')
                            continue
                            
                        try:
                            course_class = CourseClass.objects.get(class_code=class_code)
                        except CourseClass.DoesNotExist:
                            errors.append(f'Dòng {row_num}: Không tìm thấy Lớp HP {class_code}')
                            continue
                        except CourseClass.MultipleObjectsReturned:
                            course_class = CourseClass.objects.filter(class_code=class_code).order_by('-id').first()
                        
                        if Enrollment.objects.filter(course_class=course_class, student=student).exists():
                            errors.append(f'Dòng {row_num}: {student_code} đã đ.ký {class_code}')
                            continue
                        
                        current_count = course_class.enrollments.filter(is_active=True).count()
                        if current_count >= course_class.max_students:
                            errors.append(f'Dòng {row_num}: Lớp {class_code} đã đầy')
                            continue
                        
                        Enrollment.objects.create(
                            course_class=course_class,
                            student=student,
                            is_active=True
                        )
                        imported_count += 1
                    except Exception as e:
                        errors.append(f'Dòng {row_num}: {str(e)}')
            
            message = f'Import thành công {imported_count} đăng ký.'
            if errors:
                message += f' Có {len(errors)} lỗi.'
                # Trả về JSON để JS xử lý và show cả lỗi
                return JsonResponse({'success': True, 'message': message, 'errors': errors})
                
            messages.success(request, message)
            return JsonResponse({'success': True, 'message': message})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
