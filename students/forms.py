from django import forms
from .models import Student, StudentClass
from academics.models import Department


class StudentClassForm(forms.ModelForm):
    """Form thêm / sửa lớp sinh hoạt."""

    class Meta:
        model = StudentClass
        fields = ['department', 'class_code', 'class_name', 'intake_year']
        widgets = {
            'department': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_department',
            }),
            'class_code': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_class_code',
                'placeholder': 'VD: DHKTPM17A',
            }),
            'class_name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_class_name',
                'placeholder': 'VD: Lớp Kỹ Thuật Phần Mềm 17A',
            }),
            'intake_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_intake_year',
                'placeholder': 'VD: 2022',
                'min': 2000,
                'max': 2100,
            }),
        }
        labels = {
            'department': 'Ngành',
            'class_code': 'Mã lớp',
            'class_name': 'Tên lớp',
            'intake_year': 'Năm nhập học',
        }


class StudentForm(forms.ModelForm):
    """Form thêm / sửa sinh viên (có upload ảnh khuôn mặt)."""

    class Meta:
        model = Student
        fields = [
            'student_class', 'student_id', 'full_name',
            'date_of_birth', 'email', 'phone', 'photo', 'is_active',
        ]
        widgets = {
            'student_class': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_student_class',
            }),
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_student_id',
                'placeholder': 'VD: SV220001',
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_full_name',
                'placeholder': 'Họ và tên sinh viên',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'id': 'id_date_of_birth',
                'type': 'date',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'id_email',
                'placeholder': 'example@email.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_phone',
                'placeholder': '0912 345 678',
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'id': 'id_photo',
                'accept': 'image/*',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_active',
            }),
        }
        labels = {
            'student_class': 'Lớp sinh hoạt',
            'student_id': 'Mã sinh viên (MSSV)',
            'full_name': 'Họ tên',
            'date_of_birth': 'Ngày sinh',
            'email': 'Email',
            'phone': 'Số điện thoại',
            'photo': 'Ảnh khuôn mặt',
            'is_active': 'Đang học',
        }
