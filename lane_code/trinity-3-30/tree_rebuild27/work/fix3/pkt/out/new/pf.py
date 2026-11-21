"""Open, before the long steps, the two processor folders mode q reads.

The opener witness takes the folder of the model manifest's config.json pin; the forward takes the
root each model manifest names. Both must hold the processor files under their manifest names."""
from pathlib import Path


def check(cfg, manifest_pin):
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
