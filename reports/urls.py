from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('',views.report_index, name='index'),
    path('class/<int:class_id>/', views.report_class, name='class'),
    path('class/<int:class_id>/export/', views.export_class_report, name='export_class_report'),
]
