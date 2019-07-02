from django.db import models
from django.urls import reverse
from django.template.defaultfilters import slugify
from django_countries.fields import CountryField
from django.contrib.auth import get_user_model

import datetime
from datetime import timedelta

User = get_user_model()

class Project(models.Model):
    project_name = models.CharField(max_length=50, primary_key=True)
    # who owns the project?
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    created_date = models.DateTimeField(auto_now=False, auto_now_add=True)
    is_active = models.BooleanField(default=True)
    ## when on call starts 5 pm?
    on_call_begins = models.TimeField(auto_now=False, auto_now_add=False, default=datetime.time(17, 00))
    ## when on call ends 9 am?
    on_call_ends = models.TimeField(auto_now=False, auto_now_add=False, default=datetime.time(9, 00))
    country = CountryField()
    follow_holidays = models.BooleanField(default=True)
    slug = models.SlugField()
    

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.project_name

    def get_absolute_url(self):
        return reverse("Project_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.project_name)
        super(Project, self).save(*args, **kwargs)

class ProjectSettings(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "ProjectSettings"
        verbose_name_plural = "ProjectSettingss"

    def __str__(self):
        return self.project

    def get_absolute_url(self):
        return reverse("ProjectSettings_detail", kwargs={"pk": self.pk})



# Create your models here.
class Overtimes(models.Model):
    ONCALL = 'ON'
    CALLOUT = 'OUT'
    OVERTIME = 'OVER'
    OPERATIONS = [
        (ONCALL, 'On call'),
        (CALLOUT, 'Call out'),
        (OVERTIME, 'Overtime'),
    ]

    overtime_date_start = models.DateTimeField(auto_now=False, auto_now_add=False)
    # ends in the end of each day
    overtime_date_end = models.DateTimeField(auto_now=False, auto_now_add=False)
    # operation
    operation = models.CharField(
        max_length=4,
        choices=OPERATIONS,
        default=ONCALL,
    )
    # who to properly do foreignKey with on_delete is null
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    # auto compute
    time_spend_weekday = models.DurationField(null=True, blank=True)
    time_spend_weekend = models.DurationField(null=True, blank=True)
    time_spend_night = models.DurationField(null=True, blank=True)
    time_spend_holiday = models.DurationField(null=True, blank=True)
    # could be null
    comment = models.TextField(null=True, blank=True)
    # when written down
    overtimes_created = models.DateTimeField(auto_now=False, auto_now_add=True)
    owner = models.ForeignKey(User, related_name='user_owner', on_delete=models.PROTECT)
    updater = models.ForeignKey(User, related_name='user_updater', on_delete=models.PROTECT, null=True, blank=True)

    

    class Meta:
        verbose_name = "Overtimes"
        verbose_name_plural = "Overtimess"

    def __str__(self):
        begins = self.overtime_date_start.strftime("%Y/%m/%d %H:%M")
        end = self.overtime_date_end.strftime("%Y/%m/%d %H:%M")
        return  begins + ' ' +  end + ' ' + dict(Overtimes.OPERATIONS)[self.operation]

    def get_absolute_url(self):
        return reverse("Overtimes_detail", kwargs={"pk": self.pk})

    def operation_verbose(self):
        return dict(Overtimes.OPERATIONS)[self.operation]

    @property
    def get_time_spend_holiday(self):
        if self.time_spend_holiday != timedelta(0):
              return self.time_spend_holiday
        else:
              return "0"

    @property
    def get_time_spend_night(self):
        if self.time_spend_night != timedelta(0):
              return self.time_spend_night
        else:
              return "0"

    @property
    def get_time_spend_weekend(self):
        if self.time_spend_weekend != timedelta(0):
              return self.time_spend_weekend
        else:
              return "0"
