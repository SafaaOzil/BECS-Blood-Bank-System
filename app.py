from flask import (
    Flask,
    render_template,
    request,
    Response, 
    redirect, 
    url_for, 
    session
)
from src.blood_bank import BloodBank
from src.models import (
    db,
    AuditLogModel,
    BloodUnitModel,
    RoutineRequestModel,
    EmergencyMCIModel,
    UserModel
)
from src.export_service import ExportService
from src.audit_service import AuditService
from src.blood_types import BLOOD_TYPES
import os

app = Flask(__name__)


app.config["SECRET_KEY"] = os.environ.get(
    "BECS_SECRET_KEY",
    "becs-development-secret-key"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"



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



@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = UserModel.query.filter_by(
            username=username
        ).first()

        if user is None:
            error = "Invalid username or password."

        elif not user.is_active:
            error = "This account is disabled."

        elif not user.check_password(password):
            error = "Invalid username or password."

        else:
            session.clear()

            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        error=error
    )




@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


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

    selected_action = request.args.get(
        "action",
        ""
    ).strip()

    search_text = request.args.get(
        "search",
        ""
    ).strip()

    query = AuditLogModel.query

    if selected_action:

        query = query.filter(
            AuditLogModel.action == selected_action
        )

    if search_text:

        search_pattern = f"%{search_text}%"

        query = query.filter(
            db.or_(
                AuditLogModel.details.ilike(
                    search_pattern
                ),
                AuditLogModel.record_type.ilike(
                    search_pattern
                ),
                AuditLogModel.record_id.ilike(
                    search_pattern
                )
            )
        )

    audit_logs = (
        query
        .order_by(
            AuditLogModel.timestamp.desc()
        )
        .all()
    )

    available_actions = [
        "DONATION_CREATED",
        "ROUTINE_ISSUE_COMPLETED",
        "EMERGENCY_MCI_ISSUE",
        "RECORDS_EXPORTED"
    ]

    return render_template(
        "audit_trail.html",
        audit_logs=audit_logs,
        available_actions=available_actions,
        selected_action=selected_action,
        search_text=search_text
    )

# --------------------------------------------------
# Records History
# --------------------------------------------------

@app.route("/records-history")
def records_history():

    record_type = request.args.get(
        "record_type",
        "all"
    ).strip()

    search_text = request.args.get(
        "search",
        ""
    ).strip()

    # --------------------------------------------------
    # Blood Donation Records
    # --------------------------------------------------

    blood_query = BloodUnitModel.query

    if search_text:

        search_pattern = f"%{search_text}%"

        blood_query = blood_query.filter(
            db.or_(
                BloodUnitModel.blood_type.ilike(
                    search_pattern
                ),
                BloodUnitModel.donor_id.ilike(
                    search_pattern
                ),
                BloodUnitModel.donor_name.ilike(
                    search_pattern
                ),
                BloodUnitModel.status.ilike(
                    search_pattern
                )
            )
        )

    blood_units = (
        blood_query
        .order_by(BloodUnitModel.id.desc())
        .all()
        if record_type in ("all", "donations")
        else []
    )

    # --------------------------------------------------
    # Routine Request Records
    # --------------------------------------------------

    routine_query = RoutineRequestModel.query

    if search_text:

        search_pattern = f"%{search_text}%"

        routine_query = routine_query.filter(
            db.or_(
                RoutineRequestModel.requested_blood_type.ilike(
                    search_pattern
                ),
                RoutineRequestModel.destination.ilike(
                    search_pattern
                ),
                RoutineRequestModel.issued_details.ilike(
                    search_pattern
                ),
                RoutineRequestModel.status.ilike(
                    search_pattern
                )
            )
        )

    routine_requests = (
        routine_query
        .order_by(
            RoutineRequestModel.created_at.desc()
        )
        .all()
        if record_type in ("all", "routine")
        else []
    )

    # --------------------------------------------------
    # Emergency MCI Records
    # --------------------------------------------------

    emergency_records = []

    if record_type in ("all", "emergency"):

        emergency_records = (
            EmergencyMCIModel.query
            .order_by(
                EmergencyMCIModel.created_at.desc()
            )
            .all()
        )

    return render_template(
        "records_history.html",
        blood_units=blood_units,
        routine_requests=routine_requests,
        emergency_records=emergency_records,
        record_type=record_type,
        search_text=search_text
    )


# --------------------------------------------------
# Statistics
# --------------------------------------------------

@app.route("/statistics")
def statistics():

    total_donations = BloodUnitModel.query.count()

    available_units = (
        BloodUnitModel.query
        .filter_by(status="AVAILABLE")
        .count()
    )

    issued_units = (
        BloodUnitModel.query
        .filter_by(status="ISSUED")
        .count()
    )

    total_routine_requests = (
        RoutineRequestModel.query.count()
    )

    total_routine_units = (
        db.session.query(
            db.func.sum(
                RoutineRequestModel.issued_quantity
            )
        ).scalar() or 0
    )

    total_mci_events = (
        EmergencyMCIModel.query.count()
    )

    total_mci_units = (
        db.session.query(
            db.func.sum(
                EmergencyMCIModel.issued_quantity
            )
        ).scalar() or 0
    )

    blood_type_statistics = []

    for blood_type in BLOOD_TYPES:

        total = (
            BloodUnitModel.query
            .filter_by(
                blood_type=blood_type
            )
            .count()
        )

        available = (
            BloodUnitModel.query
            .filter_by(
                blood_type=blood_type,
                status="AVAILABLE"
            )
            .count()
        )

        issued = (
            BloodUnitModel.query
            .filter_by(
                blood_type=blood_type,
                status="ISSUED"
            )
            .count()
        )

        blood_type_statistics.append({
            "blood_type": blood_type,
            "total": total,
            "available": available,
            "issued": issued
        })

    return render_template(
        "statistics.html",
        total_donations=total_donations,
        available_units=available_units,
        issued_units=issued_units,
        total_routine_requests=total_routine_requests,
        total_routine_units=total_routine_units,
        total_mci_events=total_mci_events,
        total_mci_units=total_mci_units,
        blood_type_statistics=blood_type_statistics
    )



# --------------------------------------------------
# Export Records
# --------------------------------------------------

@app.route("/export/xml")
def export_xml():

    AuditService.log_action(
        action="RECORDS_EXPORTED",
        record_type="SYSTEM_EXPORT",
        record_id=None,
        details=(
            "All BECS records were exported "
            "to XML format."
        )
    )

    db.session.commit()

    xml_data = ExportService.create_xml_export()

    filename = "BECS_records_export.xml"

    return Response(
        xml_data,
        mimetype="application/xml",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }
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