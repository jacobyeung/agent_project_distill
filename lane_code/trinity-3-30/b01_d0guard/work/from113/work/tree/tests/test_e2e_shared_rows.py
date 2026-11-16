"""Shared opener rows and closed main-stream adapters under ORCH 0718Z."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import torch
from torch import nn

from student_pilot import ground_tokens as G, mdg_lora
from tests.test_stageb_mdg import fixture
from tests.test_mdg_features import small_layers


class SharedRows(unittest.TestCase):
    def test_main_and_query_share_rows_and_only_two_embedding_rows_change(self):
        model, _, _ = fixture(frames=2, lora_rank=4)
        G.install_rows(model)
        ids = [model.ground_token_ids[text] for text in G.OPENERS]
        row = model.auxiliary_heads.mdg_lora['opener_rows']
        with torch.no_grad():
            row.input_rows.add_(.2); row.output_rows.add_(.3)
        tokens = torch.arange(model.get_input_embeddings().weight.shape[0])[None]
        main = model.get_input_embeddings()(tokens)
        with mdg_lora.suffix_mask(model, torch.ones_like(tokens, dtype=torch.bool)):
            query = model.get_input_embeddings()(tokens)
        self.assertTrue(torch.equal(main, query))
        changed = (main[0] != model.get_input_embeddings().weight).any(-1).nonzero().flatten().tolist()
        self.assertEqual(changed, ids)
        hidden = torch.randn(1, 3, main.shape[-1])
        out = model.get_output_embeddings()(hidden)
        with mdg_lora.suffix_mask(model, torch.ones(1, 3, dtype=torch.bool)):
            self.assertTrue(torch.equal(out, model.get_output_embeddings()(hidden)))
        exported = G.materialize_export_rows(model.state_dict(), model)
        for key, value in (('model.language_model.embed_tokens.weight', row.input_rows),
                           ('lm_head.weight', row.output_rows)):
            self.assertTrue(torch.equal(exported[key][ids], value))
            keep = torch.ones(exported[key].shape[0], dtype=torch.bool); keep[ids] = False
            self.assertTrue(torch.equal(exported[key][keep], model.state_dict()[key][keep]))

    def test_warm_full_export_retains_learned_rows(self):
        from tests.test_e2e_ground_tokens import processor
        from student_pilot.carrier_c1_routing import add_routing_tokens
        model, _, _ = fixture(frames=2, lora_rank=4)
        proc = processor(); add_routing_tokens(proc, include_ground=True); G.add(proc)
        G.initialize(model, proc)
        ids = [model.ground_token_ids[text] for text in G.OPENERS]
        with torch.no_grad():
            model.get_input_embeddings().weight[ids] += .4
            model.get_output_embeddings().weight[ids] += .5
        before = copy.deepcopy(model.state_dict())
        G.initialize_after_warm(model, proc, dict(ground_token_ids=proc._ground_tokens['ids']))
        for key in ('model.language_model.embed_tokens.weight', 'lm_head.weight'):
            self.assertTrue(torch.equal(model.state_dict()[key][ids], before[key][ids]))

    def test_frozen_lm_routing_ce_trains_both_shared_input_and_output_rows(self):
        from student_pilot import full_ft
        model, batch, _ = fixture(frames=2, lora_rank=4)
        model.eval(); G.install_rows(model)
        for _, parameter in full_ft.base_parameters(model):
            parameter.requires_grad_(False)
        ids = [model.ground_token_ids[text] for text in G.OPENERS]
        plain = model.mdg_tokenizer.encode('x', add_special_tokens=False)[0]
        suffix = [ids[0], plain, ids[1], plain, ids[0], plain]
        batch['input_ids'] = torch.cat((batch['input_ids'], torch.tensor([suffix])), 1)
        batch['attention_mask'] = torch.ones_like(batch['input_ids'])
        if 'mm_token_type_ids' in batch:
            batch['mm_token_type_ids'] = torch.cat((batch['mm_token_type_ids'], torch.zeros(1, len(suffix), dtype=batch['mm_token_type_ids'].dtype)), 1)
        batch['labels']=batch['input_ids'].clone()
        batch['labels'][:, :-len(suffix)]=-100
        model.recipe={**model.recipe,'weights':{**model.recipe['weights'],'routing':1.}}
        with small_layers():
            model(batch,stream='routing')['loss'].backward()
        rows = model.auxiliary_heads.mdg_lora['opener_rows']
        self.assertTrue((rows.input_rows.grad.norm(dim=1)>0).all())
        self.assertTrue((rows.output_rows.grad.norm(dim=1)>0).all())
        self.assertTrue(all(p.grad is None for _,p in full_ft.base_parameters(model)))
        self.assertIsNone(mdg_lora.active_mask())

    def test_export_artifact_warm_start_preserves_the_shared_rows(self):
        import os, tempfile
        from unittest import mock
        from student_pilot import carrier_c1_run as run
        from student_pilot.p3_provenance import write, file_pin
        from tests.test_stageb_mdg import block
        from tests.test_carrier_c1_run import RunnerTests
        from tests.test_e2e_ground_tokens import processor
        from student_pilot.carrier_c1_routing import add_routing_tokens
        model, _, _ = fixture(frames=2, lora_rank=4)
        G.install_rows(model)
        rows=model.auxiliary_heads.mdg_lora['opener_rows']
        with torch.no_grad():
            rows.input_rows.add_(.4); rows.output_rows.add_(.5)
        root=Path(tempfile.mkdtemp(prefix='shared-warm-',dir=os.environ['LANE_TEST_OUTPUT']))
        write(root/'code.json',dict(commit='1'*40))
        cfg=dict(base_identity='fixture',mdg=dict(block(),lora_rank=4),code=file_pin(root/'code.json'))
        with RunnerTests().local_collectives(), mock.patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
            run.export(root/'milestone',model,model,cfg,1)
        fresh,_,_=fixture(frames=2,lora_rank=0)
        # The production loader warms the LM/pose/depth before attaching MDG.
        delattr(fresh.auxiliary_heads,'mdg')
        spec=dict(artifact=file_pin(root/'milestone/artifact.json'),lm='full',heads=[])
        report=run.init_from_artifact(fresh,spec,part='lm')
        self.assertEqual(report['ground_token_ids'],model.ground_token_ids)
        proc=processor();add_routing_tokens(proc,include_ground=True);G.add(proc)
        G.initialize_after_warm(fresh,proc,report)
        run.init_from_artifact(fresh,spec,part='heads')
        mdg_lora.install(fresh,4);G.install_rows(fresh)
        ids=[model.ground_token_ids[text] for text in G.OPENERS]
        self.assertTrue(torch.equal(fresh.auxiliary_heads.mdg_lora['opener_rows'].input_rows,rows.input_rows))
        self.assertTrue(torch.equal(fresh.auxiliary_heads.mdg_lora['opener_rows'].output_rows,rows.output_rows))
        self.assertTrue(torch.equal(fresh.get_input_embeddings()(torch.tensor([ids]))[0],rows.input_rows))

    def test_main_full_routing_suffix_logits_equal_without_adapters(self):
        from student_pilot import mdg_features
        model, batch, _ = fixture(frames=2, lora_rank=0)
        model.eval()
        reference = copy.deepcopy(model)
        # The reference owns the same new rows, with no low-rank adapters.
        ids = [reference.ground_token_ids[text] for text in G.OPENERS]
        rows = nn.Module()
        rows.input_rows = nn.Parameter(reference.get_input_embeddings().weight[ids].clone())
        rows.output_rows = nn.Parameter(reference.get_output_embeddings().weight[ids].clone())
        reference.auxiliary_heads.shared_rows = rows
        G.bind_rows(reference, rows)
        mdg_lora.install(model, 4); G.install_rows(model)
        with torch.no_grad():
            for name, p in model.auxiliary_heads.mdg_lora.named_parameters():
                if not name.startswith('opener_rows.'):
                    p.normal_(0, .2)
        source = Path(__file__).resolve().parents[2]/'inputs/ground_rows_pilot_v3121.jsonl'
        if not source.is_file():
            self.skipTest('PENDING-INPUT: '+str(source))
        row = next(row for row in map(json.loads, source.read_text().splitlines())
                   if sum(e['call'].startswith('<ground') for e in row['events']) >= 2)
        suffix = model.mdg_tokenizer.encode(row['suffix'], add_special_tokens=False)
        batch = {k:v for k,v in batch.items() if k != 'aux_mdg_labels'}
        batch['input_ids'] = torch.cat((batch['input_ids'], torch.tensor([suffix])), 1)
        batch['attention_mask'] = torch.ones_like(batch['input_ids'])
        if 'mm_token_type_ids' in batch:
            batch['mm_token_type_ids'] = torch.cat((batch['mm_token_type_ids'], torch.zeros(1, len(suffix), dtype=batch['mm_token_type_ids'].dtype)), 1)
        with small_layers(), torch.no_grad():
            a = mdg_features._native(reference)(**{k:v for k,v in batch.items() if k in (
                'input_ids','attention_mask','pixel_values_videos','video_grid_thw','mm_token_type_ids')}, logits_to_keep=0).logits
            b = mdg_features._native(model)(**{k:v for k,v in batch.items() if k in (
                'input_ids','attention_mask','pixel_values_videos','video_grid_thw','mm_token_type_ids')}, logits_to_keep=0).logits
        self.assertTrue(torch.equal(a, b))
        self.assertIsNone(mdg_lora.active_mask())
