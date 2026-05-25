from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    # Room URLs
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<int:pk>/edit/', views.room_edit, name='room_edit'),
    path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),
    
    # Schedule URLs
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create-bulk/', views.schedule_create_bulk, name='schedule_create_bulk'),
    path('schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
]
