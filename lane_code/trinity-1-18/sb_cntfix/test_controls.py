"""CPU regression tests of fail-closed protocol controls; isolated stub ledgers only."""
import concurrent.futures,copy,gzip,json,os,shutil,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'kit/files'))
import count_guard as G
import score_count_pricing as S
R=Path(__file__).resolve().parent;D=R/'out/control_tests_final';D.mkdir(exist_ok=True)
M=R/'out/MANIFEST_R0DEV.json';man=G.manifest(M);c=man['captures'][0];results=[]
def check(name,fn,reject=False):
 try:
  v=fn()
  if reject:raise AssertionError('accepted invalid input')
  assert v is not False
 except (ValueError,FileNotFoundError,FileExistsError,KeyError) as e:
  if not reject:raise
  results.append(dict(name=name,passed=True,rejection=str(e)));return
 results.append(dict(name=name,passed=True))
def save(name,d):
 p=D/name;d=copy.deepcopy(d);d.setdefault('inputs_sha256',{str(M):G.sha(M)});G.write(p,d);return p
check('real registration denied after K1 rejection',lambda:G.register(M,None,False,time.time()+60,60),True)
# No official file is opened: negative fixtures contain synthetic bad fields only.
bad=copy.deepcopy(man);bad['source']['set']='official'
check('official set rejected',lambda:G.manifest(save('bad_set.json',bad)),True)
bad=copy.deepcopy(man);bad['captures'][0]['canonical']='synthetic/not-authorized'
check('unlisted capture rejected',lambda:G.manifest(save('bad_scene.json',bad)),True)
bad=copy.deepcopy(man);bad['captures'][0]['names'][0]['name']='synthetic-unlisted-category'
check('unlisted category rejected',lambda:G.manifest(save('bad_category.json',bad)),True)
bad=copy.deepcopy(man);bad['captures'][0]['frames'][0]['sha256']='0'*64
check('unlisted frame hash rejected',lambda:G.manifest(save('bad_frame.json',bad)),True)
bad=copy.deepcopy(man);bad['captures'][0]['frames'][0]['path']='/tmp/synthetic.png'
check('outside-scratch frame rejected',lambda:G.manifest(save('bad_path.json',bad)),True)
p=D/'untrusted_items.jsonl';p.write_text('{"set":"R0-dev","inputs_sha256":{}}\n')
check('caller supplied dev item file rejected',lambda:G.items(p),True)
p=D/'scratch_escape';p.symlink_to('/tmp',target_is_directory=True)
check('resolved symlink escape rejected',lambda:G.scratch(p),True)
G.LEDGER=D/'ledger';deadline=time.time()+600
check('stub registration',lambda:G.register(M,None,True,deadline,60))
settings=save('changed_settings.json',{'stub':True,'changed':True})
check('changed settings rejected before output read',lambda:G.registered(M,settings,True),True)
check('duplicate registration rejected',lambda:G.register(M,None,True,deadline,60),True)
def consume(_):
 try:G.consume(M,None,True);return 'accepted'
 except FileExistsError:return 'rejected'
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(consume,range(2)))
check('atomic race consumes exactly one look',lambda:sorted(outcomes)==['accepted','rejected'])
check('second output directory cannot get a look',lambda:G.consume(M,None,True),True)
check('stub consumption leaves real category untouched',lambda:not G.ledger(False).exists())
# Validate authentic full stub completion, then exercise individual tampering paths.
source=R/'out/stub_final'/c['canonical'].replace('/','__');base=D/'payload';dest=base/source.name;dest.mkdir(parents=True)
for n in ('teacher.json.gz','DONE.json'):shutil.copy2(source/n,dest/n)
original=G.read(dest/'DONE.json');teacher_bytes=(dest/'teacher.json.gz').read_bytes()
check('valid DONE and payload accepted',lambda:G.validate_done(base,c,M,None,True))
for field in ('canonical','manifest_sha256','contract_sha256','settings_sha256','config_sha256','code_sha256','teacher_sha256','frames','names','stub'):
 bad=copy.deepcopy(original);bad[field]='INVALID';G.write(dest/'DONE.json',bad)
 check('stale DONE '+field,lambda:G.validate_done(base,c,M,None,True),True)
G.write(dest/'DONE.json',original)
check('stub cannot satisfy real provenance',lambda:G.validate_done(base,c,M,None,False),True)
for mode in ('missing-frame','missing-category','wrong-frame-hash','wrong-contract','false-real'):
 teacher=json.loads(gzip.decompress(teacher_bytes))
 if mode=='missing-frame':teacher['frames'].pop('0')
 elif mode=='missing-category':teacher['frames']['0']['phrases'].pop(c['names'][0]['name'])
 elif mode=='wrong-frame-hash':teacher['frame_sha256'][0]='0'*64
 elif mode=='wrong-contract':teacher['contract']['cap']=11
 else:teacher['stub']=False
 (dest/'teacher.json.gz').write_bytes(gzip.compress(json.dumps(teacher).encode()))
 changed=copy.deepcopy(original);changed['teacher_sha256']=G.sha(dest/'teacher.json.gz');G.write(dest/'DONE.json',changed)
 check('payload '+mode,lambda:G.validate_done(base,c,M,None,True),True)
# Test the decision's floating-point boundary without changing the frozen configuration.
original_config=G.config
G.config=lambda:dict(training_decision='ACCEPT_FOR_COMPARISON')
g=dict(N_tool=50.00000001,direct_S1_544=50,frozen_const=50,N_tool_minus_direct_S1_544=[.00000001,.000000001,1])
check('unrounded tiny positive gain accepted',lambda:S.verdict({'large_R0-dev':g})=='ACCEPT')
g['N_tool_minus_direct_S1_544'][1]=0
check('exact zero lower bound rejected',lambda:S.verdict({'large_R0-dev':g})=='REJECT')
check('dev-S1 cannot set primary verdict',lambda:S.verdict({'large_dev-S1':g})=='DIAGNOSTIC_ONLY')
G.config=original_config
G.write(R/'out/CONTROL_TESTS.json',dict(passed=len(results),tests=results,inputs_sha256={str(M):G.sha(M),str(__file__):G.sha(__file__),str(source/'DONE.json'):G.sha(source/'DONE.json'),str(source/'teacher.json.gz'):G.sha(source/'teacher.json.gz'),**G.pins()}))
print(len(results),'control checks passed')
