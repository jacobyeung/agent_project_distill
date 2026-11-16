"""Camera-pose and point-depth supervision settings (Cambrian-P style, training only).

The settings live in the training config's top-level "camera" object and in
protocol["camera"] with its own hash, never inside protocol["training"], so
evaluators that normalize the plain training settings see nothing new.

Every loss weight is absolute: the camera term added to a row's loss is
  weight * pose + weight_gravity * gravity + weight_scale * scale + point_depth.weight * depth.
"""
import math

CARRIER_TOKEN = '<|fim_middle|>'
POSE_ENCODING = 'opencv_cam_from_frame0_anchor_second_of_pair_T3_quatxyzw4_fovhw2_v2'
DEFAULTS = {
    'weight': 0.0, 'weight_trans': 1.0, 'weight_rot': 1.0, 'weight_focal': 0.5,
    'weight_gravity': 0.0, 'weight_scale': 0.0, 'frame_addressing': 'group16', 'point_depth': None,
    'trajectory_balance': True, 'min_trajectory_scale_m': 0.05,
    'embed_dim': 2048, 'trunk_depth': 4, 'num_heads': 16, 'refine_iterations': 4, 'stage_gamma': 0.6,
    'component_reduction': 'mean', 'loss_clamp': 100.0, 'warmup_ratio': 0.0, 'supervision': None,
    # None reads the final-norm states at the carriers (Cambrian-P's hidden_states[-1]). A list of
    # 1-based decoder-layer indices (an ablation) mixes those layers' carrier states with learned softmax weights.
    'feature_layers': None, 'feature_layer_convention': 'hidden_states_index_k_after_k_layers_last_is_final_norm_v1',
    # Head-only warmup: for optimizer steps < head_only_steps the head losses send no gradient into the
    # student (LoRA, vision blocks); their gradient then ramps linearly to full over the next head_only_steps.
    # The language-model loss trains the student as usual throughout, so arms stay matched with the no-head arm.
    'head_only_steps': 0,
    # Optional early-stop gate on the camera loss (student_pilot.camera_gate); None is off.
    'gate': None,
    # Optional early-stop gate on the text-row language-model loss against a reference run; None is off.
    'lm_gate': None,
    'placement': 'append_after_temporal_group_video_tokens_v1',
    'token_scheme': 'first_and_rest_learned_v1',
    # Temporal group g fuses sampled frames 2g and 2g+1 (0-based); its targets describe frame 2g+1.
    'representative_frame': 'second_of_temporal_pair_v1',
    # Every pose is relative to the camera of sampled frame 0 (phase 2's camera 1).
    'pose_origin': 'first_sampled_frame_v1',
    'pose_encoding': POSE_ENCODING,
    'carrier_token': CARRIER_TOKEN,
}
FIXED = ('placement', 'token_scheme', 'representative_frame', 'pose_origin', 'pose_encoding', 'carrier_token',
         'feature_layer_convention')
# Optional row routing, present in a config only when set (so every other camera config keeps its canonical bytes).
# Absent: every labelled row trains the heads (the PD design). CAMBRIAN_P_ROUTING (Cambrian-P, arXiv 2605.22819 Sec. 3.3):
# question rows train the next-token loss only (no carriers, no head loss); pose-only rows train the camera head and,
# where the label bank holds depth at their frames, the point-depth head.
CAMBRIAN_P_ROUTING = 'cambrian_p_question_rows_lm_only_pose_rows_heads_v1'
# Absent keys preserve legacy artifacts. New decoupled runs can explicitly name
# their origin conditioning and smooth, bounded FoV parameterization.
OPTIONAL = {'row_routing': (CAMBRIAN_P_ROUTING,),
            'pose_input': ('spatial_tokens_v1',),
            'pose_reference': ('first_group_concat_v1',),
            'fov_activation': ('bounded_sigmoid_v1',)}
