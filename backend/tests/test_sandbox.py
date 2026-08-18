from app.content.coding_bank import CODING_PROBLEMS
from app.sandbox.runner import grade_submission

from .solutions import SOLUTIONS_BY_TITLE


def test_every_seeded_problem_passes_its_known_solution():
    for problem in CODING_PROBLEMS:
        solution = SOLUTIONS_BY_TITLE[problem["title"]]
        result = grade_submission(problem["harness_template"], solution)
        assert result.passed, f"{problem['title']} failed: {result.error}"
        assert result.tests_total > 0
        assert result.tests_passed == result.tests_total


def test_incomplete_starter_code_does_not_pass():
    problem = CODING_PROBLEMS[0]
    result = grade_submission(problem["harness_template"], problem["starter_code"])
    assert not result.passed


def test_invalid_cpp_reports_compile_error_not_a_crash():
    problem = CODING_PROBLEMS[0]
    result = grade_submission(problem["harness_template"], "this is not valid c++")
    assert not result.passed
    assert result.error  # compiler diagnostics should be surfaced
    assert result.tests_total == 0


def test_infinite_loop_times_out_instead_of_hanging():
    problem = CODING_PROBLEMS[0]
    stuck = "bool isPalindrome(const string& s) { while(true) {} return true; }"
    result = grade_submission(problem["harness_template"], stuck)
    assert not result.passed
    assert "timed out" in result.error.lower()
