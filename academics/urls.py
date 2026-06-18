from django.urls import path

from . import views

app_name = 'academics'

urlpatterns = [
    path('', views.semester_list, name='semester_list'),
    path('semesters/', views.semester_list, name='semester_list'),
    path('semesters/create/', views.semester_create, name='semester_create'),
    path('semesters/<int:pk>/edit/', views.semester_edit, name='semester_edit'),
    path('semesters/<int:pk>/delete/', views.semester_delete, name='semester_delete'),
]
