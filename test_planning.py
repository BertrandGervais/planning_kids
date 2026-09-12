from colors import RED, ORANGE, BLUE, RESET
from date_utils import DR, WEEKEND_ISOWEEKDAYS, date_repr
from planning import Constraint, Evenement, create_simple_scenario, scenario_repr

if __name__ == "__main__":

    # Vacances scolaires zone B (années scolaires 2026-2027 et 2027-2028)
    # source: calendrier officiel education.gouv.fr
    VACANCES_ZONE_B = [
        ("Noël 2026", DR("2026-12-19", "2027-01-03")),
        ("Hiver 2027", DR("2027-02-20", "2027-03-07")),
        ("Printemps 2027", DR("2027-04-17", "2027-05-02")),
        ("Été 2027", DR("2027-07-03", "2027-08-31")),
        ("Toussaint 2027", DR("2027-10-23", "2027-11-07")),
        ("Noël 2027", DR("2027-12-18", "2028-01-02")),
    ]

    # Dates où on sait qu'on ne pourra pas garder les enfants
    CONTRAINTES = {
        "C": [
            Constraint("Concert Olivia Rodrigo", "2027-04-23", "2027-04-23"),
        ],
        "B": [
            Constraint("Urbest", "2027-01-13", "2027-01-14"),
            Constraint("Mobco Saint-Étienne", "2027-03-31", "2027-04-01"),
            Constraint("UITP Hamburg", "2027-06-14", "2027-06-17"),
            # Automne 2026 : dates pas encore communiquées
            # POLIS ?
            # RVM ?
            # GeoDataDays ?
            # Walk21 (Attention, j'essaierai de prendre 2 semaines)
        ],
    }

    EVENEMENTS_ENFANTS = [
        Evenement("Bac blanc Pauline", "2027-04-05", "2027-04-09"),
        Evenement("Lanzarote Bertrand", "2027-04-24", "2027-05-01", "B"),
        Evenement("Anniversaire Pauline", "2027-05-19"),
        Evenement("Bac français Pauline", "2027-06-15", "2027-06-15"),
        Evenement("Bac maths Pauline", "2027-06-21"),
        Evenement("Oral français Pauline", "2027-06-21", "2027-06-30"),
        Evenement("Brevet Axel", "2027-06-24", "2027-06-28"),
        Evenement("Anniversaire Axel", "2027-07-16"),
    ]

    # Divers scenarios de garde
    SCENARIOS = [
        create_simple_scenario(
            "S1 / Année commence par C (Scénario sans changement)",
            "2027-01-01",
            "2027-12-17",
            "C",
            "B",
        ),
        create_simple_scenario(
            "S2 / Année commence par B (Scénario alternatif)",
            "2027-01-01",
            "2027-12-17",
            "B",
            "C",
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

        print("Vérification de cohérence:")
        s.check_consistency()
        print()

        incompatibilites = s.check_constraints(CONTRAINTES, VACANCES_ZONE_B)
        print(
            f"Incompatibilités: B({len(incompatibilites['B'])}) C({len(incompatibilites['C'])})"
        )
        total_overlap_days = 0
        total_overlap_days_moins_critique = 0
        total_overlap_days_critique = 0
        for who, incompats in incompatibilites.items():
            for incompat, days_critique, days_moins_critique in incompats:
                all_days = sorted(days_critique + days_moins_critique)
                days_str = ", ".join(
                    f"{date_repr(d)}{' (peu critique)' if d in days_moins_critique else ''}"
                    for d in all_days
                )
                nb_total = len(all_days)
                nb_moins_critique = len(days_moins_critique)
                nb_critique = len(days_critique)
                critique = nb_critique > 0
                couleur = RED if critique else ORANGE
                print(
                    f"{couleur}{who}: {incompat} - overlap: {nb_total} jours "
                    f"dont {nb_critique} critiques, {nb_moins_critique} peu critiques "
                    f" [{days_str}]{RESET}"
                )
                total_overlap_days += nb_total
                total_overlap_days_moins_critique += nb_moins_critique
                total_overlap_days_critique += nb_critique
        total_couleur = RED if total_overlap_days_critique > 0 else ORANGE
        print(
            f"{total_couleur}Total overlap: {total_overlap_days} jours "
            f"dont {total_overlap_days_critique} critiques, "
            f"{total_overlap_days_moins_critique} peu critiques{RESET}"
        )
        print()

        print("Répartition des enfants pendant les événements:")
        total_jours_evenements = {"B": 0, "C": 0}
        for e in EVENEMENTS_ENFANTS:
            jours_par_personne = s.days_in_range_by_people(e.dr)
            suffix = f" (avec {e.who})" if e.who else ""
            couleur = ""
            if e.who:
                autre_jours = s.other_days_list(e.who, e.dr)
                jours_critique = [d for d in autre_jours if d.isoweekday() not in WEEKEND_ISOWEEKDAYS]
                jours_moins_critique = [d for d in autre_jours if d.isoweekday() in WEEKEND_ISOWEEKDAYS]
                if jours_critique:
                    couleur = RED
                elif jours_moins_critique:
                    couleur = ORANGE
            reset = RESET if couleur else ""
            print(
                f"{BLUE}{e.name}{RESET}{couleur}{suffix} - {e.dr}: "
                f"B({jours_par_personne['B']}) C({jours_par_personne['C']}){reset}"
            )
            total_jours_evenements["B"] += jours_par_personne["B"]
            total_jours_evenements["C"] += jours_par_personne["C"]
        print(
            f"Total: B({total_jours_evenements['B']}) C({total_jours_evenements['C']})"
        )

        print()
