from pathlib import Path
import json
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0';K=L/'out/kit_parity50'
p=K/'run.py';s=p.read_text();target="    if (original/'u0').exists():raise ValueError('Original source contains extensions')"
s=s.replace(target,target+'''
    base_path=HERE/'u4.json' if (HERE/'u4.json').is_file() else HERE/'BASE_PIN.json'
    base=read_wire(json.loads(base_path.read_bytes()))
    expected=base['inventory']
    pin=hashlib.sha256(json.dumps(sorted(expected.items()),sort_keys=True,
                      separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    if not expected or base['files']!=len(expected) or pin!=base['sha256']:
        raise ValueError('Invalid base pin')
    for root in (original,source):
        paths=[p for p in root.rglob('*') if p.relative_to(root).parts[0]!='u0'
               and '__pycache__' not in p.parts and p.suffix!='.pyc']
        if any(p.is_symlink() for p in paths):raise ValueError('Base contains symlinks')
        actual={str(p.relative_to(root)):p for p in paths if p.is_file()}
        if set(actual)!=set(expected):raise ValueError('Base inventory differs from MANIFEST')
        if any(hashlib.sha256(p.read_bytes()).hexdigest()!=expected[n] for n,p in actual.items()):
            raise ValueError('Base hash differs from MANIFEST')
''')
p.write_text(s)
(K/'BASE_PIN.json').write_text(json.dumps(json.loads((L/'out/patches/MANIFEST.json').read_text())['base_pin'],indent=2,sort_keys=True)+'\n')
p=E/'a11.py';s=p.read_text();needle="        (out/'u3.json').write_text(json.dumps({'u0':pack(pins)},sort_keys=True)+'\\n')"
s=s.replace(needle,needle+"\n        base=json.loads((incoming/'BASE_PIN.json').read_bytes())\n        (out/'u4.json').write_text(json.dumps({'u0':pack(base)},sort_keys=True)+'\\n')");p.write_text(s)
p=K/'test_run.py';p.write_text(p.read_text().replace("'u2.json','u3.json'","'u2.json','u3.json','u4.json'"))
# Allow the round-2 root fixture to supply a tiny authenticated base.
p=E/'tests/test_round2.py';s=p.read_text();needle="        (root/'EXTENSION_PINS.json').write_text(json.dumps(pins));kit.HERE=root"
s=s.replace(needle,"""        for target in (original,source):(target/'base.py').write_bytes(b'base')
        inventory={'base.py':hashlib.sha256(b'base').hexdigest()}
        base=dict(inventory=inventory,files=1,sha256=hashlib.sha256(json.dumps(sorted(inventory.items()),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
        (root/'BASE_PIN.json').write_text(json.dumps(base))
"""+needle);p.write_text(s)
p=E/'a12.py';s=p.read_text()
s=s.replace('*, enable_extensions=False):','*, enable_extensions=False, processor_only=False, operator_bootstrap=None, operator_source=None):',1)
s=s.replace('    from orchard_h10.common import template\n','''    if processor_only and not enable_extensions:raise ValueError('Processor-only requires --enable-extensions')
    if bool(operator_bootstrap)!=bool(operator_source):raise ValueError('Supply both operator sources')
    if operator_source and not enable_extensions:raise ValueError('Operator overlay requires --enable-extensions')
    from orchard_h10.common import template
''',1)
s=s.replace('    plan=canonical(cfg)','''    if processor_only:
        cfg.update(read_processor_only='on',read_processor_cache='on',read_vision_cache='off',
                   read_sam_cache='off',read_cache_bytes=4*1024**3)
    if operator_source:
        # The A4 operator owns one card. Scene sharding is not an adoption mode.
        cfg['read_scene_shards']=False
    plan=canonical(cfg)''',1)
s=s.replace("    bundle=L.tar_bytes({'0.py':boot,'0.json':json.dumps(public).encode()})", """    bundle_files={'0.py':boot,'0.json':json.dumps(public).encode()}
    if operator_source:
        bundle_files.update({'0.py':Path(operator_bootstrap).read_bytes(),
                             '7.py':Path(operator_source).read_bytes()})
    bundle=L.tar_bytes(bundle_files)""")
s=s.replace("    a=p.parse_args()","    p.add_argument('--processor-only',action='store_true')\n    p.add_argument('--operator-bootstrap');p.add_argument('--operator-source')\n    a=p.parse_args()")
s=s.replace('enable_extensions=a.enable_extensions),sort_keys=True)','enable_extensions=a.enable_extensions,processor_only=a.processor_only,\n                           operator_bootstrap=a.operator_bootstrap,operator_source=a.operator_source),sort_keys=True)')
p.write_text(s)
# Patch the input operator on a separate copy. The original is untouched.
O=L/'work/operator3';O.mkdir(exist_ok=True)
(O/'0.py').write_bytes((L/'work/operator3-original/0.py').read_bytes())
s=(L/'work/operator3-original/7.py').read_text()
s=s.replace('def memory_bound(*, captures=(84,), allocation_bytes=200*1024**3):','def memory_bound(*, captures=(84,), allocation_bytes=200*1024**3, read_extensions=False, read_cache_bytes=0):\n if not read_extensions:read_cache_bytes=0\n if type(read_cache_bytes) is not int or not 0<=read_cache_bytes<=16*1024**3:\n  raise ValueError(\'Invalid read cache memory bound\')')
s=s.replace('host_budget_bytes=(n+3)*per_capture+runtime_allowance)', 'host_budget_bytes=(n+3)*per_capture+runtime_allowance+read_cache_bytes)')
s=s.replace("             fits=all(r['host_budget_bytes']<=allocation_bytes for r in reads))", "             **({'read_cache_bytes':read_cache_bytes} if read_extensions else {}),\n             fits=all(r['host_budget_bytes']<=allocation_bytes for r in reads))")
s=s.replace(' result=memory_bound()',''' options={}
 if config.get('read_extensions') is True:
  from e2e_reader.read_cache import cache_bytes,switches
  cap=cache_bytes(settings) if 'on' in switches(settings).values() else 0
  options=dict(read_extensions=True,read_cache_bytes=cap)
 result=memory_bound(**options)''')
s=s.replace(" sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]",""" sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
 if cfg['config'].get('read_extensions') is True:
  sys.path.insert(0,str(p/'u0'))
  from a8 import activate
  activate(enabled=True)""")
(O/'7.py').write_text(s)
(O/'tower_sequence.py').write_text(s)
