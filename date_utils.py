from datetime import date, timedelta

DAYS = {
    1: "Lu",
    2: "Ma",
    3: "Me",
    4: "Je",
    5: "Ve",
    6: "Sa",
    7: "Di",
}

MONTHS = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre",
}

WEEKEND_ISOWEEKDAYS = (5, 6, 7)  # Ve, Sa, Di


def date_repr(d):
    day_str = DAYS[d.isoweekday()]
    return f"{d}-{day_str}"


def to_date(value):
    if isinstance(value, date):
        return value
    elif isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError


class DR:
    def __init__(self, start, end):
        self.start = to_date(start)
        self.end = to_date(end)
        assert self.start <= self.end

    @property
    def days(self):
        td = self.end - self.start
        return td.days

    def __contains__(self, d):
        assert isinstance(d, date)
        return self.start <= d and d <= self.end

    def overlap(self, dr):
        return self.start <= dr.end and dr.start <= self.end

    def overlap_range(self, dr):
        if not self.overlap(dr):
            return None
        start = max(self.start, dr.start)
        end = min(self.end, dr.end)
        return DR(start, end)

    def days_list(self):
        nb_days = (self.end - self.start).days + 1
        return [self.start + timedelta(days=i) for i in range(nb_days)]

    def __repr__(self):
        return f"{date_repr(self.start)} - {date_repr(self.end)}"


def in_holidays(d, holidays):
    for _, dr in holidays:
        if d in dr:
            return True
    return False


def is_less_critical(d, holidays):
    return in_holidays(d, holidays) and d.isoweekday() in WEEKEND_ISOWEEKDAYS


def max_consecutive_days(days):
    if not days:
        return 0
    days = sorted(days)
    max_run = current_run = 1
    for prev, curr in zip(days, days[1:]):
        if (curr - prev).days == 1:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1
    return max_run
