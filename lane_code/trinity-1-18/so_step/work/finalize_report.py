"""Embed the exact retained verification outputs in the final report."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
report=ROOT/'out/REPORT.md'
marker='\n## Exact verification commands and outputs\n'
body=report.read_text().split(marker,1)[0]
body+=marker+'''
All commands ran from `/scratch/jjyeung/orch_n30/so_step` on `trinity-1-18`. The shell ran `date -u` at each task boundary. Tests used this environment:

```bash
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/verified_delivery/combined
```

The commands below show the executed Python invocations. Each named log contains merged stdout/stderr, followed by the shell's `EXIT_CODE` record. Fresh-copy destinations are retained and must use a new name for another verification. The complete output is reproduced without trimming. CPU profiler durations and data-only timings describe synthetic fixtures only.
'''
python='nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B '
checks=[
    ('Fresh input copies: independent patches and ordered series',
     'work/verify_patches.py verified_delivery','patch_verify_delivery.txt'),
    ('Production-log arithmetic',
     'work/recheck_measurements.py','measurement_recheck.txt'),
    ('Patch unit tests; distributed cases explicitly not counted',
     'work/run_cpu_tests.py --local-only tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint',
     'cpu_units_delivery.txt'),
    ('Native local parity, including byte comparison and failure boundary',
     'work/test_local_parity.py','cpu_local_delivery.txt'),
    ('Profiler/default parity and isolated launcher checks',
     'work/test_kits.py','cpu_kits_delivery.txt'),
    ('Data replay and summary checks',
     'work/test_kit_utilities.py','cpu_utilities_delivery.txt'),
    ('Full requested suite: distributed rerun blocked by the socket restriction',
     'work/run_cpu_tests.py tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint',
     'cpu_full_delivery.txt'),
    ('Patch hashes, kit syntax and installed source excerpts',
     'work/check_delivery.py','delivery_integrity.txt'),
]
for title,command,filename in checks:
    output=(ROOT/'out/evidence'/filename).read_text()
    body+='\n### '+title+'\n\n```bash\n'+python+command+'\n```\n\n'
    body+='Exact output (`out/evidence/'+filename+'`):\n\n```text\n'+output
    if not body.endswith('\n'):
        body+='\n'
    body+='```\n'
body+='''
## What remains unverified

The exact delivered series still needs the two-rank gloo tests to verify FSDP losses, every gradient, trainables, row draws, collective payload/order and the all-rank failure boundary. This session cannot create sockets. Its local test success does not establish those distributed properties.

Production torchvision preprocessing and the actual processor assets remain outside the local fixtures. The production data-only kit checks their global RNG behavior. GPU phase times, speedups, memory fit and the actual 171377 DeltaNet bindings remain unmeasured; the requested GPU kits are delivered unrun.

The build-time choices remain CPU prefetch, decoded RGB caching and delayed component reads. No test invalidated those choices. The measurement launcher adapts the native smoke/resume guard and output path because the native guard rejects smoke plus resume and each measurement arm needs a fresh output directory. Tests verify both adaptations while preserving the original configuration.

The report retains one evidence-provenance distinction: the archived seven-test distributed proof is separate from this package's blocked rerun. A reviewer needs that distinction to avoid treating unmatched source as newly verified evidence.
'''
report.write_text(body)
print(f'REPORT_WRITTEN: {len(body.encode())} bytes; {len(checks)} exact command/output records')
