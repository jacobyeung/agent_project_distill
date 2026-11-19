"""Retained tiny-native first batch; never substitutes for real-row admission."""
import argparse
import copy
import json
from pathlib import Path
import sys
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
import torch
from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import full_ft
from tests.test_stageb_mdg import fixture
from tests.test_mdg_features import small_layers
from tests.test_carrier_c1_final import final_fixture


def fixture_rows(config, bf16=True):
    torch.set_num_threads(1)
    model, mdg_batch, mdg_target = fixture(lora_rank=config['mdg']['lora_rank'])
    from tests.test_e2e_ground_tokens import processor as tokenizer_fixture
    from student_pilot import ground_tokens
    from student_pilot.carrier_c1_routing import add_routing_tokens
    processor = tokenizer_fixture()
    add_routing_tokens(processor)
    ground_tokens.add(processor)
    ground_tokens.initialize(model, processor)
    model.mdg_tokenizer = processor.tokenizer
    ground_tokens.install_rows(model)
    # Tiny native channels retain the production adapter rank.
    # Both native vision copies must consume the same 16-pixel RGB patch fixture.
    model.auxiliary_heads.depth.model.visual = copy.deepcopy(model.model.visual).requires_grad_(True)
    model.auxiliary_heads.depth.model.visual.merger.requires_grad_(False)
    model.auxiliary_heads.depth.config.vision_config.patch_size = 16
    _, _, pose_target = final_fixture()
    if bf16:
        for _, parameter in full_ft.base_parameters(model):
            parameter.data = parameter.data.bfloat16()
    batch = {k: v for k, v in mdg_batch.items() if k != 'aux_mdg_labels'}
    batch['labels'] = torch.full_like(batch['input_ids'], -100)
    batch['labels'][0, -2:] = batch['input_ids'][0, -2:]
    batch['aux_suffix_start'] = torch.tensor([batch['input_ids'].shape[1] - 2])
    model.recipe = config['recipe']
    class Rows:
        def __init__(self, *args): pass
        def count(self, stream): return 1000
        def get(self, stream, index):
            if stream == 'mdg':
                return mdg_batch, mdg_target, dict(qid='fixture-mdg-'+str(index))
            return batch, pose_target if stream == 'pose' else None, dict(qid='fixture-'+stream+'-'+str(index))
        def close(self): pass
    return model, Rows()


def check(config, output):
    model, rows = fixture_rows(config)
    receipt = dict(streams={s: dict(count=1000) for s in config['streams']})
    supplied = {**config, 'preparation': {'fixture': True}}
    with small_layers(), mock.patch.object(run, 'prepared', return_value=(receipt, {})), \
            mock.patch.object(run, 'processor_for_receipt', return_value=None), \
            mock.patch.object(run, 'load_model', return_value=model), mock.patch.object(run, 'Rows', return_value=rows):
        records = run.first_batch_check(supplied, [0, 1, 2, 3], output)
    report = json.loads(Path(output).read_text())
    report.update(input_kind='PENDING-INPUT: tiny native fixture rows; no real data or 9B weights',
                  frames=32, atomic_openers=model.ground_token_ids, fixture_lora_rank=config['mdg']['lora_rank'], production_lora_rank=config['mdg']['lora_rank'],
                  largest_row=max(records, key=lambda r: r.get('effective_tokens', r.get('tokens', 0))),
                  over_10k=[r for r in records if r.get('over_10k_tokens', False)],
                  finite=sum(r['finite'] for r in records),
                  stream_summary={s: dict(rows=sum(r['stream']==s for r in records),
                      finite=sum(r['stream']==s and r['finite'] for r in records),
                      tokens=sorted(set(r.get('tokens') for r in records if r['stream']==s)))
                      for s in config['streams']})
    Path(output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('finite','stream_summary','largest_row','over_10k')}, indent=2))
    return all(r['finite'] for r in records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config'); parser.add_argument('output')
    args = parser.parse_args()
    sys.exit(0 if check(json.loads(Path(args.config).read_text()), args.output) else 1)
