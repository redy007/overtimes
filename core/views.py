import csv
from datetime import datetime

from django.contrib import messages
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View, UpdateView, DeleteView
from django.contrib.auth import get_user_model
from django_filters.views import FilterView

from core.filters import OvertimesFilter
from core.models import Overtimes, Project
from core.forms import OvertimesForm, ProjectForm

User = get_user_model()

class OwnerRequiredMixin():
    """
    Only owner or superuser can delete the record.
    """
    def dispatch(self, request, *args, **kwargs):
        # https://stackoverflow.com/questions/52673974/django-2-1-deleteview-only-owner-can-delete-or-redirect
        self.object = self.get_object()
        if self.object.owner != self.request.user or self.request.user.is_superuser is False:
            messages.error(request, "You're not allowed to modify the record.")
            return HttpResponseForbidden()
        return super(OwnerRequiredMixin, self).dispatch(request, *args, **kwargs)

@login_required
def addOvertime(request):
    form = OvertimesForm

    if request.method == 'POST':
        overtime_date_start = request.POST['overtime_date_start']
        overtime_date_end = request.POST['overtime_date_end']
        form = OvertimesForm(request.POST, owner=request.user, overtime_date_start=overtime_date_start, overtime_date_end=overtime_date_end)
        if form.is_valid():
            # grab values from form inputs          
            # I am adding date into overtime_date_start, overtime_date_end
            # that's why I am not allowed to use cleaned_data method
            # because the format is not same
            # form = OvertimesForm(request.POST, owner=request.user, overtime_date_start=overtime_date_start, overtime_date_end = overtime_date_end)
            form.save(overtime_date_start, overtime_date_end, obj=None)

            return redirect("home")

            # print(form.errors)
            # print(form.non_field_errors)
        else:
            print(form.non_field_errors)
            print(form.errors)
            messages_text = 'Call out was requested, but without On call'
            messages.error(request, messages_text)
    return render(request, 'form.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class OvertimeUpdateView(OwnerRequiredMixin, UpdateView):
    model = Overtimes
    template_name = 'form.html'
    form_class = OvertimesForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update overtime:'
        return context

    def form_valid(self, form):
        # grab values from form inputs

        # I am adding date into overtime_date_start, overtime_date_end
        # that's why I am not allowed to use cleaned_data method
        # because the format is not same
        overtime_date_start = self.request.POST['overtime_date_start']
        overtime_date_end = self.request.POST['overtime_date_end']

        form = OvertimesForm(self.request.POST, owner=self.request.user, overtime_date_start=overtime_date_start, overtime_date_end=overtime_date_end)
        form.is_valid()
        obj = self.get_object()
        form.save(overtime_date_start, overtime_date_end, obj)

        return redirect("home")

def search(request):
    overtimes_list = Overtimes.objects.all()
    overtimes_filter = OvertimesFilter(request.GET, queryset=overtimes_list)
    # print(overtimes_filter.__dict__)
    return render(request, 'overtimes_search.html', {'filter': overtimes_filter})

class OvertimesExportView(FilterView):
    """
    Export data to csv based on django-filters query
    """
    filterset_class = OvertimesFilter

    def render_to_response(self, context, **response_kwargs):
        filename = "{}-export.csv".format(datetime.now().replace(microsecond=0).isoformat())

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

        writer = csv.writer(response)
        writer.writerow([
            'overtime_date_start',
            'overtime_date_end',
            'project',
            'owner',
            'activity',
            'time spend',
            'weekend',
            'holidays',
            'night',
            'comment'
        ])

        for obj in self.object_list:
            writer.writerow([obj.overtime_date_start,
                obj.overtime_date_end,
                obj.project,
                obj.owner,
                obj.operation,
                obj.time_spend_weekday,
                obj.get_time_spend_weekend,
                obj.get_time_spend_holiday,
                obj.get_time_spend_night,
                obj.comment
            ])
            
        return response


class IndexView(View):
    form = OvertimesForm()
    today = datetime.now()
    def get(self, request, *args, **kwargs):
        self.form = OvertimesForm(owner=request.user)
        if request.user.is_anonymous:
            latest = Overtimes.objects \
                .filter(overtime_date_start__year=self.today.year, overtime_date_start__month=self.today.month) \
                .order_by('overtime_date_start')
        elif request.user.is_superuser:
            latest = Overtimes.objects \
                .filter(overtime_date_start__year=self.today.year, overtime_date_start__month=self.today.month) \
                .order_by('overtime_date_start')
        elif request.user.is_manager:
            latest = Overtimes.objects \
                .filter(overtime_date_start__year=self.today.year, overtime_date_start__month=self.today.month) \
                .order_by('overtime_date_start')
            latest = latest.filter(project__owner__username=request.user)
        elif request.user.is_employee:
            latest = Overtimes.objects \
                .filter(overtime_date_start__year=self.today.year, overtime_date_start__month=self.today.month) \
                .order_by('overtime_date_start')
            latest = latest.filter(who_saved__username=request.user)

        overtimes_list = Overtimes.objects.all()
        overtimes_filter = OvertimesFilter(request.GET, queryset=overtimes_list)
        context = {
            'latest': latest,
            'filter': overtimes_filter,
            'form': self.form
        }
        return render(request, 'index.html', context)

@login_required
def addProject(request):
    '''
    The view manages Customer's project and its settings
    '''
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.owner = request.user
            form.save()
            return redirect("home")

        else:
            print(form.errors)
            print(form.non_field_errors)

    project_form = ProjectForm
    # project_form = ProjectForm(initial={'owner':request.user})
    return render(request, 'project.html', {
        'form': project_form
    })

class MyProjects(View):

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            latest = Project.objects.all() \
                .order_by('created_date')
        else:
            latest = Project.objects \
                .filter(owner=request.user) \
                .order_by('created_date')

        context = {
            'latest': latest
        }
        return render(request, 'project_table.html', context)

def get_user(user):
    qs = User.objects.filter(username=user)
    if qs.exists:
        return qs[0]
    return None

@method_decorator(login_required, name='dispatch')
class ProjectUpdateView(UpdateView):
    model = Project
    template_name = 'project.html'
    form_class = ProjectForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update account:'
        return context

    def form_valid(self, form):
        form.instance.owner = get_user(self.request.user)
        form.save()
        return redirect("myprojects")

@method_decorator(login_required, name='dispatch')
class OvertimeDeleteView(OwnerRequiredMixin, DeleteView):
    model = Overtimes
    success_url = '/'
    template_name = 'post_confirm_delete.html'

    def post_delete(self, request, id):
        object = get_object_or_404(Overtimes, id=id)
        object.delete()
        return redirect(reverse("home"))
