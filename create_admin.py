from getpass import getpass

from app import app
from src.models import db, UserModel
from src.user_roles import ADMIN


def create_admin():
    print("=== Create BECS Administrator ===")

    username = input("Username: ").strip()

    if not username:
        print("Error: Username cannot be empty.")
        return

    password = getpass("Password: ")
    confirm_password = getpass("Confirm password: ")

    if not password:
        print("Error: Password cannot be empty.")
        return

    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    if len(password) < 8:
        print("Error: Password must contain at least 8 characters.")
        return

    with app.app_context():

        existing_user = UserModel.query.filter_by(
            username=username
        ).first()

        if existing_user:
            print("Error: Username already exists.")
            return

        admin = UserModel(
            username=username,
            role=ADMIN,
            is_active=True
        )

        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print()
        print("Administrator created successfully.")
        print(f"Username: {admin.username}")
        print(f"Role: {admin.role}")


if __name__ == "__main__":
    create_admin()