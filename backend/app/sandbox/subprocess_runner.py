"""
Local-dev sandbox backend: compiles and runs the submission as a plain
subprocess on the host, with rlimits as a lightweight guard rail.

This is NOT a real sandbox - it shares the host's filesystem, network, and
kernel. It exists so you can develop/test without a Docker daemon running.
For anything other than "just me, on my own machine, at localhost", use
SANDBOX_MODE=docker (see docker_runner.py), which isolates each submission
in a disposable, network-disabled container.
"""
import os
import resource
import shutil
import subprocess
import tempfile

from .. import config
from .common import SandboxResult, build_source, make_result

CPU_SECONDS_LIMIT = config.SANDBOX_TIMEOUT_SECONDS
MEMORY_BYTES_LIMIT = 256 * 1024 * 1024  # 256MB address space


def _limit_resources():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS_LIMIT, CPU_SECONDS_LIMIT))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES_LIMIT, MEMORY_BYTES_LIMIT))
    # No forking bombs / excessive processes.
    resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))


def run(harness_template: str, user_code: str) -> SandboxResult:
    if not shutil.which("g++"):
        return SandboxResult(False, 0, 0, "", "g++ is not installed in this environment.")

    source = build_source(harness_template, user_code)
    with tempfile.TemporaryDirectory(prefix="cpp-sandbox-") as tmpdir:
        src_path = os.path.join(tmpdir, "main.cpp")
        bin_path = os.path.join(tmpdir, "main")
        with open(src_path, "w") as f:
            f.write(source)

        compile_proc = subprocess.run(
            ["g++", "-O2", "-std=c++17", "-Wall", "-o", bin_path, src_path],
            capture_output=True, text=True, timeout=config.SANDBOX_TIMEOUT_SECONDS,
        )
        if compile_proc.returncode != 0:
            return make_result(1, "", "", False, compile_error=compile_proc.stderr[-4000:])

        try:
            run_proc = subprocess.run(
                [bin_path],
                capture_output=True, text=True,
                timeout=config.SANDBOX_TIMEOUT_SECONDS,
                cwd=tmpdir,
                preexec_fn=_limit_resources,
            )
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            return make_result(1, stdout, "", timed_out=True)

        return make_result(run_proc.returncode, run_proc.stdout, run_proc.stderr, timed_out=False)
