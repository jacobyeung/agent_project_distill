from pathlib import Path
import hashlib,json,re
POOL='/project/community/jjyeung/okh7'
OLD='/project/community/jjyeung/distill/okit'
MODEL='/project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar'
ALIASES={OLD:POOL+'/l_94a76bda',MODEL:POOL+'/l_3d48eea0'}
ENV={'STUDENT_ORCHARD':'Q_E1','STUDENT_SLURM_SITE':'Q_E2','STUDENT_MODEL_ROOT':'Q_E3','STUDENT_FRAME_ROOT_MAP':'Q_E4','R1_STUDENT_HEX':'Q_E5','STUDENT_PRESERVE_CHECKPOINTS':'Q_E6'}
# These exceptions describe authenticated FILE CONTENT. They are never emitted as
# wrapper names, paths, arguments, environment entries or log lines. Each selector
# is exact; no payload, dictionary, arbitrary hash key or user-added field is exempt.
PROVENANCE_FIELDS={
    'source_inventory':dict(fields=['k/7.json:{files,sources,operation_sources}',
        'k/c0.json:{files,sources,operation_sources}'],
        reason='Source identity keys must match the frozen tree and producer inventory seals; they are integrity declarations inside file content.'),
    'config_schema':dict(fields=['k/{c,n}.json:benchmark_scene_exclusions',
        'k/{c,n}.json:geometry_connector','k/{c,n}.json:trace_program_version',
        'k/{c,n}.json:r1_training/room_authority/split',
        'k/{c,n}.json:route_table/{object_size_estimation,room_size_estimation}'],
        reason='Exact schema key identities are required by frozen content readers. Their values are still scanned.'),
    'staging_schema':dict(fields=['k/l.json:staged_inputs/{archives,files,packages,directories}/<index>/destination'],
        reason='The frozen staging reader requires this exact schema key (which contains sti). Its path value is always scanned.'),
    'input_identity':dict(fields=['k/n.json:benchmark_scene_exclusions/path',
        'k/n.json:dev_scene_exclusions/path','k/n.json:r1_training/wording_exclusion/path',
        'k/n.json:s1_routing/catalog/3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'],
        reason='Original identity text preserves authenticated config content. The consumer uses the separately checked opaque pin_paths value, never this identity as its job path.'),
    'room_rule':dict(fields=['k/s.json:entries/u/a4509d8c159f71f81d0f82adad8e85ef8135d17363084e7281fadddea04c9c5c/@content/room_rule'],
        reason='The exact human-readable admission annotation preserves the pinned card content; it does not control a job name or output.'),
    'refusal_vocabulary':dict(fields=['k/g.json:payload'],
        reason='The exact bound WORDS values are required to recognize and suppress forbidden names, not to emit them.'),
}
for _field in PROVENANCE_FIELDS.values():
    _field['use']='Authenticated file content only; never used as a wrapper name, path, argument, environment entry or log line.'
SOURCE_SEALS={
    ('k/7.json','files'):'b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8',
    ('k/c0.json','files'):'b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8',
    ('k/7.json','sources'):'4dd76ad38aaab89c8873af389d86c88e18548ac54543789dcde730b3192b39cc',
    ('k/7.json','operation_sources'):'4dd76ad38aaab89c8873af389d86c88e18548ac54543789dcde730b3192b39cc',
    ('k/c0.json','sources'):'4dd76ad38aaab89c8873af389d86c88e18548ac54543789dcde730b3192b39cc',
    ('k/c0.json','operation_sources'):'44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a',
}
INPUT_IDENTITIES={
    ('benchmark_scene_exclusions','path'):('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pk/benchmark_scene_exclusions.json','3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'),
    ('dev_scene_exclusions','path'):('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w17b/work/tree_r1/student_pilot/r2_dev_merged.json','a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5'),
    ('r1_training','wording_exclusion','path'):('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/v2h/SPLIT_V2.json','2463193d00fabda5c62d07027527f57a5943dd52ee2b346a215576e55d1abf19'),
    ('s1_routing','catalog','3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'):('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/benchmark_scene_exclusions.json','3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'),
}
ROOM_RULE_PATH=('entries','u/a4509d8c159f71f81d0f82adad8e85ef8135d17363084e7281fadddea04c9c5c','@content','room_rule')
ROOM_RULE='Only production-admitted traced rows can enter; initial cell zero until the loader audit binds them.'

