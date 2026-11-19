#!/usr/bin/env python3
"""Package a completed audit and an explicit agent review receipt."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


checks = json.loads((OUT / 'CHECKS.json').read_text())
review = json.loads((OUT / 'REVIEW.json').read_text())
assert review['rows_read'] == 60
assert review['sample_qids'] == [r['qid'] for r in checks['sample']]
for name in ['READ60.md', 'READ30.md']:
    assert review['input_sha256'][str(OUT / name)] == sha(OUT / name)
assert (OUT / 'READ60.md').read_text().count('### Sample ') == 60
assert (OUT / 'READ30.md').read_text().count('```json\n') == 30
assert (OUT / 'REMOVE.json').read_bytes() == b''
checks['manual_review'] = review['findings']
checks['input_sha256'][str(OUT / 'REVIEW.json')] = sha(OUT / 'REVIEW.json')
checks['input_sha256'][str(Path(__file__).resolve())] = sha(Path(__file__).resolve())
checks['checks']['read60_complete_and_read30_full_source_rows'] = True
checks['checks']['empty_n_format_removal_list'] = True
checks['reproduce'] = ['python -B audit_away.py', 'python -B finalize_audit.py']
(OUT / 'CHECKS.json').write_text(json.dumps(checks, indent=2) + '\n')
report = '''# sb_rowD: audit complete; no rebuild required

All 60 sampled traces already state the toward relation, apply a half turn on a separate line, and derive the away answer. The full population contains this form in 8,511/8,511 rows (100%).

| Trace form | Seeded sample | Full population |
|---|---:|---:|
| Separate half-turn step | 60 | 8,511 |
| Half turn merged or out of order | 0 | 0 |
| Keeps the toward heading | 0 | 0 |
| No explicit half turn | 0 | 0 |

| Family | Sample | Full population |
|---|---:|---:|
| Easy | 27 | 3,664 |
| Medium | 25 | 2,665 |
| Hard | 8 | 2,182 |

`python -B audit_away.py` produces every count above. It checks the family index and family qid lists, selects questions containing “facing in the opposite direction of,” and asserts the exact family totals. It samples without replacement from store-index order with `random.Random(20261118).sample(population, 60)`.

The store has 204,413 rows. Its computed SHA256 is `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`, matching its receipt. All 8,511 selected qids are unique; each sampled source appears once. These checks run in the same command.

The classifier requires a toward-relation line, the immediately following half-turn line, the immediately following derived-result line, and a final answer matching the row answer. The half-turn line explicitly swaps ahead/behind and left/right. “Own step” means a separate trace line; it does not require a numbered Step label.

READ60.md prints ten examples of the only observed form, followed by the remaining fifty complete questions and traces. No examples exist for the zero-count forms. READ30.md also prints every source field for the first thirty samples.

The agent read all sixty target traces. All stated rotations and option letters are internally consistent. Sample 21 retains “is the shoes” in the source question; its trace is clear. This audit does not independently verify geometry or localization.

The local source notes are `rows_r1/STATUS.md`, `out/ADMISSION_PACKET_V7.md`, and `out/ROWS_READ_V7.md`. STATUS.md identifies the external ROWS_V7 record; the audit relies on the local notes and verified store.

The newer w19 sealed tree is available at `tree_rebuild10_w/w19/work/build19/proofs/final/frozen/work/tree_r1`; its seal log records tree SHA256 `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`. No tree validator was invoked because the task takes the audit-only branch.

No replacement rows, toward twins, or new wordings are generated. REMOVE.json is an empty JSONL stream: zero removals, matching N's newline-delimited record format. A nonempty N record has exactly `pool`, `question_type`, `reason`, `row_key`, and `scene`. Input hashes live in CHECKS.json; the empty stream has no records in which to embed metadata.

Build-only checks are not applicable: pack/validate on new rows and build sources, candidate-id recomputation, edited-field diffs, independent GT recomputation, room admission, and benchmark wording distance. No wording threshold was applied and no wording was removed. Existing store admission is not recertified.

`python -B finalize_audit.py` verifies the review receipt, sixty printed samples, thirty full source records and the empty removal stream. It writes CHECKS.json, this report, and sb_rowD.tar. The archive includes code and audit evidence, not training-row outputs. SHA256SUMS records each file hash and the archive hash; verify with `sha256sum -c out/SHA256SUMS` from the workspace.

No training, GPU, network, SSH, Git, external writes or deletions were used. No prose-history exceptions were retained.
'''
assert len(report.splitlines()) <= 80
(OUT / 'REPORT.md').write_text(report)
(ROOT / 'STATUS.md').write_text(
    'The audit is complete. All 60 sampled traces and all 8,511 census rows have a separate '
    'half-turn step. The agent read the full sample and found consistent stated rotations '
    'and option letters. The package contains READ60.md, thirty full source rows, checks, '
    'review evidence, code and an empty N-format removal stream. No replacement rows or '
    'twins are generated. The final report is out/REPORT.md.\n')
files = ['audit_away.py', 'finalize_audit.py', 'STATUS.md', 'out/REPORT.md',
         'out/CHECKS.json', 'out/REVIEW.json', 'out/READ60.md', 'out/READ30.md',
         'out/REMOVE.json']
archive = OUT / 'sb_rowD.tar'
with tarfile.open(archive, 'w') as tar:
    for name in files:
        info = tar.gettarinfo(str(ROOT / name), arcname=name)
        info.mtime = 0
        info.uid = info.gid = 0
        info.uname = info.gname = ''
        with (ROOT / name).open('rb') as source:
            tar.addfile(info, source)
with tarfile.open(archive) as tar:
    assert tar.getnames() == files
    for member in tar:
        assert hashlib.sha256(tar.extractfile(member).read()).hexdigest() == sha(ROOT / member.name)
(OUT / 'SHA256SUMS').write_text(''.join(
    f'{sha(ROOT / name)}  {name}\n' for name in files + ['out/sb_rowD.tar']))
print(json.dumps({'archive': str(archive), 'sha256': sha(archive),
                  'report_lines': len(report.splitlines()), 'status': 'PASS_AUDIT_ONLY'}))
