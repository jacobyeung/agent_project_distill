"""AST call reachability plus fresh execution coverage for the packaged read."""
import ast
from collections import defaultdict,Counter,deque
from pathlib import Path
import sys,json
import coverage
from coverage.parser import PythonParser
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *

paths=sorted((B/'code').rglob('*.py'));byname={p.stem:p for p in paths}
trees={p:ast.parse(p.read_text()) for p in paths};nodes={};owners={};defs=defaultdict(dict);imports=defaultdict(dict);stars=defaultdict(list);statements={};parents={}

def identity(p,name):return str(p.relative_to(B/'code'))+':'+name

def register(p,node,parent='<module>'):
    key=identity(p,parent);nodes[key]=(p,node);owners[key]=parent
    for child in ast.iter_child_nodes(node):
        if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            name=child.name if parent=='<module>' else parent+'.'+child.name
            defs[p][name]=identity(p,name);parents[identity(p,name)]=key;register(p,child,name)
        elif not isinstance(child,(ast.Lambda,)):
            scan(p,child,parent)

def scan(p,node,parent):
    for child in ast.iter_child_nodes(node):
        if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            name=child.name if parent=='<module>' else parent+'.'+child.name
            defs[p][name]=identity(p,name);parents[identity(p,name)]=identity(p,parent);register(p,child,name)
        else:scan(p,child,parent)

for p,t in trees.items():
    register(p,t)
    parser=PythonParser(filename=str(p));parser.parse_source();statements[p]=set(parser.statements)
    for n in ast.walk(t):
        if isinstance(n,ast.Import):
            for a in n.names:
                if a.name.split('.')[-1] in byname:imports[p][a.asname or a.name]=byname[a.name.split('.')[-1]]
        if isinstance(n,ast.ImportFrom) and (n.module or '').split('.')[-1] in byname:
            module=byname[n.module.split('.')[-1]]
            for a in n.names:
                if a.name=='*':stars[p].append(module)
                else:imports[p][a.asname or a.name]=(module,a.name)

# Ownership gives each statement to its narrowest lexical body; definitions execute in their parent.
line_owner={}
for p,t in trees.items():
    for n in statements[p]:
        matches=[k for k,(q,node) in nodes.items() if p==q and hasattr(node,'lineno') and node.lineno<n<=node.end_lineno]
        line_owner[p,n]=max(matches,key=lambda k:owners[k].count('.')*100000+nodes[k][1].lineno) if matches else identity(p,'<module>')

def shallow(node):
    if isinstance(node,ast.If) and '__name__' in ast.unparse(node.test):return
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            # Definitions and decorators execute; bodies are separate graph vertices.
            for d in getattr(child,'decorator_list',[]):yield from shallow(d)
            continue
        yield from shallow(child)

def resolve(p,name,owner):
    result=set()
    if '.' in name:
        first,tail=name.split('.',1)
        if first in imports[p] and isinstance(imports[p][first],Path):
            q=imports[p][first]
            if tail in defs[q]:result.add(defs[q][tail])
        if first=='self' and '.' in owner:
            full=owner.rsplit('.',1)[0]+'.'+tail
            if full in defs[p]:result.add(defs[p][full])
        # The serving boundary and recorder are dispatched through interfaces.
        for variable,classes in {'boundary':['NativeBoundary','Boundary'],'guard':['Recorder'],'budget':['Budget']}.items():
            if first==variable:
                for q in paths:
                    for cls in classes:
                        full=cls+'.'+tail
                        if full in defs[q]:result.add(defs[q][full])
    else:
        scopes=owner.split('.')
        for i in range(len(scopes),-1,-1):
            full='.'.join(scopes[:i]+[name]) if i else name
            if full in defs[p]:result.add(defs[p][full]);break
        imported=imports[p].get(name)
        if isinstance(imported,tuple):
            q,n=imported
            if n in defs[q]:result.add(defs[q][n])
        for q in stars[p]:
            if name in defs[q]:result.add(defs[q][name])
    return result

edges=defaultdict(set)
for key,(p,node) in nodes.items():
    owner=owners[key]
    for n in shallow(node):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
            for name in names:
                if name.split('.')[-1] in byname:edges[key].add(identity(byname[name.split('.')[-1]],'<module>'))
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load):edges[key]|=resolve(p,n.id,owner)
        if isinstance(n,ast.Attribute):
            try:edges[key]|=resolve(p,ast.unparse(n),owner)
            except ValueError:pass
    if isinstance(node,ast.ClassDef):
        # A reached class instantiation can dispatch any of its methods.
        edges[key]|={v for name,v in defs[p].items() if name.startswith(owner+'.')}
