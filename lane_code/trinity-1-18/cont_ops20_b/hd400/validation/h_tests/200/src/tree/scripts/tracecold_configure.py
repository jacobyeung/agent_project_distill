import argparse
import importlib
from pathlib import Path
import sys
import types

from student_pilot.common import digest_json
from student_pilot.ddp_config import normalize_training_config
from student_pilot.trace_contract import ANSWER_FORMAT_INSTRUCTION
from student_pilot.trace_io import canonical, load, pin, require, rows, save, verify
from student_pilot.trace_targets import lint_row


EVALUATOR = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/trinityeval_20261006/work/evaluator/student_pilot')


def native_config():
    package = types.ModuleType('tracecold_native_training_metadata')
    package.__path__ = [str(EVALUATOR)]
    sys.modules[package.__name__] = package
    return importlib.import_module(package.__name__ + '.ddp_config')


def configure(source, destination):
    require(not destination.exists(), 'Preserve the existing configuration epoch')
    ready_pin = pin(source)
    ready = load(source)
    native = native_config()
    configs = {}
    for seed in ('17', '18'):
        raw = load(verify(ready['configs'][seed]['file']))
        require(raw['answer_format_instruction'] == ANSWER_FORMAT_INSTRUCTION and 'init_adapter' not in raw,
                'The prompt or cold-start configuration differs')
        settings = normalize_training_config(raw, 'qwen35')
        require(native.normalize_training_config(settings, 'qwen35') == settings,
                'The native evaluator cannot read the unchanged optimizer metadata')
        path = save(destination / ('config_s' + seed + '.json'), raw)
        configs[seed] = {'file': path, 'normalized_training_sha256': digest_json(settings),
                         'prompt_sha256': digest_json({'answer_format_instruction': ANSWER_FORMAT_INSTRUCTION}),
                         'full_configuration_sha256': digest_json(raw), 'native_metadata_compatible': True}
    count = 0
    for arm in ('TR', 'AO'):
        for role in ('training', 'heldout_support_not_trained'):
            values = list(rows(verify(ready['arms'][arm][role])))
            expected = ready['training_order'] if role == 'training' else ready['heldout_order']
            require([row['qid'] for row in values] == expected, 'The immutable source order changed')
            for row in values:
                lint_row(row, arm)
                count += 1
    result = {**ready, 'configs': configs, 'row_source': ready_pin, 'prompt_configuration': {
        'answer_format_instruction': ANSWER_FORMAT_INSTRUCTION,
        'binding': 'The raw configuration file and full protocol hash bind this instruction; optimizer metadata remains native-compatible.'},
        'fresh_rows_linted': count, 'configuration_builder': pin(__file__), 'native_metadata_reader': pin(native.__file__)}
    require(ready_pin == pin(source), 'The prototype row authority changed')
    return save(destination / 'ROWS_READY.json', result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows-ready', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(canonical({'output': configure(args.rows_ready, args.output)}), flush=True)


if __name__ == '__main__':
    main()
