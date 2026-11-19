import os
from pathlib import Path
import signal
import sys


def forward(parent, script, root):
    pending = [int(parent)]
    while pending:
        pid = pending.pop()
        try:
            pending.extend(int(value) for value in Path(f"/proc/{pid}/task/{pid}/children").read_text().split())
            command = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            encoded = str(script).encode()
            if (encoded in command and command.index(encoded)+1 < len(command)
                    and command[command.index(encoded)+1] == str(root).encode()):
                os.kill(pid, signal.SIGUSR1)
        except (FileNotFoundError, ProcessLookupError):
            pass


if __name__ == "__main__":
    forward(*sys.argv[1:])
