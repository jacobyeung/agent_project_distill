#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
python3 -B - <<'PYCODE'
import hashlib,json,os
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_c5f3847d')
assert b.is_dir() and not b.is_symlink() and b.stat().st_mode & 0o777 == 0o700
texts={'r1.txt': '# REVIEW_VERDICT_R1P: GO AFTER FIXES\n1. HIGH, blocks proof. LOCAL FIXTURE.', 'r2.txt': '# REVIEW_VERDICT_R1P2: GO AFTER FIXES\n1. MEDIUM, fix needed. LOCAL FIXTURE.', 'r3.txt': '# REVIEW_VERDICT_R1P3: GO — LOCAL TEST ONLY\n888027436a99cfec360959c46f4271222e4c029f5d36eb9870fea4f669231029'}
record={'config_sha256': 'd8b03fd14db01af4def4a0cfd9a49d16ec492d9a3c6b0c56977f7f22b79f705a', 'source_revision': 'sha256:5e1514ef9d91bee8a1623e0e9db4844d5916a0836da953302413a212b23fe8b8', 'operator_archive_sha256': '888027436a99cfec360959c46f4271222e4c029f5d36eb9870fea4f669231029', 'reviews': {'review_r1p': {'verdict': 'GO AFTER FIXES', 'sha256': '74c27b673d4182f18a3cd5ced5fdea6e5529e0f301fce47c50c039dde6e4970e', 'file': 'r1.txt', 'role': 'antecedent'}, 'review_r1p2': {'verdict': 'GO AFTER FIXES', 'sha256': 'c70fbb2a67175816c569901b9103f7f0c045688f5fbcac97296c66603f983205', 'file': 'r2.txt', 'role': 'antecedent'}, 'review_r1p3': {'verdict': 'GO', 'sha256': 'aa8408b2aee9bbe29e89c71798cf36f1b4a3e1348b6bf4a8805ab193123a076d', 'file': 'r3.txt', 'role': 'final'}}, 'reviewers': ['review_r1p', 'review_r1p2', 'review_r1p3'], 'final_reviewer': 'review_r1p3', 'final_verdict': 'GO', 'fix_rounds': [4, 5, 6, 7], 'nonblocking_fixes': [], 'accepted_for_cpu_proof': True, 'production_go_granted': False}
for n in list(texts)+['r1.json']:
 assert not (b/n).exists() and not (b/n).is_symlink(), 'REFUSED: review destination exists'
assert json.loads((b/'BINDING.json').read_text())['config_identity']==record['config_sha256']
assert hashlib.sha256((b/'p.tar').read_bytes()).hexdigest()==record['operator_archive_sha256']
for n,t in texts.items():
 with (b/n).open('x') as f:f.write(t)
 (b/n).chmod(0o600)
with (b/'r1.json').open('x') as f:json.dump(record,f,sort_keys=True);f.write('\n')
(b/'r1.json').chmod(0o600)
for note in record['nonblocking_fixes']:print('OPERATOR LOW NON-BLOCKING: '+note)
print('PASS installed three-review chain; final review_r1p3 accepted for exact packet; no production GO granted')
PYCODE
