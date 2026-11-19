"""Assemble current guidance and exact fresh-patch regression results."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LOGS = Path(sys.argv[1]).resolve()
records = json.loads((LOGS / 'summary.json').read_text())
assert len(records) == 6 and all(r['status'] == 'PASS' for r in records)
body = (ROOT / 'work/report_body.md').read_text().rstrip()
manifest = json.loads((ROOT / 'out/patches/manifest.json').read_text())

def results(path):
    return re.findall(r'(Ran \d+ tests? in [^\n]+)\n\n(OK[^\n]*)', path.read_text())

lines = [body, '', '## Exact commands and results', '',
         'Final fresh-patch verification: ' + LOGS.name + '. Report assembled at '
         + datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + '.', '',
         'All four patches apply independently with `patch --batch --fuzz=0 -p1`. '
         'The recommended set applies in order 03, 04, 02; the all-four set adds 01 last with its switch OFF. '
         'The all-four application reports only expected line offsets where timing moves later hunks. '
         'No fuzz or failed hunk occurs, and every declared final file must match `work/tree` byte for byte. '
         'The manifest records patch bytes, SHA256, input base pins and the native gate SHA256.', '',
         '| Application | Exact test summaries | Full command/output log |', '|---|---|---|']
for record in records:
    path = Path(record['log'])
    outcome = '; '.join('`' + a + '`; `' + b + '`' for a, b in results(path))
    lines.append('| ' + record['name'] + ' | ' + outcome + ' | [exact output](tests/' + LOGS.name + '/' + path.name + ') |')
lines += ['', 'The all-four run registers **149 tests: 138 pass and 11 skip** '
          '(63 patch tests plus 86 native tests). Six delivery contracts pass separately. '
          'The recommended set registers 109 tests, with the same eleven explicit native skips. '
          'The native gate selects the full `test_s1_launch_kit`, `test_s1_production_imports` and '
          '`test_s1_checkpoint_buffers` modules, in addition to the existing native modules. '
          'It executes world-4 guard/resume tests and the shell syntax checks. '
          'No skipped test is counted as passed.', '',
          'The fresh-patch command was:', '', '```bash',
          "nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 SO_NO_LOCAL_SOCKETS=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_delivery.py",
          '```', '',
          'The runner creates owned scratch directories and sets `TEST_TMP_ROOT`, `TMPDIR` and `LANE_TEST_OUTPUT` '
          'to them. Child tests inherit the CPU limits and nice level. The exact combined test commands were:', '', '```text']
combined = (LOGS / 'combined.txt').read_text()
lines += [line[2:] for line in combined.splitlines()
          if line.startswith('$ ') and ('/tests/test_' in line or 'run_native_regression.py' in line)]
lines += ['```', '', 'The corrected before/after regression evidence is indexed in '
          '[review_round1/INDEX.md](tests/review_round1/INDEX.md). '
          'The two boundary coverage tests and reporting checks supplement the behavior tests; '
          'they do not pretend that the working memo or staging branches were broken.', '',
          'The stale-fixture comparison used:', '', '```bash',
          "nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 SO_NO_LOCAL_SOCKETS=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_known_failures.py " + str(LOGS),
          '```', '', 'Its exact comparison output is:', '', '```text',
          (LOGS / 'known_failure_comparison.txt').read_text().rstrip(), '```', '',
          'Both [input](tests/' + LOGS.name + '/known_native_failures_input.txt) and '
          '[patched](tests/' + LOGS.name + '/known_native_failures_patched.txt) runs register 92 tests and exit 1 with '
          '`FAILED (failures=4, errors=1, skipped=11)`. The five failure identities match. '
          'The supported gate passes on the input tree as well as both delivered patch sets; '
          'the extra six-test admission module is isolated in this comparison.', '',
          'Patch inventory:', '', '| Patch | Bytes | SHA256 |', '|---|---:|---|']
for name, entry in manifest.items():
    lines.append('| [' + name + '](patches/' + name + ') | ' + str(entry['bytes']) + ' | `' + entry['sha256'] + '` |')
lines += ['', 'The artifact audit checks source/base pins, standalone and combined application, syntax, '
          'test counts and skips, before/after production source identity, live guidance, links, scratch capacity '
          'and output checksums. Its exact output is [final_artifact_audit.txt](tests/final_artifact_audit.txt). '
          'The cross-run design and hand-over note are covered by the delivery contracts.', '']
(ROOT / 'out/REPORT.md').write_text('\n'.join(lines))
print('WROTE out/REPORT.md with exact results from ' + LOGS.name)
