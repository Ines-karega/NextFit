"""Matching logic (SRS FR4).

A seeker matches an opportunity only if ALL THREE rules pass:
  1. age is inside the opportunity's age range
  2. education level is one the opportunity accepts
  3. the seeker has at least one required skill (or none are required)
District is NOT a rule. It only changes the order of the list.
"""
import re
from datetime import date

import db
from rwanda import EDU_LABEL


def split_skills(text):
    """'Excel, Communication' -> ['Excel', 'Communication']"""
    skills = []
    for piece in text.replace(";", ",").replace("\n", ",").split(","):
        piece = piece.strip()
        if piece and piece not in skills:
            skills.append(piece)
    return skills


def skill_words(skill):
    """'MS Excel' -> {'ms', 'excel'}: the words of a skill, in lowercase, without punctuation."""
    return set(re.findall(r"[a-z0-9]+", skill.lower()))


def same_skill(a, b):
    """Two skills count as the same when all the words of one appear in the other.
    'Excel' and 'MS Excel' match, and so do 'EXCEL' and 'excel' (capital letters never matter).
    'Data entry' and 'Data analysis' do not match, because neither contains all the other's words."""
    words_a, words_b = skill_words(a), skill_words(b)
    if not words_a or not words_b:
        return False
    return words_a <= words_b or words_b <= words_a


def has_skill(skill, my_skills):
    """True if any of the seeker's skills counts as the same as this skill."""
    return any(same_skill(skill, mine) for mine in my_skills)


def skills_in_demand(profile, opportunities, how_many=5):
    """The skills asked for most often in open opportunities.
    Returns a list of (skill, number_of_opportunities, you_have_it)."""
    my_skills = split_skills(profile["skills"])
    counts = {}
    names = {}
    for opp in opportunities:
        if not is_open(opp):
            continue
        for skill in split_skills(opp["required_skills"]):
            key = skill.lower()
            counts[key] = counts.get(key, 0) + 1
            names[key] = skill
    top = sorted(counts, key=lambda k: -counts[k])[:how_many]
    return [(names[k], counts[k], has_skill(names[k], my_skills)) for k in top]


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
    accepted = [level.strip() for level in opp["education"].split(",") if level.strip()]
    edu_ok = profile["education"] in accepted

    # Rule 3: skills ('Excel' matches 'excel' and 'MS Excel'; see same_skill above)
    my_skills = split_skills(profile["skills"])
    required = split_skills(opp["required_skills"])
    have = [s for s in required if has_skill(s, my_skills)]
    missing = [s for s in required if not has_skill(s, my_skills)]
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
    accepted_names = ", ".join(EDU_LABEL.get(e, e) for e in accepted)
    if edu_ok:
        reasons.append((True, f"Education: {EDU_LABEL[profile['education']]} is accepted."))
    else:
        reasons.append((False, f"Education: this accepts {accepted_names}."))
    if len(required) == 0:
        reasons.append((True, "Skills: none are required."))
    if len(have) > 0:
        reasons.append((True, "Skills you have: " + ", ".join(have) + "."))
    if len(missing) > 0:
        # shown with a cross, because these are skills the seeker does not have yet
        reasons.append((False, "Skills you are missing: " + ", ".join(missing) + "."))

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


def get_matches(seeker_id):
    """The seeker's matched list (SRS B.4 steps 4 to 15): load their profile and the
    open opportunities through the data access layer, then check and sort them."""
    profile = db.get_profile(seeker_id)
    opportunities = db.get_open_opportunities(date.today().isoformat())
    return match_all(profile, opportunities)


def match_all(profile, opportunities):
    """Return only the open opportunities this seeker qualifies for, sorted."""
    matches = []
    for opp in opportunities:
        if is_open(opp):
            result = check(profile, opp)
            if result["eligible"]:
                matches.append(result)
    matches.sort(key=sort_key)
    return matches
