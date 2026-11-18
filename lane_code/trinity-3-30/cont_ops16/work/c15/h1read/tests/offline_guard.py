"""Deny process and network operations except exact local isolation fixtures.

The audit hook cannot be uninstalled by a mock or bypassed with an absolute
binary path, shell=True, or a replacement PATH. Mocks never reach these events.
The isolation helper admits only its validated wrapper command; each child
installs this guard before executing the tested module.
"""
import sys
from contextlib import contextmanager

_local_command = None


@contextmanager
def local_fixture_command(command):
    """Allow one exact command validated by isolated_fixture; no shell commands."""
    global _local_command
    previous = _local_command
    _local_command = tuple(command)
    try:
        yield
    finally:
        _local_command = previous


class OfflineViolation(RuntimeError):
    pass


def deny_external(event, args):
    if event == 'subprocess.Popen' and _local_command is not None:
        if args[0] == _local_command[0] and tuple(args[1]) == _local_command:
            return
    if (event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn',
                  'os.fork', 'os.forkpty'} or event.startswith('socket.')):
        raise OfflineViolation('Offline tests forbid process/network event: '+event)


sys.addaudithook(deny_external)
