from datetime import datetime
import xml.etree.ElementTree as ET

from src.models import (
    BloodUnitModel,
    RoutineRequestModel,
    EmergencyMCIModel,
    AuditLogModel
)


class ExportService:

    @staticmethod
    def create_xml_export():

        root = ET.Element("BECSRecords")

        root.set(
            "generated_at",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # --------------------------------------------------
        # Blood Donation Records
        # --------------------------------------------------

        donations_element = ET.SubElement(
            root,
            "BloodDonations"
        )

        blood_units = (
            BloodUnitModel.query
            .order_by(BloodUnitModel.id.asc())
            .all()
        )

        for unit in blood_units:

            donation = ET.SubElement(
                donations_element,
                "BloodUnit"
            )

            donation.set("id", str(unit.id))

            ET.SubElement(
                donation,
                "BloodType"
            ).text = unit.blood_type

            ET.SubElement(
                donation,
                "DonationDate"
            ).text = unit.donation_date

            ET.SubElement(
                donation,
                "DonorID"
            ).text = unit.donor_id

            ET.SubElement(
                donation,
                "DonorName"
            ).text = unit.donor_name

            ET.SubElement(
                donation,
                "Status"
            ).text = unit.status

            ET.SubElement(
                donation,
                "RegisteredAt"
            ).text = (
                unit.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            ET.SubElement(
                donation,
                "IssuedAt"
            ).text = (
                unit.issued_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if unit.issued_at
                else ""
            )

        # --------------------------------------------------
        # Routine Request Records
        # --------------------------------------------------

        routine_element = ET.SubElement(
            root,
            "RoutineRequests"
        )

        routine_requests = (
            RoutineRequestModel.query
            .order_by(RoutineRequestModel.id.asc())
            .all()
        )

        for routine in routine_requests:

            request_element = ET.SubElement(
                routine_element,
                "RoutineRequest"
            )

            request_element.set(
                "id",
                str(routine.id)
            )

            ET.SubElement(
                request_element,
                "RequestedBloodType"
            ).text = routine.requested_blood_type

            ET.SubElement(
                request_element,
                "RequestedQuantity"
            ).text = str(
                routine.requested_quantity
            )

            ET.SubElement(
                request_element,
                "Destination"
            ).text = routine.destination

            ET.SubElement(
                request_element,
                "IssuedQuantity"
            ).text = str(
                routine.issued_quantity
            )

            ET.SubElement(
                request_element,
                "IssuedDetails"
            ).text = routine.issued_details or ""

            ET.SubElement(
                request_element,
                "Status"
            ).text = routine.status

            ET.SubElement(
                request_element,
                "CreatedAt"
            ).text = (
                routine.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            ET.SubElement(
                request_element,
                "CompletedAt"
            ).text = (
                routine.completed_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if routine.completed_at
                else ""
            )

        # --------------------------------------------------
        # Emergency MCI Records
        # --------------------------------------------------

        emergency_element = ET.SubElement(
            root,
            "EmergencyMCIRecords"
        )

        emergency_records = (
            EmergencyMCIModel.query
            .order_by(EmergencyMCIModel.id.asc())
            .all()
        )

        for emergency in emergency_records:

            mci_element = ET.SubElement(
                emergency_element,
                "EmergencyMCI"
            )

            mci_element.set(
                "id",
                str(emergency.id)
            )

            ET.SubElement(
                mci_element,
                "AvailableBeforeIssue"
            ).text = str(
                emergency.available_before_issue
            )

            ET.SubElement(
                mci_element,
                "RequestedQuantity"
            ).text = str(
                emergency.requested_quantity
            )

            ET.SubElement(
                mci_element,
                "IssuedQuantity"
            ).text = str(
                emergency.issued_quantity
            )

            ET.SubElement(
                mci_element,
                "RemainingAfterIssue"
            ).text = str(
                emergency.remaining_after_issue
            )

            ET.SubElement(
                mci_element,
                "CreatedAt"
            ).text = (
                emergency.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        # --------------------------------------------------
        # Audit Trail
        # --------------------------------------------------

        audit_element = ET.SubElement(
            root,
            "AuditTrail"
        )

        audit_logs = (
            AuditLogModel.query
            .order_by(AuditLogModel.id.asc())
            .all()
        )

        for log in audit_logs:

            log_element = ET.SubElement(
                audit_element,
                "AuditRecord"
            )

            log_element.set(
                "id",
                str(log.id)
            )

            ET.SubElement(
                log_element,
                "Timestamp"
            ).text = (
                log.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            ET.SubElement(
                log_element,
                "Action"
            ).text = log.action

            ET.SubElement(
                log_element,
                "RecordType"
            ).text = log.record_type

            ET.SubElement(
                log_element,
                "RecordID"
            ).text = log.record_id or ""

            ET.SubElement(
                log_element,
                "Details"
            ).text = log.details

        # --------------------------------------------------
        # Generate XML
        # --------------------------------------------------

        tree = ET.ElementTree(root)

        ET.indent(
            tree,
            space="    "
        )

        return ET.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True
        )