# Function objects assigned to decoder hooks, guards and try/callback arguments remain reachable.
for key in list(nodes):
    if owners[key]=='<module>' or isinstance(nodes[key][1],ast.ClassDef):continue
    edges[key]|={child for child,parent in parents.items() if parent==key and not isinstance(nodes[child][1],ast.ClassDef)}
# Audited dynamic edges: names resolved by the decoder, import machinery or exec parity bridge.
dynamic={
 'engine.py:NativeBoundary.parity':['nomdg.py:<module>'],
 'engine.py:initialize':['gravity_guard.py:Recorder','gravity_guard.py:install'],
 'policy.py:camera_only':['policy.py:camera_only.respond','policy.py:camera_only.extra_tail'],
 'proof.py:preparation_check':['geometry.py:prepare_capture','engine.py:prepare_geometry'],
 'o.py:run':['a.py:main','p.py:main','native_stage.py:stage','native_stage.py:namespace','orchard_results.py:publish','native_job.py:card','native_job.py:environment','orchard_job.py:storage_proof','native_bootstrap.py:main'],
}
for source,targets in dynamic.items():
    for target in targets:
        mod,fn=target.split(':',1);q=byname.get(mod.removesuffix('.py'))
        if q and identity(q,fn) in nodes:edges[source].add(identity(q,fn))
roots=[identity(byname[n],'main') for n in ('entry','a','p','o','pixels')]
roots += [identity(byname[n],'<module>') for n in ('entry','a','p','o','pixels')]
reachable=set();queue=deque(roots)
while queue:
    k=queue.popleft()
    if k in reachable:continue
    reachable.add(k);queue.extend(edges[k]-reachable)

# Coverage establishes dynamic reachability only within the job graph's modules. Tests cannot make dormant CLIs reachable.
measured=defaultdict(set);evidence=[]
for name in sys.argv[1:]:
    path=Path(name)
    if not path.is_file():continue
    data=coverage.CoverageData(basename=str(path));data.read();evidence.append(pin(path))
    for filename in data.measured_files():
        p=Path(filename)
        if p in trees:measured[p].update(data.lines(filename) or [])
# Rehearsal-observed owners add dynamic edges missed by static attribute resolution.
observed=set()
for name in sys.argv[1:]:
    if not any(x in name for x in ('rehearsal','cli_')) or not Path(name).is_file():continue
    data=coverage.CoverageData(basename=name);data.read()
    for filename in data.measured_files():
        p=Path(filename)
        if p in trees:
            observed.update(line_owner[p,n] for n in data.lines(filename) or [] if (p,n) in line_owner)
queue=deque(observed-reachable)
while queue:
    key=queue.popleft()
    if key in reachable:continue
    reachable.add(key);queue.extend(edges[key]-reachable)
# The parity bridge executes a bounded slice of nomdg.run, not its old full-read command.
parity_lines=set();np=byname['nomdg'];n=next(n for n in trees[np].body if isinstance(n,ast.FunctionDef) and n.name=='run')
start=next(x.lineno for x in n.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='probe' for t in x.targets))
end=next(x.end_lineno for x in n.body if isinstance(x,ast.Assign) and ast.unparse(x.targets[0])=="trace_state['probe']")
parity_lines=set(range(start,end+1))

# Explicit phase boundaries; these classify where execution happens, not whether it passed.
gpu={
 'engine':{'NativeBoundary','tower'},'proof':{'run','preparation_check'},
 'perception':{'generate','load_geometry','session'},'read_runtime':{'load_model','prepared','version_stamp'},
 'geometry':{'prepare_capture','prepare'},'native_bootstrap':{'configure','main'},
}
venue={'a','p','o','orchard','venue','proof_stage','paths','orchard_stage','orchard_results','orchard_job','native_stage','native_job','native_bootstrap','chain_save','stdout_transfer','native_common','native_metrics','native_pin_graph','native_worker','native_launcher','orchard_launcher'}
conditions={}
for p,t in trees.items():
    for n in ast.walk(t):
        if isinstance(n,ast.If):
            for branch,label in [(n.body,ast.unparse(n.test)),(n.orelse,'not ('+ast.unparse(n.test)+')')]:
                if any(isinstance(v,(ast.Raise,ast.Return)) for v in branch):
                    for c in branch:
                        for line in range(c.lineno,c.end_lineno+1):conditions[p,line]=label
        if isinstance(n,ast.ExceptHandler):
            for line in range(n.lineno,n.end_lineno+1):conditions[p,line]='exception '+(ast.unparse(n.type) if n.type else 'BaseException')

