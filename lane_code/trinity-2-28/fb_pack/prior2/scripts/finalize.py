"""Write the review decision and package the overlay with its evidence."""
import json,hashlib,tarfile,io
from pathlib import Path
W=Path(__file__).resolve().parents[1];O=W/'out'
def load(n):return json.loads((O/n).read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p))
tests=load('TESTS.json');census=load('CENSUS_LOADER.json');files=load('FILES_TOUCHED.json');build=load('WEIGHT_BUILD.json')
assert tests['status']=='NO_NEW_FAILURE'
assert load('EVIDENCE_CHECK.json')['status']=='PASS'
rows=[]
b={ (r['clause'],r['difficulty']):r for r in census['first_1000_steps']['base']['answer_shares']}
a={ (r['clause'],r['difficulty']):r for r in census['first_1000_steps']['enabled']['answer_shares']}
for key in b:
 rows.append('| '+' / '.join(key)+f" | {b[key]['draws']:,} | {100*b[key]['back']['share']:.4f}% | {100*a[key]['back']['share']:.4f}% |")
summary=tests['full_cpu'];base=summary['base'];new=summary['new']
text=f'''**NO_GO for N’s first boundary.** The required all-cell production identity proof is MISSING. The patch must wait.

The base seal is `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7` (939 verified files).
The six-file patch applies cleanly; all 941 resulting files match `{files['new_tree_sha256']}`.
`FILES_TOUCHED.json` lists the changes. No file overlaps the other lanes’ declared scopes; their actual patch manifests were not supplied.

Set the optional `r1_training.direction_prior` pin to `TOWARD_HARD_WEIGHTS.json`. Preparation authenticates QIDs, row hashes, clauses, answers and forward relations, then binds native offsets to the card, population and indices.
The sampler alternates front/back within existing toward-hard slots and shuffles each side independently from the card seed. It preserves other positions and refuses insufficient four-draw capacity. Non-VQA streams are outside the prior’s scope.

Weights are `direction`: back `10251/3676`, front `10251/16826`; `facing_pairs`: back `2180/651`, front `2180/3709`.
All 98,315 rows in the prior lane’s pinned filtered extract match original v7 and twin bytes. The weight file records inherited source pins; missing inputs prevent independent filtering.
The loader audit includes facing_pairs and corrects 23,121 clause-parser disagreements. Its production-entrypoint fixture counts both drawn rows; the base counts one.

**Diagnostic scope:** N’s exact seed-17 card and authenticated direction/facing-pair rows, with synthetic support offsets for unavailable cells. This is not a production population or launch configuration.

| Clause / difficulty | Draws | Base back share | Patched back share |
|---|---:|---:|---:|
{chr(10).join(rows)}

The first 1,000 steps are the full schedule. Direction retains 36,866 draws, facing_pairs 18,170, and the card 288,000.
These are realized shares. The prior report’s 67.873% away-hard figure was an expectation; realized away-hard and every other non-target group remain exactly unchanged.
With the field absent, every diagnostic cell matches base byte-for-byte. With it present, only toward-hard rows change; their count and all other positions stay fixed. The maximum repeat is four, resume matches, and tampered weights refuse.
The base ignores both the field and tampered weights. `CENSUS_LOADER.json` records loader counts, sequence hashes, negative controls and input pins.

The guarded CPU runner attempts every existing module and records prohibited operations as errors. Base: {base['tests_run']} tests, {base['failures']} failures, {base['errors']} errors, {base['skips']} skips. New: {new['tests_run']} tests, {new['failures']} failures, {new['errors']} errors, {new['skips']} skips.
Comparison: `{tests['status']}`; {len(tests['regressions'])} worsened existing outcomes. `TESTS.json` includes subtest comparisons and new tests. Existing missing fixtures and restricted operations prevent an all-pass claim.

Missing filter inputs, at their original 1-18 paths (apply the prompt’s mirror map):

- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w17b/work/build17/inputs/s.json`
- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/build18/inputs/u.json`
- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/build21/inputs/u_union.json`
- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w22/work/build22/inputs/naming_remove.json`
- `/scratch/jjyeung/orch_n30/sb_d7bind/BINDING.jsonl`
- `/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json`
- `/scratch/jjyeung/orch_n30/sb_rowA/out/WORDINGS.json`

`MISSING_INPUTS.json` gives all expected paths and pins, including the room-authority input, population/indices and other-stream populations. The production receipt is also MISSING at `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json`.
No production mapping, manifest, scene list or proof was synthesized. The exact card bytes were recovered from the kit capsule and hash-verified.

Commands producing the numbers above, from this workspace:
```bash
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
PY=/scratch/jjyeung/envs/p1cpu/bin/python
nice -n 10 "$PY" scripts/setup.py                 # seal and 939 files
patch --batch -p1 -d work/new -i "$PWD/out/PATCH_PRIOR.patch"
mkdir -p work/recovered
nice -n 10 "$PY" scripts/locate.py                # input availability
nice -n 10 "$PY" scripts/recover_capsules.py      # exact card bytes
nice -n 10 "$PY" scripts/missing_inputs.py        # missing pins and kit comparison
nice -n 10 "$PY" scripts/build_weights.py         # source counts, weights, parser count
nice -n 10 "$PY" scripts/replay.py                # all draw counts, shares and invariants
nice -n 10 "$PY" scripts/cpu_run.py base          # full CPU baseline
nice -n 10 "$PY" scripts/cpu_run.py new           # full CPU patched tree
nice -n 10 "$PY" scripts/make_patch.py             # six-file patch and 941-file verification
nice -n 10 "$PY" scripts/compare_tests.py          # CPU comparison
nice -n 10 "$PY" scripts/verify_evidence.py        # direct input hashes
nice -n 10 "$PY" scripts/finalize.py               # report, archive and SHA256
```
Use fresh output directories for immutable fixtures. After the production checks pass, preparation must bind the weight pin and the orchestrator must reseal the tree and kit before activation. No launch configuration changed here.
`fbp_prior2.tar.sha256` authenticates the archive; `PACKAGE.json` records every member hash.
'''
assert len(text.splitlines())<=80,len(text.splitlines())
(O/'REPORT.md').write_text(text)
(W/'STATUS.md').write_text('The overlay, weights, diagnostic census and CPU comparison are complete and packaged. The six-file patch applies to seal 57a1f14d; diagnostic draws balance toward-hard answers while preserving other positions and the four-draw cap. The production all-cell gate remains MISSING because required filtering and prepared-population inputs are absent. N activation is NO_GO. See out/REPORT.md, out/TESTS.json and out/MISSING_INPUTS.json.\n')
selected={}
def add(p,name=None):
 p=Path(p);selected[name or str(p.relative_to(W))]=p
