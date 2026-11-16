import argparse
import json
from pathlib import Path
import re
import shutil

from stage_lib import (
    EPOCHS, STAGE, STUDENT, TRAINER_COMMIT, dataset_identity, freeze_config,
    load_student_config, selected_config_path, sha256, verify_dataset,
)


CHAIN_FILES = tuple('scripts/orchard/' + name for name in (
    'common.sh', 'submit_train.sh', 'run_train.sh', 'train_job.py', 'stage_model.py',
))
SLURM_FILES = ('slurm/train_qwen36_27b.slurm', 'slurm/train_qwen36_27b_ao.slurm')


def verify_frozen(deploy, receipt):
    if json.loads((deploy / 'answeronly_stage.json').read_text()) != receipt:
        raise ValueError('Deployment identity changed; use a new deployment and run ID')
    for relative, expected in receipt['source_files'].items():
        if sha256(deploy / relative) != expected:
            raise ValueError('Frozen deployment code changed: ' + relative)
    for relative in SLURM_FILES:
        if sha256(deploy / relative) != receipt['slurm_sha256']:
            raise ValueError('Frozen Slurm wrapper changed: ' + relative)
    if sha256(deploy / 'scripts/orchard/configs/qwen36_27b.json') != receipt['config_sha256']:
        raise ValueError('Frozen qwen36_27b config changed')


def prepare_deployment(base, deploy, variant, run_id, dataset, split, reviewed_sha256):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,100}', run_id):
        raise ValueError('Use a plain unique run identifier')
    base, deploy = Path(base).resolve(), Path(deploy).absolute()
    if deploy.is_symlink():
        raise ValueError('The frozen deployment must not be a symlink')
    deploy = deploy.resolve()
    if base == deploy or base in deploy.parents or deploy in base.parents:
        raise ValueError('Use a separate deployment root, never the source or its ancestors/children')
    if not re.fullmatch(r'[0-9a-f]{64}', reviewed_sha256):
        raise ValueError('Review Orchard stage_model.py and supply its SHA256')
    source_files = {relative: sha256(base / relative) for relative in CHAIN_FILES}
    if source_files['scripts/orchard/stage_model.py'] != reviewed_sha256:
        raise ValueError('Orchard stage_model.py differs from the reviewed bytes')
    if load_student_config(base / 'scripts/orchard') != load_student_config(STAGE):
        raise ValueError('The source deployment config differs from the arm C template')
    config = selected_config_path(variant)
    wrapper = STAGE / 'slurm/train_qwen36_27b_ao.slurm'
    receipt = {
        'schema': 'qwen36-27b-answeronly-deployment-v1',
        'student': STUDENT,
        'variant': variant,
        'run_id': run_id,
        'dataset_root': str(dataset),
        'split_record': str(split),
        'dataset_identity': dataset_identity(variant),
        'trainer_commit': TRAINER_COMMIT,
        'source_deployment': str(base),
        'source_files': source_files,
        'stage_model_reviewed_sha256': reviewed_sha256,
        'config_sha256': sha256(config),
        'slurm_sha256': sha256(wrapper),
    }
    if deploy.exists():
        verify_frozen(deploy, receipt)
        return receipt
    deploy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(base, deploy)
    for relative in ('scripts/orchard/configs/qwen36_27b.json', 'slurm/train_qwen36_27b.slurm'):
        original = deploy / relative
        quarantine = deploy / '_quarantine/answeronly_stage' / relative
        quarantine.parent.mkdir(parents=True, exist_ok=True)
        if quarantine.exists():
            raise ValueError('The source deployment already contains an answer-only quarantine')
        original.rename(quarantine)
    freeze_config(variant, deploy / 'scripts/orchard')
    for relative in SLURM_FILES:
        with (deploy / relative).open('xb') as output:
            output.write(wrapper.read_bytes())
    with (deploy / 'answeronly_stage.json').open('x') as output:
        output.write(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    verify_frozen(deploy, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=EPOCHS, required=True)
    parser.add_argument('--base-deploy', type=Path, required=True)
    parser.add_argument('--deploy', type=Path, required=True)
    parser.add_argument('--dataset-root', type=Path, required=True)
    parser.add_argument('--split-record', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--stage-model-reviewed-sha256', required=True)
    args = parser.parse_args()
    verify_dataset(args.variant, args.dataset_root, args.split_record)
    prepare_deployment(args.base_deploy, args.deploy, args.variant, args.run_id,
                       args.dataset_root, args.split_record, args.stage_model_reviewed_sha256)
    print('Verified dataset and frozen deployment: ' + str(args.deploy))


if __name__ == '__main__':
    main()
