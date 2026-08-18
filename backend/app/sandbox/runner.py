from .. import config
from .common import SandboxResult

__all__ = ["grade_submission", "SandboxResult"]


def grade_submission(harness_template: str, user_code: str) -> SandboxResult:
    """Compile+run `user_code` spliced into `harness_template`, dispatched to
    whichever backend SANDBOX_MODE selects. See docker_runner.py vs
    subprocess_runner.py docstrings for the tradeoffs."""
    if config.SANDBOX_MODE == "docker":
        from . import docker_runner
        return docker_runner.run(harness_template, user_code)
    elif config.SANDBOX_MODE == "subprocess":
        from . import subprocess_runner
        return subprocess_runner.run(harness_template, user_code)
    else:
        raise ValueError(f"Unknown SANDBOX_MODE: {config.SANDBOX_MODE!r} (expected 'docker' or 'subprocess')")
