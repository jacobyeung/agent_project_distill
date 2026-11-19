"""Write the review report, explicit owner replay commands, and artifact manifest."""
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'out'
audit = json.loads((ROOT / 'work/evidence/published_round3_audit.json').read_text())
package = json.loads((ROOT / 'work/evidence/package_round3.json').read_text())
now = subprocess.check_output(['date', '-u'], text=True).strip()
workspace_bytes = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
assert workspace_bytes < 3_000_000_000
prefix = ("nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 "
          "OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 "
          "/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B ")
input_root = package['input_root']
logs = [
    ('Round-three regressions against the saved pre-fix tool', 'before.txt', 1,
     prefix + 'work/run_tests.py --tool work/pre_round3 test_review3'),
    ('Round-two regressions against the immutable input', 'input_regressions.txt', 1,
     prefix + 'work/run_tests.py --tool ' + input_root +
     ' --case Review2Tests.test_kit_alias_rejects_actual_id --case Review2Tests.test_native_requires_exact_arm_populations'
     ' --case Review2Tests.test_native_rejects_full_task_identity_conflict test_review2'),
    ('Existing synthetic tests against the immutable input', 'input_existing.txt', 0,
     prefix + 'work/run_tests.py --tool ' + input_root + ' test_synthetic'),
    ('Cumulative patch generation and fresh application', 'package.txt', 0,
     prefix + 'work/package_round3.py'),
    ('All available tests from the patch-applied tree', 'patch_applied.txt', 0,
     "nice -n 10 /usr/bin/time -f 'MEASURED_MAX_RSS_KIB=%M\\nMEASURED_ELAPSED_SECONDS=%e\\nEXIT_CODE=%x' "
     + prefix.removeprefix('nice -n 10 ') +
     'work/run_tests.py --tool work/patchcheck_round3 --tests work/patchcheck_round3/tests'
     ' test_review2 test_review3 test_synthetic test_no_leftovers'),
    ('Existing synthetic tests with checks enabled on the patch-applied tree', 'existing_enabled.txt', 0,
     prefix + 'work/run_tests.py --tool work/patchcheck_round3 --tests work/patchcheck_round3/tests'
     ' --enable-review2 test_synthetic'),
    ('Default compatibility against immutable input, including every changed branch', 'default_compat.txt', 0,
     prefix + 'work/check_default_compat.py'),
    ('Published index and mirrored input audit', 'published_audit.txt', 0,
     prefix + 'work/audit_round3.py'),
]

# These are concrete commands for the owner, never run by this task.
entries = {e['read_id']: e for e in map(json.loads, (ROOT / 'work/evidence/INDEX_round3.jsonl').read_text().splitlines())}
meta_dir = OUT / 'replay_meta'
meta_dir.mkdir(exist_ok=True)
owner = [
    '# Published-read verification on trinity-3-30', '',
    'These commands are prepared, not executed. Install the delivered patch and place this `out/` bundle on '
    'trinity-3-30 first. Run only after the owner schedules the local source reads under the cluster rules. '
    'Every output is a new scratch artifact; the published corpus is read-only.', '',
    'Set `BUNDLE` to the copied `out/` directory and `TOOL` to the patched ingester. Choose a fresh `REPLAY` '
    'scratch directory. The following paths are examples to set once:', '', '```bash',
    'BUNDLE=/scratch/jjyeung/orch_n30/corpus/review3_bundle/out',
    'TOOL=/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py',
    'REPLAY=/scratch/jjyeung/orch_n30/corpus/review3_replay_20261119',
    '```', '',
    'For each read, compare the two scratch read-file SHA256 values after both commands exit 0. '
    'A strict exit 2 is an unresolved integrity or partial-return refusal; inspect it before proceeding. '
    'Stop on unexpected termination and do not retry automatically. The indexed published SHA256 is also '
    'shown, but its publisher used a different tool version. A strict/default difference isolates the '
    'opt-in checks; a difference from publication alone does not.', '',
]
owner_prefix = ('nice -n 10 env CUDA_VISIBLE_DEVICES=\'\' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 '
                'OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 '
                '/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest ')
