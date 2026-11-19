"""Neutral staged array entry. No scheduler commands execute in this module."""
from pathlib import Path
import sys


def main():
    source=Path(__file__).resolve().parent.parent
    sys.path[:0]=[str(source/'u0'),str(source),str(source/'tree'),str(source/'b')]
    from a9 import PublicLog,install_wire_decoder
    install_wire_decoder()
    sys.stdout=PublicLog(sys.stdout);sys.stderr=PublicLog(sys.stderr)
    try:
        from a8 import activate
        activate(enabled=True)
        from h1eval.h10.array_worker import main as worker
        return worker()
    except Exception as error:
        print(type(error).__name__)
        return 2


if __name__=='__main__':raise SystemExit(main())
