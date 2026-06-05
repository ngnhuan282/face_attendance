from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.account_list, name='list'),
    path('create/', views.account_create, name='create'),
    path('<int:pk>/update/', views.account_edit, name='edit'),
    path('<int:pk>/delete/', views.account_delete, name='delete'),
    path('permissions/', views.permission_matrix, name='permissions'),
]
