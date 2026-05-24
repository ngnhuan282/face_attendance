from django.shortcuts import render

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def student_list(request):
    """Trang quản lý sinh viên – Admin và Giảng Viên đều xem được."""
    return render(request, 'students/list.html', {'active_menu': 'students'})
