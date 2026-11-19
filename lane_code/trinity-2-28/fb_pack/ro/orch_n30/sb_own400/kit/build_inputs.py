import hashlib,json,pathlib,shutil,tarfile
R=pathlib.Path(__file__).resolve().parents[1]; K=R/'kit'; O=R/'out'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
base=pathlib.Path('/scratch/jjyeung/orch_n30'); sources={}
def copy(src,dst):
 src=pathlib.Path(src);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);sources[str(src)]={'sha256':sha(src),'bytes':src.stat().st_size,'copy':str(dst)}
for src,name in [(base/'sb_scale1/out/NEEDS_INPUTS.json','NEEDS_INPUTS.json'),(base/'k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json','K1_MANIFEST.json'),(base/'so_reads228/out/A10b/package/a/1.json','A10b_INPUTS.json'),(base/'so_reads228/out/A10b/package/a/export.json','EXPORT_PINS.json'),(base/'so_reads228/out/A10b/package/a/6','preparation.tar'),(base/'so_reads228/out/STAGE_PLAN.json','SOURCE_STAGE_PLAN.json'),(pathlib.Path('/scratch/jjyeung/k1/own_170235/logs/a.log'),'STEP544_ENV.log')]:copy(src,K/'inputs'/name)
for name in ('boundaries.py','shard.py','bindings.py','run.py'):
 copy(base/'k1_ops3/kc/k1_build/work/kit_k1a/native_kit'/name,K/'vendor/native_kit'/name)
# Preserve the sealed package byte for byte; do not rebuild its source tree.
copy(base/'so_reads228/out/A10b/package/0.tgz',K/'inputs/A10b_code.tgz')
# Unchanged native modules supply imports required by GPU.own.
native=pathlib.Path('/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2')
for n in ('common.py','read_runtime.py','routed.py','runtime_tree.py'):copy(native/n,K/'vendor/native'/n)
needs=json.loads((K/'inputs/NEEDS_INPUTS.json').read_text());manifest=json.loads((K/'inputs/K1_MANIFEST.json').read_text()); cs={c['canonical']:c for c in manifest['captures']}
train=[]
for n in needs['captures']:
 c=cs[n['canonical']];assert c['k1_split']=='train';assert hashlib.sha256(json.dumps(c,sort_keys=True,allow_nan=False).encode()).hexdigest()==n['capture_sha256'];train.append(c)
save(K/'inputs/TRAIN_CAPTURES.json',{'input_sha256':{str(K/'inputs/K1_MANIFEST.json'):sha(K/'inputs/K1_MANIFEST.json'),str(K/'inputs/NEEDS_INPUTS.json'):sha(K/'inputs/NEEDS_INPUTS.json')},'captures':train})
inputs=json.loads((K/'inputs/A10b_INPUTS.json').read_text());archives=[]
for i,a in enumerate(inputs['archives']):
 if i==1:continue # No G3T forward: its model is unused.
 parts=[]
 for j,p in enumerate(a['parts']):
  name=('s4e0b' if j==0 else 's4e'+str(j)) if i==0 else pathlib.Path(p['path']).name
  target=(K/'inputs/preparation.tar') if i==5 else pathlib.Path('/scratch/jjyeung/orch_n30/reads228/dl')/name
  parts.append({**p,'path':str(target)})
 archives.append({'parts':parts,'sha256':a['sha256'],'expanded_bytes':a['expanded_bytes']})
save(K/'inputs/ARCHIVES.json',{'input_sha256':{str(K/'inputs/A10b_INPUTS.json'):sha(K/'inputs/A10b_INPUTS.json')},'archives':archives})
save(O/'REUSED_FILES.json',{'input_sha256':{p:v['sha256'] for p,v in sources.items()},'files':sources})
missing={'step400':str(base/'cont_ops/work/r1route/out3/A10b'),'step544_missing_shards':[]}
p=base/'b04_e2ehook_m544h/m544/full_weights/full_weights.json';full=json.loads(p.read_text())
for e in full['files']:
 q=p.parent/e['name'];assert not q.exists();missing['step544_missing_shards'].append({'path':str(q),**e})
missing['input_sha256']={str(p):sha(p),str(O/'LOCAL_SEARCH.txt'):sha(O/'LOCAL_SEARCH.txt')}
missing['real_weight_cpu_check']='MISSING';save(O/'LOCAL_WEIGHTS.json',missing)
(R/'STATUS.md').write_text('The frozen bars and 242 original training captures are packaged. The pinned native own-forward method and sealed A10b restore package are preserved with hashes. No complete local 400 or 544 backbone exists; the real-weight CPU comparison is MISSING. The step-544 GPU environment is absent locally.\n')
print('Built inputs:',len(train),'captures;',len(sources),'source files')
