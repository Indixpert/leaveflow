from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    manager = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_department'
    )

    def __str__(self):
        return self.name

class User(AbstractUser):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', _('Full-Time')
        PART_TIME = 'PART_TIME', _('Part-Time')
        CONTRACTOR = 'CONTRACTOR', _('Contractor')

    email = models.EmailField(_('email address'), unique=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_to'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.get_full_name() or self.email
