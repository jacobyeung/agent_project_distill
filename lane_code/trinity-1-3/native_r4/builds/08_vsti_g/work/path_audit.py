"""Audit the real sealed input paths against the allocation wrapper's binding code."""
import ast, hashlib, json, sys, tarfile
from pathlib import Path
from types import SimpleNamespace
B=Path(__file__).resolve().parents[1];R=B.parents[1]
sys.path.append(str(B/'code'))
from adapter import load,dump,pin,sha
from venue import FSW,AP
PROJECT=Path('/project/community/jjyeung');ROOT=Path('/tmp/a15_PATH_AUDIT')
OBJ=R/'from113/work/obj'

def physical(root,path):
    p=Path(path)
    for logical,folder in ((PROJECT,'project'),(Path(FSW),'fsw'),(Path(AP),'m/ap'),(Path('/scratch/jjyeung'),'sj')):
        if p.is_relative_to(logical):return root/folder/p.relative_to(logical)
    raise ValueError('unregistered staged path: '+str(p))

def absolute(value,trail=''):
    if isinstance(value,dict):
        for k,v in value.items():yield from absolute(v,trail+'.'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):yield from absolute(v,trail+'.'+str(i))
    elif isinstance(value,str) and value.startswith('/'):yield trail,value

def read_bindings(original,model,omit_snapshot=False):
    a=original['assets'];root=ROOT
    runtime=dict(python=dict(path=str(root/'runtime/rwtrain_torch211_cu129/bin/python3.12')),
        import_paths=dict(fla=str(root/'fla/p'),numpy=str(root/'numpy'),kit=str(physical(root,a['kit_import_root'])),
                          anyhost=str(root/'closure'),aliases=str(physical(root,a['aliases_root']))))
    source=(B/'code/o.py').read_text()
    start=source.index('        bindings=[',source.index('def run(config_path):'))
    end=source.index('        # Authenticated runtime overlays',start)
    block='\n'.join(line[8:] for line in source[start:end].splitlines())
    ctx=dict(root=root,original=original,runtime=runtime,Path=Path,FSW=FSW,AP=AP,
             S=SimpleNamespace(physical=physical,PROJECT=PROJECT),load=lambda p:model)
    exec(compile(block,str(B/'code/o.py'),'exec'),ctx)
    bindings=ctx['bindings']
    if omit_snapshot:bindings=[b for b in bindings if str(b[1])!=model['root']]
    bindings += [(root/'run','/r',True),(root/'cache','/cache',True),(root/'tmp','/tmp',True)]
    return bindings,runtime

