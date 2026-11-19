"""Compare two supplied cold stores, without changing or normalizing bytes."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from student_pilot.preparation_store import Store, compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", required=True)
    parser.add_argument("--left-root", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--right-root", required=True)
    parser.add_argument("--key", required=True)
    args = parser.parse_args()
    result = compare(Store(args.left), args.left_root, Store(args.right), args.right_root, key=args.key)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
