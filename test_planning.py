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
            Constraint("WE Astreinte juillet", "2026-07-03", "2026-07-05"),
            Constraint("WE Astreinte octobre", "2026-10-16", "2026-10-18"),
        ],
        "B": [
            Constraint("Concert", "2026-02-27", "2026-03-01"),
            Constraint("Journee Accessibilité / Paris", "2026-04-14", "2026-04-14"),
            Constraint("Mobco / Paris", "2026-06-09", "2026-06-11"),
            Constraint("SOTM Monde / Paris", "2026-08-28", "2026-08-29"),
            Constraint("GeoDataDays / Tours", "2026-09-16", "2026-09-17"),
            Constraint(
                "Rencontres du Réseau vélo et marche / Nancy",
                "2026-09-30",
                "2026-10-02",
            ),
            Constraint("Journees AGIR / Angers", "2026-10-06", "2026-10-08"),
            Constraint("Smart City Expo / Barcelone", "2026-11-03", "2026-11-05"),
            # Salon maires ?
        ],
    }

    # Divers scenarios de garde
    SCENARIOS = [
        create_simple_scenario(
            "S1 / Année / Commence par B", "2026-01-02", "2026-12-19", "B", "C"
        ),
        create_simple_scenario(
            "S2 / Année / Commence par C", "2026-01-02", "2026-12-19", "C", "B"
        ),
        create_simple_scenario(
            "S3 / Jusquà l'été / Commence par B", "2026-01-02", "2026-07-11", "B", "C"
        ),
        create_simple_scenario(
            "S4 / Jusquà l'été / Commence par C", "2026-01-02", "2026-07-11", "C", "B"
        ),
        create_complex_scenario(
            "S5",
            [
                ("2026-01-02", "2026-07-11", "C", "B"),
                ("2026-08-28", "2026-12-20", "C", "B"),
            ],
        ),
        # create_complex_scenario(
        #     "S6",
        #     [
        #         ("2026-01-02", "2026-07-11", "C", "B"),
        #         ("2026-08-28", "2026-12-20", "B", "C"),
        #     ],
        # ),
        create_complex_scenario(
            "S5 amelioré",
            [
                ("2026-01-02", "2026-07-11", "C", "B"),
                ("2026-08-28", "2026-09-23", "C", "B"),
                ("2026-09-25", "2026-12-20", "B", "C"),
            ],
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
        print(scenario_repr(s, 2026))

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
