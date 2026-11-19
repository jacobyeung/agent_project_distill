"""Derive R1 from the authenticated H1 deployment; never edit the source kit."""
import argparse,copy,datetime,hashlib,importlib.util,json,os,re,shutil,sys
from pathlib import Path
AS='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(enc(v)+'\n')
H1_ID='eb45ebfd7664a57226a6a9202c365ffba268d0bd0f295d879ad6adedde07a0c8'
H1_TREE='9588661986650d29f39ce8d6ec9552f131e1684f0a622f579f439a8408cfc6f9'
ROOT=Path(__file__).resolve().parents[1]
BASE_RUNTIME={'b/a.py': '0ec9f5e9c1680ce73bf829301456c5cf987def1766516e07aa9f2e8ef44414de', 'b/ab.py': '0e1dd0ac6126fb2325affd6f12aee338f19b7fc842d6681c2d32c488622d7825', 'b/b3900003.py': '1749abcb5b41efb5a829298c0575d71d8acf7a0fa84ec09eaf19fb8e353049d9', 'b/c.sh': 'c519e62b65a9413e13d4c23aad5940dcabfda83b100abf8ce4c8ae90b71223a5', 'b/d.py': 'fc4e4c380daf678576b1f48cd4e6794baf45dc4342590300a4d4eddce176eea5', 'b/f2.py': '515c61e19baf0b189866a5145c19bfc96a671af0b24be49398034d40aaca7b67', 'b/g.py': 'f82ad268da216380c979d257b3e35dc75906577291c266a996c669369074276a', 'b/gcsput.py': '739319091d5e833003db28b7b33d9f81c3711f1357fbbf14c08e4d04654509d6', 'b/h.py': 'd4a64b0afa2581092e2a954df0353c5cabf255c63cfda4161c6ccfab97577302', 'b/i.py': '9aae09bdee66e80632c682d5a2b2236c09b18563ff86264f7d1f25102f501a0c', 'b/jc1.sh': '89cd9703edd0c80630250e64ae66c8676a3757d2ecef5a8504da10516640599a', 'b/jp0.sh': 'cd3473dcd6d28ae71d1d6cfc25cb1b6d03c04f73db7389ea8d8d7749e9c530cb', 'b/jt8c.sh': '76b7a543bf9dc31ecdf56191d324f69e9783d6b5a4462c82ea83aad615427a58', 'b/kitx.py': '55fb323596ed7965eb6006ad1c9ac7b6800b08ae0c12c8b48b3e0ccbf117a458', 'b/opaque.py': 'edb9126fafb8207de04c56f72b7d48503e1f15c3c375d3775903fd4387a76897', 'b/p0.py': 'd358490c855f03ce2eacc3e7949964b84f5da73c65e1306db3e83aa5b3321ee6', 'b/p0.sh': '85c4765067ce07bf0f4f384f817c41f2621c5233c99d255d0da21b17bada0104', 'b/profile.json': '51190cc4ef08e4419f50cfa9090a73e990cddee1219c4d75bad6e5ba5144d23a', 'b/q0.py': 'ae087f2b8b0540e0b913fb810388fc882ade79bb0b5440f834eb4231f2c67c62', 'b/r.sh': '332eb89f67c254612e8b634cb4bb342aaa0769df302b75c27031bf956698eca0', 'b/r8.py': 'd4046786d037168c6a2ee8f2266c9cf2c0049591e6f8d9a182f208a70bd06ef0', 'b/rd.py': '59d6c043db853b16492257eaf67676e2cfc705adb5d9c0a2d74321f81a20e800', 'b/s.py': 'db7a1149abf4e582160f8e1e692bed842db5d99961682d90e05412e089a44873', 'b/sa/prestage_hooks.py': 'b946487191158333dbd0df07b8b1849109b944a7be0ac09a6814d3b4a0ae0a0d', 'b/sa/sitecustomize.py': 'b3eeec3c45e00249b9d60db057b55fbd3ed1e7f2a53e6d88eba2bdaf36b94c58', 'b/sg.py': 'f2d1d6ce10c9022d41b2319eca8fa1138859494562e7417b10a792a92f19db46', 'b/v.py': '1dfaff4f73fe66040b11626823fab40fe87682bdff7b177939692716bb653d02', 'b/w.py': '6c0238671423ea96eda598d1ed3b455ba40f29784e776f28cec6d5ec1335612b', 'b/wh.json': '1f58a1f2e03f39ffd4c74b079766ee93ee7633ef73ec4fb4c344655964ef1d35', 'b/x.py': 'fadf985cf2a0d7e3f8f909b2ffe43151213b7812904b428e49ba5ef807ce6d07', 'b/z.py': 'f3dba650f47e74cd5422cf7be385ca43fabcd8f0b14bb31801e1477053e0d7f9', 'job.sh': '88ad86e54bee11aaca839110ccf6ffcfecd927530d50c93cd98bdf9cd21797d4', 'k/0.json': '516d215e939a81337908f7c2369baf1a89da3e5efda7b1e5dc8e322dc7da0d25', 'k/7.json': 'd6273a970c30df760465013ff6789deb5466dfa887790dcf0d33abc262a9ba45', 'k/pool_selection_eac5f9f0.json': 'eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9', 'k/routes.json': '62c54ed48c7e5782aed296549f9a750d5d76fd6589cbdeba2ed92acdf5282a35', 'k/s1_record.json': 'caf43b05b977e2241d0e1f69e84913f4a8b23b0db5a46d3de8a4c2d7a5369021'}

