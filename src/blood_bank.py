from datetime import datetime

from src.blood_types import (
    BLOOD_TYPES,
    BLOOD_TYPE_DISTRIBUTION,
    get_compatible_donors
)

from src.models import db, BloodUnitModel


class BloodBank:
    """
    Manages the blood units stored in the BECS database.
    """

    def add_donation(
        self,
        blood_type,
        donation_date,
        donor_id,
        donor_name
    ):
        """
        Add a new donated blood unit to the database.
        """

        if blood_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        if not donation_date.strip():
            raise ValueError("Donation date is required.")

        try:
            parsed_date = datetime.strptime(
                donation_date,
                "%d/%m/%Y"
            ).date()
        except ValueError:
            raise ValueError(
               "Donation date must be in DD/MM/YYYY format."
            )

        if parsed_date > datetime.now().date():
            raise ValueError(
               "Donation date cannot be in the future."
    )

        if not donor_id.strip():
            raise ValueError("Donor ID is required.")

        if not donor_id.isdigit():
            raise ValueError("Donor ID must contain digits only.")

        if len(donor_id) != 9:
            raise ValueError(
                "Donor ID must contain exactly 9 digits."
            )

        if not donor_name.strip():
            raise ValueError("Donor name is required.")

        if len(donor_name.strip()) < 2:
            raise ValueError("Donor name is too short.")

        unit = BloodUnitModel(
            blood_type=blood_type,
            donation_date=donation_date,
            donor_id=donor_id,
            donor_name=donor_name.strip()
        )

        db.session.add(unit)
        db.session.commit()

        return unit

    def get_stock_count(self, blood_type):
        """
        Return the number of available units
        for a specific blood type.
        """

        if blood_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        return BloodUnitModel.query.filter_by(
            blood_type=blood_type
        ).count()

    def get_inventory_summary(self):
        """
        Return the number of available units
        for every blood type.
        """

        return {
            blood_type: self.get_stock_count(blood_type)
            for blood_type in BLOOD_TYPES
        }

    def find_alternative_blood_type(
        self,
        requested_type,
        quantity=1
    ):
        """
        Find the best available alternative blood type.

        The alternative must:
        1. Be compatible with the recipient.
        2. Have enough units for the requested quantity.
        3. Prefer a more common blood type in order
           to preserve rarer blood types when possible.
        """

        if requested_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError(
                "Quantity must be a positive integer."
            )

        compatible_donors = get_compatible_donors(
            requested_type
        )

        available_alternatives = []

        for blood_type in compatible_donors:
            if blood_type == requested_type:
                continue

            if self.get_stock_count(blood_type) >= quantity:
                available_alternatives.append(blood_type)

        if not available_alternatives:
            return None

        available_alternatives.sort(
            key=lambda blood_type:
                BLOOD_TYPE_DISTRIBUTION[blood_type],
            reverse=True
        )

        return available_alternatives[0]

    def issue_blood(self, requested_type, quantity):
        """
        Issue blood units of the requested type.

        If there are not enough units of the requested
        blood type, return a compatible alternative
        recommendation when available.
        """

        if requested_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError(
                "Quantity must be a positive integer."
            )

        available_quantity = self.get_stock_count(
            requested_type
        )

        if available_quantity >= quantity:
            units = (
                BloodUnitModel.query
                .filter_by(blood_type=requested_type)
                .order_by(BloodUnitModel.id.asc())
                .limit(quantity)
                .all()
            )

            issued_unit_ids = [
                unit.id for unit in units
            ]

            for unit in units:
                db.session.delete(unit)

            db.session.commit()

            return {
                "success": True,
                "issued_type": requested_type,
                "quantity": quantity,
                "unit_ids": issued_unit_ids,
                "alternative": None
            }

        alternative = self.find_alternative_blood_type(
            requested_type,
            quantity
        )

        return {
            "success": False,
            "requested_type": requested_type,
            "requested_quantity": quantity,
            "available_quantity": available_quantity,
            "alternative": alternative
        }

    def issue_emergency_blood(self):
        """
        Issue all available O- blood units
        for a mass casualty emergency event.
        """

        emergency_blood_type = "O-"

        units = (
            BloodUnitModel.query
            .filter_by(blood_type=emergency_blood_type)
            .order_by(BloodUnitModel.id.asc())
            .all()
        )

        if not units:
            raise ValueError(
                "No O- blood units available for emergency."
            )

        issued_unit_ids = [
            unit.id for unit in units
        ]

        quantity = len(units)

        for unit in units:
            db.session.delete(unit)

        db.session.commit()

        return {
            "success": True,
            "issued_type": emergency_blood_type,
            "quantity": quantity,
            "unit_ids": issued_unit_ids
        }