from pathlib import Path
import hashlib,json,re
POOL='/project/community/jjyeung/okh7'
OLD='/project/community/jjyeung/distill/okit'
MODEL='/project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar'
ALIASES={OLD:POOL+'/l_94a76bda',MODEL:POOL+'/l_3d48eea0'}
ENV={'STUDENT_ORCHARD':'Q_E1','STUDENT_SLURM_SITE':'Q_E2','STUDENT_MODEL_ROOT':'Q_E3','STUDENT_FRAME_ROOT_MAP':'Q_E4','R1_STUDENT_HEX':'Q_E5','STUDENT_PRESERVE_CHECKPOINTS':'Q_E6'}
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
    import ast,base64
    from launch_r2.build import bad_string,WORDS
    kit=Path(kit);wh=json.loads((kit/'b/wh.json').read_text());checked=[]
    maps=[];names=[];provenance=[];capsules=[]
    def name(value,where):
        if bad_string(value,wh):raise ValueError('INPUT_NAME:'+where+':'+value)
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
        provenance.append(dict(location=where,kind='authenticated input identity resolved by pinned hash map',sha256=h,original=original))
    # These are data-schema fields, never filenames. Match their complete locations.
    config_fields={('benchmark_scene_exclusions',),('geometry_connector',),('trace_program_version',),
        ('r1_training','room_authority','split'),('route_table','object_size_estimation'),
        ('route_table','room_size_estimation')}
    path_fields={'path','file','name','source','destination','dest','member','root','output','directory',
        'parts','files','entries','links','staged_pins','p_files','p_sources','opaque_name'}
    def pathlike(s):
        return '/' in s or bool(re.search(r'\.(?:jsonl?|txt|log|tar|gz|py|sh|bin|pt|safetensors|sqlite|png)$',s))
    def visit(v,doc,parts=(),data=False):
        where=doc+':'+('/'.join(parts) or '/')
        if isinstance(v,dict):
            if v.get('encoding') in ('base64','base64-json'):
                if set(v)!={'encoding','payload','sha256'}:raise ValueError('CAPSULE_FIELDS:'+where)
                visit(json.loads(decode(v,where)),doc,parts,data);return
            if set(v)=={'payload','sha256'}:
                # Embedded staging payloads are authenticated input content, not name maps.
                visit(json.loads(decode(v,where)),doc,parts+('@content',),True);return
            for key,x in v.items():
                loc=parts+(key,)
                if doc=='k/n.json' and isinstance(x,str) and bad_string(x,wh):
                    if key=='path' and set(v)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(v['sha256'])):
                        pinned_name(x,v['sha256'],where+'/path');continue
                    if re.fullmatch('[0-9a-f]{64}',key):
                        pinned_name(x,key,where+'/'+key);continue
                schema_field=(doc in ('k/c.json','k/n.json') and loc in config_fields)
                schema_field |= (doc=='k/l.json' and len(loc)==4 and loc[0]=='staged_inputs'
                    and loc[1] in ('archives','files','packages','directories') and loc[-1]=='destination')
                if doc in ('k/7.json','k/c0.json') and not parts and key in ('files','sources','operation_sources'):
                    # These are the authenticated sealed-source inventories, not staging maps.
                    if not isinstance(x,dict) or any(not re.fullmatch('[0-9a-f]{64}',h) for h in x.values()):
                        raise ValueError('SOURCE_INVENTORY:'+where)
                    provenance.append(dict(location=where+key,entries=len(x)));continue
                if not schema_field and (not data or pathlike(key) or (parts and parts[-1] in path_fields)):
                    name(key,where+':key')
                visit(x,doc,loc,data)
        elif isinstance(v,list):
            for i,x in enumerate(v):visit(x,doc,parts+(str(i),),data)
        elif isinstance(v,str):
            if not data or pathlike(v) or any(p in path_fields for p in parts[-2:]):name(v,where)
    for p in sorted(kit.rglob('*')):
        relative=str(p.relative_to(kit));name(relative,'kit inventory')
        if p.is_symlink():raise ValueError('KIT_LINK:'+relative)
    for p in [kit/'job.sh',*sorted((kit/'b').glob('*.sh')),kit/'k/j.json']:
        raw=p.read_bytes()
        if p.suffix=='.json':
            value=json.loads(raw);raw=decode(value,str(p.relative_to(kit)))
        for n,line in enumerate(raw.decode().splitlines(),1):
            if line.lstrip().startswith('#') and not line.startswith('#SBATCH'):continue
            if bad_string(line,wh):raise ValueError('EXECUTABLE_NAME:'+p.name+':'+str(n))
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
            provenance.append(dict(location=relative,kind='bound refusal vocabulary'));continue
        visit(value,relative);maps.append(relative)
    for p in sorted((kit/'b').glob('*.py')):
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):
                s=node.value
                if s and not any(c.isspace() for c in s) and pathlike(s):
                    name(s,str(p.relative_to(kit))+':'+str(node.lineno))
        checked.append(str(p.relative_to(kit)))
    # These pinned maps are supplied by P on the job host. The runtime scanner checks
    # their complete decoded keys/values after P's byte authentication, before publication.
    operational=json.loads(decode(json.loads((kit/'k/l.json').read_text()),'k/l.json'))
    runtime_maps=[entry['manifest'] for entry in operational.get('staged_inputs',{}).get('directories',[])]
    return dict(status='PASS',executables=checked,decoded_maps=maps,checked_strings=len(names),
        capsule_hashes_checked=capsules,provenance=provenance,names=names,runtime_maps=runtime_maps,
        scope='All kit paths, decoded operational map keys and values, nested staging payload paths, '
              'shell arguments and Python path literals. Authenticated source inventories and input data '
              'retain semantic identifiers; runtime guards check dynamic staging and archive names.')
