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


def valid_location(province, district):
    return province in LOCATIONS and district in LOCATIONS[province]
