# BECS - Blood Bank Management System

BECS is a web-based Blood Bank Management System developed
as part of a Biomedical Software Engineering assignment.

The system manages blood donations, routine blood issuing,
and emergency blood issuing during a Mass Casualty Incident
(MCI).

## Technologies

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML
- CSS
- Jinja2

## Main Features

### 1. Blood Donation

The system allows blood bank staff to register a new
blood donation.

For every donation, the following information is stored:

- Blood type
- Donation date
- Donor ID
- Donor full name

The system validates the entered information before storing
the blood unit in the database.

### 2. Routine Blood Issue

The user selects:

- Requested blood type
- Number of required blood units

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

### 3. Emergency MCI

During a Mass Casualty Incident, the system provides
emergency access to O- blood.

The interface displays the maximum number of O- units
currently available.

The maximum quantity is selected by default, but the user
may select a smaller quantity.

The system prevents issuing more O- units than are
available in inventory.

## Why O- in an MCI?

According to the blood compatibility model used in this
project, O- can be given to all supported blood types.

Therefore, O- is especially useful in emergency situations
where blood may be needed urgently.

## Effect on Routine Issue Strategy

O- is relatively rare in the population distribution used
by the system.

For this reason, during routine blood issuing, the system
prefers compatible and more common alternatives when
possible.

This helps preserve O- inventory for emergency situations.

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

## Blood Type Distribution

The system uses the population distribution supplied in
the assignment:

| Blood Type | Distribution |
|------------|--------------|
| O+ | 32% |
| A+ | 34% |
| B+ | 17% |
| AB+ | 7% |
| O- | 3% |
| A- | 4% |
| B- | 2% |
| AB- | 1% |

## Database

The application uses SQLite through Flask-SQLAlchemy.

Each available blood unit is stored in the database.

When a blood unit is issued, it is removed from the
available inventory.

The local SQLite database is excluded from Git using
`.gitignore`.

## Project Structure

```text
BECS-Blood-Bank-System/
│
├── src/
│   ├── __init__.py
│   ├── blood_types.py
│   ├── blood_bank.py
│   └── models.py
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── donation.html
│   ├── routine_issue.html
│   └── emergency.html
│
├── static/
│   └── css/
│       └── style.css
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md

Installation
Clone the repository:
git clone https://github.com/SafaaOzil/BECS-Blood-Bank-System.git

Enter the project directory:
cd BECS-Blood-Bank-System

Create a virtual environment:
python -m venv .venv

Activate the virtual environment on Windows:
.venv\Scripts\activate

Install the required packages:
pip install -r requirements.txt

Running the Application
Run:
python app.py

Then open the local address displayed by Flask in a web
browser.


Assignment Simplifications
The implementation follows the simplifications defined in
the assignment.
The system works with whole blood and does not separately
manage blood components.
For the purpose of the assignment, stored blood is treated
as having no expiration limitation.
Important Note
This project is an academic software engineering project.
It is not intended for real clinical use.