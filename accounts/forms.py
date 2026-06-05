from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from academics.models import Department
from .models import Teacher
from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME

class AccountForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên đăng nhập'}),
        error_messages={
            'required': 'Tên đăng nhập không được để trống.'
        }
    )
    first_name = forms.CharField(
        max_length=150,
        label='Họ và tên đệm',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên đệm'}),
        error_messages={
            'required': 'Họ và tên đệm không được để trống.'
        }
    )
    last_name = forms.CharField(
        max_length=150,
        label='Tên',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên'}),
        error_messages={
            'required': 'Tên không được để trống.'
        }
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@eduface.vn'}),
        error_messages={
            'required': 'Email không được để trống.',
            'invalid': 'Email không hợp lệ.'
        }
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        required=True,
        error_messages={
            'required': 'Mật khẩu không được để trống.'
        }
    )
    role = forms.ChoiceField(
        choices=[('admin', 'Quản Trị Viên'), ('teacher', 'Giảng Viên')],
        label='Vai trò',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_role'})
    )
    is_active = forms.BooleanField(
        label='Hoạt động',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Teacher fields
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='Ngành',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_department'}),
        error_messages={
            'required': 'Ngành không được để trống.'
        }
    )
    teacher_id = forms.CharField(
        max_length=20,
        required=False,
        label='Mã giảng viên (MSSV/MSGV)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_teacher_id', 'placeholder': 'VD: GV001'}),
        error_messages={
            'required': 'Mã giảng viên không được để trống.'
        }
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        label='Số điện thoại',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_phone', 'placeholder': '0912 345 678'})
    )
    avatar = forms.ImageField(
        required=False,
        label='Ảnh đại diện',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'id_avatar', 'accept': 'image/*'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Tên đăng nhập này đã tồn tại.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'teacher':
            if not cleaned_data.get('department'):
                self.add_error('department', 'Ngành không được để trống.')
            if not cleaned_data.get('teacher_id'):
                self.add_error('teacher_id', 'Mã giảng viên không được để trống.')
            else:
                tid = cleaned_data.get('teacher_id')
                if Teacher.objects.filter(teacher_id=tid).exists():
                    self.add_error('teacher_id', 'Mã giảng viên này đã tồn tại.')
        return cleaned_data


class AccountEditForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        label='Họ và tên đệm',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên đệm'}),
        error_messages={
            'required': 'Họ và tên đệm không được để trống.'
        }
    )
    last_name = forms.CharField(
        max_length=150,
        label='Tên',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên'}),
        error_messages={
            'required': 'Tên không được để trống.'
        }
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@eduface.vn'}),
        error_messages={
            'required': 'Email không được để trống.',
            'invalid': 'Email không hợp lệ.'
        }
    )
    password = forms.CharField(
        label='Mật khẩu (Để trống nếu không đổi)',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        required=False
    )
    role = forms.ChoiceField(
        choices=[('admin', 'Quản Trị Viên'), ('teacher', 'Giảng Viên')],
        label='Vai trò',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_role'})
    )
    is_active = forms.BooleanField(
        label='Hoạt động',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Teacher fields
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='Ngành',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_department'}),
        error_messages={
            'required': 'Ngành không được để trống.'
        }
    )
    teacher_id = forms.CharField(
        max_length=20,
        required=False,
        label='Mã giảng viên (MSSV/MSGV)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_teacher_id', 'placeholder': 'VD: GV001'}),
        error_messages={
            'required': 'Mã giảng viên không được để trống.'
        }
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        label='Số điện thoại',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_phone', 'placeholder': '0912 345 678'})
    )
    avatar = forms.ImageField(
        required=False,
        label='Ảnh đại diện',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'id_avatar', 'accept': 'image/*'})
    )

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'teacher':
            if not cleaned_data.get('department'):
                self.add_error('department', 'Ngành không được để trống.')
            if not cleaned_data.get('teacher_id'):
                self.add_error('teacher_id', 'Mã giảng viên không được để trống.')
            else:
                tid = cleaned_data.get('teacher_id')
                qs = Teacher.objects.filter(teacher_id=tid)
                if self.user_instance and hasattr(self.user_instance, 'teacher'):
                    qs = qs.exclude(pk=self.user_instance.teacher.pk)
                if qs.exists():
                    self.add_error('teacher_id', 'Mã giảng viên này đã tồn tại.')
        return cleaned_data
