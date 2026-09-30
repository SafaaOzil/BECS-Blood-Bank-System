from datetime import datetime

from src.blood_types import (
    BLOOD_TYPES,
    BLOOD_TYPE_DISTRIBUTION,
    get_compatible_donors
)

from src.models import (
    db,
    BloodUnitModel,
    RoutineRequestModel,  
    EmergencyMCIModel
)
from src.audit_service import AuditService

class BloodBank:
    """
    Manages the blood units stored in the BECS database.
    """

    # --------------------------------------------------
    # Blood Donation
    # --------------------------------------------------

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
            raise ValueError(
                "Donor ID must contain digits only."
            )

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

        # Generate the database ID before the final commit.
        db.session.flush()

        AuditService.log_action(
            action="DONATION_CREATED",
            record_type="BLOOD_UNIT",
            record_id=unit.id,
            details=(
                f"Blood donation registered. "
                f"Blood type: {unit.blood_type}. "
                f"Donation date: {unit.donation_date}."
            )
        )

        db.session.commit()

        return unit

    # --------------------------------------------------
    # Inventory
    # --------------------------------------------------

    def get_stock_count(self, blood_type):
        """
        Return the number of available units
        for a specific blood type.
        """

        if blood_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        return BloodUnitModel.query.filter_by(
            blood_type=blood_type,
            status="AVAILABLE"
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

    # --------------------------------------------------
    # Routine Blood Issue - Recommendation
    # --------------------------------------------------

    def create_issue_plan(self, requested_type, quantity):
        """
        Create a recommended blood issue plan.

        The plan:
        1. Uses the requested blood type first.
        2. Uses only compatible alternatives.
        3. Prefers more common alternatives in order
           to preserve rarer blood types.
        4. If the full request cannot be supplied,
           returns the maximum compatible quantity available.

        This function does NOT remove blood from inventory.
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

        # The requested blood type always has first priority.
        alternative_types = [
            blood_type
            for blood_type in compatible_donors
            if blood_type != requested_type
        ]

        # Among alternatives, prefer more common blood types.
        alternative_types.sort(
            key=lambda blood_type:
                BLOOD_TYPE_DISTRIBUTION[blood_type],
            reverse=True
        )

        priority_order = [
            requested_type,
            *alternative_types
        ]

        plan = {}
        availability = {}

        remaining_quantity = quantity

        for blood_type in priority_order:

            available = self.get_stock_count(
                blood_type
            )

            availability[blood_type] = available

            if remaining_quantity > 0:
                selected_quantity = min(
                    available,
                    remaining_quantity
                )
            else:
                selected_quantity = 0

            plan[blood_type] = selected_quantity

            remaining_quantity -= selected_quantity

        total_selected = sum(plan.values())

        full_request_available = (
            total_selected == quantity
        )

        return {
            "requested_type": requested_type,
            "requested_quantity": quantity,
            "compatible_types": priority_order,
            "availability": availability,
            "recommended_plan": plan,
            "total_available_for_request": sum(
                availability.values()
            ),
            "recommended_quantity": total_selected,
            "missing_quantity": quantity - total_selected,
            "full_request_available": full_request_available
        }

    # --------------------------------------------------
    # Routine Blood Issue - Confirmation
    # --------------------------------------------------

    def confirm_issue_plan(
        self,
        requested_type,
        requested_quantity,
        selected_quantities,
        destination

    ):
        """
        Validate and issue the user's selected blood plan.

        selected_quantities example:
        {
            "A+": 2,
            "O+": 1,
            "A-": 0,
            "O-": 0
        }

        A full issue may equal the requested quantity.
        A partial issue may be smaller if the complete
        request cannot be fulfilled from compatible stock.
        """

        if requested_type not in BLOOD_TYPES:
            raise ValueError("Invalid blood type.")

        if (
            not isinstance(requested_quantity, int)
            or requested_quantity <= 0
        ):
            raise ValueError(
                "Requested quantity must be a positive integer."
            )

        if not destination or not destination.strip():
            raise ValueError(
                "Destination is required."
            )

        destination = destination.strip()
        
        compatible_donors = get_compatible_donors(
            requested_type
        )

        clean_selection = {}

        for blood_type, quantity in selected_quantities.items():

            if blood_type not in BLOOD_TYPES:
                raise ValueError(
                    "Invalid blood type in selection."
                )

            if blood_type not in compatible_donors:
                raise ValueError(
                    f"{blood_type} is not compatible "
                    f"with {requested_type}."
                )

            if not isinstance(quantity, int) or quantity < 0:
                raise ValueError(
                    "Selected quantities must be "
                    "non-negative integers."
                )

            available = self.get_stock_count(
                blood_type
            )

            if quantity > available:
                raise ValueError(
                    f"Only {available} unit(s) of "
                    f"{blood_type} are currently available."
                )

            clean_selection[blood_type] = quantity

        selected_total = sum(
            clean_selection.values()
        )

        if selected_total == 0:
            raise ValueError(
                "At least one blood unit must be selected."
            )

        if selected_total > requested_quantity:
            raise ValueError(
                "Selected quantity cannot exceed "
                "the requested quantity."
            )

        # Determine how many compatible units currently exist.
        total_compatible_available = sum(
            self.get_stock_count(blood_type)
            for blood_type in compatible_donors
        )

        # If enough compatible blood exists to satisfy the
        # complete request, a partial issue is not accepted.
        if (
            total_compatible_available >= requested_quantity
            and selected_total < requested_quantity
        ):
            raise ValueError(
                f"Please select exactly "
                f"{requested_quantity} blood unit(s)."
            )

        # If the complete request cannot be fulfilled,
        # issue the maximum available compatible quantity.
        if total_compatible_available < requested_quantity:
            maximum_possible = total_compatible_available

            if selected_total != maximum_possible:
                raise ValueError(
                    f"Only {maximum_possible} compatible "
                    f"unit(s) are available. "
                    f"Please select all available compatible "
                    f"units for the partial issue."
                )

        issued_units = []

        for blood_type, quantity in clean_selection.items():

            if quantity == 0:
                continue

            units = (
            BloodUnitModel.query
            .filter_by(
                blood_type=blood_type,
                status="AVAILABLE"
            )
            .order_by(BloodUnitModel.id.asc())
            .limit(quantity)
            .all()
        )


            for unit in units:

                issued_units.append({
                    "id": unit.id,
                    "blood_type": unit.blood_type
                })

                unit.status = "ISSUED"
                unit.issued_at = datetime.now()


                issued_by_type = {
            blood_type: quantity
            for blood_type, quantity
            in clean_selection.items()
            if quantity > 0
        }

        issued_details = ", ".join(
            f"{blood_type}: {quantity}"
            for blood_type, quantity
            in issued_by_type.items()
        )

        is_partial = (
            selected_total < requested_quantity
        )

        routine_request = RoutineRequestModel(
            requested_blood_type=requested_type,
            requested_quantity=requested_quantity,
            destination=destination,
            issued_quantity=selected_total,
            issued_details=issued_details,
            status=(
                "PARTIAL"
                if is_partial
                else "COMPLETED"
            ),
            completed_at=datetime.now()
        )

        db.session.add(routine_request)

        # Obtain the request ID before the final commit.
        db.session.flush()

        AuditService.log_action(
            action="ROUTINE_ISSUE_COMPLETED",
            record_type="ROUTINE_REQUEST",
            record_id=routine_request.id,
            details=(
                f"Routine blood request completed. "
                f"Requested blood type: "
                f"{requested_type}. "
                f"Requested quantity: "
                f"{requested_quantity}. "
                f"Destination: {destination}. "
                f"Issued quantity: "
                f"{selected_total}. "
                f"Issued blood: "
                f"{issued_details}. "
                f"Status: "
                f"{routine_request.status}."
            )
        )

        db.session.commit()

        return {
            "success": True,
            "request_id": routine_request.id,
            "requested_type": requested_type,
            "requested_quantity": requested_quantity,
            "destination": destination,
            "issued_quantity": selected_total,
            "partial": is_partial,
            "issued_units": issued_units,
            "issued_by_type": issued_by_type
        }

    # --------------------------------------------------
    # Emergency MCI
    # --------------------------------------------------

    def issue_emergency_blood(self, quantity):
        """
        Issue O- blood units for a mass casualty emergency.

        The user may choose any quantity from 1 up to
        the maximum number of O- units currently available.
        """

        emergency_blood_type = "O-"

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError(
                "Emergency quantity must be a positive integer."
            )

        available_quantity = self.get_stock_count(
            emergency_blood_type
        )

        if available_quantity == 0:
            raise ValueError(
                "No O- blood units available for emergency."
            )

        if quantity > available_quantity:
            raise ValueError(
                f"Only {available_quantity} O- blood unit(s) "
                f"are currently available."
            )

        units = (
            BloodUnitModel.query
            .filter_by(
                blood_type=emergency_blood_type,
                status="AVAILABLE"
            )
            .order_by(BloodUnitModel.id.asc())
            .limit(quantity)
            .all()
        )

        issued_unit_ids = [
            unit.id for unit in units
        ]

        for unit in units:
            unit.status = "ISSUED"
            unit.issued_at = datetime.now()

        remaining_quantity = (
            available_quantity - quantity
        )

        emergency_record = EmergencyMCIModel(
            available_before_issue=available_quantity,
            requested_quantity=quantity,
            issued_quantity=quantity,
            remaining_after_issue=remaining_quantity
        )

        db.session.add(emergency_record)

        # Generate the MCI record ID before the final commit.
        db.session.flush()

        AuditService.log_action(
            action="EMERGENCY_MCI_ISSUE",
            record_type="EMERGENCY_MCI",
            record_id=emergency_record.id,
            details=(
                f"Emergency MCI blood issue completed. "
                f"O- available before issue: "
                f"{available_quantity}. "
                f"Requested quantity: {quantity}. "
                f"Issued quantity: {quantity}. "
                f"O- remaining after issue: "
                f"{remaining_quantity}."
            )
        )

        db.session.commit()

        return {
            "success": True,
            "mci_record_id": emergency_record.id,
            "issued_type": emergency_blood_type,
            "quantity": quantity,
            "unit_ids": issued_unit_ids,
            "remaining_quantity": remaining_quantity
        }