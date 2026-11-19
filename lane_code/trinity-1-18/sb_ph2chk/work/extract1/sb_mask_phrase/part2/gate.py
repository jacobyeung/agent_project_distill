"""Read-only bars-first admission. No directories, logs or receipts are created here."""
import hashlib
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1]
BARS_SHA256 = '166be15bcd56f303b9b032bab84712264a687bc073b791251b57b814e515d774'


def fixture_dir(root=HERE):
    path = (root / os.environ.get('PART2_FIXTURE_DIR', 'work/part2_fixture')).resolve()
    if not path.is_relative_to((root / 'work').resolve()):
        raise SystemExit('REFUSED: fixture output must be under this copy/work')
    return path


def check(mode, root=HERE):
    bars = root / 'part2/BARS_PART2.json'
    if not bars.is_file():
        raise SystemExit(f'REFUSED: MISSING {bars}')
    if hashlib.sha256(bars.read_bytes()).hexdigest() != BARS_SHA256:
        raise SystemExit(f'REFUSED: altered bars {bars}')
    # Aggregate consumes capture scores from work; it must never overwrite its output.
    targets = [root / 'out/part2']
    if mode in ('capture', 'step5', 'pass', 'plan'):
        targets.append(root / 'work/part2_caps')
    if mode.startswith('fixture'):
        fixture = fixture_dir(root)
        targets.append(fixture / ('aggregate' if mode == 'fixture-aggregate' else 'caps')
                       if mode != 'fixture' else fixture)
    for folder in targets:
        if not folder.exists():
            continue
        for path in sorted(folder.rglob('*')):
            # Only the suite receipt is allowed in a fresh aggregate destination.
            if path == root / 'out/part2/TESTS_PART2.json':
                continue
            if path.is_file() and (path.suffix in ('.json', '.jsonl', '.gz') or path.name.startswith('PER_ITEM')):
                raise SystemExit(f'REFUSED: existing part 2 scored output {path}')
    for marker in ('STOP.json', 'KILLED', 'KILLED.json'):
        path = root / 'out/pool_part2' / marker
        if path.exists():
            raise SystemExit(f'REFUSED: {path}; stopped or KILLED work is never rerun')


if __name__ == '__main__':
    check(sys.argv[1])
