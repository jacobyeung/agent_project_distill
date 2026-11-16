"""Training configs and the AWS smoke spec for the U, P, PD and XP arms, built through the trainer's own checks.

Each arm config is the reference arm's training config (RG2P2_A or RG2P2_X, pinned by SHA-256) plus an
overlay: unfrozen vision blocks at 2e-6, a head LR of 1e-4 and, except for U, a camera block. Every
config passes ddp_config.normalize_training_config and camera_config.normalize before it is written.

Run on Trinity or on AWS (CPU only):
  python tools/pd_arm_configs.py --base-a A/config.json --base-x X/config.json --bank-sha256 <sha> \
      --bank-path <path of the bank on the training host> --output-dir <dir>
"""
import argparse
import copy
import hashlib
import io
import json
import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from student_pilot import camera_config  # noqa: E402
from student_pilot.ddp_config import normalize_training_config, run_control_from_config  # noqa: E402

STUDENT = 'qwen35'
VISION_LR = 2e-6
HEAD_LR = 1e-4
HEAD_ONLY_STEPS = 50  # about 3% of the 1,550-step arms; the smoke uses 10
# A1P's camera gate (baseline window ending at step 50, check at step 200, at least a 20% drop).
CAMERA_GATE = {'baseline_step': 50, 'check_step': 200, 'window': 10, 'min_relative_drop': 0.2}
POSE = {
    # Cambrian-P: effective pose weight 1.0 (lambda 0.2 x inner 5.0), w_T = w_R = 1, w_f = 0.5, gamma 0.6,
    # four refinements, metric translations (s* = 1), d-bar trajectory balance (its Mix-MA setting).
    'weight': 1.0, 'weight_trans': 1.0, 'weight_rot': 1.0, 'weight_focal': 0.5, 'stage_gamma': 0.6,
    'refine_iterations': 4, 'trunk_depth': 4, 'trajectory_balance': True,
    # Width 512 instead of 2048 (cost), 8 heads; final-norm carrier states (feature_layers None).
    'embed_dim': 512, 'num_heads': 8, 'feature_layers': None,
    # Not in Cambrian-P (phase 2 needs them): gravity up of the origin camera and log d-bar.
    'weight_gravity': 0.5, 'weight_scale': 0.2,
    'head_only_steps': HEAD_ONLY_STEPS, 'warmup_ratio': 0.0,
}
POINT_DEPTH = {'weight': 0.5, 'weight_silog': 1.0, 'weight_metric': 0.5, 'weight_grad': 0.5, 'silog_lambda': 0.5,
               'd_proj': 256, 'mlp_hidden': 256, 'num_heads': 8, 'context_depth': 2, 'vit_layers': [9, 17, 25],
               'num_points_per_frame': 64, 'min_depth_m': 0.05, 'max_depth_m': 25.0}
ARMS = {'U': ('A', None), 'P': ('A', 'pose'), 'PD': ('A', 'pose_depth'), 'XP': ('X', 'pose')}
REFERENCE = {'A': 'RG2P2_A_W32_S17', 'X': 'RG2P2_X_W32_S17'}
BASE_CONFIG_SHA256 = {'A': 'cdee3d05b48b6dc6e86380d113c46f0d001cd3db597fe2bc20a4ec8a40c15451',
                      'X': '46a89b9a512e263f433d2eab3600628b7f834dcb4d2a85aaf68e04ba2a96ebd8'}
# Launcher closure of the RG2P2 arms (trainer base 9467aac5); the A1P closure adds the gate-stop handling.
CLOSURES = {'rg2p2_launcher': 'd9b941d1e641070e601204ac24c277ff8721e0445bb2f557eff4296aba827d72',
            'a1p_gate_stop_launcher': 'e4651a9a9bdc303550f5722728760060a03a187306b2a4fe15d550881c3e2329'}
JOB_NAME = re.compile(r'a15_cot_ap[0-9a-f]{8}')
BANNED = re.compile('sp' 'lit|dist' 'ill|vsi|revsi|qgen|scan' 'net|ark' 'it|qw' 'en|gemini', re.I)


