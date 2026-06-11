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
        error_messages = {
            'student_class': {
                'required': 'Lớp không được để trống.',
            },
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
        label='Mat khau hien tai',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_current_pw',
            'placeholder': 'Mat khau hien tai',
        }),
    )
    new_password = forms.CharField(
        label='Mat khau moi',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_new_pw',
            'placeholder': 'Mat khau moi',
        }),
        min_length=6,
        error_messages={'min_length': 'Mat khau moi phai it nhat 6 ky tu.'}
    )
    confirm_password = forms.CharField(
        label='Xac nhan mat khau moi',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_sv_confirm_pw',
            'placeholder': 'Xac nhan mat khau moi',
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
                self.add_error('current_password', 'Mat khau hien tai khong dung.')

        if new_pw and confirm_pw and new_pw != confirm_pw:
            self.add_error('confirm_password', 'Mat khau xac nhan khong khop.')

        return cleaned_data
