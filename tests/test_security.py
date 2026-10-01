import pytest

from app import app
from src.models import (
    db,
    UserModel,
    BloodUnitModel,
    AuditLogModel
)

from src.user_roles import (
    ADMIN,
    BLOOD_BANK_USER,
    RESEARCH_STUDENT
)


# --------------------------------------------------
# Test Application
# --------------------------------------------------

@pytest.fixture()
def security_app():

    original_database_uri = app.config.get(
        "SQLALCHEMY_DATABASE_URI"
    )

    original_testing = app.config.get(
        "TESTING"
    )

    app.config["TESTING"] = True

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///:memory:"
    )

    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():

        db.drop_all()
        db.create_all()

        # ------------------------------------------
        # Create test users
        # ------------------------------------------

        admin = UserModel(
            username="testadmin",
            role=ADMIN,
            is_active=True
        )
        admin.set_password("Admin123!")

        blood_user = UserModel(
            username="blooduser",
            role=BLOOD_BANK_USER,
            is_active=True
        )
        blood_user.set_password("Blood123!")

        research_user = UserModel(
            username="research",
            role=RESEARCH_STUDENT,
            is_active=True
        )
        research_user.set_password("Research123!")

        disabled_user = UserModel(
            username="disabled",
            role=BLOOD_BANK_USER,
            is_active=False
        )
        disabled_user.set_password("Disabled123!")

        db.session.add_all([
            admin,
            blood_user,
            research_user,
            disabled_user
        ])

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        original_database_uri
    )

    app.config["TESTING"] = original_testing


@pytest.fixture()
def client(security_app):
    return security_app.test_client()


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def login(
    client,
    username,
    password
):

    return client.post(
        "/login",
        data={
            "username": username,
            "password": password
        },
        follow_redirects=False
    )


def logout(client):

    return client.get(
        "/logout",
        follow_redirects=False
    )


# --------------------------------------------------
# Authentication Tests
# --------------------------------------------------

def test_successful_login(client):

    response = login(
        client,
        "testadmin",
        "Admin123!"
    )

    assert response.status_code == 302

    assert response.headers["Location"].endswith("/")

    with client.session_transaction() as session:

        assert session["username"] == "testadmin"
        assert session["role"] == ADMIN


def test_failed_login_creates_audit(
    security_app,
    client
):

    response = login(
        client,
        "testadmin",
        "WrongPassword!"
    )

    assert response.status_code == 200

    assert (
        b"Invalid username or password"
        in response.data
    )

    with security_app.app_context():

        audit = (
            AuditLogModel.query
            .filter_by(
                action="LOGIN_FAILED"
            )
            .first()
        )

        assert audit is not None
        assert audit.actor_username == "testadmin"
        assert audit.actor_role == ADMIN


def test_successful_login_creates_audit(
    security_app,
    client
):

    login(
        client,
        "testadmin",
        "Admin123!"
    )

    with security_app.app_context():

        audit = (
            AuditLogModel.query
            .filter_by(
                action="LOGIN_SUCCESS"
            )
            .first()
        )

        assert audit is not None
        assert audit.actor_username == "testadmin"
        assert audit.actor_role == ADMIN


def test_disabled_user_cannot_login(
    client
):

    response = login(
        client,
        "disabled",
        "Disabled123!"
    )

    assert response.status_code == 200

    assert (
        b"This account is disabled"
        in response.data
    )


def test_logout_clears_session(
    security_app,
    client
):

    login(
        client,
        "testadmin",
        "Admin123!"
    )

    response = logout(client)

    assert response.status_code == 302

    with client.session_transaction() as session:

        assert "user_id" not in session
        assert "username" not in session
        assert "role" not in session

    with security_app.app_context():

        audit = (
            AuditLogModel.query
            .filter_by(
                action="LOGOUT"
            )
            .first()
        )

        assert audit is not None
        assert audit.actor_username == "testadmin"
        assert audit.actor_role == ADMIN


