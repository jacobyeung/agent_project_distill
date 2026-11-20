"""Read-only, single-threaded evidence analysis; all output stays beside this file."""
import ast
import base64
import collections
import difflib
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import tarfile

resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
B = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
O = Path(__file__).resolve().parent
D = B / 'w24/work/build24f'
TREE = {'launch': B/'w24c/work/tree_r1', 'run4': D/'rehearsal3/p2/s', 'run5': D/'rehearsal5/p2/s'}
KIT = {'launch': B/'w24c/out/kit_n_go', 'run4': B/'w24/work/build24i/armed_fixture_final',
       'run5': B/'w24/work/build24k/upload/n'}
REQUIRED_KIT = ['b/pc.sh','b/pc.py','b/sr.py','b/z.py','b/u.py','b/t.py','b/e.sh','job.sh']

def sha(raw): return hashlib.sha256(raw).hexdigest()
def digest(v): return sha(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def put(name, obj): (O/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def read(p):
    raw=p.read_bytes()
    return gzip.decompress(raw) if p.suffix=='.gz' else raw
def decoded(p):
    v=json.loads(read(p))
    if isinstance(v,dict) and 'payload' in v:
        raw=base64.b64decode(v['payload']); assert sha(raw)==v['sha256']; return json.loads(raw)
    return v
def inventory(root):
    result={}
    for directory,dirs,names in os.walk(root):
        dirs[:]=sorted(n for n in dirs if n not in ('.git','__pycache__','artifacts'))
        for n in sorted(names):
            p=Path(directory)/n
            assert not p.is_symlink() and p.stat().st_size<16_000_000,p
            result[p.relative_to(root).as_posix()]=p.read_bytes()
    return result
def manifest(raw): return {line.split(None,1)[1].lstrip('*'):line.split(None,1)[0] for line in raw.decode().splitlines() if line.strip()}

# Recover the GO manifest from the preserved non-GO sibling without mutating it.
run5_n=KIT['run5']; envelope=json.loads((run5_n/'k/a.json').read_bytes())
control=base64.b64decode(envelope['payload'])
assert control.count(b'"GO": false')==1
go=control.replace(b'"GO": false',b'"GO": true')
envelope['payload']=base64.b64encode(go).decode();envelope['sha256']=sha(go)
go_raw=json.dumps(envelope,sort_keys=True).encode()
original_manifest=(run5_n/'SHA256SUMS.txt').read_bytes()
recovered=original_manifest.replace(sha((run5_n/'k/a.json').read_bytes()).encode(),sha(go_raw).encode())
assert sha(recovered)==decoded(D/'rehearsal5/RUN_STARTED.json')['kit_seal']
assert recovered==(O/'RUN5_RECOVERED_SHA256SUMS.txt').read_bytes()
put('RECOVERY.json',dict(source_manifest=str(run5_n/'SHA256SUMS.txt'),source_manifest_sha256=sha(original_manifest),
                         source_control=str(run5_n/'k/a.json'),source_control_sha256=sha((run5_n/'k/a.json').read_bytes()),
                         transformation='Decoded control GO false -> true; same envelope encoding; json.dumps(sort_keys=True), no final newline; replace only k/a.json hash in manifest',
                         recovered_control_sha256=sha(go_raw),recovered_manifest_sha256=sha(recovered),
                         authenticated_by=str(D/'rehearsal5/RUN_STARTED.json')))

data={}; verification={}; manifests={}; byte_paths={}
manifest_index=collections.defaultdict(list)
for rec in json.loads((O/'MANIFEST_SEARCH.json').read_text()):
    mp=Path(rec['path'])
    for name,h in manifest(read(mp)).items():
        if name.startswith('b/') or name=='job.sh':manifest_index[(name,h)].append(mp.parent/name)

def kit_bytes(label,p,h):
    candidates=[KIT[label]/p]+manifest_index[(p,h)]
    for candidate in candidates:
        for q in [candidate,Path(str(candidate)+'.gz')]:
            if q.is_file():
                raw=read(q)
                if sha(raw)==h:
                    byte_paths[(label,p)]=str(q)
                    return raw
    raise ValueError(('Missing historical bytes',label,p,h))
for label,root in TREE.items():
    data[label]={'tree':inventory(root),'kit':{}}
    hashes={p:sha(v) for p,v in data[label]['tree'].items()}
    expected=('0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de' if label=='launch'
              else decoded(D/('rehearsal3/code.json' if label=='run4' else 'rehearsal5/code.json'))['tree_sha256'])
    assert digest(hashes)==expected,(label,digest(hashes),expected)
    verification[label]={'tree_root':str(root),'tree_sha256':expected,'tree_files':len(hashes)}
    mf=(O/'RUN5_RECOVERED_SHA256SUMS.txt').read_bytes() if label=='run5' else (KIT[label]/'SHA256SUMS.txt').read_bytes()
    manifests[label]=manifest(mf)
    verification[label].update(kit_bytes_root=str(KIT[label]),kit_manifest_sha256=sha(mf))
    for p,h in manifests[label].items():
        if p.startswith('b/') or p=='job.sh':
            raw=kit_bytes(label,p,h); assert sha(raw)==h,(label,p)
            data[label]['kit'][p]=raw
    tar_name=next(p for p in manifests[label] if p.startswith('k/t_') and p.endswith('.tar'))
    tar_path=KIT[label]/tar_name
    if label=='run4' and not tar_path.exists():
        tar_path=D/'t_57a1f14df5ab60e5.tar'
    assert sha(tar_path.read_bytes())==manifests[label][tar_name]
    tar_hashes={}
    with tarfile.open(tar_path,'r:*') as tf:
        for m in tf:
            assert m.isfile() and m.size<16_000_000 and m.name not in tar_hashes
            tar_hashes[m.name]=sha(tf.extractfile(m).read())
    verification[label].update(kit_tar=str(tar_path),kit_tar_sha256=manifests[label][tar_name],
                               kit_tar_tree_sha256=digest(tar_hashes),kit_tar_equals_executed_tree=tar_hashes==hashes)
    assert tar_hashes==hashes,label
    if label!='launch':
        prep=decoded(D/f'rehearsal{label[-1]}/PREPARED.json')
        assert prep['kit']==sha(mf) and prep['tree']==expected
        verification[label]['recorded_executed_kit']=str(B/'w24/out/kit_n_go')

# Verify the non-GO launch kit's selected executable files and complete tree archive.
nroot=B/'w24c/work/build24/kits/n'; nm=manifest((nroot/'SHA256SUMS.txt').read_bytes())
ncheck={'path':str(nroot),'seal':sha((nroot/'SHA256SUMS.txt').read_bytes()),'executable_differences':[]}
for p in data['launch']['kit']:
    raw=(nroot/p).read_bytes();assert sha(raw)==nm[p]
    if raw!=data['launch']['kit'][p]:ncheck['executable_differences'].append(p)
nt=next(p for p in nm if p.startswith('k/t_'))
assert sha((nroot/nt).read_bytes())==nm[nt]==verification['launch']['kit_tar_sha256']
verification['launch_n']=ncheck
put('VERIFICATION.json',verification)

# Resolve every static import in every reached module, including function-local imports.
# Retain a conservative all-branches closure rather than claim a dynamic execution trace.
edges=[]; dynamic=[]; closures={}; seeds_by_label={}
for label in TREE:
    files={(scope,p):raw for scope,items in data[label].items() for p,raw in items.items()}
    seeds={('kit',p) for p in REQUIRED_KIT}
    seeds|={('tree',p) for p in data[label]['tree'] if re.fullmatch(r'student_pilot/carrier_c1[^/]*\.py',p) or p.startswith('launch_r1/')}
    seeds.add(('tree','launch_r2/persistence.py'))
    seeds_by_label[label]=sorted('/'.join(k) for k in seeds)
    todo=list(seeds);seen=set()
    def add(source,target,line,reason):
        if target in files:
            edges.append(dict(version=label,source='/'.join(source),target='/'.join(target),line=line,reason=reason))
            if target not in seen:todo.append(target)
    def resolve(source,base,line,reason,relative=False):
        bases=[base]
        # Derivgen is placed on sys.path by the source tree's generator adapters.
        if not relative and source[0]=='tree':bases += ['generator/derivgen_v7/'+base]
        for b in bases:
            for p in [b+'.py',b+'/__init__.py']:
                add(source,(source[0],p),line,reason)
                if source[0]=='kit':add(source,('tree',p.removeprefix('b/')),line,reason)
    while todo:
        key=todo.pop()
        if key in seen or key not in files:continue
        seen.add(key);scope,p=key;raw=files[key]
        if p.endswith('.py'):
            tree=ast.parse(raw,filename='/'.join(key))
            parent=PurePosixPath(p).parent
            for ancestor in [parent,*parent.parents]:
                if str(ancestor)=='.':continue
                add(key,(scope,str(ancestor/'__init__.py')),1,'package initializer')
            if p=='launch_r2/distributed.py':
                for helper in ['launch_s1/b/v.py','launch_s1/b/q0.py']:
                    add(key,('tree',helper),15,'parent_launcher finite name tuple')
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):
                    if node.level:
                        root=parent
                        for _ in range(node.level-1):root=root.parent
                        base=str(root.joinpath(*(node.module or '').split('.')))
                    else:base=(node.module or '').replace('.','/')
                    options=[base]+[base+'/'+a.name for a in node.names if a.name!='*']
                    for name in options:
                        resolve(key,name,node.lineno,'from import',bool(node.level))
                        if scope=='kit' and not node.level:resolve(key,'b/'+name,node.lineno,'kit-local from import')
                elif isinstance(node,ast.Import):
                    for a in node.names:
                        resolve(key,a.name.replace('.','/'),node.lineno,'import')
                        if scope=='kit':resolve(key,'b/'+a.name.replace('.','/'),node.lineno,'kit-local import')
                elif isinstance(node,ast.Call):
                    call=ast.unparse(node.func)
                    if any(x in call for x in ['import_module','__import__','spec_from_file_location','run_path','run_module','exec']):
                        dynamic.append(dict(version=label,path='/'.join(key),line=node.lineno,call=ast.unparse(node)[:700]))
                        if call.endswith(('import_module','__import__','run_module')) and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
                            module=node.args[0].value
                            if module.startswith('.'):
                                resolve(key,str(parent/module.lstrip('.').replace('.','/')),node.lineno,'relative literal dynamic module',True)
                            else:resolve(key,module.replace('.','/'),node.lineno,'literal dynamic module')
                elif isinstance(node,ast.Constant) and isinstance(node.value,str):
                    # Explicit file paths used for subprocess/importlib helpers.
                    s=node.value
                    if len(s)<250 and s.endswith(('.py','.sh')):
                        add(key,(scope,s),node.lineno,'literal helper path')
                        add(key,(scope,str(parent/s)),node.lineno,'relative literal helper path')
                        if scope=='kit':add(key,('kit','b/'+s),node.lineno,'kit helper basename')
        elif p.endswith('.sh'):
            for lineno,line in enumerate(raw.decode().splitlines(),1):
                for name in re.findall(r'(?:\$ROOT|\$Q_KIT|\$HX)/([\w/.-]+\.(?:py|sh))',line):
                    add(key,('kit',name),lineno,'shell helper')
    closures[label]=seen
allkeys=set.union(*closures.values())
recorded_closure_checks={}
for label,name in [('run4','rehearsal3'),('run5','rehearsal5')]:
    seal=decoded(D/name/'code.json')
    assert seal['files']=={p:sha(raw) for p,raw in data[label]['tree'].items()}
    assert all(('tree',p) in allkeys and sha(data[label]['tree'][p])==h for p,h in seal['sources'].items())
    recorded_closure_checks[label]=dict(record=str(D/name/'code.json'),source_files=len(seal['sources']),
                                       all_recorded_sources_in_table=True,all_source_hashes_match=True)
put('RECORDED_CLOSURE_CHECKS.json',recorded_closure_checks)
put('DEPENDENCIES.json',dict(method='union of conservative static all-branches closures',seeds=seeds_by_label,edges=edges,dynamic_calls=dynamic))

def affected(raw, ranges, name):
    if not raw:return ['<absent>']
    lines=raw.decode().splitlines();result=set()
    if name.endswith('.py'):
        tr=ast.parse(raw)
        functions=[n for n in ast.walk(tr) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        for start,end in ranges:
            for i in range(start+1,max(start+2,end+1)):
                covering=[n for n in functions if n.lineno<=i<=n.end_lineno]
                result.add(min(covering,key=lambda n:n.end_lineno-n.lineno).name if covering else '<module>')
    else:
        for start,end in ranges:
            current='<shell top level>'
            for line in lines[:start+1]:
                match=re.match(r'\s*([A-Za-z_]\w*)\s*\(\)\s*\{',line)
                if match:current=match[1]
                elif line=='}':current='<shell top level>'
            result.add(current)
    return sorted(result)

(O/'DIFFS').mkdir(exist_ok=True)
rows=[]
for scope,p in sorted(allkeys):
    blobs={v:data[v][scope].get(p) for v in TREE}
    hs={v:sha(raw) if raw is not None else None for v,raw in blobs.items()}
    status='IDENTICAL' if len(set(hs.values()))==1 and None not in hs.values() else 'DIFFERS'
    row=dict(file=scope+'/'+p,sha256=hs,status=status,paths={v:(str(TREE[v]/p) if scope=='tree' else byte_paths[(v,p)]) if blobs[v] is not None else None for v in TREE},
             closure_membership=[v for v in TREE if (scope,p) in closures[v]])
    if status=='DIFFERS':
        summaries=[];text=[f'# {scope}/{p}\n','All diffs read launch C as old and the rehearsal as new. Missing files are explicit.\n']
        for v in ['run4','run5']:
            a=blobs['launch'];b=blobs[v]
            if a==b: text.append(f'{v}: IDENTICAL to launch.\n');continue
            aa=(a or b'').decode().splitlines(keepends=True);bb=(b or b'').decode().splitlines(keepends=True)
            ops=[x for x in difflib.SequenceMatcher(None,aa,bb,autojunk=False).get_opcodes() if x[0]!='equal']
            summary=dict(version=v,removed_lines=sum(j-i for _,i,j,k,l in ops),added_lines=sum(l-k for _,i,j,k,l in ops),
                         launch_functions=affected(a,[(i,j) for _,i,j,k,l in ops],p),
                         run_functions=affected(b,[(k,l) for _,i,j,k,l in ops],p),
                         changed_ranges=[dict(launch=[i+1,j],run=[k+1,l],kind=tag) for tag,i,j,k,l in ops],
                         launch_missing=a is None,run_missing=b is None)
            summaries.append(summary)
            text.append(f"{v}: {summary['removed_lines']} launch lines removed; {summary['added_lines']} rehearsal lines added. Functions: launch {', '.join(summary['launch_functions'])}; rehearsal {', '.join(summary['run_functions'])}.\n")
            text+=['```diff\n',''.join(difflib.unified_diff(aa,bb,fromfile='launch/'+scope+'/'+p,tofile=v+'/'+scope+'/'+p,n=3)),'```\n']
        fn=scope+'__'+p.replace('/','__')+'.md'
        (O/'DIFFS'/fn).write_text('\n'.join(text))
        row['diff_summary']=summaries;row['diff_path']='DIFFS/'+fn
    rows.append(row)
counts=dict(total=len(rows),identical=sum(r['status']=='IDENTICAL' for r in rows),differs=sum(r['status']=='DIFFERS' for r in rows))
put('LOOP_HASHES.json',dict(schema='loop-hashes-24h1-v1',counts=counts,verification=verification,rows=rows))
md=['# Train-loop SHA-256 comparison\n',f"{counts['total']} files: {counts['identical']} IDENTICAL; {counts['differs']} DIFFERS.\n",
    'The file set is a conservative union across all three versions. See DERIVATION.md, PROVENANCE.md, DEPENDENCIES.json and VERIFICATION.json. Run5 kit bytes come from the sealed non-GO sibling; the recovered GO manifest exactly matches the run record. MISSING means the file is absent in that version.\n',
    '| File | Launch kit / tree C SHA-256 | Run4 SHA-256 | Run5 SHA-256 | Result |', '|---|---|---|---|---|']
for r in rows:
    label=f"[{r['file']}]({r['diff_path']})" if r['status']=='DIFFERS' else r['file']
    md.append('| '+label+' | '+' | '.join(r['sha256'][v] or 'MISSING' for v in TREE)+' | '+r['status']+' |')
(O/'LOOP_HASHES.md').write_text('\n'.join(md)+'\n')
print(json.dumps(counts));print('DIFFERS',*[r['file'] for r in rows if r['status']=='DIFFERS'],sep='\n')
print('DYNAMIC',len(dynamic));print('OUTPUT_BYTES',sum(p.stat().st_size for p in O.rglob('*') if p.is_file()))
