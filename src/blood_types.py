# Supported blood types in the BECS system
BLOOD_TYPES = [
    "A+",
    "O+",
    "B+",
    "AB+",
    "A-",
    "O-",
    "B-",
    "AB-"
]


# Blood donation compatibility.
# Key   = donor blood type
# Value = blood types that can receive blood from this donor
DONATION_COMPATIBILITY = {
    "A+":  ["A+", "AB+"],
    "O+":  ["O+", "A+", "B+", "AB+"],
    "B+":  ["B+", "AB+"],
    "AB+": ["AB+"],
    "A-":  ["A+", "A-", "AB+", "AB-"],
    "O-":  ["A+", "O+", "B+", "AB+", "A-", "O-", "B-", "AB-"],
    "B-":  ["B+", "B-", "AB+", "AB-"],
    "AB-": ["AB+", "AB-"]
}


# Blood type distribution in Israel according to the assignment
BLOOD_TYPE_DISTRIBUTION = {
    "O+": 32.0,
    "A+": 34.0,
    "B+": 17.0,
    "AB+": 7.0,
    "O-": 3.0,
    "A-": 4.0,
    "B-": 2.0,
    "AB-": 1.0
}


def is_compatible(donor_type, recipient_type):
    """
    Check whether a donor blood type can be given
    to a recipient blood type.
    """
    if donor_type not in BLOOD_TYPES:
        return False

    if recipient_type not in BLOOD_TYPES:
        return False

    return recipient_type in DONATION_COMPATIBILITY[donor_type]
def get_compatible_donors(recipient_type):
    """
    Return all blood types that can donate to the given recipient.
    """

    if recipient_type not in BLOOD_TYPES:
        raise ValueError("Invalid blood type.")

    compatible_donors = []

    for donor_type in BLOOD_TYPES:
        if is_compatible(donor_type, recipient_type):
            compatible_donors.append(donor_type)

    return compatible_donors