for row in audit['reads_detail']:
    if row['read_id'] not in audit['enabled_unverified_ids']:
        continue
    rid = row['read_id']
    entry = entries[rid]
    fields = ('read_id', 'set', 'vehicle', 'official', 'export', 'arms', 'serving', 'reader_build',
              'job_id', 'date', 'purpose', 'reported_by', 'notes')
    metadata = {k: entry[k] for k in fields if k in entry}
    (meta_dir / (rid + '.json')).write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
    common = '--source ' + shlex.quote(row['source']) + ' --meta "$BUNDLE/replay_meta/' + rid + '.json"'
    if row['format'] == 'native':
        common += ' --inputs /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src'
    owner += ['## ' + rid, '', 'Published read SHA256: `' + row['output']['sha256'] + '`.', '', '```bash',
              'date -u', owner_prefix + common + ' --read-id ' + rid + ' --out "$REPLAY/default"',
              'date -u', owner_prefix + common + ' --read-id ' + rid + ' --out "$REPLAY/enabled" --review2-checks',
              'nice -n 10 sha256sum "$REPLAY/default/reads/' + rid + '.jsonl.gz" "$REPLAY/enabled/reads/' + rid + '.jsonl.gz"',
              '```', '', 'If the verified strict output must become a new read, this exact command uses a new ID. '
              'It stages only; publication remains a separate owner action:', '', '```bash', 'date -u',
              owner_prefix + common + ' --read-id ' + rid + '.review3 --out "$REPLAY/new_ids" --review2-checks',
              '```', '']
(OUT / 'OWNER_REPLAY.md').write_text('\n'.join(owner))

