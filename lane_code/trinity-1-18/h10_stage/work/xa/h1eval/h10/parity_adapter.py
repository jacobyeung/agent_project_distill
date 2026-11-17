"""Metadata-only binding to the reviewed parity reader and its scored journals."""
import json
import os
from pathlib import Path
from h1eval.items import digest, sha

DEFAULT_SETTINGS = '/scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit/settings_bw.json'
ENTRY = 'e2e_reader.parity:make_real'


def read(path):
    return json.loads(Path(path).read_text())


def settings_for(path, name):
    settings = read(path)
    settings.update(settings.get('item_sets', {}).get(name, {}))
    overlay = os.environ.get('H10_OVERLAY')
    if overlay:
        overlay = Path(overlay).resolve()
        if not (overlay.is_relative_to('/scratch') or overlay.is_relative_to('/dev/shm')):
            raise ValueError('Stage the runtime overlay on /scratch or /dev/shm')
        settings['env_roots'] = list(dict.fromkeys([*settings.get('env_roots', []), str(overlay)]))
    settings['arm'] = 'own_depth'
    return settings


def validate_own_settings(settings, items):
    if any(r['question_type'] == 'object_abs_distance' for r in items):
        if not settings.get('sam3') or not settings.get('selector_head'):
            raise ValueError('Own ground/gap requires staged SAM 3 and selector_head in settings')


def artifact_spec(path):
    value = read(path)
    if not all(k in value for k in ('root', 'name', 'sha256')):
        raise ValueError('Expected b04 artifact binding JSON with root, name, sha256')
    return value


def map_items(items, settings, *, name='devs1_routed'):
    if name=='r0dev_f32':
        from .reserve_frames import bind
        return bind(items,settings)
    from e2e_reader import parity
    from student_pilot.h1_r0 import room_key
    from parity_kit.common import TASKS, FRAMES, DENSE, rows
    captures = parity._captures(settings.get('frames_json', FRAMES))
    dense = parity._captures(settings.get('dense_manifest', DENSE))
    # Official ReVSI needs an explicit native task binding; never borrow dev-S1 clips.
    if name == 'revsi999' and not settings.get('tasks'):
        raise ValueError('ReVSI frames not staged: supply native tasks, frames_json, dense_manifest and frames_root')
    tasks = [t for p in settings.get('tasks', TASKS) for t in rows(p)]
    by_id = {str(t['id']): t for t in tasks}
    if len(by_id) != len(tasks):
        raise ValueError('Duplicate native task IDs')
    bound_settings = dict(settings, frames_json={'captures': captures}, dense_manifest={'captures': dense})
    mapped, mapping = {}, []
    for item in items:
        task = by_id.get(item['id'])
        if task is None:
            prefix = 'ReVSI frames not staged: ' if name == 'revsi999' else ''
            raise ValueError(prefix + 'unmapped item ' + item['id'])
        for field in ('question', 'question_type', 'options', 'dataset', 'scene', 'native', 'source_frame_indices'):
            if field in item and item[field] != task.get(field):
                raise ValueError('Native item binding differs: ' + item['id'] + ':' + field)
        if str(item.get('answer', item.get('ground_truth'))) != str(task['answer']):
            raise ValueError('Native answer binding differs: ' + item['id'])
        if room_key(task) != item['room_key']:
            raise ValueError('Native physical-room binding differs: ' + item['id'])
        if task.get('native') not in captures or task.get('native') not in dense:
            raise ValueError('frames not staged: ' + item['id'])
        b = parity.bind_item(task, bound_settings, verify=False)
        c, d = captures[task['native']], dense[task['native']]
        mapping.append(dict(id=item['id'], key=parity.key(task), native=task['native'],
                            task_sha256=digest(task), layout_count=32,
                            anchor_indices=b['frames']['anchor_indices'],
                            dense_count=len(b['frames']['dense_indices']),
                            frame_binding_sha256=digest(dict(anchors=c, dense=d))))
        mapped[item['id']] = task
    if len({r['key'] for r in mapping}) != len(items):
        raise ValueError('Duplicate mapped reader keys')
    return mapped, dict(schema='h10-parity-mapping-v1', items=mapping, sha256=digest(mapping))


def reader_code_hash(reader_root):
    # Pin runner source only. parity_kit also holds mutable journals and restored weights.
    root = Path(reader_root) / 'parity_kit'
    files = sorted(root.glob('*.py'))
    if not files:raise ValueError('Missing parity runner source')
    return digest([(p.name, sha(p)) for p in files])


def prepare_runtime(settings):
    """Select the pinned native tree before importing the model or geometry modules."""
    import sys
    import student_pilot
    from parity_kit.common import install
    tree = Path(settings['tree']).resolve()
    install(tree)
    # h1_r0 is the kit's reserve checker. All model/read modules must come from the sealed tree.
    for name, module in tuple(sys.modules.items()):
        if name.startswith('student_pilot.') and name != 'student_pilot.h1_r0':
            source = getattr(module, '__file__', None)
            if source and not Path(source).resolve().is_relative_to(tree):
                raise ValueError('Native tree already imported from another root: ' + name)
    student_pilot.__path__ = [str(tree / 'student_pilot')]


