"""Bind the sealed out3/A4 reader and settings, independently of the staged /p tree."""
from pathlib import Path
import sys
import tarfile
import hashlib
from contextlib import contextmanager
from . import provenance as P

ROOT = Path(__file__).resolve().parents[2]
A4 = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4')
PAYLOAD = ROOT/'in/claimed_reader'
PINS = {
    'serving_table': ('ret/metadata/reads/0/metadata/0.json', '2c3cc6b4f97ed64157f9addf73447763c781d2ba2294c7a3ff1b95ef75a0ebca'),
    'descriptor': ('tower_sequence.py', '97c8e6dfe33e7fd2988dc44e740f7a3b19627259b8f86827598ed368e1659e22'),
    'reader_package': ('package/0.tgz', '4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d'),
    'export_pin': ('ret/metadata/EXPORT_PIN.json', 'ed907e4adc1772db9c802eebafb252dbd87b4d591c04392fce7e5f6062156834'),
}
_VERIFIED = False
_RUNTIME_MODULES = {}
_RUNTIME_DEPTH = 0


@contextmanager
def reader_runtime():
    """Use A4's native helpers during a serial read, preserving N's training modules.

    The deployed geometry validates the exact helper source. Sharing N's imported
    student_pilot namespace would change that contract even with a pinned reader.
    Model objects remain the caller's adapter-installed objects throughout.
    """
    global _RUNTIME_DEPTH
    if _RUNTIME_DEPTH:
        _RUNTIME_DEPTH += 1
        try:yield
        finally:_RUNTIME_DEPTH -= 1
        return
    def native(name):return name.split('.')[0] in ('student_pilot','evalpath')
    saved={n:m for n,m in sys.modules.items() if native(n)}
    paths=list(sys.path)
    for name in saved:del sys.modules[name]
    sys.modules.update(_RUNTIME_MODULES)
    sys.path.insert(0,str(PAYLOAD/'tree'))
    _RUNTIME_DEPTH=1
    try:yield
    finally:
        _RUNTIME_MODULES.update({n:m for n,m in sys.modules.items() if native(n)})
        for name in list(sys.modules):
            if native(name):del sys.modules[name]
        sys.modules.update(saved);sys.path[:]=paths;_RUNTIME_DEPTH=0


def default_binding():
    return {k: dict(path=str(A4/p), sha256=h) for k,(p,h) in PINS.items()}


def load_binding(binding=None):
    global _VERIFIED
    binding = default_binding() if binding is None else binding
    for name, (_, expected) in PINS.items():
        if not binding.get(name):
            raise ValueError('MISSING grounding.'+name+' {path,sha256}')
        if binding[name]['sha256'] != expected:
            raise ValueError('Claimed A4 pin differs: '+name)
        P.checked(binding[name])
    if not _VERIFIED:
        # Check every staged source against the sealed archive, including helper imports.
        with tarfile.open(binding['reader_package']['path']) as archive:
            for member in archive.getmembers():
                if member.isfile():
                    expected = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
                    P.checked(dict(path=str(PAYLOAD/member.name),sha256=expected))
        _VERIFIED = True
    for path in (PAYLOAD, PAYLOAD/'b'):
        if str(path) not in sys.path: sys.path.insert(0,str(path))
    for name,module in list(sys.modules.items()):
        if name.split('.')[0] in ('e2e_reader','parity_kit','h1eval') or name=='_parity_reader_policy':
            file = getattr(module,'__file__',None)
            if file and not Path(file).resolve().is_relative_to(PAYLOAD):
                raise ValueError('Unsealed reader already imported: '+file)
    settings = P.load(binding['serving_table']['path'])
    if (settings['arm'],settings['stage1_select_rule'],settings['perception_memo'],settings['perception_memo_modules']) != ('own_depth','candidates_argmax','on',['g3t']):
        raise ValueError('Claimed arm settings differ')
    return settings


def budget(processor):
    from parity_kit.common import policy
    p = policy()
    return p.ThinkingBudget(processor.tokenizer,p.DECODE_BUDGET,
                            openers=processor._routing_tokens['ids'].values())