patch_log = (OUT / 'round3_logs/patch_applied.txt').read_text()
rss = re.search(r'MEASURED_MAX_RSS_KIB=(\d+)', patch_log).group(1)
elapsed = re.search(r'MEASURED_ELAPSED_SECONDS=([\d.]+)', patch_log).group(1)
fixed_hash = next(r['output_sha256'] for r in package['changed_files'] if r['path'] == 'ingest_read.py')
input_hash = next(r['input_sha256'] for r in package['changed_files'] if r['path'] == 'ingest_read.py')
report = [
    'VERDICT: PARTIAL All six required findings are fixed and tested; enabled-mode byte impact for seven published reads requires absent source returns.',
    '',
    '**Published bytes:** no changed read payload has been confirmed. Default read/orphan output is unchanged relative to the input tool. '
    'With `--review2-checks`, the following published read IDs remain unverified:', '',
    *['- `' + rid + '`' for rid in audit['enabled_unverified_ids']], '',
    '**Index bytes:** regenerating any of the 18 published entries would change `tool_version`; all 18 IDs appear in the table below. '
    'The published corpus was never edited. Do not interpret an unverified enabled-mode read as certified unchanged.', '',
    'All counts and resource values in this report are measured locally or read from the named index. '
    'The byte-impact classifications are code/index conclusions, not real-return replay measurements. '
    'Completion timestamp from `date -u`: ' + now + '.', '',
    '| Evidence | Measured or recorded result |', '|---|---|',
    '| Required findings | 2 MEDIUM and 4 LOW fixed; no HIGH findings in the verdict |',
    '| Round-three baseline | 17 tests; 27 failing assertions/subtests across 14 test methods; all 6 findings reproduced |',
    '| Immutable-input regressions | 3 tests; 3 failures |',
    '| Patch-applied full suite | 61 tests: 60 passed, 1 skipped because its real return is absent |',
    '| Existing synthetic suite | 20 passed on input; 20 passed with checks enabled on the patch-applied tool |',
    '| Default compatibility | 13 fixtures; identical read/orphan bytes; indexes differ only in tool_version |',
    '| Patch application | 20 delivered files match; 15 input files unchanged, 3 modified, 2 new test files |',
    '| Test process | ' + rss + ' KiB peak RSS; ' + elapsed + ' seconds elapsed |',
    '| Published index | 18 entries; 14,323,288 bytes; read-only copy throttled to at most 8 MiB/s |',
    '| Native evidence | 9 hash-verified input files; 6,967 input rows; 636 keys with exactly 2 compatible candidates each |',
    '| Workspace before final report/manifest write | ' + str(workspace_bytes) + ' bytes; below 3 GB |',
    '| Cumulative patch | ' + str(package['patch_bytes']) + ' bytes |', '',
    '## Review round 3: finding -> fix -> test', '',
    '| Finding | Fix | Regression evidence |', '|---|---|---|',
    '| 1 MEDIUM: partial native populations refuse even with archive-partial | Missing arms and key subsets append partial issues. Extra arms/keys and conflicting declarations still refuse. Without a declared key list, validation uses the union of observed populations to identify missing keys. | `test_f1_missing_arm_can_be_archived_partial`, `test_f1_subset_keys_can_be_archived_partial`: baseline exits 2 with archive-partial; fixed exits 0 and both read/index mark partial. Without archive-partial, fixed exits 2. Existing extra-key/arm and declaration tests still pass. |',
    '| 2 MEDIUM: new reads omit the switch | HOWTO’s new-read command explicitly passes `--review2-checks`; SCHEMA documents aliases, partials, contradictions and joins. `add_read.sh` remains byte-identical and forwards the explicit flag. This resolves the dispatch’s default-off constraint without silently changing callers. | `test_f2_documented_new_read_command_enables_checks`: baseline recipe fails; fixed recipe passes, and an isolated execution of the wrapper’s ingest line proves flag and quoted input-path forwarding. Publication commands never execute in the test. |',
    '| 3 LOW: duplicate eligible kit scores silently select first | Compare scores across every eligible exact row, or every eligible key-only alias if no exact row exists; refuse differences even when inline scores exist. Exact-ID precedence remains unchanged. | `test_f3_conflicting_key_only_scores_refused`, `test_f3_conflicting_exact_scores_refused`, `test_f3_conflict_cannot_be_archived_partial` fail before and pass after; identical duplicates and exact precedence pass. |',
    '| 4 LOW: unlabeled native report rows skip contradiction checks | Resolve a missing report arm from `arms.X`, compare duplicates with the resolved label, and normalize report-only arms. Preserve original rows in raw fields. Malformed arm-array rows refuse. | `test_f4_unlabeled_report_contradiction_refused`, `test_f4_unlabeled_contradiction_cannot_be_archived_partial`, `test_f4_unlabeled_report_only_arm_is_preserved` fail before and pass after; the latter checks unmodified raw rows. |',
    '| 5 LOW: native row fields override task identity | Compare shared question/options/room/room_key/scene/video/type/stratum/truth/scorer/unit/released-answer fields against all compatible task-candidate evidence before normalization. Native `answer` remains a prediction. | `test_f5_row_task_room_conflict_refused` plus 14 field subtests and an additive-candidate test fail before and pass after. Matching fields and differing predictions remain accepted. |',
    '| 6 LOW: inputs supplied but task absent yields complete nulls | Track explicit input loading, including empty directories; refuse a native key without a candidate when inputs are supplied or input paths exist. No-input null behavior remains supported. | `test_f6_missing_input_task_refused`, `test_f6_empty_explicit_inputs_cannot_archive_null_task` fail before and pass after; the no-input control passes. |', '',
    'Every LOW fix is small and implemented. No required finding was deferred. Findings 7 and 8 are informational: '
    'finding 7 requires the publication qualifications below; finding 8 retains the documented orphan-sidecar contract. '
    'All 636 selected native tasks lack `room_key`; compatible evidence with that field stays in the sidecar. '
    'The checks do not merge it into `raw.input` or normalized fields. Changing that contract would change bytes and needs new read IDs.', '',
    'The two review-two tests that expected hard refusal for a missing arm now check partial issues and CLI exit semantics. '
    'The exact-population refusal regression now uses an undeclared key, so it continues to test a hard contradiction.', '',
    '## Patch and default behavior', '',
    'Apply only [01_ingest_review2.diff](patches/01_ingest_review2.diff) to the immutable input tree. '
    'Despite its retained filename, this is the complete cumulative patch, including both review rounds, documentation and tests. '
    'Its SHA256 is `' + package['patch_sha256'] + '`. The input ingest SHA256 is `' + input_hash + '`; '
    'the fixed ingest SHA256 is `' + fixed_hash + '`.', '',
    'All production behavior changes require `--review2-checks`, whose default is off. '
    'The wrapper, scorer, publisher, routed adapter, offread adapter and emission logic are unchanged. '
    'The default compatibility checks compare compressed read files and orphan sidecars byte for byte, and compare all index fields except `tool_version`. '
    'The index stores the executing script hash, so changed code necessarily changes that provenance field when generating a new index. '
    'Existing published entries retain their original bytes.', '',
    '## Published-read impact', '',
    'The read-only published INDEX was re-read at 10:57:13 UTC into `work/evidence/INDEX_round3.jsonl`. '
    'Its SHA256 is `' + audit['index_sha256'] + '`, identical to the supplied task’s saved snapshot. '
    'The published tool version is `' + audit['recorded_tool_versions'][0] + '`, which differs from the immutable input version. '
    '“Unchanged” below means that these fixes introduce no default-path payload difference relative to that input; it does not claim to reproduce a different publisher version.', '',
    '| Published read_id | Format | Items | Arms | Default payload | Enabled payload | Regenerated index |',
    '|---|---|---:|---|---|---|---|',
]
for row in audit['reads_detail']:
    report.append('| `' + row['read_id'] + '` | ' + row['format'] + ' | ' + str(row['item_count']) + ' | ' +
                  ', '.join(row['arms']) + ' | unchanged | ' + row['enabled'] + ' | would change tool_version |')
