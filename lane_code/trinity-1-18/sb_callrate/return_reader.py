"""Read-only authenticated routed-return loader, adapted from score_r5.load."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).absolute().parent
DEFAULT_INPUT = HERE / 'in'
OUT3 = Path('cont_ops/work/r1route/out3')
OUT3S = Path('cont_ops16/work/c15/r1route/out3s')


class Inputs:
    def __init__(self, root=DEFAULT_INPUT, original_root='/scratch/jjyeung/orch_n30'):
        self.root = Path(root).absolute()
        self.original_root = Path(original_root)
        self.sources = {}
        self.links = {}

    def path(self, path):
        """Resolve copied links without accessing the original node's targets."""
        path = Path(os.path.abspath(path))
        for _ in range(32):
            changed = False
            for parent in reversed((path, *path.parents)):
                if parent.is_symlink():
                    target = Path(os.readlink(parent))
                    self.links[str(parent)] = str(target)
                    if target.is_absolute() and target.is_relative_to(self.original_root):
                        target = self.root / target.relative_to(self.original_root)
                    elif not target.is_absolute():
                        target = parent.parent / target
                    path = Path(os.path.abspath(target / path.relative_to(parent)))
                    changed = True
                    break
            if not changed:
                return path
        raise ValueError('Symlink cycle: ' + str(path))

    def data(self, path):
        path = self.path(path)
        if not path.is_file():
            raise FileNotFoundError('MISSING: ' + str(path))
        data = path.read_bytes()
        self.sources[str(path)] = hashlib.sha256(data).hexdigest()
        return data

    def digest(self, path):
        self.data(path)
        return self.sources[str(self.path(path))]

    def read(self, path):
        return json.loads(self.data(path))

    def provenance(self):
        return [{'path': p, 'sha256': s} for p, s in sorted(self.sources.items())]


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_read(io, root, package, read_no, step, bases, manifest_path=None, reference_read=None):
    root, package, bases = map(io.path, (root, package, bases))
    src = io.path(package / 'src')
    plan = io.read(package / 'READ_PLAN.json')
    expected = plan['read_settings'][read_no]
    identity = io.read(root / 'metadata/IDENTITY.json')
    public = io.read(package / 'package/0.json')
    if identity['plan'] != public['plan_sha256'] or identity['operator_sha256'] != io.digest(package / 'tower_sequence.py'):
        raise ValueError('Return plan/operator differs: ' + str(root))
    if identity['reads'][read_no] != expected:
        raise ValueError('Read plan differs: ' + str(root))
    # Preserve the step-200 checks and apply the same binding check to new exports.
    if step == 200 or 'export_binding' in plan:
        pin = io.read(root / 'metadata/EXPORT_PIN.json')
        binding = plan['export_binding']
        for key in ('run', 'step', 'member_directory', 'lineage', 'object', 'config_sha256'):
            if pin.get(key) != binding[key]:
                raise ValueError('Export binding differs: ' + key)
        if binding['step'] != step:
            raise ValueError('Requested step differs from export binding')
        for key, value in binding['preparation_sha256'].items():
            if pin['preparation'][key]['sha256'] != value:
                raise ValueError('Preparation differs: ' + key)
    journal_root = root / 'metadata/reads' / str(read_no) / 'metadata/journals'
    for started in sorted(journal_root.glob('*/*/STARTED.json')):
        io.digest(started)
        if not (started.parent / 'items.jsonl').is_file():
            raise ValueError('Started segment lacks journal: ' + str(started.parent / 'items.jsonl'))
    paths = sorted(journal_root.glob('*/*/items.jsonl'))
    if not paths:
        raise FileNotFoundError('MISSING: ' + str(journal_root / '*/*/items.jsonl'))
    first = io.read(paths[0].parent / 'environment.json')['binding']
    # Identify the manifest by its authenticated digest, never by a guessed population.
    if manifest_path:
        candidates = [Path(manifest_path)]
    else:
        candidates = sorted((src / 'items').glob('*.json'))
    matching = [p for p in candidates if io.digest(p) == first['items_sha256']]
    if len(matching) != 1:
        raise FileNotFoundError('MISSING: unique manifest with sha256 ' + first['items_sha256'] + ' at ' + str(src / 'items/*.json'))
    manifest_path = matching[0]
    manifest = io.read(manifest_path)
    items = {i['id']: i for i in manifest['items']}
    if len(items) != len(manifest['items']):
        raise ValueError('Duplicate manifest id')
    order = io.read(src / '9.json')['order']
    planned_types = [order[i] for i in expected['types']]
    planned = {k: i for k, i in items.items() if i['question_type'] in planned_types}
    baseline_name = 'b2' if manifest_path.name == 'room134.json' else 'b1'
    ref_no = reference_read if reference_read is not None else (read_no if step == 544 else 0)
    ref_dir = bases / baseline_name / 'work/ret/metadata/reads' / str(ref_no) / 'metadata/journals'
    envs = sorted(ref_dir.glob('*/*/environment.json'))
    if not envs:
        raise FileNotFoundError('MISSING: ' + str(ref_dir / '*/*/environment.json'))
    reference = io.read(envs[0])['binding']
    rows, shared = {}, None
    for path in paths:
        env = io.read(path.parent / 'environment.json')
        b = env['binding']
        fixed = dict(arms=['tower'], modes=[{'name': 'none'}], step=step, lineage='SFT', fixture=False,
                     stage1_select_rule=expected['stage1_select_rule'], perception_memo_modules=['g3t'],
                     save_own_depth=False, perception_memo=expected['perception_memo'],
                     perception_memo_verify_ids=expected['perception_memo_verify_ids'],
                     items_sha256=io.digest(manifest_path), item_set_sha256=manifest['item_set_sha256'])
        for key in ('reader_sha256', 'parity_code_sha256', 'evaluator_code_sha256', 'maker_sha256'):
            fixed[key] = reference[key]
        for key, value in fixed.items():
            if b.get(key) != value:
                raise ValueError('Journal binding differs: ' + key + ' in ' + str(path))
        if b['settings_sha256'] != canonical(env['settings']):
            raise ValueError('Settings hash differs')
        for key in ('stage1_select_rule', 'perception_memo', 'perception_memo_modules', 'perception_memo_verify_ids', 'save_own_depth'):
            if env['settings'].get(key) != fixed[key]:
                raise ValueError('Settings differ: ' + key)
        current = {k: b[k] for k in ('export_sha256', 'settings_sha256', 'artifact_manifest_sha256')}
        if shared is not None and current != shared:
            raise ValueError('Mixed journals')
        shared = current
        text = io.data(path).decode()
        if text and not text.endswith('\n'):
            raise ValueError('Uncommitted tail: ' + str(path))
        for line in text.splitlines():
            row = json.loads(line)
            key = row['id']
            if key in rows or key not in planned:
                raise ValueError('Duplicate or unplanned item: ' + key)
            if row.get('complete') is not True or row.get('arm') != 'tower' or row.get('mode') != 'none':
                raise ValueError('Uncommitted or wrong-arm row: ' + key)
            if row['type'] != items[key]['question_type'] or row['room_key'] != items[key]['room_key']:
                raise ValueError('Pair metadata differs: ' + key)
            # Scores need no heads, tokens, timing, or audit arrays.
            output = row['output']
            rows[key] = {**row, 'output': {k: output[k] for k in ('text', 'finish', 'calls', 'hook', 'scores') if k in output}}
    return rows, planned, manifest


def registered(io, bases):
    bases = io.path(bases)
    ba, ia, _ = load_read(io, bases/'b1/work/ret', bases/'b1', 0, 544, bases)
    bd, id_, _ = load_read(io, bases/'b1/work/ret', bases/'b1', 1, 544, bases)
    br, ir, _ = load_read(io, bases/'b2/work/ret', bases/'b2', 0, 544, bases)
    # The camera/distance read's 36 room ids also occur in room134: b2 is authoritative.
    return {**ba, **bd, **br}, {**ia, **id_, **ir}


def infer_package(io, root):
    identity = io.read(Path(root)/'metadata/IDENTITY.json')
    candidates = [Path(root).parent, Path(root), io.root/OUT3S/'A', io.root/OUT3S/'B',
                  io.root/OUT3/'bases/b1', io.root/OUT3/'bases/b2']
    for p in candidates:
        if io.path(p/'READ_PLAN.json').is_file() and io.path(p/'tower_sequence.py').is_file():
            if io.digest(p/'tower_sequence.py') == identity['operator_sha256']:
                return p
    raise FileNotFoundError('MISSING: matching READ_PLAN.json, tower_sequence.py, package/0.json and src/ beside ' + str(root) + '; pass --a-package/--b-package')
