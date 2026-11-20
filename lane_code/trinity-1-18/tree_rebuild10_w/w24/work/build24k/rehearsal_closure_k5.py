"""Enumerate the selected planner's exact closure and supply authenticated fixtures."""
from pathlib import Path
import ast,json,hashlib

def inventory(kit,cfg,resolved,root,J):
    capacity=root.parents[1]/'build24/proofs/capacity'
    workspace=root.parents[2]
    aliases={p.name:str(p) for folder in ('build21','build22')
             for p in (workspace/'work'/folder/'upload/u').glob('*') if p.is_file()}
    known={h:v['path'] for h,v in resolved['small_files'].items()}
    known[resolved['receipt']['sha256']]=resolved['receipt']['path']
    paths={};fields={};missing=[];supplied={}
    def pins(value,field='config'):
        if isinstance(value,dict):
            if 'path' in value and 'sha256' in value:
                h=value['sha256'];paths.setdefault(h,value['path']);fields.setdefault(h,[]).append(field)
            else:
                for k,v in value.items():pins(v,field+'.'+str(k))
        elif isinstance(value,list):
            for i,v in enumerate(value):pins(v,field+'.'+str(i))
    pins(cfg)
    def locate(h,field):
        if h in supplied:return supplied[h]['path']
        candidates=[known.get(h),paths.get(h),aliases.get(h)]
        for candidate in candidates:
            if not candidate:continue
            p=Path(candidate)
            if not p.is_relative_to('/scratch/jjyeung/orch_n30') or not p.is_file():continue
            if J.sha(p)!=h:continue
            if p.suffix=='.sqlite' and not (p.is_relative_to(capacity) or p.is_relative_to(root/fixture)):
                raise ValueError('Production database forbidden:'+str(p))
            supplied[h]=dict(path=str(p),sha256=h,bytes=p.stat().st_size,field=field)
            return str(p)
        raise ValueError('FIXTURE_PIN_UNAVAILABLE:'+h+':'+field)
    # Discover child pin names without changing the native closure's traversal.
    def discover(pin):
        h=pin['sha256'];p=Path(locate(h,'stream-discovery'))
        if p.stat().st_size>50_000_000:return
        with p.open('rb') as f:head=f.read(1)
        if head not in (b'{',b'['):return
        try:value=J.load(p)
        except (ValueError,UnicodeError):return
        if not isinstance(value,dict):return
        children=[value[k] for k in ('database','model','division','dense_indices') if k in value]
        children += [s[k] for s in value.get('sources',[]) if isinstance(s,dict)
                     for k in ('receipt','model','dense_plan','teacher','clips_plan') if k in s]
        for child in children:
            pins(child,'native-child')
            if isinstance(child,dict) and set(child)=={'path','sha256'} and child['sha256'] not in discovered:
                discovered.add(child['sha256']);discover(child)
    discovered=set()
    for pin in cfg['streams'].values():discover(pin)
    # Pool refresh/scene rebuild open these authenticated manifest children.
    queue=[cfg['s1_routing']['selection']];expanded=set()
    while queue:
        pin=queue.pop();h=pin['sha256']
        if h in expanded:continue
        expanded.add(h);p=Path(locate(h,'pool-scene'))
        if p.stat().st_size>2_000_000:continue
        try:value=J.load(p)
        except (ValueError,UnicodeError):continue
        before=set(paths);pins(value,'pool-scene')
        for ch in set(paths)-before:
            cp=Path(locate(ch,'pool-scene'))
            if cp.suffix=='.json':queue.append(dict(path=str(cp),sha256=ch))
    for h in list(paths):
        try:locate(h,fields[h][0])
        except ValueError as e:missing.append(str(e))
    # Execute the exact nested closure once, extracted from the immutable kit.
    path=kit/'b/pl.py';tree=ast.parse(path.read_text())
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='closure')
    sources={};calls=[]
    def need(h,field):
        calls.append(dict(sha256=h,field=field));sources[h]=locate(h,field)
    def load(path):
        value=J.load(path);pins(value,'native-open');return value
    ns=dict(Path=Path,seen=set(),sources=sources,need=need,load=load,output=None,base=cfg['streams']['routing'])
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
    try:ns['closure'](cfg['streams'])
    except ValueError as e:missing.append(str(e))
    J.write(root/'FIXTURE_CLOSURE.json',dict(planner=str(path),planner_sha256=J.sha(path),
        native_closure_calls=1,native_stream_pins=calls,supplied=list(supplied.values()),missing=missing,
        cause='The fixture source map supplies each complete bounded stream and its authenticated child pins.'))
    if missing:raise ValueError(';'.join(missing))