def scan_python_environment_literals(tree,name,doc):
    """Check every literal contribution to environment sinks, including aliases.

    Name bindings and mapping mutations are followed conservatively across scopes.
    Runtime arguments/inherited environment remain runtime inputs; this is a source
    scanner, not an execution sandbox. All decoded maps are checked separately.
    """
    import ast
    bindings={};os_names={'os'};env_names=set();putenv_names=set();sinks=[]
    def bind(key,value):bindings.setdefault(key,[]).append(value)
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            os_names.update(a.asname or a.name for a in node.names if a.name=='os')
        elif isinstance(node,ast.ImportFrom) and node.module=='os':
            env_names.update(a.asname or a.name for a in node.names if a.name in ('environ','environb'))
            putenv_names.update(a.asname or a.name for a in node.names if a.name=='putenv')
        elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for result in ast.walk(node):
                if isinstance(result,ast.Return) and result.value is not None:bind(node.name,result.value)
        elif isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
            for target in node.targets if isinstance(node,ast.Assign) else [node.target]:
                if isinstance(target,ast.Name) and node.value is not None:bind(target.id,node.value)
                elif isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name):
                    bind(target.value.id,target.slice)
                    if node.value is not None:bind(target.value.id,node.value)
        elif isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            if isinstance(node.func.value,ast.Name) and node.func.attr in ('update','setdefault','__setitem__'):
                for arg in [*node.args,*node.keywords]:bind(node.func.value.id,arg)
    def environment(node):
        return (isinstance(node,ast.Name) and node.id in env_names or
            isinstance(node,ast.Attribute) and node.attr in ('environ','environb') and
            isinstance(node.value,ast.Name) and node.value.id in os_names)
    for _ in range(len(bindings)+1):
        added={key for key,values in bindings.items() if any(environment(v) for v in values)}-env_names
        setters={key for key,values in bindings.items() if any(
            isinstance(v,ast.Attribute) and environment(v.value) or
            isinstance(v,ast.Name) and v.id in putenv_names for v in values)}-putenv_names
        if not added and not setters:break
        env_names.update(added)
        putenv_names.update(setters)
    def literal(node,seen=frozenset()):
        if isinstance(node,ast.Constant) and isinstance(node.value,(str,bytes)):
            return node.value.decode() if isinstance(node.value,bytes) else node.value
        if isinstance(node,ast.Name) and node.id not in seen and len(bindings.get(node.id,[]))==1:
            return literal(bindings[node.id][0],seen|{node.id})
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
            a=literal(node.left,seen);b=literal(node.right,seen)
            if a is not None and b is not None:return a+b
        if isinstance(node,ast.JoinedStr):
            values=[literal(x.value if isinstance(x,ast.FormattedValue) else x,seen) for x in node.values]
            if all(v is not None for v in values):return ''.join(values)
        return None
    def inspect(node,where,seen=frozenset()):
        text=literal(node)
        if text is not None:name(text,where)
        if isinstance(node,ast.keyword) and node.arg is not None:name(node.arg,where+':key')
        if isinstance(node,ast.Name) and node.id not in seen:
            for value in bindings.get(node.id,[]):inspect(value,where,seen|{node.id})
        for child in ast.iter_child_nodes(node):inspect(child,where,seen)
    for node in ast.walk(tree):
        values=[]
        if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
            for target in node.targets if isinstance(node,ast.Assign) else [node.target]:
                if isinstance(target,ast.Subscript) and environment(target.value):values.extend([target.slice,node.value])
                elif environment(target):values.append(node.value)
        elif isinstance(node,ast.Subscript) and environment(node.value):values.append(node.slice)
        elif isinstance(node,ast.Call):
            values.extend(k.value for k in node.keywords if k.arg=='env')
            func=node.func
            setter=(isinstance(func,ast.Attribute) and (environment(func.value) or
                func.attr=='putenv' and isinstance(func.value,ast.Name) and func.value.id in os_names))
            setter |= isinstance(func,ast.Name) and func.id in putenv_names
            if setter:values.extend([*node.args,*node.keywords])
        if values:
            where=doc+':'+str(node.lineno)+':environment'
            for value in values:
                if value is not None:inspect(value,where)
            sinks.append(dict(location=where,expression=ast.unparse(node)))
    return sinks

def scan_python_environment(tree,name,doc):
    from environment21f import scan_python
    sinks=scan_python_environment_literals(tree,name,doc)
    scan_python(tree,name,doc)
    return sinks

