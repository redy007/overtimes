from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_manager = models.BooleanField(blank=False)
    is_employee = models.BooleanField(blank=False)

    REQUIRED_FIELDS = ['email', 'is_manager', 'is_employee', 'is_superuser', 'is_staff']

    def __str__(self):
        # return self.first_name + self.last_name
        return self.username
