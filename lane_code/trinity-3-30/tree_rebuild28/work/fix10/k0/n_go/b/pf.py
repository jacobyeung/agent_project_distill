"""Open, before the long steps, the two processor folders mode q reads.

The opener witness takes the folder of the model manifest's config.json pin; the forward takes the
root each model manifest names. Both must hold the processor files under their manifest names.

First, run the tree's own receipt predicates on the configured stream receipts, so that a receipt
the preparation would refuse is refused here, by name, before the long steps."""
from pathlib import Path


def receipts(cfg):
    """carrier_c1_run.prepare lines 536-541 on every non-pose stream receipt, against the run
    division (the pose mix division, or the pose preparation's inputs.division), and
    s1_routing._build line 229 (the routing receipt against the pointing receipt's division).
    Lines 543-547 read the pointing receipt that preparation rebuilds, not the configured one."""
    from student_pilot.p3_provenance import load, pinned
    from student_pilot.carrier_c1_run import division_admits
    from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
    streams = cfg['streams']
    pose = load(pinned(streams['pose']))
    division = pose.get('division') if pose.get('schema') == 'c1-pose-mix-v1' else pose['inputs']['division']
    if division is None:
        raise ValueError('R1_STREAM_RECEIPT_REFUSED:pose(division_unknown)')
    failed = []
    for name, pin in streams.items():
        if name in ('pose', 'mdg'):
            continue
        receipt = load(pinned(pin))
        schema = ROUTING_SCHEMA if name == 'routing' else 'c1-stream-v1'
        parts = dict(schema=receipt.get('schema') != schema, stream=receipt.get('stream') != name,
                     division=not division_admits(receipt['division'], division),
                     heldout_overlap=receipt.get('heldout_overlap') != 0,
                     gt_masks_only=name == 'pointing' and receipt.get('gt_masks_only') is not True)
        bad = [k for k, v in parts.items() if v]
        if bad:
            failed.append(name + '(' + ','.join(bad) + ')')
    if 'routing' in streams and 'pointing' in streams:
        legacy = load(pinned(streams['routing']))
        if not division_admits(legacy['division'], load(pinned(streams['pointing']))['division']):
            failed.append('routing(s1_routing_division)')
    if failed:
        raise ValueError('R1_STREAM_RECEIPT_REFUSED:' + ';'.join(failed))


def check(cfg, manifest_pin):
    receipts(cfg)
    from student_pilot.p3_provenance import load, pinned, sha256
    from student_pilot.decoupled_v_run import processor_for
    from student_pilot.mdg_parent import model_pin
    from launch_r1.p_opener_witness import prepared_vocabulary
    try:
        prepared_vocabulary(load(pinned(cfg['r1_training']['p_run']['config'])))
        pins = {pin['sha256']: pin for pin in (manifest_pin, model_pin(cfg))}
        for pin in pins.values():
            manifest = load(pinned(pin))
            root = Path(manifest['root'])
            for name, expected in manifest['files'].items():
                small = name.endswith(('.json', '.txt', '.jinja', '.model'))
                if Path(name).name != name or not (root/name).is_file() or small and sha256(root/name) != expected:
                    raise ValueError('file missing or changed: ' + name)
            processor_for(str(root))
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, ImportError) as error:
        raise ValueError('R1_PROCESSOR_FOLDER_UNUSABLE:' + type(error).__name__ + ':' + str(error)) from error
