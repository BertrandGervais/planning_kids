from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

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

    def __repr__(self):
        return f"{date_repr(self.start)} - {date_repr(self.end)}"


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

    def check_consistency(self):
        for g in self.gardes:
            for other_g in self.gardes:
                if other_g != g and other_g.dr.overlap(g.dr):
                    print('ERROR overlap', g, other_g)
                    return False
        return True
    
    def check_constraints(self, constraints):
        incompatibilites = {}
        for who in constraints:
            assert who in self.people
            incompatibilites[who] = []
        for who, c_list in constraints.items():
            for c in c_list:
                if self.overlap(who, c.dr):
                    incompatibilites[who].append(c)
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


if __name__ == "__main__":

    # Dates où on sait qu'on ne pourra pas garder les enfants
    CONTRAINTES = {
        "C": [
            Constraint("Concert Olivia Rodrigo", "2027-04-23", "2027-04-23"),        
        ],
        "B": [            
            Constraint("Urbest", "2027-01-13", "2027-01-14"),
            Constraint("Mobco Saint-Étienne", "2027-03-31", "2027-04-01"),
            # Constraint("Bac blanc", "2027-04-05", "2027-04-09"),       
            Constraint("Lanzarote", "2027-04-24", "2027-05-01"),            
            Constraint("UITP Hamburg", "2027-06-14", "2027-06-17"),
            # Constraint("Bac français", "2027-06-15", "2027-06-15"),
            # Constraint("Bac maths", "2027-06-21", "2027-06-21"),
            # Constraint("Oral français", "2027-06-21", "2027-06-30"),
            # Constraint("Brevet", "2027-06-24", "2027-06-28"),

            # Automne 2026 : dates pas encore communiquées
            # POLIS ?
            # RVM ?            
            # GeoDataDays ?
            # Walk21 (Attention, j'essaierai de prendre 2 semaines)
        ],
    }

    # Divers scenarios de garde
    SCENARIOS = [
        create_simple_scenario(
            "S1 / Année / Commence par B", "2027-01-01", "2027-12-17", "B", "C"
        ),
        create_simple_scenario(
            "S2 / Année / Commence par C", "2027-01-01", "2027-12-17", "C", "B"
        ),        
    ]

    # check if respective constraints overlap
    print("******************************************************************")
    print("Contraintes incompatibles")
    print("******************************************************************")
    for who, c_list in CONTRAINTES.items():
        for c in c_list:
            for other_who, other_c_list in CONTRAINTES.items():
                if other_who != who:
                    for other_c in other_c_list:
                        if c.overlap(other_c):
                            print(f"{who}({c}) / {other_who}({other_c})")
    print()

    # check incompatibilites for each scenario
    for s in SCENARIOS:

        print("-------------------------------------------------------------------")
        print(f"Scénario {s.name}")
        print("-------------------------------------------------------------------")
        print(scenario_repr(s, 2027))

        nb_days_by_people = s.nb_days_by_people
        print(
            f"Nombre de jours par personne: B({nb_days_by_people['B']}) C({nb_days_by_people['C']})"
        )
        print()

        print('Vérification de cohérence:')
        s.check_consistency()
        print()

        incompatibilites = s.check_constraints(CONTRAINTES)
        print(
            f"Incompatibilités: B({len(incompatibilites['B'])}) C({len(incompatibilites['C'])})"
        )
        for who, incompats in incompatibilites.items():
            for incompat in incompats:
                print(f"{who}: {incompat}")

        print()
