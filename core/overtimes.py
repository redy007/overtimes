from django.conf import settings
from datetime import timedelta, datetime, time
from django.utils.dateparse import parse_datetime
import holidays
import inspect

from core.models import Project

# where employees actually works
OFFSHORE = getattr(settings, "OFFSHORE", None)

class ManageOvertimes():
    """
    It's whole business logic here. The class computes overtimes, on calls and call outs.
    """
    def __init__(self, overtime_date_start, overtime_date_end, operationType, projectName):
        self.time_spend_weekday = timedelta(0) 
        self.time_spend_weekend = timedelta(0) 
        self.time_spend_night = timedelta(0) 
        self.time_spend_holiday = timedelta(0) 
        self.d1 = parse_datetime(overtime_date_start).date()  # start date
        self.d2 = parse_datetime(overtime_date_end).date()  # end date
        self.delta = self.d2 - self.d1         # timedelta
        self.overtime_date_start = parse_datetime(overtime_date_start)
        self.overtime_date_end = parse_datetime(overtime_date_end)
        self.operationType = operationType

        self.projectSettings = Project.objects.get(project_name=projectName)

    @staticmethod
    def time_until_end_of_day(dt=None):
        # type: (datetime.datetime) -> datetime.timedelta
        """
        Get timedelta until end of day on the datetime passed, or current time.
        """
        if dt is None:
            dt = datetime.now()
        tomorrow = dt + timedelta(days=1)
        return datetime.combine(tomorrow, time.min) - dt

    @staticmethod
    def is_night_shift(start, end, x):
        """Return true if x is in the range [start, end]"""
        if start <= end:
            return start <= x <= end
        else:
            return start <= x or x <= end
    
    @staticmethod
    def first_day_oncall(on_call_starts, overtime_date_end, on_call_ends, overtime_date_start):
        if on_call_starts <= overtime_date_end and on_call_ends <= overtime_date_start:
            # afternoon
            use_time_begins = on_call_starts if on_call_starts >= overtime_date_start else overtime_date_start
            # use_time_ends = overtime_date_end
            # sum time
            return ManageOvertimes.time_until_end_of_day(use_time_begins)
    
    @staticmethod
    def duty(on_call_starts, overtime_date_end, on_call_ends, overtime_date_start):
        """Comupte function - how much spend in action"""
        time_spend = timedelta(0) 
        print('on_call_starts: ', on_call_starts,
            'overtime_date_end: ' , overtime_date_end, 
            'on_call_ends: ' , on_call_ends, 
            'overtime_date_start: ', overtime_date_start)
        # is morning or afternoon?
        if on_call_starts <= overtime_date_end and on_call_ends <= overtime_date_start:
            # afternoon
            use_time_begins = on_call_starts if on_call_starts >= overtime_date_start else overtime_date_start
            use_time_ends = overtime_date_end
            # sum time
            time_spend += use_time_ends - use_time_begins

        elif on_call_starts >= overtime_date_end and on_call_ends >= overtime_date_start:
            # morning
            use_time_begins = overtime_date_start
            use_time_ends = on_call_ends if on_call_ends <= overtime_date_end else overtime_date_end
            #sum time
            time_spend += use_time_ends - use_time_begins

        elif on_call_ends >= overtime_date_start and on_call_starts <= overtime_date_end:
            # cross the day
            time_spend += on_call_ends - overtime_date_start
            time_spend += overtime_date_end - on_call_starts
        
        return time_spend

    def exec_main(self):

        # TODO: Enable follow customer's vacation

        # https://pypi.org/project/holidays/
        print('tady jsem')
        print(self.projectSettings.country)
        customers_holidays = holidays.CountryHoliday(self.projectSettings.country) if self.projectSettings.follow_holidays else False
        # cz_holidays = holidays.CZ()
        cz_holidays = holidays.CountryHoliday(OFFSHORE)
        for i in range(self.delta.days + 1):
            x_day = self.d1 + timedelta(days=i)
            # od kolik do kolika je pohotovost?
            # it's database time field
            on_call_starts = datetime.combine(x_day, self.projectSettings.on_call_begins) 
            on_call_ends = datetime.combine(x_day, self.projectSettings.on_call_ends)
            # for ManageOvertimes.is_night_shift()
            night_time_start = datetime.combine(x_day, time(22, 0, 0))
            night_time_end = datetime.combine(x_day, time(6, 0, 0))
            # je to prvni nebo posledni den pohotovosti?
            # je pohotovost drzena pouze jeden den (par hodin)?
            if self.d1 == self.d2:
                if self.operationType == 'OUT' or self.operationType == 'OVER':
                    if ManageOvertimes.is_night_shift(night_time_start, night_time_end, self.overtime_date_start) or ManageOvertimes.is_night_shift(night_time_start, night_time_end, self.overtime_date_end):
                        self.time_spend_night += ManageOvertimes.duty(night_time_start, self.overtime_date_end, self.overtime_date_start, self.overtime_date_start)
                
                if x_day.weekday() <= 5:
                    self.time_spend_weekday += ManageOvertimes.duty(on_call_starts, self.overtime_date_end, on_call_ends, self.overtime_date_start)
                if x_day in cz_holidays:
                    self.time_spend_holiday += ManageOvertimes.duty(on_call_starts, self.overtime_date_end, on_call_ends, self.overtime_date_start)
                elif x_day.weekday() >= 5:
                    self.time_spend_weekend += ManageOvertimes.duty(None, self.overtime_date_end, None, self.overtime_date_start)
            
            elif x_day == self.d1:
                # first day // perhaps it starts from 17h
                # need to add different end =>  to 24 or 00??
                # night = datetime.combine(x_day, time.max)
                tomorrow = x_day + timedelta(days=1)
                night = datetime.combine(tomorrow, time.min)
                if self.operationType == 'OUT' or self.operationType == 'OVER':
                    if ManageOvertimes.is_night_shift(night_time_start, night_time_end, self.overtime_date_start) or ManageOvertimes.is_night_shift(night_time_start, night_time_end, self.overtime_date_end):
                        self.time_spend_night += ManageOvertimes.duty(night_time_start, night, self.overtime_date_start, self.overtime_date_start)
                # def duty(on_call_starts, overtime_time_end, on_call_ends, overtime_date_start, nightCheck=False):
                if x_day.weekday() <= 5:
                    # muzu zacit, kdyz bezi odpoledni (od 17h)
                    # vim, ze je to prvni den, ale na druhou stranu potrebuji generickou tridu
                    self.time_spend_weekday += ManageOvertimes.first_day_oncall(on_call_starts, night, on_call_ends, self.overtime_date_start)
                    # duty(on_call_starts, night, on_call_ends, overtime_time_start)
                if x_day in cz_holidays:
                    self.time_spend_holiday += ManageOvertimes.duty(on_call_starts, night, on_call_ends, self.overtime_date_start)
                elif x_day.weekday() >= 5:
                    self.time_spend_weekend += ManageOvertimes.duty(on_call_starts, night, on_call_ends, self.overtime_date_start)
                
            elif x_day == self.d2:
                # last day // perhaps it ends at 9 am
                # need to change start => fromm 00 or ??
                morning = datetime.combine(x_day, time.min)
                if self.operationType == 'OUT' or self.operationType == 'OVER':
                    if ManageOvertimes.is_night_shift(night_time_start, night_time_end, self.overtime_date_start) or ManageOvertimes.is_night_shift(night_time_start, night_time_end, self.overtime_date_end):
                        self.time_spend_night += ManageOvertimes.duty(night_time_start, self.overtime_date_end, self.overtime_date_start, morning)
                if x_day.weekday() <= 5:
                    self.time_spend_weekday += ManageOvertimes.duty(on_call_starts, self.overtime_date_end, on_call_ends, morning)
                if x_day in cz_holidays:
                    self.time_spend_holiday += ManageOvertimes.duty(on_call_starts, self.overtime_date_end, on_call_ends, morning)
                elif x_day.weekday() >= 5: 
                    self.time_spend_weekend += ManageOvertimes.duty(None, self.overtime_date_end, None, morning)
            else:
                # between days d1 and d2
                # from 00 to 24 hours so it's cross day, but I need to put diff hours to duty()
                night = datetime.combine(x_day, time.max)
                morning = datetime.combine(x_day, time.min)
                # all(inspect.isclass(customers_holidays), x_day in customers_holidays)
                # TODO: if someone start at 2 pm and needs to start at 1 pm due to training
                # then the overtime will be counted as 0, but still the request is ok
                # need to be changed 
                if self.operationType == 'OUT' or self.operationType == 'OVER':
                    if ManageOvertimes.is_night_shift(night_time_start, night_time_end, self.overtime_date_start) or ManageOvertimes.is_night_shift(night_time_start, night_time_end, overtime_date_end):
                        self.time_spend_night += timedelta(hours=8)
                if x_day.weekday() <= 5:
                    self.time_spend_weekday += timedelta(hours=13)
                if x_day in cz_holidays and x_day.weekday() >= 5:
                    self.time_spend_holiday += timedelta(hours=24)
                elif x_day in cz_holidays:
                    # we're workin' as normal business day
                    self.time_spend_holiday += ManageOvertimes.duty(on_call_starts, night, on_call_ends, morning)
                elif x_day.weekday() >= 5:
                    self.time_spend_weekend += timedelta(hours=24)
        return (
            self.time_spend_weekday,
            self.time_spend_weekend,
            self.time_spend_night,
            self.time_spend_holiday
        )
                    