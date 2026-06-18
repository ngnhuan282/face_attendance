from datetime import timedelta

from django import forms

from .models import AcademicYear, Semester


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
