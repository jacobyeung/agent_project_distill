import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];O=L/'out'
read=lambda name:json.loads((O/name).read_text())
coverage=read('B3B_COVERAGE_CLASSIFIED.json');seal=read('TREE_SEAL.json');kits=read('B3B_KITS.json')
merged=read('B3B_MERGED_BINDING.json');review=read('B3B_FINAL_REVIEW.json')
regressions=read('B3B_REGRESSION_ACCEPTANCE.json')
assert regressions['all_required_pass'] and regressions['all_latest_pass'] and coverage['strict_cpu_gate']
tests=[]
for path in sorted(O.glob('B3B_*TEST_RESULTS.json')):
    v=json.loads(path.read_text())
    tests.append(f"| `out/{path.name}` | {v['tests']} | {len(v['failures'])} | {len(v['errors'])} | {len(v['skipped'])} |")
text=f'''# Build 3b report

The tree binds the merged dev population across every stream. Native metadata rebuilds, upstream receipts, the census and the trainer use the same exclusion pin. Both kits remain non-admitting until the real frame-host inputs and existing evidence gates pass. No job was submitted.

## For the tree review

- `student_pilot/r2_scene_bindings.py` deterministically merges the sealed dev list with the shared rooms and capture aliases. It rebuilds native pool selection, source receipts, the exact census, admitted counts and reader indices.
- `launch_r2/host.py` runs the metadata steps before the repeat gate and materialization. `native_config` attaches the rebuilt reports to every native stream receipt. `launch_r2/build.py` binds the merged list in both kits and leaves the new host inputs explicitly missing.
- `student_pilot/r2_intake.py` applies the merged native exclusion in addition to the retained sealed r2 rules. `s1_exclusions.py` and `s1_scene_census.py` recognize provenance aliases consistently and compare the rebuilt reference exactly. Existing foreign-list and census refusal messages remain.
- `student_pilot/r2_contract.py` verifies the all-stream bindings before preparation and prepared reads. Direct configuration also binds the merged population. Review the raw-source provenance, pool selection's own upstream report, reference pin, population counts and rank-facing indices together.
- `student_pilot/s1_pool.py` supports opaque output filenames and progress summaries for the host rebuild. Its native selection rules remain in use. `launch_r2/distributed.py` isolates parent imports after the full regression exposed a bootstrap module collision.

Paths above are relative to `work/tree_r1`. The complete changes against the immutable base are in `out/TREE.diff`; identities are in `out/TREE_FILES.sha256` and `out/TREE_SEAL.json`.

## Bound population

The merged SHA256 is `{merged['merged']['sha256']}` (`out/B3B_MERGED_BINDING.json`). It uses the sealed `dev_s1_withhold_v1` schema and preserves the original members. Its inputs are:

| Input | SHA256 | Source |
|---|---|---|
| Sealed dev population | `{merged['inputs'][0]['sha256']}` | `work/kit07ca49df_meta/m/k/dev_scene_exclusions.json` |
| Shared withheld rooms and aliases | `{merged['inputs'][1]['sha256']}` | `work/shared/WITHHELD_ROOMS_80.json` |

VQA, pool distance/room programs, camera, each sealed pose source and pointing all use this population. Both arms receive it because they share the mixture. Benchmark exclusions and the other sealed r2 exclusions remain independently required. Unknown overlap refuses.

The frame host rebuilds QID exclusion lists before invoking native `s1_pool.prepare`. It re-derives source receipts from authenticated metadata, prints and pins shared-room removal counts, writes the new `dev_s1_manifest_v1` reference, and derives counts and indices from actual admitted envelopes. The metadata pin must be bound by the original receipt; a matching count is insufficient. Native SQLite inputs open read-only. Full mode also binds the pose census to the sealed databases. The repeat gate then runs before any RGB store is materialized. The sealed selection or sealed reference fails the unchanged mismatch checks. The runnable entry is each kit's `b/f.sh`; the required inputs are documented in `out/FRAME_HOST_JOB.md`.

Real removal counts remain unknown. The card names the counts that the frame-host job must fill (`out/PRELAUNCH_CARD.md`). Local fixture counts are not population estimates and do not admit the real mixture.

## CPU evidence

The bounded pool fixture follows the supplied manifest, selection and index shapes. It includes native packed distance and room records and direct routing records. The real producer and `selected_rows` reader retain clean rows and refuse withheld native names and aliases. The pool-family proof also runs real materialization, native store reads, sampling and every-rank encoding (`out/B3B_POOL_PROOF.json`; `out/B3B_POOL_BATCH_PROOF.json`; `work/tree_r1/tests/test_r2_build3b.py`).

Per-stream proofs run real intake, materialization, SQLite reads and membership admission. Re-sealing a leaked row still fails the native reader. The integrated proof runs native preparation, census verification, the mixed sampler and encoding for every rank. Synthetic RGB, a tiny lossless processor/tokenizer and pretrained-model metadata stand in at the unavailable model boundary; producers, filtering, census, stores and readers are real. Encoding stops before model forward (`out/B3B_NATIVE_PROOF.json`). Retained earlier model proofs remain separate evidence.

The host metadata proof derives actual fixture counts and reader indices. Its incomplete fixture population fails the repeat gate before a store is written; no synthetic full-population admission is claimed (`out/B3B_COUNTS_PROOF.json`). Mutations cover old config/upstream/pool/reference bindings, census counts, incomplete metadata, source membership, cross-stream assignments, facing pairs and output containment (`work/tree_r1/tests/test_r2_build3b.py`).

| Test evidence | Tests | Failures | Errors | Skips |
|---|---:|---:|---:|---:|
{chr(10).join(tests)}

Every number in that table comes from the file named in its row. Earlier failed runs remain visible. Their fixture defects and any production fixes are recorded in `work/build3b/STATUS.md`; the accepted regression results determine the final status.

The full-suite run and subsequent targeted closure resolve all {regressions['required_tests']} required cases; the latest outcomes cover {regressions['final_tests']} cases and all pass (`out/B3B_REGRESSION_ACCEPTANCE.json`). This is cumulative acceptance, not a claim that the earlier full run passed before its defect was repaired. The per-case evidence remains linked in that record.

Changed-statement coverage over the cumulative tree is {coverage['executed']}/{coverage['total']}; production coverage is {coverage['production_executed']}/{coverage['production_total']}. The unexecuted production classes are `{coverage['unexecuted_by_class']}` (`out/B3B_COVERAGE_CLASSIFIED.json`). The standard-library tracer records current hits and remaps prior hits only across unchanged lines from authenticated snapshots. Each remaining statement has its file, line, text, category and reason (`out/B3B_COVERAGE_REMAP.json`; `work/build3b/coverage.py`).

## Artifacts and limits

Tree seal: `{seal['tree_sha256']}` (`out/TREE_SEAL.json`).

| Arm | Kit | SHA256 | Source |
|---|---|---|---|
'''
for item in kits:
    text+=f"| {'A0' if item['connector']=='none' else 'A2'} | `{item['kit_path']}` | `{item['kit_sha256']}` | `out/B3B_KITS.json` |\n"
