from datetime import date, timedelta

from app.models import Mother, RiskIndicator, Visit, db
from app.status import follow_up_status, prioritise


def make_mother(days_ago, **extra):
    mother = Mother(full_name="Test Mother", facility_id=1,
                    delivery_date=date.today() - timedelta(days=days_ago), **extra)
    db.session.add(mother)
    db.session.flush()
    return mother


def test_due_date_is_delivery_plus_42_days(app):
    mother = make_mother(0)
    assert mother.due_date == date.today() + timedelta(days=42)


def test_due_date_follows_a_corrected_delivery_date(app):
    mother = make_mother(10)
    mother.delivery_date = date(2026, 1, 1)
    assert mother.due_date == date(2026, 2, 12)


def test_status_moves_from_on_time_to_due_soon_to_overdue(app):
    assert follow_up_status(make_mother(20)) == "on_time"
    assert follow_up_status(make_mother(38)) == "due_soon"
    assert follow_up_status(make_mother(42)) == "due_soon"
    assert follow_up_status(make_mother(43)) == "overdue"


def test_recorded_visit_clears_overdue(app):
    mother = make_mother(60)
    mother.visits.append(Visit(visit_date=date.today(), outcome="Attended"))
    db.session.flush()
    assert follow_up_status(mother) == "completed"


def test_overdue_with_risk_comes_first_then_longest_overdue(app):
    late = make_mother(70)
    later_with_risk = make_mother(50)
    later_with_risk.risks.append(RiskIndicator(risk_type="bleeding"))
    db.session.flush()
    upcoming = make_mother(5)
    ordered = prioritise([upcoming, late, later_with_risk])
    assert ordered == [later_with_risk, late, upcoming]