import copy
import hashlib
import json
from pathlib import Path
import re


SCHEMA = 's1-warm-export-choice-v1'
UNSEALED = {'path': '/UNSEALED_AUTHORIZATION_REQUIRED/source.json', 'sha256': '0' * 64}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_pin(pin):
    if (not isinstance(pin, dict) or set(pin) != {'path', 'sha256'}
            or not isinstance(pin['path'], str) or not Path(pin['path']).is_absolute()
            or '..' in Path(pin['path']).parts
            or not isinstance(pin['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', pin['sha256'])
            or pin['sha256'] == '0' * 64):
        raise ValueError('The export choice requires absolute non-placeholder SHA256 pins')


def instantiate(base, choice):
    if (not isinstance(choice, dict) or not {'schema', 'run', 'artifact', 'donor_config'} <= set(choice)
            or set(choice) - {'schema', 'run', 'artifact', 'donor_config', 'donor_row_order'}
            or choice['schema'] != SCHEMA or choice['run'] != '469ddece'):
        raise ValueError('Select one pinned export and its effective donor configuration from run 469ddece')
    validate_pin(choice['artifact'])
    validate_pin(choice['donor_config'])
    if 'donor_row_order' in choice:
        validate_pin(choice['donor_row_order'])
    if Path(base['output']).name != '469ddece' or base['recipe']['steps'] != 1000:
        raise ValueError('The fixed base must be the 1000-step run-469ddece template')
    key = digest(dict(policy='s1-warm-start-private-v1', choice=choice))[:8]
    persistent_key = digest(dict(run=key, purpose='persistent'))[:8]
    if key == '469ddece' or persistent_key == '5da50f2b':
        raise ValueError('Warm run/root identity collides with the donor')
    cfg = copy.deepcopy(base)
    for name in ('preparation', 'admission', 'authorization'):
        cfg.pop(name, None)
    cfg.update(output=str(Path(base['output']).parent / key),
               preparation_output=str(Path(base['preparation_output']).parent / key),
               code=copy.deepcopy(UNSEALED),
               init_artifact=dict(artifact=choice['artifact'], lm='full',
                                  heads=['pose', 'depth', 'frame_embeddings']),
               warm_start=dict(schema='s1-export-warm-start-v1', donor_config=choice['donor_config']))
    if 'donor_row_order' in choice:
        cfg['warm_start']['donor_row_order'] = choice['donor_row_order']
    return dict(schema='s1-unsealed-warm-start-template-v1', status='BLOCKED_UNSEALED',
                production_authorized=False, config=cfg, export_identity=copy.deepcopy(choice),
                run_key=key, persistent_run_root='/home/jjyeung/okit/r/' + persistent_key,
                admission=dict(policy='unchanged-four-stream-full-population',
                               directory=str(Path(cfg['output']) / 'inputs'),
                               parent_grounding_required=True, gpu_first_step_required=True),
                pending_gates=['named-export-metadata-and-payload-verification',
                               'donor-effective-config-preparation-and-parent-metadata-binding',
                               'same-ordered-admitted-row-pins', 'independent-source-review',
                               'authorized-reseal', 'native-binding-check', 'content-scan', 'operator-gate'])


def template(base_pin):
    return dict(schema='s1-unsealed-warm-start-template-v1', status='BLOCKED_UNSEALED',
                production_authorized=False, fixed_base=base_pin, open_parameter='export_identity',
                export_identity=None,
                export_identity_schema=dict(schema=SCHEMA, run='469ddece',
                    artifact={'path': 'SELECTED_EXPORT_ARTIFACT_JSON', 'sha256': 'PIN_REQUIRED'},
                    donor_config={'path': 'MIRRORED_EFFECTIVE_DONOR_CONFIG_JSON', 'sha256': 'PIN_REQUIRED'}),
                instantiate='config_template.instantiate(fixed_base, export_identity)',
                 required_metadata=['artifact.json', 'effective donor config.json',
                                    'donor preparation receipt', 'all four donor stream receipt JSONs',
                                    'original donor-init artifact metadata'],
                runtime_payloads=['heads.pt', 'full_weights/full_weights.json',
                                  'full_weights/model.safetensors.index.json', 'all indexed weight shards'],
                safety='No fetch, copy, seal, authorization, admission bypass, or launch is implemented.')
