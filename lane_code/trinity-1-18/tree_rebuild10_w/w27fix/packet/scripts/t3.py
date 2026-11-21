# T3: wiring test. Runs the fixed kit's real pl.plan_payload and its real stage hook (z.copy_resolved_payload
# included) end to end on a small synthetic handover whose model manifest, P config, P preparation receipt and the
# nine non-weight model files are the real bytes. Shims: k/p.json's upload list is emptied (the uploads are not on this
# node) and selection_pin returns a synthetic pin. Everything else is the kit's and the tree's own code.
import sys,os,json,base64,hashlib,io,tarfile
S,KB,HERE,REAL=sys.argv[1:5]
sys.path.insert(0,S);sys.path.insert(1,KB);sys.path.insert(2,HERE)
if os.environ.get('T27_OVL'):sys.path.append(os.environ['T27_OVL'])   # test environment only: adds torchvision
from pathlib import Path
import z,pl,pf,t27probe
from student_pilot.r1_persisted import scope,proof_scope,_paths
from student_pilot.p3_provenance import pinned
kit=Path(KB).parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def out(k,v):print(k,json.dumps(v,sort_keys=True,default=str),flush=True)
NS=Path('/tmp/q_22c714e1');root=NS/'p';root.mkdir();src=NS/'src';src.mkdir()
def put(raw):
    h=sha(raw);p=src/h
    if not p.exists():p.write_bytes(raw)
    return h
def real(h):
    raw=(Path(REAL)/h).read_bytes();assert sha(raw)==h;return put(raw)
J=lambda value:(json.dumps(value,sort_keys=True)+'\n').encode()
cfg0=json.loads(base64.b64decode(json.loads((kit/'k/c.json').read_text())['payload']))
config_pin=dict(cfg0['r1_training']['p_run']['config']);prep_pin=dict(cfg0['r1_training']['p_run']['preparation'])
real(config_pin['sha256']);real(prep_pin['sha256'])
man_pin=json.loads((src/prep_pin['sha256']).read_text())['model'];real(man_pin['sha256'])
manifest=json.loads((src/man_pin['sha256']).read_text())
small=[n for n in manifest['files'] if n.endswith(('.json','.txt','.jinja','.model'))]
for n in small:real(manifest['files'][n])
tok=manifest['files']['tokenizer.json']
shard=b'synthetic shard';heads=b'synthetic heads'
ih=put(J(dict(weight_map={})))
fh=put(J(dict(index=dict(name='model.safetensors.index.json',sha256=ih),files=[dict(name='model-00001-of-00005.safetensors',sha256=sha(shard),bytes=len(shard))])))
ph=put(J(dict(schema='synthetic stream receipt',model=man_pin)));rh=put(J(dict(schema='synthetic routing base')))
sh=put(J(dict(regenerated_sha256='0'*64)));ah=put(J(dict(schema='synthetic artifact')))
pin=lambda h,name:dict(path='/x/'+name,sha256=h)
pins={'artifact':pin(ah,'artifact.json'),'config':config_pin,'preparation':prep_pin,'full_weights':pin(fh,'full_weights.json'),
      'export/model.safetensors.index.json':pin(ih,'model.safetensors.index.json'),
      'export/model-00001-of-00005.safetensors':pin(sha(shard),'model-00001-of-00005.safetensors'),'heads':pin(sha(heads),'heads.pt')}
eh=put(J(dict(schema='p-export-only-v1',step=400,pins=pins)))
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w') as archive:
    for name,raw in (('model-00001-of-00005.safetensors',shard),('heads.pt',heads)):
        info=tarfile.TarInfo(name);info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
part=buffer.getvalue();(src/'part0').write_bytes(part)
entry=lambda h:dict(path=str(src/h),bytes=(src/h).stat().st_size)
small_files={h:dict(entry(h),original='files/s/'+h[:8],member='files/s/'+h[:8]) for h in
             (config_pin['sha256'],prep_pin['sha256'],man_pin['sha256'],tok,ih,fh,ph,rh,ah)}
