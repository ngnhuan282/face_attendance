from django import forms
from django.forms.models import ModelChoiceIterator
from itertools import groupby
from .models import Student, StudentClass
from academics.models import Department


# ── Grouped choice field: nhóm lớp sinh hoạt theo Ngành ──
class GroupedStudentClassIterator(ModelChoiceIterator):
    """Iterator trả về (group_label, [(val, label), ...]) thay vì flat list."""
    def __iter__(self):
        if self.field.empty_label is not None:
            yield ('', self.field.empty_label)
        queryset = self.queryset.select_related('department').order_by('department__name', 'class_code')
        for dept, items in groupby(queryset, key=lambda x: x.department.name if x.department else '—'):
            choices = [(self.choice(c)[0], self.choice(c)[1]) for c in items]
            yield (dept, choices)


class GroupedModelChoiceField(forms.ModelChoiceField):
    iterator = GroupedStudentClassIterator

    def label_from_instance(self, obj):
        return str(obj)


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
        error_messages = {
            'department': {
                'required': 'Ngành không được để trống.',
            },
            'class_code': {
                'required': 'Mã lớp không được để trống.',
                'unique': 'Mã lớp này đã tồn tại.',
            },
            'class_name': {
                'required': 'Tên lớp không được để trống.',
            },
            'intake_year': {
                'required': 'Năm nhập học không được để trống.',
            },
        }


class StudentForm(forms.ModelForm):
    """Form thêm / sửa sinh viên (có upload ảnh khuôn mặt)."""

    # Override field student_class: dùng grouped choice (nhóm theo Ngành)
    student_class = GroupedModelChoiceField(
        queryset=StudentClass.objects.select_related('department').order_by('department__name', 'class_code'),
        required=False,
        empty_label='-- Chọn lớp sinh hoạt --',
        label='Lớp sinh hoạt',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_student_class',
        }),
        error_messages={'required': 'Lớp không được để trống.'},
    )

    class Meta:
        model = Student
        fields = [
            'student_class', 'student_id', 'full_name',
            'date_of_birth', 'email', 'phone', 'photo', 'is_active',
        ]
        widgets = {
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
            'student_id': 'Mã sinh viên (MSSV)',
            'full_name': 'Họ tên',
            'date_of_birth': 'Ngày sinh',
            'email': 'Email',
            'phone': 'Số điện thoại',
            'photo': 'Ảnh khuôn mặt',
            'is_active': 'Đang học',
        }
        error_messages = {
            'student_id': {
                'required': 'Mã sinh viên không được để trống.',
                'unique': 'Mã sinh viên này đã tồn tại.',
            },
            'full_name': {
                'required': 'Họ tên không được để trống.',
            },
        }



class StudentInfoForm(forms.Form):
    """Form de sinh vien tu cap nhat thong tin lien lac."""

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_email',
            'placeholder': 'example@sgu.edu.vn',
        }),
        error_messages={
            'required': 'Email khong duoc de trong.',
            'invalid': 'Email khong hop le.',
        }
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        label='So dien thoai',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_phone',
            'placeholder': '0912 345 678',
        })
    )


class StudentPhotoForm(forms.Form):
    """Form de sinh vien tu cap nhat anh khuon mat."""

    photo = forms.ImageField(
        label='Anh khuon mat moi',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_photo',
            'accept': 'image/*',
        }),
        error_messages={'required': 'Vui long chon anh.'}
    )

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Anh khong duoc vuot qua 5MB.')
        return photo


class StudentPasswordForm(forms.Form):
    """Form de sinh vien tu doi mat khau."""

    current_password = forms.CharField(
        label='Mật khẩu hiện tại',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_current_pw',
            'placeholder': 'Mật khẩu hiện tại',
        }),
    )
    new_password = forms.CharField(
        label='Mật khẩu mới',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_new_pw',
            'placeholder': 'Mật khẩu mới',
        }),
        min_length=6,
        error_messages={'min_length': 'Mật khẩu mới phải ít nhất 6 ký tự.'}
    )
    confirm_password = forms.CharField(
        label='Xác nhận mật khẩu mới',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_confirm_pw',
            'placeholder': 'Xác nhận mật khẩu mới',
        }),
    )

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        current_pw = cleaned_data.get('current_password')
        new_pw = cleaned_data.get('new_password')
        confirm_pw = cleaned_data.get('confirm_password')

        if current_pw and self.user_instance:
            if not self.user_instance.check_password(current_pw):
                self.add_error('current_password', 'Mật khẩu hiện tại không đúng.')

        if new_pw and confirm_pw and new_pw != confirm_pw:
            self.add_error('confirm_password', 'Mật khẩu xác nhận không khớp.')

        return cleaned_data
