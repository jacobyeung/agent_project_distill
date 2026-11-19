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
    import base64,sys
    from launch_r2.build import bad_string
    kit=Path(kit);wh=json.loads((kit/'b/wh.json').read_text());checked=[]
    for p in [kit/'job.sh',*sorted((kit/'b').glob('*.sh')),kit/'k/j.json']:
        raw=p.read_bytes()
        if p.suffix=='.json':
            value=json.loads(raw);raw=base64.b64decode(value['payload'],validate=True)
            if hashlib.sha256(raw).hexdigest()!=value['sha256']:raise ValueError('CAPSULE_HASH')
        for n,line in enumerate(raw.decode().splitlines(),1):
            if line.lstrip().startswith('#') and not line.startswith('#SBATCH'):continue
            if bad_string(line,wh):raise ValueError('EXECUTABLE_NAME:'+p.name+':'+str(n))
        checked.append(str(p.relative_to(kit)))
    value=json.loads((kit/'k/l.json').read_text());raw=base64.b64decode(value['payload'],validate=True)
    if hashlib.sha256(raw).hexdigest()!=value['sha256']:raise ValueError('CAPSULE_HASH')
    def visit(v):
        if isinstance(v,dict):
            for x in v.values():visit(x)
        elif isinstance(v,list):
            for x in v:visit(x)
        elif isinstance(v,str) and v.startswith('/') and bad_string(v,wh):raise ValueError('INPUT_NAME')
    visit(json.loads(raw))
    return dict(status='PASS',executables=checked,decoded_input_map='k/l.json',scope='Executable shell, arguments, environment names/values, staged names and decoded operational input paths; sealed source code and provenance records retain their original identities.')