# --------------------------------------------------
# Anonymous User Tests
# --------------------------------------------------

def test_anonymous_user_redirected_to_login(
    client
):

    response = client.get(
        "/",
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# --------------------------------------------------
# Administrator Authorization Tests
# --------------------------------------------------

def test_admin_can_access_admin_pages(
    client
):

    login(
        client,
        "testadmin",
        "Admin123!"
    )

    users_response = client.get(
        "/admin/users"
    )

    audit_response = client.get(
        "/audit-trail"
    )

    export_response = client.get(
        "/export/xml"
    )

    assert users_response.status_code == 200
    assert audit_response.status_code == 200
    assert export_response.status_code == 200


# --------------------------------------------------
# Blood Bank User Authorization Tests
# --------------------------------------------------

def test_blood_bank_user_can_access_operational_pages(
    client
):

    login(
        client,
        "blooduser",
        "Blood123!"
    )

    assert client.get(
        "/donation"
    ).status_code == 200

    assert client.get(
        "/routine-issue"
    ).status_code == 200

    assert client.get(
        "/emergency"
    ).status_code == 200

    assert client.get(
        "/records-history"
    ).status_code == 200

    assert client.get(
        "/statistics"
    ).status_code == 200


def test_blood_bank_user_cannot_access_admin_pages(
    client
):

    login(
        client,
        "blooduser",
        "Blood123!"
    )

    assert client.get(
        "/admin/users"
    ).status_code == 403

    assert client.get(
        "/audit-trail"
    ).status_code == 403

    assert client.get(
        "/export/xml"
    ).status_code == 403


# --------------------------------------------------
# Research Student Authorization Tests
# --------------------------------------------------

def test_research_student_can_access_safe_pages(
    client
):

    login(
        client,
        "research",
        "Research123!"
    )

    assert client.get(
        "/"
    ).status_code == 200

    assert client.get(
        "/records-history"
    ).status_code == 200

    assert client.get(
        "/statistics"
    ).status_code == 200


def test_research_student_cannot_access_operational_pages(
    client
):

    login(
        client,
        "research",
        "Research123!"
    )

    protected_routes = [
        "/donation",
        "/routine-issue",
        "/emergency",
        "/audit-trail",
        "/admin/users",
        "/export/xml"
    ]

    for route in protected_routes:

        response = client.get(route)

        assert response.status_code == 403


# --------------------------------------------------
# Research Student Donor Privacy
# --------------------------------------------------

def test_research_student_cannot_view_donor_identity(
    security_app,
    client
):

    with security_app.app_context():

        unit = BloodUnitModel(
            blood_type="A+",
            donation_date="01/10/2026",
            donor_id="987654321",
            donor_name="Private Donor",
            status="AVAILABLE"
        )

        db.session.add(unit)
        db.session.commit()

    login(
        client,
        "research",
        "Research123!"
    )

    response = client.get(
        "/records-history"
    )

    assert response.status_code == 200

    assert b"Private Donor" not in response.data
    assert b"987654321" not in response.data

def test_research_student_cannot_search_by_donor_identity(
    security_app,
    client
):

    with security_app.app_context():

        unit = BloodUnitModel(
            blood_type="AB-",
            donation_date="15/08/2099",
            donor_id="123123123",
            donor_name="Hidden Research Donor",
            status="AVAILABLE"
        )

        db.session.add(unit)
        db.session.commit()

    login(
        client,
        "research",
        "Research123!"
    )

    response = client.get(
        "/records-history?search=Hidden%20Research%20Donor"
    )

    assert response.status_code == 200

    # The donor ID must never be exposed.
    assert b"123123123" not in response.data

    # Searching by donor name must NOT return
    # the matching donation record.
    #
    # The donor name itself may appear in the search input
    # because it was supplied by the user in the URL.
    assert b"15/08/2099" not in response.data