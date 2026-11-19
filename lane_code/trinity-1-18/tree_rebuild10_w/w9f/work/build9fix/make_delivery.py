"""Package source, both kits, comparison base, fixtures and exact packet tests."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix'
seal=json.loads((L/'out/TREE_SEAL.json').read_text())['tree_sha256'];target=L/'out'/f'tree_rebuild_b9f_{seal[:8]}.tar'
members=[]
for folder in ('work/tree_r1','work/base/tree_b01ce449','fixtures','work/build9fix/kits','work/build9fix/inputs','work/build_n1/inputs','work/rows_slices/slices_final','work/contracts_r6/tests_r6','work/contracts_r6/packet_root/work/tests_r6'):
    source=folder.startswith(('work/tree_r1','work/base'))
    for p in (L/folder).rglob('*'):
        if p.is_file() and not p.is_symlink() and not (source and set(p.relative_to(L/folder).parts)&{'.git','__pycache__','artifacts'}):members.append(p)
for name in ('RUN_PY.sh','PACKAGE_TEST.sh','PACKET_TEST.sh','TARGETED_TEST.sh','targeted.py','packet_recovery.py','packet_support.py','PACKET_INPUTS.json','make_delivery.py','test_runner.py','compact_tmp.py','package.py','compare.py','coverage.py','coverage_all.py','classify_coverage.py','coverage_cases.py','coverage_b7.py','packet_final.py','legacy_guard_proof.py','LEGACY_GUARDS.json','stop_multirank.py','stop_monitor.py','proofs/stop_multirank/RUN.sh','proofs/stop_multirank/SOURCE.json','proofs/stop_multirank/DRIVER_PINS.json'):
    
    if (B/name).exists(): members.append(B/name)
for name in ('PATCH_MANIFEST_R6.json','contract_hash_checks_r6.py','PATCH_geometry_r6.diff','PATCH_candidates_r6.diff','PATCH_box_r6.diff','PATCH_geometry_on_tree_r1_r6.diff','run_tests_r6.py','final_suites_r6.py','CONTRACTS_REPORT_R6.md','ROW_FAMILY_PARITY_R6.md'):
    members.append(L/'work/contracts_r6'/name)
packet_inputs=json.loads((L/'work/build9fix/PACKET_INPUTS.json').read_text())
for name in ('work/build5/proofs/suite_tree/results.json','work/build5/proofs/suite_tree/source_hashes.json',
             'work/contracts_r6/tree_copy/student_pilot/r2_policy.py'):
    members.append(L/name)
members.extend(p for p in B.iterdir() if p.is_file() and p.suffix in ('.py','.sh'))
members.extend(L/'out'/name for name in ('MIX_A0.json','MIX_A2.json','MIX_R1.json'))
members=list(dict.fromkeys(members))
size=sum(p.stat().st_size for p in members)+sum(row['bytes'] for row in packet_inputs);assert size<200_000_000
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
with tarfile.open(target,'w:gz') as tar:
    for p in sorted(members):tar.add(p,arcname=str(p.relative_to(L)),recursive=False)
    for row in packet_inputs:tar.add(L/row['source'],arcname=row['target'],recursive=False)
assert target.stat().st_size<150_000_000
h=hashlib.sha256()
with target.open('rb') as f:
    for block in iter(lambda:f.read(1024**2),b''):h.update(block)
record=dict(path=str(target.relative_to(L)),bytes=target.stat().st_size,sha256=h.hexdigest(),tree_seal=seal,format='gzip-compressed tar',member_bytes=size)
(B/'DELIVERY.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
