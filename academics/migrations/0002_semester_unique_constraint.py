from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='semester',
            constraint=models.UniqueConstraint(
                fields=('academic_year', 'semester_num'),
                name='uniq_semester_per_academic_year',
            ),
        ),
    ]
