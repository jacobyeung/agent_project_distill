"""Bind an authenticated donor export to its native prepared vocabulary."""
from pathlib import Path
import argparse
from student_pilot.p3_provenance import load, pinned, write, file_pin
from student_pilot.r2_contract import bound_init


def prepared_vocabulary(source):
    from student_pilot.carrier_c1_run import processor_for_receipt
    from student_pilot.r2_openers import vocabulary
    receipt = load(pinned(source['preparation']))
    manifest = load(pinned(receipt['model']))
    files = manifest['files']
    required = {'config.json', 'tokenizer.json', 'tokenizer_config.json'}
    if not required <= files.keys():
        raise ValueError('P_EXPORT_TOKENIZER_FILES_REQUIRED')
    root = pinned(dict(path=str(Path(manifest['root'])/'config.json'),
                       sha256=files['config.json'])).parent
    # Only tokenizer/processor metadata are read; no model tensors are loaded.
    metadata = {p.name for p in root.iterdir() if p.is_file()
                and p.suffix in ('.json', '.txt', '.model', '.jinja')}
    for name in sorted(metadata | required):
        if name not in files:
            raise ValueError('P_EXPORT_TOKENIZER_FILE_UNBOUND:'+name)
        pinned(dict(path=str(root/name), sha256=files[name]))
    processor = processor_for_receipt(dict(manifest,root=str(root)), receipt)
    return vocabulary(processor)


def produce(cfg, output):
    from student_pilot.r1_training import PARENT
    from student_pilot.r1_handover import donor, compare_configs
    if not cfg.get('r1_training') or cfg.get('routing_opener_init') != 'keep':
        raise ValueError('P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED:routing_opener_init')
    spec = cfg.get('init_artifact') or {}
    if spec.get('lm') != 'full':
        raise ValueError('Keep requires a full warm start')
    artifact_pin = spec['artifact']
    if artifact_pin['sha256'] == PARENT:
        raise ValueError('P_EXPORT_WITNESS_REQUIRES_DONOR_EXPORT')
    artifact = load(pinned(artifact_pin))
    source, _, _, _ = donor(cfg, artifact)  # Authenticate P's complete published closure.
    compare_configs(source, cfg)
    lineage = bound_init(cfg)
    if (lineage['artifact_sha256'] != PARENT or lineage['step'] != 544
            or source.get('init_artifact', {}).get('artifact', {}).get('sha256') != PARENT):
        raise ValueError('P_EXPORT_OPENER_LINEAGE_MISMATCH')
    pinned(source['init_artifact']['artifact'])
    recorded = prepared_vocabulary(source)
    if artifact.get('routing_vocabulary') is not None and artifact['routing_vocabulary'] != recorded:
        raise ValueError('P_EXPORT_OPENER_VOCABULARY_MISMATCH')
    witness = dict(artifact_sha256=artifact_pin['sha256'],
                   lineage_sha256=PARENT, **recorded)
    write(Path(output), witness)
    # N binds this pin before producing its target identity and handover mapping.
    return file_pin(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    return produce(load(args.config), args.output)


if __name__ == '__main__':
    main()
