"""Prune input assets and map retained sources to opaque paths."""
import ast
import hashlib
import json
from pathlib import PurePosixPath as P

DENY=('split','vsi','revsi','scannet','arkit','sam','g3t','depth','distill','qwen','ground','dev','bench','mask','tower','reader','student','teacher','k1','t1')


def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def label_key(k):
    s=k.lower()
    return s in ('gt','label','labels') or 'answer' in s or 'ground_truth' in s or s.startswith('label_')


def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if not label_key(k)}
    if isinstance(v,list):return [clean(x) for x in v]
    return v


def reshape(pf, B, here):
    original=dict(pf)
    rows=json.loads(pf['g/0.json'])['items'];proof=[]
    fields=('id','dataset','scene','question_type','question','options','native','source_frame_indices','room')
    for r in rows:
        old=r['task'];r['task']={k:old[k] for k in fields if k in old}
        proof.append(dict(item_id=r['item_id'],prompt_sha256=digest({k:old[k] for k in fields if k in old}),
                          frame_binding_sha256=r['mapping']['frame_binding_sha256']))
        r['mapping']['task_sha256']=digest(r['task'])
        # Recorded calls and printed answers are unused by this worker.
        for k in list(r):
            if k not in ('item_id','capture','task','source_indices','mapping'):r.pop(k)
    pf['g/0.json']=B.jd(dict(items=rows))
    pf['g/1.json']=B.jd({'0':B.sha(pf['g/0.json'])})
    pf['items/devs1_routed.json']=B.jd(dict(items=[r['task'] for r in rows]))
    # stage_restore reads this object before replacing it with authenticated export pins.
    request='b/work/n13/ret/native/paired/request.json'
    pf[request]=b'{}\n'
    assets={n for n in pf if n.startswith('b/work/meta/') and n.endswith(('FRAMES.json','DENSE_MANIFEST.json','config.json','s1_receipt.json','data_receipt.json'))}
    assets.update([request,'items/devs1_routed.json','g/0.json','g/1.json','g/8.json','tree/student_pilot/tower_scale_rule.json'])
    assets.update(n for n in pf if n.startswith('tree/student_pilot/assets/') or n.startswith('orchard_h10/vendor/') and n.endswith('.json'))
    # Keep the transitive static import graph, including imports inside functions.
    candidates={n:d for n,d in pf.items() if n.endswith('.py') and not n.startswith(('tree/tests/','tree/scripts/','tree/tools/','h1eval/reader_core/'))}
    modules={}
    for prefix in ('tree/','', 'b/'):
        for n in candidates:
            if prefix and not n.startswith(prefix):continue
            s=n[len(prefix):] if prefix else n
            name=s[:-3].replace('/','.')
            if name.endswith('.__init__'):name=name[:-9]
            modules[name]=n
    # File-based imports in the sealed helper modules.
    roots={n for n in candidates if n.startswith(('orchard_h10/','g/')) and n not in ('g/p.py','g/q.py','orchard_h10/build.py','orchard_h10/inventory.py')}
    roots.update(n for n in candidates if n.startswith('b/heads/'))
    roots.update(n for n in candidates if n.startswith('b/work/'))
    roots.update(['8.py','h1eval/h10/parity_adapter.py','b/parity_kit/stage_restore.py','b/parity_kit/build_manifest.py','tree/student_pilot/tower_scale_rule.py'])
    keep=set();todo=list(roots)
    reverse={n:mod for mod,n in modules.items()}
    while todo:
        n=todo.pop()
        if n in keep or n not in candidates:continue
        keep.add(n);mod=reverse.get(n,'');base=mod if n.endswith('/__init__.py') else mod.rpartition('.')[0]
        names=[]
        for node in ast.walk(ast.parse(candidates[n])):
            if isinstance(node,ast.Import):names.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom):
                stem=node.module or ''
                if node.level:
                    bits=base.split('.');stem='.'.join(bits[:len(bits)-node.level+1]+([stem] if stem else []))
                names.append(stem);names.extend(stem+'.'+a.name for a in node.names)
        names.extend('.'.join(mod.split('.')[:i]) for i in range(1,len(mod.split('.'))))
        for name in names:
            if name in modules:todo.append(modules[name])
    retained={n:pf[n] for n in sorted(keep|assets) if n in pf}
    # No data asset may carry labels, including preparation/receipt metadata.
    for n,v in retained.items():
        if n.endswith('.json'):
            value=json.loads(v)
            assert clean(value)==value, 'labelled asset: '+n
    mapping={};edges={};dirs={'': ''}
    # Keep bootstrap infrastructure at its already non-scientific paths.
    for n in retained:
        parts=P(n).parts;old='';new=''
        for i,part in enumerate(parts):
            child='/'.join(filter(None,(old,part)))
            if child not in mapping:
                fixed=parts[0] in ('orchard_h10','g') or len(parts)==1 or i==0 and part in ('b','tree')
                value=part if fixed else 'x'+hashlib.sha256(child.encode()).hexdigest()[:12]+(''.join(P(part).suffixes) if i==len(parts)-1 else '')
                if any(w in value.lower() for w in DENY):raise ValueError('E21 '+value)
                mapping[child]='/'.join(filter(None,(new,value)))
                edges[(new,part)]=value
            old=child;new=mapping[child]
    encoded={}
    for mod,n in modules.items():
        if n not in retained:continue
        # Only logical module names, never b.* or tree.* aliases.
        if mod.startswith(('b.','tree.')):continue
        encoded[mod.encode().hex()]=[mapping[n],n.endswith('/__init__.py'),False]
        bits=mod.split('.')
        for i in range(1,len(bits)):
            parent='.'.join(bits[:i]);key=parent.encode().hex()
            if key not in encoded:
                directory=P(mapping[n]).parents[len(bits)-i-1]
                encoded[key]=[str(directory),True,True]
    # Bare helper imports reached through a sys.path insertion.
    for n in retained:
        if n.startswith(('b/heads/selector/','b/heads/scale/','orchard_h10/vendor/')) and n.endswith('.py'):
            encoded[P(n).stem.encode().hex()]=[mapping[n],False,False]
    output={mapping[n]:v for n,v in retained.items()}
    output['l.py']=(here/'runtime/l.py').read_bytes()
    output['j.py']=(here/'runtime/j.py').read_bytes()
    output['l.json']=B.jd(dict(edges=[[list(k),v] for k,v in edges.items()],modules=encoded))
    # Encode logical names in the map; no descriptive paths are materialized.
    data=json.loads(output['l.json']);data['edges']=[[ [a,b.encode().hex()],v] for (a,b),v in edges.items()]
    output['l.json']=B.jd(data)
    source_proof={mapping[n]:dict(source=n,sha256=B.sha(v)) for n,v in retained.items() if n.endswith('.py') and v==original.get(n) and n.startswith(('b/','tree/','h1eval/'))}
    return output,dict(paths=mapping,sources=source_proof,bindings=proof,removed=sorted(set(original)-set(retained)))
