from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Field, Layout
from datetime import timedelta

from core.models import Overtimes, Project
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from users.models import User



from .overtimes import ManageOvertimes

class OvertimesForm(forms.ModelForm):
    operation = forms.ChoiceField(choices=Overtimes.OPERATIONS)
    # https://stackoverflow.com/questions/51326314/changing-field-in-django-form-overriding-clean
    # overtime_date_start = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M'])
    # overtime_date_end = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M'])

    class Meta:
        model = Overtimes
        fields = (
            'overtime_date_start',
            'overtime_date_end',
            'operation',
            'project',
            'comment',
        )
        widgets = {
            'comment': forms.Textarea(attrs={'cols': 20, 'rows': 1}),
            'overtime_date_start': forms.HiddenInput(),
            'overtime_date_end': forms.HiddenInput()
        }


    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        self.overtime_date_start = kwargs.pop('overtime_date_start', None)
        self.overtime_date_end = kwargs.pop('overtime_date_end', None)
        super(OvertimesForm, self).__init__(*args, **kwargs)

    def clean(self):
        self.cleaned_data = super(OvertimesForm, self).clean()
        print('test call out')
        print(self.cleaned_data.get('operation'))
        # callout could be done only when employee has overtime logged in
        if self.cleaned_data.get('operation') == 'OUT':
            is_oncall = Overtimes.objects.filter(
                owner=self.owner, 
                overtime_date_start__gte=self.overtime_date_start, 
                overtime_date_end__lte=self.overtime_date_end
            ).exists()

            if is_oncall is False:
                print('is_oncall is NOK')
                raise forms.ValidationError("Call out was requested, but without On call")
            else:
                print('is_oncall is OK')

        return self.cleaned_data

    def save(self, overtime_date_start, overtime_date_end, obj, commit=True):
        time_spend_weekday = timedelta(0)
        time_spend_weekend = timedelta(0)
        time_spend_night = timedelta(0)
        time_spend_holiday = timedelta(0)

        overtime = ManageOvertimes(
            overtime_date_start,
            overtime_date_end,
            self.cleaned_data.get('operation'),
            self.cleaned_data.get('project')
        )
        time_spend_weekday, time_spend_weekend, time_spend_night, time_spend_holiday = overtime.exec_main() 

        if obj is None:
            obj = Overtimes()
            owner = self.owner
            updater = None
        else:
            owner = obj.owner
            updater = self.owner

        obj.project = self.cleaned_data.get('project')
        obj.operation = self.cleaned_data.get('operation')
        obj.time_spend_weekday = time_spend_weekday
        obj.time_spend_weekend = time_spend_weekend
        obj.time_spend_night = time_spend_night
        obj.time_spend_holiday = time_spend_holiday
        obj.overtime_date_start = overtime_date_start
        obj.overtime_date_end = overtime_date_end
        obj.owner = owner
        obj.updater = updater
        obj.save()
        return obj

class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = (
            "project_name",
            "is_active",
            "on_call_ends",
            "on_call_begins",
            'country',
            'follow_holidays',
            'owner'
        )
    
    def __init__(self,*args,**kwargs):
        super (ProjectForm,self ).__init__(*args,**kwargs) # populates the post
        self.fields['owner'].queryset = User.objects.filter(is_manager=True)
        self.fields['owner'].required = False
