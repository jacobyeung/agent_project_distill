"""Reproduce the final CPU checks; fixtures always use a fresh workspace destination."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
KIT = ROOT/'sb_mask_phrase'
OUT = ROOT/'out'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    runs = []
    fixture = 'work/part2_cpu_ph2fix_verified'
    aggregate = 'work/part2_aggregate_ph2fix_verified'
    if (KIT/fixture).exists() or (KIT/aggregate).exists():
        sys.exit('REFUSED: final verification destinations exist; review them before choosing a fresh destination')
    def run(name, args, extra=None, expected=0):
        command = ['bash', 'sb_mask_phrase/run.sh', *args]
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', **(extra or {}))
        log = OUT/(name+'.log')
        with log.open('w') as f:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
        if result.returncode < 0 or result.returncode in (137, 143):
            sys.exit(f'KILLED: {name}; stop, never rerun')
        runs.append(dict(name=name, command=command, environment=extra or {}, returncode=result.returncode,
                         expected_returncode=expected, status='PASS' if result.returncode == expected else 'FAIL', log=str(log)))
        print(name, result.returncode, flush=True)
    run('final_part1', ['test_kit.py'])
    run('final_part2', ['part2/test_part2.py'])
    run('launcher_tests', ['part2/test_launcher.py'])
    run('final_dryrun', ['dryrun.py', 'report'])
    run('final_fixture', ['part2/price.py', 'fixture', 'arkitscenes/41048124,scannetpp/067e2e4e61'], {'PART2_FIXTURE_DIR': fixture})
    # Reuse the explicitly synthetic capture inputs; do not recapture or claim GPU output.
    dest = KIT/aggregate
    dest.mkdir()
    command = ['cp', '-a', str(KIT/'work/part2_fixture/caps'), str(dest)+'/']
    subprocess.run(command, check=True)
    run('final_aggregate', ['part2/price.py', 'fixture-aggregate'], {'PART2_FIXTURE_DIR': aggregate})
    run('final_step5_cpu', ['part2/sam3_pass.py', 'step5'], {'PART2_GO': '1'}, expected=1)
    assert 'part 2 needs CUDA' in (OUT/'final_step5_cpu.log').read_text()
    assert not (KIT/'out/pool_part2/STEP5.json').exists(), 'CPU run must not fabricate a GPU gate'
    run('final_staging', ['part2/staging.py'])
    evidence = [KIT/'out/TESTS.json', KIT/'out/part2/TESTS_PART2.json', KIT/'out/DRYRUN.json',
                KIT/fixture/'FIXTURE.json', dest/'aggregate/DECISION_PART2.json', OUT/'STAGING_PART2.json',
                OUT/'PIN_RELOCATION.json']
    t1, t2, dry, fix, agg, staging, _ = [json.loads(p.read_text()) for p in evidence]
    assert t1['passed'] and t1['ran'] == 26
    assert t2['passed'] and t2['ran'] == 20
    assert dry['status'] == fix['status'] == staging['status'] == 'PASS'
    assert agg['w_exact_rows_equal_w_cf'] == 1037 and 'FIXTURE' in agg
    code = [Path(__file__), KIT/'run.sh', KIT/'launch.sh', *sorted((KIT/'part2').glob('*.py')), KIT/'part2/launch_part2.sh']
    pins = {str(p): sha(p) for p in [OUT/'LAUNCHER_TESTS.json', *evidence, *code, *[Path(r['log']) for r in runs]]}
    record = dict(status='PASS' if all(r['status'] == 'PASS' for r in runs) else 'FAIL', runs=runs,
                  synthetic_capture_staging_command=command, part1_tests=t1['ran'], part2_tests=t2['ran'],
                  step5=dict(status='FAIL', reason='CUDA required; expected CPU refusal; no GPU model loaded'),
                  gpu_pass='NOT RUN', launcher_tests=json.loads((OUT/'LAUNCHER_TESTS.json').read_text())['ran'], input_sha256=pins)
    (OUT/'CPU_VALIDATION.json').write_text(json.dumps(record, indent=1)+'\n')


if __name__ == '__main__':
    main()
