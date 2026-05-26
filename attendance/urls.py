from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_demo, name="demo"),
    path("stream/<int:session_id>/", views.video_stream, name="video_stream"),
    path("api/sessions/", views.session_list_create, name="session_list_create"),
    path("api/sessions/<int:pk>/", views.session_detail, name="session_detail"),
    path("api/records/", views.record_list_create, name="record_list_create"),
    path("api/records/<int:pk>/", views.record_detail, name="record_detail"),
    path("api/recognize/", views.recognize_attendance, name="recognize_attendance"),
]