def neutral_map(value):
    def visit(v):
        if isinstance(v,dict):return {k:visit(x) for k,x in v.items()}
        if isinstance(v,list):return [visit(x) for x in v]
        if isinstance(v,str):
            for old,new in ALIASES.items():
                if v==old or v.startswith(old+'/'):return new+v[len(old):]
        return v
    neutral=visit(value)
    checks=[dict(path=neutral['small']['file'],sha256=value['small']['sha256']),dict(path=neutral['model']['file'],sha256=value['model']['sha256'])]
    return neutral,checks
def neutral_shell(shell):
    shell=shell.replace(OLD,ALIASES[OLD])
    for old,new in ENV.items():shell=shell.replace(old,new)
    a=shell.index('    local tmp="$S/.model.$$"');b=shell.index('    tk_readonly_files "$snap"',a)
    shell=shell[:a]+'    /usr/bin/python3 -I "$Q_KIT/b/m.py" "$file" "$sha" "$snap" "$REV"\n'+shell[b:]
    shell='\n'.join(line for line in shell.splitlines() if not line.lstrip().startswith('#'))+'\n'
    return shell
def scan_decoded(kit):
    import ast,base64,shlex
    from functools import lru_cache
    from launch_r2.build import bad_string,WORDS
    kit=Path(kit);wh=json.loads((kit/'b/wh.json').read_text());checked=[]
    maps=[];names=[];provenance=[];capsules=[];environments=[]
    python_sources=[];shell_sources=[]
    # Repeat identities still count as visited; memoize only the pure word test.
    @lru_cache(maxsize=None)
    def forbidden(value):return bad_string(value,wh)
    def name(value,where,exception=None):
        if forbidden(value):
            if exception is None:raise ValueError('INPUT_NAME:'+where+':'+value)
            provenance.append(dict(location=where,field=exception,value=value))
        names.append(dict(location=where,value=value))
    def decode(value,where):
        raw=base64.b64decode(value['payload'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=value['sha256']:raise ValueError('CAPSULE_HASH:'+where)
        capsules.append(where)
        return raw
    spec=json.loads(decode(json.loads((kit/'k/p.json').read_text()),'k/p.json'))
    pin_paths=spec.get('pin_paths',{})
    def pinned_name(original,h,where):
        expected=spec['namespace']+'/u/'+h
        if pin_paths.get(h)!=expected or not any(x['sha256']==h for x in spec['uploads']):
            raise ValueError('INPUT_NAME_UNMAPPED:'+where+':'+original)
        name(expected,where+':resolved')
        name(original,where,'input_identity')
    # These are data-schema fields, never filenames. Match their complete locations.
    config_fields={('benchmark_scene_exclusions',),('geometry_connector',),('trace_program_version',),
        ('r1_training','room_authority','split'),('route_table','object_size_estimation'),
        ('route_table','room_size_estimation')}
    def pathlike(s):
        return '/' in s or bool(re.search(r'\.(?:jsonl?|txt|log|tar|gz|py|sh|bin|pt|safetensors|sqlite|png)$',s))
    def visit(v,doc,parts=(),inventory=False):
        where=doc+':'+('/'.join(parts) or '/')
        if isinstance(v,dict):
            if v.get('encoding') in ('base64','base64-json'):
                if set(v)!={'encoding','payload','sha256'}:raise ValueError('CAPSULE_FIELDS:'+where)
                for key in v:name(key,where+':key')
                name(v['encoding'],where+'/encoding');name(v['sha256'],where+'/sha256')
                visit(json.loads(decode(v,where)),doc,parts);return
            if set(v)=={'payload','sha256'}:
                for key in v:name(key,where+':key')
                name(v['sha256'],where+'/sha256')
                visit(json.loads(decode(v,where)),doc,parts+('@content',));return
            for key,x in v.items():
                loc=parts+(key,)
                if doc=='k/n.json' and isinstance(x,str) and forbidden(x):
                    identity=INPUT_IDENTITIES.get(loc)
                    if identity:
                        original,h=identity
                        if x!=original or (key=='path' and (set(v)!={'path','sha256'} or v['sha256']!=h)):
                            raise ValueError('INPUT_NAME_UNMAPPED:'+where+'/'+key+':'+x)
                        name(key,where+':key');pinned_name(x,h,where+'/'+key);continue
                schema_field=(doc in ('k/c.json','k/n.json') and loc in config_fields)
                schema_field |= (doc=='k/l.json' and len(loc)==4 and loc[0]=='staged_inputs'
                    and loc[1] in ('archives','files','packages','directories') and loc[2].isdigit() and loc[-1]=='destination')
                source_seal=SOURCE_SEALS.get((doc,key)) if not parts else None
                if source_seal:
                    if (not isinstance(x,dict) or any(not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) for h in x.values())
                        or hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=source_seal):
                        raise ValueError('SOURCE_INVENTORY:'+where)
                exception=('staging_schema' if doc=='k/l.json' else 'config_schema') if schema_field else None
                if inventory:exception='source_inventory'
                name(key,where+':key',exception)
                visit(x,doc,loc,bool(source_seal))
        elif isinstance(v,list):
            for i,x in enumerate(v):visit(x,doc,parts+(str(i),))
        elif isinstance(v,str):
            exception='room_rule' if doc=='k/s.json' and parts==ROOM_RULE_PATH and v==ROOM_RULE else None
            name(v,where,exception)
    for p in sorted(kit.rglob('*')):
        relative=str(p.relative_to(kit));name(relative,'kit inventory')
        if p.is_symlink():raise ValueError('KIT_LINK:'+relative)
    for p in [*sorted(kit.rglob('*.sh')),kit/'k/j.json']:
        raw=p.read_bytes()
        if p.suffix=='.json':
            value=json.loads(raw);raw=decode(value,str(p.relative_to(kit)))
        shell_lines=[]
        for n,line in enumerate(raw.decode().replace('\\\n','').splitlines(),1):
            if line.lstrip().startswith('#') and not line.startswith('#SBATCH'):continue
            if forbidden(line):raise ValueError('EXECUTABLE_NAME:'+p.name+':'+str(n)+':'+line)
            shell_lines.append(line)
        for token in shlex.split('\n'.join(shell_lines),comments=False):name(token,str(p.relative_to(kit))+':shell')
        shell_sources.append((str(p.relative_to(kit)),raw.decode()))
        checked.append(str(p.relative_to(kit)))
    # Check p_files first so the reviewed defect is reported directly, before ancillary metadata.
    paths=sorted(kit.rglob('*.json'),key=lambda p:(str(p.relative_to(kit))!='k/p.json',str(p.relative_to(kit))))
    for p in paths:
        relative=str(p.relative_to(kit))
        if relative=='k/j.json':continue
        value=json.loads(p.read_text())
        if relative=='k/g.json':
            raw=decode(value,relative)
            if json.loads(raw)!=list(WORDS):raise ValueError('WORD_LIST_DIFFERS')
            for key in value:name(key,relative+':key')
            for word in json.loads(raw):name(word,relative,'refusal_vocabulary')
            continue
        visit(value,relative);maps.append(relative)
    for p in sorted(kit.rglob('*.py')):
        tree=ast.parse(p.read_text())
        environments.extend(scan_python_environment_literals(tree,name,str(p.relative_to(kit))))
        python_sources.append((str(p.relative_to(kit)),tree))
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):
                s=node.value
                if s and not any(c.isspace() for c in s) and pathlike(s):
                    name(s,str(p.relative_to(kit))+':'+str(node.lineno))
        checked.append(str(p.relative_to(kit)))
    # Preserve every named 21d refusal before checking completeness of the proof.
    from environment21f import scan_python,scan_shell,ENVIRONMENT_VALUE_ALLOWLIST
    for relative,tree in python_sources:scan_python(tree,name,relative)
    for relative,source in shell_sources:environments.extend(scan_shell(source,name,relative))
    # These pinned maps are supplied by P on the job host. The runtime scanner checks
    # their complete decoded keys/values after P's byte authentication, before publication.
    operational=json.loads(decode(json.loads((kit/'k/l.json').read_text()),'k/l.json'))
    runtime_maps=[entry['manifest'] for entry in operational.get('staged_inputs',{}).get('directories',[])]
    return dict(status='PASS',executables=checked,decoded_maps=maps,checked_strings=len(names),
        capsule_hashes_checked=capsules,provenance=provenance,names=names,runtime_maps=runtime_maps,
        provenance_allowlist=PROVENANCE_FIELDS,environment_sinks=environments,
        environment_value_allowlist=sorted(ENVIRONMENT_VALUE_ALLOWLIST),
        scope='All kit paths and every decoded map key/string value, including every nested payload. '
              'Only exact, named authenticated content identifiers are allowed; no subtree is skipped. '
              'Shell tokens, Python path literals and environment names/values are checked. '
              'Unresolved environment writes and maps refuse; only explicitly allowlisted literal '
              'keys may have runtime values. Only an unmodified whole-environment spread/copy '
              'may inherit names; added keys and values are checked. Complex shell requires '
              'an exact reviewed source hash and a per-program literal-name runtime allowlist.')
