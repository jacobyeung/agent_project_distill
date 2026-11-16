"""Bounded two-minute polling of the one named incoming local archive."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent
PATH = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/partb/meta/e10fbb95.tar')
EXPECTED = 67143680
DIGEST = 'e10fbb95487f3bafc379f99ac42668f94ac4c479129d8631d63750112cab3266'
DEADLINE = datetime(2026, 11, 16, 6, 11, 32, tzinfo=timezone.utc).timestamp()
rows = []
while True:
    size = PATH.stat().st_size if PATH.exists() else None
    row = dict(utc=datetime.now(timezone.utc).isoformat(), bytes=size)
    rows.append(row)
    if size == EXPECTED:
        with PATH.open('rb') as stream:
            row['sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        row['verified'] = row['sha256'] == DIGEST
    done = row.get('verified', False) or time.time() >= DEADLINE or 'sha256' in row
    (ROOT / 'evidence/METADATA_POLL.json').write_text(json.dumps(dict(
        expected_bytes=EXPECTED, expected_sha256=DIGEST, observations=rows,
        done=done, verified=row.get('verified', False)), indent=2) + '\n')
    if done:
        print(json.dumps(row))
        break
    time.sleep(min(120, max(0, DEADLINE - time.time())))
