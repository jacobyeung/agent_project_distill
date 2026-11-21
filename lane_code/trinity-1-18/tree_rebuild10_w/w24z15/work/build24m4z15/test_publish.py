import ast,gzip,hashlib,importlib.util,json,os,subprocess,sys,traceback
from pathlib import Path
J=Path.cwd();D=J/'work/build24m4z15';F=D/'publish';F.mkdir()
K=J/'out/kit_qdp'
def module(name):
 spec=importlib.util.spec_from_file_location(name,J/'out'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old,new=module('j7'),module('j8')
source_names=['p/q/b/population.json','p/q/b/indices.json','p/q/b/reader_filters.json','p/q/b/binding.json','p/q/b/receipt.json','p/q/h/receipt.json','p/q/h/config.json','p/q/f.json','p/q/host.json','p/q/RESULT.json','p/q/selection/receipt.json']
node=F/'n';node.mkdir()
for i,n in enumerate(source_names):
 p=node/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'i':i,'value':'A'*1000}))
(node/'ev').mkdir()
# Incompressible candidates exceed 3.5 MB even without the logs.
(node/'p/q/b/z.json').write_bytes(os.urandom(2_600_000))
(node/'p/q/a').mkdir();(node/'p/q/a/z.json').write_bytes(os.urandom(2_600_000))
(node/'ev/z.bin').write_bytes(os.urandom(3_600_000));(node/'ev/zz.txt').write_text('small survives a skipped candidate\n')
logs=[node/'ev'/n for n in ('q.log','r.log','dbb.log','q.steps')]+[F/'s.log',F/'s.err']
for p in logs:p.write_bytes(os.urandom(280_000))
before=F/'before';after=F/'after'
r=subprocess.run([sys.executable,'-I','-s','-B',str(J/'out/j7.py'),'p',str(node),str(before),str(K),'1'],capture_output=True,text=True)
(D/'PUBLISH_BEFORE.log').write_text(r.stdout+r.stderr)
assert r.returncode!=0 and "ValueError: E95" in r.stderr and not list(before.iterdir())
after.mkdir()
for n in ('j2.log','j2.err','j2.log.part','j2.err.part'):(after/n).write_bytes(b'0'*300_000)
v=new.publish(node,after,K,1,*logs[-2:])
assert v['returncode']==1 and len(v['missing'])==0 and len(v['skipped'])>=3
assert all(set(row)>={'name','bytes'} for row in v['skipped'])
assert [x['name'].split('.json')[0] for x in v['files'][:11]]==[f'j7/e{i}' for i in range(11)]
assert [x['source'] for x in v['files'][11:17]]==['ev/q.log','ev/r.log','ev/dbb.log','ev/q.steps',str(logs[-2]),str(logs[-1])]
for row in v['files']:
 raw=(after/row['name']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['stored_sha256']
 if row['name'].endswith('.gz'):raw=gzip.decompress(raw)
 source=Path(row['source']);source=source if source.is_absolute() else node/source
 expected=source.read_bytes()[-262144:] if 'tail_bytes' in row else source.read_bytes()
 assert raw==expected and hashlib.sha256(raw).hexdigest()==row['sha256']
assert any(row['source']=='ev/zz.txt' for row in v['files'])
assert sum(p.stat().st_size for p in after.rglob('*') if p.is_file())<5_000_000
assert v['bytes']<=3_500_000 and v['j2_reserved_bytes']==1_200_000
# E96 remains an all-or-nothing refusal on an occupied destination.
try:new.publish(node,after,K,1)
except ValueError as e:assert str(e)=='E96'
else:raise AssertionError('E96')
for label,kind in [('oversize','large'),('symlink','link')]:
 n=F/label;(n/'ev').mkdir(parents=True);p=n/'ev/x'
 if kind=='large':
  with p.open('wb') as f:f.seek(50_000_000);f.write(b'x')
 else:p.symlink_to(node/'ev/zz.txt')
 t=F/(label+'_out')
 try:new.publish(n,t,K,1)
 except ValueError as e:assert str(e)=='E94'
 else:raise AssertionError('E94')
 assert not list(t.iterdir())
# The bounded tail of a >50 MB log remains useful, without reading its prefix.
n=F/'large_tail';(n/'ev').mkdir(parents=True)
with (n/'ev/q.log').open('wb') as f:f.seek(60_000_000);f.write(b'last\n')
t=F/'large_tail_out';r=new.publish(n,t,K,0)
assert r['files'][0]['bytes']==262144
# More than the old 100 KB manifest cap must not discard fitting receipts.
n=F/'many';(n/'ev').mkdir(parents=True)
for i in range(440):(n/'ev'/f'{i:04}.txt').write_text('x')
r=new.publish(n,F/'many_out',K,0);assert len(r['files'])==440
# Modes m, b, q and shared helper definitions are source-identical.
a,b=(ast.parse((J/'out'/p).read_text()) for p in ('j7.py','j8.py'))
for name in ('sha','load','write','remap','binary','probe'):
 x=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name==name)
 y=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.get_source_segment((J/'out/j7.py').read_text(),x)==ast.get_source_segment((J/'out/j8.py').read_text(),y)
assert ast.dump(a.body[-1])==ast.dump(b.body[-1])
result=dict(status='OK',fixed=11,tails=6,skipped=v['skipped'],payload_bytes=v['bytes'],total_bytes=sum(p.stat().st_size for p in after.rglob('*') if p.is_file()),E94=True,E96=True,unchanged_modes=True,large_tail=True,large_manifest=True)
(D/'PUBLISH_TESTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