def parity_tower_records(directory, items, mapped, *, settings, export, artifact, reader_root):
    from parity_kit.provenance import validate_rows, comparison_identity, receipt_digest
    root = Path(directory)
    journals = sorted((root / 'gpu_results').glob('own_depth_p*/items.jsonl'))
    if not journals:
        journals = sorted(root.glob('own_depth_p*/items.jsonl'))
    if not journals and (root / 'items.jsonl').exists():
        journals = [root / 'items.jsonl']
    if not journals:
        raise ValueError('No b04 own_depth partition journals')
    rows, pins, identity = {}, [], None
    restore = read(Path(export) / 'RESTORE.json')
    expected_artifact = artifact_spec(artifact)
    from parity_kit.common import TASKS, FRAMES, DENSE, REQUEST
    metadata = {n: settings.get(n, default) for n, default in
                [('frames_json', FRAMES), ('dense_manifest', DENSE), ('request', REQUEST)]}
    metadata['config'] = settings['config']
    expected_tasks = [sha(p) for p in settings.get('tasks', TASKS)]
    for journal in journals:
        receipt_path = journal.parent / 'LOAD_RECEIPT.json'
        receipt = read(receipt_path)
        if sha(receipt_path) != receipt_digest(receipt):
            raise ValueError('Tower receipt bytes differ')
        batch = []
        with journal.open() as stream:
            for line in stream:
                if not line.endswith('\n'):
                    raise ValueError('Incomplete tower JSONL tail')
                batch.append(json.loads(line))
        validate_rows(batch, receipt, sha(receipt_path))
        if receipt['arm'] != 'own_depth':
            raise ValueError('Tower arm must be own_depth')
        if set(receipt['keys']) != {r['key'] for r in batch}:
            raise ValueError('Tower partition is missing items')
        comparable = comparison_identity(receipt)
        if identity is not None and comparable != identity:
            raise ValueError('Tower partition bindings differ')
        identity = comparable
        if receipt['restore'] != restore or receipt['restore_pin']['sha256'] != sha(Path(export) / 'RESTORE.json'):
            raise ValueError('Tower export restore differs')
        if receipt['artifact_manifest'] != expected_artifact:
            raise ValueError('Tower artifact binding differs')
        for field, path in metadata.items():
            if receipt['inputs'][field]['sha256'] != sha(path):
                raise ValueError('Tower metadata differs: ' + field)
        if [p['sha256'] for p in receipt['inputs']['tasks']] != expected_tasks:
            raise ValueError('Tower task pins differ')
        for field in ('tree', 'frames_root', 'selector_head', 'scale_head', 'sam3', 'require_dense64'):
            if receipt['inputs']['settings'].get(field) != settings.get(field):
                raise ValueError('Tower perception settings differ: ' + field)
        code = receipt['inputs']['runtime_code']
        code_by_name = {}
        for pin in code:
            path = Path(pin['path'])
            if path.parent.name in ('e2e_reader', 'parity_kit'):
                key = (path.parent.name, path.name)
                if key in code_by_name:
                    raise ValueError('Duplicate tower code pins')
                code_by_name[key] = pin['sha256']
        expected_code = [(folder, path) for folder in ('e2e_reader', 'parity_kit')
                         for path in sorted((Path(reader_root) / folder).glob('*.py'))]
        if not expected_code or set(code_by_name) != {(folder, p.name) for folder, p in expected_code}:
            raise ValueError('Tower reader code inventory differs')
        for folder, path in expected_code:
            if code_by_name.get((folder, path.name)) != sha(path):
                raise ValueError('Tower reader code differs: ' + path.name)
        from parity_kit.common import C8R
        policy_pins = [p for p in code if Path(p['path']).name == 'reader_policy.py']
        if len(policy_pins) != 1 or policy_pins[0]['sha256'] != sha(C8R / 'reader_policy.py'):
            raise ValueError('Tower decode policy differs')
        for row in batch:
            key = row['key']
            if key in rows:
                raise ValueError('Duplicate tower items')
            if not isinstance(row.get('text'), str) or not row.get('finish') or row.get('frames', {}).get('count') != 32 or row.get('id') != key:
                raise ValueError('Incomplete tower record')
            rows[key] = row
        pins.append(dict(path=str(journal), records_sha256=sha(journal), receipt_sha256=sha(receipt_path)))
    result = []
    for item in items:
        from e2e_reader.parity import key
        task = mapped[item['id']]
        row = rows.get(key(task))
        if row is None:
            raise ValueError('Tower reuse is missing items: ' + item['id'])
        if row['question_type'] != task['question_type'] or row['room'] != task['room']:
            raise ValueError('Tower item binding differs')
        result.append(dict(id=item['id'], room_key=item['room_key'], type=item['question_type'],
                           arm='tower', mode='none', intervention={'name': 'none'}, applied=False,
                           output=row, seconds=row['seconds'], complete=True, reused=True))
    return result, dict(format='parity-load-v2', partitions=pins,
                       limitations=['Rows do not carry the kit item-set digest; task-file pins and native keys bind items.',
                                    'Rows attest completed reads; this conversion does not rehash model payloads.',
                                    'Runtime is checked across tower partitions, not equated to the own runtime.'])
