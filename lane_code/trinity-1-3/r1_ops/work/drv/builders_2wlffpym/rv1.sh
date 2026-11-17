#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
python3 -B - <<'PYCODE'
import json,os
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_1130b378')
assert b.is_dir() and not b.is_symlink() and b.stat().st_mode & 0o777 == 0o700
texts={'r1.txt': '# GO — LOCAL TEST ONLY; NOT AN ACTUAL REVIEW\n782f303d81e300b1b24094863d6ce7d984690529f0e414474c3e693df87e19da\nb7d19ec090bcab112ed0ce72758e4491e02aff14d4645ac3945bb56ebd7d379e\n42bbcbb218c982b4e33cc92c7be97f01359ae2e47cd20e387c0008edefc6b1cb\n', 'r2.txt': '# GO — LOCAL TEST ONLY; NOT AN ACTUAL REVIEW\n782f303d81e300b1b24094863d6ce7d984690529f0e414474c3e693df87e19da\nb7d19ec090bcab112ed0ce72758e4491e02aff14d4645ac3945bb56ebd7d379e\n42bbcbb218c982b4e33cc92c7be97f01359ae2e47cd20e387c0008edefc6b1cb\n'}
record={'config_sha256': '782f303d81e300b1b24094863d6ce7d984690529f0e414474c3e693df87e19da', 'source_revision': 'sha256:b7d19ec090bcab112ed0ce72758e4491e02aff14d4645ac3945bb56ebd7d379e', 'operator_archive_sha256': '42bbcbb218c982b4e33cc92c7be97f01359ae2e47cd20e387c0008edefc6b1cb', 'reviews': {'review_r1p': {'verdict': 'GO', 'sha256': '87b8fc4e978ad66dfe2753e2822a141518f04094cfc6acce2f7700188798a2a4', 'file': 'r1.txt'}, 'review_r1p2': {'verdict': 'GO', 'sha256': '87b8fc4e978ad66dfe2753e2822a141518f04094cfc6acce2f7700188798a2a4', 'file': 'r2.txt'}}}
for n,t in texts.items():
 with (b/n).open('x') as f:f.write(t)
with (b/'r1.json').open('x') as f:json.dump(record,f,sort_keys=True);f.write('\n')
print('PASS installed two exact-packet GO verdicts; no production GO granted')
PYCODE
