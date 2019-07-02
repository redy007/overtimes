from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django_filters.views import FilterView
from core.filters import OvertimesFilter

import django_saml2_auth.views

from core.views import (
    IndexView,
    MyProjects,
    ProjectUpdateView,
    addOvertime,
    OvertimeUpdateView,
    OvertimeDeleteView,
    addProject,
    search
)

urlpatterns = [
    # TODO: authentication for https://django-auth-adfs.readthedocs.io/en/latest/demo.html

    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='home'),
    path('add_overtime', addOvertime, name='add_overtime'),
    path('update_overtime/<int:pk>/', OvertimeUpdateView.as_view(), name='update_overtime'),
    path('delete_overtime/<int:pk>/', OvertimeDeleteView.as_view(), name='delete_overtime'),
    path('add_project', addProject, name='add_project'),
    path('myprojects', MyProjects.as_view(), name='myprojects'),
    path('update_project/<slug:slug>/', ProjectUpdateView.as_view(), name='update_project'),
    # path('search/', FilterView.as_view(filterset_class=OvertimesFilter,
    #    template_name='overtimes_search.html'), name='search'),
    path('search/', search, name='search'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