rows=[];unreachable=[];counts=Counter();new_counts=Counter();files=[]
for p in paths:
    live={n for n in statements[p] if line_owner[p,n] in reachable or (p==np and n in parity_lines)}
    guarded={line for n in ast.walk(trees[p]) if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test) for line in range(n.lineno,n.end_lineno+1)} if p.stem not in ('entry','a','p','o','pixels') else set()
    live-=guarded
    dead=statements[p]-live;miss=live-measured[p]
    if dead:unreachable.append(dict(origin='inherited' if (R/'work/c8r/code'/p.relative_to(B/'code')).is_file() or p.name in ('s0.py','s1.py','s2.py','s3.py') else 'operator or fixture helper',file=str(p.relative_to(B)),lines=sorted(dead),count=len(dead),owners=sorted({line_owner[p,n] for n in dead})))
    groups=defaultdict(list)
    for line in sorted(miss):
        owner=owners[line_owner[p,line]];category='UNEXPLAINED';why='Reachable statement has no execution or phase classification.'
        if p.stem in venue:category='venue staging (Trinity or Orchard)';why='Allocation, namespace, asset staging, phase supervision or return path: '+owner
        if any(owner==n or owner.startswith(n+'.') for n in gpu.get(p.stem,set())) or (p==np and line in parity_lines):
            category='GPU decode';why='Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: '+owner
        if p.stem=='engine' and any(isinstance(n,ast.If) and ast.unparse(n.test)=='not boundary.synthetic' and any(c.lineno<=line<=c.end_lineno for c in n.body) for n in ast.walk(trees[p])):
            category='GPU decode';why='The real boundary invokes prompt/cache/head parity before scoring.'
        if p.stem=='entry' and line==6:category='venue staging (Trinity or Orchard)';why='READ_OVERLAY is set by the production namespace before numerical imports.'
        if (p,line) in conditions:
            category='error branch (with condition)';why=conditions[p,line]
        groups[category,why].append(line);counts[category]+=1
        old=R/'work/c8r/code'/p.relative_to(B/'code')
        if p.name not in ('s0.py','s1.py','s2.py','s3.py') and (not old.is_file() or old.read_bytes()!=p.read_bytes()):new_counts[category]+=1
    for (category,why),lines in groups.items():rows.append(dict(file=str(p.relative_to(B)),lines=lines,count=len(lines),classification=category,evidence=why))
    files.append(dict(file=str(p.relative_to(B)),sha256=sha(p),reachable=len(live),executed=len(live&measured[p]),unexecuted=len(miss),unreachable=len(dead)))

def compact(lines):
    result=[]
    for line in lines:
        if result and line==result[-1][-1]+1:result[-1].append(line)
        else:result.append([line])
    return ','.join(str(x[0]) if len(x)==1 else str(x[0])+'-'+str(x[-1]) for x in result)
value=dict(scope='AST reachability from entry commands and their allocation phases; dormant inherited CLIs excluded',roots=roots,
    dynamic_edges=dynamic,reachable_functions=sorted(reachable),edges={k:sorted(v) for k,v in edges.items() if k in reachable},
    rehearsal_observed_owners=sorted(observed),coverage=evidence,counts=dict(counts),v1_v1b_counts=dict(new_counts),files=files,rows=rows,unreachable=unreachable,
    passed=new_counts['UNEXPLAINED']==0)
dump(B/'out/UNEXECUTED.json',value)
text=['The census combines an AST call graph with fresh test and rehearsal coverage. `out/UNEXECUTED.json` records roots, dynamic edges, source hashes and coverage pins.','',
      'A classified line has not passed a GPU or venue check. Dormant inherited entry points are outside this read and listed separately.','',
      '| File | Unexecuted lines | Class | Evidence or condition |','|---|---|---|---|']
for r in rows:text.append(f"| `{r['file']}` | {compact(r['lines'])} | {r['classification']} | {r['evidence'].replace('|','/')} |")
text+=['','Unreachable inherited code cannot execute from the read roots. Operator and fixture helpers have separate entry points outside that scope.','','| File | Origin | Executable lines |','|---|---|---:|']
for r in unreachable:text.append(f"| `{r['file']}` | {r['origin']} | {r['count']} |")
text.insert(1,f"V1/V1b unexplained reachable lines: {new_counts['UNEXPLAINED']}. Inherited unexplained reachable lines: {counts['UNEXPLAINED']-new_counts['UNEXPLAINED']}. GPU, venue and error counts: {dict(counts)}.")
(B/'out/UNEXECUTED.md').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(counts=counts,new=new_counts,unreachable=sum(x['count'] for x in unreachable))))
for r in rows:
    if r['classification']=='UNEXPLAINED':print(r['file'],compact(r['lines']))
