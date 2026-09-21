from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    USER = "user", "User"
    ADMIN = "admin", "Admin"


class User(AbstractUser):
    """RBAC のための role を持つユーザー。

    Django 標準の is_staff / is_superuser は管理画面用の権限なので、
    API の認可には使わず、アプリケーション上の役割として role を持たせる。
    """

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.USER)

    @property
    def is_admin_role(self) -> bool:
        return self.role == Role.ADMIN
