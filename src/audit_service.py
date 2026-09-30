from src.models import db, AuditLogModel


class AuditService:
    """
    Service responsible for creating audit trail records.

    Audit records document important actions performed
    in the BECS system.
    """

    @staticmethod
    def log_action(
        action,
        record_type,
        record_id,
        details
    ):
        """
        Create an audit trail record.

        The caller is responsible for committing the
        database transaction.
        """

        audit_record = AuditLogModel(
            action=action,
            record_type=record_type,
            record_id=str(record_id)
            if record_id is not None
            else None,
            details=details
        )

        db.session.add(audit_record)

        return audit_record