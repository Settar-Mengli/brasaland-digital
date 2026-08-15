"""Prove reporting and rfp Celery queues are isolated on a real Redis broker.

Verdict is queue depth plus THAT worker's log. AsyncResult is never used
(shared Redis result backend cannot attribute a worker).

DISPOSABLE Redis only. The script FLUSHDB's the configured database. Never
point REDIS_URL at the live Compose broker.

How to run (from repo root, after ``uv sync`` in both service dirs)::

    $env:REDIS_URL = "redis://localhost:6380/0"
    $env:CELERY_ISOLATION_ALLOW_FLUSH = "1"
    uv run --directory services/reporting --python 3.13 python ../../scripts/test_celery_queue_isolation.py
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"

REPORTING_TASK = "reporting.run_pipeline_task"
RFP_TASK = "rfp.process_rfp"
WRONG_WORKER_WAIT_SECONDS = 8.0
WORKER_READY_TIMEOUT_SECONDS = 60.0
TEARDOWN_WAIT_SECONDS = 15.0
RUN_ID = uuid.uuid4().hex[:8]

_WIN_ENV_KEEP = frozenset(
    {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "WINDIR",
        "COMSPEC",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "TEMP",
        "TMP",
        "USERNAME",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "OS",
        "PROCESSOR_ARCHITECTURE",
        "NUMBER_OF_PROCESSORS",
        "PUBLIC",
        "ALLUSERSPROFILE",
        "COMPUTERNAME",
    }
)
_POSIX_ENV_KEEP = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TERM",
        "TMPDIR",
        "SHELL",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
    }
)


def _fail(message: str) -> None:
    raise AssertionError(message)


def _redis_url() -> str:
    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        _fail("REDIS_URL is required")
    return url


def _require_flush_opt_in() -> None:
    if os.environ.get("CELERY_ISOLATION_ALLOW_FLUSH") != "1":
        _fail(
            "Refusing to FLUSHDB without CELERY_ISOLATION_ALLOW_FLUSH=1 "
            "(disposable Redis only — not the Compose broker)"
        )


def _path_without_venvs(raw: str) -> str:
    kept: list[str] = []
    for part in raw.split(os.pathsep):
        if not part:
            continue
        parts = Path(part).parts
        if ".venv" in parts:
            continue
        kept.append(part)
    return os.pathsep.join(kept)


def _service_env() -> dict[str, str]:
    """OS + uv PATH, no parent venv. Each ``uv run`` uses cwd's project."""
    keep = _WIN_ENV_KEEP if sys.platform == "win32" else _POSIX_ENV_KEEP
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        if key.upper() in keep or key in keep:
            env[key] = value
    path = env.get("PATH", os.environ.get("PATH", ""))
    env["PATH"] = _path_without_venvs(path)
    env["REDIS_URL"] = _redis_url()
    env["DATABASE_URL"] = "sqlite:///:memory:"
    env["PYTHONPATH"] = str(DATA_ROOT)
    return env


