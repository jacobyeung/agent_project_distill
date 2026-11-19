"""Serialize bounded CPU gates and retain exact commands, output, and baseline failures."""
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
    MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false')
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
units = ['tests.test_carrier_c1_run', 'tests.test_so_prefetch', 'tests.test_so_cache',
         'tests.test_so_metrics', 'tests.test_so_review', 'tests.test_so_round2', 'tests.test_so_joint']
existing = ['tests.test_gx_carrier','tests.test_gf1_cache','tests.test_gf1_contracts',
            'tests.test_gx_s6','tests.test_startup_receipt','tests.test_carrier_c1_final']
related = ['tests.test_gx_s7','tests.test_gx_s8','tests.test_carrier_c1_t0.ExportLeg',
           'tests.test_pose_samples','tests.test_carrier_c1_data','tests.test_batch_options']
failure_ids = lambda text: re.findall(r'^(?:ERROR|FAIL): (.*)$', text, re.M)
expected = failure_ids((ROOT/'out/evidence/round2_baseline_existing.txt').read_text())
assert len(expected) == 6
related_expected = failure_ids((ROOT/'out/evidence/round2_baseline_related.txt').read_text())
assert len(related_expected) == 2
checks = []
for build, tree, base in [('b20', ROOT/'work/tree', ROOT/'in/tree/work/tree_r1'),
                          ('b21', ROOT/'work/b21_final/work/tree_r1',
                           Path('/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/tree_r1'))]:
    suites = [('units', ['work/run_cpu_tests.py','--local-only',*units]),
              ('related', ['work/run_cpu_tests.py','--local-only',*related]),
              ('parity', ['work/test_local_parity.py']), ('kits', ['work/test_kits.py']),
              ('review_kits', ['work/test_review_kits.py']), ('utilities', ['work/test_kit_utilities.py']),
              ('round2_kits', ['work/test_round2_kits.py'])]
    if build == 'b21':
        suites.insert(1, ('existing', ['work/run_cpu_tests.py','--local-only',*existing]))
    for kind, args in suites:
        env = dict(os.environ, SO_TEST_TREE=str(tree), SO_TEST_BASE=str(base))
        command = ['nice','-n','10',sys.executable,'-I','-s','-B',*args]
        print(datetime.datetime.now(datetime.timezone.utc).isoformat()+' START '+build+' '+kind, flush=True)
        result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        transcript = ('$ SO_TEST_TREE='+str(tree)+' SO_TEST_BASE='+str(base)+' '+shlex.join(command)+'\n'
                      + result.stdout+'\nEXIT='+str(result.returncode)+'\n')
        name = f'round2_final_{build}_{kind}.txt'
        (ROOT/'out/evidence'/name).write_text(transcript)
        accepted = result.returncode == 0
        if kind == 'existing':
            accepted = result.returncode == 1 and failure_ids(result.stdout) == expected
        if kind == 'related':
            accepted = result.returncode == 1 and failure_ids(result.stdout) == related_expected
        checks.append(dict(build=build, kind=kind, exit=result.returncode, accepted=accepted,
                           baseline_only=kind in ('existing','related'), log=name,
                           summary=re.findall(r'^(?:Ran .*|OK.*|FAILED.*)$', result.stdout, re.M)))
        (ROOT/'out/evidence/round2_final_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
        print(build+' '+kind+' EXIT='+str(result.returncode)+' ACCEPTED='+str(accepted), flush=True)
        if not accepted:
            raise SystemExit(1)
print('ALL_LOCAL_GATES_PASS_WITH_EIGHT_DECLARED_BASELINE_FAILURES', flush=True)
