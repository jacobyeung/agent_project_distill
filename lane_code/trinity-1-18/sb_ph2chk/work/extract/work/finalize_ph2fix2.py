"""Validate completed CPU evidence and refresh production preflight without launching."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];KIT=ROOT/'sb_mask_phrase';OUT=ROOT/'out'
sys.path.insert(0,str(KIT/'part2'))
import launch_gpu as L

def main():
    tests=[('part1',KIT/'out/TESTS.json',26,'final_part1.log','test_kit.py'),
           ('part2',KIT/'out/part2/TESTS_PART2.json',26,'final_part2.log','part2/test_part2.py'),
           ('launcher',OUT/'LAUNCHER_TESTS.json',25,'launcher_tests.log','part2/test_launcher.py')]
    paths=[Path(__file__),ROOT/'verify_cpu.py'];runs=[]
    for name,p,count,log,script in tests:
        d=json.loads(p.read_text());assert d['ran']==count and (d.get('passed') or d.get('status')=='PASS')
        text=(OUT/log).read_text();assert re.search(r'Ran '+str(count)+r' tests? in ',text) and '\nOK\n' in text
        runs.append(dict(name=name,tests=count,status='PASS',command=['bash','sb_mask_phrase/run.sh',script],log=str(OUT/log)))
        paths.extend([p,OUT/log])
    for name,p,cmd in [
        ('dryrun',KIT/'out/DRYRUN.json',['dryrun.py','report']),
        ('fixture',KIT/'work/part2_cpu_ph2fix2_verified/FIXTURE.json',['part2/price.py','fixture','arkitscenes/41048124,scannetpp/067e2e4e61'])]:
        d=json.loads(p.read_text());assert d['status']=='PASS';paths.append(p)
        runs.append(dict(name=name,status='PASS',command=['bash','sb_mask_phrase/run.sh',*cmd],environment={'PART2_FIXTURE_DIR':'work/part2_cpu_ph2fix2_verified'} if name=='fixture' else {}))
    p=KIT/'work/part2_aggregate_ph2fix2_verified/aggregate/DECISION_PART2.json';d=json.loads(p.read_text());paths.append(p)
    assert (d['rows'],d['captures'],d['both_good_rows'])==(1012,204,442)
    assert (d['rows_1037'],d['captures_1037'],d['both_good_rows_1037'])==(1037,209,456)
    gain=d['arms']['W_exact']['gain'];assert round(gain['estimate'],2)==3.82 and [round(x,2) for x in gain['ci95']]==[2.16,5.63]
    runs.append(dict(name='aggregate',status='PASS',command=['bash','sb_mask_phrase/run.sh','part2/price.py','fixture-aggregate'],environment={'PART2_FIXTURE_DIR':'work/part2_aggregate_ph2fix2_verified'},population=[1012,204,442],W1_gain=gain))
    step5=OUT/'final_step5_cpu.log';assert 'part 2 needs CUDA' in step5.read_text();paths.append(step5)
    runs.append(dict(name='step5_cpu',status='EXPECTED_REFUSAL',command=['bash','sb_mask_phrase/run.sh','part2/sam3_pass.py','step5'],environment={'PART2_GO':'1'}))
    assert not (KIT/'out/pool_part2/STEP5.json').exists()
    for name in ('GUARD_PH2FIX2.json','GPU_ESTIMATE_PH2FIX2.json','STRACE_PH2FIX2.json','STAGING_PART2.json'):
        p=OUT/name;paths.append(p);d=json.loads(p.read_text())
        if name in ('GUARD_PH2FIX2.json','STAGING_PART2.json'): assert d['status']=='PASS'
    pins=L.preflight(KIT);assert L.admit_state(KIT/'out/pool_part2')==0
    preflight=OUT/'LAUNCH_PREFLIGHT.json'
    preflight.write_text(json.dumps(dict(status='PASS',gpu='NOT PROBED',command='python -B work/finalize_ph2fix2.py',input_sha256=pins),indent=1)+'\n')
    paths.extend([preflight, *sorted((KIT/'part2').glob('*.py')), KIT/'part2/launch_gpu.sh',KIT/'part2/vendor/PINS.json',KIT/'part2/vendor/terminator.sh'])
    record=dict(status='PASS',fresh_strace='MISSING: sandbox denies ptrace; see STRACE_PH2FIX2.json',gpu='NOT RUN',runs=runs,input_sha256={str(p):L.sha(p) for p in paths})
    (OUT/'CPU_VALIDATION.json').write_text(json.dumps(record,indent=1)+'\n')
    print('PASS: CPU suites, dry-run steps 1–4, fixture aggregate, guard replay, staging and production preflight. Fresh strace MISSING.')
if __name__=='__main__':main()
