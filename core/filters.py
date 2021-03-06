from django.db.models import Sum
import django_filters
from core.models import Overtimes

class OvertimesFilter(django_filters.FilterSet):
    overtime_date_start = django_filters.DateFilter(lookup_expr=('gt'), label='Overtime is greater (mm/dd/yyyy):')
    overtime_date_end = django_filters.DateFilter(lookup_expr=('lt'), label='Overtime is less (mm/dd/yyyy):')
    overtimes_created = django_filters.DateRangeFilter(label='Overtime logged in:')
    operation = django_filters.ChoiceFilter(choices=Overtimes.OPERATIONS)
    who_saved = django_filters.CharFilter(label='User', method='foreign_key_user')

    class Meta:
        model = Overtimes
        fields = ['overtime_date_start', 'overtime_date_end', 'project', 'operation', 'owner', 'overtimes_created']
    
    def foreign_key_user(self, queryset, name, value):
        return queryset.filter(who_saved__username=value)

    @property
    def sum_weekday(self):
        qs = super(OvertimesFilter, self).qs

        return qs.aggregate(Sum('time_spend_weekday'))['time_spend_weekday__sum']

    @property
    def sum_weekend(self):
        qs = super(OvertimesFilter, self).qs

        return qs.aggregate(Sum('time_spend_weekend'))['time_spend_weekend__sum']

    @property
    def sum_night(self):
        qs = super(OvertimesFilter, self).qs

        return qs.aggregate(Sum('time_spend_night'))['time_spend_night__sum']

    @property
    def sum_holiday(self):
        qs = super(OvertimesFilter, self).qs

        return qs.aggregate(Sum('time_spend_holiday'))['time_spend_holiday__sum']