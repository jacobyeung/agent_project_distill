from pathlib import Path
import hashlib,json,tarfile
r=Path(__file__).resolve().parents[1]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
commands={
'original_suite':'bash work/review/review_run.sh p1cpu tests_run.py',
'reproduction':'bash work/review/reproduce.sh; bash work/review/complete_checks.sh',
'contract':'bash work/review/review_run.sh p1cpu contract_audit.py; bash work/review/review_run.sh p1cpu contract_audit_4col.py',
'archive':'python -B work/verify_archive.py',
'seeds':'python -B work/check_seeds.py',
'population':'python -B work/check_receipts.py',
'model_size_and_hours':'bash kit_v2/run_cpu.sh sam3 ../work/static_check.py',
'gpu_environment_import_audit':'PYTHONNOUSERSITE=1 bash kit_v2/run_cpu.sh sam3 ../work/import_audit.py',
'patched_suite':"OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B -m pytest -q -p no:cacheprovider --basetemp work/pytest_patched kit_v2/tests",
'patched_scoring':'bash work/patched_check.sh',
'staging':'bash kit_v2/run_cpu.sh p1cpu mc_staging.py',
'patch_apply':'patch -d work/patch_verify -p1 < out/GUARD.patch',
'package':'python -B work/package_check.py'}
checks=r/'out/check'
assert '109 passed' in (checks/'tests_patched.log').read_text()
assert not json.loads((checks/'IMPORT_AUDIT.json').read_text())['nfs_attempts']
assert json.loads((checks/'REAL_RERUN_REFUSAL.json').read_text())['files_unchanged']
parity=json.loads((r/'work/patched/out/v2/dry/STUB_PARITY.json').read_text())
assert all(x['passed'] for x in parity['checks'].values())
files=list((r/'kit_v2').rglob('*'))+list((r/'in').rglob('*'))
files += [p for p in checks.glob('*') if p.name not in ('EVIDENCE.json','PACKAGE_VERIFY.json')]
files += [r/'out/GUARD.patch',r/'out/v2/STAGING.json',r/'out/v2/KIT_MANIFEST.sha256',r/'out/v2/BARS_FROZEN.json',r/'out/v2/POPULATION.json',r/'out/v2/KIT_REPORT.md',r/'out/CACHK_VERDICT.md']
files += list((r/'work').glob('*.py'))+list((r/'work').glob('*.sh'))
files += list((r/'work/review').glob('*.py'))+list((r/'work/review').glob('*.sh'))+list((r/'work/review').glob('CONTRACT*.json'))+list((r/'work/review/logs').glob('*.log'))
files += [r/'work/review/out/v2/dry/STEP0_PRECISION.json',r/'work/review/out/v2/dry/STUB_PARITY.json',r/'work/patched/out/v2/dry/STUB_PARITY.json']
pins={str(p):h(p) for p in files if p.is_file()}
evidence=dict(command=commands['package'],commands=commands,part1_tests=74,patched_tests=109,guard_tests=35,
 source_archive_sha256='c5fbb8b12f31b1f09931821cf8ac39c6edb5b8b477db0f7135c3521f5f01b31e',
 frozen_sha256=h(r/'out/v2/BARS_FROZEN.json'),staging_bytes=json.loads((r/'out/v2/STAGING.json').read_text())['total_bytes'],
 caveats=['Original reviewer reproduction lacks the new empty stub; complete_checks.sh adds it.',
 'CPU run without PYTHONNOUSERSITE attempted user-site NFS lookups; the audit blocked them. The launcher-equivalent environment made zero attempts.',
 'The model memory and GPU time remain estimates; no GPU was used.'],input_sha256=pins)
(checks/'EVIDENCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
(r/'STATUS.md').write_text('GO for the guarded GPU pass. All nine edits are DONE; archive/manifest, exclusions, 74 original tests, 109 patched tests, fresh scoring and final-summary refusal checks pass. The launcher-equivalent CPU model build attempts no NFS access. The patched kit and GUARD.patch retain the registered bars hash; staging totals 14,924,717,613 bytes. GPU execution requires one native-bf16 card of at least 24 GB and a two-hour cumulative cap; GPU results and measured CUDA memory remain MISSING. Deliverables are out/CACHK_VERDICT.md, out/GUARD.patch, and out/sb_cachk.tar with its SHA256.\n')
archive=r/'out/sb_cachk.tar'
paths=['kit_v2','in','out/v2','out/CACHK_VERDICT.md','out/CAFIX_NOTES.md','out/GUARD.patch','out/check','STATUS.md']
paths += [str(p.relative_to(r)) for p in (r/'work').glob('*.py')]+[str(p.relative_to(r)) for p in (r/'work').glob('*.sh')]
paths += [str(p.relative_to(r)) for p in (r/'work/review').glob('*.py')]+[str(p.relative_to(r)) for p in (r/'work/review').glob('*.sh')]
paths += ['work/review/logs','work/review/CONTRACT_AUDIT.json','work/review/CONTRACT_AUDIT_4COL.json','work/review/out/v2/dry/STEP0_PRECISION.json','work/review/out/v2/dry/STUB_PARITY.json','work/patched/out/v2/dry/STUB_PARITY.json']
with tarfile.open(archive,'w') as t:
 for name in paths:t.add(r/name,arcname=name)
ash=h(archive);(r/'out/sb_cachk.tar.sha256').write_text(ash+'  out/sb_cachk.tar\n')
rows=[]
with tarfile.open(archive) as t:
 for m in t.getmembers():
  if m.isfile():
   actual=hashlib.sha256(t.extractfile(m).read()).hexdigest();expected=h(r/m.name)
   assert actual==expected,m.name
   rows.append(dict(path=m.name,sha256=actual))
(checks/'PACKAGE_VERIFY.json').write_text(json.dumps(dict(command=commands['package'],files=rows,input_sha256={str(archive):ash,str(Path(__file__)):h(Path(__file__))}),indent=2)+'\n')
print('archive',ash,'files',len(rows),'bytes',archive.stat().st_size)
