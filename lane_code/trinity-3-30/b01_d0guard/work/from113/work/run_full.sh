#!/bin/bash
set -e
L=/scratch/jjyeung/orch_n30/native_r2; F=$L/work/full_c8r; B=$L/builds/05_analysis_fix
cd $F
echo "archive $(sha256sum result.tar.gz | cut -c1-64) expect 5c150bafb333117b2e026def36564b26cecf25bcdf9d536e5350c84fdef972a1 bytes $(stat -c %s result.tar.gz)"
mkdir -p x && tar xzf result.tar.gz -C x COMPLETE.json native/R1.json native/R1.json.pin.json native/paired/IN_JOB_ADMISSION.json native/paired/results/COMPLETE.json native/paired/results/GPU_PARITY.json metadata/ORCHARD_NATIVE.json metadata/NATIVE_RUNTIME.json metadata/REVIEW.json logs/worker.log
cd x; python3 - <<'PY'
import json,hashlib
c=json.load(open('COMPLETE.json'))
for p,h in c['receipts'].items():
    g=hashlib.sha256(open(p,'rb').read()).hexdigest(); print('receipt',p,'OK' if g==h else 'MISMATCH '+g)
b=json.load(open('native/R1.json'))
print('N1',[(a,r['key'],(r.get('decode') or {}).get('finish')) for a in ('unflagged','scripted') for r in b['arms'][a] if (r.get('decode') or {}).get('finish') in ('call_limit','error') and max((v or 0) for v in r['scores'].values())>0])
PY
cd $B
export PYTHONPATH=$L/work/np226:$L/work/pyextra
/usr/bin/time -v $L/env312/bin/python3.12 -I -s -B out/native_vs_direct.py --bundle $F/x/native/R1.json --admission $F/x/native/paired/IN_JOB_ADMISSION.json --direct-artifact $B/in/direct_raw/metadata/EXPORT_ARTIFACT.json --output $B/out/real > $B/out/real_run.log 2>&1; echo "analysis exit $?"