# CameraSupervision children, plus the separately attached geometry projector (init_modules.geometry).
# Keep this key absent from legacy canonical configs.
FREEZABLE_MODULES = ('projector', 'head', 'point_depth', 'cam_token_connector', 'cam_head_bypass', 'geometry')
G3T_PRIOR_DEFAULTS = {
    'enabled': True,
    'cam_token_dim': 4096,
    'carrier_connector': True,
    'head_bypass': True,
    'pose_prior': True,
}


def normalize_g3t_prior(value):
    if value is None or value is False:
        return None
    if value is True:
        return dict(G3T_PRIOR_DEFAULTS)
    if not isinstance(value, dict) or set(value) - G3T_PRIOR_DEFAULTS.keys():
        raise ValueError('Unknown camera g3t_prior configuration')
    cfg = {**G3T_PRIOR_DEFAULTS, **value}
    for key in ('enabled', 'carrier_connector', 'head_bypass', 'pose_prior'):
        if type(cfg[key]) is not bool:
            raise ValueError('Invalid camera g3t_prior flag: ' + key)
    if type(cfg['cam_token_dim']) is not int or not (16 <= cfg['cam_token_dim'] <= 16384 and cfg['cam_token_dim'] % 2 == 0):
        raise ValueError('Invalid camera g3t_prior cam_token_dim')
    if not cfg['enabled']:
        return None
    if not (cfg['carrier_connector'] or cfg['head_bypass'] or cfg['pose_prior']):
        raise ValueError('Enabled camera g3t_prior must enable at least one path')
    return cfg


