"""Tests for the matching rules (SRS FR4 and FR5).

Run from the main project folder with:
    python -m unittest discover tests
These tests do not need a database: they give the matching code a seeker profile
and some opportunities directly, and check the result.
"""
import os
import sys
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import matching  # noqa: E402  (must come after the line above)


def days_from_today(n):
    return (date.today() + timedelta(days=n)).isoformat()


def opportunity(**changes):
    """An open opportunity that a 22-year-old graduate with Excel matches, unless changed."""
    opp = {"id": 1, "title": "Test opportunity", "type": "JOB", "status": "OPEN",
           "province": "Kigali City", "district": "Gasabo", "deadline": days_from_today(10),
           "min_age": 18, "max_age": 25, "education": "BACHELORS,MASTERS", "required_skills": "Excel, SQL"}
    opp.update(changes)
    return opp


SEEKER = {"age": 22, "province": "Kigali City", "district": "Gasabo",
          "education": "BACHELORS", "skills": "excel, communication"}


class TheThreeRules(unittest.TestCase):
    """FR4.1: a seeker matches only when age, education and skills all pass."""

    def test_all_three_rules_met(self):
        self.assertTrue(matching.check(SEEKER, opportunity())["eligible"])

    def test_too_old(self):
        self.assertFalse(matching.check(SEEKER, opportunity(min_age=25, max_age=30))["eligible"])

    def test_too_young(self):
        self.assertFalse(matching.check(dict(SEEKER, age=17), opportunity())["eligible"])

    def test_education_not_accepted(self):
        self.assertFalse(matching.check(SEEKER, opportunity(education="TVET"))["eligible"])

    def test_no_shared_skill(self):
        self.assertFalse(matching.check(SEEKER, opportunity(required_skills="Welding"))["eligible"])

    def test_no_skills_required_means_skills_rule_passes(self):
        self.assertTrue(matching.check(SEEKER, opportunity(required_skills=""))["eligible"])

    def test_skills_compare_without_capital_letters(self):
        self.assertTrue(matching.check(dict(SEEKER, skills="EXCEL"), opportunity())["eligible"])

    def test_district_not_stated_is_never_counted_as_the_seekers_district(self):
        result = matching.check(SEEKER, opportunity(district="Not stated"))
        self.assertTrue(result["eligible"])
        self.assertFalse(result["in_district"])

    def test_district_is_not_a_rule(self):
        far_away = opportunity(province="Western", district="Rusizi")
        self.assertTrue(matching.check(SEEKER, far_away)["eligible"])


class SkillWording(unittest.TestCase):
    """Skills match when all the words of one appear in the other; capital letters never matter."""

    def test_extra_word_still_matches(self):
        self.assertTrue(matching.same_skill("Excel", "MS Excel"))
        self.assertTrue(matching.same_skill("MS Excel", "excel"))

    def test_longer_phrase_matches(self):
        self.assertTrue(matching.same_skill("Customer service", "Excellent customer service"))

    def test_different_second_word_does_not_match(self):
        self.assertFalse(matching.same_skill("Data entry", "Data analysis"))

    def test_part_of_a_word_does_not_match(self):
        self.assertFalse(matching.same_skill("Java", "JavaScript"))

    def test_seeker_with_ms_excel_matches_an_excel_opportunity(self):
        result = matching.check(dict(SEEKER, skills="MS Excel"), opportunity(required_skills="Excel"))
        self.assertTrue(result["eligible"])
        self.assertEqual(result["skill_match"], "FULL")


class SkillMatchAndExplanation(unittest.TestCase):
    """FR4.3 and FR4.4: full or partial skill match, and the 'why' sentences."""

    def test_partial_skill_match(self):
        result = matching.check(SEEKER, opportunity(required_skills="Excel, SQL"))
        self.assertEqual(result["skill_match"], "PARTIAL")

    def test_full_skill_match(self):
        result = matching.check(SEEKER, opportunity(required_skills="Excel"))
        self.assertEqual(result["skill_match"], "FULL")

    def test_explanation_names_skills_had_and_missing(self):
        sentences = [text for _, text in matching.check(SEEKER, opportunity())["reasons"]]
        self.assertIn("Skills you have: Excel.", sentences)
        self.assertIn("Skills you are missing: SQL.", sentences)

    def test_missing_skills_are_marked_as_not_met(self):
        reasons = dict((text, met) for met, text in matching.check(SEEKER, opportunity())["reasons"])
        self.assertFalse(reasons["Skills you are missing: SQL."])

    def test_explanation_names_age_and_education(self):
        sentences = " ".join(text for _, text in matching.check(SEEKER, opportunity())["reasons"])
        self.assertIn("Age: you are 22; this is for ages 18 to 25.", sentences)
        self.assertIn("Education: Bachelor's is accepted.", sentences)


class DeadlinesAndOrder(unittest.TestCase):
    """FR4.2, FR5.1 and FR5.3: hide expired ones, own district first, closest deadline first."""

    def test_expired_opportunity_is_hidden(self):
        self.assertEqual(matching.match_all(SEEKER, [opportunity(deadline=days_from_today(-1))]), [])

    def test_last_day_is_still_shown(self):
        self.assertEqual(len(matching.match_all(SEEKER, [opportunity(deadline=days_from_today(0))])), 1)

    def test_closed_opportunity_is_hidden(self):
        self.assertEqual(matching.match_all(SEEKER, [opportunity(status="CLOSED")]), [])

    def test_own_district_first_then_closest_deadline(self):
        opps = [opportunity(id=1, title="Elsewhere, soon", district="Huye", province="Southern", deadline=days_from_today(1)),
                opportunity(id=2, title="Own district, later", deadline=days_from_today(20)),
                opportunity(id=3, title="Own district, sooner", deadline=days_from_today(5))]
        titles = [m["opp"]["title"] for m in matching.match_all(SEEKER, opps)]
        self.assertEqual(titles, ["Own district, sooner", "Own district, later", "Elsewhere, soon"])

    def test_days_left_is_counted(self):
        result = matching.check(SEEKER, opportunity(deadline=days_from_today(7)))
        self.assertEqual(result["days_left"], 7)


class SplittingSkills(unittest.TestCase):
    """Skills are separated by commas (the label on the forms explains this)."""

    def test_commas_separate_skills(self):
        self.assertEqual(matching.split_skills("Excel, Customer service"), ["Excel", "Customer service"])

    def test_without_commas_it_is_one_skill(self):
        self.assertEqual(matching.split_skills("Excel Customer service"), ["Excel Customer service"])

    def test_repeated_skills_are_kept_once(self):
        self.assertEqual(matching.split_skills("Excel, Excel"), ["Excel"])


if __name__ == "__main__":
    unittest.main()