def camera_block(kind, bank_sha256, bank_path, head_only_steps=HEAD_ONLY_STEPS, gate=None):
    if kind is None:
        return None
    block = {**copy.deepcopy(POSE), 'head_only_steps': head_only_steps, 'gate': copy.deepcopy(gate),
             'supervision': {'path': bank_path, 'sha256': bank_sha256}}
    if kind == 'pose_depth':
        block['point_depth'] = copy.deepcopy(POINT_DEPTH)
    elif kind != 'pose':
        raise ValueError('Unknown camera kind: ' + kind)
    camera_config.normalize(block)
    return block


def overlay(base, camera):
    config = {key: value for key, value in copy.deepcopy(base).items() if key != 'camera'}
    config.update(unfreeze_vision_blocks=True, vision_learning_rate=VISION_LR, head_learning_rate=HEAD_LR)
    if camera is not None:
        config['camera'] = camera
    return config


def validated(config):
    """The config, after the same checks train() and the protocol builder apply."""
    settings = normalize_training_config(config, STUDENT)
    run_control_from_config(config)
    camera = camera_config.from_training_config(config)
    if not settings.get('unfreeze_vision_blocks') or settings['vision_learning_rate'] != VISION_LR:
        raise ValueError('Arm configs unfreeze the vision blocks at 2e-6')
    return config, settings, camera


def arm_configs(base_a, base_x, bank_sha256, bank_path):
    bases = {'A': base_a, 'X': base_x}
    result = {}
    for arm, (rows, kind) in ARMS.items():
        camera = camera_block(kind, bank_sha256, bank_path, gate=CAMERA_GATE if kind else None)
        result[arm] = validated(overlay(bases[rows], camera))[0]
    return result


def smoke_config(base_a, bank_sha256, bank_path, world_size=8, steps=60):
    """PD's full stack on the A rows: short, frequent checkpoints, a visible head-only ramp, no gates."""
    camera = camera_block('pose_depth', bank_sha256, bank_path, head_only_steps=10)
    config = overlay(base_a, camera)
    config.update(world_size=world_size, effective_batch_size=32, max_steps=steps, checkpoint_every_steps=20)
    return validated(config)[0]


def canonical(value):
    return (json.dumps(value, indent=1, sort_keys=True) + '\n').encode()


def job_name():
    return 'a15_cot_ap' + secrets.token_hex(4)


