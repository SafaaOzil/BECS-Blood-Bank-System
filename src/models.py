from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class BloodUnitModel(db.Model):
    """
    Represents one blood unit stored in the database.
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

    def __repr__(self):
        return (
            f"<BloodUnitModel "
            f"id={self.id}, "
            f"blood_type={self.blood_type}>"
        )