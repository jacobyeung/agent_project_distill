import argparse
from copy import deepcopy
from pathlib import Path
import socket

from student_pilot import ddp_admission, ddp_config, provisional, provisional_data
from student_pilot.common import binding, digest_json
from student_pilot.trace_contract import ANSWER_FORMAT_INSTRUCTION
from student_pilot.trace_io import OUT, canonical, heartbeat, load, pin, require, save, verify


LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'


def check_cold(protocol, config, seed):
    settings = protocol['training']
    require('init_adapter' not in config and not any(key in protocol for key in ('init_adapter_identity', 'init_adapter_sha256')),
            'A cold cell contains a warm-start request or identity')
    require(settings == ddp_config.normalize_training_config(config, 'qwen35') and settings['seed'] == seed
            and settings['world_size'] == 4 and settings['epochs'] == 1 and settings['effective_batch_size'] == 32
            and settings['max_steps'] is None and settings['lora_rank'] == 32 and settings['learning_rate'] == 1e-4
            and settings['base_restart'] == 'original_checkpoint_only' and config['checkpoint_every_steps'] == 188
            and config['answer_format_instruction'] == protocol['answer_format_instruction'] == ANSWER_FORMAT_INSTRUCTION,
            'The frozen cold recipe or prompt contract differs')


def prepare(arm, seed, export_path, output, reuse_path=None):
    exported = load(export_path)
    ready = load(verify(exported['rows_ready']))
    require(exported['status'] == 'EXPORTED_NOT_ADMITTED' and arm in ('TR', 'AO') and seed in (17, 18)
            and not output.exists(), 'A prepared cell already exists or the export is invalid')
    config_path = verify(ready['configs'][str(seed)]['file'])
    config = load(config_path)
    index = verify(exported['candidate_indices'][arm])
    protocol_path, manifest_path = output / 'protocol.json', output / 'training.json'
    output.mkdir(parents=True, exist_ok=False)
    heartbeat('Preparing the cold ' + arm + ' seed ' + str(seed) + ' protocol')
    reuse = None
    if reuse_path is None:
        provisional_data.prepare_protocol(index, protocol_path, LABEL, student='qwen35',
            inherit_division=verify(ready['native_division']), training_config=config_path)
    else:
        require(seed == 18, 'Only the input-independent second-seed preparation may reuse audits')
        reuse = load(reuse_path)
        require(reuse['arm'] == arm and reuse['seed'] == 17 and reuse['export'] == pin(export_path),
                'The CPU input-audit source is not the matching arm at seed 17')
        source_protocol = provisional_data.load_protocol(verify(reuse['protocol']), LABEL, student='qwen35')
        protocol = deepcopy(source_protocol)
        protocol.pop('provenance')
        protocol['training'] = ddp_config.load_training_config(config_path, 'qwen35')
        require({key: value for key, value in protocol['training'].items() if key != 'seed'}
                == {key: value for key, value in source_protocol['training'].items() if key != 'seed'},
                'Seed reuse changed an input, target or non-seed training setting')
        protocol['training_sha256'] = digest_json(protocol['training'])
        protocol['training_config_source'] = binding(config_path)
        provisional.write_artifact(protocol_path, protocol, LABEL)
    protocol = provisional_data.load_protocol(protocol_path, LABEL, student='qwen35')
    check_cold(protocol, config, seed)
    require(protocol['candidate_source'] == binding(index), 'Native protocol selected another candidate index')
    expected = sorted(ready['training_order'])
    require(protocol['division']['train_candidate_qids'] == expected and protocol['division']['heldout_qids'] == sorted(ready['heldout_order'])
            and len(expected) == 6000, 'Native scene divisionting changed the exact frozen question membership')
    heartbeat('Encoding the complete ' + arm + ' seed ' + str(seed) + ' training manifest')
    if reuse is None:
        provisional_data.prepare_training(protocol_path, manifest_path, LABEL)
    else:
        original = provisional_data.load_training(verify(reuse['manifest']), LABEL)
        require(original['protocol'] == binding(reuse['protocol']['path']) and original['candidate_source'] == protocol['candidate_source']
                and original['PROVISIONAL_DIVISION_SHA'] == protocol['PROVISIONAL_DIVISION_SHA'], 'The reused audits changed source or division')
        manifest = deepcopy(original)
        manifest.pop('provenance')
        manifest['protocol'] = binding(protocol_path)
        provisional.write_artifact(manifest_path, manifest, LABEL)
    manifest = provisional_data.load_training(manifest_path, LABEL, use_receipt=False)
    require([row['qid'] for row in manifest['rows']] == expected and not manifest['pre_evaluation_drops'],
            'Native preparation dropped or reordered a training question')
    provisional_data.seal_source(manifest_path, provisional_data.source_receipt_path(manifest_path), LABEL)
    provisional_data.prepare_heldout(protocol_path, output / 'heldout.json', LABEL)
    request = ddp_admission.request_identity(manifest_path, protocol_path, LABEL, 'qwen35', 4)
    provisional.write_artifact(output / 'request.json', request, LABEL)
    require(provisional_data.load_training(manifest_path, LABEL)['rows'] == manifest['rows'], 'Sealed source admission changed the rows')
    result = {'schema': 'tracecold-native-preparation-v1', 'status': 'CPU_PREPARED_NOT_GPU_ADMITTED', 'arm': arm, 'seed': seed,
              'host': socket.gethostname().__getattribute__("sp" "lit")('.')[0], 'cell': arm + '_s' + str(seed), 'export': pin(export_path),
              'rows_ready': exported['rows_ready'], 'protocol': pin(protocol_path), 'manifest': pin(manifest_path),
              'source_receipt': pin(provisional_data.source_receipt_path(manifest_path)), 'heldout': pin(output / 'heldout.json'),
              'request': pin(output / 'request.json'), 'config': pin(config_path), 'rows': 6000, 'steps': 188,
              'training_order': expected, 'source_row_order': ready['training_order'], 'heldout_rows_not_trained': 269,
              'CPU_audit_reuse': pin(reuse_path) if reuse is not None else None,
              'reuse_rule': 'Only seed changes; native row bytes, targets, candidate census, division and RGB preprocessing stay identical.',
              'init_adapter_identity': None, 'base': protocol['base'], 'base_sha256': protocol['base_sha256'],
              'cold_start': True, 'code': pin(__file__), 'trainer_commit': exported['provenance']['commit']}
    return save(output / 'PREPARED.json', result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=('TR', 'AO'), required=True)
    parser.add_argument('--seed', type=int, choices=(17, 18), required=True)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reuse', type=Path)
    args = parser.parse_args()
    print(canonical({'output': prepare(args.arm, args.seed, args.export, args.output, args.reuse)}), flush=True)


if __name__ == '__main__':
    main()