text+=f'''
Temporary storage is {review['tmp_bytes']} bytes; the lane is {review['lane_bytes']} bytes (`out/B3B_FINAL_REVIEW.json`). The harness measures storage before and after each test, retains fixtures, and applies the required file-size and CPU limits (`work/build3b/TEST.sh`; `work/build3b/bounded_runner.py`). The storage walker matched the inherited walker exactly (`out/B3B_STORAGE_WALK.json`). The previous temporary folders were read-only. No full store or real checkpoint/frame/database/cache copy ran locally.

Not checked: real pool bytes, real source joins and counts, real metadata exports, actual frame-host runtime/relocation, full stores, pretrained forward behavior, GPU fit or timing, distributed training or evaluation. The A2 dense artifact remains an explicitly synthetic staging fixture. The existing scanner checks external job paths/arguments/environment and runtime filenames; native source namespaces and native receipt contents retain the previously disclosed scanner exceptions (`out/BUILD3_REPORT.md`; `work/tree_r1/launch_r2/build.py`).

No network, SSH, Git, other agent, launch or Orchard call ran. All writes stayed inside the lane.
'''
(O/'BUILD3B_REPORT.md').write_text(text)
design=O/'DESIGN_RECORD_tree_rebuild_20261115.md'
section='''
## Build 3b

Question: How can the shared rooms be excluded from every stream while the native sealed bindings still agree?

Answer: Bind a deterministic merged dev list in both arms, rebuild the routing pool through native metadata code, re-derive each stream receipt, generate an exact census reference, and compute after-withholding counts before the repeat gate. The trainer checks the same pins before accepting stores.

Reasons and evidence: The merged input/output identities are in `out/B3B_MERGED_BINDING.json`. Native pool selection and reading are proved in `out/B3B_POOL_PROOF.json`. The producer-to-reader CPU proof and metadata gate are in `out/B3B_NATIVE_PROOF.json` and `out/B3B_COUNTS_PROOF.json`. Cumulative changed-statement coverage and artifact checks are in `out/B3B_COVERAGE_CLASSIFIED.json` and `out/B3B_FINAL_REVIEW.json`.

Options rejected: Changing only the config pin leaves foreign upstream reports and census references. Relabelling an old report would hide its old population. Reusing sealed pool indices could retain withheld aliases. Using pre-withholding counts could admit excessive repeats. Guessing real counts would claim evidence that is absent. Each alternative is refused.

Default: Both arms share the merged population. Source metadata must describe the original receipt population before the added withholding; historical reports remain pinned provenance. The frame host supplies complete inputs and type assignments, whose content binds the generated counts and indices.

What might not work and how we notice: Real source metadata or joins may be missing or inconsistent; hash, population and membership checks refuse. Actual retained counts may exceed the repeat limit or break facing pairs; metadata checks refuse before stores. Host relocation/runtime and pretrained/GPU behavior remain untested.

Tests that would settle it: Run the pinned frame-host CPU job on real metadata and RGB, inspect per-source removal counts and the exact census, require the existing statement obligations and every rank's batch, then complete the separately required review and admission. Local fixtures do not substitute for these results.

Status: The implementation, bounded CPU evidence, refreshed tree and restaged kits are delivered for review. Real frame-host admission and all launch/GPU work remain pending. Exact test outcomes, source identities and limitations are in `out/BUILD3B_REPORT.md`.
'''
old=design.read_text() if design.exists() else '# Trainer-tree design record\n'
if '\n## Build 3b\n' not in old:design.write_text(old+section)
(L/'work/build3b/STATUS.md').write_text('''# Build 3b status

The tree, merged binding, native metadata rebuild, CPU proofs, cumulative coverage, kits and report are delivered. The authoritative results and remaining limitations are in `out/BUILD3B_REPORT.md`.

Defaults: both arms share the merged exclusion; missing or inconsistent real metadata refuses; source reports are recounted, never relabelled. Real frame-host admission and launch remain pending.

Test fixture defects repaired: the camera mutation needed provenance on native routing rows; a metadata test reused the pool fixture directory name. Production review moved metadata under the guarded runtime output, authenticated source-population bindings, supported canonical-only native metadata, and kept all original scene guards. The full regression exposed a parent-launcher import collision, now isolated and tested. Native pool output filenames and host progress summaries use opaque identifiers.
''')
