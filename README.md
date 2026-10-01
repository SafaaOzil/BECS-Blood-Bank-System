# BECS - Blood Bank Management System

BECS is a web-based Blood Bank Management System developed
as part of a Biomedical Software Engineering assignment.

The system manages blood donations, routine blood issuing,
emergency blood issuing during a Mass Casualty Incident
(MCI), electronic record history, audit trails, statistics,
user access, and records export.

The project was developed incrementally.

The current version extends the original BECS system with:

- Electronic record controls inspired by FDA 21 CFR Part 11
- Authentication and role-based access control
- HIPAA-inspired privacy and access controls
- Cybersecurity-inspired security mechanisms
- Administrative user management
- System metadata
- CSRF protection
- Session security and automatic session timeout

These features are implemented for academic purposes and
do not represent full regulatory compliance.

---

## Technologies

- Python
- Flask
- Flask-SQLAlchemy
- Flask-WTF
- Werkzeug
- SQLite
- HTML
- CSS
- Jinja2
- XML

---

# Main Features

## 1. Blood Donation

Authorized blood bank personnel can register a new blood
donation.

For every donation, the following information is stored:

- Blood type
- Donation date
- Donor ID
- Donor full name
- Blood unit status
- Registration timestamp
- Issue timestamp, when applicable

The system validates the entered information before storing
the blood unit in the database.

Every successful donation is also recorded in the audit
trail.

---

## 2. Routine Blood Issue

Authorized blood bank personnel can create a routine blood
request by selecting:

- Requested blood type
- Number of required blood units
- Destination

The system checks the current blood inventory and creates
a compatible blood issue recommendation.

The requested blood type receives first priority.

If there are not enough units of the requested blood type,
the system searches for compatible alternatives.

Compatible alternatives are prioritized using the blood
type population distribution provided in the assignment.
More common compatible blood types are preferred before
rarer compatible blood types when appropriate.

The user can review and modify the proposed quantities
before confirming the issue.

If the complete request cannot be fulfilled, the system
can issue the maximum compatible quantity currently
available.

Each completed routine request is permanently recorded
with:

- Requested blood type
- Requested quantity
- Destination
- Issued quantity
- Issued blood type details
- Request status
- Creation timestamp
- Completion timestamp

A request can be stored as:

- COMPLETED
- PARTIAL

Every successful routine issue is also recorded in the
audit trail.

---

## 3. Emergency MCI

During a Mass Casualty Incident, authorized blood bank
personnel can access the emergency MCI interface.

The system provides emergency access to O- blood.

The interface displays the maximum number of O- units
currently available.

The maximum quantity is selected by default, but the user
may select a smaller quantity.

The system prevents issuing more O- units than are
available in inventory.

Each emergency MCI issue is permanently recorded with:

- O- units available before the issue
- Requested quantity
- Issued quantity
- Remaining O- units
- Date and time of the emergency issue

Every successful MCI issue is also recorded in the audit
trail.

---

## Why O- in an MCI?

According to the blood compatibility model used in this
project, O- can be given to all supported blood types.

Therefore, O- is especially useful in emergency situations
where blood may be needed before the recipient's blood type
is known.

---

## Effect on Routine Issue Strategy

O- is relatively rare in the population distribution used
by the system.

For this reason, during routine blood issuing, the system
attempts to preserve rare compatible blood types when
suitable alternatives are available.

This helps preserve O- inventory for emergency situations.

---

# Authentication and User Accounts

BECS requires users to authenticate before accessing
protected system functionality.

Each user account contains:

- Username
- Secure password hash
- Role
- Active / disabled status
- Creation timestamp

Passwords are not stored as plain text.

Password hashing and verification are implemented using
Werkzeug security functions.

Disabled accounts cannot log in to the system.

---

# Role-Based Access Control

BECS implements server-side role-based access control
(RBAC).

The system contains three user roles:

### ADMIN

The administrator has access to administrative and
operational functionality, including:

- Dashboard
- Blood Donation
- Routine Blood Issue
- Emergency MCI
- Records History
- Statistics
- Audit Trail
- User Management
- System Metadata
- XML Records Export

### BLOOD_BANK_USER

The blood bank worker performs normal operational
activities.

The role can access:

- Dashboard
- Blood Donation
- Routine Blood Issue
- Emergency MCI
- Records History
- Statistics

The role cannot access administrative functions such as
User Management, Metadata, or the Audit Trail.

### RESEARCH_STUDENT

The research student receives restricted access intended
for analysis of non-identifying system data.

The role can access:

- Dashboard
- De-identified Records History
- Statistics

The research student cannot access:

- Donor ID
- Donor full name
- Blood Donation
- Routine Blood Issue
- Emergency MCI
- Audit Trail
- User Management
- System Metadata
- Full XML records export

