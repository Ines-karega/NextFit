"""Matching logic (SRS FR4).

A seeker matches an opportunity only if ALL THREE rules pass:
  1. age is inside the opportunity's age range
  2. education level is one the opportunity accepts
  3. the seeker has at least one required skill (or none are required)
District is NOT a rule. It only changes the order of the list.
"""
from datetime import date

from rwanda import EDU_LABEL


def split_skills(text):
    """'Excel, Communication' -> ['Excel', 'Communication']"""
    skills = []
    for piece in text.replace(";", ",").replace("\n", ",").split(","):
        piece = piece.strip()
        if piece and piece not in skills:
            skills.append(piece)
    return skills


def days_until(deadline_text):
    """How many days from today until the deadline (a 'YYYY-MM-DD' text)."""
    return (date.fromisoformat(deadline_text) - date.today()).days


def is_open(opp):
    """An opportunity is open if the admin has not closed it and the deadline has not passed."""
    return opp["status"] == "OPEN" and days_until(opp["deadline"]) >= 0


def check(profile, opp):
    """Compare one seeker with one opportunity. Returns a dictionary with the result."""
    # Rule 1: age
    age_ok = opp["min_age"] <= profile["age"] <= opp["max_age"]

    # Rule 2: education
    accepted = opp["education"].split(",")
    edu_ok = profile["education"] in accepted

    # Rule 3: skills (compare in lowercase so 'Excel' equals 'excel')
    my_skills = [s.lower() for s in split_skills(profile["skills"])]
    required = split_skills(opp["required_skills"])
    have = [s for s in required if s.lower() in my_skills]
    missing = [s for s in required if s.lower() not in my_skills]
    skills_ok = len(required) == 0 or len(have) > 0

    # FR4.4: full or partial skill match
    if len(missing) == 0:
        skill_match = "FULL"
    elif len(have) > 0:
        skill_match = "PARTIAL"
    else:
        skill_match = "NONE"   # only seen on the Browse page, never on matches

    # FR4.3: the "why" explanation, as (passed?, sentence) pairs
    reasons = []
    reasons.append((age_ok, f"Age: you are {profile['age']}; this is for ages {opp['min_age']} to {opp['max_age']}."))
    accepted_names = ", ".join(EDU_LABEL[e] for e in accepted)
    if edu_ok:
        reasons.append((True, f"Education: {EDU_LABEL[profile['education']]} is accepted."))
    else:
        reasons.append((False, f"Education: this accepts {accepted_names}."))
    if len(required) == 0:
        reasons.append((True, "Skills: none are required."))
    if len(have) > 0:
        reasons.append((True, "Skills you have: " + ", ".join(have) + "."))
    if len(missing) > 0:
        reasons.append((skills_ok, "Skills you are missing: " + ", ".join(missing) + "."))

    return {
        "opp": opp,
        "eligible": age_ok and edu_ok and skills_ok,
        "skill_match": skill_match,
        "days_left": days_until(opp["deadline"]),
        "in_district": opp["district"] == profile["district"],
        "reasons": reasons,
    }


def sort_key(result):
    """Own district first (False sorts before True), then closest deadline."""
    return (not result["in_district"], result["opp"]["deadline"])


def get_matches(profile, opportunities):
    """Return only the open opportunities this seeker qualifies for, sorted."""
    matches = []
    for opp in opportunities:
        if is_open(opp):
            result = check(profile, opp)
            if result["eligible"]:
                matches.append(result)
    matches.sort(key=sort_key)
    return matches
