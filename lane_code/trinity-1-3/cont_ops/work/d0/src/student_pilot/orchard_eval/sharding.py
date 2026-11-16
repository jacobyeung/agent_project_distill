"""Answer-free shard assignment and immutable receipt census."""
from pathlib import Path

from .contracts import (binding, digest, load_json, output_path, provisional_mode, safe_id,
                        validate_receipt, verify_pin, write_once)


def validate_shard(index, count):
    if type(count) is not int or count < 1 or type(index) is not int or not 0 <= index < count:
        raise ValueError('Shard count must be positive and 0 <= shard index < shard count')


def shard_work_id(cell_work_id, index, count):
    validate_shard(index, count)
    return cell_work_id if count == 1 else f'{cell_work_id}__shard_{index}_of_{count}'


def assignment(header, count):
    return {'schema': 'student-shard-assignment-v1',
            'generation_manifest': header['core']['generation_manifest'],
            'shard_count': count,
            'assignments': [{'qid': qid, 'shard_index': k % count}
                            for k, qid in enumerate(header['core']['ordered_ids'])]}


def manifest_value(plan, index):
    return {'schema': 'student-shard-manifest-v1', 'assignment': plan,
            'assignment_sha256': digest(plan), 'shard_index': index,
            'ordered_ids': [row['qid'] for row in plan['assignments'] if row['shard_index'] == index]}


def register_shard(output, header, index, count, destination, admission, work, root, paper, resume):
    """Called under the cohort lock, before any item can start."""
    plan_path = output / 'sharding.json'
    if not plan_path.exists() and count == 1 and destination is None:
        return
    plan = assignment(header, count)
    if plan_path.exists():
        if load_json(plan_path) != plan:
            raise ValueError('Shard assignment/count differs from this frozen cell')
    else:
        if (output / 'attempts.jsonl').exists() or (output / 'completion.json').exists():
            raise ValueError('Cannot add sharding to an existing unsharded cell')
        write_once(plan_path, plan, root, paper)
    destination = output_path(destination or output / 'shards' / f'{index}.manifest.json', root, paper)
    registration = output / 'shard_workers' / f'{index}.json'
    value = manifest_value(plan, index)
    if registration.exists():
        previous = load_json(registration)
        if not resume:
            raise ValueError('Shard exists; explicit resume is required')
        if (previous['manifest']['path'] != str(destination.absolute())
                or load_json(verify_pin(previous['manifest'])) != value or previous['work_id'] != work):
            raise ValueError('Shard manifest or work identity drift')
    else:
        if destination.exists():
            if load_json(destination) != value:
                raise ValueError('Shard manifest output differs from its assignment')
            pin = binding(destination)
        else:
            pin = write_once(destination, value, root, paper)
        write_once(registration, {'schema': 'student-shard-registration-v1', 'shard_index': index,
                                 'manifest': pin, 'lease': admission, 'work_id': work}, root, paper)


def shard_census(output, header, require_complete=True):
    """Verify every published shard and require all workers for a complete cell."""
    output = Path(output)
    if not (output / 'sharding.json').exists():
        return True
    plan = load_json(output / 'sharding.json')
    count = plan['shard_count']
    validate_shard(0, count)
    if plan != assignment(header, count):
        raise ValueError('Shard assignment manifest differs from generation membership')
    seen, ids = set(), []
    for path in sorted((output / 'shard_workers').glob('*.json')):
        entry = load_json(path)
        index = entry['shard_index']
        validate_shard(index, count)
        if index in seen or path.name != f'{index}.json':
            raise ValueError('Duplicate or misnamed shard registration')
        seen.add(index)
        value = load_json(verify_pin(entry['manifest']))
        if value != manifest_value(plan, index):
            raise ValueError('Shard manifest assignment/hash mismatch')
        ids.extend(value['ordered_ids'])
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate item across shard manifests')
    complete = seen == set(range(count)) and set(ids) == set(header['core']['ordered_ids'])
    if require_complete and not complete:
        raise ValueError('Missing shard manifests; cell census is incomplete')
    return complete


def receipt_census(output, header, require_complete=True, provisional_diagnostic=None):
    provisional_mode(header['core'], provisional_diagnostic)
    receipts = {}
    for path in sorted((Path(output) / 'questions').glob('*.json')):
        receipt = validate_receipt(load_json(path), header, provisional_diagnostic)
        qid = receipt['qid']
        if qid in receipts or path.name != f'{safe_id(qid)}.json':
            raise ValueError('Duplicate or misnamed question receipt')
        receipts[qid] = receipt
    if require_complete and set(receipts) != set(header['core']['ordered_ids']):
        raise ValueError('Missing question receipts; cell census is incomplete')
    shard_census(output, header, require_complete)
    return receipts
