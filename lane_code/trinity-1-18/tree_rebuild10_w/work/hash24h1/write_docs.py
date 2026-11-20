"""Write compact evidence notes from the verified comparison."""
from pathlib import Path
import hashlib
import json

B=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
O=Path(__file__).resolve().parent
D=B/'w24/work/build24f'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(O/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
table=load(O/'LOOP_HASHES.json'); rows={r['file']:r for r in table['rows']}
checks={v:load(D/f'rehearsal{v[-1]}/CHECK.json') for v in ['run4','run5']}
missing=[r['path'] for r in checks['run4'] if not r['passed']]
assert missing==['milestone export / local receipt / kit copier']
assert next(r for r in checks['run5'] if r['path']==missing[0])['passed']
done_path=D/'rehearsal5/target/o/rehearsal/live/gcs_m2.done'
done=load(done_path)
artifact=D/'rehearsal5/train/m2/artifact.json'
assert sha(artifact)==done['marker_sha256']
local_path=D/'rehearsal5/train/persist'/(done['marker_sha256']+'.local.json')
receipt=load(local_path)
assert receipt['archive']['sha256']==done['sha256']
sources=['rehearsal_run4.log','rehearsal_run5.log','rehearsal_runner.py','rehearsal_runner5.py',
         'go_rehearsal.sh','go_rehearsal5.sh','rehearsal_copier.py','rehearsal_copier5.py',
         'rehearsal4/PREPARED.json','rehearsal4/SOURCE_SNAPSHOT.json','rehearsal4/VIEW.json',
         'rehearsal4/v.json','rehearsal4/STAGES.json','rehearsal4/CHECK.json','rehearsal3/code.json',
         'rehearsal5/PREPARED.json','rehearsal5/RUN_STARTED.json','rehearsal5/VIEW.json',
         'rehearsal5/code.json','rehearsal5/COPIER_SOURCE.json','rehearsal5/STAGES.json','rehearsal5/CHECK.json']
put('EVIDENCE_RECORDS.json',[dict(path=str(D/p),sha256=sha(D/p)) for p in sources])
copier={p:dict(launch=rows['kit/b/'+p]['sha256']['launch'],run4=rows['kit/b/'+p]['sha256']['run4'],
               run5=rows['kit/b/'+p]['sha256']['run5'],
               run5_equals_launch=rows['kit/b/'+p]['sha256']['run5']==rows['kit/b/'+p]['sha256']['launch'])
        for p in ['pc.sh','pc.py','sr.py']}
coverage=dict(run4_not_proved=missing,run4_passed=sum(r['passed'] for r in checks['run4']),
              run5_passed=sum(r['passed'] for r in checks['run5']),run5_unproved=[r['path'] for r in checks['run5'] if not r['passed']],
              run5_copier_row_passed=True,all_three_copier_files_byte_identical=False,copier_files=copier,
              marker_path=str(done_path),marker_file_sha256=sha(done_path),marker=done,
              artifact_path=str(artifact),artifact_hash_matches_marker=True,
              local_receipt_path=str(local_path),receipt_archive_hash_matches_marker=True,
              execution_scope='Run5 imports shipped pc.py with a local writer; pc.sh is inspected for source selection, not launched; sr.py execution is not demonstrated.',
              conclusion='Run5 covers the local copier row, but does not establish byte-identical coverage of all three launch copier files.')
put('COVERAGE.json',coverage)

provenance=f'''Paths below are absolute unless prefixed by `B`, where `B={B}`. A kit's recorded execution path differs from the preserved locations used to recover its bytes. Each table row records its actual byte source in `LOOP_HASHES.json`.

| Version | Recorded kit path | Kit manifest SHA-256 | Executed tree path | Tree seal |
|---|---|---|---|---|
| Launch GO | B/w24c/out/kit_n_go | {table['verification']['launch']['kit_manifest_sha256']} | B/w24c/work/tree_r1 | {table['verification']['launch']['tree_sha256']} |
| Run4 | B/w24/out/kit_n_go | {table['verification']['run4']['kit_manifest_sha256']} | B/w24/work/build24f/rehearsal3/p2/s | {table['verification']['run4']['tree_sha256']} |
| Run5 | B/w24/out/kit_n_go | {table['verification']['run5']['kit_manifest_sha256']} | B/w24/work/build24f/rehearsal5/p2/s | {table['verification']['run5']['tree_sha256']} |

Run4's root is `B/w24/work/build24f/rehearsal4`, as selected by `rehearsal_runner.py:9` and `go_rehearsal.sh`. The runner selects `L/out/kit_n_go` at lines 64 and 109. Its own `rehearsal4/PREPARED.json` records the kit and tree seals above. `rehearsal4/SOURCE_SNAPSHOT.json` names the physical source snapshot. The final mounts in `rehearsal4/VIEW.json` expose `rehearsal3/p2` as `/tmp/q_22c714e1/p2` and `rehearsal3/p2/s` as `w24/work/tree_r1`. Thus the empty host-side `rehearsal4/p2` directory is not the executed source. `rehearsal4/v.json` pins `rehearsal3/code.json`; its complete inventory and 274-source closure match the snapshot. Run4 records its kit seal at preparation, not separately in every stage record.

Run5's root is `B/w24/work/build24f/rehearsal5`. `rehearsal_runner5.py:62-75` checks its prepared kit path and seal, records `RUN_STARTED.json`, starts the selected kit's copier, and calls the selected `b/t.py`. `rehearsal5/RUN_STARTED.json`, `PREPARED.json`, `PREPARATION_STARTED.json` and `COPIER_SOURCE.json` independently name the path and seal above. The final mounts in `rehearsal5/VIEW.json` expose `rehearsal5/p2/s` at both the worker's `/tmp/q_22c714e1/p2/s` and `w24/work/tree_r1`. `rehearsal5/code.json` authenticates that snapshot and its 274-source closure.

The current `B/w24/out/kit_n_go/SHA256SUMS.txt` hashes to `{sha(B/'w24/out/kit_n_go/SHA256SUMS.txt')}`, so that directory cannot be treated as either complete historical kit. Matching individual files there are used only when their bytes match the historical manifest's exact digest.

Run4's exact manifest survives at `B/w24/work/build24i/armed_fixture_final/SHA256SUMS.txt` and `armed_upload_fixture_final/n/SHA256SUMS.txt`; both match the run's own seal. The first copy supplies its executable bytes. Its tar member digest matches `B/w24/work/build24f/t_57a1f14df5ab60e5.tar`. All tar members match the executed snapshot.

Run5's preserved non-GO sibling is `B/w24/work/build24k/upload/n` (manifest seal `814db98aabae2859b8be5bc8e509cc8fd43bd9baa32c11ec293176f155b116f8`). Changing only the decoded `k/a.json` GO value from false to true and updating that manifest row yields the exact run-recorded GO seal `05f0ffa1c8467c46c61f958ad239e9aef393bc3e6e293a55202c507ec84fbd76`. The recovered manifest is `RUN5_RECOVERED_SHA256SUMS.txt`; `RECOVERY.json` and `analyze.py` specify and verify the transformation. The sibling is sparse, so missing executable bytes come from other preserved copies, accepted only after matching this authenticated manifest. No input kit was reconstructed or modified on disk.

The launch GO and non-GO manifests match the requested seals `e54fc1b9...` and `0ef1e5e5...`. Every executable/helper compared between them is identical. Both tree tarballs hash to `ecf3de4ade6f9a81f678a14a522767b4c4f8184b9d2862cb29a4b6d2244b8a08`; their complete member inventories match tree C. `VERIFICATION.json` contains all full seals, archive paths and tree counts.

Run4's copier wrapper imports `build24f/live.py`, rather than its shipped `b/pc.py`; its NOT PROVED row cannot establish execution of the kit copier. Run5's wrapper imports its shipped `b/pc.py` and supplies a local writer, local sessions, an in-memory target override and an m2-to-m100 name mapping. Its actual training marker is `{done_path}`; its marker digest matches `train/m2/artifact.json`, and its archive digest matches the local persistence receipt. The separate `copier_synthetic` marker is not used as the training result here.

Run5's `pc.py` and `sr.py` match the launch kit, but `pc.sh` differs by the launch-only `b/ep.py` call in `tk_live_finish`. The wrapper reads `pc.sh` to select the module; it does not execute the shell shutdown path or establish execution of `sr.py`. Run5 therefore covers the recorded local copier row, not a byte-identical three-file copier/shutdown path. Its budget phase refused; its checker reports 6/9 PASS, with finite-loss, budget-stop and resume rows NOT PROVED. These CPU stand-ins establish neither a full run5 pass nor production transport/GPU execution.

`EVIDENCE_RECORDS.json` hashes the cited run records. `COVERAGE.json` records the exact copier hashes and coverage checks. Run labels and version comparisons are retained because the task requires identifying the inputs of each execution.
'''
(O/'PROVENANCE.md').write_text(provenance)

derivation='''The table contains a conservative file-level dependency union, derived from all three versions of the code. It includes conditional and function-local imports, so membership does not claim that every branch executed during a rehearsal.

1. The entry chain is `job.sh -> b/pc.sh` for the copier and `b/t.py -> torch.distributed.run -> b/e.sh -> b/u.py` for training. `b/u.py` adds the staged source root and imports `p3_provenance`, `carrier_c1_run`, `r1_persisted`, `launch_r1.entry` and `launch_r1.production_proof`; it calls `verify_staging`, `admit` and `train`.
2. `carrier_c1_run.train` authenticates/prepares inputs, restores state when requested, binds output and calls `run_steps`. `run_steps` calls `optimize_step`, `checkpoint`, `export` and `launch_r2.persistence.milestone`; export also calls `trained_groups.publish`, `r1_training.boundary` and component/source binding helpers. `milestone -> upload` validates native state, builds a tar and writes the local or durable receipt. These imports are traversed rather than selected from names alone.
3. The explicit minimum roots are every `student_pilot/carrier_c1*.py`, every file in `launch_r1/`, `launch_r2/persistence.py`, and the eight requested kit files: `b/pc.sh`, `b/pc.py`, `b/sr.py`, `b/z.py`, `b/u.py`, `b/t.py`, `b/e.sh`, `job.sh`. Those minimums include build/validation code as requested; their dependencies remain in the conservative union.
4. `analyze.py` parses each reached Python module with `ast`, follows `Import` and `ImportFrom` at every nesting level, resolves relative imports and package initializers, and continues until no new local file remains. It resolves kit-local imports, literal dynamic imports and explicit helper filenames. Shell references add the helpers used by the entry/copier path. The generator's `derivgen` search root and the finite parent-launcher module names are handled explicitly. `DEPENDENCIES.json` records each source-to-target edge, source line and reason in each version.
5. A manual review of dynamic import sites checks the finite local modules (`headcall/phase1.py`'s declared source list, `.camera_targets`, `ofs.core`, and `launch_s1.b.{v,q0,i}`); all are in the table. Path-selected external model, scorer, backend and writer modules are outside the tree and are not assigned invented tree hashes. `launch_r2.persistence.upload` loads a pinned external writer only on its durable branch; the rehearsal uses the local-only branch and the copier's explicit local writer. No imported code was executed by this analysis. The dynamic call inventory is preserved in `DEPENDENCIES.json`.
6. The file set is the union across launch, run4 and run5, not merely the launch set. Both runs' `code.json` source closures contain 274 files: every recorded source is present in the table and every digest matches the physical snapshot (`RECORDED_CLOSURE_CHECKS.json`). Complete tree inventories and tar member hashes reproduce the three recorded tree seals; this also ties selected tree rows to the launch archive.

There are 319 tree files and 25 kit files: 344 total, 326 IDENTICAL and 18 DIFFERS. The 319 tree files plus exactly the eight requested kit files contain 327 rows, 320 IDENTICAL and 7 DIFFERS. Following the additional shell/helper references contributes 17 kit rows, including the launch-only exit publisher called by `pc.sh`; these are retained in the main table and clearly use the `kit/` prefix.

`IDENTICAL` requires all three SHA-256 values to exist and agree. `DIFFERS` includes a file missing from either historical manifest; JSON uses null and Markdown uses MISSING. A missing file is not treated as an empty file. Per-version byte locations and closure membership are recorded in `LOOP_HASHES.json`. The GO and non-GO launch kit share all compared executable bytes and the same tree archive.

Each `DIFFS/` document compares launch bytes as the old side and each differing rehearsal as the new side. It reports removed/added lines, changed ranges and affected functions, followed by a unified diff. An absent historical file is shown as removal of the full launch file. Thus the changed-line counts have an explicit direction and do not imply that these edits happened during a rehearsal.

The analysis uses the specified isolated Python interpreter, one process/thread at nice 10, and a 2 GiB address-space limit for hashing and AST analysis. It reads local source files and small run records, never launches a trainer, and writes only inside this folder. The output is below 20 MB.
'''
(O/'DERIVATION.md').write_text(derivation)

diff=[r['file'] for r in table['rows'] if r['status']=='DIFFERS']
tree=[p for p in diff if p.startswith('tree/')];kit=[p for p in diff if p.startswith('kit/')]
report=[
'Compared 344 files: 326 IDENTICAL and 18 DIFFERS; hashes are in LOOP_HASHES.md and LOOP_HASHES.json.',
'The 319 tree files plus the eight requested kit files contain 320 IDENTICAL and 7 DIFFERS; helper traversal adds 17 rows.',
'Run4 passed 8/9 rows; “milestone export / local receipt / kit copier” was NOT PROVED.',
'Run5 covered that local copier row via rehearsal5/target/o/rehearsal/live/gcs_m2.done; its budget phase refused.',
'The copier files are not all byte-identical: pc.py and sr.py match launch; pc.sh adds a launch-only ep.py call in tk_live_finish.',
'Run5 imported pc.py with local stand-ins; it did not exercise the pc.sh shutdown path or prove production transport.',
'Differing tree files: '+', '.join(tree)+'.',
'Differing kit files: '+', '.join(kit[:7])+'.',
'Differing kit files: '+', '.join(kit[7:])+'.',
'PROVENANCE.md identifies recorded paths/seals and authenticates recovered kit bytes; DERIVATION.md explains the closure; DIFFS/ has every diff.'
]
assert len(report)<12
(O/'REPORT.md').write_text('\n'.join(report)+'\n')
print('Wrote REPORT.md:',len(report),'lines; coverage:',json.dumps(copier))
