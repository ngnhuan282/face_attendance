"""
Management command: seed_users
Tạo tài khoản mẫu cho 2 vai trò: Admin và Giảng Viên.

Sử dụng:
    python manage.py seed_users
    python manage.py seed_users --reset   (xoá và tạo lại)
"""
from __future__ import annotations

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME


SEED_USERS = [
    {
        "username":   "admin",
        "password":   "admin123",
        "first_name": "Quản Trị",
        "last_name":  "Viên",
        "email":      "admin@eduface.vn",
        "is_staff":   True,
        "is_superuser": True,
        "group":      ADMIN_GROUP_NAME,
    },
    {
        "username":   "giangvien",
        "password":   "gv123456",
        "first_name": "Nguyễn Văn",
        "last_name":  "Hùng",
        "email":      "hung.nv@eduface.vn",
        "is_staff":   False,
        "is_superuser": False,
        "group":      TEACHER_GROUP_NAME,
    },
]


class Command(BaseCommand):
    help = "Tạo tài khoản mẫu: admin (Quản Trị Viên) và giangvien (Giảng Viên)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Xoá tài khoản seed cũ rồi tạo lại từ đầu.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]

        # Đảm bảo các group tồn tại
        admin_group, _   = Group.objects.get_or_create(name=ADMIN_GROUP_NAME)
        teacher_group, _ = Group.objects.get_or_create(name=TEACHER_GROUP_NAME)
        group_map = {
            ADMIN_GROUP_NAME:   admin_group,
            TEACHER_GROUP_NAME: teacher_group,
        }

        for data in SEED_USERS:
            username = data["username"]

            if reset:
                User.objects.filter(username=username).delete()
                self.stdout.write(f"  [XOA] Da xoa tai khoan cu: {username}")

            user, created = User.objects.get_or_create(username=username)

            if created or reset:
                user.set_password(data["password"])
                user.first_name   = data["first_name"]
                user.last_name    = data["last_name"]
                user.email        = data["email"]
                user.is_staff     = data["is_staff"]
                user.is_superuser = data["is_superuser"]
                user.is_active    = True
                user.save()

                group = group_map[data["group"]]
                user.groups.set([group])

                verb = "[TAO MOI]" if created else "[CAP NHAT]"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  {verb}: {username} / {data['password']}  ->  nhom [{data['group']}]"
                    )
                )
            else:
                self.stdout.write(
                    f"  [DA TON TAI]: {username} (bo qua - dung --reset de ghi de)"
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== seed_users hoan tat ==="))
        self.stdout.write("")
        self.stdout.write("  Tai khoan test:")
        self.stdout.write("    [ADMIN]  admin      / admin123   ->  Quan Tri Vien (superuser)")
        self.stdout.write("    [GV]     giangvien  / gv123456   ->  Giang Vien")
