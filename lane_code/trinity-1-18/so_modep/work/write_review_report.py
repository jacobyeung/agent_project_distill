"""Write the delivery report from exact retained test outputs."""
from pathlib import Path
import json, re, subprocess

L = Path(__file__).resolve().parents[1]
O = L/'out'
stamp = subprocess.check_output(['date', '-u'], text=True).strip()
parity = json.loads((L/'work/review1_parity/RESULT.json').read_text())
(O/'tests/review1_file_parity.json').write_text(json.dumps(parity, indent=2)+'\n')
matrix = json.loads((O/'tests/review1_native_matrix.json').read_text())
assert len(matrix) == 4 and all(row['returncode'] == 0 for row in matrix)
manifest = json.loads((O/'patches/manifest.json').read_text())
verification = json.loads((O/'tests/review1_delivery_verification.json').read_text())
mutations = json.loads((O/'tests/review1_mutations.json').read_text())
assert len(mutations) == 6
assert (O/'tests/review1_parity_mutation.json').is_file()

def summary(name):
    text = (O/'tests'/name).read_text()
    lines = [line for line in text.splitlines() if re.match(r'^(Ran \d+ tests? in |OK|FAILED)', line)]
    assert lines and lines[-1].startswith('OK'), (name, lines)
    return ' / '.join('`'+line+'`' for line in lines)

rows = []
for row in matrix:
    name = Path(row['log']).name
    rows.append('| '+row['label']+' | '+summary(name)+' | ['+name+'](tests/'+name+') |')
for label in ('standalone01', 'standalone02', 'targeted'):
    name = 'review1_'+label+'.log'
    rows.append('| '+label+' | '+summary(name)+' | ['+name+'](tests/'+name+') |')
contracts = O/'tests/review1_contracts.log'
if contracts.is_file():
    rows.append('| report/helper contracts | '+summary(contracts.name)+' | ['+contracts.name+'](tests/'+contracts.name+') |')
table = '\n'.join(rows)
parity_lines = '\n'.join(line for line in (O/'tests/review1_parity.log').read_text().splitlines()
                         if line.startswith('MODEP_PARITY '))
mutation_rows = []
for row in mutations:
    log = Path(row['log'])
    assert 'FAILED (failures=1)' in log.read_text()
    mutation_rows.append('| '+row['mutation']+' | `'+row['test'].split('.')[-1]+'` | `FAILED (failures=1)`; exit 1, errors 0 | ['+log.name+'](tests/'+log.name+') |')
contract_results = O/'tests/review1_contract_mutations.json'
if contract_results.is_file():
    for row in json.loads(contract_results.read_text()):
        log = Path(row['log'])
        mutation_rows.append('| '+row['mutation']+' | report/helper contract | `FAILED (failures=1)`; errors 0 | ['+log.name+'](tests/'+log.name+') |')
mutation_table = '\n'.join(mutation_rows)
peak = max(row['observed_peak_rss_kib'] for row in parity['results'])
patch_rows = '\n'.join('| ['+p['file']+'](patches/'+p['file']+') | `'+p['switch']+'=1` | '+str(p['bytes'])+' | `'+p['sha256']+'` |'
                       for p in manifest['patches'])

