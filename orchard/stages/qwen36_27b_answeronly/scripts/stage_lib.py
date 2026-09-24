import hashlib
import json
from pathlib import Path


STAGE = Path(__file__).resolve().parents[1]
STUDENT = 'qwen36_27b'
TRAINER_COMMIT = '433d8a117bf94bcd8214de9a6d6e149ff6f5f74f'
EPOCHS = {'setH': 3, 'setH_e1': 1, 'fullpool': 1}


def manifest():
    value = json.loads((STAGE / 'manifest.json').read_text())
    if value['student'] != STUDENT or value['trainer_commit'] != TRAINER_COMMIT:
        raise ValueError('The stage must preserve the student and trainer pins')
    if set(value['variants']) != set(EPOCHS):
        raise ValueError('The stage must contain exactly the three requested variants')
    return value


def variant_spec(variant):
    if variant not in EPOCHS:
        raise ValueError('Unknown answer-only variant: ' + variant)
    spec = manifest()['variants'][variant]
    if spec['epochs'] != EPOCHS[variant] or spec['config'] != 'qwen36_27b_ao_' + variant + '.json':
        raise ValueError('Variant config name or epoch count changed')
    if spec['dataset'] != ('fullpool' if variant == 'fullpool' else 'setH'):
        raise ValueError('Variant dataset selection changed')
    return spec


def dataset_identity(variant):
    return manifest()['datasets'][variant_spec(variant)['dataset']]


def load_student_config(here, student=STUDENT):
    if student != STUDENT:
        raise ValueError('The model-staging key must remain qwen36_27b')
    return json.loads((Path(here) / 'configs' / (student + '.json')).read_text())


def validate_config(variant, config):
    baseline = load_student_config(STAGE)
    expected = {**baseline, 'epochs': variant_spec(variant)['epochs']}
    if config != expected:
        changed = sorted(key for key in set(config) | set(expected) if key not in config or key not in expected or config[key] != expected[key])
        raise ValueError('Only the documented epoch count may change: ' + ', '.join(changed))
    if (config['epochs'], config['world_size'], config['effective_batch_size']) != (EPOCHS[variant], 4, 32):
        raise ValueError('The matched recipe requires the declared epochs, world 4, and batch 32')
    return config


def selected_config_path(variant):
    bundled = STAGE / 'configs' / variant_spec(variant)['config']
    validate_config(variant, json.loads(bundled.read_text()))
    frozen = STAGE / 'frozen_configs' / variant / 'configs' / (STUDENT + '.json')
    if frozen.exists():
        if frozen.read_bytes() != bundled.read_bytes():
            raise ValueError('Transferred frozen config differs from the selected variant')
        return frozen
    return bundled


def freeze_config(variant, here):
    source = selected_config_path(variant)
    target = Path(here) / 'configs' / (STUDENT + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != source.read_bytes():
            raise ValueError('Refusing to overwrite a different frozen config: ' + str(target))
    else:
        with target.open('xb') as output:
            output.write(source.read_bytes())
    validate_config(variant, load_student_config(here))
    return target


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_identity(expected, hashes, rows):
    if set(hashes) != {'candidate_index.jsonl', 'split_trainer.json'}:
        raise ValueError('Identity must bind candidate_index.jsonl and split_trainer.json')
    for name, wanted in expected['sha256'].items():
        if hashes[name] != wanted:
            raise ValueError(name + ' sha256 differs from the pinned dataset')
    if rows != expected['rows']['total']:
        raise ValueError('Candidate row count differs from the pinned dataset')


def verify_dataset(variant, dataset_root, split_record):
    index = Path(dataset_root) / 'candidate_index.jsonl'
    split = Path(split_record)
    if split.name != 'split_trainer.json':
        raise ValueError('The split must retain its published split_trainer.json filename')
    hashes = {index.name: sha256(index), split.name: sha256(split)}
    with index.open('rb') as source:
        rows = sum(1 for _ in source)
    verify_identity(dataset_identity(variant), hashes, rows)
    return hashes, rows
