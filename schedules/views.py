from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import models
from django.contrib import messages
from django.core.paginator import Paginator
from datetime import datetime, timedelta

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required
from .models import Room, Schedule
from courses.models import CourseClass

# ======================== ROOM VIEWS ========================

@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def room_list(request):
    """Danh sách phòng học"""
    rooms = Room.objects.all().order_by('id')
    
    search_query = request.GET.get('search', '')
    if search_query:
        rooms = rooms.filter(
            models.Q(room_code__icontains=search_query) |
            models.Q(building__icontains=search_query)
        )
        
    paginator = Paginator(rooms, 10)
    page_number = request.GET.get('page', 1)
    if page_number == 'last' or page_number == '999999':
        page_number = paginator.num_pages
    page_obj = paginator.get_page(page_number)
    
    context = {
        'active_menu': 'rooms',
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'schedules/room_list.html', context)

@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def room_create(request):
    try:
        room_code = request.POST.get('room_code')
        building = request.POST.get('building', '')
        capacity = request.POST.get('capacity', 40)
        has_camera = request.POST.get('has_camera') == 'on'
        
        if not room_code:
            return JsonResponse({'error': 'Vui lòng điền mã phòng'}, status=400)
            
        if Room.objects.filter(room_code=room_code).exists():
            return JsonResponse({'error': 'Mã phòng đã tồn tại'}, status=400)
            
        Room.objects.create(
            room_code=room_code,
            building=building,
            capacity=int(capacity),
            has_camera=has_camera
        )
        
        messages.success(request, f'Thêm phòng {room_code} thành công!')
        from django.urls import reverse
        return redirect(reverse('schedules:room_list') + '?page=999999')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def room_edit(request, pk):
    try:
        room = get_object_or_404(Room, pk=pk)
        
        room_code = request.POST.get('room_code')
        building = request.POST.get('building', '')
        capacity = request.POST.get('capacity', 40)
        has_camera = request.POST.get('has_camera') == 'on'
        
        if not room_code:
            return JsonResponse({'error': 'Vui lòng điền mã phòng'}, status=400)
            
        if Room.objects.filter(room_code=room_code).exclude(pk=pk).exists():
            return JsonResponse({'error': 'Mã phòng đã tồn tại'}, status=400)
            
        room.room_code = room_code
        room.building = building
        room.capacity = int(capacity)
        room.has_camera = has_camera
        room.save()
        
        messages.success(request, f'Cập nhật phòng {room_code} thành công!')
        return redirect('schedules:room_list')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def room_delete(request, pk):
    try:
        room = get_object_or_404(Room, pk=pk)
        if room.schedules.exists():
            return JsonResponse({'error': 'Không thể xóa phòng học đang có lịch học'}, status=400)
        
        room.delete()
        return JsonResponse({'success': True, 'message': 'Xóa phòng thành công!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ======================== SCHEDULE VIEWS ========================

@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def schedule_list(request):
    """Danh sách lịch học"""
    schedules = Schedule.objects.select_related('course_class', 'course_class__course', 'room').all().order_by('id')
    
    courseclass_id = request.GET.get('courseclass_id')
    if courseclass_id:
        schedules = schedules.filter(course_class_id=courseclass_id)
        
    start_date = request.GET.get('start_date')
    if start_date:
        schedules = schedules.filter(date__gte=start_date)
        
    end_date = request.GET.get('end_date')
    if end_date:
        schedules = schedules.filter(date__lte=end_date)
        
    paginator = Paginator(schedules, 15)
    page_number = request.GET.get('page', 1)
    if page_number == 'last' or page_number == '999999':
        page_number = paginator.num_pages
    page_obj = paginator.get_page(page_number)
    
    course_classes = CourseClass.objects.all().order_by('-id')
    rooms = Room.objects.all().order_by('building', 'room_code')
    
    context = {
        'active_menu': 'schedules',
        'page_obj': page_obj,
        'courseclass_id': int(courseclass_id) if courseclass_id else '',
        'start_date': start_date,
        'end_date': end_date,
        'course_classes': course_classes,
        'rooms': rooms,
    }
    return render(request, 'schedules/schedule_list.html', context)

@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def schedule_create_bulk(request):
    """Tạo lịch học hàng loạt theo tuần"""
    try:
        courseclass_id = request.POST.get('course_class')
        room_id = request.POST.get('room')
        day_of_week = int(request.POST.get('day_of_week'))
        start_period = int(request.POST.get('start_period'))
        end_period = int(request.POST.get('end_period'))
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        if not all([courseclass_id, room_id, day_of_week, start_period, end_period, start_date_str, end_date_str]):
            return JsonResponse({'error': 'Vui lòng điền đủ thông tin'}, status=400)
            
        if start_period >= end_period:
            return JsonResponse({'error': 'Tiết kết thúc phải lớn hơn tiết bắt đầu'}, status=400)
            
        course_class = get_object_or_404(CourseClass, pk=courseclass_id)
        room = get_object_or_404(Room, pk=room_id)
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        if start_date > end_date:
            return JsonResponse({'error': 'Ngày bắt đầu không được lớn hơn ngày kết thúc'}, status=400)
            
        dates_to_create = []
        current_date = start_date
        
        target_weekday = day_of_week - 2 
        
        while current_date <= end_date:
            if current_date.weekday() == target_weekday:
                dates_to_create.append(current_date)
            current_date += timedelta(days=1)
            
        if not dates_to_create:
            return JsonResponse({'error': 'Không có ngày nào khớp với thứ trong khoảng thời gian đã chọn.'}, status=400)
            
        # Check conflicts
        for d in dates_to_create:
            # 1. Trùng lịch của cùng lớp học phần
            if Schedule.objects.filter(course_class=course_class, date=d).exists():
                return JsonResponse({'error': f'Lớp {course_class.class_code} đã có lịch học vào ngày {d.strftime("%d/%m/%Y")}.'}, status=400)
                
            # 2. Trùng phòng học
            overlapping = Schedule.objects.filter(
                room=room,
                date=d,
                start_period__lte=end_period,
                end_period__gte=start_period
            ).first()
            if overlapping:
                return JsonResponse({'error': f'Phòng {room.room_code} đã có lớp {overlapping.course_class.class_code} học từ tiết {overlapping.start_period}-{overlapping.end_period} vào ngày {d.strftime("%d/%m/%Y")}.'}, status=400)
                
        last_schedule = Schedule.objects.filter(course_class=course_class).order_by('-session_number').first()
        session_num = (last_schedule.session_number + 1) if last_schedule else 1
        
        created_count = 0
        for d in dates_to_create:
            Schedule.objects.create(
                course_class=course_class,
                room=room,
                day_of_week=day_of_week,
                start_period=start_period,
                end_period=end_period,
                date=d,
                session_number=session_num
            )
            session_num += 1
            created_count += 1
            
        if created_count == 0:
            return JsonResponse({'error': 'Không có buổi học nào được tạo. Có thể do chọn trùng lịch hoặc khoảng thời gian không khớp.'}, status=400)
            
        messages.success(request, f'Tạo thành công {created_count} buổi học!')
        from django.urls import reverse
        return redirect(reverse('schedules:schedule_list') + f'?courseclass_id={courseclass_id}&page=999999')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def schedule_edit(request, pk):
    try:
        schedule = get_object_or_404(Schedule, pk=pk)
        
        room_id = request.POST.get('room')
        start_period = request.POST.get('start_period')
        end_period = request.POST.get('end_period')
        date_str = request.POST.get('date')
        
        if not all([room_id, start_period, end_period, date_str]):
            return JsonResponse({'error': 'Vui lòng điền đủ thông tin'}, status=400)
            
        if int(start_period) >= int(end_period):
            return JsonResponse({'error': 'Tiết kết thúc phải lớn hơn tiết bắt đầu'}, status=400)
            
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # day_of_week
        day_of_week = date_obj.weekday() + 2
        
        if Schedule.objects.filter(course_class=schedule.course_class, date=date_obj).exclude(pk=pk).exists():
            return JsonResponse({'error': 'Ngày học này đã có lịch cho lớp học phần'}, status=400)
            
        # Check overlap in same room
        overlapping = Schedule.objects.filter(
            room_id=room_id,
            date=date_obj,
            start_period__lte=int(end_period),
            end_period__gte=int(start_period)
        ).exclude(pk=pk).first()
        if overlapping:
            return JsonResponse({'error': f'Phòng {overlapping.room.room_code} đã có lớp {overlapping.course_class.class_code} học từ tiết {overlapping.start_period}-{overlapping.end_period} vào ngày {date_obj.strftime("%d/%m/%Y")}.'}, status=400)
            
        schedule.room_id = room_id
        schedule.start_period = int(start_period)
        schedule.end_period = int(end_period)
        schedule.date = date_obj
        schedule.day_of_week = day_of_week
        schedule.save()
        
        messages.success(request, f'Cập nhật buổi học ngày {date_obj.strftime("%d/%m/%Y")} thành công!')
        return redirect('schedules:schedule_list')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@group_required(ADMIN_GROUP_NAME)
@require_http_methods(["POST"])
def schedule_delete(request, pk):
    try:
        schedule = get_object_or_404(Schedule, pk=pk)
        date_str = schedule.date.strftime("%d/%m/%Y")
        schedule.delete()
        return JsonResponse({'success': True, 'message': f'Xóa buổi học ngày {date_str} thành công!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