def g3t_prior_enabled(cfg):
    prior = (cfg or {}).get('g3t_prior')
    return bool(isinstance(prior, dict) and prior.get('enabled'))


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def normalize(value):
    if not isinstance(value, dict) or set(value) - DEFAULTS.keys() - OPTIONAL.keys() - {'g3t_prior', 'freeze_modules', 'max_groups'}:
        raise ValueError('Unknown camera configuration')
    if 'max_groups' in value and (type(value['max_groups']) is not int or not 16 <= value['max_groups'] <= 48):
        raise ValueError('Camera max_groups must be an integer in 16..48')
    for key, allowed in OPTIONAL.items():
        if key in value and value[key] not in allowed:
            raise ValueError(f'Unsupported camera {key}: {value[key]}')
    cfg = {**DEFAULTS, **value}
    if 'freeze_modules' in value:
        modules = value['freeze_modules']
        if (not isinstance(modules, list) or any(type(name) is not str or name not in FREEZABLE_MODULES for name in modules)
                or len(set(modules)) != len(modules)):
            raise ValueError('Camera freeze_modules must list distinct supported camera modules')
        cfg['freeze_modules'] = sorted(modules)
    if 'g3t_prior' in value:
        prior = normalize_g3t_prior(value['g3t_prior'])
        if prior is None:
            cfg.pop('g3t_prior', None)
        else:
            cfg['g3t_prior'] = prior
    if cfg.get('fov_activation') and g3t_prior_enabled(cfg):
        raise ValueError('Bounded FoV activation requires a fresh head without a G3T pose prior')
    if cfg.get('pose_input') and (cfg.get('pose_reference') != 'first_group_concat_v1'
                                 or cfg.get('fov_activation') != 'bounded_sigmoid_v1'
                                 or cfg.get('feature_layers') is not None or g3t_prior_enabled(cfg)):
        raise ValueError('Spatial pose requires the fixed origin/FoV settings and ViT features without a G3T prior')
    for key in ('weight', 'weight_trans', 'weight_rot', 'weight_focal', 'weight_gravity', 'weight_scale',
                'min_trajectory_scale_m', 'stage_gamma', 'loss_clamp', 'warmup_ratio'):
        if not finite(cfg[key]) or cfg[key] < 0:
            raise ValueError('Invalid camera setting: ' + key)
    if cfg['frame_addressing'] != 'group16':
        # Per-frame (pair32) addressing would need targets and depth for both frames of a pair; neither is supervised.
        raise ValueError('Only group16 frame addressing is supervised; got ' + str(cfg['frame_addressing']))
    from .point_depth_head import normalize_point_depth, point_depth_enabled
    cfg['point_depth'] = normalize_point_depth(cfg['point_depth'])
    if cfg['min_trajectory_scale_m'] <= 0 or not 0 < cfg['stage_gamma'] <= 1 or cfg['loss_clamp'] <= 0 or cfg['warmup_ratio'] > 1:
        raise ValueError('Invalid camera trajectory floor, stage weighting, clamp or warmup')
    for key, low, high in (('embed_dim', 16, 8192), ('trunk_depth', 1, 12), ('num_heads', 1, 64), ('refine_iterations', 1, 8),
                           ('head_only_steps', 0, 100000)):
        if type(cfg[key]) is not int or not low <= cfg[key] <= high:
            raise ValueError('Invalid camera setting: ' + key)
    if cfg['embed_dim'] % cfg['num_heads']:
        raise ValueError('Camera head width must divide by its head count')
    layers = cfg['feature_layers']
    if layers is not None and (not isinstance(layers, list) or not 1 <= len(layers) <= 16
                               or any(type(k) is not int or not 1 <= k <= 128 for k in layers)
                               or layers != sorted(set(layers))):
        raise ValueError('Camera feature layers must be None (final norm) or 1-16 increasing distinct layer indices')
    if type(cfg['trajectory_balance']) is not bool or cfg['component_reduction'] not in ('mean', 'sum'):
        raise ValueError('Invalid camera trajectory balance or component reduction')
    for key in FIXED:
        if cfg[key] != DEFAULTS[key]:
            raise ValueError('Unsupported camera contract: ' + key)
    if point_depth_enabled(cfg['point_depth']) and not cfg['weight'] > 0:
        # The depth head is conditioned on the pose head's predicted field of view.
        raise ValueError('The point-depth head requires the pose head (camera weight > 0)')
    if g3t_prior_enabled(cfg) and not cfg['weight'] > 0:
        raise ValueError('The G3T camera prior requires the pose head (camera weight > 0)')
    from .camera_gate import normalize_gate, normalize_lm_gate
    cfg['gate'] = normalize_gate(cfg['gate'])
    cfg['lm_gate'] = normalize_lm_gate(cfg['lm_gate'])
    if enabled(cfg):
        pin = cfg['supervision']
        if not isinstance(pin, dict) or set(pin) != {'path', 'sha256'} or not isinstance(pin['path'], str) or not pin['path']:
            raise ValueError('Camera supervision requires a pinned sidecar')
        if not isinstance(pin['sha256'], str) or len(pin['sha256']) != 64 or any(c not in '0123456789abcdef' for c in pin['sha256']):
            raise ValueError('Invalid camera sidecar SHA256')
    return cfg


def enabled(cfg):
    if not cfg:
        return False
    from .point_depth_head import point_depth_enabled
    return bool(cfg.get('weight', 0) > 0 or point_depth_enabled(cfg.get('point_depth')))


def from_training_config(value):
    """The normalized, enabled camera object of a raw training config, or None.

    A config without a camera block, or with a disabled one (arm U's {"weight": 0}), has no camera
    supervision; both give None, as the protocol does, so the launcher, the protocol and train() agree."""
    if not isinstance(value, dict):
        raise ValueError('Training config contains unknown settings or is not an object')
    if 'camera' not in value:
        return None
    camera = normalize(value['camera'])
    return camera if enabled(camera) else None


def ramp(step, total_steps, cfg):
    if total_steps < 1 or not 0 <= step < total_steps:
        raise ValueError('Camera step is outside the training plan')
    warmup = math.ceil(total_steps * cfg['warmup_ratio'])
    return min(1.0, (step + 1) / max(1, warmup))


def backbone_gradient_scale(step, cfg):
    """Scale on the head losses' gradient into the student at this optimizer step (head-only warmup)."""
    hold = cfg['head_only_steps']
    if step < 0:
        raise ValueError('Camera step is negative')
    if hold == 0 or step >= 2 * hold:
        return 1.0
    return 0.0 if step < hold else (step - hold + 1) / (hold + 1)
