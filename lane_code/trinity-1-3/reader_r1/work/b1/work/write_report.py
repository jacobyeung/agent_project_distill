from pathlib import Path
import json,hashlib,collections,os
W=Path.cwd();O=W/'out';P=W/'work/p'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={n:(O/n).read_text() for n in ['STATIC_TESTS.txt','STUB_TESTS.txt','REPORT_TESTS.txt','RUNTIME_TESTS.txt','EXISTING_TESTS.txt','REPLAY_RUN.txt','EAT1_SCAN.txt','REHEARSAL.txt']}
text='''B1 CPU validation — INCOMPLETE, NOT READY FOR SUBMISSION

G1 BLOCKED: patched StageOne replay cannot import torch. No patched replay result is claimed.
The replay driver calls StageOne(..., rule=rule), StageOne.select, StageOneSocket and ReadServers;
it contains no replay2.Select wrapper. work/check_replay.py compares every response and query,
checks the 7 remaining pairs, both geometries, accuracy, and diagnostics size against staged evidence.

G2 PARTIAL: four structural/identity checks and six stub-method tests pass. The default null
formula, socket __call__, lift/link/features, box formatter and callhook response bytes remain
unchanged. Planted null-slot, ignored-rule, ignored-settings and printed-format mutants fail
these stub tests. Real Torch tests, b04 fixtures and the complete replay are NOT RUN successfully.

G3 PASS FOR THE CHANGE'S DECISION-PATH STATIC DELTA: 26 findings before and 26 after,
zero new findings by (file, function, rule, detail). No allowlist changes. Whole-file scan logs
include setup/output-only findings, documented in EAT1_GATE.json. This is not a whole-reader
EAT-1 certification; inherited findings remain.

CPU first batch / full H1-0 empty-root restore: NOT RUN. Model, SAM 3, RGB, restored environment,
bwrap and policy archives are referenced by input manifests but absent from W. Local package
integrity and namespace-source construction rehearsal passes for both packages. No 2.json
submission receipt was generated. Retokened policy/environment inputs require restaging.

CPU limits: CUDA hidden in replay command; OMP/MKL/OpenBLAS threads 1; prepared replay NP=8.
No network, Git, SSH, job submission or process kill was used.

'''
for n,v in checks.items():text+='\n===== '+n+' =====\n'+v
(O/'TESTS.txt').write_text(text)
E=[json.loads(l) for l in (W/'in/replay/replay_out2.jsonl').read_text().splitlines()]
table=[]
for geo in ('tower','hybrid'):
 for rule in ('null_argmax','candidates_argmax'):
  rs=[r for r in E if r['geo']==geo and r['rule']==rule and 'error' not in r]
  count=sum(s.strip().endswith(': not seen') for r in rs for s in r['ground'].values())
  reads=sum(any(s.strip().endswith(': not seen') for s in r['ground'].values()) for r in rs)
  table.append(f'| {geo} | {rule} | {len(rs)} | {count} | {reads} | Not run: torch missing |')
packages=[]
for token in ('c4d7e0a91b28f','d8a2f6c09e137'):
 cfg=json.loads((O/token/'CONFIG.json').read_text())
 packages.append(dict(token=token,manifest_sha256=sha(O/token/'PACKAGE.json'),**{k:v for k,v in cfg.items() if k!='token'}))
