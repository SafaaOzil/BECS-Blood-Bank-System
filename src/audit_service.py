from flask import has_request_context, session

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
        details,
        actor_username=None,
        actor_role=None
    ):
        """
        Create an audit trail record.

        If the action occurs during an authenticated web
        request, the current user's username and role are
        automatically recorded.

        The caller is responsible for committing the
        database transaction.
        """

        if has_request_context():

            if actor_username is None:
                actor_username = session.get("username")

            if actor_role is None:
                actor_role = session.get("role")

        audit_record = AuditLogModel(
            action=action,
            record_type=record_type,
            record_id=(
                str(record_id)
                if record_id is not None
                else None
            ),
            actor_username=actor_username,
            actor_role=actor_role,
            details=details
        )

        db.session.add(audit_record)

        return audit_record