def build(omit_snapshot=False):
    f=load(B/'out/FAMILY.json');a=f['parent_config']['assets'];docs={};document_hashes={};sources=[]
    # Read small metadata only; never unpack or hash any large checkpoint.
    for role in ('metadata','model'):
        record=next(x for x in a['small_objects'] if x['role']==role)
        archive=OBJ/Path(record['name']).name
        if sha(archive)!=record['sha256']:raise ValueError('real metadata archive pin differs')
        sources.append(pin(archive))
        with tarfile.open(archive) as t:
            for m in t:
                if m.isfile() and m.name.endswith('.json') and m.size<16*1024**2:
                    raw=t.extractfile(m).read()
                    if hashlib.sha256(raw).hexdigest()!=record['members'][m.name]['sha256']:raise ValueError('metadata member differs')
                    logical=str(Path(FSW)/m.name[4:]) if m.name.startswith('fsw/') else str(Path('/scratch/jjyeung')/m.name[3:]) if m.name.startswith('sj/') else None
                    if logical:
                        docs[logical]=json.loads(raw);document_hashes[logical]=hashlib.sha256(raw).hexdigest()
    if sha(B/'out/d.tar')!='9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f':raise ValueError('reference archive differs')
    with tarfile.open(B/'out/d.tar') as t:
        request=json.load(t.extractfile('native/paired/request.json'))
        media=json.load(t.extractfile('d.json'))
    artifact=load(OBJ/'m544_artifact.json')
    if sha(OBJ/'m544_artifact.json')!=request['artifact']['sha256']:raise ValueError('step-544 artifact differs')
    sources += [pin(OBJ/'m544_artifact.json'),pin(B/'out/d.tar')]
    for key in ('config','data_receipt'):
        if document_hashes[request[key]['path']]!=request[key]['sha256']:raise ValueError('request metadata differs')
    cfg=docs[request['config']['path']];receipt=docs[cfg['preparation']['path']]
    for record in (cfg['preparation'],cfg['code'],receipt['model']):
        if document_hashes[record['path']]!=record['sha256']:raise ValueError('nested metadata pin differs')
    model=docs[receipt['model']['path']]
    if receipt['model']!=a['model_manifest']:raise ValueError('model manifest differs')
    if cfg.get('align') or receipt.get('geometry_online') or receipt.get('mdg'):
        raise ValueError('unaudited model-loader branch')
    bindings,runtime=read_bindings(f['parent_config'],model,omit_snapshot)
    records={}
    def add(path,origin,kind='file'):
        p=Path(path)
        if not p.is_absolute() or '..' in p.parts:raise ValueError('noncanonical read path '+str(p))
        key=(str(p),kind);records.setdefault(key,set()).add(origin)
    for k in ('artifact','config','data_receipt'):add(request[k]['path'],'request.'+k)
    for k in ('preparation','code'):add(cfg[k]['path'],'config.'+k)
    add(receipt['model']['path'],'preparation.model')
    add(model['root'],'processor_for / load_model and optional Transformers local-file probes','subtree')
    for name in ('processor_config.json','generation_config.json','added_tokens.json','special_tokens_map.json','chat_template.json'):
        add(Path(model['root'])/name,'optional Transformers local-file existence probe')
    for name in model['files']:add(Path(model['root'])/name,'model.files: tokenizer, processor and base weights')
    for k in ('heads','full_weights'):add(artifact[k]['path'],'step-544 artifact.'+k)
    # Payload manifests are unavailable locally. Their complete child namespace is audited;
    # stage verifies the export inventory, and full_ft requires basename-only shard names.
    add(Path(artifact['full_weights']['path']).parent,'full_ft.read_export index and all shard children','subtree')
    for item in a['depth']:add(item['logical_path'],'load_depth_stage1: heads metadata, encoder copy and point-depth weights')
    for name in a['tree_sources']:add(Path(a['tree_root'])/name,'sealed trainer tree (conservative complete inventory)')
    for p in sorted((B/'code').rglob('*')):
        if p.is_file():add(Path('/x')/p.relative_to(B/'code'),'shipped adapter/import/source verification')
    for n in ('c.json','d.json','e.json','s.json','f.jsonl','g.jsonl','selected_frames_vstibench.json'):add('/d/'+n,'read input or optional existence probe')
    for path,origin,kind in [('/b/frames','media-selected RGB frames','subtree'),('/r/i','prepared input manifests and frame store','subtree'),('/r/v','resume input validation','subtree'),('/r/cell/g/raw','tower receipt and raw NPZ inputs','subtree'),('/r/cell/g/scaled','scale outputs and geometry manifest','subtree'),('/r/p/PROOF.json','read proof receipt','file'),('/r','journals, resume segments, phase receipts and merged return','subtree'),('/a/model.safetensors','frozen tower input','file'),('/a/config.json','frozen tower configuration','file'),('/a/model.safetensors.RECEIPT.json','frozen tower receipt','file')]:add(path,origin,kind)
    for p in runtime['import_paths'].values():add(p,'native runtime import closure','subtree')
    add(Path(runtime['python']['path']).parent.parent,'native Python interpreter and installed packages','subtree')
    for n in ('z.json','w.json'):add(ROOT/n,'allocation runtime/worker spec')
    for n in ('home','temp','cache'):add(ROOT/n,'allocation runtime environment','subtree')
    for n in ('usr','etc','bin','sbin','lib','lib64','sys','opt','run','proc','dev'):
        bindings.append((Path('/')/n,Path('/')/n,n in ('proc','dev')))
        add('/'+n,'venue.namespace system/runtime closure','subtree')
    rows=[]
    for (p,kind),origins in sorted(records.items()):
        matches=[b for b in bindings if Path(p).is_relative_to(Path(b[1]))
                 and not (Path(p).is_relative_to(ROOT) and str(b[1])=='/tmp')]
        match=max(matches,key=lambda b:len(str(b[1]))) if matches else None
        rows.append(dict(path=p,kind=kind,origins=sorted(origins),bound=match is not None,
                         target=str(match[1]) if match else None,physical=str(Path(match[0])/Path(p).relative_to(match[1])) if match else None,
                         writable=match[2] if match else None))
    # Preserve references that are metadata values, not file-open instructions.
    informational=[]
    for name,value in [('config',cfg),('data_receipt',docs[request['data_receipt']['path']]),('preparation',receipt),('artifact',artifact),('media',media)]:
        for field,path in absolute(value,name):
            if (path,'file') not in records and (path,'directory') not in records:
                informational.append(dict(field=field,path=path,role=('source-media provenance only; adapter reads staged /b/frames and does not open original video/receipt locations' if name=='media' else 'provenance/training metadata; read_runtime.prepared compares values without opening training streams; init_artifact is explicitly omitted before loading')))
    unbound=[r['path'] for r in rows if not r['bound']]
    return dict(schema='read-path-audit-v1',passed=not unbound,unbound=unbound,paths=rows,
                bindings=[dict(source=str(s),target=str(t),writable=w) for s,t,w in bindings],
                sources=sources,audit_source=pin(__file__),source_pins={str(p.relative_to(B)):sha(p) for p in [B/'code/o.py',B/'code/a.py',B/'code/engine.py']},
                model_root=model['root'],model_members=list(model['files']),step=artifact['step'],
                informational_references=informational,
                scope='Real pinned metadata and source-level path closure for prepare and read; subtree rows cover runtime-generated filenames and manifest-selected children, not a GPU open trace.',
                unavailable_payload_metadata=['step-544 full_weights.json/index payload','depth heads.json payload'],
                not_checked=['Actual GPU checkpoint load','Orchard mount execution','Payload byte availability beyond the staging attestations'],
                prohibited_loads='No object-grounding selector or VSTI-fitted file is loaded; camera_only policy and geometry preparation are unchanged.')

def assert_audit(value):
    if not value['passed'] or value['unbound']:raise ValueError('unbound read paths: '+repr(value['unbound']))
    if not value['paths'] or any(not r['bound'] for r in value['paths']):raise ValueError('incomplete read audit')

def main():
    result=build();dump(B/'out/PATH_AUDIT.json',result);assert_audit(result)
    print('Real-metadata path audit:',len(result['paths']),'paths/closures; zero unbound')
if __name__=='__main__':main()
