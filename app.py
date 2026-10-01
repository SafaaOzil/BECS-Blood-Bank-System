from flask import (
    Flask,
    render_template,
    request,
    Response, 
    redirect, 
    url_for, 
    session,
    abort
)
from src.auth import login_required, roles_required
from datetime import timedelta
from src.user_roles import (
    ADMIN,
    BLOOD_BANK_USER,
    RESEARCH_STUDENT
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
from flask_wtf.csrf import CSRFProtect



app = Flask(__name__)


app.config["SECRET_KEY"] = os.environ.get(
    "BECS_SECRET_KEY",
    "becs-development-secret-key-change-in-production"
)

csrf = CSRFProtect(app)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    minutes=30
)



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
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = UserModel.query.filter_by(
            username=username
        ).first()

        if user is None:

            error = "Invalid username or password."

            AuditService.log_action(
                action="LOGIN_FAILED",
                record_type="AUTHENTICATION",
                record_id=None,
                details=(
                    f"Failed login attempt for username "
                    f"'{username}': unknown username."
                ),
                actor_username=username or None,
                actor_role=None
            )

            db.session.commit()


        elif not user.is_active:

            error = "This account is disabled."

            AuditService.log_action(
                action="LOGIN_FAILED",
                record_type="AUTHENTICATION",
                record_id=user.id,
                details=(
                    f"Failed login attempt for disabled "
                    f"user '{user.username}'."
                ),
                actor_username=user.username,
                actor_role=user.role
            )

            db.session.commit()


        elif not user.check_password(password):

            error = "Invalid username or password."

            AuditService.log_action(
                action="LOGIN_FAILED",
                record_type="AUTHENTICATION",
                record_id=user.id,
                details=(
                    f"Failed login attempt for user "
                    f"'{user.username}': invalid credentials."
                ),
                actor_username=user.username,
                actor_role=user.role
            )

            db.session.commit()


        else:
            session.clear()
            session.permanent = True
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            AuditService.log_action(
                action="LOGIN_SUCCESS",
                record_type="AUTHENTICATION",
                record_id=user.id,
                details=(
                    f"Successful login for user "
                    f"'{user.username}'."
                )
            )

            db.session.commit()

            return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        error=error
    )




@app.route("/logout")
def logout():

    if session.get("user_id"):

        AuditService.log_action(
            action="LOGOUT",
            record_type="AUTHENTICATION",
            record_id=session.get("user_id"),
            details=(
                f"User '{session.get('username')}' logged out."
            )
        )

        db.session.commit()

    session.clear()

    return redirect(url_for("login"))

# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@app.route("/")
@login_required
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
@roles_required(ADMIN)
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
        "RECORDS_EXPORTED",
        "USER_CREATED",
        "USER_DISABLED",
        "USER_ENABLED",
        "LOGIN_SUCCESS",
        "LOGIN_FAILED",
        "LOGOUT"
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
@login_required
def records_history():

    record_type = request.args.get(
        "record_type",
        "all"
    ).strip()

    search_text = request.args.get(
        "search",
        ""
    ).strip()

    current_role = session.get("role")

    # --------------------------------------------------
    # Blood Donation Records
    # --------------------------------------------------

    blood_query = BloodUnitModel.query

    if search_text:

        search_pattern = f"%{search_text}%"

        # Research students must not search
        # donor-identifying information.
        if current_role == RESEARCH_STUDENT:

            blood_query = blood_query.filter(
                db.or_(
                    BloodUnitModel.blood_type.ilike(
                        search_pattern
                    ),
                    BloodUnitModel.status.ilike(
                        search_pattern
                    )
                )
            )

        else:

            # Admin and Blood Bank User keep the
            # original full search functionality.
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
@login_required
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
@roles_required(ADMIN)
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
@roles_required(ADMIN, BLOOD_BANK_USER)
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
@roles_required(ADMIN, BLOOD_BANK_USER)
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
@roles_required(ADMIN, BLOOD_BANK_USER)
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
@roles_required(ADMIN, BLOOD_BANK_USER)
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
# Admin - User Management
# --------------------------------------------------

