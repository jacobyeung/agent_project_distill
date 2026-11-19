import os
"""Build the two opaque kits from the build-22 VQA bindings."""
from pathlib import Path
import ast,base64,hashlib,json,shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24';T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'));B=L/'work/build22'
sys.path[:0]=[str(D),str(T),str(L/'work/build21')]
import joblib as J
from student_pilot.p3_provenance import digest,file_pin,source_files
from student_pilot.source_seal import inventory,archive,check_archive,create
from launch_r2.build import capsule_json

def cap(k,name,value):(k/name).write_bytes(capsule_json(value))
def retire(path,name):
    target=L/'attic/build24'/name;index=0
    while target.exists():
        index+=1;target=L/'attic/build24'/(name+'_'+str(index))
    path.rename(target)
def reseal(k):
    files={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
    (k/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))
    record=J.load(k/'BUILD.json');record.update(GO=False,kit_sha256=J.seal(k));cap(k,'BUILD.json',record)
    return J.seal(k)

def main():
    (D/'inputs').mkdir(exist_ok=True);(D/'kits').mkdir(exist_ok=True)
    cfg=J.load(B/'kits/q/k/n.json');card=J.load(B/'inputs/mix.json')
    for cell in card['cells']:
        if cell['stream']=='routing':cell.update(rows_per_step=0,ceiling_rows_per_step=0)
    for name in ('coverage_distance','coverage_units','camera_wording'):
        if not any(c['type']==name for c in card['cells']):card['cells'].append(dict(type=name,stream='routing',rows_per_step=0,ceiling_rows_per_step=0))
    card['cells'].append(dict(type='routing_base',stream='routing',rows_per_step=64))
    mix=J.write(D/'inputs/mix.json',card)
    catalog=J.load(B/'inputs/row_sources.json')
    catalog={k:v for k,v in catalog.items() if k in ('room','room_programs_excluded')}
    sources=J.write(D/'inputs/row_sources.json',catalog)
    real=L.parent/'ext/m400real';run=J.load(real/'r.json');runtime=J.load(real/('files'+run['config']['path']))
    base=runtime['streams']['routing'];base_path=real/('files'+base['path'])
    assert J.sha(base_path)=='ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984'
    cfg['r1_training'].update(routing_slices='deferred_first_boundary',row_sources=sources,row_slice_inputs={},mix=mix)
    cfg['r1_training'].pop('routing_inputs',None);cfg['r1_training'].pop('source_membership',None)
    cfg['streams']['routing']=base;cfg['s1_routing']=runtime['s1_routing']
    audit=J.load(B/'inputs/room_audit.json');audit.update(row_sources=sources,slices={})
    room=J.write(D/'inputs/room_audit.json',audit);cfg['r1_training']['room_audit']=room
    pop=J.write(D/'inputs/population.json',dict(schema='r1-population-v1',complete=False,after_all_filters=False,
        card_sha256=mix['sha256'],counts={c['type']:0 for c in card['cells']},evidence=[mix,base]))
    idx=J.write(D/'inputs/indices.json',dict(population_sha256=pop['sha256'],cells={c['type']:[] for c in card['cells']}))
    cfg['r2_sampling']=dict(schema='r1-sampling-v1',card=mix,population=pop,indices=idx)
    cfg['world_size']=4
    J.write(D/'inputs/config.json',cfg)
    original=J.load(B/'UPLOADS.json');available={};uploads={};reasons={}
    for item in original['files']:
        if not item['opaque_name'].startswith('u/'):continue
        p=B/'upload'/item['opaque_name']
        if not p.is_file():p=Path(item['local_path'])
        if not str(p).startswith(str(L.parent)):continue
        if p.is_file() and J.sha(p)==item['sha256']:available[item['sha256']]=p
    for p in (D/'inputs').glob('*.json'):available[J.sha(p)]=p
    available[J.sha(base_path)]=base_path
    visited=set()
    def visit(value,reason):
        if isinstance(value,dict):
            h=value.get('sha256')
            if h in available:
                reasons.setdefault(h,[]).append(reason)
                if h not in visited:
                    visited.add(h);p=available[h]
                    uploads[h]=dict(local_path=str(p),opaque_name='u/'+h,sha256=h,bytes=p.stat().st_size,needed_minimal=True)
                    if p.stat().st_size<30_000_000:
                        try:nested=J.load(p)
                        except (ValueError,UnicodeError):nested=None
                        if nested is not None:visit(nested,'closure:'+h)
            for key,item in value.items():visit(item,reason+'/'+str(key))
        elif isinstance(value,list):
            for item in value:visit(item,reason)
    visit(cfg,'config');visit(room,'room')
    spec=J.load(B/'kits/q/k/p.json')
    # P's opaque staging map still uses this authenticated prerequisite set.
    visit(J.load(B/'kits/q/k/l.json'),'p_staging')
    for h in spec['p_files'].values():visit(dict(sha256=h),'p_files')
    visit(spec['p_kit_config'],'p_kit_config')
    for h in spec['p_sources'].values():
        if h.startswith('u/'):visit(dict(sha256=h[2:]),'p_sources')
    camera='e3c72962e3fd774c7e15fa1e4aeae1b6642264bf4f3cf54b9e350b8d7bfb9707'
    assert camera not in uploads, reasons.get(camera)
    files=inventory(T);tree=digest(files)
    J.write(L/'out/TREE_SEAL.json',dict(tree_sha256=tree,files=len(files)))
    J.write(D/'TREE_FILES.json',files)
    records={}
    for name,step in (('q',400),('n',600)):
        k=D/'kits'/name
        if k.exists():
            retire(k,'kit_'+name+'_'+J.seal(k)[:8])
        shutil.copytree(B/'kits/q',k)
        control=J.load(k/'k/a.json');old=k/control['source']['path'];retire(old,name+'_'+old.name)
        target=k/'k'/('t_'+tree[:16]+'.tar');archive(T,target,files,compress=True);check_archive(file_pin(target),files)
        source=dict(path=str(target.relative_to(k)),sha256=J.sha(target),tree_sha256=tree)
        closure={str(p.relative_to(T)):J.sha(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])}
        cap(k,'k/7.json',dict(schema='c1-sealed-source-v1',commit='sha256:'+tree,tree_sha256=tree,files=files,
            archive={x:source[x] for x in ('path','sha256')},sources=closure,operation_sources=closure))
        sp=J.load(B/'kits/q/k/p.json');ns=sp['namespace']
        code=create(T,target,closure,{},archive_path=ns+'/t.tar');raw=(json.dumps(code,sort_keys=True,indent=2)+'\n').encode()
        (k/'k/c0.json').write_bytes(json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())).encode())
        sp.update(step=step,code_sha256=hashlib.sha256(raw).hexdigest(),room_sha256=room['sha256'],
            uploads=[{a:b for a,b in v.items() if a not in ('local_path','needed_minimal')} for v in uploads.values()],
            pin_paths={h:ns+'/u/'+h for h in uploads})
        if step==600:sp.update(milestone='h_6ed2c7aa/m600',handover=None)
        launch_cfg={**cfg,'r1_training':{**cfg['r1_training'],'proof_mode':'train'}} if step==600 else cfg
        cap(k,'k/p.json',sp);cap(k,'k/n.json',launch_cfg)
        portable=J.load(k/'k/c.json')
        # Preserve the established relocation of every non-routing input.
        portable['r1_training'].update(routing_slices='deferred_first_boundary',row_slice_inputs={},
            row_sources=dict(sources,path='u/'+sources['sha256']),mix=dict(mix,path='u/'+mix['sha256']),room_audit=dict(room,path='u/'+room['sha256']))
        portable['r1_training'].pop('routing_inputs',None);portable['r1_training'].pop('source_membership',None)
        if step==600:portable['r1_training']['proof_mode']='train'
        portable['streams']['routing']=dict(base,path=ns+'/u/'+base['sha256'])
        portable['r2_sampling']={key:dict(v,path=ns+'/u/'+v['sha256']) if isinstance(v,dict) else v for key,v in cfg['r2_sampling'].items()}
        portable['code']=dict(path='k/7.json',sha256=J.sha(k/'k/7.json'));cap(k,'k/c.json',portable)
        cap(k,'k/s.json',dict(entries={'u/'+mix['sha256']:dict(payload=base64.b64encode((D/'inputs/mix.json').read_bytes()).decode(),sha256=mix['sha256'])},unresolved=[]))
        control['source']=source;control['GO']=False;cap(k,'k/a.json',control)
        report=J.load(k/'k/8.json');report['report_sha256']=mix['sha256'];cap(k,'k/8.json',report)
        host=J.load(k/'k/h.json');host.pop('routing_inputs',None);host['steps']=[s for s in host['steps'] if s!='r1_routing.compose_native'];cap(k,'k/h.json',host)
        request=J.load(k/'k/r.json');request.pop('routing_inputs',None);request.update(routing_base=base,milestone=step);cap(k,'k/r.json',request)
        (k/'b/z.py').write_bytes((D/'joblib.py').read_bytes())
        build=J.load(k/'BUILD.json');build.update(GO=False,source_seal=tree)
        if step==600:
            script=(k/'job.sh').read_text().replace('--partition=general','--partition=advanced').replace('--gres=gpu:1','--gres=gpu:4')
            (k/'job.sh').write_text(script)
            build['resource_request'].update(partition='advanced',gpus=4,ranks=4)
        cap(k,'BUILD.json',build);seal=reseal(k)
        all_uploads=list(uploads.values())+[dict(local_path=str(p),opaque_name=name+'/'+str(p.relative_to(k)),bytes=p.stat().st_size,sha256=J.sha(p),needed_minimal=True) for p in k.rglob('*') if p.is_file()]
        J.write(D/('UPLOADS_'+name+'.json'),dict(files=all_uploads,total_bytes=sum(x['bytes'] for x in all_uploads)))
        records[name]=dict(step=step,tree_seal=tree,kit_seal=seal,GO=False,upload_files=len(all_uploads),upload_bytes=sum(x['bytes'] for x in all_uploads))
    J.write(D/'KIT.json',records);J.write(D/'UPLOAD_REASONS.json',reasons)
    print(json.dumps(records,indent=2))
if __name__=='__main__':main()
