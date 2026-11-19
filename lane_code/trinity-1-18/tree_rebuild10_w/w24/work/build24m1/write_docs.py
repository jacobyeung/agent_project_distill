from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24m1'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
kits=J.load(D/'KIT.json');up=J.load(L/'out/UPLOADS_24M1.json');e=J.load(D/'RETAINED_EVIDENCE.json')
path=L/'out/N_CARD_KIT_ROWS.md';old=L/'attic/build24m1/out/N_CARD_KIT_ROWS.md';old.parent.mkdir(parents=True,exist_ok=True)
s=path.read_text();path.rename(old)
s=s.replace(' Exactly the three Option T files differ from tree 57a1f14d; 937 files remain identical.','')
for name,oldseal in [('q','6215397d48349983ef30c5b7492618d570f4586d0c85f9d101e00c7bb96669c3'),('n','814db98aabae2859b8be5bc8e509cc8fd43bd9baa32c11ec293176f155b116f8'),('n_go','05f0ffa1c8467c46c61f958ad239e9aef393bc3e6e293a55202c507ec84fbd76')]:s=s.replace(oldseal,kits[name]['kit_seal'])
s=s.replace('UPLOADS_24K.json','UPLOADS_24M1.json')
s=s.replace('Mode r stages the same inputs, runs the native routing builder and P regeneration/equality recipe, and publishes routing_selection.json to <n_root>/o/<jobid>/. Production stores are available only on Orchard.', 'Mode r writes routing_selection.json inside the job root. After bwrap exits, the batch shell publishes it, filtered q.log, refusal r0.json when present, and status r1.json to <n_root>/o/<jobid>/; the combined cap is under 5 MB and the workload exit code is preserved. P regeneration refreshes its saved selection with equality checks.')
s=s.replace('Frames, indices and timestamps are omitted;', 'The recursive sample filter removes frame, frames, frame_index, frame_indices, frame_id, timestamp, timestamps and every *_frame* key;')
s=s.replace('The retained fixture scanned 79,971 rows in 53.7 seconds, produced 964,322 bytes, and found zero protected-room rows.',f"The retained fixture scanned 79,971 rows in {e['elapsed_seconds']:.1f} seconds, produced {e['evidence_bytes']:,} bytes, and found zero protected-room rows.")
s=s.replace('and has not been run.','and is not run by this build.')
s+='All kit job.sh and b/*.sh files are mode 0755. Upload manifests include permission-only replacements; preserve those modes when extracting the stream.\n'
path.write_text(s)
assert len(s.splitlines())<40
notes='''The mode-r audit follows jr.sh, v.py, x.py, z.bootstrap, the decoded job shell, a.py r and rg.regenerate.

The most likely early failure is R1_BINARY_MISSING:bwrap. k/l.json pins /project/community/jjyeung/cp4tk_rt/kit/bwrap, but tk_env's PATH contained only the provenance directory, venv, /usr/local/bin, /usr/bin and /bin. The actual host may also have installed bwrap, so this remains an inference without job 173349's q.log. Decoded kit_n_go/k/j.json:393 adds the pinned binary's directory. FAILURE_TESTS.json reproduces refusal with the original PATH shape and passes with the directory supplied.

The definite publication defect was the write to <n_root>/o/<job>/ inside a.py r. That destination is read-only in the view. b/a.py:16 installs a local refusal writer; b/rg.py writes the selection under the job root. Decoded k/j.json:408 calls b/rd.py after the pipeline and outside bwrap. b/rd.py:24 copies q.log first, then r0.json and routing_selection.json, and writes r1.json. The limits are 2,000,000, 500,000 and 2,000,000 bytes respectively, plus a small status record. It preserves nonzero workload status and fails a successful workload if publication fails. No binary payload is published.

P's saved pool selection has a different implementation map from the sealed producer; P_RECIPE_AUDIT.json records both digests. b/rg.py:36 calls the existing checked refresh before P's native regeneration. That refresh authenticates inputs and requires normalized equality for every selection field except implementation. The exact selected-row byte/order comparison remains mandatory. Unit tests cover refresh ordering and unequal rows; production equality still needs Orchard stores.

P's config pin is present in the selected small archive; its absence from the upload list alone is not a defect. b/pl.py:108 now explicitly authenticates that config before reading the materialization. b/pl.py:114 includes P's removals and exclusions, alongside materialization inputs, legacy database, division, base model and catalog. No identity check or pin is weakened.

SLURM_JOB_ID must contain ASCII digits; valid job 173349 satisfies it. The check now runs before expensive work, and failures publish a filtered refusal. The job_tmp and temporary_paths checks remain native and unchanged; the real mode-r fixture passes both. All three rg.py SQLite input connections retain mode=ro with uri=True; native output databases live below the writable job root. k/h.json still requires python3, bash and bwrap. The CPU mode skips the GPU guard. The caller resolves request and kit arguments before cd; jr.sh is unchanged.

kit_n_go/b/rv.py:100 recursively removes the requested frame and timestamp keys, including every key containing _frame. Samples retain their identifiers, text, order and count. Kit n shares this helper. Kit q has no reviewer-sample helper; it receives the routing, staging, publication and executable-mode fixes.

The sealed tree, all configuration capsules, admission/legality/removals, opener rows, step-544 lineage, resolver identity checks and DEFERRED boundary remain unchanged. INVARIANTS.json records the exact protected files and seals.

Operational exception: a test-only hardlink transport truncated 61 retained upload files; RESTORED_INPUTS.json records their restoration from immutable packages and the final audit verifies every uploaded input hash. A later fixture-directory copy exceeded the 200 MB transient growth cap before the test was interrupted. Identical generated copies now reference retained inodes; partial output is retained losslessly. Final retained growth is reported separately. The run did not satisfy the transient disk constraint.
'''
(D/'MODE_R_AUDIT.md').write_text(notes)
report=[
'GUESS: 173349 most likely refused R1_BINARY_MISSING:bwrap because the pinned binary was outside PATH; fixed, but unproven without its node-local q.log.',
'The definite read-only publication defect is fixed: a.py keeps mode-r outputs under the job root; decoded kit_n_go/k/j.json:408 publishes after bwrap via b/rd.py:11.',
'b/a.py:16 writes filtered r0.json; b/rd.py:24 publishes q.log, r0.json, routing_selection.json and r1.json under 5 MB, including failures. Exit codes 1 and 7 survive.',
'Decoded k/j.json:393 exposes the authenticated bwrap directory. The native runtime check fails before this PATH fix and passes after it.',
'b/rg.py:36 refreshes P’s stale pool selection through the existing equality-checked helper; exact P row-byte/order comparison stays mandatory. P_RECIPE_AUDIT.json and P_REFRESH_TESTS.json cover this.',
'b/pl.py:108 explicitly authenticates P’s config; :114 stages P’s removals/exclusions with the materialization inputs. The config pin already belongs to the selected archive.',
'SLURM ID, job_tmp confinement, read-only SQLite inputs, binaries and the full call path are audited in work/build24m1/MODE_R_AUDIT.md.',
'kit_n_go/b/rv.py:100 strips every requested key recursively. All 160 retained samples keep identifiers/text/counts; FRAME_TESTS.json records the four streams.',
f"The native evidence pass scans {e['total_rows']:,} admitted rows in {e['elapsed_seconds']:.1f} s and publishes {e['evidence_bytes']:,} bytes; counts and protected-room policy pass.",
'All job.sh and b/*.sh files in q, n and the GO template are 0755. The upload delta includes ten permission-only replacements.',
'Mode r passes with /project read-only except live and publishes outside bwrap. Its 16,001-row native digest matches the retained result; selection acceptance and mutation tests pass.',
'Decoded scans, kit/naming/resolver/guard/live suites, 30 review-wait cases, eight security cases, failure publication and P refresh tests pass; see VALIDATION.json.',
'Both final hidden-path runs pass staging, verification, guard, room audit and publication, then stop at the unavailable production database; SEQUENCE.json records the boundary.',
'Tree 189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710 and all protected config/resolver bytes remain unchanged; all 11 existing packages verify.',
f"Kit q {kits['q']['kit_seal']}; kit n {kits['n']['kit_seal']}.",
f"GO template {kits['n_go']['kit_seal']}; q/n GO remain false. The GO delta is separate and is not uploaded.",
f"UPLOADS_24M1.json/.list contains {up['total_files']} files, {up['total_bytes']} bytes; stream root is {up['stream_root']}. jr.sh is unchanged.",
'The test transport damaged 61 retained upload inputs; all were restored exactly from unchanged packages and verified. A fixture copy exceeded the transient 200 MB cap; this constraint was not met.',
'Final retained growth and lossless references are recorded in work/build24m1/STORAGE.json. No production store, routing approval, independent review, upload or launch is claimed.',
'Package path, seal and archive SHA256 are in out/DELIVERY_24M1.json. Production admission remains blocked pending the reviewed routing pin and prepared-config review.'
]
(L/'out/BUILD24M1_REPORT.md').write_text('\n'.join(report)+'\n');assert len(report)<25
print('card',len(s.splitlines()),'report',len(report),'lines')
