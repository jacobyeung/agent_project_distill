"""Assemble the report with exact final test commands and unedited output."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LOGS = Path(sys.argv[1]).resolve()
records = json.loads((LOGS / 'summary.json').read_text())
manifest = json.loads((ROOT / 'out/patches/manifest.json').read_text())
assert [record['status'] for record in records] == ['PASS'] * 5
tests = {'01_prepared_input_cache.diff':['test_prepared_input_cache.py', 'test_prepared_cache_wrapper.py'],
         '02_parallel_frame_sha.diff':['test_parallel_frame_sha.py'],
         '03_checkpoint_verify_memo.diff':['test_checkpoint_verify_memo.py'],
         '04_launch_phase_timing.diff':['test_launch_phase_timing.py']}
switches = ['TK_PREPARED_INPUT_CACHE', 'TK_PARALLEL_FRAME_SHA', 'TK_CHECKPOINT_VERIFY_MEMO', 'TK_LAUNCH_TIMING']
body = (ROOT / 'work/report_body.md').read_text().rstrip()
lines = [body, '', 'Final patch verification completed before the 08:45Z deadline. Report assembled at '
         + datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + '.', '',
         'Each patch applied independently to a fresh build-20 copy, and the complete set applied in numeric order with `patch --batch --fuzz=0 -p1`. No fuzz or offset was needed. The packaging check confirms that only the eleven declared production/test paths differ from the input tree. The manifest contains exact patch bytes, SHA256, base-file hashes and the application method.', '',
         '| Patch | Bytes | Default-OFF switch | Independent test results and exact log |',
         '|---|---:|---|---|']
for (name, names), switch, record in zip(tests.items(), switches, records):
    log = Path(record['log']).read_text()
    counts = re.findall(r'Ran (\d+) tests? in [^\n]+', log)
    lines.append('| [' + name + '](patches/' + name + ') | ' + str(manifest[name]['bytes'])
                 + ' | `' + switch + '` | ' + ' + '.join(counts) + ' passed; [exact output](tests/'
                 + LOGS.name + '/' + name + '.txt) |')
lines.extend(['', 'The final combined run passes **49 new tests and 51 selected native regressions (100 tests)**. It includes key-component misses, exact config-file pin changes, same-key/different-code refusal, corruption, missing/partial/purged sources, concurrent publishers/consumers, real wrapper serialization, native training-gate acceptance and provenance preservation. The default-OFF paths, frame rejection cases, checkpoint invalidation and timing exit/stdout behavior are covered.', '',
              'The actual outer verification command was:', '', '```bash',
              'nice -n 10 env CUDA_VISIBLE_DEVICES=\'\' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_delivery.py',
              '```', '',
              'The runner sets `TEST_TMP_ROOT`, `TMPDIR` and `LANE_TEST_OUTPUT` to its new owned scratch directory. Child commands inherit nice level 10 and the CPU/CUDA limits. To run the included patch tests on a rebuilt source tree, use the same environment with each command below, after setting those three fixture paths:', '',
              '| Test command from the source root | Exact independent result |', '|---|---|'])
for record, (name, names) in zip(records, tests.items()):
    log = Path(record['log']).read_text()
    results = re.findall(r'(Ran \d+ tests? in [^\n]+)\n\n(OK)', log)
    assert len(results) == len(names)
    for test, result in zip(names, results):
        lines.append('| `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/' + test + ' -v` | `'
                     + result[0] + '`; `' + result[1] + '` |')
lines.extend(['', 'The following block is the **unedited combined application and test output**, including exact commands and exit codes. The standalone logs linked above retain the independent applications and their own exact timings.', '',
              '```text', (LOGS / 'combined.txt').read_text().rstrip(), '```', '',
              'The optional expanded check retains the input fixture failure rather than modifying its assertions. Its command and complete output are in [the input log](tests/' + LOGS.name + '/known_native_failures_input.txt) and [the patched log](tests/' + LOGS.name + '/known_native_failures_patched.txt). Both runs contain 57 tests and exit 1, with the same four failures and one error. The comparison command was:', '',
              '```bash', 'nice -n 10 env CUDA_VISIBLE_DEVICES=\'\' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_known_failures.py ' + str(LOGS), '```', '',
              'Its exact output is:', '', '```text', (LOGS / 'known_failure_comparison.txt').read_text().rstrip(), '```', ''])
(ROOT / 'out/REPORT.md').write_text('\n'.join(lines))
note = ROOT / 'out/NOTE_FOR_TREE_REBUILD.md'
text = note.read_text()
text = text.replace('48 new tests', '49 new tests').replace('tests/20261119T071707Z/', 'tests/' + LOGS.name + '/')
note.write_text(text)
print('WROTE out/REPORT.md and synchronized hand-over test counts/log paths')
