"""Isolated-interpreter entry; imports only this exact source tree."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from student_pilot.preparation_cpu import main

if __name__ == "__main__":
    main()