(O/'PACKAGES.json').write_text(json.dumps(packages,indent=2)+'\n')
hashes=json.loads((O/'FILE_HASHES.json').read_text())
report='''B1 implements candidate-only selector decoding, per-call diagnostics, and optional own-depth snapshots. Both package variants build, but **the delivery is not ready for submission**: G1 and the runtime portion of G2 lack a Python environment with Torch, pytest and safetensors. The full restore also lacks its large dependency archives.

The patched payload is `work/p`. Inputs under `in/` remain read-only. `PATCH.diff` applies relative to the payload root. `h1eval/reader_core`, the selector weights, all candidate producers, and the formatter remain unchanged.

The reader accepts `stage1_select_rule` in read settings. `null_argmax` is the default. `candidates_argmax` takes the argmax of the first N head slots, with PyTorch's first-index tie rule; an empty socket returns no candidate without evaluating the head. The rule is explicit in the environment binding and runner IDENTITY, and the package plan pins it. The identity test refuses a rule change before launching a worker.

Each valid box-ground call carries its own `stage1` object through `CallHook.report()` into the output record. It includes 32 retained-proposal counts, retained maxima, lift entries, lifted proposals, `lift_reasons` from the producer's outcome list, linked-candidate count, and up to 30 candidate IDs, frame lists, peaks, logits and float32 feature lists. It also records the null logit, chosen index and whether null won the unrestricted argmax. On empty candidates the head is not evaluated: `null_logit` and `null_would_win` are JSON null. Gap records carry operand states and their last selection counts. The diagnostic cap changes only the record; selection still considers every candidate.

`save_own_depth` defaults to true and is part of the read binding. After generation, the launcher saves float16 own depth with pose9, gravity, grid coordinates, camera matrices and anchor indices under the shard's `own_depth/`. The read output carries its relative path and SHA256. Grounding reuses its existing own grid; a read without a ground call queries that grid after generation. The saved arrays do not feed any response. Setting the flag false skips the snapshot. The retained geometry uses full precision in the reader.

G1: **BLOCKED**. `work/replay/replay_patched.py` uses the patched StageOne with its rule, through the real socket and formatter. `work/check_replay.py` is prepared to compare ground text, gap text, query choices, errors, diagnostic size and accuracy. The command stops at `ModuleNotFoundError: torch`. The following columns are staged evidence, not new measurements:

| Geometry | Rule | Evidence reads | Evidence not-seen pairs | Evidence not-seen reads | Patched result |
|---|---|---:|---:|---:|---|
'''+ '\n'.join(table)+'''

| Geometry | Record clean program MRA | Record rescued program MRA | Patched result |
|---|---:|---:|---|
| hybrid | 0.500 | 0.496 | Not run |
| tower | 0.646 | 0.534 | Not run |

The evidence has 600 runs, with eight missing-geometry errors for two items, and 294 covered pairs on 148 successful reads per variant. The replay driver preserves those jobs, so the checker will report mismatches rather than remove failed items. The 7-pair and 7/148-read claims remain unverified for this patch. Cached SAM proposals and hybrid G3T depth are proxies; they do not prove own-depth GPU behavior.

G2: **PARTIAL**. Four structural/identity checks and six stub-method checks pass. The null rule uses the same full-slot `torch.argmax` and `-1` mapping as H1-0. The socket's decision method and all lifting, linking, feature production, boxes and printed response functions are byte- or AST-identical. Diagnostics add observations and never feed the choice or formatter. The tests compare the patched and original selection methods on 69 synthetic slot arrays, cover ties and empty candidates, and reject off-by-one, ignored-rule, ignored-settings and printed-format mutants. These are stub tests, not real Torch or b04 fixture parity. `work/test_b1.py` contains the pending runtime, JSON-size, report-survival and depth round-trip checks.

The b04 suites cannot start because pytest is unavailable. The staged tar also omits its tokenizer, K1 tower/cache fixtures, trained scale/selector data and proof geometry. `work/run_existing.py` redirects absolute fixture references into W and supports baseline and patched runs. The package headcall/ground suites still need their dependencies and external fixtures; they have not been claimed as passed. No CPU first batch has run.

G3: **PASS for the scoped static delta**. The EAT-1 scanner reports 26 findings before and 26 after in changed decision-path files, with no new semantic finding. The before/after whole-file scans report 199 and 190 findings. A text-based comparison also notices the unchanged 0.3 floor on a renamed assignment. Other new raw findings are build-time inventory reads and post-generation snapshot naming/hashing. `EAT1_GATE.json` states the scope, exclusions and comparison key; `EAT1_before.json`, `EAT1_after.json` and `EAT1_new.json` preserve raw evidence. No allowlist was modified. The selector rule adds no fitted constant, threshold, alias table or decision-path file read. Existing reader findings prevent a whole-reader EAT-1 PASS claim.

`b1_report.py` accepts the two returned items files, an item manifest, and optional `--pairs-cache`. It reports call stages, capped/not-seen reads, task MRA, paired room bootstrap intervals (10,000 draws; seed 20261115), metre-only results, each gap's metre error, and name/dataset tables. It prints the pre-registered predictions beside observations and reports missing diagnostics. Its fixture passes. A compatibility check using the staged H1-0 return as both inputs gives 150 reads, task MRA 0.200, 43 metre items, metre MRA 0.297674, 63 not-seen reads and 33 capped reads; its paired difference is zero. `REPORT_BASELINE_SELFCHECK.json` is a self-check, not a candidates-rule result.

Both kits select `object_abs_distance`, arm `own`, mode `none`, and the 150 baseline items. The code archives preserve the complete staged inventory, including nested selector input modules. They build through `orchard_h10/build.py`. The local empty-root rehearsal checks every payload pin, creates the package's bind-source directories, validates descriptors, and checks exact worker arguments. Its log is `REHEARSAL.txt`. It does not execute bwrap, restore, SAM or a language model and is not equivalent to the full H1-0 rehearsal.

The input descriptors retain original archive pins. **Policy input restaging is required:** the inherited `q/policy.json` attests script paths under the original token, so replacing the token in the descriptor alone cannot satisfy the unchanged policy-receipt check. The orchestrator must verify and reissue that receipt for each new namespace and authenticate the replacement archive. It must also verify environment wrappers after relocation. These checks must precede a real CPU restore and the package's operator `check`. No submission receipt has been minted here.

Package pins:

'''
for p in packages:
 report+=f"- `{p['token']}`: PACKAGE.json SHA256 `{p['manifest_sha256']}`; payload SHA256 `{p['payload_sha256']}`; plan `{p['plan_sha256']}`.\n"
