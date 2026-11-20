from common import *
import importlib.util,ast
sp=importlib.util.spec_from_file_location('rcj_record',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
sp=importlib.util.spec_from_file_location('record_stage',L/'work/build24m4j/p_tree/launch_s1/b/s.py');S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
F=D/'record_k';F.mkdir();p=F/'pool/p/k/e.json';p.parent.mkdir(parents=True);p.write_bytes(b'{"runtime":true}\n');h=J.sha(p)
x=R.Inputs.__new__(R.Inputs);x.root=F/'node';x.root.mkdir();x.z=J;x.sources={};x.records={};x.archives={};x.stage=S.Stage(F,x.root/'s');x.current={}
x.spec=dict(p_files={'k/e.json':h},uploads=[],pool=str(F/'pool'),p_root='p')
target=x.root/'e.json';x.file(x.need(h,'e'),h,'e',dest=target)
assert target.read_bytes()==p.read_bytes() and x.sources[h]==str(target)
v=J.load(kit('qd')/'k/l.json');spec=J.load(kit('qd')/'k/p.json')
assert v['record']['sha256'] in spec['p_files'].values()
source=(L/'out/rcj/x.py').read_text();assert "inputs.file(inputs.need(v['sha256'], 'e'), v['sha256'], 'e', dest=record)" in source
J.write(D/'RECORD_TEST.json',dict(status='PASS',real_record_pin=v['record'],declared_source='p_files/k/s1_record.json',native_transport_fixture=True,obsolete_original_path_not_opened=True))
print('RECORD RESOLVER PASS')
