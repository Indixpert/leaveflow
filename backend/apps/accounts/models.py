from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', _('Full-Time')
        PART_TIME = 'part_time', _('Part-Time')
        CONTRACTOR = 'contractor', _('Contractor')

    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
        help_text="The employment type of the user."
    )
    # Other fields for the custom user might exist here.