@app.route("/admin/users", methods=["GET", "POST"])
@roles_required(ADMIN)
def manage_users():

    error = None
    success = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        role = request.form.get(
            "role",
            ""
        ).strip()

        # ------------------------------
        # Validation
        # ------------------------------

        if not username:
            error = "Username is required."

        elif len(username) < 3:
            error = "Username must contain at least 3 characters."

        elif not password:
            error = "Password is required."

        elif len(password) < 8:
            error = "Password must contain at least 8 characters."

        elif role not in (
            ADMIN,
            BLOOD_BANK_USER,
            RESEARCH_STUDENT
        ):
            error = "Invalid user role."

        elif UserModel.query.filter_by(
            username=username
        ).first():

            error = "Username already exists."

        # ------------------------------
        # Create User
        # ------------------------------

        else:

            new_user = UserModel(
                username=username,
                role=role,
                is_active=True
            )

            new_user.set_password(password)

            db.session.add(new_user)

            # Flush so the new user receives an ID
            # before the audit record is created.
            db.session.flush()

            AuditService.log_action(
                action="USER_CREATED",
                record_type="USER",
                record_id=new_user.id,
                details=(
                    f"User account '{new_user.username}' created "
                    f"with role {new_user.role}."
                )
            )

            db.session.commit()

            success = "User created successfully."

    users = (
        UserModel.query
        .order_by(UserModel.id.asc())
        .all()
    )

    return render_template(
        "admin_users.html",
        users=users,
        error=error,
        success=success,
        roles=[
            ADMIN,
            BLOOD_BANK_USER,
            RESEARCH_STUDENT
        ]
    )




# --------------------------------------------------
# Admin - Enable / Disable User
# --------------------------------------------------

@app.route(
    "/admin/users/<int:user_id>/toggle-status",
    methods=["POST"]
)
@roles_required(ADMIN)
def toggle_user_status(user_id):

    user = db.session.get(
        UserModel,
        user_id
    )

    if user is None:
        abort(404)

    # Prevent the currently logged-in administrator
    # from disabling their own account.
    if user.id == session.get("user_id"):
        abort(400)

    user.is_active = not user.is_active

    if user.is_active:
        action = "USER_ENABLED"
        status_text = "enabled"
    else:
        action = "USER_DISABLED"
        status_text = "disabled"

    AuditService.log_action(
        action=action,
        record_type="USER",
        record_id=user.id,
        details=(
            f"User account '{user.username}' "
            f"({user.role}) was {status_text}."
        )
    )

    db.session.commit()

    return redirect(
        url_for("manage_users")
    )




# --------------------------------------------------
# Admin - System Metadata
# --------------------------------------------------

@app.route("/admin/metadata")
@roles_required(ADMIN)
def system_metadata():
    print("DATABASE:", app.config["SQLALCHEMY_DATABASE_URI"])
    print("USERS:", UserModel.query.count())
    print("BLOOD UNITS:", BloodUnitModel.query.count())
    print("AUDIT RECORDS:", AuditLogModel.query.count())

    metadata = {
        "total_users": UserModel.query.count(),

        "active_users": UserModel.query.filter_by(
            is_active=True
        ).count(),

        "total_blood_units": BloodUnitModel.query.count(),

        "available_blood_units": BloodUnitModel.query.filter_by(
            status="AVAILABLE"
        ).count(),

        "issued_blood_units": BloodUnitModel.query.filter_by(
            status="ISSUED"
        ).count(),

        "total_routine_requests": RoutineRequestModel.query.count(),

        "total_emergency_mci_records": EmergencyMCIModel.query.count(),

        "total_audit_records": AuditLogModel.query.count()
    }

    return render_template(
        "metadata.html",
        metadata=metadata
    )



# --------------------------------------------------
# Refresh session timeout
# --------------------------------------------------

@app.before_request
def refresh_session_timeout():

    if session.get("user_id"):
        session.permanent = True
        session.modified = True



# --------------------------------------------------
# Run application
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)