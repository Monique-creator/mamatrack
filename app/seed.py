from datetime import date, timedelta

from .models import Facility, Mother, RiskIndicator, User, Visit, db

DEMO_PASSWORD = "MamaTrack2026"

STAFF = [
    ("supervisor", "Diane Mukamana", "supervisor", None),
    ("nurse.alice", "Alice Uwimana", "nurse", "Kacyiru Health Centre"),
    ("nurse.paul", "Paul Habimana", "nurse", "Remera Health Centre"),
    ("chw.jean", "Jean Bosco Nkurunziza", "chw", "Kacyiru Health Centre"),
    ("chw.claire", "Claire Ingabire", "chw", "Remera Health Centre"),
]

# name, days since delivery, facility, chw username, visit outcome, risk
MOTHERS = [
    ("Aline Uwase", 63, "Kacyiru Health Centre", "chw.jean", None, "bleeding"),
    ("Grace Mukeshimana", 55, "Kacyiru Health Centre", "chw.jean", None, None),
    ("Josiane Nyirahabimana", 47, "Kacyiru Health Centre", "chw.jean", None, "distance"),
    ("Solange Umutoni", 38, "Kacyiru Health Centre", "chw.jean", None, None),
    ("Esther Iradukunda", 36, "Kacyiru Health Centre", None, None, "high_bp"),
    ("Chantal Niyonsaba", 21, "Kacyiru Health Centre", "chw.jean", None, None),
    ("Sandrine Mutoni", 9, "Kacyiru Health Centre", None, None, None),
    ("Divine Uwera", 50, "Kacyiru Health Centre", "chw.jean", "Attended", None),
    ("Ange Mukamurenzi", 45, "Remera Health Centre", "chw.claire", None, "infection"),
    ("Belyse Ishimwe", 30, "Remera Health Centre", "chw.claire", None, None),
    ("Claudine Uwamahoro", 60, "Remera Health Centre", None, "Referred", None),
]


def seed_if_empty():
    if User.query.first():
        return

    facilities = {name: Facility(name=name, district="Gasabo")
                  for name in ("Kacyiru Health Centre", "Remera Health Centre")}
    db.session.add_all(facilities.values())

    people = {}
    for username, name, role, facility in STAFF:
        user = User(username=username, full_name=name, role=role, is_active=True,
                    facility=facilities.get(facility))
        user.set_password(DEMO_PASSWORD)
        people[username] = user
    db.session.add_all(people.values())
    db.session.flush()

    today = date.today()
    for name, days, facility, chw, outcome, risk in MOTHERS:
        delivered = today - timedelta(days=days)
        mother = Mother(full_name=name, delivery_date=delivered, phone="0788000000",
                        facility=facilities[facility], chw=people.get(chw),
                        registered_by=people["nurse.alice"].id)
        db.session.add(mother)
        if outcome:
            mother.visits.append(Visit(visit_date=delivered + timedelta(days=40),
                                       outcome=outcome, recorded_by=people["nurse.alice"].id))
        if risk:
            mother.risks.append(RiskIndicator(risk_type=risk, created_by=people["nurse.alice"].id,
                                              note="Reported during home visit."))
    db.session.commit()