def build_reader(model, processor, binding, device):
    with reader_runtime():
        return _build_reader(model,processor,binding,device)


def _build_reader(model, processor, binding, device):
    settings = load_binding(binding)
    # The training artifact manifest must admit the installed adapter code and current
    # immutable export as well as the exact deployed perception assets.
    pin = binding.get('artifact_manifest')
    if not pin:
        raise ValueError('MISSING grounding.artifact_manifest {path,sha256}: '+settings['artifact_manifest'])
    specs = P.load(P.checked(pin))
    P.checked(dict(path=str(Path(specs['root'])/specs['name']),sha256=specs['sha256']))
    # These roots must admit the exact staged source, including A4's native helpers.
    expected_roots=dict(reader=PAYLOAD/'b/e2e_reader',tree=PAYLOAD/'tree',
                        heads=PAYLOAD/'b/heads',runner=PAYLOAD/'b/parity_kit')
    for role,path in expected_roots.items():
        if Path(specs.get('code_roots',{}).get(role,'')).resolve()!=path.resolve():
            raise ValueError('MISSING artifact code root '+role+': '+str(path))
    from e2e_reader.artifact import Artifact
    from e2e_reader.parity import _head
    from e2e_reader.real import real_perception
    from student_pilot.sam3_tower import Sam3Tower
    artifact = Artifact(specs['root'],specs['name'],specs['sha256'],
                        code_roots=specs.get('code_roots'),env_roots=settings['env_roots'],
                        write_roots=[str(ROOT/'out')],
                        required_roles=('checkpoint','tokenizer','g3t','sam3','selector_head')).verify()
    # Artifact.verify hashes these bytes; retain its verified inputs in every receipt.
    for component in artifact.manifest['components'].values():
        for entry in component['files']:
            P.INPUTS[str(artifact._resolve(entry['rel']))]=entry['sha256']
    for entry in artifact.manifest.get('code',[]):
        P.INPUTS[str(artifact._code_path(entry))]=entry['sha256']
    for name in ('checkpoint_path','receipt_path'):
        if Path(settings['sam3'][name]).resolve() not in artifact.files('sam3'):
            raise ValueError('SAM file missing from artifact: '+name)
    selector = _head(artifact,settings['selector_head'],'selector_head')
    perception = real_perception(artifact,device=str(device),stage1_select_rule='candidates_argmax',
            perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],
            sam3_tower=Sam3Tower(dict(settings['sam3'],device=str(device))),selector_head=selector)
    return dict(artifact=artifact,perception=perception)


def require_replay(pin, tree_root=None):
    if not pin:raise ValueError('MISSING greedy_replay {path,sha256}; run scripts/greedy_replay.py before training')
    receipt=P.load(P.checked(pin))
    types={'camera_displacement','camera_rotation','camera_movement_direction','object_abs_distance','room_size_estimation'}
    if (receipt.get('status')!='PASS' or receipt.get('counts')!={t:4 for t in types}
            or receipt.get('mismatches')!=[] or receipt.get('export_pin_sha256')!=PINS['export_pin'][1]):
        raise ValueError('Greedy A4 replay did not pass four items per type')
    if not receipt.get('input_sha256'):raise ValueError('Replay has no input pins')
    if tree_root is not None and receipt.get('tree_root')!=str(Path(tree_root).resolve()):
        raise ValueError('Replay used a different N training tree')
    for path,sha in receipt['input_sha256'].items():P.checked(dict(path=path,sha256=sha))
    for name in ('rollout.py','serving.py','adapters.py','replay.py','choice.py'):
        path=ROOT/'overlay/rl_on_n'/name
        if receipt['input_sha256'].get(str(path))!=P.sha(path):raise ValueError('Replay code differs: '+name)


def call_caps():
    # Read the deployed literal without importing its unrelated task-admission stack.
    import ast
    path=PAYLOAD/'h1eval/h10/parity_adapter.py'
    P.sha(path)
    for node in ast.parse(path.read_text()).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PER_READ_CALL_CAP' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('MISSING PER_READ_CALL_CAP in '+str(path))
