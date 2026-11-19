from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'work/build_patches.py';s=p.read_text()
s=s.replace("['u0/tests/test_round2.py']}","['u0/tests/test_round2.py','u0/tests/test_round3.py',\n     'u0/tests/test_operator_round3.py','u0/tests/test_lock_round3.py']}")
s=s.replace("'work/apply-round2'","'work/apply-round3'")
s=s.replace('copy_values(original,verify)','copy_values(full_base,verify)')
s=s.replace("for rel,data in original.items():assert (verify/rel).read_bytes()==data,rel", "for rel,data in full_base.items():assert (verify/rel).read_bytes()==data,rel")
s=s.replace("for name in ('read_cache','read_journal','off','public','round1','round2','compare'):","for name in ('read_cache','read_journal','off','public','round1','round2','round3','operator_round3','lock_round3','compare'):")
needle="suite=[]\nenv=dict(os.environ,READ_INPUT_SRC=str(A),READ_TEST_TMP=str(L/'work/test-artifacts'))"
s=s.replace(needle,'''
# The operator patch has a separate input root; the three reader patches are additive.
operator_before=(BASE/'A4/tower_sequence.py').read_bytes()
operator_after=(L/'work/operator3/tower_sequence.py').read_bytes()
assert operator_before==(L/'work/operator3-original/7.py').read_bytes()
name='04_operator_cache_bound.diff'
raw=''.join(difflib.unified_diff(operator_before.decode().splitlines(True),
    operator_after.decode().splitlines(True),fromfile='a/tower_sequence.py',tofile='b/tower_sequence.py',n=3)).encode()
(L/'out/patches'/name).write_bytes(raw)
operator_root=run/'operator';operator_root.mkdir()
(operator_root/'tower_sequence.py').write_bytes(operator_before)
result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(operator_root)],
                      input=raw,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
assert result.returncode==0 and b'fuzz' not in result.stdout.lower(),result.stdout
assert (operator_root/'tower_sequence.py').read_bytes()==operator_after
with (L/'out/checks/patch_application.txt').open('a') as f:f.write(result.stdout.decode())
manifest['patches'][name]=dict(sha256=sha(raw),bytes=len(raw),apply_from='fresh A4 operator directory, outside src',
    files={'tower_sequence.py':dict(before_sha256=sha(operator_before),after_sha256=sha(operator_after),bytes=len(operator_after))})
manifest['operator_base_pin']=dict(path=str(BASE/'A4/tower_sequence.py'),sha256=sha(operator_before),
    bootstrap_source=str(BASE/'A4/package/BATCH.sh'),batch_sha256=sha((BASE/'A4/package/BATCH.sh').read_bytes()),
    decoded_bootstrap_sha256=sha((L/'work/operator3-original/0.py').read_bytes()))
public_operator=L/'out/operator';public_operator.mkdir(exist_ok=True)
(public_operator/'0.py').write_bytes((L/'work/operator3-original/0.py').read_bytes())
(public_operator/'tower_sequence.py').write_bytes(operator_after)
manifest['operator_files']={p.name:dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in public_operator.iterdir() if p.is_file()}
manifest['application_checks']['A4_operator']='zero fuzz; explicit read_extensions default OFF; exact delivered bytes'

suite=[]
env=dict(os.environ,READ_INPUT_SRC=str(A),READ_TEST_TMP=str(L/'work/test-artifacts'),
         READ_OPERATOR_SOURCE=str(operator_root/'tower_sequence.py'))''')
s=s.replace("manifest['kit_files']={",'''# Authenticate the actual 927-file roots, not only the small regression fixtures.
import importlib.util
sys.path[:0]=[str(L/'out/kit_parity50'),str(verify/'u0')]
spec=importlib.util.spec_from_file_location('verify_kit_roots',L/'out/kit_parity50/run.py')
kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
kit.validate_roots(dict(original_source_root=str(A),source_root=str(verify)))
assert json.loads((L/'out/kit_parity50/BASE_PIN.json').read_bytes())==manifest['base_pin']
manifest['authenticated_roots']=dict(original=str(A),patched=str(verify),files_per_root=len(full_base))
manifest['kit_files']={''')
s=s.replace("print('PASS: 3 additive unified diffs; '+str(len(all_files))+' files; zero-fuzz A4/B5 application; unchanged original hash trees.')", "print('PASS: 3 additive reader diffs ('+str(len(all_files))+' files) plus 1 default-OFF A4 operator diff; zero-fuzz application; unchanged original reader hash trees.')")
s=s.replace("print('PASS: all 7 CPU suites pass from the fresh applied A4 tree.')", "print('PASS: all 10 CPU suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.')")
s=s.replace('Regenerated three additive diffs, full A4 base pin and B5 archive pin; zero-fuzz application and applied-tree suites passed.', 'Regenerated three additive reader diffs plus the operator diff; full A4/B5/operator base pins, zero-fuzz application and applied-tree suites passed.')
p.write_text(s)
