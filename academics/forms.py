import re
from datetime import date, timedelta

from django import forms

from .models import AcademicYear, Department, Faculty, Semester


class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['code', 'name']
        labels = {
            'code': 'Mã khoa',
            'name': 'Tên khoa',
        }
        widgets = {
            'code': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'VD: CNTT'},
            ),
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'VD: Công Nghệ Thông Tin'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].error_messages['required'] = 'Vui lòng nhập mã khoa.'
        self.fields['name'].error_messages['required'] = 'Vui lòng nhập tên khoa.'

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        qs = Faculty.objects.filter(code=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Mã khoa này đã tồn tại.')
        return code

    def clean_name(self):
        return self.cleaned_data['name'].strip()


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['faculty', 'code', 'name']
        labels = {
            'faculty': 'Khoa',
            'code': 'Mã ngành',
            'name': 'Tên ngành',
        }
        widgets = {
            'faculty': forms.Select(attrs={'class': 'form-control'}),
            'code': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'VD: KTPM'},
            ),
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'VD: Kỹ Thuật Phần Mềm'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty'].queryset = Faculty.objects.order_by('code')
        self.fields['faculty'].empty_label = '-- Chọn khoa --'
        self.fields['faculty'].error_messages['required'] = 'Vui lòng chọn khoa.'
        self.fields['code'].error_messages['required'] = 'Vui lòng nhập mã ngành.'
        self.fields['name'].error_messages['required'] = 'Vui lòng nhập tên ngành.'

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        qs = Department.objects.filter(code=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Mã ngành này đã tồn tại.')
        return code

    def clean_name(self):
        return self.cleaned_data['name'].strip()


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date']
        labels = {
            'name': 'Năm học',
            'start_date': 'Ngày bắt đầu',
            'end_date': 'Ngày kết thúc',
        }
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'VD: 2025 - 2026'},
            ),
            'start_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'},
            ),
            'end_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        self.fields['name'].error_messages['required'] = 'Vui lòng nhập năm học.'
        self.fields['start_date'].error_messages['required'] = 'Vui lòng nhập ngày bắt đầu.'
        self.fields['end_date'].error_messages['required'] = 'Vui lòng nhập ngày kết thúc.'

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        match = re.fullmatch(r'(\d{4})\s*-\s*(\d{4})', name)
        if not match:
            raise forms.ValidationError('Năm học phải có dạng 2025 - 2026.')

        start_year = int(match.group(1))
        end_year = int(match.group(2))
        if end_year != start_year + 1:
            raise forms.ValidationError('Năm học phải gồm 2 năm liên tiếp, ví dụ 2025 - 2026.')

        normalized_name = f'{start_year} - {end_year}'
        duplicated = AcademicYear.objects.filter(name=normalized_name)
        if self.instance.pk:
            duplicated = duplicated.exclude(pk=self.instance.pk)
        if duplicated.exists():
            raise forms.ValidationError('Năm học này đã tồn tại.')

        return normalized_name

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.')
            return cleaned_data

        if name and start_date and end_date:
            year_match = re.fullmatch(r'(\d{4})\s*-\s*(\d{4})', name)
            if year_match:
                start_year = int(year_match.group(1))
                end_year = int(year_match.group(2))
                if start_date.year != start_year:
                    self.add_error(
                        'start_date',
                        f'Ngày bắt đầu của năm học {name} phải nằm trong năm {start_year}.',
                    )
                if end_date.year != end_year:
                    self.add_error(
                        'end_date',
                        f'Ngày kết thúc của năm học {name} phải nằm trong năm {end_year}.',
                    )
                if start_date < date(start_year, 1, 1) or end_date > date(end_year, 12, 31):
                    self.add_error(
                        'start_date',
                        f'Thời gian năm học {name} phải nằm trong khoảng năm {start_year} đến {end_year}.',
                    )

        if start_date and end_date and self.instance.pk:
            outside_semester = (
                self.instance.semesters
                .filter(start_date__lt=start_date)
                .order_by('start_date')
                .first()
            ) or (
                self.instance.semesters
                .filter(end_date__gt=end_date)
                .order_by('-end_date')
                .first()
            )
            if outside_semester:
                self.add_error(
                    'start_date',
                    f'Khoảng năm học phải bao phủ tất cả học kỳ hiện có. {outside_semester} đang nằm ngoài khoảng mới.',
                )

        if start_date and end_date:
            overlapping_year = (
                AcademicYear.objects
                .filter(start_date__lte=end_date, end_date__gte=start_date)
                .exclude(pk=self.instance.pk)
                .order_by('-start_date')
                .first()
            )
            if overlapping_year:
                self.add_error(
                    'start_date',
                    f'Thời gian năm học bị trùng với {overlapping_year}.',
                )

        return cleaned_data


