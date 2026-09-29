from dataclasses import dataclass
from src.blood_types import BLOOD_TYPES

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