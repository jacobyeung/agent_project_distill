"""Local logic/namespace tests only; no production preparation claim."""
import base64, hashlib, json, os, re, stat, subprocess, sys, tempfile, zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
H=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(H/'tools'))
import proof_prepare as p
out=Path(tempfile.mkdtemp(prefix='proof_',dir=H/'evidence/fix8_admission'))
# Fresh-job parent creation must never repair or follow an existing bad parent.
for case in ('absent','private','public','link','dangling','file','foreign_owner'):
    root=out/case;root.mkdir(mode=0o700)
    parent=root/'jjyeung';work=parent/'p_8c74b291_123'
    if case in ('private','public','foreign_owner'):
        parent.mkdir(mode=0o700);parent.chmod(0o755 if case=='public' else 0o700)
    elif case in ('link','dangling'):
        target=root/'target'
        if case=='link':target.mkdir(mode=0o700)
        parent.symlink_to(target)
    elif case=='file':parent.write_text('untouched')
    def run():
        try:p.create_work(work)
        except ValueError:
            assert case not in ('absent','private')
            assert not work.exists()
        else:
            assert case in ('absent','private')
            for q in (parent,work,work/'tmp/jjyeung/a_17c4ffa4',work/'slots',work/'arm',work/'runs'):
                assert stat.S_IMODE(q.lstat().st_mode)==0o700 and q.lstat().st_uid==os.geteuid()
            try:p.create_work(work)
            except FileExistsError:pass
            else:raise AssertionError('Existing proof workspace was reused')
    if case=='foreign_owner':
        with patch.object(p.os,'geteuid',return_value=os.geteuid()+1):run()
    else:run()
    if case=='public':assert stat.S_IMODE(parent.stat().st_mode)==0o755
    if case in ('link','dangling'):assert parent.is_symlink() and not (target/'p_8c74b291_123').exists()
s=(H/'build/a_8c74b291.sh').read_text()
blob=re.search(r"base64.b64decode\('([^']+)'\)",s)[1]
raw=zlib.decompress(base64.b64decode(blob))
assert raw==(H/'tools/proof_prepare.py').read_bytes()
assert p.sha(H/'payload/jb.sh')==p.sha(H/'evidence/fix8_before/payload/jb.sh')
assert p.sha(H/'runtime/jb.sh')==p.sha(H/'payload/jb.sh')
assert p.sha(H/'EXPORT_OBJECTS.txt')==p.sha(H/'evidence/fix8_before/EXPORT_OBJECTS.txt')
script=p.program((H/'payload/jb.sh').read_text(),(H/'build/fx/job.sh').read_text())
(out/'entry.sh').write_text(script)
subprocess.run(['/bin/bash','-n',str(out/'entry.sh')],check=True)
subprocess.run(['/bin/bash','-n',str(H/'build/a_8c74b291.sh')],check=True)
assert script.endswith('/bin/bash "$ROOT/b/r.sh" p 0\n')
assert '"$ROOT/b/r8.py"' not in script and 'exec /bin/bash "$ROOT/b/r.sh" "$MODE"' not in script
assert 'newest || true' not in script and 'binding mirror written' not in script
assert 'sess.json lacks' in script and 'staging entries verified' in script
assert '3800000000000' in script and '"$ROOT/b/p0.sh" "$ROOT"' in script
assert '"$ROOT/b/g.py" "$ROOT" p' in script

# Execute the generated shell sequence with command stubs. Substitutions exist
# only in this test file; the shipped script has no fixture/dry-run switch.
trace=out/'trace';shim=out/'shim.py'
shim.write_text('import os,sys\nfrom pathlib import Path\np=Path('+repr(str(trace))+')\n'
 'with p.open("a") as f:f.write(" ".join(sys.argv[1:])+"\\n")\n'
 'if sys.argv[-1]=="p0":raise SystemExit(int(os.environ.get("FAIL_STAGE","0")))\n')
stub=out/'stub.sh';stub.write_text('#!/bin/bash\nexec '+sys.executable+' -B '+str(shim)+' "$@"\n');stub.chmod(0o700)
for failure in (0,9):
    # Keep set-e semantics and the exact final mode-p invocation structure.
    dry='set -e\nexport CUDA_VISIBLE_DEVICES=""\nROOT='+str(out)+'\n'
    for name in ('outer_preflight','a','p0','g'):
        dry+=str(stub)+' '+name+'\n'
    dry+=script[script.rindex('/bin/bash "$ROOT/b/r.sh" p 0'):].replace('/bin/bash "$ROOT/b/r.sh"',str(stub))
    r=p.execute(['/bin/bash','-s'],dry,out/('dry'+str(failure)+'.log'),
        lambda:dict(admission_result={'status':'PREPARED','TEST_ONLY':True},prepared_seals={'TEST_ONLY':True}),
        runner=lambda *a,**kw:subprocess.run(*a,env=dict(os.environ,FAIL_STAGE=str(failure)),**kw))
    assert r['rc']==failure and r['status']==('PASS' if not failure else 'FAIL')
    if failure:assert r['admission_result'] is None
