"""Gated stream reader for tools/r1aws.py payload polls. Writes its PID, stops itself (SIGSTOP) before opening any part,
then writes every part of MANIFEST (a JSON list of local file paths, in order) to stdout. The IO governor admits it
(SIGCONT) and paces it through the downstream pv.
usage: r1stream.py MANIFEST PIDFILE | pv ... | ssh code-aws bash -s
"""
import json
import os
import signal
import sys


def main():
    parts = json.load(open(sys.argv[1]))
    with open(sys.argv[2] + ".part", "w") as stream:
        stream.write(str(os.getpid()))
    os.rename(sys.argv[2] + ".part", sys.argv[2])
    os.kill(os.getpid(), signal.SIGSTOP)
    out = sys.stdout.buffer
    for path in parts:
        with open(path, "rb") as source:
            for block in iter(lambda: source.read(1 << 16), b""):
                out.write(block)
    out.flush()


if __name__ == "__main__":
    main()
