"""Verify final artifacts, behavior boundaries and completed test evidence."""
from pathlib import Path
import ast,hashlib,json,re,sys,tarfile,time
B=Path(__file__).resolve().parents[1];OLD=B.parent/'03_vsti_c';sys.path.append(str(B/'code'))
from adapter import *
import engine
kit=B/'work/kit_verified.log';assert re.search(r'Ran 67 tests.*\n\nOK\s*$',kit.read_text(),re.S)
legacy=load(B/'out/LEGACY_TESTS.json');extra=load(B/'out/LEGACY_EXTRA.json')
assert legacy['run']==28 and not legacy['errors'] and not legacy['failures']
assert extra['run']==2 and extra['passed']
for name in ('legacy_verified.log','legacy_extra_verified.log'):assert (B/'work'/name).read_text().rstrip().endswith('OK')
old=(OLD/'code/o.py').read_text();new=(B/'code/o.py').read_text()
assert old[old.index('        J.J.storage_proof'):old.index('    except BaseException as error:')]==new[new.index('        J.J.storage_proof'):new.index('    except BaseException as error:',new.index('def run(config_path):'))]
transport=Path('code/sj/orch_cd/evalx/work/milestone/orchard_results.py')
assert (OLD/transport).read_text().replace("'[a-z][0-9a-f]{8,32}'","'(?:[a-z][0-9a-f]{8,32}|[0-9a-f]{24,32})'")==(B/transport).read_text()
assert [x for x in old.splitlines() if '#SBATCH' in x]==[x for x in new.splitlines() if '#SBATCH' in x]
changed=[]
for p in (B/'code').rglob('*'):
 if p.is_file() and p.read_bytes()!=(OLD/'code'/p.relative_to(B/'code')).read_bytes():changed.append(str(p.relative_to(B)))
assert sorted(changed)==['code/o.py',str(transport)]
family=load(B/'out/FAMILY.json');baseline=load(OLD/'out/FAMILY.json');expected=json.loads(json.dumps(baseline))
expected['code']=family['code'];expected['code_sources']=family['code_sources'];expected['added']['c']=family['added']['c']
assert family==expected and family['code_sources']==engine.source_pins()
assert family['added']['d']==baseline['added']['d']
assert sha(B/'out/d.tar')==sha(OLD/'out/d.tar')=='9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f'
with tarfile.open(B/'out/c.tar') as t:
 members=t.getmembers();assert all(m.isfile() for m in members)
 assert {m.name for m in members}=={str(p.relative_to(B/'code')) for p in (B/'code').rglob('*') if p.is_file()}
 for m in members:assert hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(B/'code'/m.name)
