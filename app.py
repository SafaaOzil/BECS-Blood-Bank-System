from flask import Flask, render_template, request
from src.blood_bank import BloodBank
from src.models import db
from src.blood_types import BLOOD_TYPES


app = Flask(__name__)


# --------------------------------------------------
# Database configuration
# --------------------------------------------------

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blood_bank.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# Create database tables if they do not already exist
with app.app_context():
    db.create_all()


# Create the blood bank service
blood_bank = BloodBank()


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@app.route("/")
def dashboard():

    inventory = blood_bank.get_inventory_summary()

    return render_template(
        "dashboard.html",
        inventory=inventory
    )
# --------------------------------------------------
# Blood Donation
# --------------------------------------------------

@app.route("/donation", methods=["GET", "POST"])
def donation():

    success_message = None
    error_message = None
    form_data = {}

    if request.method == "POST":

        form_data = request.form

        blood_type = request.form.get(
            "blood_type",
            ""
        ).strip()

        donation_date = request.form.get(
            "donation_date",
            ""
        ).strip()

        donor_id = request.form.get(
            "donor_id",
            ""
        ).strip()

        donor_name = request.form.get(
            "donor_name",
            ""
        ).strip()

        try:
            blood_bank.add_donation(
                blood_type,
                donation_date,
                donor_id,
                donor_name
            )

            success_message = (
                f"Blood donation registered successfully. "
                f"Blood type: {blood_type}"
            )

            # Clear the form after successful registration
            form_data = {}

        except ValueError as error:
            error_message = str(error)

    return render_template(
        "donation.html",
        blood_types=BLOOD_TYPES,
        success_message=success_message,
        error_message=error_message,
        form_data=form_data
    )

# --------------------------------------------------
# Run application
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)