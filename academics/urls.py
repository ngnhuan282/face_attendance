from django.urls import path

from . import views

app_name = 'academics'

urlpatterns = [
    path('', views.semester_list, name='semester_list'),
    path('years/', views.academic_year_list, name='academic_year_list'),
    path('years/create/', views.academic_year_create, name='academic_year_create'),
    path('years/<int:pk>/edit/', views.academic_year_edit, name='academic_year_edit'),
    path('years/<int:pk>/delete/', views.academic_year_delete, name='academic_year_delete'),
    path('semesters/', views.semester_list, name='semester_list'),
    path('academic-years/<int:pk>/edit/', views.academic_year_edit, name='academic_year_edit_legacy'),
    path('semesters/create/', views.semester_create, name='semester_create'),
    path('semesters/<int:pk>/edit/', views.semester_edit, name='semester_edit'),
    path('semesters/<int:pk>/delete/', views.semester_delete, name='semester_delete'),
]
