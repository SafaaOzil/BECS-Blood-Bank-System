# BECS - Blood Bank Management System

BECS is a web-based Blood Bank Management System developed
as part of a Biomedical Software Engineering assignment.

The system manages blood donations, routine blood issuing,
emergency blood issuing during a Mass Casualty Incident
(MCI), electronic record history, audit trails, statistics,
and records export.

The extended version of the project includes electronic
record management features inspired by the record-keeping
principles discussed in FDA 21 CFR Part 11 guidance.

---

## Technologies

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML
- CSS
- Jinja2
- XML
- Pytest

---

## Main Features

### 1. Blood Donation

The system allows blood bank staff to register a new
blood donation.

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

### 2. Routine Blood Issue

The user selects:

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
rarer compatible blood types.

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

### 3. Emergency MCI

During a Mass Casualty Incident, the system provides
emergency access to O- blood.

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
where blood may be needed urgently.

---

## Effect on Routine Issue Strategy

O- is relatively rare in the population distribution used
by the system.

For this reason, during routine blood issuing, the system
prefers compatible and more common alternatives when
possible.

This helps preserve O- inventory for emergency situations.

---

## Electronic Record History

The extended version of BECS preserves historical records
instead of deleting issued blood units.

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

---

## Audit Trail

BECS includes a chronological audit trail for important
record-related activities.

The audit trail records:

- Timestamp
- Action
- Record type
- Record ID
- Details

The following actions are currently recorded:

- DONATION_CREATED
- ROUTINE_ISSUE_COMPLETED
- EMERGENCY_MCI_ISSUE
- RECORDS_EXPORTED

The Audit Trail interface is read-only through the web
application.

Audit records are displayed from newest to oldest.

---

## Search and Filtering

The system provides search and filtering capabilities for
stored records.

### Audit Trail

Audit records can be filtered by action type and searched
using record information or details.

### Records History

Historical records can be filtered by record type:

- Blood Donations
- Routine Requests
- Emergency MCI

Donation and routine request records can also be searched
using relevant stored information such as blood type,
donor information, destination, or status.

---

## Statistics

The Statistics page provides an overview of the current
system data.

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

---

## XML Records Export

BECS supports exporting stored electronic records to a
portable XML file.

The XML export contains:

- Blood donation records
- Routine request records
- Emergency MCI records
- Audit trail records

The generated file contains a generation timestamp and
preserves the stored information in a structured format.

Each successful export operation is itself recorded in the
audit trail as:

`RECORDS_EXPORTED`

---

## Blood Types

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

## Blood Type Distribution

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

## Database

The application uses SQLite through Flask-SQLAlchemy.

The database stores:

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

## Project Structure

```text
BECS-Blood-Bank-System/
│
├── src/
│   ├── __init__.py
│   ├── blood_types.py
│   ├── blood_bank.py
│   ├── models.py
│   ├── audit_service.py
│   └── export_service.py
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── donation.html
│   ├── routine_issue.html
│   ├── emergency.html
│   ├── records_history.html
│   ├── statistics.html
│   └── audit_trail.html
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
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Installation

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

## Running the Application

Run:

```bash
python app.py
```

Then open the local address displayed by Flask in a web
browser.

---

## Automated Tests

The project includes automated regression tests using
Pytest.

The tests use a separate in-memory SQLite database:

```text
sqlite:///:memory:
```

Therefore, running the tests does not modify the normal
application database.

The automated tests cover:

- Donation persistence and audit logging
- Routine blood issuing
- Partial routine issuing
- Emergency MCI issuing
- Record history creation
- Audit trail creation
- XML export structure

Run the tests with:

```bash
pytest -v
```

The current automated test suite contains 5 tests.

---

## Assignment Simplifications

The implementation follows the simplifications defined in
the assignment.

The system works with whole blood and does not separately
manage blood components.

For the purpose of the assignment, stored blood is treated
as having no expiration limitation.

---

## Part 11-Inspired Record Controls

The extended version of BECS implements electronic
record-keeping features inspired by the FDA 21 CFR Part 11
guidance discussed as part of the assignment.

These features include:

- Persistent electronic records
- Timestamped audit records
- Preservation of issued blood unit history
- Routine request history
- Emergency MCI history
- Search and filtering
- Electronic record statistics
- Export of records to XML

These features are implemented for academic purposes and
should not be interpreted as full regulatory compliance
with FDA 21 CFR Part 11.

---

## Important Note

This project is an academic Biomedical Software Engineering
project.

It is not intended for real clinical use and has not been
validated, certified, or approved for use in an actual
blood bank or healthcare environment.