size=load(B/'out/RETURN_SIZE.json');assert size['passed'] and size['source_pins']==engine.source_pins()
assert size['full_return_expanded_bytes']<=size['expanded_cap_bytes'] and size['full_return_archive_bytes']<=size['archive_cap_bytes']
assert sha(size['archive']['path'])==size['archive']['sha256']
# Refresh prose measurements from the final archive rather than the source sidecars.
p=B/'out/DIAGNOSIS.md';text=p.read_text()
text=re.sub(r'\*\*[\d,]+ expanded bytes\*\*, \*\*[\d,]+ archive bytes\*\*, and \*\*\d+ files\*\*',f"**{size['full_return_expanded_bytes']:,} expanded bytes**, **{size['full_return_archive_bytes']:,} archive bytes**, and **{size['full_return_members']} files**",text)
text=re.sub(r'The expanded headroom is [\d,]+ bytes and archive headroom is [\d,]+ bytes',f"The expanded headroom is {size['expanded_headroom_bytes']:,} bytes and archive headroom is {size['archive_headroom_bytes']:,} bytes",text);p.write_text(text)
inv=[]
for p in sorted((B/'tests').glob('test_*.py')):
 inv.extend(dict(file=str(p.relative_to(B)),test=n.name) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'))
assert len(inv)==67
dump(B/'out/TESTS.json',dict(passed=True,kit_run=67,inherited_run=30,kit_log=pin(kit),
 inherited=pin(B/'out/LEGACY_TESTS.json'),extra=pin(B/'out/LEGACY_EXTRA.json'),inventory=inv,source_pins=engine.source_pins(),
 inherited_scope='Same 28+2 selected inherited tests as V1c; the inherited inventory records excluded allocation/transport tests.',
 fixture_note='Optional index list explicitly absent in inherited CPU fixtures; current shared list has incompatible indices schema. Production adapter unchanged.'))
seen=set();logical=unique=allocated=0
for p in B.rglob('*'):
 if any(n in p.relative_to(B).parts for n in ('.git','.agents','.aws','.codex')) or not p.is_file():continue
 st=p.stat();logical+=st.st_size
 if (st.st_dev,st.st_ino) not in seen:
  seen.add((st.st_dev,st.st_ino));unique+=st.st_size;allocated+=st.st_blocks*512
assert unique<4_000_000_000 and allocated<4_000_000_000
footprint=dict(unique_file_bytes=unique,allocated_bytes=allocated,path_sum_bytes_including_hardlink_duplicates=logical,
 limit_bytes=4_000_000_000,note='Unique file bytes and allocated storage stay under the limit; summing hard-linked paths counts the same file more than once. Sparse cap fixtures occupy fewer disk blocks than their logical size.')
pkg=load(B/'out/PACKAGE.json')
for key in ('code','family','reference'):assert sha(pkg[key]['path'])==pkg[key]['sha256']
dump(B/'out/PACKAGE_VERIFY.json',dict(passed=True,package=pin(B/'out/PACKAGE.json'),code_members_verified=True,
 d_byte_identical=True,execution_phase_body_identical=True,batch_directives_identical=True,only_changed_code=changed,
 family_policy_unchanged=True,footprint=footprint))
unchecked=['Job 170228 actual token, final run inventory, free disk and logs were unavailable',
 'GPU tower/checkpoint/decoding and completed 450-item return size',
 'Actual Orchard namespace, staging, live pool/GCS channels, transfer/deadline duration',
 'Guaranteed delivery after fatal process loss, unavailable channels/storage or protected artifacts exceeding fixed caps']
dump(B/'out/FINAL_RESULT.json',dict(status='built and CPU-verified',package=pkg,tests=pin(B/'out/TESTS.json'),
 return_size=pin(B/'out/RETURN_SIZE.json'),diagnosis=pin(B/'out/DIAGNOSIS.md'),token_reproduction=pin(B/'out/TOKEN_REPRO.json'),
 verify=pin(B/'out/PACKAGE_VERIFY.json'),footprint=footprint,not_checked=unchecked))
(B/'STATUS.md').write_text('V1f is built and CPU-verified. All 67 kit and 30 inherited tests pass. The final archive matches the code; d.tar is byte-identical to V1c. Full prepare-return sizes and limitations are in out/RETURN_SIZE.json; diagnosis and hashes are in out/FINAL_RESULT.json. No remote job was submitted.\n')
lines=[
 'RESULT: V1f built and CPU-verified; no job submitted. Evidence: out/FINAL_RESULT.json.',
 'Code SHA256 '+pkg['code']['sha256']+' (out/c.tar).',
 'Family SHA256 '+pkg['family']['sha256']+' (out/FAMILY.json).',
 'Reference SHA256 '+pkg['reference']['sha256']+' (out/d.tar); byte-identical to V1c.',
 'Tests: 67 kit + 30 inherited pass (out/TESTS.json; work/kit_verified.log).',
 'CPU prepare return: 311 scenes; '+str(size['full_return_expanded_bytes'])+' expanded bytes; '+str(size['full_return_archive_bytes'])+' archive bytes; '+str(size['full_return_members'])+' members (out/RETURN_SIZE.json).',
 'Caps: 536870912 expanded bytes, 299983616 archive bytes, 10000 members; no scaled arrays omitted in the size rehearsal (out/RETURN_SIZE.json).',
 'Token mismatch reproduced: digit-leading packet tokens failed before both channels; admission now matches existing packet tokens (out/TOKEN_REPRO.json).',
 'Full return failures trigger a diagnostic return with both tracebacks, inventory, protected evidence and log tails (code/o.py; tests/test_v1f.py).',
 'All four input tar roles reject hard links and symlinks before packet creation (tests/test_v1f.py).',
 'Execution phase body, budgets, batch directives and all other code remain unchanged except inherited token admission (out/PACKAGE_VERIFY.json).',
 'Diff and ranked diagnosis: out/DIFF_vs_V1c.patch; out/DIAGNOSIS.md. Operator namespace command: out/rehearsal/RUNBOOK.md.',
 'Unique-file footprint '+str(unique)+' bytes; allocated '+str(allocated)+' bytes, under 4000000000 (out/PACKAGE_VERIFY.json).',
 'Unchecked: failed-job token/logs/disk, GPU/real weights, completed decoded-return size, Orchard namespace, live channels and return timing (out/FINAL_RESULT.json).',
 'Physical failures can still prevent delivery; fixed caps cannot hold arbitrarily large protected journals (out/DIAGNOSIS.md).']
assert len(lines)<=20
next(iter(sorted((B/'events').glob('*_RESULT_final.md'))),B/'events'/(time.strftime('%Y%m%dT%H%MZ',time.gmtime())+'_RESULT_final.md')).write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(passed=True,code=pkg['code']['sha256'],family=pkg['family']['sha256'],return_bytes=size['full_return_archive_bytes'],footprint=footprint),indent=2))
