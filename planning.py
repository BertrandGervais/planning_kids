from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from date_utils import DR, MONTHS, to_date, is_less_critical


class Garde:
    def __init__(self, who, dr):
        self.who = who
        self.dr = dr

    @property
    def days(self):
        return self.dr.days

    def __repr__(self):
        return f"{self.who}({self.dr})"


class Constraint:
    def __init__(self, name, start, end):
        self.name = name
        self.dr = DR(start, end)

    def overlap(self, other_c):
        return self.dr.overlap(other_c.dr)

    def __repr__(self):
        return f"{self.name} - {self.dr}"


class Scenario:
    def __init__(self, name):
        self.name = name
        self.gardes = []

    @property
    def people(self):
        return list(set([g.who for g in self.gardes]))

    @property
    def nb_days_by_people(self):
        days_by_people = {}
        for who in self.people:
            days = 0
            for g in self.gardes:
                if g.who == who:
                    days += g.days
            days_by_people[who] = days
        return days_by_people

    def add(self, who, start, end):
        g = Garde(who, DR(start, end))
        self.gardes.append(g)

    def overlap(self, who, dr):
        for g in self.gardes:
            if g.who == who and g.dr.overlap(dr):
                return True
        return False

    def overlap_days_list(self, who, dr):
        days = set()
        for g in self.gardes:
            if g.who == who:
                r = g.dr.overlap_range(dr)
                if r is not None:
                    days.update(r.days_list())
        return sorted(days)

    def check_consistency(self):
        for g in self.gardes:
            for other_g in self.gardes:
                if other_g != g and other_g.dr.overlap(g.dr):
                    print('ERROR overlap', g, other_g)
                    return False
        return True

    def check_constraints(self, constraints, holidays=None):
        holidays = holidays or []
        incompatibilites = {}
        for who in constraints:
            assert who in self.people
            incompatibilites[who] = []
        for who, c_list in constraints.items():
            for c in c_list:
                days = self.overlap_days_list(who, c.dr)
                if days:
                    days_moins_critique = [d for d in days if is_less_critical(d, holidays)]
                    days_critique = [d for d in days if d not in days_moins_critique]
                    incompatibilites[who].append((c, days_critique, days_moins_critique))
        return incompatibilites

    def __repr__(self):
        return f"{self.gardes}"

    def merge(self, other_scenario):
        assert len(self.people) == 0 or self.people == other_scenario.people
        new_gardes = self.gardes
        for other_garde in other_scenario.gardes:
            assert not self.overlap(other_garde.who, other_garde.dr)
            new_gardes.append(other_garde)
        self.gardes = new_gardes


def scenario_repr(s, year):
    repr = ""
    for month in range(1, 12+1):
        m_str = MONTHS[month]
        m_start = date(year=year, month=month, day=1)
        m_dr = DR(m_start, m_start + relativedelta(months=1))
        month_gardes = []
        for g in s.gardes:
            if g.dr.start in m_dr:
                month_gardes.append(g)
        repr_gardes = " - ".join(
            [f"{g.who}({g.dr.start.day}-{g.dr.end.day})" for g in month_gardes]
        )
        repr += f"{m_str}: {repr_gardes}\r\n"
    return repr


def create_simple_scenario(name, start, end, who_starts, who_other):
    start = to_date(start)
    assert start.isoweekday() == 5  # Friday
    end = to_date(end)
    assert start <= end
    week = timedelta(days=7)
    scenario = Scenario(name)
    d = start
    who = who_starts
    while d < end:
        scenario.add(who, d, d + week - timedelta(days=1))
        d += week
        if who == who_starts:
            who = who_other
        else:
            who = who_starts
    return scenario


def create_complex_scenario(name, simple_scenario_params):
    scenario = Scenario(name)
    for s_params in simple_scenario_params:
        s = create_simple_scenario("", *s_params)
        scenario.merge(s)
    return scenario