def identity(cfg):
    v={k:x for k,x in cfg.items() if k not in ('preparation','admission','authorization','milestone_gate')}
    if 'readout' in v:v['readout']={k:x for k,x in v['readout'].items() if k!='contiguous_clips'}
    if v.get('frame_layout')=='spread':v.pop('frame_layout')
    return hashlib.sha256(enc(v).encode()).hexdigest()
def digest(v):return hashlib.sha256(enc(v).encode()).hexdigest()
def safe(n):return not Path(n).is_absolute() and all(x not in ('','.','..') for x in n.split('/'))

def validate_switches(cfg):
    """Admit only S2 with S1 off and both own-sampling probabilities zero."""
    h=cfg.get('h1',{})
    schedules=(cfg.get('scheduled_sampling',{}),cfg.get('recipe',{}).get('scheduled_sampling',{}))
    if (h.get('routing_pose_targets') is not True or h.get('faithful_own_camera_rows') is not False
            or any(type(s.get('max_own_probability')) not in (int,float)
                   or s['max_own_probability']!=0 for s in schedules)):
        raise ValueError('Launch requires S2=true, S1=false, and both max_own_probability=0')

def validate_evidence(root):
    """Check pre-submission records without initializing allocation state."""
    # g.check always reaches persistent_launch for this kit. Reuse only its
    # read-only helpers and d.contract; job.sh retains the full runtime check.
    old_path=sys.path[:];old_bytecode=sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode=True
        sys.path.insert(0,str(root/'b'))
        def inherited(name):
            spec=importlib.util.spec_from_file_location('_r1_inherited_'+name,root/'b'/(name+'.py'))
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            return module
        gate=inherited('g');admission=inherited('d')
        launch=load(root/'k/launch.json');cfg=gate.read_pin(root,launch['config'])
        code=load(root/'k/7.json');config_sha=gate.identity(cfg);commit=code['commit']
        contract_sha=gate.digest(admission.contract(launch,cfg))
        review=gate.read_pin(root,launch['review'])
        staged=gate.read_pin(root,launch['staging'])
        archived=gate.read_pin(root,launch['archive'])
        auth=load(root/'k/4.json')
        if cfg.get('continuation'):
            from r4 import validate
            validate(auth)
        for name,record in (('review.json',review),('staging.json',staged),('4.json',auth)):
            if record.get('config_sha256')!=config_sha or record.get('source_revision')!=commit:
                raise ValueError('Evidence identity or source differs: '+name)
        if (review.get('verdict')!='PASS' or not review.get('reviewer')
                or cfg.get('admission',{}).get('sha256')!=launch['review']['sha256']
                or review.get('admission_contract_sha256')!=contract_sha
                or review.get('admission_scope')!='pinned-template-and-native-data-derivation'):
            raise ValueError('Independent review does not cover the in-job derivation')
        if (staged.get('status')!='PASS' or staged.get('missing')!=[]
                or staged.get('project_community_write_bytes')!=0):
            raise ValueError('Read-only cache staging is not verified')
        if (archived.get('status')!='ARCHIVED' or archived.get('durable') is not True
                or archived.get('sha256')!=code['archive']['sha256']
                or archived.get('tree_sha256')!=code['tree_sha256']
                or not isinstance(archived.get('location'),str) or not archived['location']
                or archived['location'].startswith(('/scratch/','/tmp/'))):
            raise ValueError('Off-scratch source archive is not attested')
        expiry=datetime.datetime.fromisoformat(auth['allow_until_utc'].replace('Z','+00:00'))
        if (expiry.tzinfo is None or expiry<datetime.datetime(2026,11,22,tzinfo=datetime.timezone.utc)
                or expiry<=datetime.datetime.now(datetime.timezone.utc) or 'p' not in auth.get('modes',[])
                or auth.get('admission_contract_sha256')!=contract_sha):
            raise ValueError('Written slot authorization is absent, foreign or expires too early')
    finally:
        sys.path[:]=old_path;sys.dont_write_bytecode=old_bytecode

