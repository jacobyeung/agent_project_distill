"""Assemble exact test receipts and hash the completed kit delivery."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
checks=json.loads((OUT/'evidence/round5_checks.json').read_text())
assert len(checks)==13 and all(c['accepted'] for c in checks)
stamp=subprocess.check_output(['date','-u'],text=True).strip()
prefix="nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \\\n  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \\\n  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "
text='''## Exact local commands and outputs

**Measured test outcomes:** all **50 local kit cases passed**, including all
**13 round-5 cases**. The complete dedicated set has **92 cases: 91 passes and
one skip**. The two broad suites reproduce the eight named baseline failure
entries below. They are not clean passes, and the runner does not conceal them.

The runner executes suites serially, sets the four switches OFF, pins
`SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1`,
limits execution to cores 0–7, and sets eight torch threads before CPU work.
Only socket-required cases are excluded. Each linked log records its full command,
complete stdout/stderr and exit status; the table quotes its exact summary.

```bash
cd /scratch/jjyeung/orch_n30/so_step
date -u
'''+prefix+'''work/run_round5_checks.py
```

| Suite | Exact summary | Complete command and output |
|---|---|---|
'''
for c in checks:
    summary='; '.join(c['summary'])+'; EXIT='+str(c['exit'])
    text+=f"| {c['kind']} | `{summary}` | [{c['log']}](evidence/{c['log']}) |\n"
text+='''
The [runner output](evidence/round5_run.txt) ends with
`ROUND5_LOCAL_GATES_PASS_WITH_EIGHT_DECLARED_BASELINE_FAILURES`, `EXIT=0`.

The before/after regression uses the same test file and CPU environment. This
command deliberately selects the snapshot and exits nonzero:

```bash
date -u
SO_KIT_BUNDLE=/scratch/jjyeung/orch_n30/so_step/out_round5 \\
'''+prefix+'''work/test_round5_kits.py
```

'''
before=(OUT/'evidence/round5_before.txt').read_text()
summary=re.findall(r'^(?:Ran .*|FAILED.*|EXIT=.*)$',before,re.M)
text+='[Exact snapshot output](evidence/round5_before.txt): `'+'; '.join(summary)+'`.\n'
text+='''The errors include actual grid and replay refusals plus missing new helper
imports; the CLI failures show that the continuation executable is absent.
The wrong-manifest test catches processor construction before pin validation.
The two unchanged refusal controls are not claimed as defects.

Reproduce the simulation and integrity checks with:

```bash
date -u
'''+prefix+'''work/simulate_round5.py
date -u
'''+prefix+'''work/verify_round5.py
```

The [simulation output](evidence/round5_simulation.json) contains exact counts for
all five 100,000-trial scenarios. The [integrity output](evidence/round5_integrity.txt)
records `ROUND5_PATCH_REPLAY_PASS: 4 patches; 22 touched files; zero fuzz/offsets; both patch folders unchanged`,
`KIT_PYTHON_SYNTAX_PASS`, and `SNAPSHOT_HASHES_PASS: 154 out/ files match their input inventory; external work references excluded`,
with `EXIT=0`. The snapshot inventory also references work files outside `out/`;
those references are not part of the requested output snapshot.

'''
p=OUT/'REPORT.md';report=p.read_text()
a=report.index('## Exact local commands and outputs')
b=report.index('## Coordinator command')
report=report[:a]+text+report[b:]
report=report.replace('evidence/round4_integrity.txt','evidence/round5_integrity.txt').replace('ROUND4_PATCH_REPLAY_PASS','ROUND5_PATCH_REPLAY_PASS')
report=report.replace('evidence/round4_existing.txt','evidence/round5_existing.txt').replace('evidence/round4_related.txt','evidence/round5_related.txt')
report=report.replace('No production GPU run or speedup measurement was performed.',
    'All 50 local kit tests passed. The complete dedicated set passed 91 cases with\none skip; broader suites reproduce eight known baseline failure entries.\nNo production GPU run or speedup measurement was performed.')
manifest=json.loads((OUT/'patches_b21/manifest.json').read_text())
patch_table='''The four handed-over patch hashes are unchanged:

| Patch | SHA256 |
|---|---|
'''
for name,pin in manifest.items():
    if name.endswith('.diff'):
        patch_table+=f"| [{name}](patches_b21/{name}) | `{pin['sha256']}` |\n"
report=report.replace('## Kit acceptance and numeric continuation rules',patch_table+'\n## Kit acceptance and numeric continuation rules')
p.write_text(report)
p=OUT/'NOTE_FOR_TREE_REBUILD.md';note=p.read_text()
note+='''
Validation: all 50 local kit cases pass, including 13 round-5 regressions.
The complete dedicated set has 91 passes and one skip; the broad suites reproduce
eight known baseline failure entries. REPORT and `evidence/round5_*` contain exact
commands and outputs. The snapshot regression fails on each requested defect;
trainer patches and their 22 output pins remain unchanged. No production audit
or GPU replay was run by this dispatch.
'''
p.write_text(note)
size=int(subprocess.check_output(['du','-sb',str(ROOT)],text=True).split()[0])
assert size < 3_000_000_000
(OUT/'REPORT.md').write_text(report+f'\nWorkspace size measured at {stamp}: **{size:,} bytes**, below 3 GB,\nbefore final inventory writes. Started 14:37:23 UTC; deadline 15:37:23 UTC.\n')
(ROOT/'work/STATUS.md').write_text(f'''Updated {stamp}. Started 14:37:23 UTC; deadline 15:37:23 UTC.

VERDICT: DONE. All five round-5 kit/documentation findings are fixed. out_round5 preserves the input out directory. The four handed-over trainer patches and manifests remain byte-identical. Scoped zero-fuzz replay matches all 22 output pins; 154 snapshot out files match their inventory. No trainer source was edited.

All 50 local kit tests passed, including 13 round-5 regressions. The dedicated set totals 92 cases: 91 pass and one skip. The two broader suites reproduce the same eight baseline failure entries, with no new failures. The snapshot run has 13 cases and intentionally fails (6 failure entries, 11 error entries including subtests). Exact outputs and commands are in out/evidence/round5_* and REPORT.

The audit accepts 576 spatial patches with t<=32, the sidecar shares that cap, and the processor manifest must match the trainer model pin. Replay and continuation both pool D and M over four ranks with multiplier 2. The read-only continuation command checks update 1 immediately and the wall rule after update 21. The NOTE contains exact commands and simulation false-refusal rates (100,000 trials per scenario); at one scalar per rank the delivered rule refuses 80.305% and pooling refuses 13.018% under the stated simulated Gaussian noise.

Decision: all four ranks individually exceeding their local bounds cannot pass the pooled maximum bound. The regression tests each rank outside its local bound in turn, with another rank supplying larger spread; an all-fail control refuses. The report states the proof. The continuation core plus validation/CLI uses about 80 lines to refuse invalid or incomplete records.

Production CPU audit, torchvision coverage, GPU replay and speed measurements remain host admission work and were not run. The unchanged trainer's coordinator proof is 31 tests OK in 880.158s at 12:55:19 UTC. No Git, SSH, GPU, paid API, deletion or external job was used. Workspace size before final inventory writes: {size} bytes.
''')
meta=json.loads((ROOT/'out_round5/ARTIFACTS.json').read_text())
work_files={name for name in meta['artifacts'] if name.startswith('../work/')}
work_files.update('../work/'+name for name in ('test_round5_kits.py','simulate_round5.py','run_round5_checks.py',
    'verify_round5.py','update_round5_docs.py','finalize_round5.py'))
files=sorted([p for p in OUT.rglob('*') if p.is_file() and p.name!='ARTIFACTS.json'])
artifacts={}
for p in files+[OUT/name for name in sorted(work_files)]:
    relative=str(p.relative_to(OUT))
    raw=p.read_bytes()
    artifacts[relative]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
meta.update(verified_utc=stamp,review_round=5,verdict='DONE',snapshot='out_round5',
    trainer_patches_changed=False,local_dedicated_cases=92,local_passes=91,local_skips=1,
    local_kit_cases=50,round5_regression_cases=13,baseline_failure_entries=8,
    workspace_bytes=size,artifacts=artifacts)
(OUT/'ARTIFACTS.json').write_text(json.dumps(meta,indent=2)+'\n')
for relative,pin in artifacts.items():
    assert hashlib.sha256((OUT/relative).read_bytes()).hexdigest()==pin['sha256'],relative
for folder in ('patches','patches_b21'):
    for p in (OUT/folder).iterdir():
        assert p.read_bytes()==(ROOT/'out_round5'/folder/p.name).read_bytes(),p
for folder in ('kit_timing','kit_profile'):
    for p in (OUT/folder).glob('*.py'):
        ast.parse(p.read_text(),filename=str(p))
for filename in ('REPORT.md','NOTE_FOR_TREE_REBUILD.md'):
    value=(OUT/filename).read_text()
    assert value.startswith('VERDICT: DONE') and 'Review round 5: finding -> fix -> test' in value
    assert 'h*w <= 520' not in value and 'eight extra config lines' not in value
print(stamp)
print(f'ROUND5_FINAL: {len(artifacts)} hashes verified; 50 kit tests pass; 92 dedicated cases (91 pass, 1 skip); 8 unchanged baseline failure entries')
print('TRAINER_PATCHES_BYTE_IDENTICAL; REPORT_AND_NOTE_COMPLETE; WORKSPACE_BYTES='+str(size))
