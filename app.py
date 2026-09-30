from flask import Flask, render_template, request
from src.blood_bank import BloodBank
from src.models import db, AuditLogModel
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
# Audit Trail
# --------------------------------------------------

@app.route("/audit-trail")
def audit_trail():

    audit_logs = (
        AuditLogModel.query
        .order_by(AuditLogModel.timestamp.desc())
        .all()
    )

    return render_template(
        "audit_trail.html",
        audit_logs=audit_logs
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
# Routine Blood Issue
# --------------------------------------------------

@app.route("/routine-issue", methods=["GET", "POST"])
def routine_issue():

    error_message = None
    issue_plan = None
    form_data = {}

    if request.method == "POST":

        form_data = request.form

        requested_type = request.form.get(
            "requested_type",
            ""
        ).strip()

        quantity_text = request.form.get(
            "quantity",
            ""
        ).strip()

        destination = request.form.get(
            "destination",
            ""
        ).strip()


        if not destination:

            error_message = "Destination is required."

        else:

            try:
                quantity = int(quantity_text)

                issue_plan = blood_bank.create_issue_plan(
                    requested_type,
                    quantity
                )

            except ValueError as error:
                error_message = str(error)

    return render_template(
        "routine_issue.html",
        blood_types=BLOOD_TYPES,
        error_message=error_message,
        success_message=None,
        issue_plan=issue_plan,
        form_data=form_data
    )


# --------------------------------------------------
# Confirm Routine Blood Issue
# --------------------------------------------------

@app.route("/confirm-routine-issue", methods=["POST"])
def confirm_routine_issue():

    requested_type = request.form.get(
        "requested_type",
        ""
    ).strip()

    requested_quantity_text = request.form.get(
        "requested_quantity",
        ""
    ).strip()

    destination = request.form.get(
        "destination",
        ""
    ).strip()

    try:
        if not destination:
            raise ValueError(
                "Destination is required."
            )
        requested_quantity = int(
            requested_quantity_text
        )

        compatible_types = blood_bank.create_issue_plan(
            requested_type,
            requested_quantity
        )["compatible_types"]

        selected_quantities = {}

        for blood_type in compatible_types:

            field_name = (
                "selected_"
                + blood_type
                .replace("+", "_plus")
                .replace("-", "_minus")
            )

            quantity_text = request.form.get(
                field_name,
                "0"
            ).strip()

            selected_quantities[blood_type] = int(
                quantity_text
            )

        result = blood_bank.confirm_issue_plan(
            requested_type,
            requested_quantity,
            selected_quantities,
            destination
        )
        issued_details = ", ".join(
            f"{blood_type}: {quantity}"
            for blood_type, quantity
            in result["issued_by_type"].items()
        )
        



        issued_description = ", ".join(
            f"{quantity} × {blood_type}"
            for blood_type, quantity
            in result["issued_by_type"].items()
        )

        if result["partial"]:

            success_message = (
                f"Partial issue completed: "
                f"{result['issued_quantity']} of "
                f"{result['requested_quantity']} requested "
                f"unit(s) were issued. "
                f"Issued: {issued_description}."
            )

        else:

            success_message = (
                f"Blood issue completed successfully. "
                f"Issued: {issued_description}."
            )

        return render_template(
            "routine_issue.html",
            blood_types=BLOOD_TYPES,
            error_message=None,
            success_message=success_message,
            issue_plan=None,
            form_data={}
        )

    except (ValueError, TypeError) as error:

        try:
            issue_plan = blood_bank.create_issue_plan(
                requested_type,
                int(requested_quantity_text)
            )
        except (ValueError, TypeError):
            issue_plan = None

        return render_template(
            "routine_issue.html",
            blood_types=BLOOD_TYPES,
            error_message=str(error),
            success_message=None,
            issue_plan=issue_plan,
            form_data={
                "requested_type": requested_type,
                "quantity": requested_quantity_text,
                "destination": destination
            }
        )




# --------------------------------------------------
# Emergency MCI
# --------------------------------------------------

@app.route("/emergency", methods=["GET", "POST"])
def emergency():

    success_message = None
    error_message = None

    if request.method == "POST":

        quantity_text = request.form.get(
            "quantity",
            ""
        ).strip()

        try:
            quantity = int(quantity_text)

            result = blood_bank.issue_emergency_blood(
                quantity
            )

            success_message = (
                f"Emergency issue completed successfully. "
                f"{result['quantity']} O- blood unit(s) "
                f"were issued. "
                f"{result['remaining_quantity']} "
                f"O- unit(s) remain in inventory."
            )

        except ValueError as error:
            error_message = str(error)

    o_negative_stock = blood_bank.get_stock_count(
        "O-"
    )

    return render_template(
        "emergency.html",
        o_negative_stock=o_negative_stock,
        success_message=success_message,
        error_message=error_message
    )








# --------------------------------------------------
# Run application
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)