"""Audit the sealed import graph without executing delivered modules or loading weights."""
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def sha(data): return hashlib.sha256(data).hexdigest()
def unpack(data):
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        return {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}
def decode(data):
    value = json.loads(data)
    return json.loads(bytes.fromhex(value['a0'])) if set(value) == {'a0'} else value

# Each external dependency must have Orchard evidence before it can pass admission.
ENVIRONMENT = {
    name: dict(distribution=distribution, proof=proof,
               environment_receipt_sha256='e46a9a59e1de189ae736a5d4e94c7827eabfcfa695057fda9640e8120a54a81a',
               orchard_run='173662', versions='Exact environment bytes pinned; version strings are not returned by T1')
    for name, distribution, proof in [
        ('torch','torch','T1 GPU replay and preparation import torch; same retained model code'),
        ('torchvision','torchvision','T1 preparation imports torchvision and verifies its version against q/env.json'),
        ('transformers','transformers','T1 preparation verifies version against q/env.json and >=5.12; successful native model/processor load'),
        ('scipy','scipy','T1 preparation imports scipy and verifies version against q/env.json'),
        ('packaging','packaging','T1 preparation executes packaging.version.Version'),
        ('numpy','numpy','T1 replay executes NumPy; returned logs/0.log explicitly records 2.3.5'),
        ('PIL','Pillow','T1 parity.bind_item loads the same served PNGs with PIL.Image'),
        ('safetensors','safetensors','T1 native/full-weight restoration and tower weight load use safetensors.torch'),
        ('tokenizers','tokenizers','T1 model processor load imports tokenizers; same retained batches/tokenization code'),
        ('huggingface_hub','huggingface-hub','T1 successful tower imports vggt.models.g3t, whose top level imports PyTorchModelHubMixin'),
    ]
}
from audit_policy import EXCLUSIONS, DYNAMIC

