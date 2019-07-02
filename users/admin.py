from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm


def make_manager(modeladmin, request, queryset):
    """ Manager can CRUD accounts """
    queryset.update(is_manager=True, is_staff=True)

make_manager.short_description = 'Promote user as manager'

def make_employee(modeladmin, request, queryset):
    """ Every active user can add overtimes, this is more for future use """
    queryset.update(is_employee=True, is_staff=True)

make_employee.short_description = 'Promote user as employee'

def make_superuser(modeladmin, request, queryset):
    """ The superuser can go to admin interface and set another users as wish """
    queryset.update(is_superuser=True, is_staff=True)

make_superuser.short_description = 'Promote user as superuser'

def disable_user(modeladmin, request, queryset):
    """ If user is not staff, then is not allowed to add overtime  """
    queryset.update(is_staff=False)

disable_user.short_description = 'Disable user'

class CustomUserAdmin(UserAdmin):
    """
    Admin user interface => Users->Users
    """
    model = User
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'is_employee', 'is_manager')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
)

    list_display = ('username', 'first_name', 
                    'last_name', 'is_employee', 'is_manager', 
                    'is_staff', 'is_superuser')
    actions = [make_manager, make_employee, make_superuser, disable_user]

admin.site.register(User, CustomUserAdmin)


# admin.site.register(User)