"""User data isolation between accounts."""
import pytest
from app.models import User, Job, Monitor, Collection
from app.services.security import create_access_token


def _auth_header(user_id: str, email: str, name: str):
    token = create_access_token({"sub": user_id, "email": email, "name": name})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_a(db_session):
    user = User(id="user_a", email="a@test.com", name="User A")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def user_b(db_session):
    user = User(id="user_b", email="b@test.com", name="User B")
    db_session.add(user)
    db_session.commit()
    return user


def test_user_cannot_read_other_users_job(client, db_session, user_a, user_b):
    job = Job(
        id="job_isolated_1",
        trace_id="trace_1",
        job_type="search_query",
        input="secret query",
        status="completed",
        user_id=user_b.id,
    )
    db_session.add(job)
    db_session.commit()

    res = client.get("/jobs/job_isolated_1", headers=_auth_header(user_a.id, user_a.email, user_a.name))
    assert res.status_code == 404


def test_user_sees_only_own_jobs(client, db_session, user_a, user_b):
    db_session.add_all([
        Job(id="job_a1", trace_id="t1", job_type="search_query", input="a", status="completed", user_id=user_a.id),
        Job(id="job_b1", trace_id="t2", job_type="search_query", input="b", status="completed", user_id=user_b.id),
    ])
    db_session.commit()

    res = client.get("/jobs", headers=_auth_header(user_a.id, user_a.email, user_a.name))
    assert res.status_code == 200
    ids = {j["job_id"] for j in res.json()}
    assert "job_a1" in ids
    assert "job_b1" not in ids


def test_user_cannot_delete_other_users_monitor(client, db_session, user_a, user_b):
    mon = Monitor(id="mon_1", user_id=user_b.id, topic="Other topic")
    db_session.add(mon)
    db_session.commit()

    res = client.delete("/monitors/mon_1", headers=_auth_header(user_a.id, user_a.email, user_a.name))
    assert res.status_code == 404


def test_user_cannot_delete_other_users_collection(client, db_session, user_a, user_b):
    coll = Collection(id="coll_1", user_id=user_b.id, name="Other")
    db_session.add(coll)
    db_session.commit()

    res = client.delete("/collections/coll_1", headers=_auth_header(user_a.id, user_a.email, user_a.name))
    assert res.status_code == 404
