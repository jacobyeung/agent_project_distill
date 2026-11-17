#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
python3 -B - <<'PYCODE'
import hashlib,json,os
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_6f8ed106')
assert b.is_dir() and not b.is_symlink() and b.stat().st_mode & 0o777 == 0o700
texts={'r1.txt': '# REVIEW_VERDICT_R1P: GO AFTER FIXES\n1. HIGH, blocks proof. LOCAL FIXTURE.', 'r2.txt': '# REVIEW_VERDICT_R1P2: GO AFTER FIXES\n1. MEDIUM, fix needed. LOCAL FIXTURE.', 'r3.txt': '# REVIEW_VERDICT_R1P3: GO — LOCAL TEST ONLY', 'r4.txt': '# REVIEW_VERDICT_R1P4: GO AFTER FIXES\n2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d\n1. LOW, non-blocking: Add an optional explanatory note.\n'}
record={'config_sha256': '2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d', 'source_revision': 'sha256:b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b', 'operator_archive_sha256': 'def1e1f2b1153328b024209e69fcbb71f2dd556b7376eacb836d40bb66d9845f', 'reviews': {'review_r1p': {'verdict': 'GO AFTER FIXES', 'sha256': '74c27b673d4182f18a3cd5ced5fdea6e5529e0f301fce47c50c039dde6e4970e', 'file': 'r1.txt', 'role': 'antecedent'}, 'review_r1p2': {'verdict': 'GO AFTER FIXES', 'sha256': 'c70fbb2a67175816c569901b9103f7f0c045688f5fbcac97296c66603f983205', 'file': 'r2.txt', 'role': 'antecedent'}, 'review_r1p3': {'verdict': 'GO', 'sha256': '5152e741aea9f44de1aabd2489911aee8043a2630bfbcfdc9554df1139940081', 'file': 'r3.txt', 'role': 'antecedent'}, 'review_r1p4': {'verdict': 'GO AFTER FIXES', 'sha256': '7cdd87ee1c2b1216ce6b89cd39840f942662de565a05534af603b4f83aa3d26a', 'file': 'r4.txt', 'role': 'final'}}, 'reviewers': ['review_r1p', 'review_r1p2', 'review_r1p3', 'review_r1p4'], 'final_reviewer': 'review_r1p4', 'final_verdict': 'GO AFTER FIXES', 'fix_rounds': [4, 5, 6, 7, 8], 'nonblocking_fixes': ['1. LOW, non-blocking: Add an optional explanatory note.'], 'accepted_for_cpu_proof': True, 'production_go_granted': False}
for n in list(texts)+['r1.json']:
 assert not (b/n).exists() and not (b/n).is_symlink(), 'REFUSED: review destination exists'
assert json.loads((b/'BINDING.json').read_text())['config_identity']==record['config_sha256']
assert hashlib.sha256((b/'p.tar').read_bytes()).hexdigest()==record['operator_archive_sha256']
for n,t in texts.items():
 with (b/n).open('x') as f:f.write(t)
 (b/n).chmod(0o600)
with (b/'r1.json').open('x') as f:json.dump(record,f,sort_keys=True);f.write('\n')
(b/'r1.json').chmod(0o600)
for note in record['nonblocking_fixes']:print('OPERATOR LOW FIX: '+note)
print('PASS installed four-review chain; final review_r1p4 accepted for exact packet; no production GO granted')
PYCODE