Authorization is enforced on the server and does not rely
only on hiding navigation links.

Unauthorized access to protected routes is rejected.

---

# HIPAA-Inspired Privacy Controls

The current version introduces privacy and access-control
mechanisms inspired by healthcare privacy principles
discussed as part of the assignment.

Donor identifying information is treated as sensitive
information within the application.

Operational users who require the information for blood
bank activities can access it.

Research students receive a de-identified view.

For the RESEARCH_STUDENT role:

- Donor names are hidden
- Donor IDs are hidden
- Donor identity fields are excluded from search
- Administrative records are inaccessible
- Full XML export is inaccessible

This demonstrates the principle of limiting access to
identifying information according to the user's role and
purpose.

These controls are educational examples and should not be
interpreted as full HIPAA compliance.

---

# User Management

Administrators can manage application users through the
User Management interface.

Administrators can:

- Create new users
- Assign a role
- View account status
- Disable accounts
- Re-enable accounts

Supported roles are:

- ADMIN
- BLOOD_BANK_USER
- RESEARCH_STUDENT

The system prevents an administrator from disabling their
own currently authenticated account.

User management actions are recorded in the audit trail.

Passwords and password hashes are not displayed in the
User Management interface or written to the audit trail.

---

# Electronic Record History

BECS preserves historical records instead of deleting
issued blood units.

Each blood unit has a status:

- AVAILABLE
- ISSUED

When a blood unit is issued, its status changes from
AVAILABLE to ISSUED and the issue timestamp is stored.

The original blood unit record remains in the database.

The Records History interface provides access to:

- Blood donation history
- Routine request history
- Emergency MCI history

The information displayed depends on the authenticated
user's role.

---

# Audit Trail

BECS includes a chronological audit trail for important
system and record-related activities.

Audit records contain information such as:

- Timestamp
- Action
- Record type
- Record ID
- User / actor
- User role
- Details

Examples of recorded actions include:

- DONATION_CREATED
- ROUTINE_ISSUE_COMPLETED
- EMERGENCY_MCI_ISSUE
- RECORDS_EXPORTED
- LOGIN_SUCCESS
- LOGIN_FAILED
- LOGOUT
- USER_CREATED
- USER_ENABLED
- USER_DISABLED

The Audit Trail interface is available only to
administrators.

Audit records are displayed from newest to oldest.

The web application provides a read-only view of audit
records.

Legacy audit records created before user authentication
was introduced may not contain actor information.

---

# Search and Filtering

The system provides search and filtering capabilities for
stored records.

## Audit Trail

Administrators can filter audit records by action type and
search stored audit information.

## Records History

Historical records can be filtered by record type:

- Blood Donations
- Routine Requests
- Emergency MCI

Search behavior is role-aware.

Operational users can search relevant stored information,
including donor information where authorized.

Research students cannot use donor identity fields to
retrieve identifying donor records.

---

# Statistics

The Statistics page provides an overview of current system
data.

It displays:

- Total donations
- Available blood units
- Issued blood units
- Total routine requests
- Units issued through routine requests
- Total MCI events
- Units issued during MCI events

The system also displays blood unit statistics for each
supported blood type, including:

- Total units
- Available units
- Issued units

The Statistics page can provide aggregate information
without requiring donor identity information.

---

# System Metadata

Administrators have access to a System Metadata page.

The page provides an administrative overview of stored
system records, including:

- Total users
- Active users
- Total blood units
- Available blood units
- Issued blood units
- Total routine requests
- Total emergency MCI records
- Total audit records

The Metadata page is restricted to the ADMIN role.

---

# XML Records Export

BECS supports exporting stored electronic records to a
portable XML file.

The export contains:

- Blood donation records
- Routine request records
- Emergency MCI records
- Audit trail records

Because the complete export may contain identifying donor
information, full XML export is restricted to
administrators.

The generated file contains a generation timestamp and
preserves stored information in a structured format.

Each successful export operation is itself recorded in the
audit trail as:

`RECORDS_EXPORTED`

---

# Security Controls

The current version includes several security mechanisms
inspired by cybersecurity principles discussed in the
assignment.

## Password Protection

Passwords are stored as secure password hashes rather than
plain-text passwords.

## Authentication

Protected application functionality requires an
authenticated user session.

## Role-Based Authorization

Access to protected functionality is checked according to
the authenticated user's role.

Authorization is enforced on the server side.

## CSRF Protection

BECS uses Flask-WTF CSRF protection for state-changing
POST requests.

Forms include CSRF tokens that are validated by the
server before processing the request.

## Session Security

The application configures:

- HttpOnly session cookies
- SameSite=Lax session cookies
- Permanent authenticated sessions
- 30-minute session timeout