report += ['',
    'The 7 routed/offread reads use unchanged adapters. The 4 kit reads without report sources cannot enter the changed report-score path. '
    'The other 6 kit indexes omit per-item report IDs and duplicate scores. Their zero orphan counts do not exclude an exact-ID namespace collision or conflicting eligible scores. '
    'Their source archives are absent from this node’s mirror, so neither alias safety nor new score checks can be certified from INDEX alone.', '',
    'For native, the request and report declare the same 636 keys; each indexed arm has 636 items. '
    'The 9 input files match their published hashes and contain 6,967 rows, exactly the orphan count. '
    'The remaining 2,544 consumed rows equal 4 × 636 and cannot contribute bare-ID task candidates through the native benchmark-key path. '
    'Each key has exactly 2 compatible task candidates, so the missing-task check does not affect this published read. '
    'However, INDEX lacks the native per-row labels, score duplicates and row/task fields needed to evaluate the other checks. '
    'The native return archive is absent, so enabled-mode emission or refusal remains unverified.', '',
    'No published read payload is classified as confirmed “would change.” The 7 unverified IDs are not cleared for re-ingest under their existing names. '
    '[OWNER_REPLAY.md](OWNER_REPLAY.md) gives exact scratch-only commands for default/enabled comparisons and conditional new `.review3` IDs, with metadata derived from INDEX. '
    'These commands were not run. An enabled-mode refusal requires investigation; `--archive-partial` does not override an integrity contradiction.', '',
    '## Exact validation commands and outputs', '',
    'Commands ran from `/scratch/jjyeung/orch_n30/so_corpus_fix`. Each execution step began with `date -u`. '
    'Output blocks below contain the captured combined stdout/stderr verbatim; exit codes are recorded separately. '
    'The baseline failures are intentional evidence, not unexplained failures in the patched suite. '
    '`work/run_tests.py` confines fixtures to the workspace and imports only the listed test modules. '
    'The packaging command created a fresh `work/patchcheck_round3`; to repeat it, choose another unused scratch directory rather than deleting the delivered evidence.', '',
]
for label, filename, code, command in logs:
    report += [label + ':', '', '```bash', 'date -u', command, '```', '', '```text',
               (OUT / 'round3_logs' / filename).read_text().rstrip('\n'), '```', '',
               'Measured exit code: ' + str(code) + '.', '']
