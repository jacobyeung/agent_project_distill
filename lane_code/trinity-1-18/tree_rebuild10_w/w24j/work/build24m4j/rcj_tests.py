from common import *
import importlib.util,tarfile,io,sqlite3
from unittest.mock import patch
F=D/'rcj_test';F.mkdir()
sp=importlib.util.spec_from_file_location('rcj_test_helper',L/'out/rcj/x.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
sp=importlib.util.spec_from_file_location('p_stage',D/'p_tree/launch_s1/b/s.py');S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
# The selected bytes flow through the actual sealed Stage.publish implementation.
x=M.Inputs.__new__(M.Inputs);x.root=F/'node';x.root.mkdir();x.z=J;x.sources={};x.records={};x.archives={};x.stage=S.Stage(F,F/'node/s')
source=F/'a.tar';wanted=b'needed bytes\n';h=hashlib.sha256(wanted).hexdigest()
with tarfile.open(source,'w') as t:
 for name,raw in [('a',wanted),('b',b'unneeded bytes')]:
  member=tarfile.TarInfo(name);member.size=len(raw);t.addfile(member,io.BytesIO(raw))
p=x.member([str(source)],h,'p',['a']);assert Path(p).read_bytes()==wanted
assert set(x.sources)=={h} and not (x.root/'u'/'b').exists()
try:x.member([str(source)],'0'*64,'p',['a'])
except ValueError as e:assert str(e)=='Staged payload differs from its pin';bad=str(e)
else:raise AssertionError('Accepted altered member')
for t in x.archives.values():t.close()
# Publication retains independent native files, complete DB bytes and timings.
root=F/'output';(root/'r').mkdir(parents=True);target=F/'remote/o/123'
J.write(root/'r/receipt.json',dict(count=1));J.write(root/'r/materialization.json',dict(status='PASS'))
J.write(root/'r_imports.json',dict(status='PASS'));J.write(root/'staging.json',dict(seconds=1.25));J.write(root/'build.json',dict(seconds=2.5,status='PASS'))
with sqlite3.connect(root/'r/rows.sqlite') as db:db.execute('CREATE TABLE rows(i INTEGER)')
load=J.load
class Z:
 seal=staticmethod(J.seal);sha=staticmethod(J.sha);write=staticmethod(J.write)
 @staticmethod
 def load(p):return dict(n_root=str(F/'remote')) if str(p).endswith('k/p.json') else load(p)
with patch.object(M,'attach',return_value=Z):M.publish(kit('qd'),root,'123',0)
meta=J.load(target/'db_bytes.json')['files'][0];assert meta['sha256']==J.sha(root/'r/rows.sqlite') and meta['size']==(root/'r/rows.sqlite').stat().st_size and bytes.fromhex(meta['header'])==b'SQLite format 3\0'
assert J.load(target/'timings.json')['staging_seconds']==1.25
# One failed publication cannot suppress the other evidence or timings.
copy=M.shutil.copyfile
def failing_copy(a,b):
 if Path(b).name=='receipt.json':raise OSError('fixture')
 return copy(a,b)
with patch.object(M,'attach',return_value=Z),patch.object(M.shutil,'copyfile',side_effect=failing_copy):
 try:M.publish(kit('qd'),root,'124',1)
 except ValueError as e:assert str(e)=='R1_PUBLICATION_INCOMPLETE'
 else:raise AssertionError('Publication failure hidden')
assert (F/'remote/o/124/materialization.json').is_file() and (F/'remote/o/124/db_bytes.json').is_file() and J.load(F/'remote/o/124/timings.json')['publication_errors']
# Run's finally block publishes before propagating the build failure.
sys.path.insert(0,str(kit('qd')/'b'));import rb
J.write(root/'env.json',dict(paths=[]));J.write(root/'plan.json',dict(paths={},config={}))
seen=[]
with patch.object(M,'attach',return_value=Z),patch.object(rb,'reconstruct',side_effect=ValueError('fixture')),patch.object(M,'publish',side_effect=lambda *a:seen.append(a)):
 try:M.run(kit('qd'),root,'125')
 except ValueError as e:assert str(e)=='fixture' and seen
 else:raise AssertionError('Build failure hidden')
J.write(D/'RCJ_TESTS.json',dict(status='PASS',selected_members_only=True,altered_member_refusal=bad,whole_database_hash=True,independent_publication=True,published_before_raise=True,scheduler_script_checked=True,production_executed=False))
print('RCJ PASS: selective staging; corrupt bytes refused; whole DB hash/header; independent publication before raise')
