import pytest
from flask import Flask

from src.models import (
    db,
    BloodUnitModel,
    RoutineRequestModel,
    EmergencyMCIModel,
    AuditLogModel
)

from src.blood_bank import BloodBank
from src.export_service import ExportService


@pytest.fixture()
def test_app():

    app = Flask(__name__)

    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():

        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def blood_bank(test_app):
    return BloodBank()


def test_donation_creates_blood_unit_and_audit(
    test_app,
    blood_bank
):

    with test_app.app_context():

        blood_bank.add_donation(
            "A+",
            "30/09/2026",
            "123456789",
            "Test Donor"
        )

        unit = BloodUnitModel.query.one()

        assert unit.blood_type == "A+"
        assert unit.donor_id == "123456789"
        assert unit.donor_name == "Test Donor"
        assert unit.status == "AVAILABLE"

        audit = AuditLogModel.query.one()

        assert audit.action == "DONATION_CREATED"
        assert audit.record_type == "BLOOD_UNIT"
        assert audit.record_id == str(unit.id)


def test_routine_issue_creates_history_and_audit(
    test_app,
    blood_bank
):

    with test_app.app_context():

        blood_bank.add_donation(
            "A+",
            "30/09/2026",
            "111111111",
            "Donor One"
        )

        blood_bank.add_donation(
            "A+",
            "30/09/2026",
            "222222222",
            "Donor Two"
        )

        result = blood_bank.confirm_issue_plan(
            "A+",
            2,
            {
                "A+": 2,
                "O+": 0,
                "A-": 0,
                "O-": 0
            },
            "Operating Room"
        )

        assert result["issued_quantity"] == 2
        assert result["partial"] is False

        issued_units = (
            BloodUnitModel.query
            .filter_by(status="ISSUED")
            .count()
        )

        assert issued_units == 2

        routine = RoutineRequestModel.query.one()

        assert routine.requested_blood_type == "A+"
        assert routine.requested_quantity == 2
        assert routine.destination == "Operating Room"
        assert routine.issued_quantity == 2
        assert routine.status == "COMPLETED"

        audit = (
            AuditLogModel.query
            .filter_by(
                action="ROUTINE_ISSUE_COMPLETED"
            )
            .one()
        )

        assert audit.record_type == "ROUTINE_REQUEST"
        assert audit.record_id == str(routine.id)


def test_partial_routine_issue(
    test_app,
    blood_bank
):

    with test_app.app_context():

        blood_bank.add_donation(
            "O-",
            "30/09/2026",
            "333333333",
            "Partial Donor"
        )

        result = blood_bank.confirm_issue_plan(
            "A+",
            2,
            {
                "A+": 0,
                "O+": 0,
                "A-": 0,
                "O-": 1
            },
            "Trauma"
        )

        assert result["issued_quantity"] == 1
        assert result["partial"] is True

        routine = RoutineRequestModel.query.one()

        assert routine.requested_quantity == 2
        assert routine.issued_quantity == 1
        assert routine.status == "PARTIAL"
        assert routine.destination == "Trauma"


def test_emergency_mci_creates_history_and_audit(
    test_app,
    blood_bank
):

    with test_app.app_context():

        for index in range(3):

            blood_bank.add_donation(
                "O-",
                "30/09/2026",
                f"44444444{index}",
                f"MCI Donor {index}"
            )

        result = blood_bank.issue_emergency_blood(2)

        assert result["quantity"] == 2
        assert result["remaining_quantity"] == 1

        available = (
            BloodUnitModel.query
            .filter_by(
                blood_type="O-",
                status="AVAILABLE"
            )
            .count()
        )

        issued = (
            BloodUnitModel.query
            .filter_by(
                blood_type="O-",
                status="ISSUED"
            )
            .count()
        )

        assert available == 1
        assert issued == 2

        emergency = EmergencyMCIModel.query.one()

        assert emergency.available_before_issue == 3
        assert emergency.requested_quantity == 2
        assert emergency.issued_quantity == 2
        assert emergency.remaining_after_issue == 1

        audit = (
            AuditLogModel.query
            .filter_by(
                action="EMERGENCY_MCI_ISSUE"
            )
            .one()
        )

        assert audit.record_type == "EMERGENCY_MCI"
        assert audit.record_id == str(emergency.id)


def test_xml_export_contains_all_record_sections(
    test_app,
    blood_bank
):

    with test_app.app_context():

        blood_bank.add_donation(
            "B+",
            "30/09/2026",
            "555555555",
            "Export Donor"
        )

        xml_data = ExportService.create_xml_export()

        xml_text = xml_data.decode("utf-8")

        assert "<BECSRecords" in xml_text
        assert "<BloodDonations>" in xml_text
        assert "<RoutineRequests" in xml_text
        assert "<EmergencyMCIRecords" in xml_text
        assert "<AuditTrail>" in xml_text

        assert "Export Donor" in xml_text
        assert "DONATION_CREATED" in xml_text