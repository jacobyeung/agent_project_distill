"""Package source, both kits, comparison base, fixtures and exact packet tests."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
if (B/'REQUALIFICATION.json').exists() and json.loads((B/'REQUALIFICATION.json').read_text()).get('pending'):
    raise SystemExit('Final source qualification is pending; no package written')
seal=json.loads((L/'out/TREE_SEAL.json').read_text())['tree_sha256'];target=L/'out'/f'tree_rebuild_b16_{seal[:8]}.tar'
members=[]
for folder in ('work/tree_r1','work/base/tree_b01ce449','fixtures','work/build16/kits','work/n1fix2/inputs','work/n1fix2/inherited','work/build_n1/inputs','work/rows_slices/slices_final','work/contracts_r6/tests_r6','work/contracts_r6/packet_root/work/tests_r6'):
    source=folder.startswith(('work/tree_r1','work/base'))
    for p in (L/folder).rglob('*'):
        if p.is_file() and not p.is_symlink() and not (source and set(p.relative_to(L/folder).parts)&{'.git','__pycache__','artifacts'}):members.append(p)
for name in ('RUN_PY.sh','PACKAGE_TEST.sh','PACKET_TEST.sh','TARGETED_TEST.sh','targeted.py','packet_recovery.py','packet_support.py','PACKET_INPUTS.json','make_delivery.py','test_runner.py','compact_tmp.py','package.py','compare.py','coverage.py','coverage_all.py','classify_coverage.py','coverage_cases.py','coverage_b7.py','packet_final.py','legacy_guard_proof.py','LEGACY_GUARDS.json','stop_multirank.py','stop_monitor.py','proofs/stop_multirank/RUN.sh','proofs/stop_multirank/SOURCE.json','proofs/stop_multirank/DRIVER_PINS.json'):
    
    if (B/name).exists(): members.append(B/name)
for name in ('PATCH_MANIFEST_R6.json','contract_hash_checks_r6.py','PATCH_geometry_r6.diff','PATCH_candidates_r6.diff','PATCH_box_r6.diff','PATCH_geometry_on_tree_r1_r6.diff','run_tests_r6.py','final_suites_r6.py','CONTRACTS_REPORT_R6.md','ROW_FAMILY_PARITY_R6.md'):
    members.append(L/'work/contracts_r6'/name)
packet_inputs=json.loads((L/'work/build16/PACKET_INPUTS.json').read_text())
for name in ('work/build5/proofs/suite_tree/results.json','work/build5/proofs/suite_tree/source_hashes.json',
             'work/contracts_r6/tree_copy/student_pilot/r2_policy.py'):
    members.append(L/name)
members.extend(p for p in B.iterdir() if p.is_file() and p.suffix in ('.py','.sh'))
for folder in ('original','proofs/review_inputs'):
    members.extend(p for p in (B/folder).rglob('*') if p.is_file() and not p.is_symlink())
members.extend(L/'work/build9fix'/name for name in ('test_runner.py','compact_tmp.py'))
members.extend(L/'out'/name for name in ('MIX_A0.json','MIX_A2.json','MIX_R1.json'))
members.append(L/'work/build12/legacy9fix_source.py')
members.append(L/'work/merge11/legacy9fix_source.py')
members.extend(p for p in (L/'work/build12').iterdir() if p.is_file() and p.suffix in ('.py','.sh'))
for name in ('MERGE12.json','DECISIONS.md','CHANGED_COVERAGE.json','GAPS.json',
             'NATIVE_FUNCTION_EQUALITY.json','PROOF_EQUALITY.json','RUNNER_EQUIVALENCE.json','HARNESS_BASE.json',
             'STORAGE.json','EXECUTABLE_PATH_SEARCH.json','SELECTED_PATH_AUDIT.json'):
    p=L/'work/build12'/name
    if p.exists():members.append(p)
proof_root=L/'work/build12/proofs'
for p in proof_root.rglob('*.json'):
    if set(p.relative_to(proof_root).parts)&{'frozen','prior_frozen','prior_kits'}:continue
    if p.name in ('RESULT.json','EAT1_REPORT.json','ASCII_CANDIDATE.json',
                  'INFERENCE_COMPONENTS.json','GROUP_RECEIPT.json','RESUME_RECEIPT.json',
                  'results.json','hits.json','source_hashes.json','MONITOR_STORAGE.json'):
        members.append(p)
for folder in ('n1/packet','n1/suite_tree','n1/suite_base'):
    for name in ('results.json','hits.json','source_hashes.json'):
        p=proof_root/folder/name
        if p.exists():members.append(p)
for folder in ('work/build10/eat1','work/build10/eat1_clean'):
    members.extend(p for p in (L/folder).rglob('*') if p.is_file() and not p.is_symlink()
                   and p.suffix in ('.py','.md','.json','.toml','.txt'))
members.append(L/'out/EAT1_FIXED_MATH.patch')
members.extend((L/'work/build12/harness_base').rglob('*.py'))
for name in ('SUITE_COMPARISON.json','KIT_RESULT.json'):
    if (B/name).exists():members.append(B/name)
members=list(dict.fromkeys(members))
extra=L/'work/build13'
for p in extra.rglob('*'):
    if p.is_file() and not p.is_symlink() and not set(p.relative_to(extra).parts)&{'mutant','frozen','kits'} and p.suffix in ('.py','.sh','.json','.md') and p.stat().st_size<30_000_000:members.append(p)
extra=L/'work/build14'
for p in extra.rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(extra)
    # An archive cannot carry its own digest; publish that receipt beside it.
    if str(rel) in ('DELIVERY.json','proofs/final/package/ARCHIVE.json','proofs/integrity/RESULT.json'):continue
    if set(rel.parts)&{'mutant','frozen','kits','retained_kits13'}:continue
    if p.suffix in ('.py','.sh','.json','.md') and p.stat().st_size<30_000_000:members.append(p)

extra=L/'work/build15'
for p in extra.rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(extra)
    if str(rel) in ('DELIVERY.json','FINAL_RUNS.json','proofs/integrity/RESULT.json'):continue
    if set(rel.parts)&{'mutant','frozen','kits','retained_kits_attempt'}:continue
    if p.suffix in ('.py','.sh','.json','.md') and p.stat().st_size<30_000_000:members.append(p)


extra=L/'work/build16'
for p in extra.rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(extra)
    if str(rel) in ('DELIVERY.json','proofs/integrity/RESULT.json'):continue
    if set(rel.parts)&{'mutant','frozen','base','kits','retained_kits_attempt'}:continue
    if p.suffix in ('.py','.sh','.json','.jsonl','.md','.log') and p.stat().st_size<30_000_000:members.append(p)

members.extend(p for p in (L/'out').glob('*.md'))
members.extend(L/'out'/n for n in ('TREE_SEAL.json','TREE_FILES.sha256','TREE.diff'))
members=list(dict.fromkeys(members))
size=sum(p.stat().st_size for p in members)+sum(row['bytes'] for row in packet_inputs)
assert size<1_200_000_000
print(json.dumps(dict(selected_member_bytes=size,selected_members=len(members))),flush=True)
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
assert workspace+150_000_000<1_500_000_000
class LimitedArchive:
    def __init__(self,raw):self.raw=raw
    def write(self,data):
        if self.raw.tell()+len(data)>=150_000_000:
            raise ValueError('Compressed archive would exceed 150 MB; stopped before writing that block')
        return self.raw.write(data)
    def __getattr__(self,name):return getattr(self.raw,name)
with target.open('wb') as raw:
    with tarfile.open(fileobj=LimitedArchive(raw),mode='w:gz') as tar:
        for p in sorted(members):tar.add(p,arcname=str(p.relative_to(L)),recursive=False)
        for row in packet_inputs:tar.add(L/row['source'],arcname=row['target'],recursive=False)
assert target.stat().st_size<150_000_000
h=hashlib.sha256()
with target.open('rb') as f:
    for block in iter(lambda:f.read(1024**2),b''):h.update(block)
record=dict(path=str(target.relative_to(L)),bytes=target.stat().st_size,sha256=h.hexdigest(),tree_seal=seal,format='gzip-compressed tar',member_bytes=size)
(L/'work/build16/DELIVERY.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
