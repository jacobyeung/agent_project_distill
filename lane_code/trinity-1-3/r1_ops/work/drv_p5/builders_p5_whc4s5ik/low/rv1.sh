#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
python3 -B - <<'PYCODE'
import hashlib,json,os
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_69d2930d')
assert b.is_dir() and not b.is_symlink() and b.stat().st_mode & 0o777 == 0o700
texts={'r1.txt': '# REVIEW_VERDICT_R1P: GO AFTER FIXES\n1. HIGH, blocks proof. LOCAL FIXTURE.', 'r2.txt': '# REVIEW_VERDICT_R1P2: GO AFTER FIXES\n1. MEDIUM, fix needed. LOCAL FIXTURE.', 'r3.txt': '# REVIEW_VERDICT_R1P3: GO — LOCAL TEST ONLY', 'r4.txt': '# REVIEW_VERDICT_R1P4: GO — LOCAL ANTECEDENT', 'r5.txt': '# REVIEW_VERDICT_R1P5: GO — LOCAL ANTECEDENT', 'r6.txt': '# Packet A: GO — LOCAL ANTECEDENT', 'r7.txt': '# Packet A: GO AFTER FIXES\nfac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f\n1. LOW, non-blocking: Add an optional explanatory note.\n'}
record={'config_sha256': 'fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f', 'source_revision': 'sha256:b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b', 'operator_archive_sha256': 'a5dc8f306b6867c24fc80aa1215697cb178337252ec912f61ff575b8ec1e9169', 'packet': 'A', 'reviews': {'review_r1p': {'verdict': 'GO AFTER FIXES', 'sha256': '74c27b673d4182f18a3cd5ced5fdea6e5529e0f301fce47c50c039dde6e4970e', 'file': 'r1.txt', 'role': 'antecedent'}, 'review_r1p2': {'verdict': 'GO AFTER FIXES', 'sha256': 'c70fbb2a67175816c569901b9103f7f0c045688f5fbcac97296c66603f983205', 'file': 'r2.txt', 'role': 'antecedent'}, 'review_r1p3': {'verdict': 'GO', 'sha256': '5152e741aea9f44de1aabd2489911aee8043a2630bfbcfdc9554df1139940081', 'file': 'r3.txt', 'role': 'antecedent'}, 'review_r1p4': {'verdict': 'GO', 'sha256': 'ba1759e72b323f45fbbefdcb31b40c07d0a08297f60097fa25b42457593813e1', 'file': 'r4.txt', 'role': 'antecedent'}, 'review_r1p5': {'verdict': 'GO', 'sha256': 'e99d24d7241585fdc5a0d7dba31ad908a99600d83f315e089ece2e69848c842c', 'file': 'r5.txt', 'role': 'antecedent'}, 'review_r1p6': {'verdict': 'GO', 'sha256': '948c8ecf1b610aa11445f4cb01cee588e38bc6932bd649f843db3f983e225628', 'file': 'r6.txt', 'role': 'antecedent'}, 'review_r1p7': {'verdict': 'GO AFTER FIXES', 'sha256': 'db81602f203bd8b9550de1a8b2527ca9c53c51f35bd7238bd20c715479d829c9', 'file': 'r7.txt', 'role': 'final'}}, 'reviewers': ['review_r1p', 'review_r1p2', 'review_r1p3', 'review_r1p4', 'review_r1p5', 'review_r1p6', 'review_r1p7'], 'final_reviewer': 'review_r1p7', 'final_verdict': 'GO AFTER FIXES', 'fix_rounds': [4, 5, 6, 7, 8, 9, 10, 11], 'nonblocking_fixes': ['1. LOW, non-blocking: Add an optional explanatory note.'], 'accepted_for_cpu_proof': True, 'production_go_granted': False}
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
print('PASS installed seven-review chain; final review_r1p7 accepted for packet A; no production GO granted')
PYCODE
