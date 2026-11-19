"""Write the review report and hash manifest from captured validation evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'out'
audit = json.loads((ROOT / 'work/evidence/published_round4_audit.json').read_text())
package = json.loads((ROOT / 'work/evidence/package_round4.json').read_text())
commands = json.loads((OUT / 'round4_logs/commands.json').read_text())
stamp = subprocess.check_output(['date', '-u'], text=True).strip()
env = "CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1"
spec = importlib.util.spec_from_file_location('proof', ROOT / 'work/tool/prove_kit_alias_ids.py')
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)
kit = [r for r in audit['reads_detail'] if r['format'] == 'kit' and r['report_sources']]
assert {r['read_id']: r['item_count'] for r in kit} == proof.EXPECTED_COUNTS
assert all(r['orphan_count'] == 0 for r in kit)
kit_bytes = sum(r['output']['bytes'] for r in kit)
kit_items = sum(r['item_count'] for r in kit)
workspace_bytes = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())

owner = (OUT / 'round3/OWNER_REPLAY.md').read_text()
owner = owner.replace('review3_bundle', 'review4_bundle').replace('review3_replay', 'review4_replay')
owner = owner.replace('.review3', '.review4')
proof_command = ("nice -n 10 env " + env +
                 ' /usr/bin/python3 -I -s -B "$BUNDLE/scripts/prove_kit_alias_ids.py" '
                 '--corpus-root /data2/jjyeung/agent_project_data/distill_trace_corpus')
owner = owner.replace('Install the delivered patch', 'Install patch 01 (and patch 02 for new-read wrapper use)')
marker = 'For each read, compare the two scratch read-file SHA256 values'
addition = f'''The corpus owner on trinity-3-30 runs the cheap alias proof after scheduling shared I/O. This agent did not run it on `/data*`. Set `BUNDLE` as above, then run:

```bash
date -u
{proof_command}
```

The script opens only the six named kit read files with report sources. It reads them serially at at most 1 MiB/s in 64 KiB chunks, validates each read ID and item count, and scans every `item_id` for `devrows:`. INDEX records {kit_bytes:,} compressed bytes and {kit_items:,} items across these files; these are snapshot values, not fresh measurements. No INDEX, source archive, directory tree, or other published file is read by the script. The script writes nothing.

Exit 0 means all six files completed with zero matching IDs. Together with their recorded zero orphan counts, this rules out the actual-ID alias defect in finding 7. Exit 1 means matching IDs exist and source inspection is needed. Exit 2 means the proof is incomplete; missing/corrupt files, malformed rows, identity/count mismatches, and oversized rows cannot yield success. This scan does not certify duplicate report scores (finding 3) or any native-return check. Stop if a command is killed; do not relaunch automatically.

'''
owner = owner.replace(marker, addition + marker)
(OUT / 'OWNER_REPLAY.md').write_text(owner)

unverified = '\n'.join('- `' + read_id + '`' for read_id in audit['enabled_unverified_ids'])
report = f'''VERDICT: DONE Findings 1–6 are fixed and tested; separate wrapper and paced owner-run proof patches are delivered.

**Published payload impact:** no changed published read payload is confirmed. Direct ingest with the switch off preserves read/orphan bytes relative to the input tool. Enabled-mode payload equivalence remains unverified for these read IDs because their source returns are absent:

{unverified}

**Index impact:** regenerating any of the 18 indexed reads changes `tool_version`; every ID is listed below. The published corpus was neither read nor edited during this round. The saved INDEX and mirrored task inputs supply the publication evidence. Do not republish an existing read ID to activate these checks.

## Measured and recorded results

Completed on trinity-1-18 at {stamp}. Start: Thu Nov 19 11:57:38 UTC 2026; deadline: 13:27:38 UTC. Counts below are measured locally or read from named evidence, never estimated performance results.

| Evidence | Result |
|---|---|
| Required findings | 2 MEDIUM and 4 LOW fixed; none deferred |
| Before-fix regressions, rerun | 17 tests; 27 failing assertions/subtests across 14 methods; all six findings reproduced |
| Wrapper before-fix regression | 1 test; 1 failure when the caller omits the flag |
| Original input regressions | 3 tests; 3 expected failures |
| Original input synthetic suite | 20 tests passed |
| Core patch only | 61 tests: 60 passed, 1 skipped for absent real return |
| Full applied patch stack | 70 tests: 69 passed, 1 skipped for absent real return |
| Existing suite with checks enabled | 20 tests passed |
| Default compatibility | 13 fixtures; read/orphan bytes identical; index differs only in tool_version |
| Full test process | 227972 KiB peak RSS; 1.97 seconds elapsed |
| Patch application | 23 delivered files match; 14 input files unchanged, 4 modified, 5 added |
| Local INDEX snapshot | {audit['index_bytes']:,} bytes; 18 reads |
| Native task audit | 9 hash-verified files; 6,967 input rows; 636 keys with 2 compatible candidates each; zero conflicts |
| Cheap proof's target files | 6 named files; {kit_bytes:,} compressed bytes and {kit_items:,} items recorded in INDEX; production scan not run |
| Workspace before final report/manifest | {workspace_bytes:,} bytes; below the 3 GB limit |

## Review round 4: finding -> fix -> test

| Finding | Fix | Before/after regression evidence |
|---|---|---|
| 1 MEDIUM: partial native returns hard-refuse | Missing required arms and strict key subsets append issues. Exit 2 without `--archive-partial`; exit 0 with `partial=true` when archiving. Undeclared arms, extra keys, contradictory declarations and label mismatches still raise Refusal. | `test_f1_missing_arm_can_be_archived_partial`, `test_f1_subset_keys_can_be_archived_partial` fail before and pass after, checking both CLI exits and read/index partial flags. Review-two missing-arm tests now check partial semantics; the hard-refusal population test uses an undeclared key. |
| 2 MEDIUM: checks are inert for new reads | SCHEMA documents the switch in completion/alias/native contracts; HOWTO enables it in the new-read command. Separate patch 02 adds the flag to `add_read.sh`. Direct ingest still defaults off. | `test_f2_documented_new_read_command_enables_checks` fails before and passes after. `test_wrapper_enables_checks_without_caller_flag` fails on the saved current wrapper and passes with patch 02; quoted paths and forwarded flags survive. |
| 3 LOW: conflicting eligible kit scores choose the first | Compare every eligible exact match, or every key-only alias if no exact match exists; differing scores always refuse, including with inline scores or archive-partial. Exact-ID precedence remains intact. | `test_f3_conflicting_exact_scores_refused`, `test_f3_conflicting_key_only_scores_refused`, `test_f3_conflict_cannot_be_archived_partial` fail before and pass after. Identical duplicates and exact-ID precedence pass. |
| 4 LOW: unlabeled native report rows skip validation | Infer arm X from `arms.X` for validation and normalization. Compare the resolved row with the journal; conflicting duplicates refuse. Report-only rows are emitted with original raw fields intact. | All three `test_f4_*` cases fail before and pass after: contradiction refusal, refusal despite archive-partial, and report-only arm/raw preservation. |
| 5 LOW: native row overrides task identity | Compare shared question/options/room/room_key/scene/video/type/stratum/truth/scorer/unit/released-answer fields against all compatible candidate evidence before normalization. Native `answer` remains a prediction. | Room conflict, 14 field subtests, and an additive-candidate conflict fail before and pass after. Matching identity and differing predictions remain accepted. |
| 6 LOW: supplied inputs lack a native task | Track explicit input loading, including empty directories; refuse result keys without candidates whenever inputs are supplied or loaded. No-input null behavior remains documented. | `test_f6_missing_input_task_refused` and `test_f6_empty_explicit_inputs_cannot_archive_null_task` fail before and pass after. No-input control passes. |
| 7 INFO: cheap alias proof | Deliver `scripts/prove_kit_alias_ids.py`, also in patch 03. The corpus owner on trinity-3-30 runs it after scheduling shared I/O. This agent ran synthetic tests only. | Eight script tests cover six-file scope, a match in the last row/file, missing/corrupt/short files, invalid identity/JSON, and pacing before bounded reads. |

No required fix is deferred. Finding 8 retains the sidecar contract: compatible additive `room_key` evidence is not merged into native `raw.input` or normalized fields. The audit confirms all 636 selected tasks lack that field; the compatible candidates carrying it remain in the orphan sidecar. This acceptance does not make the field available to analyses that read only `reads/`.

## Patches and installation

All diffs target the immutable input tree at `{package['input_root']}`. Patch 01 contains the complete ingest fixes, docs and core tests. Patch 02 changes the wrapper and adds its regression; it requires patch 01's CLI support. Patch 03 adds only the owner proof script and tests. The owner can take patch 01's docs/checks without patch 02; the core-only applied-tree test verifies that combination.

| Patch | Bytes | SHA256 |
|---|---:|---|
'''
for patch in package['patches']:
    path = Path(patch['path'])
    report += f"| [{path.name}](patches/{path.name}) | {patch['bytes']} | `{patch['sha256']}` |\n"
report += f'''
The input ingest SHA256 is `{package['input_hashes']['ingest_read.py']}`; the fixed ingest SHA256 is `{package['output_hashes']['ingest_read.py']}`. The saved report, patches, manifest and owner instructions are under [round3/](round3/). `work/pre_round4` preserves the tool before this dispatch; `work/pre_round3` supplies the unfixed finding regressions.

Every ingest behavior change is gated by `--review2-checks`, default false. Patch 02 explicitly selects this mode for the new-read wrapper; the direct CLI default does not change. The scorer, publisher, routed/offread adapters and emission logic remain unchanged. Index `tool_version` hashes the executing script, so newly generated index bytes cannot be identical after any code fix; this is the sole default-mode index difference in all 13 fixtures.

## Published-read classification

The saved snapshot `work/evidence/INDEX_round3.jsonl` hashes to `{audit['index_sha256']}`. All published entries record tool version `{audit['recorded_tool_versions'][0]}`, which differs from the input script. “Unchanged” below means no payload difference introduced relative to the supplied input script, not a replay of the different published tool version. These are code/index conclusions; no real-return replay measurement is claimed.

| Published read_id | Format | Items | Arms | Default payload | Enabled payload | Regenerated index |
|---|---|---:|---|---|---|---|
'''
for row in audit['reads_detail']:
    report += '| `%s` | %s | %s | %s | unchanged | %s | would change tool_version |\n' % (
        row['read_id'], row['format'], row['item_count'], ', '.join(row['arms']), row['enabled'])
report += f'''
The seven routed/offread reads use unchanged adapters. The four kit reads without report sources cannot reach the changed report lookup. For the other six kit reads, zero orphans and the absence of `devrows:` item IDs would prove that the actual-ID alias defect did not fire. The delivered scan establishes the missing premise; it has not been run on production. Even a successful scan does not exclude conflicting duplicate scores, so finding 3 still needs source replay before certifying enabled-mode equivalence.

For native, request/report declarations agree on 636 keys and INDEX records 636 items per arm. The nine mirrored input files match the indexed hashes and supply all 6,967 orphan candidates. The other 2,544 consumed rows are 4 × 636 native-key rows, which cannot provide bare-ID task candidates. Each key has two compatible candidates, so full task-candidate identity and missing-task checks do not affect this read. Per-arm key sets, report labels/duplicates and row/task conflicts still require the absent source return. An enabled refusal is not a demonstrated byte change; it requires diagnosis before publication.

No published payload is confirmed “would change.” The seven unverified IDs above must not be reused for an enabled re-ingest. [OWNER_REPLAY.md](OWNER_REPLAY.md) supplies exact scratch-only comparisons and conditional `.review4` read IDs with saved metadata. The owner runs the proof and any replay on trinity-3-30. None of those commands ran here.

The cheap proof reads exactly {kit_bytes:,} compressed bytes if the files still match the snapshot, paced at 1 MiB/s with no catch-up bursts. Expected scan time is an estimate: at least about {kit_bytes / (1024 * 1024):.1f} seconds of pacing, plus decompression and filesystem latency. The script opens only six named gzip files, checks read IDs and item counts, and writes nothing. Exit 0 means no prefixed IDs; exit 1 means IDs found; exit 2 means incomplete proof.

## Exact validation commands and outputs

All commands run from `{ROOT}` with this environment:

```bash
export {env}
```

Each step started with `date -u`; its exact timestamp, command, combined stdout/stderr and exit code follow. Baseline nonzero exits are expected demonstrations. The `before_findings` run uses `work/pre_round3`, where findings 1–6 are unfixed; the wrapper baseline uses `work/pre_round4`. Packaging creates fresh directories and is not an overwrite/retry recipe. The real-return module is excluded by the prompt.
'''
for command in commands:
    report += f"\n### {command['name']}\n\nUTC: `{command['utc']}`. Measured exit code: {command['exit_code']}.\n\n```bash\ndate -u\n{command['command']}\n```\n\n"
    output = (ROOT / command['output']).read_text()
    report += '```text\n' + output + '```\n' if output else 'Exact combined stdout/stderr: empty.\n'
report += '''
## Risks, detection and work not run

- Direct callers can omit the switch and retain legacy behavior. The documented command and separate wrapper patch select checks for new read IDs.
- Exact identity checks can reject inconsistent annotations or JSON types. Refusal messages name the key, field, arm or report source. Investigate source evidence; archive-partial does not override integrity contradictions.
- Partial native reads contain available rows and mark every emitted item and index as partial. Missing arms/keys never produce a falsely complete read with checks enabled. Extra keys, contradictory declarations and labels remain refusals.
- Unlabeled native report-only rows can add an arm when checks are enabled. The synthetic regression verifies both inclusion and raw preservation. The native published read needs source replay to determine whether this changes its payload.
- Production proof/replay, publication and deployment were not run. No published file, SSH, Git, GPU job, paid API call or deletion was used. Only library documentation was accessed over the network.
- `tests/test_real_returns.py` was not imported or executed, as required. `test_no_leftovers` skipped because its real return is absent. This limits real-source certification; it does not defer a required code fix.

The ingester and proof script use the Python standard library. The test harness calls `torch.set_num_threads(8)` before execution. Installed-source evidence: `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_torch_docs.py:9819` documents the CPU intra-op thread limit; `:9822` requires setting it before eager/JIT/autograd work. The [official PyTorch 2.11 documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html) was also read. No other tensor/framework behavior is involved.

Writing rule applied: no-archaeology. The required review-round heading and before/after evidence remain because the user explicitly requested them. They show which defects the tests detect, not an implementation-history narrative.
'''
(OUT / 'REPORT.md').write_text(report)
(ROOT / 'work/STATUS.md').write_text(stamp + '\nDONE: findings 1–6 verified, all patches and regression evidence packaged. '
    'Core: 60 pass/1 skip; full: 69 pass/1 skip; 20 enabled existing tests pass; 13 default-byte fixtures pass. '
    'Report and manifest written. Owner on trinity-3-30 must run six-file proof and any published-source replay; '
    'seven enabled payloads remain unverified. Published corpus untouched.\n')
paths = [OUT / 'REPORT.md', OUT / 'OWNER_REPLAY.md', ROOT / 'work/STATUS.md',
         ROOT / 'work/run_tests.py', ROOT / 'work/check_default_compat.py',
         ROOT / 'work/package_round4.py', ROOT / 'work/validate_round4.py', ROOT / 'work/finalize_round4.py',
         ROOT / 'work/audit_round4.py', ROOT / 'work/evidence/package_round4.json',
         ROOT / 'work/evidence/published_round4_audit.json', ROOT / 'work/evidence/INDEX_round3.jsonl']
for folder in ['patches', 'scripts', 'round4_logs', 'replay_meta', 'round3']:
    paths.extend(p for p in (OUT / folder).rglob('*') if p.is_file())
manifest = dict(completed_utc=stamp, verdict='DONE', commands=commands, package=package,
                confirmed_changed_read_payload_ids=[], enabled_unverified_ids=audit['enabled_unverified_ids'],
                regenerated_index_version_changed_ids=audit['regenerated_index_version_changed_ids'],
                deferred_required_findings=[], production_proof_run=False,
                production_proof_owner='corpus owner on trinity-3-30 after scheduling shared I/O',
                proof_files=[dict(read_id=r['read_id'], **r['output']) for r in kit],
                workspace_bytes_before_finalization=workspace_bytes,
                files=[dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size,
                            sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(set(paths))])
(OUT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
print('REPORT: ' + str(OUT / 'REPORT.md'))
print('MANIFEST: %d hashed files; all six proof targets match INDEX and have zero orphans' % len(manifest['files']))
print('VERDICT: DONE; owner production proof/replays are explicitly not run')