for name in ('setup.py','locate.py','recover_capsules.py','missing_inputs.py','build_weights.py','replay.py','cpu_guard.py','cpu_run.py','make_patch.py','compare_tests.py','verify_evidence.py','finalize.py'):
 add(W/'scripts'/name)
for n in ['REPORT.md','PATCH_PRIOR.patch','FILES_TOUCHED.json','TESTS.json','CENSUS_LOADER.json','TOWARD_HARD_WEIGHTS.json','WEIGHT_BUILD.json','BASE_SEAL.json','INPUT_LOCATIONS.json','CAPSULE_RECOVERY.json','MISSING_INPUTS.json','EVIDENCE_CHECK.json','CPU_FINAL_base.json','CPU_FINAL_new.json','CPU_FINAL_base.log','CPU_FINAL_new.log','CPU_FINAL_base_driver.log','CPU_FINAL_new_driver.log','REPLAY_final.log','WEIGHT_BUILD_final.log','UNIT_release.log','PATCH_APPLY.log']:add(O/n)
for row in files['files']:add(W/'work/new'/row['path'],'overlay/'+row['path'])
add(W/'STATUS.md');add(W/'work/recovered/card.json')
for p in (W/'work/replay_delivery').glob('*.json'):add(p)
source=Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/fb_pack/prior/out')
for n in ('SOURCE_CENSUS.json','CENSUS.json','DIRECTION_ROWS.tsv.gz','REPORT.md'):add(source/n,'evidence/prior/'+n)
manifest={n:dict(sha256=sha(p),bytes=p.stat().st_size) for n,p in sorted(selected.items())}
record={'schema':'fbp-prior2-overlay-v1','decision':'NO_GO_PRODUCTION_PROOF_MISSING','base_tree_sha256':files['base_tree_sha256'],'new_tree_sha256':files['new_tree_sha256'],'files':manifest,'inputs':[pin(p) for p in selected.values()]}
(O/'PACKAGE.json').write_text(json.dumps(record,indent=2)+'\n');add(O/'PACKAGE.json')
target=O/'fbp_prior2.tar'
with tarfile.open(target,'w') as tar:
 for name,p in sorted(selected.items()):
  info=tarfile.TarInfo(name);info.size=p.stat().st_size;info.mode=0o644;info.mtime=0
  with p.open('rb') as f:tar.addfile(info,f)
with tarfile.open(target) as tar:
 for m in tar:
  h=hashlib.sha256(tar.extractfile(m).read()).hexdigest();assert h==sha(selected[m.name]),m.name
h=sha(target);(O/'fbp_prior2.tar.sha256').write_text(h+'  fbp_prior2.tar\n')
print('Archive',target.stat().st_size,'bytes',h,'report lines',len(text.splitlines()),flush=True)