assert trace.read_text().splitlines()==['outer_preflight','a','p0','g','p 0','outer_preflight','a','p0']
bad=p.execute(['/bin/true'],'',out/'badseal.log',lambda:(_ for _ in ()).throw(ValueError('bad seal')))
assert bad['status']=='FAIL' and bad['rc']==1

# Run the real mount plan, with only the NET namespace omitted because this
# local sandbox denies NETLINK_ROUTE. No network command runs in this test.
kh=out/'kit';kh.mkdir(mode=0o700)
for n in ('b','k','o','arm','runs'):(kh/n).mkdir(mode=0o700)
(kh/'k/config.json').write_text('production-byte-sentinel')
(kh/'arm/real').write_text('untouched');(kh/'runs/real').write_text('untouched')
rs=out/'r/root';rs.mkdir(parents=True);(rs/'real').write_text('untouched')
work=out/'work';work.mkdir(mode=0o700)
for n in ('tmp','slots','arm','runs'):(work/n).mkdir(mode=0o700)
args=p.command('/usr/bin/bwrap',kh,work,rs)
assert '--unshare-net' in args and args[args.index('--setenv')+1:args.index('--setenv')+3]==['CUDA_VISIBLE_DEVICES','']
args.remove('--unshare-net')
probe='''set -e
test -z "$CUDA_VISIBLE_DEVICES"
test "$(stat -c %a K)" = 700
test "$(stat -c %a R/..)" = 700
test "$(cat K/k/config.json)" = production-byte-sentinel
test ! -e R/real
test ! -e K/runs/real
test ! -e K/arm/real
echo isolated > /tmp/sentinel
echo isolated > R/claim
echo isolated > K/runs/proof
echo isolated > K/arm/proof
echo receipt > K/o/proof
if echo bad > K/k/config.json; then exit 7; fi
'''.replace('K',str(kh)).replace('R/',str(rs)+'/')
# In the isolated empty /tmp, exercise the driver at its actual absolute path,
# then the verbatim production directory preflight without staging any data.
wrapper=(H/'payload/jb.sh').read_text()
preflight=wrapper[wrapper.index('private_dir() {'):wrapper.index('private_dir "$O"')]
preflight+='\nO='+str(rs.parent.parent)+'\nKH='+str(kh)+'\nRS='+str(rs)+'\nRUN=/tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4\n'
preflight+=wrapper[wrapper.index('# BEGIN directory preflight'):wrapper.index('# END directory preflight')]
cold=('from pathlib import Path; import sys; sys.path.insert(0,'+repr(str(H/'tools'))+'); '
      'import proof_prepare as p; assert not Path("/tmp/jjyeung").exists(); '
      'p.create_work(Path("/tmp/jjyeung/p_8c74b291_123")); p.private(Path("/tmp/jjyeung"))')
import shlex
probe+='\n'+shlex.quote(sys.executable)+' -B -c '+shlex.quote(cold)+'\n'+preflight
probe+='\ntest -d "$RUN"\ntest ! -e /tmp/jjyeung/a_17c4ffa4/root/.stamp\n'
result=subprocess.run(args,input=probe,text=True,capture_output=True)
(out/'namespace.log').write_text(result.stdout+result.stderr)
assert result.returncode==0,result.stderr
assert (work/'tmp/sentinel').read_text().strip()=='isolated'
assert (work/'slots/claim').is_file() and not (rs/'claim').exists()
assert (rs/'real').read_text()=='untouched'
assert (kh/'runs/real').read_text()=='untouched' and not (kh/'runs/proof').exists()
assert (kh/'arm/real').read_text()=='untouched' and not (kh/'arm/proof').exists()
assert (kh/'o/proof').is_file()
report=dict(status='PASS',path=str(out),production_preparation='NOT RUN',
 checks=['absent and private parents pass; public, linked, dangling, file and foreign-owned parents refuse',
 'existing workspace refuses reuse','fresh absolute /tmp/jjyeung and production directory preflight',
 'embedded bytes','unchanged jb/runtime/exports','exact production prefixes and mode p boundary',
 'shell success and staging failure','failed seal cannot pass','real bwrap filesystem isolation'],
 limits=['Local namespace probe omits network namespace only; production script retains it.',
 'Production imports, data, GPU-free partition scheduling and full preparation require Orchard.'])
(H/'evidence/fix8_admission/proof_tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