report+='''
After the runtime gates, fresh input receipts, complete restore rehearsal, and cross-family review pass, the orchestrator can stage each directory under `/project/community/jjyeung/<token>` and run these exact commands on Orchard. They were not executed:

```bash
cd /project/community/jjyeung/c4d7e0a91b28f
/usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 01:45:00
/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 01:45:00
cd /project/community/jjyeung/d8a2f6c09e137
/usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 01:45:00
/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 01:45:00
```

The job names are `a15_cot_apc4d7e0a91b28f` and `a15_cot_apd8a2f6c09e137`. The estimate is about 2.5 H100-hours total (300 reads at about 25 seconds plus loading); the two suggested walltime reservations total 3.5 GPU-hours. No dollar rate was supplied or fetched.

The orchestrator should obtain one cross-family review before submission, as B1 requests. The review should check selector-slot indexing, settings propagation, metadata isolation, snapshot timing, resume refusal, the narrowed read plan, and retokened inputs. Admission and legality logic are unchanged; the read selects a different route rule. `REVIEW_REQUEST.md` records the request.

File hashes (before → after):

'''
for row in hashes:report+=f"- `{row['file']}`: `{row['before'] or 'new file'}` → `{row['after']}`.\n"
size=0
for root,ds,fs in os.walk(W,followlinks=False):
 for f in fs:
  p=Path(root)/f
  if not p.is_symlink():size+=p.stat().st_size
report+=f'''\nThe workdir uses approximately {size/1e9:.3f} GB of regular-file logical bytes, below 5 GB. No deletion was performed. Temporary paths are listed in `REMOVAL_CANDIDATES.md`. All generated files are inside W; one mistyped log-redirection attempt outside W was refused by the filesystem and wrote nothing.\n\nThe report uses the no-archaeology and summary writing rules. The before/after comparisons above are retained because they are required compatibility evidence, not project history.\n'''
(O/'REPORT.md').write_text(report)
(O/'REVIEW_REQUEST.md').write_text('''The orchestrator is asked to arrange one cross-family review before submission. B1 changes a read routing rule and adds diagnostics; admission and legality rules remain unchanged. Review PATCH.diff and TESTS.txt, verify candidate-slot argmax and ties, default-response parity, settings and resume identity, diagnostic isolation, snapshot persistence, both 150-read plans, and the retokened input receipts. G1 and runtime G2 are currently blocked by missing Python dependencies; full restore inputs are absent. Do not approve submission on the stub tests alone.\n''')
(O/'REMOVAL_CANDIDATES.md').write_text('''No files were deleted. The user may remove these temporary directories after retaining the final deliverables and completing runtime validation:\n\n- `work/rehearsal/`: an intermediate integrity rehearsal.\n- `work/rehearsal_final/`: extracted final packages and placeholder bind-source directories.\n- `work/reader_repin/`: the complete explicit reader-repin inventory.\n- `work/report_fixture/`, `work/static_resume/`, `work/existing_tests/`: local test artifacts.\n\nRetain `work/p`, `work/replay`, the test/check scripts and `in/` until runtime validation is complete. No deletion command is queued outside W because this task permits writes only inside W.\n''')
print('W bytes',size,'packages',packages)
