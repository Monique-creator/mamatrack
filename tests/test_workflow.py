from datetime import date, timedelta

from app.models import Mother, Visit
from app.status import follow_up_status


def test_future_delivery_date_is_refused(client, login):
    login("nurse.alice")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    response = client.post("/mothers/new", data={"full_name": "Future Mum",
                                                 "delivery_date": tomorrow, "facility_id": "1"})
    assert b"cannot be in the future" in response.data
    assert Mother.query.filter_by(full_name="Future Mum").first() is None


def test_duplicate_mother_gets_a_warning(client, login):
    login("nurse.alice")
    existing = Mother.query.first()
    form = {"full_name": existing.full_name, "facility_id": str(existing.facility_id),
            "delivery_date": existing.delivery_date.isoformat()}
    response = client.post("/mothers/new", data=form)
    assert b"Possible duplicate" in response.data


def test_recording_a_visit_completes_the_case(client, login):
    login("nurse.alice")
    mother = Mother.query.filter_by(full_name="Grace Mukeshimana").first()
    assert follow_up_status(mother) == "overdue"

    client.post(f"/mothers/{mother.id}/visit",
                data={"visit_date": date.today().isoformat(), "outcome": "Attended"})
    assert follow_up_status(mother) == "completed"


def test_offline_sync_is_not_duplicated_on_retry(client, login):
    login("chw.jean")
    mother = Mother.query.filter_by(full_name="Solange Umutoni").first()
    update = {"ref": "phone-1", "mother_id": mother.id, "outcome": "Attended",
              "visit_date": date.today().isoformat(), "risk_type": "high_bp"}

    client.post("/api/sync", json={"updates": [update]})
    client.post("/api/sync", json={"updates": [update]})
    assert Visit.query.filter_by(mother_id=mother.id).count() == 1
    assert len(mother.active_risks) == 1


def test_different_synced_visits_go_to_review(client, login):
    login("chw.jean")
    mother = Mother.query.filter_by(full_name="Solange Umutoni").first()
    first = {"ref": "a", "mother_id": mother.id, "outcome": "Attended",
             "visit_date": date.today().isoformat()}
    second = dict(first, ref="b", outcome="Referred")

    client.post("/api/sync", json={"updates": [first, second]})
    assert follow_up_status(mother) == "review"
    assert Visit.query.filter_by(mother_id=mother.id).count() == 2