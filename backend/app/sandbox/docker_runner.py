"""
Production sandbox backend: compiles and runs each submission inside a
fresh, disposable container (built from ../../sandbox-runner/Dockerfile),
with no network access and hard CPU/memory/process limits. This is what
SANDBOX_MODE=docker uses, and is the intended mode for the self-hosted
docker-compose setup.

Requires the `docker` CLI to be available and pointed at a reachable daemon
(the backend's Dockerfile installs the CLI; docker-compose.yml mounts the
host's /var/run/docker.sock so it can talk to the host daemon - this is the
"Docker-outside-of-Docker" pattern, not Docker-in-Docker).
"""
import os
import shutil
import subprocess
import tempfile

from .. import config
from .common import SandboxResult, build_source, make_result

COMPILE_FAIL_MARKER = "__SANDBOX_COMPILE_FAILED__"
TIMEOUT_MARKER = "__SANDBOX_TIMEOUT__"

_RUN_SCRIPT = """\
set -o pipefail
g++ -O2 -std=c++17 -Wall -o main main.cpp 2> compile_stderr.txt
if [ $? -ne 0 ]; then
  echo "{compile_marker}"
  cat compile_stderr.txt
  exit 1
fi
timeout {timeout}s ./main
code=$?
if [ $code -eq 124 ]; then
  echo "{timeout_marker}"
fi
exit $code
""".strip()


def run(harness_template: str, user_code: str) -> SandboxResult:
    if not shutil.which("docker"):
        return SandboxResult(False, 0, 0, "", "docker CLI is not available in this environment.")

    source = build_source(harness_template, user_code)
    with tempfile.TemporaryDirectory(prefix="cpp-sandbox-") as tmpdir:
        src_path = os.path.join(tmpdir, "main.cpp")
        script_path = os.path.join(tmpdir, "run.sh")
        with open(src_path, "w") as f:
            f.write(source)
        with open(script_path, "w") as f:
            f.write(_RUN_SCRIPT.format(
                compile_marker=COMPILE_FAIL_MARKER,
                timeout_marker=TIMEOUT_MARKER,
                timeout=config.SANDBOX_TIMEOUT_SECONDS,
            ))
        # The sandbox image runs as uid 10001; make the bind-mounted dir
        # writable by it regardless of the host uid running this process.
        os.chmod(tmpdir, 0o777)
        os.chmod(src_path, 0o666)
        os.chmod(script_path, 0o777)

        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", config.SANDBOX_MEMORY_LIMIT,
            "--cpus", config.SANDBOX_CPU_LIMIT,
            "--pids-limit", "64",
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
            "-v", f"{tmpdir}:/sandbox:rw",
            "-w", "/sandbox",
            "--user", "10001:10001",
            config.SANDBOX_IMAGE,
            "bash", "run.sh",
        ]

        outer_timeout = config.SANDBOX_TIMEOUT_SECONDS + 20  # compile + container startup slack
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=outer_timeout)
        except subprocess.TimeoutExpired:
            return make_result(1, "", "", timed_out=True)

        stdout = proc.stdout

        if COMPILE_FAIL_MARKER in stdout:
            compile_error = stdout.split(COMPILE_FAIL_MARKER, 1)[1].strip()
            return make_result(1, "", "", False, compile_error=compile_error or "Compilation failed.")

        if TIMEOUT_MARKER in stdout:
            return make_result(1, stdout.replace(TIMEOUT_MARKER, "").strip(), proc.stderr, timed_out=True)

        return make_result(proc.returncode, stdout, proc.stderr, timed_out=False)
