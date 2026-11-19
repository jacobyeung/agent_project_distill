from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c'
def read(p):return json.loads(p.read_text())
d=read(C/'DELIVERY.json');tests=read(C/'TESTS.json');coverage=read(C/'COVERAGE.json')
deps=read(C/'DEPENDENCIES.json');scan=read(C/'SCAN.json');preview=read(C/'proofs/capacity_preview/RESULT.json')
assert preview['status']=='PASS' and scan['status']=='PASS'
text='''PASS: review 21's naming MUST is fixed and verified. GO remains false; nothing was submitted.

The exclusion payload stages as `k/3119aa4a.json` with the unchanged SHA-256
`3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`.
The sealed `p_sources` map reads it from N's existing content-addressed upload. The sealed
`pin_paths` map lets consumers resolve its original authenticated pin without changing the
exclusion records or scene bindings. Evidence: `work/build21c/STAGING.json`,
`work/build21/proofs/naming21c/TESTS.json` and `work/build21/kits/q/k/p.json`.

Changed files and behavior:

- `work/build21/kit.py`: creates the opaque P-file alias and pinned consumer map, omits build-local
  upload paths from the job map, and emits guarded staging/snapshot/result helpers.
- `work/build21/joblib.py`: authenticates the source-map relationships; checks P-file, export,
  native-link and snapshot names; scans host-supplied directory metadata before staging.
- `work/build21/naming21.py`: scans every JSON map recursively, including nested capsules,
  `p_files` keys, input/link paths, Python path literals and result archive members. It checks
  logical input names through their authenticated hash map while preserving provenance identities.
- `work/build21/jobtest.py`: initializes the explicit fixture maps.
- `work/build21/test21.py` and `portable21c.py`: record test input reads and support byte-preserving
  lookup of bundled prerequisites after extraction.
- `work/build21/naming_test21c.py`: adds the failing-before, name-mutation, map-authentication,
  content-hash and consumer checks. The other `*21c.py` helpers reproduce coverage and delivery checks.
- Generated kit files: `b/z.py`, `b/m.py`, `b/o.py`, new `b/s.py`, `k/p.json`, `BUILD.json` and
  `SHA256SUMS.txt`. `UPLOADS.json`, `FINAL_KITS.json`, `OPERATOR.md` and `PACKAGE_MANIFEST.json`
  describe the final kit. `work/build21c/FIX.diff` and `CHANGES.json` contain the code diff and hashes.

The unchanged base kit fails the expanded scanner with exactly
`INPUT_NAME:k/p.json:p_files:key:k/benchmark_scene_exclusions.json`.
The fixed kit passes. A planted `k/BeNcHmArK.json` entry refuses by name; changed payload bytes
refuse by hash. Relative destination values, map keys, result members, nested maps and runtime
directory metadata have refusal controls. Evidence: `work/build21c/FAILING_BEFORE.json`,
`MUTATIONS.json`, `STAGING.json` and the test records below.

Tests (each count describes the named run; overlapping runs are not added):

'''
for row in tests:
    text+=f"- `{row['name']}`: {row['tests']} tests, {row['failures']} failures, {row['errors']} errors; `{row['source']}`.\n"
text+=f'''
Changed-statement coverage: {coverage['observed']}/{coverage['total']} AST statement heads observed
with standard-library tracing and exact source hashes. Per-statement evidence and uncovered guards
are in `work/build21c/COVERAGE.json`.

The final decoded scan reports PASS across {len(scan['decoded_maps'])} JSON maps and
{scan['checked_strings']} checked strings (`work/build21c/SCAN.json`). The host-only raster map
`k/input_mdg_rasters.json` is not available locally. Its pinned hash and the runtime scanner scope
are recorded in that file; the authenticated metadata reader's name-refusal path passed a fixture test.

The sealed tree did not change. The staging path changed, so capacity staging authentication and
q forward previews were rerun for both milestones. The existing synthetic stores were retained;
the real handover binder authenticated the current source seal before each preview. The RGB/label
fixture, tiny native model and processor boundary remain the CPU stand-ins.
Evidence: `work/build21c/proofs/capacity_preview/RESULT.json`.
'''
for step,row in preview['milestones'].items():
    text+=f"- Milestone {step}: PASS; {row['staged_pins']} authenticated staged pins and {row['records']} finite forward records across ranks 0–3 and all four streams.\n"
text+=f'''
P's trained opener rows, the step-544 lineage path, admission, legality and the DEFERRED boundary
remain unchanged. The tree seal is `{d['tree_seal']}` ({d['tree_files']} files), identical to the base.
Evidence: `out/TREE_SEAL.json`, `work/build21/FINAL_KITS.json` and `work/build21c/START.json`.

Fixture portability:

The complete extra prerequisite set totals {deps['complete_additional_bytes']} bytes, exceeding the
40 MB allowance. The package includes {deps['bytes']} bytes in {len(deps['files'])} smaller prerequisite
files, including the baseline source, build-15/build-N1 inputs and build-16–20/n1fix2 helpers.
`work/build21c/DEPENDENCIES.json` lists the remaining {len(deps['omissions'])} files by path, bytes and
SHA-256. The full focused suite requires those files after unpacking; a standalone full-suite run
from the archive is not claimed. No checkpoint, frame set, database or cache was copied into the package.

Delivery (source for all fields: `work/build21c/DELIVERY.json`):

- Package: `{d['package']}` (gzip).
- Package SHA-256: `{d['sha256']}`.
- Package bytes: {d['bytes']}; verified archive members: {d['members']}.
- Package content seal: `{d['package_seal']}`.
- Kit q seal: `{d['kit_seal']}`.
- Upload inventory: {d['upload_bytes']} bytes in {d['upload_files']} files (`work/build21/UPLOADS.json`).
- Workspace growth: {d['workspace_growth_bytes']} bytes, below the 3 GB limit.
- Base package unchanged: `{d['base']['path']}`; SHA-256 `{d['base']['sha256']}`.
- Completed: {d['timestamp']}.

The archive was streamed back and every member matched the new package manifest. The final package
checksum and this report remain outside the archive to avoid a self-referential checksum.
Production scheduler execution, the full production model and unavailable host inputs were not run.
No SSH, network, GPU, Git, scheduler or additional agents were used.
'''
assert len(text.splitlines())<300
(L/'out/BUILD21C_REPORT.md').write_text(text)
print(text)
