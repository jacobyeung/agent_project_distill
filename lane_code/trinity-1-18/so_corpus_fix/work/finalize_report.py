"""Package measured evidence and the static publication-impact decision."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / 'work'
INPUT = pathlib.Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin')
timestamp = subprocess.check_output(['date', '-u'], text=True).strip()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
patch = ROOT / 'out/patches/01_ingest_review2.diff'
for name in ('ingest_read.py', 'tests/test_review2.py'):
    assert (WORK / 'tool' / name).read_bytes() == (WORK / 'patchcheck_final' / name).read_bytes()
unchanged_files = 0
for source in INPUT.rglob('*'):
    if source.is_file() and source.name != 'ingest_read.py':
        assert source.read_bytes() == (WORK / 'tool' / source.relative_to(INPUT)).read_bytes()
        unchanged_files += 1
audit = json.loads((WORK / 'evidence/published_audit.json').read_text())
total_bytes = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
assert total_bytes < 3_000_000_000
published_versions = sorted({json.loads(line)['tool_version'] for line in (WORK / 'evidence/INDEX.jsonl').open()})
env = "CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1"
python = '/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B'
prefix = 'nice -n 10 env ' + env + ' ' + python
time_format = (chr(92) + 'n').join(['MEASURED_MAX_RSS_KIB=%M', 'MEASURED_ELAPSED_SECONDS=%e', 'EXIT_CODE=%x'])

paragraphs = [
    'VERDICT: DONE Three opt-in fixes pass synthetic validation; the static published-read audit indicates no re-ingest.\n',
    'The tool copy is `work/tool/`. Enable the fixes with `ingest --review2-checks`; the switch defaults off. '
    'Only `ingest_read.py` and the new `tests/test_review2.py` are in the patch. '
    'The delivered scope is LEFTOVER item 1. Completion time from `date -u`: ' + timestamp + '.\n',
    'All counts and resource values below are measured locally or read from the named index snapshot; publication-impact conclusions marked “inferred” are static decisions, not measured byte comparisons.\n',
    '| Evidence | Measured or recorded result |\n|---|---|\n'
    '| Requested regressions against input | 3 tests, 3 failures, exit 1 |\n'
    '| Final patch applied to a fresh input copy | 43 tests passed: 23 new and 20 existing; exit 0 |\n'
    '| Existing synthetic suite with checks enabled | 20 tests passed; exit 0 |\n'
    '| Final patch test process | 227928 KiB peak RSS; 1.41 seconds elapsed; unittest body 0.165 seconds |\n'
    '| Default compatibility | 7 fixtures; identical read/orphan bytes; indexes differ only in tool_version |\n'
    '| Existing real-return-dependent leftover test | 1 skipped: real return absent |\n'
    '| Published index snapshot | 18 reads: 10 kit, 5 routed, 2 offread, 1 native |\n'
    '| Native input identity audit | 9 source files match indexed hashes; 636 matching task IDs; 0 conflicting supplied fields |\n'
    '| Workspace before writing this report | %d bytes, measured by summing local file sizes |\n'
    '| Patch | %d bytes; unified diff with a/ and b/ paths |\n' % (total_bytes, patch.stat().st_size),
    'The fixes have these effects:\n\n'
    '1. Kit keeps exact report-ID lookup first. Alias lookup accepts only key-only records and skips actual-ID records, including when a valid key-only alias follows one. Rejected evidence remains in the orphan sidecar.\n'
    '2. Native retains empty arm-array declarations without changing raw metadata. It checks required arms, report array labels, exact request/report key declarations, and each observed arm’s key set. A declared population contradiction returns exit 2 even with `--archive-partial`. Existing completion-count checks remain in force.\n'
    '3. Native compares every supplied task field, including options, scene, video, room, room_key, truth, arbitrary identity fields, and nested values. It also compares the effective ground_truth/answer and units/unit aliases. Missing fields can add evidence; conflicting supplied values refuse the join. This distinction preserves the valid additive room_key evidence in all 636 indexed native tasks. The selected task and emitted payload are not rewritten.\n',
    'The patch is [01_ingest_review2.diff](patches/01_ingest_review2.diff). Its SHA256 is `' + sha(patch) + '`. '
    'The input ingest SHA256 is `' + sha(INPUT / 'ingest_read.py') + '`; the fixed ingest SHA256 is `' + sha(WORK / 'tool/ingest_read.py') + '`. '
    'All %d other input files remain byte-identical in the work copy. The applied patch matches both delivered changed files byte for byte.\n' % unchanged_files,
    'Default compatibility means identical read payloads and orphan payloads. The index’s `tool_version` is the SHA256 of the executing script, so a newly generated index necessarily records the changed source hash. '
    'This provenance difference is explicit; no claim is made that newly generated index JSON is byte-identical to the input tool’s index. '
    'The on-disk published indexes were not modified. Their recorded tool version is `' + ', '.join(published_versions) + '`, which differs from the supplied input script; this audit isolates the delivered fixes rather than claiming a full reproduction of an older publisher.\n',
    'The publication decision uses `/data2/jjyeung/agent_project_data/distill_trace_corpus/INDEX.jsonl`, '
    'snapshotted at `work/evidence/INDEX.jsonl` (14323288 bytes; SHA256 `' + audit['index_sha256'] + '`). '
    'The published schema is snapshotted at `work/evidence/PUBLISHED_SCHEMA.md`; lines 25 and 27–35 define alias handling and index evidence. '
    'The complete machine-readable audit, including each published output SHA256, is `work/evidence/published_audit.json`.\n',
    'Each “unchanged” decision below applies to `reads/<read_id>.jsonl.gz` for the same read ID, source and metadata. '
    'The default-off path is unchanged for every entry. With checks enabled, the basis is: A, unchanged adapter code; '
    'B, no family report sources, so the changed kit lookup cannot affect this read; '
    'C, inferred unchanged from zero published orphans and the absence of the review’s wrong-alias signature; '
    'D, inferred unchanged because native only adds validation, both arm counts and the union count are 636, the request/report declare the same 636 keys, and all hash-verified task identities are compatible. '
    'Item counts and arms in the table are recorded INDEX values.\n',
    '| Published read_id | Format | Items | Arms | Decision | Basis |\n|---|---|---:|---|---|---|',
]
for row in audit['reads_detail']:
    basis = 'C (inferred)' if row['format'] == 'kit' and row['report_sources'] else 'B' if row['format'] == 'kit' else 'D (inferred)' if row['format'] == 'native' else 'A'
    paragraphs.append('| `%s` | %s | %d | %s | unchanged | %s |' %
                      (row['read_id'], row['format'], row['item_count'], ', '.join(row['arms']), basis))
paragraphs.extend([
    '\nNo read is classified “would change,” so no re-ingest commands or new read IDs are required by this decision. No re-ingest or publication ran.\n',
    'The six C decisions are inferences, not proofs: INDEX does not retain the streamed per-item report IDs. '
    'Zero orphans rules out the review’s isolated bad-alias example but cannot exclude a separate generated item whose actual ID is the same devrows-prefixed ID. '
    'The native index likewise omits the actual per-arm key lists; equal per-arm and union counts prove equal arm populations but do not alone prove membership in the declared key set. '
    'The supplied review’s real-output losslessness and score-exactness findings support the decision; they are prior evidence, not tests rerun here. '
    'A source-row audit on trinity-3-30 would be needed to turn these inferences into byte-level certification.\n',
    'What could go wrong and how to notice: without `--review2-checks`, the three defects remain enabled by the required compatibility policy. '
    'With the switch on, legitimate but conflicting task annotations can trigger `Ambiguous native task`; inspect the candidate tasks rather than suppressing the refusal. '
    'A hidden kit namespace collision would appear as an actual-ID report row supplying another item’s scores and would change its normalized scores when the switch is enabled. '
    'A native declaration mismatch produces a native arm/key refusal before emission. If a source audit reveals a changed read, the owner must use a new read ID and preserve the published read.\n',
    'Not done: `tests/test_real_returns.py` was neither imported nor executed because its real returns are absent on this node. '
    'No direct comparison against the published read gzip bytes was performed. No files in the published corpus or input mirror were written. '
    'LEFTOVER items other than item 1 were not performed.\n',
    'The tests use the required CPU environment and `torch.set_num_threads(8)` before test execution. '
    'The relevant installed behavior is documented at `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_torch_docs.py:9819` '
    '(CPU intra-op thread limit; call before eager/JIT/autograd work at line 9822), and in the '
    '[official PyTorch 2.11 documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html). '
    'The production ingest code uses the Python standard library and relies on no tensor or training behavior.\n',
    'The following commands ran from `/scratch/jjyeung/orch_n30/so_corpus_fix`; each step was preceded by `date -u`. '
    'Code blocks contain exact captured process output. The test runner is `work/run_tests.py`; it imports only the named modules and places all fixtures under this workspace. '
    'Input/fixed comparisons are retained because the dispatch explicitly requires failure evidence and compatibility checks.\n',
])

def evidence(description, command, filename, exit_code=None):
    paragraphs.append(description + '\n\n```bash\n' + command + '\n```\n\n```text\n' +
                      (WORK / 'evidence' / filename).read_text().rstrip() + '\n```\n' +
                      ('\nMeasured process exit code: %s.\n' % exit_code if exit_code is not None else ''))

evidence('The requested three regressions against the immutable input (08:49:32 UTC):',
         prefix + ' work/run_tests.py --tool ' + str(INPUT) +
         ' --case Review2Tests.test_kit_alias_rejects_actual_id --case Review2Tests.test_native_requires_exact_arm_populations'
         ' --case Review2Tests.test_native_rejects_full_task_identity_conflict test_review2',
         'regressions_input.log', 1)
evidence('The final patch applied to a fresh copy of the input (08:53:57 UTC):',
         'nice -n 10 patch --batch --forward --no-backup-if-mismatch -p1 -d work/patchcheck_final < out/patches/01_ingest_review2.diff',
         'patch_apply.log', 0)
evidence('The full synthetic suite using the final patch-applied implementation (08:53:57 UTC):',
         "nice -n 10 /usr/bin/time -f '" + time_format + "' env " +
         env + ' ' + python + ' work/run_tests.py --tool ' + str(WORK / 'patchcheck_final') + ' test_review2 test_synthetic',
         'patch_final_tests.log')
evidence('All existing synthetic tests with the checks enabled (08:49:34 UTC):',
         prefix + ' work/run_tests.py --enable-review2 test_synthetic', 'existing_enabled.log', 0)
evidence('Input/fixed default-output compatibility, including all three defect fixtures (08:54:21 UTC):',
         prefix + ' work/check_default_compat.py', 'default_compat_final.log', 0)
evidence('The existing leftover test skips without invoking a real ingest (08:52:49 UTC):',
         prefix + ' work/run_tests.py test_no_leftovers', 'no_leftovers.log', 0)
paragraphs.append('The static audit command was `' + prefix + ' work/audit_published.py` (08:54:23 UTC, exit 0). '
                  'Its complete exact output is `work/evidence/published_audit_final.log`.\n')
(ROOT / 'out/REPORT.md').write_text('\n'.join(paragraphs))
(WORK / 'STATUS.md').write_text(
    'All three tasks are complete as of ' + timestamp + ' (date -u).\n\n'
    'The final patch is out/patches/01_ingest_review2.diff; the report is out/REPORT.md. '
    'The patch applies cleanly and passes 43 synthetic tests. All 20 existing synthetic tests also pass with the checks enabled. '
    'Seven default compatibility fixtures preserve read/orphan bytes; index tool_version records the new source hash.\n\n'
    'The static audit recommends no re-ingest for the 18 published reads. Six kit decisions and the native decision are explicitly inferred; '
    'the report documents the missing per-item evidence and does not claim a real-byte replay. Nine mirrored native task files match indexed hashes, '
    'and all 636 matched tasks have compatible supplied identity fields.\n\n'
    'tests/test_real_returns.py was not run because its real returns are unavailable. '
    'The existing no-leftovers test skipped for the same reason. No publication, re-ingest, SSH, Git, GPU work, or deletion ran.\n')
receipt = dict(completed_utc=timestamp, patch_sha256=sha(patch), patch_bytes=patch.stat().st_size,
               input_sha256=sha(INPUT / 'ingest_read.py'), fixed_sha256=sha(WORK / 'tool/ingest_read.py'),
               unchanged_input_files=unchanged_files, report_sha256=sha(ROOT / 'out/REPORT.md'),
               workspace_bytes=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()))
(ROOT / 'out/RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps(receipt, sort_keys=True))
