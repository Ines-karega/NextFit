"""Rwanda's province and district structure (SRS 2.5), plus fixed option lists."""

LOCATIONS = {
    "Kigali City": ["Gasabo", "Kicukiro", "Nyarugenge"],
    "Southern": ["Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe",
                 "Nyanza", "Nyaruguru", "Ruhango"],
    "Western": ["Karongi", "Ngororero", "Nyabihu", "Nyamasheke",
                "Rubavu", "Rusizi", "Rutsiro"],
    "Northern": ["Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo"],
    "Eastern": ["Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma",
                "Nyagatare", "Rwamagana"],
}

# (stored value, label shown to the user) - same list for seekers and admins
EDUCATION_LEVELS = [
    ("SECONDARY", "Secondary"),
    ("TVET", "TVET"),
    ("BACHELORS", "Bachelor's"),
    ("MASTERS", "Master's"),
    ("PHD", "PhD"),
]
EDU_LABEL = dict(EDUCATION_LEVELS)

OPP_TYPES = [("TRAINING", "Training"), ("INTERNSHIP", "Internship"), ("JOB", "Job")]
TYPE_LABEL = dict(OPP_TYPES)

WORK_MODES = [("ON_SITE", "On-site"), ("REMOTE", "Remote"), ("HYBRID", "Hybrid")]
MODE_LABEL = dict(WORK_MODES)

STATUSES = ["Secondary student", "TVET student", "University student",
            "Graduate", "Unemployed", "Employed", "Other"]

MIN_SEEKER_AGE = 16
MAX_SEEKER_AGE = 30


# Used when an advert names the province (for example "Kigali") but not the district.
# Only opportunities can use it; a seeker always chooses their real district.
NOT_STATED = "Not stated"


def valid_location(province, district, allow_not_stated=False):
    if province not in LOCATIONS:
        return False
    return district in LOCATIONS[province] or (allow_not_stated and district == NOT_STATED)
