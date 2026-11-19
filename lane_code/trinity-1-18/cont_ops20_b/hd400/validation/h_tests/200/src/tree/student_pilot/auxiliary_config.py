"""Training-only auxiliary settings; omitted settings preserve the old config hash."""
import math

DEFAULTS = {
    'pose_weight': 0.0, 'depth_weight': 0.0, 'warmup_ratio': 0.1,
    'head_width': 128, 'depth_grid': 4, 'translation_unit_m': 1.0,
    'temporal_patch_size': 2, 'frame_count': 32,
    'representation': 'first_tubelet_camera_c2w_rotation_columns6_translation3_v1',
    'feature_source': 'final_language_norm_video_tokens_v1',
    'supervision': None,
}
# Perception heads added after the pose/depth contract. A config that names none
# of these keys normalizes exactly as before, so its hash is unchanged.
PERCEPTION_DEFAULTS = {
    'count_weight': 0.0, 'object_weight': 0.0, 'reason_weight': 0.0,
    'reason_mix_prob': 0.3, 'reason_mix_start': 0.3,
    'query_contract': 'qwen35_single_id_query_tokens_v3',
    'category_source': 'final_language_norm_question_span_mean_v1',
}
SIDECAR_OBJECTIVES = ('pose', 'depth', 'count', 'object')
OBJECTIVES = SIDECAR_OBJECTIVES + ('reason',)
FIXED = ('depth_grid', 'temporal_patch_size', 'frame_count', 'representation', 'feature_source',
         'query_contract', 'category_source')


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def normalize(value):
    if not isinstance(value, dict) or set(value) - DEFAULTS.keys() - PERCEPTION_DEFAULTS.keys():
        raise ValueError('Unknown auxiliary configuration')
    defaults = {**DEFAULTS, **PERCEPTION_DEFAULTS} if set(value) & PERCEPTION_DEFAULTS.keys() else DEFAULTS
    cfg = {**defaults, **value}
    weights = [name + '_weight' for name in OBJECTIVES if name + '_weight' in cfg]
    numbers = weights + [k for k in ('warmup_ratio', 'translation_unit_m', 'reason_mix_prob', 'reason_mix_start') if k in cfg]
    for k in numbers:
        if not finite_number(cfg[k]):
            raise ValueError('Nonfinite auxiliary setting: ' + k)
    if min(cfg[k] for k in weights) < 0 or not 0 <= cfg['warmup_ratio'] <= 1 or cfg['translation_unit_m'] <= 0:
        raise ValueError('Invalid auxiliary loss weight, warmup, or translation unit')
    if 'reason_mix_prob' in cfg and not (0 <= cfg['reason_mix_prob'] <= 1 and 0 <= cfg['reason_mix_start'] <= 1):
        raise ValueError('Invalid prediction-mixing probability or start fraction')
    if type(cfg['head_width']) is not int or not 1 <= cfg['head_width'] <= 1024:
        raise ValueError('Invalid auxiliary head width')
    for k in FIXED:
        if k in cfg and (cfg[k] != defaults[k] or type(cfg[k]) is not type(defaults[k])):
            raise ValueError('Unsupported auxiliary contract: ' + k)
    pin = cfg['supervision']
    if sidecar_enabled(cfg):
        if not isinstance(pin, dict) or set(pin) != {'path', 'sha256'} or not isinstance(pin['path'], str) or not pin['path']:
            raise ValueError('Enabled auxiliary losses require a pinned supervision sidecar')
        if not isinstance(pin['sha256'], str) or len(pin['sha256']) != 64 or any(c not in '0123456789abcdef' for c in pin['sha256']):
            raise ValueError('Invalid supervision SHA256')
    return cfg


def weight(cfg, name):
    return cfg.get(name + '_weight', 0) if cfg else 0


def sidecar_enabled(cfg):
    """Objectives whose targets come from the pinned per-row GT sidecar."""
    return bool(cfg and any(weight(cfg, name) > 0 for name in SIDECAR_OBJECTIVES))


def reason_enabled(cfg):
    """Heads called at query tokens; their targets come from the training text itself."""
    return bool(cfg and weight(cfg, 'reason') > 0)


def enabled(cfg):
    return sidecar_enabled(cfg) or reason_enabled(cfg)


def ramp(step, total_steps, cfg):
    if total_steps < 1 or not 0 <= step < total_steps:
        raise ValueError('Auxiliary step is outside the training plan')
    warmup = math.ceil(total_steps * cfg['warmup_ratio'])
    return min(1.0, (step + 1) / max(1, warmup))


def mixing_active(step, total_steps, cfg):
    """Prediction mixing starts at a fixed fraction of the scheduled optimizer steps."""
    if not reason_enabled(cfg) or cfg['reason_mix_prob'] <= 0:
        return False
    if total_steps < 1 or not 0 <= step < total_steps:
        raise ValueError('Auxiliary step is outside the training plan')
    return step >= math.ceil(total_steps * cfg['reason_mix_start'])
