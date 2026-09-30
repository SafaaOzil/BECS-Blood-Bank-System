from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class BloodUnitModel(db.Model):
    """
    Represents one blood unit stored in the BECS database.

    Blood units are kept as permanent records.
    Issued units are marked as ISSUED instead of being deleted.
    """

    __tablename__ = "blood_units"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    blood_type = db.Column(
        db.String(3),
        nullable=False
    )

    donation_date = db.Column(
        db.String(10),
        nullable=False
    )

    donor_id = db.Column(
        db.String(9),
        nullable=False
    )

    donor_name = db.Column(
        db.String(100),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="AVAILABLE"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    issued_at = db.Column(
        db.DateTime,
        nullable=True
    )

    def __repr__(self):
        return (
            f"<BloodUnitModel "
            f"id={self.id}, "
            f"blood_type={self.blood_type}, "
            f"status={self.status}>"
        )


class RoutineRequestModel(db.Model):
    """
    Stores the permanent history of routine blood requests.
    """

    __tablename__ = "routine_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    requested_blood_type = db.Column(
        db.String(3),
        nullable=False
    )

    requested_quantity = db.Column(
        db.Integer,
        nullable=False
    )

    destination = db.Column(
        db.String(100),
        nullable=False
    )

    issued_quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    def __repr__(self):
        return (
            f"<RoutineRequestModel "
            f"id={self.id}, "
            f"blood_type={self.requested_blood_type}, "
            f"status={self.status}>"
        )


class EmergencyMCIModel(db.Model):
    """
    Stores the permanent history of emergency MCI issues.
    """

    __tablename__ = "emergency_mci"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    available_before_issue = db.Column(
        db.Integer,
        nullable=False
    )

    requested_quantity = db.Column(
        db.Integer,
        nullable=False
    )

    issued_quantity = db.Column(
        db.Integer,
        nullable=False
    )

    remaining_after_issue = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    def __repr__(self):
        return (
            f"<EmergencyMCIModel "
            f"id={self.id}, "
            f"issued_quantity={self.issued_quantity}>"
        )


class AuditLogModel(db.Model):
    """
    Immutable audit trail record.

    Audit records are intended to be viewed and exported,
    not edited or deleted through the application.
    """

    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    action = db.Column(
        db.String(50),
        nullable=False
    )

    record_type = db.Column(
        db.String(50),
        nullable=False
    )

    record_id = db.Column(
        db.String(50),
        nullable=True
    )

    details = db.Column(
        db.Text,
        nullable=False
    )

    def __repr__(self):
        return (
            f"<AuditLogModel "
            f"id={self.id}, "
            f"action={self.action}, "
            f"record_type={self.record_type}>"
        )