text = f'''VERDICT: DONE All review findings are fixed and regression-tested; both default-OFF patches are packaged against b262e7a7, while production adoption still requires real-store parity.

**Planning saving: ≤18.5 min, estimated (possibly 0).** No production ON launch or production saving was measured. The estimate assumes a 26.38% fixture reduction applies to an unmeasured 40–70 minute path-heavy share. Warm-cache 256-byte files can overstate the benefit on Orchard storage. Patch 02 adds zero minutes to the planning estimate. On the first approved ON launch, derive the conditional estimate as `0.264 * OFF phase_resources.frames.seconds`, then report actual matched OFF/ON timings separately.

| Quantity | Value | Evidence class |
|---|---:|---|
| Production mode-p duration, jobs 172660 / 171377 | 140.57 / 145.27 min | Measured logs, references in PROFILE.md |
| Revalidation/frame envelope | 70.20 min | Inferred residual, not a frame timer |
| Path benchmark, 32,768 references | 9.795 s OFF / 7.211 s ON; 26.38% lower | Retained measured fixture means, `tests/bench_paths.log`; not rerun for this source-spelling fix |
| Sparse regression fixture | 820 selected / 4,096 rows; four chunks per pass | Constructed fixture, asserted in delivered tests |
| Native parity | 39 files × four configurations; 76 rows, 2,432 references; 32 distinct frames per source | Measured/asserted CPU fixture; five source groups |
| Native parity peak RSS | {peak:,} KiB | Measured for this process, not every subprocess |

[PROFILE.md](PROFILE.md) contains the production source references, assumptions and retained benchmark measurements. The CPU parity times below establish output parity; they are not a production speedup estimate.

Both switches OFF on N's first launch. ON from the next launch only after one production launch shows parity on real stores. [NOTE_FOR_TREE_REBUILD.md](NOTE_FOR_TREE_REBUILD.md) names the exact kit lines, per-job ledger and production comparison files: `frame_inventory.sqlite`, `frames.json`, prepared indices including `vqa_indices.json` and `pose_scene_order.json`, all source databases/receipts, `data_receipt.json`, and the phase completion files. The first production job stays OFF; an isolated real-store shadow comparison must establish OFF/ON parity before a later job enables a switch. That production gate remains unsatisfied by this CPU delivery.

## Review round 1: finding -> fix -> test

The review contains no HIGH findings. Its one MEDIUM and four LOW findings are all addressed.

| Finding | Fix | Passing regression and broken variant |
|---|---|---|
| 1 MEDIUM: no order-sensitive multi-chunk sparse comparison | Test 820 keys below one-quarter density for both a table and JSON-expanding view. Compare raw `(i,row)` tuples, the complete `expect`/`keep` event stream and an order-dependent keep result. Trace exactly eight selected queries across two passes. Separately compare native inventory bytes for 820 distinct frames. | `test_multichunk_sparse_events_and_order_sensitive_output` and `test_multichunk_frame_inventory_bytes_are_order_sensitive` pass. Reversed chunks fail both; descending rows fail the ordered test. |
| 2 LOW: ON was only inferred; one-frame fixture | The native harness spies on `_resolve_read_fast` and `_selected_rows`, asserts zero OFF / positive ON calls, and requires multiple frames per source. The fixture supplies 32 physical files with distinct contents and rotates VQA frame order. | The four native runs pass. Ignoring either switch fails its counting regression. A deliberately degenerate one-frame native fixture fails the harness assertion. |
| 3 LOW: parser literal | Copy the base `mapping.__getattribute__("sp" "lit")` spelling into the cached parser. This is the only production-code change in this review. | `test_mapping_parser_preserves_source_spelling` passes; restoring the literal attribute spelling fails it. |
| 4 LOW: overstated savings | Use the bounded conditional estimate; the measurement helper multiplies the OFF frame timer by 0.264. | `test_review_contracts.py` checks the headline and a 1,000-second fixture gives exactly 264 estimated seconds. An inflated headline and wrong multiplier fail. |
| 5 LOW: unrecorded process-wide switches | Document training/resume inheritance, exact `<kit>/b/r.sh` export lines and both values beside the job ID in `<kit>/o/modep_switches.jsonl`. | Document contracts pass; removing the scope, SQL switch line or ledger requirement fails. |

The requested review-round heading records the finding-to-evidence mapping. It is retained to meet the dispatch requirement. This is an internal operator report, so exact implementation names and paths are necessary.

The patches apply independently and together with zero fuzz or offsets. The recomputed base seal is `{verification['base_seal']}`. The base has {verification['base_files']} files; delivery has {verification['delivered_files']}. Only the six manifest-listed files differ: three production files and three tests. [Application output](tests/review1_patch_application.json) and [verification](tests/review1_delivery_verification.json) record the checks. No default or switch semantics changed during this review.

| Patch | Enable switch; default OFF | Bytes | SHA256 |
|---|---|---:|---|
{patch_rows}

[manifest.json](patches/manifest.json) binds both patches and every file to base seal `b262e7a7`. Each patch includes its targeted tests. Rebuild native authenticated identities before adoption.

Patch 02 retains the full-file pin hash and read-only connection (`student_pilot/s1_exclusions.py:161-168`), selected membership checks and original output-index order (`:173-184`). Sorted disjoint 256-key chunks use explicit `ORDER BY i` (`:147-158`). The unique native integer keys make concatenated chunks equal the native ascending scan. The [SQLite SELECT documentation](https://www.sqlite.org/lang_select.html#orderby) specifies the ordering behavior. Tests now prove the order and content of both validation passes, not just output length.

Patch 01 retains the original OFF resolver and every resolution/refusal check (`student_pilot/orchard_paths.py:33-62`); its cache holds mapping text only (`:84-88`). [Python pathlib](https://docs.python.org/3.12/library/pathlib.html#pathlib.PurePath.is_relative_to) specifies lexical containment. Production numerical operations, RNG draws, thread settings, pin authentication and receipt schemas are unchanged.

All rerun suite results are exact summaries from the linked complete stdout/stderr logs:

| Configuration/suite | Exact output | Full output |
|---|---|---|
{table}

Each matrix run executes the 112 focused native tests plus the extended admission, exclusion, journaling, alias, import and fast-path regressions. Its two explicit skips are the unavailable external dev-S1 manifest and socket-dependent Gloo. Standalone 01 skips Gloo; standalone 02 skips the external manifest. The targeted 13-test regression suite has no skips.

The native harness executes real `s1_admission.admit(..., prepare_only=True)` with the supplied tiny model/tokenizer and selected-parent fixtures. It fixes paths, UUIDs and exactly native `resources.seconds` / `resources.peak_rss_kib` during publication; native writers recompute all dependent pins. It compares the complete file sets, SHA256 values and raw bytes without post-hoc exclusions. Exact output:

```text
{parity_lines}
```

[Full native output](tests/review1_parity.log) and [every file/digest, observed calls, source counts and timers](tests/review1_file_parity.json) contain the evidence. The native fixture ran against `work/tree`; package verification proves that tree is byte-identical to the fresh `work/delivery_tree` used by the matrix.

Deliberately broken variants are retained under `work/review1_mutations/`. Each code mutant replaces one function in memory, preserving its real module globals so spies and fixture patches still work. The following failures are expected; the mutation driver requires an assertion failure and zero test errors:

| Broken variant | Regression | Exact outcome | Full failure |
|---|---|---|---|
{mutation_table}

The one-frame native fixture separately exits 1 at `assert all(value['unique_frames'] > 1 ...)`; [failure output](tests/review1_parity_degenerate.log) and [driver result](tests/review1_parity_mutation.json) show it. The delivered native fixture passes that assertion for every source in all four configurations. The corrected implementations pass the targeted suite and the full matrix.

Commands run from `/scratch/jjyeung/orch_n30/so_modep`:

```bash
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/package_patches.py' > out/tests/review1_package_manifest.log
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_review_package.py' > out/tests/review1_package_verification.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/validate_matrix.py' > out/tests/review1_matrix_driver.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; export MODEP_TREE="$PWD/work/tree" MODEP_TEST_LABEL=review1_targeted; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_native_tests.py tests.test_modep_select_sql tests.test_modep_fast_paths' > out/tests/review1_targeted.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; export MODEP_TREE="$PWD/work/tree" MODEP_NATIVE_LABEL=review1_parity; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/native_parity.py' > out/tests/review1_parity.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; export MODEP_TREE="$PWD/work/review1_patch01" MODEP_TEST_LABEL=review1_standalone01; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_native_tests.py tests.test_modep_fast_paths tests.test_modep_gloo tests.test_s1_admission' > out/tests/review1_standalone01.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; export MODEP_TREE="$PWD/work/review1_patch02" MODEP_TEST_LABEL=review1_standalone02; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_native_tests.py tests.test_modep_select_sql tests.test_s1_scene_exclusions' > out/tests/review1_standalone02.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_review_mutations.py' > out/tests/review1_mutations_final.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_parity_mutant.py' > out/tests/review1_parity_mutant_driver.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_review_contracts.py' > out/tests/review1_contracts.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_review_contracts.py --mutations' > out/tests/review1_contract_mutations.log 2>&1
```

The matrix driver prints exactly `off 0`, `paths 0`, `sql 0`, `both 0`, each on its own line. [Expanded matrix commands](tests/review1_native_matrix.json), [code mutation driver](tests/review1_mutations_final.log), [document mutation driver](tests/review1_contract_mutations.log), and [package output](tests/review1_package_verification.log) preserve exact outputs. These commands used fresh retained output labels; an independent replay needs new labels rather than deleting fixtures or rerunning the package verifier over existing trees.

What could go wrong: production metadata latency and database density may erase the saving; compare matched phase seconds and retained-reference denominators. Unexpected path aliases, symlink changes or corrupted inputs must still refuse; any differing row, inventory byte, sample or refusal blocks adoption. Process-wide inheritance extends beyond mode p, so retain normal native training/proof gates. Code edits change source seals, so rebuild all authenticated launch artifacts.

Not done: real-store production parity, production savings, full H100 training, the unstaged external-manifest test and socket-enabled Gloo. `work/run_gloo.sh` remains the requested lane follow-up and is not claimed as distributed fast-path coverage. No production switch was enabled.

All compute ran at nice 10 on CPUs 0–7 with CUDA hidden and OMP/MKL/OpenBLAS capped at eight. Test code calls `torch.set_num_threads(8)`; installed Torch 2.11 documents CPU intra-op control at `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_torch_docs.py:9815-9826`, and one-time interop control at `:9829-9840`. The [official Torch 2.11 documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html) was checked during this review. No Git, SSH, Slurm, paid API, GPU execution or deletion was used; inputs stayed read-only. Work began 2026-11-19 10:59:49 UTC on trinity-1-18; the deadline is 12:29:49 UTC. Report generated {stamp}.
'''
(O/'REPORT.md').write_text(text)
print('REPORT_WRITTEN '+stamp)
