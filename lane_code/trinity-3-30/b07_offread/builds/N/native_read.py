#!/usr/bin/env python3
"""Prepare and inspect a native read; never submit automatically."""
from pathlib import Path
if (Path(__file__).resolve().parent/'xnames.py').exists():
    import xnames,os
    xnames.install(Path(__file__).resolve().parent)
    os.environ['A0_ROOTS']='r.json'
from offnative.cli import main
if __name__ == '__main__':
    main()