def _run_in_service(service: str, code: str) -> str:
    proc = subprocess.run(
        ["uv", "run", "--python", "3.13", "python", "-c", code],
        cwd=str(REPO_ROOT / "services" / service),
        env=_service_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        _fail(
            f"{service} python -c failed (exit {proc.returncode}):\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout


def _flushdb() -> None:
    import redis

    client = redis.Redis.from_url(_redis_url())
    client.flushdb()
    client.close()


def _list_processes() -> list[tuple[int, str]]:
    if sys.platform == "win32":
        cmd = (
            "Get-CimInstance Win32_Process | ForEach-Object { "
            "if ($_.CommandLine) { '{0}`t{1}' -f $_.ProcessId, $_.CommandLine } }"
        )
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                cmd,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        rows: list[tuple[int, str]] = []
        for line in proc.stdout.splitlines():
            if "\t" not in line:
                continue
            pid_s, cmdline = line.split("\t", 1)
            try:
                rows.append((int(pid_s.strip()), cmdline))
            except ValueError:
                continue
        return rows
    proc = subprocess.run(
        ["ps", "-eo", "pid=,args="],
        capture_output=True,
        text=True,
        check=False,
    )
    rows = []
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        pid_s, _, args = stripped.partition(" ")
        try:
            rows.append((int(pid_s), args.strip()))
        except ValueError:
            continue
    return rows


def _processes_matching(needle: str) -> list[tuple[int, str]]:
    self_pid = os.getpid()
    return [
        (pid, cmd)
        for pid, cmd in _list_processes()
        if needle in cmd and pid != self_pid
    ]


def _kill_tree(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        )
        return
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def _assert_no_process_with(needle: str, timeout: float = TEARDOWN_WAIT_SECONDS) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _processes_matching(needle):
            return
        time.sleep(0.2)
    leftover = _processes_matching(needle)
    if leftover:
        formatted = "; ".join(f"pid={pid} {cmd}" for pid, cmd in leftover)
        _fail(f"orphan worker still running ({needle!r}): {formatted}")


# Matches both {service}-isolation-{run_id} and Celery's {service}-isolation@%h.
_ISOLATION_PREFIXES = ("reporting-isolation", "rfp-isolation")


def _sweep_leftover_isolation_workers() -> None:
    for needle in _ISOLATION_PREFIXES:
        for pid, _cmd in _processes_matching(needle):
            _kill_tree(pid)
    for needle in _ISOLATION_PREFIXES:
        _assert_no_process_with(needle)


def queue_depth(queue: str) -> int:
    """Message count via kombu passive declare (0 if the queue is absent)."""
    output = _run_in_service(
        "reporting",
        f"""
from celery_app import celery_app
with celery_app.connection_for_read() as conn:
    with conn.channel() as channel:
        try:
            declared = channel.queue_declare(queue={queue!r}, passive=True)
        except Exception as exc:
            name = type(exc).__name__
            text = str(exc).lower()
            if name in {{"NotFound", "ChannelError", "ResponseError"}} or "not exist" in text:
                print(0)
            else:
                raise
        else:
            if hasattr(declared, "message_count"):
                print(declared.message_count)
            else:
                print(declared[1])
""",
    )
    return int(output.strip().splitlines()[-1])


def enqueue_reporting() -> str:
    return _run_in_service(
        "reporting",
        "from tasks import run_pipeline_task; print(run_pipeline_task.delay(None).id)",
    ).strip().splitlines()[-1]


def enqueue_rfp() -> str:
    return _run_in_service(
        "rfp",
        'from tasks import process_rfp; print(process_rfp.delay("isolation-probe").id)',
    ).strip().splitlines()[-1]


class _Worker:
    def __init__(self, service: str, queue: str) -> None:
        self.service = service
        self.queue = queue
        self.node = f"{service}-isolation-{RUN_ID}"
        self.lines: list[str] = []
        self._proc = subprocess.Popen(
            [
                "uv",
                "run",
                "--python",
                "3.13",
                "celery",
                "-A",
                "celery_app.celery_app",
                "worker",
                "--loglevel=INFO",
                "-Q",
                queue,
                "--pool=solo",
                "-n",
                self.node,
                "--without-heartbeat",
                "--without-mingle",
                "--without-gossip",
            ],
            cwd=str(REPO_ROOT / "services" / service),
            env=_service_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=sys.platform != "win32",
        )
        self._thread = threading.Thread(target=self._drain, daemon=True)
        self._thread.start()

    def _drain(self) -> None:
        stdout = self._proc.stdout
        if stdout is None:
            return
        for line in stdout:
            self.lines.append(line)

    def output(self) -> str:
        return "".join(self.lines)

    def wait_ready(self, timeout: float = WORKER_READY_TIMEOUT_SECONDS) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                _fail(
                    f"{self.service} worker exited {self._proc.returncode} before ready:\n"
                    f"{self.output()}"
                )
            if "ready." in self.output().lower():
                return
            time.sleep(0.2)
        _fail(f"{self.service} worker not ready after {timeout}s:\n{self.output()}")

    def stop(self) -> None:
        if self._proc.poll() is None:
            _kill_tree(self._proc.pid)
            deadline = time.monotonic() + TEARDOWN_WAIT_SECONDS
            while self._proc.poll() is None and time.monotonic() < deadline:
                time.sleep(0.1)
        _assert_no_process_with(f"{self.service}-isolation")


def test_broker_routing() -> None:
    _flushdb()
    reporting_id = enqueue_reporting()
    reporting_depth = queue_depth("reporting")
    if reporting_depth < 1:
        _fail(
            f"reporting task {reporting_id} did not land on queue 'reporting' "
            f"(reporting depth={reporting_depth}, celery depth={queue_depth('celery')})"
        )
    if queue_depth("rfp") != 0:
        _fail("reporting task was visible on queue 'rfp'")
    if queue_depth("celery") != 0:
        _fail("reporting task landed on default queue 'celery'")

    rfp_id = enqueue_rfp()
    rfp_depth = queue_depth("rfp")
    if rfp_depth < 1:
        _fail(
            f"rfp task {rfp_id} did not land on queue 'rfp' "
            f"(rfp depth={rfp_depth}, celery depth={queue_depth('celery')})"
        )
    if queue_depth("celery") != 0:
        _fail("rfp task landed on default queue 'celery'")
    after = queue_depth("reporting")
    if after != reporting_depth:
        _fail(
            f"enqueuing rfp changed reporting depth {reporting_depth} -> {after} "
            f"(rfp task {rfp_id})"
        )
    print("ok broker routing")


def test_wrong_worker_ignores(
    worker_service: str,
    worker_queue: str,
    enqueue: Callable[[], str],
    foreign_task_name: str,
    expected_queue: str,
) -> None:
    _flushdb()
    worker = _Worker(worker_service, worker_queue)
    try:
        worker.wait_ready()
        task_id = enqueue()
        deadline = time.monotonic() + WRONG_WORKER_WAIT_SECONDS
        while time.monotonic() < deadline:
            time.sleep(0.5)
        remaining = queue_depth(expected_queue)
        if remaining < 1:
            _fail(
                f"{foreign_task_name} {task_id} left queue {expected_queue!r} "
                f"while only {worker_service} (-Q {worker_queue}) was running "
                f"({expected_queue} depth={remaining}, celery depth={queue_depth('celery')})\n"
                f"{worker.output()}"
            )
        blob = worker.output()
        blob_l = blob.lower()
        if foreign_task_name in blob:
            _fail(
                f"{worker_service} worker log mentioned {foreign_task_name}:\n{blob}"
            )
        if "received task" in blob_l:
            _fail(f"{worker_service} worker logged Received task:\n{blob}")
        if "unregistered" in blob_l:
            _fail(f"{worker_service} worker logged an unregistered task:\n{blob}")
        print(
            f"ok {worker_service} -Q {worker_queue} ignored {foreign_task_name} {task_id}"
        )
    finally:
        worker.stop()


def main() -> int:
    try:
        _require_flush_opt_in()
        _redis_url()
        _sweep_leftover_isolation_workers()
        test_broker_routing()
        test_wrong_worker_ignores(
            worker_service="rfp",
            worker_queue="rfp",
            enqueue=enqueue_reporting,
            foreign_task_name=REPORTING_TASK,
            expected_queue="reporting",
        )
        test_wrong_worker_ignores(
            worker_service="reporting",
            worker_queue="reporting",
            enqueue=enqueue_rfp,
            foreign_task_name=RFP_TASK,
            expected_queue="rfp",
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