The session timeout is refreshed while the authenticated
user remains active.

In a production HTTPS deployment, Secure cookies should
also be enabled.

## Login Auditing

Successful and failed login attempts are recorded in the
audit trail.

Passwords are never written to the audit trail.

## Account Disabling

Administrators can disable accounts that should no longer
be permitted to authenticate.

---

# Blood Types

The system supports the following blood types:

- A+
- O+
- B+
- AB+
- A-
- O-
- B-
- AB-

---

# Blood Type Distribution

The system uses the population distribution supplied in
the assignment:

| Blood Type | Distribution |
|------------|-------------:|
| O+ | 32% |
| A+ | 34% |
| B+ | 17% |
| AB+ | 7% |
| O- | 3% |
| A- | 4% |
| B- | 2% |
| AB- | 1% |

---

# Database

The application uses SQLite through Flask-SQLAlchemy.

The database stores:

- Users
- Blood units
- Routine blood requests
- Emergency MCI records
- Audit trail records

Issued blood units are not deleted.

Instead, their status is changed from `AVAILABLE` to
`ISSUED`, and the issue timestamp is stored.

This allows the application to preserve historical records
while only counting `AVAILABLE` units as current inventory.

The local SQLite database is excluded from Git using
`.gitignore`.

---

# Project Structure

```text
BECS-Blood-Bank-System/
│
├── src/
│   ├── __init__.py
│   ├── blood_types.py
│   ├── blood_bank.py
│   ├── models.py
│   ├── audit_service.py
│   ├── export_service.py
│   ├── auth.py
│   └── user_roles.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── donation.html
│   ├── routine_issue.html
│   ├── emergency.html
│   ├── records_history.html
│   ├── statistics.html
│   ├── audit_trail.html
│   ├── admin_users.html
│   └── metadata.html
│
├── static/
│   └── css/
│       └── style.css
│
├── tests/
│   ├── __init__.py
│   └── test_part11.py
│
├── app.py
├── create_admin.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/SafaaOzil/BECS-Blood-Bank-System.git
```

Enter the project directory:

```bash
cd BECS-Blood-Bank-System
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

# Secret Key Configuration

BECS uses a Flask secret key for session and CSRF
protection.

The application contains a development fallback so that
the project can run locally.

For a production environment, a unique secret key should
be supplied using the `BECS_SECRET_KEY` environment
variable rather than relying on the development fallback.

Example for PowerShell:

```powershell
$env:BECS_SECRET_KEY="replace-with-a-secure-random-secret"
```

The secret value should not be committed to Git.

---

# Creating the First Administrator

Before using the protected system, create an administrator
account:

```bash
python create_admin.py
```

The script requests the administrator credentials
interactively.

The password is hashed before it is stored in the
database.

After creating the administrator, the account can be used
to log in and create additional users through the User
Management page.

---

# Running the Application

Run:

```bash
python app.py
```

Then open the local address displayed by Flask in a web
browser.

The application will initially display the login page.

---

# Part 11-Inspired Record Controls

The extended version of BECS implements electronic
record-keeping features inspired by FDA 21 CFR Part 11
guidance discussed as part of the assignment.

These features include:

- Persistent electronic records
- Timestamped audit records
- User-attributed audit events
- Preservation of issued blood unit history
- Routine request history
- Emergency MCI history
- Search and filtering
- Electronic record statistics
- Electronic records export
- Authentication
- Role-based access restrictions

These features are implemented for academic purposes and
should not be interpreted as full regulatory compliance
with FDA 21 CFR Part 11.

---

# Cybersecurity-Inspired Controls

The project also demonstrates security mechanisms relevant
to software used in healthcare-related environments.

Implemented examples include:

- User authentication
- Password hashing
- Role-based authorization
- Least-privilege style access restrictions
- Login attempt auditing
- Account disabling
- Session timeout
- HttpOnly cookies
- SameSite cookies
- CSRF protection
- Restricted access to administrative functionality
- Restricted access to identifying donor information

These controls are educational examples.

They do not constitute a complete cybersecurity program,
security certification, or regulatory approval.

---

# Assignment Simplifications

The implementation follows the simplifications defined in
the original assignment.

The system works with whole blood and does not separately
manage blood components.

For the purpose of the assignment, stored blood is treated
as having no expiration limitation.

---

# Important Note

This project is an academic Biomedical Software Engineering
project.

The Part 11, healthcare privacy, and cybersecurity
mechanisms implemented in BECS are educational
demonstrations inspired by the requirements and guidance
discussed in the course.

The system should not be interpreted as fully compliant
with HIPAA, FDA 21 CFR Part 11, or other healthcare
regulations.

It is not intended for real clinical use and has not been
validated, certified, or approved for use in an actual
blood bank or healthcare environment.