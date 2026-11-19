"""CPU proof of the tower-and-own camera read kit, without a GPU or model weights.

1. Rehearsal: the operator's rehearsal entry, dispatched as a/5.py dispatches it
   (per-type worker arguments, real tower socket and own head server with stubs).
2. Settings identity: A4's and the fork's prepare() write identical tower settings.
3. Fixture read: the real operator run(), orchard runner, worker_args and launch.run
   decode both arms for all 450 camera items with a replay maker (A4 tower rows,
   step-544 own rows), then the real unpack_return.py and ownread.py --fixture.
4. Strict return: journals with A4's real binding and both arms pass the strict
   scorer; the fixture return is refused by it.
5. Partial return: the strict return without displacement's own rows passes the real
   unpack_return.py, ownread.py refuses it (exit 2, one line), and --allow-partial
   scores it with PARTIAL on every line and no decision.
usage: cpu_proof.py BUILD_DIR FRESH_WORK_DIR
"""
import copy,hashlib,importlib.util,io,json,os,shutil,subprocess,sys,tarfile,time
from pathlib import Path

KIT=Path(__file__).resolve().parents[1]
PY=sys.executable
REPLAY={}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,raw):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_bytes(raw)

def replay_make_real(export_dir,artifact_manifest,items,*,perception_factory=None,device='cpu'):
 table=REPLAY['tower' if perception_factory is None else 'own']
 def generate(item):return copy.deepcopy(table[item['id']]['output'])
 return generate

class Exited:
 def __init__(self,rc):self.rc=rc
 def wait(self):return self.rc

def launcher(argv,env=None,cwd=None,stdout=None,stderr=None):
 """Stand-in for the worker process: entry.py action 2 with the replay maker."""
 from orchard_h10.runner import worker_args
 from h1eval.h10 import launch
 cfg=read(Path(cwd)/argv[-1]);assert cfg['action']==2 and argv[-1]==f"{cfg['type']}0.json"
 args=launch.parser().parse_args(worker_args(cfg)+['--reader-entry','e2e_reader.real:make_real'])
 assert args.arms=='tower,own' and args.modes=='none' and not args.type_journals
 from contextlib import redirect_stdout
 with redirect_stdout(io.TextIOWrapper(stdout,write_through=True)) as log:
  launch.run(args,make_real=replay_make_real);log.flush();log.detach()
 return Exited(0)

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def pack(root,files,out):
 with tarfile.open(out,'w:gz') as t:
  for n,raw in sorted(files.items()):
   m=tarfile.TarInfo(n);m.size=len(raw);t.addfile(m,io.BytesIO(raw))

def unpack(B,archive,dest,token,complete=True):
 receipt=archive.with_suffix('.json')
 receipt.write_text(json.dumps(dict(token=token+'00000001',job='1',synthetic=False,plan_sha256=read(B/'package/0.json')['plan_sha256'],
   archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,complete=complete,status='COMPLETE' if complete else 'FAILED')))
 r=subprocess.run([PY,'-B',str(B/'unpack_return.py'),'--archive',str(archive),'--exit',str(receipt),'--out',str(dest)],capture_output=True,text=True)
 return r

