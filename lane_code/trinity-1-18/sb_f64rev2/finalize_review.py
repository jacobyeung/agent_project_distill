"""Bind every retained JSON to review inputs and write the bounded final verdict."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
reports={p.stem:json.loads(p.read_text()) for p in OUT.glob('*.json')}
assert 'forward_review' in reports, 'Wait for the full forward before finalizing.'
assert len(reports['forward_review']['records'])==4
assert all(x['finite'] for x in reports['forward_review']['records'])
source={}
for v in reports.values():
    for name,h in v.get('input_sha256',{}).items():
        p=Path(name)
        if not p.is_relative_to(ROOT) or p.suffix in ('.py','.sh','.jsonl'):
            if name in source: assert source[name]==h, name
            source[name]=h
for p in [*ROOT.glob('*.py'),*ROOT.glob('*.sh')]:source[str(p)]=sha(p)
for name in ['behavior_check.py','resume_audit.py','anchor_order_check.py','forward_check.py','regression_check.py']:
    p=ROOT.parent/'sb_f64rev'/name;source[str(p)]=sha(p)
# This manifest binds the source/data graph. Its digest is a direct input of the final annotated fixtures.
manifest=dict(command='bash run_cpu.sh finalize_review.py',input_sha256=source,scope='Read-only review inputs; synthetic artifacts are not production bindings.')
mp=OUT/'INPUTS.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');mh=sha(mp)
# Fixtures are diagnostic outputs, not usable configuration/preparation artifacts. Retain their original payloads.
fixture_inputs={str(mp):mh,str(Path(__file__).resolve()):sha(__file__)}
for folder in [ROOT/'tmp',ROOT/'proofs']:
    for p in list(folder.rglob('*.json')):
        try:v=json.loads(p.read_text())
        except (ValueError,UnicodeError):
            sidecar=dict(command='bash run_cpu.sh finalize_review.py',scope='Intentionally malformed test fixture retained unchanged.',input_sha256={**fixture_inputs,str(p):sha(p)})
            p.with_name(p.name+'.provenance.json').write_text(json.dumps(sidecar,indent=2)+'\n')
            continue
        if not isinstance(v,dict):v=dict(fixture_payload=v)
        v['review_provenance']=dict(command='bash run_cpu.sh finalize_review.py',input_sha256=fixture_inputs,inputs_manifest=str(mp),scope='Synthetic test output; not a production input or proof.')
        if 'input_sha256' not in v:v['input_sha256']=fixture_inputs
        p.write_text(json.dumps(v,indent=1)+'\n')
# Add the immutable graph to report provenance. Resume depends on other reports, so update it last.
for key in [k for k in reports if k!='resume_review']+['resume_review']:
    v=reports[key];provenance=v.setdefault('input_sha256',{})
    provenance[str(mp)]=mh
    for name in list(provenance):
        p=Path(name)
        if p.is_relative_to(ROOT) and p.is_file():provenance[name]=sha(p)
    (OUT/(key+'.json')).write_text(json.dumps(v,indent=2)+'\n')
f=reports['forward_review'];peak=max(r['peak_rss_gib'] for r in f['records'])
lines=[
'# GO AFTER FIXES',
'',
'CPU-side readiness requires the pilot preflight fix below. GPU training and reading remain blocked by real inputs and measurements.',
'Reviewed archive: `da6405ae0f0095414deecf3727a7aa88937686bfcbfa2dcf09e5aa8b1678a4bb`; its kit files, checksums and installed tree patch match (`static_review.json`).',
'',
'1. **CLOSED — store conversion.** Missing pins refuse all four source rows and publish nothing; tests preserve sparse indices, targets and row count. Reversed anchors refuse at converter/reader entry points. The raw `nest_row` helper still sorts; its increasing-anchor precondition is enforced by those callers (`behavior_review.json`, `anchor_order_review.json`, `kit_review.json`).',
'',
'2. **CLOSED — token-audit counterexamples.** Empty, single-row and duplicate-partial shards all give `launch_ready=false`. The complete synthetic audit passes; partial, mixed-run, altered and missing-field cases refuse (`resume_review.json`, `kit_review.json`).',
'',
'3. **OPEN — actual first batches.** Preparation, `r2_sampling`, row-plan/host/review bindings, three stream hashes, code/admission pins and the reader manifest remain MISSING. `static_review.json:missing_inputs` gives exact paths and owners: W, orchestrator, independent reviewer and reader lane. The staged depth-init JSON matches, but its configured in-job path is absent.',
f'   The independent full-depth rerun passes four synthetic pose ranks with finite losses and 9,127 tokens each; peak RSS is {peak:.2f} GiB (`forward_review.json`). It does not establish actual planned-batch readiness.',
'',
'4. **OPEN — GPU evidence and pilot gate.** The pilot uses trainer FSDP FULL_SHARD, FP32 masters, AdamW updates, non-reentrant LM checkpointing, full accumulation and a sharded checkpoint. GPU peaks and timing are unmeasured. Its preflight nevertheless accepts a complete audit with a failed row and omits that row from its longest-row selection (`pilot_review.json`).',
'',
'5. **CLOSED — export helper.** Missing, null, different and invalid nested declarations refuse; matching declarations pass. Reader anchor checks also pass (`kit_review.json`). Filled reader pins remain MISSING under finding 3.',
'',
'6. **CLOSED — anchor evidence and installation.** The 12 layout tests pass; the nine-file tree delta matches the supplied patch, with no scoring/room-rule edits. `src/b/f64_read.py` resolves correctly and the reader config pins its exact bytes (`behavior_review.json`, `static_review.json`).',
'',
'7. **OPEN — baseline completeness.** Each suite runs 109 tests, with zero assertion failures and the same one error: MISSING `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`. The kit does not identify its owner; the orchestrator must route it to the pool producer (`baseline_regression.json`, `patched_regression.json`).',
'',
'8. **OPEN — readiness closure.** The builder must fix the pilot gate and add failure-versus-tripwire tests. Production owners must then bind real inputs, pass actual all-rank CPU first batches and the complete token audit, and obtain the authorized four-rank GPU pilot. Reading also needs its manifest and memory evidence.',
'',
'**Required code fix:** `kit/scripts/mem_pilot.py:68` checks only structural `errors`. Reject any audited `check_row` failure or ceiling violation using complete per-stream counts; allow tripwire-only rows for memory calibration. The injected fixture is explicitly synthetic, and the token summary correctly remains non-ready.',
'**Evidence limits:** 45 kit tests pass, but the pilot API test checks attribute existence, not a training execution. Historical CPU/analytic JSONs lack generating-input hashes; H100 calibration logs and GPU measurements are absent. The claimed 3,733 missing PNGs rely on an unverified reuse count, not supplied filled pins. No launch claim is supported.',
'',
'Commands below ran from `/scratch/jjyeung/orch_n30/sb_f64rev2`; each JSON binds its inputs by SHA256, directly or through `INPUTS.json`.',
'- `bash run_cpu.sh static_check.py` produced archive/patch/pin checks, exact missing paths, staged depth-init verification and reader-plan counts.',
'- `bash run_cpu.sh behavior_check.py` and `bash run_cpu.sh anchor_order_check.py` produced store/export/anchor counterexamples and the 12 layout-test results.',
'- `bash run_cpu.sh kit_check.py` produced the 45-test result; `bash run_cpu.sh regression_check.py baseline` and `bash run_cpu.sh regression_check.py patched` produced both 109-test results.',
'- `bash run_cpu.sh resume_audit.py` reproduced token counterexamples and checked saved evidence; `bash run_cpu.sh forward_check.py` produced full-depth CPU records.',
'- `bash run_cpu.sh pilot_check.py` produced unbound-input refusals and the failed-row pilot counterexample; `bash run_cpu.sh pilot_gate_matrix.py` checked passing, tripwire-only and failed-row controls; `bash run_cpu.sh finalize_review.py` bound retained JSONs and wrote this verdict.',
'',
'The review used CPU only, no network or Git, and wrote only in this workspace. `REVIEW_METHOD.md` documents script adaptations and the scope of the pilot check.'
]
assert len(lines)<=40
(OUT/'REVIEW_VERDICT.md').write_text('\n'.join(lines)+'\n')
(ROOT/'STATUS.md').write_text(f'The review is complete: GO AFTER FIXES for CPU-side readiness. All 45 kit tests pass, both 109-test regressions retain only the missing POOL.jsonl error, and all four full-depth synthetic pose forwards produce finite losses at 9,127 tokens with peak RSS {peak:.2f} GiB. The pilot preflight still accepts failed-row audits and must reject those failures while allowing tripwire-only rows. Real training inputs, filled reader pins and GPU measurements remain MISSING. Evidence and commands are in out/REVIEW_VERDICT.md; every retained JSON carries input provenance.\n')
print(json.dumps(dict(verdict='GO AFTER FIXES',lines=len(lines),peak_rss_gib=peak,records=len(f['records']),input_files=len(source))))
