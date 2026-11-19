"""Package the validated kit, exact source diff and CPU evidence."""
from pathlib import Path
import sys,tarfile,csv,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__)
O=ROOT/'out';W=ROOT/'work'
tests=read_json(O/'TESTS.json');dry=read_json(O/'DRYRUN.json')
code=read_json(O/'CODE_SHA256.json');audit=read_json(O/'FIX4_DIFF.json')
plant=read_json(O/'FIX4_plant.json');plant2=read_json(O/'FIX4_plant2.json')
a0=read_json(O/'fix_validation/a0_rerun_summary.json')
regressions=read_json(O/'FIX3_PROBES.json');stage=read_json(O/'STAGE_TOTALS.json')
assert all(x['status']=='PASS' for x in (tests,dry,audit,plant,plant2,regressions))
assert tests['tests']==68 and tests['errors']==tests['failures']==0
assert code['code_sha256']==dry['code_sha256']==audit['code_sha256']==digest(code_pins())
assert a0['equal']==a0['rows']==1037 and a0['set_equal']==a0['captures']==209
assert a0['subset_1012']['equal']==a0['subset_1012']['rows']==1012
assert a0['subset_1012']['set_equal']==a0['subset_1012']['captures']==204
assert plant2['summary']['planted_files_refused']==30
preserved=read_json(W/'fix4_archive_inputs.json')['input_sha256']
for path,h in preserved.items():assert sha(path)==h,path
sha(O/'STAGE_LIST.tsv')
with (O/'STAGE_LIST.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
seen=set();incremental={}
for part in 'ABCH':
    selected={r['path']:int(r['bytes']) for r in rows if r['bytes'] and part in r['parts'].split(',')}
    incremental[part]=sum(n for p,n in selected.items() if p not in seen)
    seen.update(selected)
write_json(O/'STAGE_INCREMENTAL.json',dict(bytes=incremental,GB={p:v/1e9 for p,v in incremental.items()},command='bash scripts/cpu.sh work/package_fix4.py',schedule='A, B, C, H sequentially on one node'))
def loc(file,needle):
    return file+':'+str(next(i for i,l in enumerate((ROOT/file).read_text().splitlines(),1) if needle in l))
edit1=', '.join(loc('code/evaluate_v2.py',needle) for needle in ('def decision',"path=OUT/'DECISION.json';d=decision(part)","if split=='train':decision('A')","if split=='train':decision('B')"))
edit2=loc('code/process_guard.py',"units=('C32','C64')")
edit4=loc('code/test_kit.py',"root=ROOT/'runtime'/('gain_'")
lines=[
    'The tower-frames kit passes all required CPU checks. No GPU work ran.',
    f"Edit 1: {edit1} refuse planted decisions before scoring and update; test_plant_A_decision_with_B_bars and test_plant_B_decision_train_complete pass with unchanged trees.",
    f"Edit 2: {edit2} checks A/B captures before H freeze; test_plant_H_freeze_after_model_output refuses both late freezes.",
    f"Edit 3: {loc('scripts/gpu_environment.sh','$1+0 > 1024')} compares memory numerically; test_gpu_padded_memory_refuses_either_reading rejects all eight padded busy fixtures, and test_gpu_padded_idle_boundary_passes accepts 1,024 MiB.",
    f"Edit 4: {edit4} freezes a fresh root inside each loop iteration; test_run_b_persists_added_frame_gain passes PASS, FAIL and MISSING cases.",
    f"Regressions: {loc('code/test_fix3.py','def test_plant_A_decision')} adds the plants and valid A-then-B scoring; {loc('code/test_fix3.py','def test_gpu_padded_memory')} adds padded readings.",
    '`bash scripts/cpu.sh code/test_kit.py > out/tests_fix4.log 2>&1`: 68/68 PASS; out/TESTS.json and out/FIX3_PROBES.json record the evidence.',
    '`bash scripts/cpu.sh work/run_fix4_probes.py plant > out/plant_fix4.log 2>&1`: all nine original probes rerun; seven file plants and the forged FREEZE refuse without score writes.',
    '`bash scripts/cpu.sh work/run_fix4_probes.py plant2 > out/plant2_fix4.log 2>&1`: 30/30 required file plants refuse with unchanged trees; the duplicate-row probe refuses; 16/16 real price rows round-trip.',
    'The original synthetic gain comparison and five reviewer-designated informational controls remain diagnostic; both bound B report attacks refuse, and the matching-report control succeeds.',
    'Probe wrappers only redirect result writes into this workspace and record input hashes; out/FIX4_plant.json and out/FIX4_plant2.json retain every result.',
    '`bash scripts/cpu.sh code/dryrun.py > out/dryrun_fix4.log 2>&1`: PASS; 296 captures, 9,472 numbering hashes and 450 camera records.',
    '`bash scripts/cpu.sh work/a0_rerun.py > out/a0_fix4.log 2>&1`: 1,037/1,037 full A0 rows and 209/209 row sets; 1,012/1,012 decision rows and 204/204 row sets match.',
    '`bash scripts/cpu.sh work/diff_fix4.py > out/diff_fix4.log 2>&1`: only code/evaluate_v2.py, code/process_guard.py, scripts/gpu_environment.sh, code/test_kit.py and code/test_fix3.py differ among archived sources.',
    'out/FIX4_SOURCE.diff and out/FIX4_DIFF.json confirm the four trial edits exactly, plus the added tests; configs, inputs, vendor and other delivered scripts are byte-identical to sb_ktfix3.tar.',
    '`bash scripts/cpu.sh work/finalize_fix4.py > out/finalize_fix4.log 2>&1` runs unchanged scripts/finalize_v3.py with only its archive destination redirected to sb_ktfix4.tar.',
    f"New code_sha256 for GPU_GO.json: `{code['code_sha256']}`. out/CODE_SHA256.json, out/DRYRUN.json and out/GPU_NEED.json bind this hash.",
    '`bash scripts/cpu.sh work/refresh_stage.py > out/stage_fix4.log 2>&1` refreshes local staging hashes and reuses verified external hashes.',
    '`bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh scripts/run_H.sh` passes.',
    '`bash scripts/cpu.sh work/package_fix4.py` writes out/sb_ktfix4.tar and out/sb_ktfix4.tar.sha256; out/FIX4_MEMBERS.json pins every payload member.',
    '`bash scripts/cpu.sh work/verify_fix4.py` checks the delivery, replay counts, code pins, member hashes, source diff and both unchanged reviewed archives; `sha256sum -c out/sb_ktfix4.tar.sha256` verifies the archive.',
    'MISSING: /scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json. GPU_GO.json remains an external authorization; no held-out look was consumed.',
]
assert len(lines)<=25
(O/'FIX4_REPORT.md').write_text('\n'.join(lines)+'\n')
(ROOT/'STATUS.md').write_text('The tower-frames kit passes 68 CPU tests, all 30 required reviewer plants, the duplicate-row probe, the dry run and both A0 replay populations (1,037/1,037 and 1,012/1,012). The source diff contains exactly the four requested edits and regressions. out/FIX4_REPORT.md and out/sb_ktfix4.tar deliver the kit; out/sb_ktfix4.tar.sha256 binds the archive. Both reviewed archives remain unchanged. No GPU work ran.\n')
with tarfile.open(O/'sb_ktfix3.tar') as tar:
    names={m.name for m in tar if m.isfile()}
names.discard('out/FIX3_MEMBERS.json')
names.discard('out/FIX3_REPORT.md')
for stage_name in ('tests','dryrun','a0','stage','finalize'):
    names.discard('out/'+stage_name+'_fix3.log')
    names.add('out/'+stage_name+'_fix4.log')
names.update('out/'+n for n in ('FIX4_REPORT.md','FIX4_DIFF.json','FIX4_SOURCE.diff','FIX4_plant.json','FIX4_plant2.json','plant_fix4.log','plant2_fix4.log','diff_fix4.log','validate_fix4.log'))
names.update('work/'+n for n in ('run_fix4_probes.py','finalize_fix4.py','validate_fix4.py','diff_fix4.py','package_fix4.py','verify_fix4.py','fix4_archive_inputs.json'))
names.update(str(p.relative_to(ROOT)) for p in (W/'ktchk2_probes').iterdir() if p.is_file())
names.update(str(p.relative_to(ROOT)) for p in (W/'fix4_expected').rglob('*') if p.is_file())
assert all((ROOT/n).is_file() and not (ROOT/n).is_symlink() for n in names)
member_pins={n:sha(ROOT/n) for n in sorted(names)}
write_json(O/'FIX4_MEMBERS.json',dict(files=member_pins,code_sha256=code['code_sha256']))
names.add('out/FIX4_MEMBERS.json')
archive=O/'sb_ktfix4.tar'
with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as tar:
    for n in sorted(names):
        p=ROOT/n;info=tar.gettarinfo(str(p),arcname=n)
        info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
        with p.open('rb') as f:tar.addfile(info,f)
with tarfile.open(archive) as tar:
    assert len(tar.getnames())==len(names)
    for n,h in member_pins.items():assert hashlib.sha256(tar.extractfile(n).read()).hexdigest()==h,n
h=sha(archive)
(O/'sb_ktfix4.tar.sha256').write_text(h+'  out/sb_ktfix4.tar\n')
write_json(O/'PACKAGE.json',dict(status='PASS',archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(names),report_lines=len(lines),code_sha256=code['code_sha256'],command='bash scripts/cpu.sh work/package_fix4.py'))
print(json.dumps(dict(status='PASS',code_sha256=code['code_sha256'],archive_sha256=h,bytes=archive.stat().st_size,members=len(names),report_lines=len(lines))))