class Imports(ast.NodeVisitor):
    def __init__(self, module, package):
        self.module, self.package = module, package
        self.scope = []
        self.guards = []
        self.rows = []
        self.aliases = {}
    def row(self, node, name, kind, **extra):
        self.rows.append(dict(line=node.lineno, scope='.'.join(self.scope), name=name, kind=kind, guards=list(self.guards), **extra))
    def visit_FunctionDef(self, node):
        self.scope.append(node.name); self.generic_visit(node); self.scope.pop()
    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef
    def visit_Import(self, node):
        for a in node.names:
            self.aliases[a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
            self.row(node, a.name, 'import')
    def visit_ImportFrom(self, node):
        stem = node.module or ''
        if node.level:
            parts = self.package.split('.')
            stem = '.'.join(parts[:len(parts)-node.level+1] + ([stem] if stem else []))
        for a in node.names:
            self.aliases[a.asname or a.name] = stem+'.'+a.name
        self.row(node, stem, 'from', symbols=[a.name for a in node.names])
    def visit_If(self, node):
        guard = ast.unparse(node.test)
        self.visit(node.test)
        self.guards.append(guard)
        for child in node.body: self.visit(child)
        self.guards.pop()
        self.guards.append('not ('+guard+')')
        for child in node.orelse: self.visit(child)
        self.guards.pop()
    def visit_Call(self, node):
        func = ast.unparse(node.func)
        head, sep, tail = func.partition('.')
        func = self.aliases.get(head, head) + (sep+tail if sep else '')
        if func in ('importlib.import_module', '__import__', 'builtins.__import__'):
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                name = node.args[0].value
                if name.startswith('.'):
                    level = len(name)-len(name.lstrip('.'))
                    name = '.'.join(self.package.split('.')[:len(self.package.split('.'))-level+1]+[name.lstrip('.')])
                self.row(node, name, 'literal_dynamic', expression=ast.unparse(node))
            else:
                self.row(node, ast.unparse(node), 'dynamic')
        elif func == 'importlib.util.spec_from_file_location':
            self.row(node, ast.unparse(node), 'file_dynamic')
        self.generic_visit(node)

def audit(delivery=None, overrides=None):
    raw = (HERE/'out/delivery.tgz').read_bytes() if delivery is None else delivery
    outer = unpack(raw); files = unpack(outer['0.tgz'])
    if overrides:
        for key,value in overrides.items():
            if value is None:files.pop(key,None)
            else:files[key]=value
    for name, content in outer.items():
        if name.endswith('.py'): files['outer/'+name]=content
    build = json.loads((HERE/'out/BUILD.json').read_text())
    assert sha(raw) == build['delivery_sha256']
    assert sha(outer['0.tgz']) == build['payload_sha256']
    mapping = {bytes.fromhex(k).decode():v for k,v in decode(files['l.json'])['modules'].items()}
    for name in ('j','l'): mapping[name] = [name+'.py',False,False]
    reverse = {v:k for k,v in build['layout']['paths'].items()}
    aliases = {}
    for name, entry in mapping.items():
        if not entry[2]: aliases.setdefault(entry[0], []).append(name)
    canonical = {}
    for path, names in aliases.items():
        canonical[path] = min(names,key=lambda n:(n.startswith('student_pilot.g3t_vendor.'), n.count('.') == 0, len(n)))
    inventory = {}
    def exports(tree):
        names=set()
        def visit(node):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                names.add(node.name);return
            if isinstance(node,ast.Import):
                names.update(a.asname or a.name.split('.')[0] for a in node.names)
            elif isinstance(node,ast.ImportFrom):names.update(a.asname or a.name for a in node.names)
            elif isinstance(node,ast.Name) and isinstance(node.ctx,ast.Store):names.add(node.id)
            for child in ast.iter_child_nodes(node):visit(child)
        visit(tree);return sorted(names)
    for path, content in files.items():
        if not path.endswith('.py'): continue
        module = canonical.get(path, path[:-3].replace('/','.'))
        package = module if path.endswith('/__init__.py') or mapping.get(module,[None,False])[1] else module.rpartition('.')[0]
        tree=ast.parse(content,filename=path)
        visitor = Imports(module,package); visitor.visit(tree)
        for node in ast.walk(tree):
            if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or node.func.id!='exec' or not node.args:continue
            expr=node.args[0]
            if isinstance(expr,ast.Call) and isinstance(expr.func,ast.Attribute) and expr.func.attr=='decode':expr=expr.func.value
            if isinstance(expr,ast.Call) and ast.unparse(expr.func)=='bytes.fromhex' and expr.args and isinstance(expr.args[0],ast.Constant):
                embedded=bytes.fromhex(expr.args[0].value)
                nested=Imports(module,package);nested.visit(ast.parse(embedded))
                for row in nested.rows:
                    row['embedded_line']=row['line'];row['line']=node.lineno
                    row['embedded_sha256']=sha(embedded);visitor.rows.append(row)
        inventory[path] = dict(module=module,source=reverse.get(path,path),sha256=sha(content),exports=exports(tree),imports=visitor.rows)
    roots = ['g.w','orchard_h10.entry','orchard_h10.job','orchard_h10.prepare','l','j']
    # File-loaded helpers and every vendor member are explicit extra roots.
    extra = [p for p in inventory if reverse.get(p,p).startswith(('tree/student_pilot/g3t_vendor/','b/work/')) or reverse.get(p,p) in ('b/heads/selector/selector_head.py','b/heads/scale/scale_head.py')]
    todo = [(p,'outer numeric launcher/operator') for p in inventory if p.startswith('outer/')] + [(mapping[n][0], 'entry:'+n) for n in roots] + [(p,'file-loaded helper or vendor source pin') for p in extra]
    reached = {}; edges=[]; unresolved=[]; excluded=[]; environment=set()
    def resolve(name, owner, row):
        if name.startswith('@'):
            path=build['layout']['paths'].get(name[1:],name[1:])
            if path not in files:return dict(status='unresolved',reason='file target absent',target=path)
            todo.append((path,owner))
            return dict(status='delivered',target=path)
        entry = mapping.get(name)
        if entry:
            path,is_package,namespace=entry
            if not namespace and path not in files:
                return dict(status='unresolved',reason='sealed module map points to absent file',target=path)
            if namespace:
                if not any(p.startswith(path+'/') for p in files):return dict(status='unresolved',reason='empty namespace',target=path)
            else: todo.append((path,owner))
            for i in range(1,len(name.split('.'))):
                parent='.'.join(name.split('.')[:i]);e=mapping.get(parent)
                if e and not e[2]:todo.append((e[0],owner))
            return dict(status='delivered_namespace' if namespace else 'delivered',target=path)
        if name.split('.')[0] in sys.stdlib_module_names:
            return dict(status='stdlib',target=name,reason='Python standard library; pinned Orchard Python runtime')
        if name.split('.')[0] in ENVIRONMENT:
            environment.add(name.split('.')[0]);return dict(status='environment',target=name,evidence=ENVIRONMENT[name.split('.')[0]])
        return dict(status='unresolved',reason='no delivered module or authenticated environment evidence')
    while todo:
        path,via = todo.pop()
        if path in reached:continue
        if path not in inventory:
            unresolved.append(dict(file=path,reason='root missing'));continue
        reached[path]=via
        item=inventory[path]
        for row in item['imports']:
            edge=dict(file=path,source=item['source'],**row)
            key=(item['source'],row['scope'],row['name'])
            if any(g in ("__name__ == '__main__'", "__name__ == \"__main__\"") for g in row['guards']):
                edge.update(status='excluded',reason='Imported module; standalone __main__ test/CLI guard is false');excluded.append(edge)
            elif key in EXCLUSIONS:
                edge.update(status='excluded',reason=EXCLUSIONS[key]);excluded.append(edge)
            elif item['source']=='l.py' and row['scope']=='install.Finder.find_spec':
                edge.update(status='resolved_loader_map',reason='Targets come only from sealed l.json; every map entry checked, demanded targets walked transitively')
                for target, package, namespace in mapping.values():
                    if not namespace and target not in files:unresolved.append(dict(file=path,target=target,reason='missing loader target'))
            elif row['kind'] in ('dynamic','file_dynamic'):
                targets=DYNAMIC.get((item['source'],row['scope'],row['name']))
                if targets is None:edge.update(status='unresolved',reason='nonliteral module or file loader needs explicit target proof');unresolved.append(edge)
                else:
                    edge['resolutions']=[resolve(n,path,row) for n in targets]
                    edge['status']='resolved_dynamic'
                    if any(r['status']=='unresolved' for r in edge['resolutions']):unresolved.append(edge)
            else:
                edge.update(resolve(row['name'],path,row))
                if edge['status']=='unresolved':unresolved.append(edge)
                if row['kind']=='from' and edge['status'].startswith('delivered'):
                    children=[]
                    for symbol in row['symbols']:
                        child=row['name']+'.'+symbol
                        if child in mapping:
                            resolved=dict(name=child,**resolve(child,path,row));children.append(resolved)
                            if resolved['status']=='unresolved':unresolved.append(dict(file=path,line=row['line'],**resolved))
                        elif symbol!='*':
                            target=edge['target'];declared=inventory.get(target,{}).get('exports',[])
                            if symbol not in declared and '*' not in declared:
                                bad=dict(file=path,source=item['source'],line=row['line'],name=child,reason='from-import symbol is neither a delivered submodule nor a declared module attribute')
                                unresolved.append(bad)
                            else:children.append(dict(name=child,status='declared_attribute',target=target))
                    edge['child_modules']=children
            edges.append(edge)
    parent_path=Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/out2/t1/delivery.tgz')
    assumptions=dict(
        worker_module='g.w',numeric_action=3,arm='own_depth',
        no_segmentation="if any(settings.get(k) for k in ('sam3','selector_head','scale_head'))" in files['g/w.py'].decode(),
        geometry_only_socket="gen.perception.socket=None" in files['g/w.py'].decode(),
        one_prefill_no_decode="counter.prefills!=1 or counter.steps!=0" in files['g/w.py'].decode(),
        source='Pinned g/w.py and orchard_h10/prepare.py; exclusions refer to these fixed job paths')
    if not all(assumptions[k] for k in ('no_segmentation','geometry_only_socket','one_prefill_no_decode')):
        unresolved.append(dict(reason='job-path assumptions changed; review import exclusions'))
    parent_raw=parent_path.read_bytes()
    assert sha(parent_raw)=='ef9575f1eb53d4b603592d6cd94e0bdd07e0a83e69c720c97b4191dadbe4542e'
    old=decode(unpack(parent_raw)['a/1.json']); inputs=decode(outer['a/1.json'])
    assert inputs['archives']==old['archives'] and inputs['files']['env']==old['files']['env']
    retpath=Path('/scratch/jjyeung/orch_n30/cont_ops24_c/cap/t1ret/0.tgz')
    ret_raw=retpath.read_bytes();ret=unpack(ret_raw)
    receipt=decode((retpath.parent/'RETURN_RECEIPT.json').read_bytes())
    assert sha(ret_raw)=='18a13249741b43acbfb8b355d5f042b8383dbe6f0ca5fbe2bd0476444ea5105b'
    assert receipt['returned'] and receipt['job']=='173662'
    assert receipt['channels']['pool']['files']['result.tar.gz']['sha256']==sha(ret_raw)
    parent_files=unpack(unpack(parent_raw)['0.tgz'])
    for path,pin in build['layout']['sources'].items():
        if files.get(path)!=parent_files[pin['source']]:
            unresolved.append(dict(file=path,reason='retained source differs from authenticated T1'))
    environment_proof=dict(parent_delivery_sha256=sha(parent_raw),environment_file_pin=inputs['files']['env'],
        archive_pins=inputs['archives'],python=inputs['python'],env_roots=inputs['env_roots'],
        t1_return_sha256=sha(ret_raw),t1_return_receipt=receipt,t1_complete=decode(ret['COMPLETE.json']),
        inference='Same authenticated archive and environment-receipt pins as successful T1; no local CPU package is used as Orchard evidence')
    not_reached=[dict(file=p,source=v['source'],reason='No import edge from GPU entry, launch/staging roots, file helpers or vendor pin',imports=v['imports']) for p,v in inventory.items() if p not in reached]
    return dict(schema=1,passed=not unresolved,delivery_sha256=sha(raw),delivery_bytes=len(raw),payload_sha256=sha(outer['0.tgz']),
                job_path_assumptions=assumptions,environment_proof=environment_proof, roots=roots,additional_file_roots=extra,files_parsed=len(inventory),retained_sources=len(build['layout']['sources']),
                vendor_files=sum(v['source'].startswith('tree/student_pilot/g3t_vendor/') for v in inventory.values()),
                reachable_files=len(reached),reachable_imports=len(edges),files=inventory,edges=edges,
                reachable_via=reached,environment_packages={n:ENVIRONMENT[n] for n in sorted(environment)},
                unresolved=unresolved,excluded=excluded,unreachable_files=not_reached,
                excluded_unreachable_imports=[dict(file=f['file'],source=f['source'],reason=f['reason'],**row)
                    for f in not_reached for row in f['imports']],
                limitations='Static module closure includes deferred bodies; only enumerated, source-pinned job-inapplicable sites and __main__ guards are excluded. Third-party packages form the boundary, authenticated by unchanged T1 environment inputs and successful T1 operations. No claim of GPU execution in this validation.')

if __name__=='__main__':
    result=audit();(HERE/'out/IMPORT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','files_parsed','reachable_files','reachable_imports')}))
    for r in result['unresolved']:print(r.get('source',r.get('file')),r.get('line'),r.get('scope'),r.get('name'))
    raise SystemExit(not result['passed'])