report += [
    '## Risks, detection, and remaining work', '',
    '- Operators who omit `--review2-checks` retain legacy behavior by dispatch requirement. Use the documented new-read command; the wrapper-forwarding regression guards that recipe.',
    '- Exact identity comparisons can reject contradictory annotations, including JSON-type differences. The refusal names the native key/field or report path. Inspect the raw source evidence; do not disable the switch to publish the read.',
    '- A final incomplete native return emits only available evidence with `partial=true` under `--archive-partial`. Extra keys, label conflicts, conflicting scores and missing task joins still return exit 2 before emission.',
    '- Report-only native rows without labels can add an arm with checks enabled. Tests verify raw preservation. Published impact for the native read remains unverified until its source archive is available.',
    '- `tests/test_real_returns.py` was neither imported nor executed, as required by the prompt. `test_no_leftovers` skipped because its real return is absent. No real-output replay, publication, owner command, SSH, Git, GPU work, paid API call or deletion ran.',
    '- The enabled-mode audit of the 7 listed reads remains incomplete. The concrete owner commands and metadata are delivered; the report stays PARTIAL until those missing-source checks establish payload equivalence or identify new read IDs.', '',
    'The ingest tool uses only the Python standard library; no tensor or training behavior is involved. '
    'Tests call `torch.set_num_threads(8)` before execution. The installed behavior is documented at '
    '`/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_torch_docs.py:9819` '
    '(CPU intra-op thread limit) and `:9822` (call before eager/JIT/autograd work), corroborated by the '
    '[official PyTorch 2.11 documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html), read during this task.', '',
    'Writing rule applied: `no-archaeology`. The before/after test evidence and the required review-round section are retained because the user explicitly requires them; no revision-history narrative is needed to interpret the delivered behavior.', '',
]
(OUT / 'REPORT.md').write_text('\n'.join(report))

manifest_paths = [ROOT / package['patch'], OUT / 'REPORT.md', OUT / 'OWNER_REPLAY.md',
                  ROOT / 'work/run_tests.py', ROOT / 'work/check_default_compat.py', ROOT / 'work/audit_round3.py',
                  ROOT / 'work/package_round3.py', ROOT / 'work/finalize_round3.py',
                  ROOT / 'work/evidence/INDEX_round3.jsonl', ROOT / 'work/evidence/published_round3_audit.json',
                  ROOT / 'work/evidence/package_round3.json']
manifest_paths += sorted((OUT / 'round3_logs').glob('*.txt'))
manifest_paths += sorted(meta_dir.glob('*.json'))
manifest_paths += sorted((ROOT / 'work/pre_round3').glob('*'))
def info(path):
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
manifest = dict(completed_utc=now, verdict='PARTIAL', findings_fixed=[1, 2, 3, 4, 5, 6],
                deferred_required_findings=[], tests_run=61, tests_passed=60, tests_skipped=1,
                confirmed_changed_read_payload_ids=[], enabled_unverified_ids=audit['enabled_unverified_ids'],
                regenerated_index_tool_version_changed_ids=audit['regenerated_index_version_changed_ids'],
                publication_modified=False, workspace_bytes_before_final_report=workspace_bytes,
                package=package, files=[info(p) for p in manifest_paths],
                commands=[dict(label=label, command=command, exit_code=code, output='out/round3_logs/' + filename)
                          for label, filename, code, command in logs])
(OUT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
receipt = dict(completed_utc=now, verdict=manifest['verdict'], patch_sha256=package['patch_sha256'],
               fixed_sha256=fixed_hash, input_sha256=input_hash, patch_bytes=package['patch_bytes'],
               report_sha256=info(OUT / 'REPORT.md')['sha256'], manifest_sha256=info(OUT / 'MANIFEST.json')['sha256'],
               unchanged_input_files=len(package['unchanged_files']), workspace_bytes=workspace_bytes)
(OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
(ROOT / 'work/STATUS.md').write_text(now + '\n\nAll six required review findings are fixed. '
    'The cumulative patch applies cleanly and reproduces all 20 delivered tool files. '
    'The patch-applied suite passes 60 tests and skips one absent-real-return test; the enabled existing suite passes 20. '
    'Thirteen default compatibility fixtures preserve compressed read/orphan bytes and every index field except tool_version. '
    'REPORT.md is PARTIAL solely because enabled-mode published impact for seven reads cannot be certified without absent source returns. '
    'Their IDs, exact owner replay/new-ID commands, metadata, test outputs and hashes are delivered. '
    'The published index was read only; no published payload or input tree was edited.\n')
print('REPORT: ' + str(OUT / 'REPORT.md'))
print('MANIFEST: ' + str(OUT / 'MANIFEST.json'))
print('VERDICT: PARTIAL; all 6 required fixes complete; 7 published enabled-mode impact checks need absent source returns')
print('WORKSPACE_BYTES_BEFORE_FINAL_REPORT=' + str(workspace_bytes))
print('PATCH_SHA256=' + package['patch_sha256'])