def main():
 build,work=Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve()
 work.mkdir(parents=True);report=dict(build=str(build),work=str(work),python=sys.version.split()[0],steps={})
 B=work/'b';shutil.copytree(build,B,ignore=shutil.ignore_patterns('o_*.sh','BUILD.json'));src=B/'src'
 refs=read(KIT/'ref/REFS.json');A4=Path(refs['tower200']['package']);A4RET=A4/'ret'
 public=read(B/'package/0.json');operator=B/'tower_sequence.py';token=public['token']
 J=work/'job';put(J/'d/e/tiny.txt',b'fixture');put(J/'d/binding.json',b'{}')
 put(J/'d/6.json',(A4RET/'metadata/EXPORT_PIN.json').read_bytes())
 put(J/'d/settings.json',(json.dumps(refs['tower200']['settings'],sort_keys=True,indent=2)+'\n').encode())
 inputs=read(A4RET/'metadata/INPUTS.json')
 base=dict(package=str(src),python=PY,export=str(J/'d/e'),binding=str(J/'d/binding.json'),export_pin=str(J/'d/6.json'),
           settings=str(J/'d/settings.json'),plan_sha256=public['plan_sha256'],
           inputs_sha256=canonical({k:v for k,v in inputs.items() if k!='resume'}),operator_sha256=sha(operator),device='cpu',prefix=[])
 env={k:os.environ[k] for k in ('PATH','HOME','USER') if k in os.environ}
 env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1')

 # 1. Rehearsal entry exactly as a/5.py writes 1.json and dispatches the operator.
 put(J/'a/1.json',json.dumps(dict(action=1,package=str(src),config={**base,'output':str(J/'rh'),'measure_memory':True},rehearsal=True)).encode())
 t=time.time();r=subprocess.run([PY,'-B','-I',str(operator),str(J/'a/1.json')],env=env,capture_output=True,text=True)
 assert r.returncode==0,r.stderr[-3000:]
 rh=read(J/'rh/REHEARSAL.json');mem=read(J/'rh/metadata/MEMORY.json')
 assert [x['type'] for x in rh]==['camera_displacement','camera_rotation','camera_movement_direction'] and mem['fits'] is True
 report['steps']['rehearsal']=dict(passed=True,seconds=round(time.time()-t,1),workers=[dict(type=x['type'],arms=x['args'][x['args'].index('--arms')+1],
   out=x['args'][x['args'].index('--out')+1].split('/metadata/')[-1]) for x in rh],memory_fits=mem['fits'],
   checks=['per-type worker args (arms tower,own; modes none; no --type-journals)','tower socket stub, candidates_argmax','own head server stub: scale 1, move and turn served'])

 # 2. Settings identity against A4's own operator.
 sys.path[:0]=[str(src/'b'),str(src/'tree'),str(src)]
 fork=module('fork_operator',operator);a4op=module('a4_operator',A4/'tower_sequence.py')
 cf=fork.prepare({**base,'output':str(J/'pf')});ca=a4op.prepare({**base,'output':str(J/'pa')})
 same=(J/'pf/metadata/reads/0/metadata/0.json').read_bytes()==(J/'pa/metadata/reads/0/metadata/0.json').read_bytes()
 ret_same=(J/'pf/metadata/reads/0/metadata/0.json').read_bytes()==(A4RET/'metadata/reads/0/metadata/0.json').read_bytes()
 norm=lambda c,root:json.loads(json.dumps(c).replace(str(J/root),'OUT'))
 cf0,ca0=norm(cf[0],'pf'),norm(ca[0],'pa')
 keys=sorted(k for k in set(cf0)|set(ca0) if cf0.get(k)!=ca0.get(k))
 assert same and ret_same and keys==['arms','single_worker','types'],(same,ret_same,keys)
 report['steps']['settings_identity']=dict(passed=True,tower_settings_identical_to_a4_operator=same,identical_to_a4_return_settings=ret_same,
   settings_sha256=sha(J/'pf/metadata/reads/0/metadata/0.json'),worker_config_keys_that_differ=keys)

 # 3. Fixture read through the real operator, runner and launch.run.
 for arm,name in (('tower','tower200'),('own','own544')):
  REPLAY[arm]={json.loads(l)['id']:json.loads(l) for l in (KIT/'ref'/f'{name}.jsonl').read_text().splitlines()}
 from orchard_h10 import runner
 config={**base,'output':str(J/'r')}
 t=time.time()
 summary=fork.run(config,time.time()+5*3600,['0'],runner=lambda cfg,cards,end,prefix:runner.run(cfg,cards,end,prefix=prefix,launcher=launcher))
 assert summary['complete'] and summary['completed']==900 and summary['failure'] is None,summary
 steps=[json.loads(l) for l in (J/'r/metadata/reads/0/STEPS.jsonl').read_text().splitlines()]
 counts={}
 for p in sorted((J/'r/metadata/reads/0/metadata/journals').glob('*/*/items.jsonl')):
  rows=[json.loads(l) for l in p.read_text().splitlines()]
  counts[p.parent.parent.name]={a:sum(r['arm']==a for r in rows) for a in ('tower','own')}
  b=read(p.parent/'environment.json')['binding'];assert b['arms']==['tower','own'] and b['fixture'] is True
 assert counts=={'0':{'tower':150,'own':150},'1':{'tower':150,'own':150},'2':{'tower':150,'own':150}},counts
 report['steps']['fixture_read']=dict(passed=True,seconds=round(time.time()-t,1),summary={k:summary[k] for k in ('completed','expected','complete','failure')},
   worker_starts=[s['type'] for s in steps if s['event']=='start'],journal_rows=counts,identity=read(J/'r/metadata/IDENTITY.json')['reads'][0])

 # 3b. Return archive, real unpack_return.py, ownread.py --fixture.
 files={str(p.relative_to(J/'r')):p.read_bytes() for p in (J/'r').rglob('*') if p.is_file() and 'cache' not in p.relative_to(J/'r').parts}
 files['metadata/INPUTS.json']=(A4RET/'metadata/INPUTS.json').read_bytes();files['metadata/EXPORT_PIN.json']=(A4RET/'metadata/EXPORT_PIN.json').read_bytes()
 pack(J/'r',files,work/'fixture.tgz');u=unpack(B,work/'fixture.tgz',work/'ret_fixture',token)
 assert u.returncode==0,u.stderr[-3000:]
 import ownread
 scored=ownread.main(['--root',str(work/'ret_fixture'),'--out',str(work/'score_fixture'),'--fixture'])
 for kind,v in scored['types'].items():
  assert v['complete'] and v['vs_200_tower']['tower_minus_tower200']['value']==0 and v['vs_544_rows']['own_minus_own544']['value']==0
  reg=ownread.REGISTERED_544[kind];g=v['vs_544_rows']['gap_544']
  assert round(g['value'],2)==reg['own_minus_tower'] and [round(x,2) for x in g['ci95_544rng']]==reg['ci95'],(kind,g,reg)
 try:ownread.score(work/'ret_fixture',B,False);refused=None
 except ValueError as e:refused=str(e)
 assert refused and 'fixture' in refused
 report['steps']['fixture_return']=dict(passed=True,unpack=json.loads(u.stdout.strip().splitlines()[-1]),strict_scorer_refuses_fixture=refused,
   registered_544_reproduced=True,scores=str(work/'score_fixture/ownread.txt'))

 # 4. Strict return: A4's real journal binding with both arms.
 S=work/'strict';files={n:raw for n,raw in files.items() if '/journals/' not in n}
 own=REPLAY['own'];tower=REPLAY['tower']
 for t in ('0','1','2'):
  env_raw=read(A4RET/'metadata/reads/0/metadata/journals'/t/'0/environment.json')
  env_raw['binding']['arms']=['tower','own']
  from orchard_h10.common import ORDER
  ids=[k for k in REPLAY['tower'] if tower[k]['type']==ORDER[int(t)]]
  lines=[json.dumps(tower[k],sort_keys=True) for k in ids]+[json.dumps(own[k],sort_keys=True) for k in ids]
  base_path=f'metadata/reads/0/metadata/journals/{t}/0/'
  files[base_path+'environment.json']=(json.dumps(env_raw,sort_keys=True,indent=2)+'\n').encode()
  files[base_path+'items.jsonl']=('\n'.join(lines)+'\n').encode()
 pack(S,files,work/'strict.tgz');u=unpack(B,work/'strict.tgz',work/'ret_strict',token)
 assert u.returncode==0,u.stderr[-3000:]
 strict=ownread.main(['--root',str(work/'ret_strict'),'--out',str(work/'score_strict')])
 assert all(v['complete'] for v in strict['types'].values()) and not strict['fixture']
 report['steps']['strict_return']=dict(passed=True,scores=str(work/'score_strict/ownread.txt'),
   own_minus_tower={k:round(v['own_minus_tower']['value'],2) for k,v in strict['types'].items()})

 # 5. Partial return: no displacement own rows (300 own / 450 tower). unpack_return.py keeps it; ownread refuses it by default.
 partial=dict(files);name='metadata/reads/0/metadata/journals/0/0/items.jsonl'
 partial[name]=''.join(l+'\n' for l in partial[name].decode().splitlines() if json.loads(l)['arm']!='own').encode()
 pack(S,partial,work/'partial.tgz');u=unpack(B,work/'partial.tgz',work/'ret_partial',token,complete=False)
 assert u.returncode==0,u.stderr[-3000:]
 cmd=[PY,'-B',str(KIT/'ownread.py'),'--root',str(work/'ret_partial'),'--out']
 refused=subprocess.run(cmd+[str(work/'score_partial')],env=env,capture_output=True,text=True)
 assert (refused.returncode==2 and refused.stdout=='' and refused.stderr.count('\n')==1
         and refused.stderr.startswith('ownread refused: Incomplete paired set') and not (work/'score_partial').exists()),refused
 diag=subprocess.run(cmd+[str(work/'score_partial_diag'),'--allow-partial'],env=env,capture_output=True,text=True)
 lines=diag.stdout.splitlines();v=read(work/'score_partial_diag/ownread.json')
 assert diag.returncode==0 and lines and all(l.startswith('PARTIAL') for l in lines),diag
 assert v['partial'] and v['types']['camera_displacement']['own_n']==0 and v['all_within_bar_interval'] is None
 report['steps']['partial_return']=dict(passed=True,unpack=json.loads(u.stdout.strip().splitlines()[-1]),default_exit=refused.returncode,
   default_reason=refused.stderr.strip(),allow_partial_lines=len(lines),allow_partial_lines_marked=sum(l.startswith('PARTIAL') for l in lines),
   scores=str(work/'score_partial_diag/ownread.txt'))
 report['passed']=all(s['passed'] for s in report['steps'].values())
 (work/'CPU_PROOF.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],report=str(work/'CPU_PROOF.json'))))

if __name__=='__main__':
 sys.path.insert(0,str(KIT));main()
