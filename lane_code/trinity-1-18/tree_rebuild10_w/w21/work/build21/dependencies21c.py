from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c'
groups=('final_focused','edges','producer_edges')
reads=set()
for group in groups:reads.update(json.loads((B/'proofs'/group/'READ_INPUTS.json').read_text()))
rows=[];aliases={};omissions=[]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
selected={}
uploads=json.loads((B/'UPLOADS.json').read_text())
upload_names={x['sha256']:'work/build21/upload/'+x['opaque_name'] for x in uploads['files'] if x['opaque_name'].startswith('u/')}
reused=[]
for text in sorted(reads):
    p=Path(text)
    if not p.is_file():continue
    if p.is_relative_to(L/'work/tree_r1') or p.is_relative_to(L/'work/tmp'):continue
    if any(p.is_relative_to(B/'proofs'/group) for group in groups):continue
    if p.suffix=='.pyc':continue
    if p.suffix in ('.db','.sqlite','.pt','.bin','.safetensors','.png','.npz'):
        omissions.append(dict(path=text,sha256=sha(p),bytes=p.stat().st_size,reason='Generated tensor, database or frame input'));continue
    h=sha(p)
    if h in upload_names:
        aliases[text]=upload_names[h]
        reused.append(dict(path=text,name=upload_names[h],sha256=h,bytes=p.stat().st_size))
        continue
    name=str(p.relative_to(L)) if p.is_relative_to(L) else 'work/build21c/deps/'+h
    if not p.is_relative_to(L):
        for marker in ('/work/','/fixtures/'):
            if marker in text:
                candidate=L/(marker.strip('/')+'/'+text.split(marker,1)[1])
                if candidate.is_file() and sha(candidate)==h:
                    name=str(candidate.relative_to(L));p=candidate;break
    aliases[text]=name
    selected[name]=dict(source=str(p),name=name,sha256=h,bytes=p.stat().st_size)
for directory in [L/'work/base/tree_b01ce449',L/'work/build15/inputs',L/'work/build_n1/inputs',L/'work/n1fix2/inputs',
                  *[L/f'work/build{i}/inputs' for i in range(16,21)]]:
    for p in directory.rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        if p.suffix in ('.db','.sqlite','.pt','.bin','.safetensors','.png','.npz'):continue
        name=str(p.relative_to(L));selected.setdefault(name,dict(source=str(p),name=name,sha256=sha(p),bytes=p.stat().st_size))
for directory in [L/'work/n1fix2',*[L/f'work/build{i}' for i in range(16,21)]]:
    for p in directory.glob('*.py'):
        name=str(p.relative_to(L));selected.setdefault(name,dict(source=str(p),name=name,sha256=sha(p),bytes=p.stat().st_size))
complete_bytes=sum(x['bytes'] for x in selected.values())+sum(x['bytes'] for x in omissions)
for name,entry in list(selected.items()):
    if entry['bytes']>=40_000_000:
        omissions.append(dict(path=entry['source'],sha256=entry['sha256'],bytes=entry['bytes'],reason='Complete fixture closure exceeds the 40 MB addition limit'))
        selected.pop(name)
        aliases={k:v for k,v in aliases.items() if v!=name}
value=dict(schema='build21c-test-inputs-v1',workspace=str(L),groups=list(groups),aliases=aliases,
    files=sorted(selected.values(),key=lambda x:x['name']),bytes=sum(x['bytes'] for x in selected.values()),omissions=omissions,
    reused_uploads=reused,complete_additional_bytes=complete_bytes,standalone=False)
assert value['bytes']<40_000_000
(C/'DEPENDENCIES.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(bytes=value['bytes'],files=len(selected),omissions=omissions),indent=2))
print(json.dumps(sorted(selected.values(),key=lambda x:x['bytes'],reverse=True)[:20],indent=2))
