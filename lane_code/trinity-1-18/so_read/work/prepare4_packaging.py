from pathlib import Path
p=Path('work/build_patches.py');s=p.read_text()
s=s.replace('range(12,19)','range(12,20)')
s=s.replace("'u0/tests/test_operator_round3.py','u0/tests/test_lock_round3.py']}", "'u0/tests/test_operator_round3.py','u0/tests/test_lock_round3.py','u0/tests/test_round4.py']}")
s=s.replace("'work/apply-round3'","'work/apply-round4'")
s=s.replace("L/'work/operator3/tower_sequence.py'","L/'work/operator4/tower_sequence.py'")
start=s.index("manifest['operator_files']={")
end=s.index("\nsuite=[]",start)
s=s[:start]+'''# The return and CPU-proof helpers are A4 operator-side changes, guarded by
# read_extensions. They apply from the same operator directory as patch 04.
name='05_operator_return_and_proof.diff';parts=[];pins={}
for rel in ('unpack_return.py','package/a/5.py'):
 before=(BASE/'A4'/rel).read_bytes();after=(L/'work/operator4'/rel).read_bytes()
 parts.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),
                                  fromfile='a/'+rel,tofile='b/'+rel,n=3))
 pins[rel]=dict(before_sha256=sha(before),after_sha256=sha(after),bytes=len(after))
 dest=operator_root/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(before)
 dest=public_operator/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(after)
raw=''.join(parts).encode();(L/'out/patches'/name).write_bytes(raw)
result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(operator_root)],input=raw,
                      stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
assert result.returncode==0 and b'fuzz' not in result.stdout.lower(),result.stdout
for rel in pins:assert sha((operator_root/rel).read_bytes())==pins[rel]['after_sha256']
with (L/'out/checks/patch_application.txt').open('a') as f:f.write(result.stdout.decode())
manifest['patches'][name]=dict(sha256=sha(raw),bytes=len(raw),files=pins,
    apply_from='fresh A4 operator directory, outside src, after patch 04')
manifest['operator_files']={str(p.relative_to(public_operator)):dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
    for p in public_operator.rglob('*') if p.is_file()}
manifest['application_checks']['A4_operator']='zero fuzz; explicit read_extensions default OFF; exact delivered bytes'
''' +s[end:]
s=s.replace("READ_OPERATOR_SOURCE=str(operator_root/'tower_sequence.py'))", "READ_OPERATOR_SOURCE=str(operator_root/'tower_sequence.py'),READ_OPERATOR4_SOURCE=str(operator_root))")
s=s.replace("'operator_round3','lock_round3','compare')", "'operator_round3','lock_round3','round4','compare')")
s=s.replace("plus 1 default-OFF A4 operator diff", "plus 2 default-OFF A4 operator diffs")
s=s.replace("all 10 CPU suites", "all 11 CPU suites")
s=s.replace("three additive reader diffs plus the operator diff", "three additive reader diffs plus two operator diffs")
s=s.replace("u0/a12.py --enable-extensions builds the production overlays (apply all three patches)", "u0/a19.py --enable-extensions builds the bound A4 cache-only package; a12 is the generic integration builder (apply reader patches 01-03 and A4 operator patches 04-05)")
p.write_text(s)