external=[dict(entry(manifest['files'][n]),sha256=manifest['files'][n]) for n in small if manifest['files'][n]!=tok]
cfg=dict(streams=dict(pose=dict(path='u/'+ph,sha256=ph),routing=dict(path='u/'+rh,sha256=rh)),training_mode='final',
    r1_training=dict(p_run=dict(config=config_pin,preparation=prep_pin),
                     persisted_files={p['sha256']:'/tmp/q_22c714e1/u/'+p['sha256'] for p in pins.values()}))
request=dict(config=None,device='cuda:0',frame_roots=[],memory_gib=180,milestone=400,room_audit=None,
    routing_base=dict(path='u/'+rh,sha256=rh),routing_selection=dict(path='u/'+sh,sha256=sh),staged_pins=[],weights=True)
resolved=dict(schema='q20-resolved-v1',kit_sha256=z.seal(kit),request=request,config=cfg,paths={sh:'/tmp/q_22c714e1/u/'+sh},
    archive=None,receipt=dict(entry(eh),sha256=eh),small_files=small_files,external_metadata=external,
    parts=[dict(path=str(src/'part0'),sha256=sha(part),bytes=len(part))],tar_sha256=sha(part),tar_bytes=len(part),
    model_manifest=man_pin,model_files=manifest['files'],model_root=manifest['root'])
native_load=z.load
def shim_load(path):
    value=native_load(path)
    return dict(value,uploads=[]) if Path(path)==kit/'k/p.json' else value
z.load=shim_load;pl.load=shim_load
pl.selection_pin=lambda _:(dict(path='u/'+sh,sha256=sh),src/sh)
phase=['plan'];native_check=pf.check;log=[]
def recorded_check(cfg,manifest_pin):
    del t27probe.TAPS[:];t27probe.tap()
    folder=pinned(dict(path=str(Path(manifest['root'])/'config.json'),sha256=manifest['files']['config.json'])).parent
    try:native_check(cfg,manifest_pin);result='ok'
    except Exception as error:result=type(error).__name__+':'+str(error)[:200]
    log.append(phase[0]);out('PF_CHECK_CALLED_BY_KIT',dict(phase=phase[0],config_json_pin_folder=str(folder),result=result,
        processor_for_called_with=[dict(directory=t['directory'],named=len(t['processor_files_present'])) for t in t27probe.TAPS]))
    if result!='ok':raise ValueError(result)
pf.check=recorded_check
out('HEAD',dict(kit_seal=resolved['kit_sha256'][:16],root=str(root)))
req,sources,stage=pl.plan_payload(kit,resolved,root)
plan=json.loads((root/'plan.json').read_text());q=root/'q'
out('PLANNED',dict(q_exists_before_staging=q.exists(),rehearsal_folder=sorted(os.listdir(root/'i/y')),sources=len(sources),
    config_pin_paths_unchanged=all(str(v['path']).startswith(str(q/'u'))  for v in (plan['config']['streams']['pose'],plan['config']['r1_training']['p_run']['config']))))
phase[0]='stage'
with scope(sources),proof_scope():
    try:
        stage(plan['entries'],q)
        y=q/'y';names=sorted(os.listdir(y));named={n:manifest['files'][n] for n in small}
        mapping=_paths.get()
        out('STAGED',dict(top=sorted(os.listdir(q)),y=names,y_mode=oct(y.stat().st_mode&0o777),w=sorted(os.listdir(q/'w')),
            y_is_exactly_the_non_weight_manifest_files=names==sorted(small),
            hard_links_of_pool=all(os.stat(y/n).st_ino==os.stat(q/'u'/h).st_ino for n,h in named.items()),
            scope_maps_named_hashes_to_y=all(mapping[h]==str(y/n) for n,h in named.items()),
            other_pins_stay_in_u=mapping[man_pin['sha256']]==str(q/'u'/man_pin['sha256']) and mapping[prep_pin['sha256']]==str(q/'u'/prep_pin['sha256']),
            export_names_stay_in_w=mapping[fh]==str(q/'w/full_weights.json'),
            all_directories_0700=all(p.stat().st_mode&0o777==0o700 for p in [q,*[p for p in q.rglob('*') if p.is_dir()]])))
        pf.check=native_check
        out('RESULT',dict(case='tree witness under the scope the stage hook left entered',**t27probe.witness(plan['config']['r1_training']['p_run']['config'])))
    finally:stage.close()
out('PF_CHECK_PHASES',log)
print('DONE')
