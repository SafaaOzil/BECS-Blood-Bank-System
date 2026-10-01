from sqlalchemy import inspect, text

from app import app
from src.models import db


def migrate_audit_actor():

    with app.app_context():

        inspector = inspect(db.engine)

        columns = {
            column["name"]
            for column in inspector.get_columns("audit_logs")
        }

        print("Current audit_logs columns:")
        print(sorted(columns))

        if "actor_username" not in columns:

            db.session.execute(
                text(
                    "ALTER TABLE audit_logs "
                    "ADD COLUMN actor_username VARCHAR(50)"
                )
            )

            print("Added actor_username.")

        else:
            print("actor_username already exists.")

        if "actor_role" not in columns:

            db.session.execute(
                text(
                    "ALTER TABLE audit_logs "
                    "ADD COLUMN actor_role VARCHAR(30)"
                )
            )

            print("Added actor_role.")

        else:
            print("actor_role already exists.")

        db.session.commit()

        print("Audit trail migration completed successfully.")


if __name__ == "__main__":
    migrate_audit_actor()