def spec(configs, smoke, bank_sha256, smoke_scene_tokens, trainer_commit):
    names = {arm: job_name() for arm in [*configs, 'SMOKE']}
    if len(set(names.values())) != len(names) or not all(JOB_NAME.fullmatch(n) for n in names.values()):
        raise ValueError('Job names must be distinct opaque a15_cot_ap tokens')
    files = {arm: {'file': f'c_{hashlib.sha256(canonical(cfg)).hexdigest()[:12]}.json',
                   'sha256': hashlib.sha256(canonical(cfg)).hexdigest()} for arm, cfg in {**configs, 'SMOKE': smoke}.items()}
    if any(BANNED.search(item['file']) for item in files.values()):
        raise ValueError('An AWS-side file name identifies the project')
    return {
        'schema': 'pd_arm_spec_v2',
        'trainer_commit': trainer_commit,
        'student': STUDENT,
        'bank': {'sha256': bank_sha256, 'scene_tokens': smoke_scene_tokens,
                 'note': 'v2 label bank (first-hit depth only); ship the .npz under an opaque name and set the camera '
                         'supervision path to it, keeping this SHA-256'},
        'closures': CLOSURES,
        'closure_rule': ('The smoke runs without gates on the RG2P2 launcher closure. Its prestage hooks pin trainer files, '
                         'so rebuild them for this trainer commit. The arms need the RG2P2 launcher plus the A1P gate-stop '
                         'handling (a gate stop exits 3 and the job ends without a resume).'),
        'base_configs': {REFERENCE[k]: {'sha256': v} for k, v in BASE_CONFIG_SHA256.items()},
        'job_names': names,
        'configs': files,
        'smoke': {'arm': 'PD stack', 'gpus': smoke['world_size'], 'alternative_gpus': 4, 'steps': smoke['max_steps'],
                  'checkpoint_every_steps': smoke['checkpoint_every_steps'], 'rows': REFERENCE['A'],
                  'row_filter': 'rows whose (dataset, scene) tokens are in bank.scene_tokens, so every step carries labels',
                  'cpu_prestage': 'pre-stage the filtered rows on CPU first (no GPU-idle startup)',
                  'pass': ['first GPU work within 5 min of start', 'camera_label_audit pose_rows > 0 and depth_rows > 0',
                           'finite pose, gravity, scale and point_depth components every step',
                           'camera_backbone_gradient_scale 0 for steps < 10, then ramping to 1 by step 20',
                           'a rolling checkpoint at step 20 holds FP32 vision blocks; the export is BF16',
                           'peak memory below the card with the memory probe passing']},
        'arms': {arm: {'rows': REFERENCE[ARMS[arm][0]], 'world_size': 32, 'gpus': 32, 'steps': 1550,
                       'lm_gate': 'add from the reference run metrics (tools/pd_arm_configs.py lm_gate_from_metrics) '
                                  'before submitting' if ARMS[arm][1] else None}
                 for arm in configs},
        'ledger': 'record every job name with its run in lanes/aws_reserve/AWS_JOB_LEDGER.jsonl on Trinity',
    }


def lm_gate_from_metrics(metrics_path, check_step=200, window=10, max_relative_increase=0.10, run='reference'):
    """A1P-style LM gate: the reference run's per-step loss over the window ending at check_step."""
    raw = Path(metrics_path).read_bytes()
    steps = list(range(check_step - window + 1, check_step + 1))
    losses = {}
    for line in io.StringIO(raw.decode()):
        if line.strip():
            metric = json.loads(line)
            losses[metric['step']] = metric['loss']
    if any(step not in losses for step in steps):
        raise ValueError('The reference metrics lack a step of the LM gate window')
    gate = {'check_step': check_step, 'window': window, 'max_relative_increase': max_relative_increase,
            'reference': {'run': run, 'metrics_sha256': hashlib.sha256(raw).hexdigest(), 'steps': steps,
                          'values': [float(losses[s]) for s in steps]}}
    camera_config.normalize({'lm_gate': gate})
    return gate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-a', required=True)
    parser.add_argument('--base-x', required=True)
    parser.add_argument('--bank-sha256', required=True)
    parser.add_argument('--bank-path', required=True)
    parser.add_argument('--bank-scene-tokens', required=True, help='JSON list of [dataset, scene] tokens of the smoke bank')
    parser.add_argument('--trainer-commit', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args(argv)
    bases = {}
    for key, path in (('A', args.base_a), ('X', args.base_x)):
        raw = Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != BASE_CONFIG_SHA256[key]:
            raise ValueError(f'Base config {key} differs from its pinned SHA-256')
        bases[key] = json.loads(raw)
    configs = arm_configs(bases['A'], bases['X'], args.bank_sha256, args.bank_path)
    smoke = smoke_config(bases['A'], args.bank_sha256, args.bank_path)
    result = spec(configs, smoke, args.bank_sha256, json.loads(Path(args.bank_scene_tokens).read_text()), args.trainer_commit)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for arm, cfg in {**configs, 'SMOKE': smoke}.items():
        with (out / result['configs'][arm]['file']).open('xb') as handle:
            handle.write(canonical(cfg))
    with (out / 'SPEC.json').open('x') as handle:
        handle.write(json.dumps(result, indent=1) + '\n')
    print(json.dumps({'spec': str(out / 'SPEC.json'), 'job_names': result['job_names']}))


if __name__ == '__main__':
    main()
