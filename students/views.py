from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def student_list(request):
    """Trang quản lý sinh viên (UI tĩnh)."""
    return render(request, 'students/list.html', {'active_menu': 'students'})
