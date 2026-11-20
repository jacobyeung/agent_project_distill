from pathlib import Path
import ast, hashlib, importlib.util, json, os, sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4r';T=L/'work/tree_r1c'
sys.path[:0]=[str(D),str(T),str(L/'out/kit_qd/b')]
from common import kit, NAMES, write
import z,rb
base=json.loads((D/'BASELINE.json').read_bytes())
assert {p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}==base['rcj']

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

X=module('rcj_audit',L/'out/rcj/x.py')
F=D/'audit_fixture';F.mkdir()
z.write(F/'env.json',dict(venv=str(F/'v'),scratch=str(F/'g'),paths=[str(F/'f')],mounts=[],record=str(F/'e.json')))
real_load=z.load
class Z:
    @staticmethod
    def checked(path,h):return Path(path)
    @staticmethod
    def load(path):
        if str(path).endswith('k/l.json'):return dict(bwrap=dict(file='/project/community/jjyeung/cp4tk_rt/kit/bwrap',sha256='0'*64))
        if str(path).endswith('k/p.json'):return dict(namespace='/tmp/q_22c714e1',n_root=str(F))
        return real_load(path)

records=[]
for mode in ('b','r'):
    z.write(F/'mode.json',dict(mode=mode))
    for action in ('plan','run','check'):
        with patch.object(X,'attach',return_value=Z),patch.object(X.subprocess,'run',return_value=type('P',(),dict(returncode=0))()) as run:
            assert X.launch(kit('qd'),F,'123',action)==0
        cmd=run.call_args.args[0]
        whole=any(cmd[i:i+3]==['--ro-bind','/','/'] for i in range(len(cmd)))
        assert whole==(mode=='b')
        if mode=='b':assert '--tmpfs' not in cmd
        else:
            assert cmd.index('--remount-ro')>cmd.index('--tmpfs')
        records.append(dict(mode=mode,action=action,command=cmd))
with patch.object(X,'attach',return_value=Z),patch.object(X.subprocess,'run',return_value=type('P',(),dict(returncode=0))()) as run:
    X.rdiff(kit('qd'),F,F)
cmd=run.call_args.args[0]
assert not any(cmd[i:i+3]==['--ro-bind','/','/'] for i in range(len(cmd)))
records.append(dict(mode='r',action='rdiff',command=cmd))
cmd=rb.command(Path('/tmp/q_22c714e1/z/i'),'/tmp/q_22c714e1/z/i/control','/tmp/q_22c714e1/z/s',{},dict(binds=[],executable=sys.executable))
assert not any(cmd[i:i+3]==['--ro-bind','/','/'] for i in range(len(cmd)))
records.append(dict(mode='r/q',action='rb',command=cmd))

files={};changed={}
for name in NAMES:
    k=kit(name)
    current={str(p.relative_to(k)):z.sha(p) for p in k.rglob('*') if p.is_file()}
    changed[name]=sorted(n for n,h in current.items() if h!=base['files'][name][n]['sha256'])
    assert changed[name]==['BUILD.json','SHA256SUMS.txt','b/sc.py']
    assert (k/'b/sc.py').read_bytes()==(kit('qd')/'b/sc.py').read_bytes()
    # The complete native program after mount construction remains byte exact.
    old=(L/'attic/build24m4r'/k.relative_to(L)/'b/sc.py').read_text()
    now=(k/'b/sc.py').read_text()
    assert old[old.index('    start=time.monotonic()'):]==now[now.index('    start=time.monotonic()'):]
    for rel in ('b/sc.py','b/pl.py','b/rb.py','b/x.py','b/pc.py','b/z.py'):
        p=k/rel
        if p.is_file():files[str(p.relative_to(L))]=dict(sha256=z.sha(p),bwrap_lines=[i for i,line in enumerate(p.read_text().splitlines(),1) if 'bwrap' in line or '--tmpfs' in line or '--ro-bind' in line])
for rel in ('x.py','pc.py','ch.py'):
    p=L/'out/rcj'/rel;files[str(p.relative_to(L))]=dict(sha256=z.sha(p),bwrap_lines=[i for i,line in enumerate(p.read_text().splitlines(),1) if 'bwrap' in line or '--tmpfs' in line or '--ro-bind' in line])
files['work/build24m4r/rdiff.py']=dict(sha256=z.sha(D/'rdiff.py'),bwrap_lines=[])
assert z.sha(D/'rdiff.py')==X.RD
write(D/'COMMAND_AUDIT.json',dict(status='PASS',changed=changed,files=files,commands=records,
    findings={
        'sc.py':'All four copies construct a fresh root; /tmp input binds resolve in the caller namespace. Private /tmp and the new root are remounted read-only after installing the writable output.',
        'pl.py':'Delegates reconstruction to rb.command and census to sc.bind; constructs no bwrap command.',
        'rb.py':'Constructs a fresh root with /usr and /etc, then private /tmp; source lookup stays in the caller namespace in modes r and q.',
        'kit_x.py':'Delegates to z.bootstrap; neither file constructs bwrap mounts.',
        'rcj_x.py':'Mode r launch and rdiff use host_root, which omits /tmp and /scratch. Mode b binds / but mounts no tmpfs; its entire source file is unchanged.',
        'pc.py':'Processor children extend rb.command, which already constructs a fresh root. Metadata mounts follow the private metadata tmpfs. The kit publisher constructs no bwrap command.',
        'ch.py':'Constructs no bwrap command.',
        'rdiff.py':'The pinned comparison script constructs no bwrap command; x.rdiff supplies its fresh-root sandbox.'},
    mode_b_byte_identical=True,mode_b_evidence='All rcj files and all kit files except sc.py and its two seal records match the exact input baseline; mode b uses unchanged rb.command, never sc.bind.',
    census_compare_unchanged=True,census_compare_sha256=z.sha(T/'student_pilot/s1_scene_census.py'),native_sc_tail_unchanged=True))
print('Command audit PASS; all rcj bytes and mode-b code unchanged; only sc.py and seals changed in each kit')
