"""Apply next-leg orders while retaining the existing admission gates."""
import ast, json, re
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/build6'
def edit(name,fn):
    p=T/name;s=p.read_text();p.write_text(fn(s))
p=T/'student_pilot/r2_contract.py';s=p.read_text()
start=s.index('INIT = ');end=s.index('\n\ndef check_init',start)
identity=ast.literal_eval(ast.unparse(ast.parse(s[start:end]).body[0].value).replace('dict(', '{')) if False else None
namespace={};exec(s[start:end],namespace);identity=namespace['INIT']
selection=dict(schema='r2-init-selection-v1',identity=identity,selection='fallback',
               reason='No tested D0 export was supplied in this lane. Step-544 remains the pinned fallback.',
               evidence=None,source='work/build6/integrate/current/student_pilot/carrier_c1_run.py; out/BUILD5_REPORT.md',admission=False)
for dest in (L/'out/INIT_INPUT.json',L/'fixtures/work/build6/INIT_INPUT.json'):
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(selection,indent=2)+'\n')
helper='''def init_identity(value):
    if not isinstance(value, dict) or not re.fullmatch('[0-9a-f]{64}', str(value.get('artifact_sha256', ''))):
        raise ValueError('Missing pinned init identity')
    if any(not value.get(k) for k in ('parent_run', 'parent_kit', 'parent_source_seal', 'parent_configuration_prefix')) or type(value.get('step')) is not int or value['step'] < 0:
        raise ValueError('Incomplete pinned init lineage')
    if not re.fullmatch('[0-9a-f]{64}', str(value['parent_source_seal'])):
        raise ValueError('Incomplete pinned init lineage')
    return deepcopy(value)


def selected_init(pin):
    if not pin:
        raise ValueError('Missing pinned init selection')
    value = load(pinned(pin))
    if value.get('schema') != 'r2-init-selection-v1':
        raise ValueError('Invalid init selection')
    return init_identity(value.get('identity'))


def bound_init(cfg):
    value = cfg.get('r2', {}).get('init', cfg.get('r2_identity', {}).get('init'))
    return init_identity(value)
'''
s=s[:start]+helper+s[end:]
s=s.replace("    if spec.get('contract') != CONTRACT or spec.get('init') != INIT:","    init = init_identity(spec.get('init'))\n    if spec.get('contract') != CONTRACT:")
s=s.replace('INIT[','init[')
s=s.replace("lineage_init(cfg.get('init_artifact', {}).get('artifact', {}))", "lineage_init(cfg.get('init_artifact', {}).get('artifact', {}), init=bound_init(cfg))")
s=s.replace('def lineage_init(pin):\n', 'def lineage_init(pin, *, init):\n    init = init_identity(init)\n')
s=s.replace("!= INIT", "!= init")
s=s.replace("'ft': ('ft', 'feet'), 'm2': ('square meters', 'square metres')", "'ft': ('ft', 'feet'), 'in': ('in', 'inch', 'inches'), 'ft2': ('square feet', 'square foot', 'sq ft'), 'm2': ('square meters', 'square metres')")
s=s.replace("'ft': ('feet',), 'm2': ('square meters', 'square metres')", "'ft': ('feet',), 'in': ('inch', 'inches'), 'ft2': ('square feet', 'square foot', 'sq ft'), 'm2': ('square meters', 'square metres')")
p.write_text(s)
edit('student_pilot/r2_config.py',lambda s:s.replace('from .r2_contract import INIT, CONTRACT','from .r2_contract import selected_init, CONTRACT').replace('dense_manifest=None, stage=1, overrides=True','dense_manifest=None, stage=1, overrides=True, init_pin=None').replace('dict(init=INIT,','dict(init=selected_init(init_pin),'))
edit('launch_r2/build.py',lambda s:s.replace('bindings=None, overrides=True):','bindings=None, overrides=True, init_pin=None):').replace('dense_manifest=dense_manifest)\n    cfg = relocate','dense_manifest=dense_manifest, init_pin=init_pin)\n    cfg = relocate'))
edit('launch_r2/host.py',lambda s:s.replace('import CONTRACT, INIT','import CONTRACT, bound_init').replace("'init':INIT", "'init':bound_init(cfg)"))
edit('student_pilot/r2_openers.py',lambda s:s.replace('from .r2_contract import INIT','from .r2_contract import bound_init').replace("lineage_init(init.get('artifact', {}))", "lineage_init(init.get('artifact', {}), init=bound_init(cfg))").replace("INIT['artifact_sha256']", "bound_init(cfg)['artifact_sha256']",1).replace("INIT['artifact_sha256']", "bound_init(receipt)['artifact_sha256']"))
edit('student_pilot/r2_policy.py',lambda s:s.replace('    from .r2_contract import INIT\n', '').replace(" or ancestor == INIT['artifact_sha256'] or artifact_pin.get('sha256') == INIT['artifact_sha256']",'').replace("            or ancestor == INIT['artifact_sha256'] or artifact_pin.get('sha256') == INIT['artifact_sha256']",''))
# The historical identity belongs to test inputs, never to the runtime default.
test_helper='''from pathlib import Path
import os
from student_pilot.p3_provenance import load, file_pin
ROOT = Path(os.environ.get('R2_FIXTURES', Path(__file__).resolve().parents[3]/'fixtures'))
PIN = file_pin(ROOT/'work/build6/INIT_INPUT.json')
INIT = load(ROOT/'work/build6/INIT_INPUT.json')['identity']
def binding(): return dict(r2_identity=dict(init=INIT))
'''
(T/'tests/r2_init_fixture.py').write_text(test_helper)
changes=[]
for p in (T/'tests').glob('test_r2*.py'):
    s=p.read_text();old=s
    s=s.replace('from student_pilot.r2_contract import INIT','from tests.r2_init_fixture import INIT')
    s=s.replace('from student_pilot.r2_contract import CONTRACT, INIT','from student_pilot.r2_contract import CONTRACT\nfrom tests.r2_init_fixture import INIT')
    s=s.replace('from student_pilot.r2_contract import lineage_init,INIT','from student_pilot.r2_contract import lineage_init\n        from tests.r2_init_fixture import INIT')
    if 'C.INIT' in s:s=s.replace('C.INIT','INIT');s+='\nfrom tests.r2_init_fixture import INIT\n'
    # Add an explicit fixture pin to existing kit/configuration tests.
    parsed=ast.parse(s);lines=s.splitlines(True);offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    insert=[]
    for node in ast.walk(parsed):
        if not isinstance(node,ast.Call):continue
        fn=ast.unparse(node.func)
        if fn in ('B.build','C.configure','configure'):
            insert.append(offsets[node.end_lineno-1]+node.end_col_offset-1)
    for pos in sorted(insert,reverse=True):s=s[:pos]+', init_pin=INIT_PIN'+s[pos:]
    if insert:s+='\nfrom tests.r2_init_fixture import PIN as INIT_PIN\n'
    # Explicit init binding preserves the prior tests' lineage premise.
    s=s.replace("lineage_init({'sha256':INIT['artifact_sha256']})", "lineage_init({'sha256':INIT['artifact_sha256']}, init=INIT)")
    s=s.replace("lineage_init({'sha256':'f'*64})", "lineage_init({'sha256':'f'*64}, init=INIT)")
    if s!=old:p.write_text(s);changes.append(str(p.relative_to(T)))
(B/'TEST_INPUT_ADAPTATIONS.json').write_text(json.dumps(dict(reason='The runtime no longer chooses a constant init. Existing tests explicitly supply the same historical fixture pin; assertions remain.',files=changes),indent=2))
print('Pinned init and answer-unit table updated.')
