import calendar

def year_options(queryset, date_field = 'date', max = None):
    if not queryset:
        return []
    queryset = queryset.order_by('-' + date_field)
    if not queryset.count():
        return []
    latest = getattr(queryset[0], date_field)
    oldest = getattr(queryset.reverse()[0], date_field)
    years = range(oldest.year, latest.year+1)
    for year in years:
        if year in [latest.year, oldest.year]:
            continue
        d = {date_field + '__year':year}
        if not queryset.filter(**d):
            years.remove(year)
    if max and len(years) > max:
        years = years[-max:]
    return years

def month_options(queryset, year, date_field = 'date'):
    queryset = queryset.filter(date__year=year).order_by('-' + date_field)
    if not queryset.count():
        return []
    months = [i+1 for i in range(12)]
    for month in list(months):
        d = {date_field + '__month':month}
        if not queryset.filter(**d).count():
            months.remove(month)
    return months

def day_options(queryset, year, month, date_field = 'date'):
    queryset = queryset.filter(date__year=year, date__month=month).order_by('-' + date_field)
    if not queryset.count():
        return []
    days = [i+1 for i in range(max(max(calendar.monthcalendar(year, month))))]
    for day in list(days):
        d = {date_field + '__day':day}
        if not queryset.filter(**d).count():
            days.remove(day)
    return days