class SemesterForm(forms.ModelForm):
    SEMESTER_CHOICES = (
        (1, 'Học kỳ 1'),
        (2, 'Học kỳ 2'),
        (3, 'Học kỳ 3'),
    )

    semester_num = forms.ChoiceField(
        choices=SEMESTER_CHOICES,
        label='Học kỳ',
        widget=forms.Select(attrs={'class': 'form-control'}),
        error_messages={'required': 'Vui lòng chọn học kỳ.'},
    )

    class Meta:
        model = Semester
        fields = ['academic_year', 'semester_num', 'start_date', 'end_date', 'is_active']
        labels = {
            'academic_year': 'Năm học',
            'start_date': 'Ngày bắt đầu',
            'end_date': 'Ngày kết thúc',
            'is_active': 'Đang áp dụng',
        }
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'},
            ),
            'end_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'},
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].queryset = AcademicYear.objects.order_by('-start_date')
        self.fields['academic_year'].empty_label = '-- Chọn năm học --'
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        self.fields['academic_year'].error_messages['required'] = 'Vui lòng chọn năm học.'
        self.fields['start_date'].error_messages['required'] = 'Vui lòng nhập ngày bắt đầu.'
        self.fields['end_date'].error_messages['required'] = 'Vui lòng nhập ngày kết thúc.'

    def clean_semester_num(self):
        return int(self.cleaned_data['semester_num'])

    def clean(self):
        cleaned_data = super().clean()
        academic_year = cleaned_data.get('academic_year')
        semester_num = cleaned_data.get('semester_num')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        missing_previous_numbers = []

        if academic_year and semester_num:
            for number in range(1, semester_num):
                previous_semester = Semester.objects.filter(
                    academic_year=academic_year,
                    semester_num=number,
                )
                if self.instance.pk:
                    previous_semester = previous_semester.exclude(pk=self.instance.pk)
                if not previous_semester.exists():
                    missing_previous_numbers.append(number)

            if missing_previous_numbers:
                missing_labels = ', '.join(f'HK{number}' for number in missing_previous_numbers)
                self.add_error(
                    'semester_num',
                    f'Cần tạo {missing_labels} trước khi tạo HK{semester_num}.',
                )

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.')

        if start_date and end_date and start_date <= end_date and semester_num:
            semester_start_monday = start_date - timedelta(days=start_date.weekday())
            semester_end_sunday = end_date + timedelta(days=6 - end_date.weekday())
            week_count = (semester_end_sunday - semester_start_monday).days // 7 + 1

            if semester_num in (1, 2) and not (10 <= week_count <= 15):
                self.add_error(
                    'end_date',
                    f'Học kỳ {semester_num} phải kéo dài từ 10 đến 15 tuần. Thời gian hiện tại là {week_count} tuần',
                )

            if semester_num == 3 and not (6 <= week_count <= 9):
                self.add_error(
                    'end_date',
                    f'Học kỳ 3 phải kéo dài từ 6 đến 9 tuần. Thời gian hiện tại là {week_count} tuần',
                )

        if academic_year and start_date and end_date:
            if start_date < academic_year.start_date or end_date > academic_year.end_date:
                self.add_error(
                    'start_date',
                    'Thời gian học kỳ phải nằm trong khoảng thời gian của năm học',
                )

            if start_date <= end_date and not missing_previous_numbers:
                overlapping_semesters = Semester.objects.filter(
                    academic_year=academic_year,
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                )
                if self.instance.pk:
                    overlapping_semesters = overlapping_semesters.exclude(pk=self.instance.pk)

                overlapping_semester = overlapping_semesters.first()
                if overlapping_semester:
                    self.add_error(
                        'start_date',
                        f'Thời gian học kỳ bị trùng với {overlapping_semester}',
                    )

                if semester_num and not overlapping_semester:
                    previous_semesters = Semester.objects.filter(
                        academic_year=academic_year,
                        semester_num__lt=semester_num,
                        end_date__gte=start_date,
                    )
                    next_semesters = Semester.objects.filter(
                        academic_year=academic_year,
                        semester_num__gt=semester_num,
                        start_date__lte=end_date,
                    )
                    if self.instance.pk:
                        previous_semesters = previous_semesters.exclude(pk=self.instance.pk)
                        next_semesters = next_semesters.exclude(pk=self.instance.pk)

                    previous_semester = previous_semesters.order_by('-semester_num').first()
                    if previous_semester:
                        self.add_error(
                            'start_date',
                            f'Học kỳ {semester_num} phải bắt đầu sau {previous_semester}',
                        )

                    next_semester = next_semesters.order_by('semester_num').first()
                    if next_semester:
                        self.add_error(
                            'end_date',
                            f'Học kỳ {semester_num} phải kết thúc trước {next_semester}',
                        )

        if academic_year and semester_num:
            duplicated = Semester.objects.filter(
                academic_year=academic_year,
                semester_num=semester_num,
            )
            if self.instance.pk:
                duplicated = duplicated.exclude(pk=self.instance.pk)
            if duplicated.exists():
                self.add_error('semester_num', 'Học kỳ này đã tồn tại trong năm học đã chọn.')

        return cleaned_data
