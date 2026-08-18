import re
from dataclasses import dataclass

RESULT_LINE_RE = re.compile(r"RESULT:(\d+)/(\d+)")


@dataclass
class SandboxResult:
    passed: bool
    tests_passed: int
    tests_total: int
    output: str
    error: str


def build_source(harness_template: str, user_code: str) -> str:
    if "{{USER_CODE}}" not in harness_template:
        raise ValueError("harness_template is missing the {{USER_CODE}} placeholder")
    return harness_template.replace("{{USER_CODE}}", user_code)


def parse_result(stdout: str) -> tuple[int, int]:
    """Find the RESULT:<passed>/<total> marker line the harness prints last."""
    match = None
    for m in RESULT_LINE_RE.finditer(stdout):
        match = m  # take the last occurrence in case user code prints its own text
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def make_result(returncode: int, stdout: str, stderr: str, timed_out: bool, compile_error: str = "") -> SandboxResult:
    if compile_error:
        return SandboxResult(False, 0, 0, "", compile_error)
    if timed_out:
        return SandboxResult(False, 0, 0, stdout, "Execution timed out (possible infinite loop).")
    tests_passed, tests_total = parse_result(stdout)
    if returncode != 0:
        return SandboxResult(
            False, tests_passed, tests_total, stdout,
            stderr or f"Program exited with non-zero status {returncode} (crash or failed assertion).",
        )
    passed = tests_total > 0 and tests_passed == tests_total
    return SandboxResult(passed, tests_passed, tests_total, stdout, stderr)