def derive(source,out,packet,source_manifest_sha,*,fixture=False,evidence=None,bundle=None,selection_evidence=None):
    os.umask(0o077);source=Path(source);out=Path(out);packet=Path(packet)
    if sha(source/'SHA256SUMS.txt')!=source_manifest_sha:raise ValueError('Source manifest binding differs')
    manifest={}
    for line in (source/'SHA256SUMS.txt').read_text().splitlines():
        h,n=line.split('  ',1)
        if not safe(n) or n in manifest or not re.fullmatch('[0-9a-f]{64}',h):raise ValueError('Unsafe source inventory')
        manifest[n]=h
    for name,expected in BASE_RUNTIME.items():
        if manifest.get(name)!=expected or sha(source/name)!=expected:raise ValueError('Inherited runtime differs: '+name)
    missing=[]
    for n,h in manifest.items():
        path=source/n
        if path.is_symlink():raise ValueError('Linked source member')
        if not path.is_file():
            if not fixture:raise ValueError('Source member absent: '+n)
            missing.append(n)
        elif sha(path)!=h:raise ValueError('Source member SHA differs: '+n)
    parent_launch=load(source/'k/launch.json');parent=load(source/parent_launch['config']['file'])
    if identity(parent)!=H1_ID or load(source/'k/7.json')['tree_sha256']!=H1_TREE:raise ValueError('Not the pinned H1 deployment')
    archive=packet/('t.tar' if (packet/'t.tar').exists() else 'r1p_code.tar')
    cfg=load(packet/'config.json');binding=load(packet/'BINDING.json');code=load(packet/'records/c.json')
    if identity(cfg)!=binding['config_identity'] or sha(archive)!=code['archive']['sha256']:raise ValueError('Packet binding differs')
    if code['tree_sha256']!=binding['tree_sha256'] or cfg['type_mix']!=binding['mix']:raise ValueError('Packet tree or mix differs')
    validate_switches(cfg)
    if out.absolute()!=out.resolve():raise ValueError('Linked output parent')
    if out.exists():raise ValueError('Output must start absent')
    out.mkdir(mode=0o700,parents=True)
    for n in manifest:
        if n in missing:continue
        dest=out/n;dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        dest.write_bytes((source/n).read_bytes());dest.chmod(0o700 if os.access(source/n,os.X_OK) else 0o600)
    # All mutations are confined to this fresh copy. Inherited evidence is retained
    # as source material, but none of its pins authorizes the new configuration.
    cur=load(out/'k/0.json');launch=copy.deepcopy(parent_launch);oldrun=launch['run_key'];run=binding['run_key'];token=binding['store_key']
    for n in ('b/c.sh','b/p0.sh','b/r.sh','b/h.py','b/i.py','job.sh'):
        path=out/n;text=path.read_text();text=text.replace('/tmp/jjyeung/a_'+oldrun,'/tmp/jjyeung/a_'+run)
        if n=='b/c.sh':
            # Read-only file bytes remain in read-only namespace mounts. Keep
            # their private directories searchable at the required mode 0700.
            if text.count('chmod -R a-w ')!=3:raise ValueError('Inherited staging permissions differ')
            text=text.replace('chmod -R a-w ','tk_readonly_files ')
            anchor='rsync -rt "$HX/b"'
            if text.count(anchor)!=1:raise ValueError('Inherited kit copy differs')
            text=text.replace(anchor,'rsync -rt --chmod=D700 "$HX/b"')
            helper='tk_readonly_files() {\n    find "$1" -type f -exec chmod a-w {} +\n    find "$1" -type d -exec chmod 700 {} +\n}\n'
            text=text.replace('tk_stage_model() {',helper+'\ntk_stage_model() {')
        path.write_text(text)
    record=load(out/'k/s1_record.json');record['trees']['trainer']=dict(commit=code['commit'],file_count=len(code['files']),files=code['files'])
    write(out/'k/s1_record.json',record);write(out/'k/7.json',code)
    archive_name=Path(code['archive']['path']).name;(out/'k'/archive_name).write_bytes((archive).read_bytes())
    cur['trainer']=dict(file=code['archive']['path'],sha256=code['archive']['sha256']);cur['commit']=code['commit']
    cur['record']=dict(file=AS+'8865619b/k/s1_record.json',sha256=sha(out/'k/s1_record.json'))
    location=bundle or '/project/community/jjyeung/okh7/i_'+token
    staged={str(Path(cfg['streams']['vqa']['path']).parent/'d.db'):dict(parts=[binding['orchard_store']],sha256=binding['database_sha256'])}
    if binding.get('unit_binding'):
        for name,value in binding['unit_binding']['artifacts'].items():
            if sha(packet/name)!=value['sha256']:raise ValueError('Unit artifact differs')
            staged[value['path']]=dict(parts=[location+'/'+name],sha256=value['sha256'])
    for name in binding['record_files']:
        if not re.fullmatch('[a-z0-9_]+[.]json',name):raise ValueError('Unsafe record filename')
        path=packet/'records'/name
        dest=AS+binding.get('record_key',token)+'/'+path.name
        staged[dest]=dict(parts=[location+'/'+path.name],sha256=sha(path))
    staged[AS+binding.get('record_key',token)+'/s.json']=dict(parts=[location+'/s.json'],sha256=sha(packet/'proof/selection/r.json'))
    for dest,item in staged.items():
        if any(e.get('dest')==dest for e in cur.get('extra',[])):raise ValueError('Fresh staging destination is occupied')
        cur.setdefault('extra',[]).append(dict(dest=dest,**item))
    write(out/'k/0.json',cur)
    launch.update(status='FIXTURE' if fixture else 'BLOCKED',production_authorized=False,kit_key=token,run_key=run,
        run_directory='/tmp/jjyeung/a_'+run+'/runs/'+run,persistent_run_root='/project/community/jjyeung/okh7/r/'+run,
        source_revision=code['commit'],source_selection=cfg['s1_routing']['selection'],route_table=cfg['s1_route_policy']['table'])
    launch['in_job_admission']['directory']=cfg['output']+'/inputs'
    # Independent review, native staging and written authorization remain external inputs.
    pending=dict(status='PENDING',config_sha256=identity(cfg),source_revision=code['commit'],production_authorized=False)
    for n in ('review.json','staging.json','4.json'):
        value={**pending,'allowed_partitions':['advanced','general','bootstrap']} if n=='4.json' else pending
        if n=='4.json' and cfg.get('continuation'):
            from r4 import bind
            value=bind(value)
        write(out/'k'/n,value)
    arc=dict(schema='s1-source-archive-v1',status='PENDING',durable=False,tree_sha256=code['tree_sha256'],
             sha256=sha(archive),bytes=(archive).stat().st_size)
    write(out/'k/archive.json',arc)
    selected=load(selection_evidence) if selection_evidence else load(packet/'proof/selection/q.json')
    if selected.get('selection_sha256')!=binding['selection_sha256'] or selected.get('status')!='PASS':raise ValueError('Selection evidence differs')
    if evidence:
        if not selected.get('native_regeneration_executed'):raise ValueError('Native selection regeneration required')
        if binding.get('unit_binding') and not selected.get('native_unit_regeneration_executed'):raise ValueError('Native unit selection regeneration required')
        if fixture:raise ValueError('Fixture cannot take production evidence')
        for n in ('review.json','staging.json','4.json','archive.json'):
            value=load(Path(evidence)/n)
            if n!='archive.json' and value.get('config_sha256')!=identity(cfg):raise ValueError('Evidence identity differs: '+n)
            if n=='4.json':
                value['allowed_partitions']=['advanced','general','bootstrap']
                if cfg.get('continuation'):
                    from r4 import bind
                    value=bind(value)
            write(out/'k'/n,value)
        cfg['admission']=dict(path=AS+'8865619b/k/review.json',sha256=sha(out/'k/review.json'))
        launch.update(status='READY',production_authorized=True)
    key=sha_json(cfg)[:8];write(out/('k/'+key+'.json'),cfg);write(out/'k/1.json',{'0':key})
    launch['config']=dict(file='k/'+key+'.json',sha256=sha(out/('k/'+key+'.json')))
    seal=dict(schema='s1-run-seal-v1',tree_sha256=code['tree_sha256'],config_sha256=identity(cfg),archive=code['archive'])
    launch['source_seal']={**seal,'sha256':digest(seal)}
    for k,n in (('review','review.json'),('staging','staging.json'),('archive','archive.json')):
        launch[k]=dict(file='k/'+n,sha256=sha(out/'k'/n))
    write(out/'k/selection_equality.json',selected)
    write(out/'k/launch.json',launch)
    added=set()
    if cfg.get('continuation'):
        from importlib.util import spec_from_file_location,module_from_spec
        spec=spec_from_file_location('_c0',packet/'c0.py');c0=module_from_spec(spec);spec.loader.exec_module(c0)
        c0.policy(cfg,load(packet/'a0.json'))
        for src,dest in (('c0.py','b/c0.py'),('a0.json','k/a0.json')):
            (out/dest).write_bytes((packet/src).read_bytes());added.add(dest)
        (out/'b/r4.py').write_bytes((packet/'r4.py').read_bytes());added.add('b/r4.py')
        launch['slot']['wall_seconds']=86400
        write(out/'k/launch.json',launch)
        for name,anchor,replacement in (
            ('g', '    expiry = datetime.datetime.fromisoformat(auth["allow_until_utc"]',
             '    from r4 import allocation\n    allocation(auth, mode, environment)\n    expiry = datetime.datetime.fromisoformat(auth["allow_until_utc"]'),
            ('i', "    arms=auth['arm'] if isinstance(auth['arm'],list) else [auth['arm']]",
             "    from r4 import allocation\n    allocation(auth, mode, os.environ)\n    arms=auth['arm'] if isinstance(auth['arm'],list) else [auth['arm']]")):
            path=out/'b'/(name+'.py');text=path.read_text()
            if text.count(anchor)!=1:raise ValueError('Authority boundary differs: '+name)
            path.write_text(text.replace(anchor,replacement))
        p=out/'job.sh';s=p.read_text().replace('13:00:00','24:00:00')
        anchor='/bin/bash "$ROOT/b/p0.sh" "$ROOT"'
        if s.count(anchor)!=1:raise ValueError('Preflight boundary differs')
        s=s.replace(anchor,'if [[ "${SLURM_JOB_PARTITION:-}" == advanced ]]; then export TK_ALLOCATION_MODE=u; else export TK_ALLOCATION_MODE=p; fi\n'+anchor)
        anchor='MODE="$(/usr/bin/python3 -I "$ROOT/b/r8.py"'
        if s.count(anchor)!=1:raise ValueError('Mode boundary differs')
        s=s.replace(anchor,'/usr/bin/python3 -I "$ROOT/b/c0.py" "$ROOT" "$RUN"\n'+anchor);p.write_text(s)
        p=out/'b/r8.py';s=p.read_text()
        s=s.replace('import argparse\n','import argparse\nimport sys\n')
        s=s.replace('import uuid\n','import uuid\n\nsys.path.insert(0, str(Path(__file__).resolve().parent))\n')
        anchor='    if persistent is not None:\n'
        if s.count(anchor)!=1:raise ValueError('Resume boundary differs')
        s=s.replace(anchor,"    if not checkpoints and (root/'d/0.json').exists():\n        from c0 import verify, load as c_load\n        kit=Path(os.environ['TK_KIT_HOME'])\n        verify(root/'d',c_load(kit/'k/a0.json'))\n        if persistent is not None:persistent_check(root,persistent,job,'t',None,0)\n        return 'u'\n"+anchor);p.write_text(s)
        # r8 executes before r.sh exports the kit location.
        p=out/'job.sh';s=p.read_text().replace('/usr/bin/python3 -I "$ROOT/b/c0.py"','export TK_KIT_HOME="$ROOT"\n/usr/bin/python3 -I "$ROOT/b/c0.py"');p.write_text(s)
        p=out/'b/w.py';s=p.read_text();anchor="        cfg['milestone_gate']=pick(auth,'milestone_gate',arm)"
        if s.count(anchor)!=1:raise ValueError('Training boundary differs')
        s=s.replace(anchor,"        if cfg.get('continuation'):\n            if mode!='u':raise ValueError('c0:38')\n            from c0 import install\n            install(run,cfg,json.loads((root/'k/a0.json').read_text()))\n"+anchor);p.write_text(s)
        p=out/'b/r.sh';s=p.read_text();anchor='export TK_KIT_HOME="$HX"'
        if s.count(anchor)!=1:raise ValueError('Admission allocation boundary differs')
        s=s.replace(anchor,anchor+'\nif [[ "${1:-}" == t || "${1:-}" == u ]]; then export TK_ALLOCATION_MODE="$1"; fi')
        p.write_text(s)
    p=out/'b/z.py';s=p.read_text();anchor="    with archive.open('rb') as stream:"
    if s.count(anchor)!=1:raise ValueError('Redeploy boundary differs')
    s=s.replace(anchor,"    if (root/'b').exists() and not (root/'b').stat().st_mode & 0o200:\n        raise ValueError('Sealed kit refuses in-place redeployment; derive a fresh kit')\n"+anchor);p.write_text(s)
    names=set(manifest)|{'k/'+key+'.json','k/'+archive_name}|added
    actual={n:manifest[n] if n in missing else sha(out/n) for n in sorted(names)}
    (out/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in actual.items()))
    if evidence:
        validate_evidence(out)
    # Seal code directories only after inventory and evidence validation.
    for directory in sorted((p for p in (out/'b').rglob('*') if p.is_dir()),reverse=True):
        directory.chmod(0o500)
    (out/'b').chmod(0o500)
    result=dict(status=launch['status'],config_identity=identity(cfg),config_key=key,manifest_sha256=sha(out/'SHA256SUMS.txt'),
        source_manifest_sha256=source_manifest_sha,missing_source_members=missing,source_identity=H1_ID,
        run_key=run,staged_additions=staged,production_authorized=False,
        native_preparation='NOT_RUN',independent_review='REQUIRED' if evidence is None else 'SUPPLIED')
    return result

def sha_json(value):return hashlib.sha256((enc(value)+'\n').encode()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--source-manifest-sha256',required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--packet',type=Path,required=True);p.add_argument('--fixture',action='store_true')
    p.add_argument('--evidence',type=Path);p.add_argument('--bundle');p.add_argument('--selection-evidence',type=Path);a=p.parse_args()
    result=derive(a.source,a.out,a.packet,a.source_manifest_sha256,fixture=a.fixture,evidence=a.evidence,bundle=a.bundle,selection_evidence=a.selection_evidence)
    write(a.out.parent/(a.out.name+'.json'),result);print(enc(result))
if __name__=='__main__':main()
