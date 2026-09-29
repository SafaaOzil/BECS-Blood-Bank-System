from dataclasses import dataclass
from src.blood_types import (
    BLOOD_TYPES,
    BLOOD_TYPE_DISTRIBUTION,
    get_compatible_donors
)
@dataclass
class BloodUnit:
    """
    Represents one donated blood unit in the BECS system.
    """

    blood_type: str
    donation_date: str
    donor_id: str
    donor_name: str

class BloodBank:
    """
    Manages the blood units stored in the BECS blood bank.
    """

    def __init__(self):
        self.inventory = {blood_type: [] for blood_type in BLOOD_TYPES}

    def add_donation(self, blood_type, donation_date, donor_id, donor_name):
        """
        Add a new donated blood unit to the inventory.
        """

        if blood_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        if not donation_date.strip():
            raise ValueError("Donation date is required.")

        if not donor_id.strip():
            raise ValueError("Donor ID is required.")

        if not donor_name.strip():
            raise ValueError("Donor name is required.")

        unit = BloodUnit(
            blood_type=blood_type,
            donation_date=donation_date,
            donor_id=donor_id,
            donor_name=donor_name
        )

        self.inventory[blood_type].append(unit)

        return unit
    def get_stock_count(self, blood_type):
        """
        Return the number of available units for a specific blood type.
        """

        if blood_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        return len(self.inventory[blood_type])

    def get_inventory_summary(self):
        """
        Return the number of available units for every blood type.
        """

        return {
            blood_type: len(units)
            for blood_type, units in self.inventory.items()
        }

    
    def find_alternative_blood_type(self, requested_type, quantity=1):
        """
        Find the best available alternative blood type.

        The alternative must:
        1. Be compatible with the recipient.
        2. Have enough units for the requested quantity.
        3. Prefer a more common blood type in order to preserve
           rarer blood types when possible.
        """

        if requested_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        compatible_donors = get_compatible_donors(requested_type)

        available_alternatives = []

        for blood_type in compatible_donors:
            if blood_type == requested_type:
                continue

            if self.get_stock_count(blood_type) >= quantity:
                available_alternatives.append(blood_type)

        if not available_alternatives:
            return None

        available_alternatives.sort(
            key=lambda blood_type: BLOOD_TYPE_DISTRIBUTION[blood_type],
            reverse=True
        )

        return available_alternatives[0]


    ###########################
    def issue_blood(self, requested_type, quantity):
        """
        Issue blood units of the requested type.

        If there are not enough units of the requested blood type,
        return a compatible alternative recommendation when available.
        """

        if requested_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        available_quantity = self.get_stock_count(requested_type)

        # Enough units of the requested blood type are available
        if available_quantity >= quantity:
            issued_units = []

            for _ in range(quantity):
                unit = self.inventory[requested_type].pop(0)
                issued_units.append(unit)

            return {
                "success": True,
                "issued_type": requested_type,
                "quantity": quantity,
                "units": issued_units,
                "alternative": None
            }

        # Not enough units - look for a compatible alternative
        alternative = self.find_alternative_blood_type(
    requested_type,
    quantity)

        return {
            "success": False,
            "requested_type": requested_type,
            "requested_quantity": quantity,
            "available_quantity": available_quantity,
            "alternative": alternative
        }
    def issue_emergency_blood(self):
        """
        Issue all available O- blood units for a mass casualty
        emergency event.

        Raises an error if no O- units are available.
        """

        emergency_blood_type = "O-"

        available_quantity = self.get_stock_count(emergency_blood_type)

        if available_quantity == 0:
            raise ValueError("No O- blood units available for emergency.")

        issued_units = self.inventory[emergency_blood_type].copy()

        self.inventory[emergency_blood_type].clear()

        return {
            "success": True,
            "issued_type": emergency_blood_type,
            "quantity": available_quantity,
            "units": issued_units
        }