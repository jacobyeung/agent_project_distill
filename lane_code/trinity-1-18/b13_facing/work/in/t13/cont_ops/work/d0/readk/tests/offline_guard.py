"""Deny real process and network operations before any test imports kit code.

The audit hook cannot be uninstalled by a mock or bypassed with an absolute
binary path, shell=True, or a replacement PATH. Mocks never reach these events.
"""
import sys


class OfflineViolation(RuntimeError):
    pass


def deny_external(event, args):
    if (event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn',
                  'os.fork', 'os.forkpty'} or event.startswith('socket.')):
        raise OfflineViolation('Offline tests forbid process/network event: '+event)


sys.addaudithook(deny_external)
