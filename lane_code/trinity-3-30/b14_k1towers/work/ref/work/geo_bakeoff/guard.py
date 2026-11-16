import ctypes
import os
import selectors
import struct
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .io import ROOT


class ProgressGuard:
    def __init__(self, path, events, label, seconds=600):
        self.path, self.events, self.label, self.seconds = Path(path), Path(events), label, seconds
        libc = ctypes.CDLL(None, use_errno=True)
        self.libc = libc
        self.fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self.fd < 0:
            raise OSError(ctypes.get_errno(), "inotify is required for the stall guard")
        self.watches = set()
        self.add(self.path.parent.parent)
        self.add(self.path.parent)

    def add(self, path):
        if path.is_dir() and path not in self.watches:
            if self.libc.inotify_add_watch(self.fd, os.fsencode(path), 0x100 | 0x80 | 0x8) < 0:
                raise OSError(ctypes.get_errno(), "Could not watch progress directory")
            self.watches.add(path)

    def wait(self, process):
        selector = selectors.DefaultSelector()
        exit_read, exit_write = os.pipe()
        def wait_for_exit():
            process.wait()
            try:
                os.write(exit_write, b"x")
            except BrokenPipeError:
                pass
            finally:
                os.close(exit_write)
        threading.Thread(target=wait_for_exit, daemon=True).start()
        start, alerted, alerts = time.time(), False, 0
        try:
            selector.register(exit_read, selectors.EVENT_READ, "exit")
            selector.register(self.fd, selectors.EVENT_READ, "progress")
            while True:
                latest = max(start, self.path.stat().st_mtime) if self.path.exists() else start
                timeout = None if alerted else max(0, latest + self.seconds - time.time())
                ready = selector.select(timeout)
                if not ready:
                    self.events.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
                    alerts += 1
                    path = self.events / f"{stamp}_BLOCKER_stall_{self.label}_{process.pid}_{alerts}.md"
                    with path.open("x") as f:
                        f.write(f"{self.label} has made no recorded progress for {self.seconds} seconds.\n"
                                f"Progress: {self.path}\nPID: {process.pid}. The guard alerts; it does not kill or retry the job.\n")
                    alerted = True
                    continue
                for key, _ in ready:
                    if key.data == "exit":
                        return process.wait()
                    data = os.read(self.fd, 65536)
                    offset = 0
                    while offset < len(data):
                        _, _, _, length = struct.unpack_from("iIII", data, offset)
                        name = data[offset+16:offset+16+length].rstrip(b"\0").decode()
                        offset += 16 + length
                        if name == self.path.parent.name:
                            self.add(self.path.parent)
                        if name == self.path.name:
                            alerted = False
        finally:
            selector.close()
            os.close(exit_read)
            os.close(self.fd)


def guarded(command, progress, events, label, log, env, vnice=None, seconds=600, resume=False, cwd=None):
    parent = Path(progress).parent.parent
    parent.mkdir(parents=True, exist_ok=True)
    guard = ProgressGuard(progress, events, label, seconds)
    with Path(log).open("ab" if resume else "xb") as output:
        if vnice is not None:
            import shlex
            wrapper = parent / f"{label}_{time.time_ns()}_worker.sh"
            with wrapper.open("x") as f:
                f.write("#!/usr/bin/env bash\nset -euo pipefail\nexec " + shlex.join(command) + "\n")
            wrapper.chmod(0o700)
            command = [str(vnice), shlex.quote(str(wrapper))]
        process = subprocess.Popen(command, env={**env, "PYTHONSAFEPATH": "1"}, cwd=cwd or ROOT / "work",
                                   stdout=output, stderr=subprocess.STDOUT)
        code = guard.wait(process)
    if code:
        raise subprocess.CalledProcessError(code, command)
