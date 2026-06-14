# Generated manually for per-user notification read state.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0002_alter_notification_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationRead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('read_at', models.DateTimeField(auto_now_add=True, verbose_name='Đọc lúc')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_receipts', to='notifications.notification', verbose_name='Cảnh báo')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_notifications', to=settings.AUTH_USER_MODEL, verbose_name='Người đọc')),
            ],
            options={
                'verbose_name': 'Trạng thái đọc cảnh báo',
                'verbose_name_plural': 'Trạng thái đọc cảnh báo',
                'ordering': ['-read_at'],
                'unique_together': {('notification', 'user')},
            },
        ),
    ]
