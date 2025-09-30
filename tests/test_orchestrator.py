from __future__ import annotations

from pathlib import Path

from helpers import orchestrator


def test_build_api_command_includes_expected_flags():
    command = orchestrator.build_api_command("127.0.0.1", 9001, reload=True)
    assert command[:4] == [orchestrator.sys.executable, "-m", "uvicorn", "api:app"]
    assert "--host" in command
    assert "--port" in command
    assert command[-1] == "--reload" or command[-1] == str(9001)
    assert "--reload" in command


def test_build_dashboard_command_uses_streamlit():
    cmd = orchestrator.build_dashboard_command("0.0.0.0", 8502, Path("app.py"))
    assert cmd[:4] == [orchestrator.sys.executable, "-m", "streamlit", "run"]
    assert "--server.address" in cmd
    assert "--server.port" in cmd


def test_run_stack_launches_processes_and_cleans(monkeypatch):
    class FakeProcess:
        def __init__(self, target=None, kwargs=None, daemon=None):
            self.target = target
            self.kwargs = kwargs or {}
            self.daemon = daemon
            self.exitcode = None
            self.started = False
            self.terminated = False

        def start(self):
            self.started = True

        def is_alive(self):
            return not self.terminated

        def terminate(self):
            self.terminated = True
            self.exitcode = -15

        def join(self, timeout=None):
            return None

    processes: list[FakeProcess] = []

    def fake_process_factory(*args, **kwargs):
        proc = FakeProcess(*args, **kwargs)
        processes.append(proc)
        return proc

    class FakePopen:
        instances: list["FakePopen"] = []

        def __init__(self, cmd, stdout=None, stderr=None):
            self.cmd = cmd
            self.stdout = stdout
            self.stderr = stderr
            self._poll = None
            self.terminated = False
            FakePopen.instances.append(self)

        def poll(self):
            return self._poll

        def terminate(self):
            self.terminated = True
            self._poll = -15

        def wait(self, timeout=None):
            return self._poll or 0

    monkeypatch.setattr(orchestrator, "Process", fake_process_factory)
    monkeypatch.setattr(orchestrator.subprocess, "Popen", FakePopen)

    orchestrator.run_stack(
        interval=5,
        folder_ids=["demo"],
        sync_on_start=False,
        api_host="127.0.0.1",
        api_port=9000,
        dashboard_host="127.0.0.1",
        dashboard_port=8600,
        app_path=Path("custom.py"),
        run_duration=0.0,
        poll_interval=0.0,
        sleep_fn=lambda _: None,
    )

    assert processes, "Watcher process should be created"
    watcher_proc = processes[0]
    assert watcher_proc.started, "Watcher should be started"
    assert watcher_proc.kwargs["interval"] == 5
    assert watcher_proc.kwargs["folder_ids"] == ("demo",)
    assert watcher_proc.kwargs["sync_on_start"] is False

    assert len(FakePopen.instances) == 2, "API and dashboard subprocesses should be launched"
    api_cmd, dashboard_cmd = FakePopen.instances[0].cmd, FakePopen.instances[1].cmd
    assert "uvicorn" in " ".join(api_cmd)
    assert "streamlit" in " ".join(dashboard_cmd)

    assert all(proc.terminated for proc in FakePopen.instances), "Subprocesses should be terminated"
    assert watcher_proc.terminated, "Watcher process should be terminated"

