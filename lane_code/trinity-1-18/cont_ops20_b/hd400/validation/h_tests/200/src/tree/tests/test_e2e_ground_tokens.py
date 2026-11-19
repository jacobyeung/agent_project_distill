"""Training/runtime token parity without changing the prefix vocabulary."""
import copy
from types import SimpleNamespace
import unittest
from unittest import mock

import torch

from student_pilot import carrier_c1_run as run, ground_tokens, mdg_features


def processor():
    from tokenizers import Tokenizer, models, pre_tokenizers, decoders
    from transformers import PreTrainedTokenizerFast
    chars = sorted(set('<ground obj="chairtablelong"><gap a="x" b="y"> ordinary prose after'))
    vocab = {'[UNK]': 0, '[PAD]': 1, **{c: i+2 for i,c in enumerate(chars)}}
    raw = Tokenizer(models.WordLevel(vocab, unk_token='[UNK]'))
    raw.pre_tokenizer = pre_tokenizers.Split('', behavior='isolated')
    raw.decoder = decoders.Fuse()
    return SimpleNamespace(tokenizer=PreTrainedTokenizerFast(tokenizer_object=raw, unk_token='[UNK]',pad_token='[PAD]'))



class GroundTokens(unittest.TestCase):
    def test_training_and_native_decode_gate_the_same_atomic_call_positions(self):
        from contextlib import contextmanager
        from student_pilot import mdg_lora, mdg_stream
        from tests.test_stageb_mdg import fixture
        from tests.test_mdg_features import small_layers
        model, batch, _ = fixture(frames=2, lora_rank=4)
        model.eval()
        names = ['chair', 'tablelong']
        masks = []
        original = mdg_lora.suffix_mask
        @contextmanager
        def recorded(owner, mask):
            masks.append(mask.detach().cpu().clone())
            with original(owner, mask):
                yield
        with small_layers(), mock.patch.object(mdg_lora, 'suffix_mask', recorded):
            prefix = mdg_features.capture_prefix(model, batch)
            self.assertEqual(masks, [])
            mdg_features.suffix_states(model, prefix, names, train_adapters=True)
            training = masks.pop()
            mdg_stream.stream_suffix_states(model, prefix, batch, names)
        lengths = [len(mdg_features.suffix_tokens(model.mdg_tokenizer, n)[0]) for n in names]
        self.assertEqual(len(masks), sum(lengths))
        offset = 0
        for row, length in zip(training, lengths):
            actual = torch.cat([m.flatten() for m in masks[offset:offset+length]])
            self.assertTrue(torch.equal(row[:length], actual))
            self.assertTrue(actual.all())  # opener through closing '>', inclusive
            self.assertFalse(row[length:].any())  # training padding stays closed
            offset += length
        # The streaming gate closes for ordinary prose immediately after the call.
        @contextmanager
        def capture(owner):
            yield SimpleNamespace(states=dict(layer=torch.zeros(1, 1, 32), norm=torch.zeros(1, 1, 32)))
        stream = mdg_stream.QueryStream(model, model.mdg_tokenizer)
        masks.clear()
        text = 'ordinary prose <ground obj="chair"> after'
        ids = model.mdg_tokenizer.encode(text, add_special_tokens=False)
        with mock.patch.object(mdg_lora, 'suffix_mask', recorded), mock.patch.object(mdg_features, '_SuffixCapture', capture):
            for index in ids:
                with stream.token(torch.tensor([[index]])):
                    pass
        call, _ = mdg_features.suffix_tokens(model.mdg_tokenizer, 'chair')
        begin = ids.index(model.ground_token_id)
        expected = [begin <= i < begin+len(call) for i in range(len(ids))]
        self.assertEqual([bool(m.item()) for m in masks], expected)

    def test_stageb_is_atomic_and_stagea_and_absent_paths_are_unchanged(self):
        manifest = dict(root='/fixture')
        def build(rank):
            receipt = dict(training_mode='final', frame_markers=True)
            if rank is not None:
                receipt['mdg'] = dict(lora_rank=rank)
            with mock.patch.object(run, 'processor_for', side_effect=lambda root: processor()):
                return run.processor_for_receipt(manifest, receipt)
        absent, a, b = build(None), build(0), build(32)
        self.assertNotIn(ground_tokens.OPENER, absent.tokenizer.get_vocab())
        self.assertEqual(a.tokenizer.get_vocab(), b.tokenizer.get_vocab())
        self.assertEqual(set(b.tokenizer.get_vocab()) - set(absent.tokenizer.get_vocab()), set(ground_tokens.OPENERS))
        index = b.tokenizer.convert_tokens_to_ids(ground_tokens.OPENER)
        ids, phrase = mdg_features.suffix_tokens(b.tokenizer, 'chair')
        self.assertEqual(ids[0], index)
        self.assertEqual(b.tokenizer.decode(ids[phrase]), 'chair')
        again = build(32)
        self.assertEqual(b.tokenizer.get_vocab(), again.tokenizer.get_vocab())
        self.assertEqual(b._ground_tokens, again._ground_tokens)
        self.assertEqual(ground_tokens.add(b), b._ground_tokens)

    def test_reserved_rows_initialize_once_and_export_weights_restore_exactly(self):
        from tests.test_stageb_mdg import fixture
        model, batch, _ = fixture(frames=2, lora_rank=4)
        proc = processor()
        from student_pilot.carrier_c1_routing import add_routing_tokens
        add_routing_tokens(proc)
        tokens = ground_tokens.add(proc)
        before = copy.deepcopy(model.state_dict())
        index = ground_tokens.initialize(model, proc)
        parts = tokens['constituents'][ground_tokens.OPENER]
        self.assertEqual(model.ground_token_id, index)
        self.assertTrue(torch.equal(model.get_input_embeddings().weight[index],
                                    before['model.language_model.embed_tokens.weight'][parts].mean(0)))
        keep = torch.ones(model.get_input_embeddings().weight.shape[0], dtype=torch.bool)
        keep[list(tokens['ids'].values())] = False
        self.assertTrue(torch.equal(model.get_input_embeddings().weight[keep],
                                    before['model.language_model.embed_tokens.weight'][keep]))
        trained = copy.deepcopy(model.state_dict())
        trained['model.language_model.embed_tokens.weight'][index].add_(1.)
        model.load_state_dict(trained)
        fresh, _, _ = fixture(frames=2, lora_rank=4)
        ground_tokens.initialize(fresh, proc)
        fresh.load_state_dict(trained)
        self.assertTrue(torch.equal(fresh.get_input_embeddings().weight,
                                    model.get_input_embeddings().weight))

    def test_two_opener_rows_train_with_a_frozen_lm_and_reload(self):
        import os, tempfile
        from pathlib import Path
        from student_pilot import mdg_lora, full_ft, stageb_mdg
        from tests.test_stageb_mdg import fixture
        from tests.test_mdg_features import small_layers
        model, batch, _ = fixture(frames=2, lora_rank=4)
        proc = processor()
        from student_pilot.carrier_c1_routing import add_routing_tokens
        add_routing_tokens(proc)
        ground_tokens.add(proc)
        ground_tokens.initialize(model, proc)
        model.mdg_tokenizer = proc.tokenizer
        ground_tokens.install_rows(model)
        for _, p in full_ft.base_parameters(model):
            p.requires_grad_(False)
        base = {n: p.detach().clone() for n, p in full_ft.base_parameters(model)}
        rows = model.auxiliary_heads.mdg_lora['opener_rows']
        original_rows = copy.deepcopy(rows.state_dict())
        optimizer = torch.optim.AdamW(model.auxiliary_heads.mdg_lora.parameters(), lr=1e-3, weight_decay=0.)
        with small_layers(), stageb_mdg.capture_mode(model):
            prefix = mdg_features.capture_prefix(model, batch)
            states = mdg_features.suffix_states(model, prefix, ['chair'], train_adapters=True)
            with torch.enable_grad():
                loss = states.query.square().mean() + states.phrase.square().mean()
                # Both new rows remain trainable when a call uses either opener.
                ids = torch.tensor([[model.ground_token_ids[text] for text in ground_tokens.OPENERS]])
                with mdg_lora.suffix_mask(model, torch.ones_like(ids, dtype=torch.bool)):
                    embedded = model.get_input_embeddings()(ids)
                    logits = model.get_output_embeddings()(embedded)
                    loss = loss + embedded.square().mean() + logits[..., ids[0]].square().mean()
                loss.backward()
                self.assertTrue((rows.input_rows.grad.norm(dim=1) > 0).all())
                self.assertTrue((rows.output_rows.grad.norm(dim=1) > 0).all())
                optimizer.step()
            self.assertTrue(torch.equal(prefix.hidden, mdg_features.capture_prefix(model, batch).hidden))
        self.assertTrue(all(torch.equal(p, base[n]) and p.grad is None for n, p in full_ft.base_parameters(model)))
        self.assertTrue(all(not torch.equal(v, original_rows[n]) for n, v in rows.state_dict().items()))
        directory = Path(tempfile.mkdtemp(prefix='e2e_opener_', dir=os.environ['LANE_TEST_OUTPUT']))
        meta = mdg_lora.export(directory, model, model.state_dict())
        fresh, _, _ = fixture(frames=2, lora_rank=4)
        ground_tokens.initialize(fresh, proc)
        fresh.mdg_tokenizer = proc.tokenizer
        mdg_lora.load(fresh, directory, meta)
        for name, value in rows.state_dict().items():
            self.assertTrue(torch.equal(value, fresh.auxiliary_heads.mdg_lora['opener_rows'].state_dict()[name]))

    def test_standalone_bundle_restores_the_two_learned_rows_without_training_inputs(self):
        import os, tempfile
        from pathlib import Path
        from student_pilot import mdg_runtime, mdg_eval, mdg_lora
        from student_pilot.mask_grounding_head import MaskGroundingHead
        from student_pilot.p3_provenance import write, file_pin
        from tests.test_mdg_runtime import Runtime, processor as native_processor
        from tests.test_mask_grounding_head import config as head_config
        from tests.test_stageb_mdg import block
        from tests.test_carrier_c1_run import RunnerTests
        Runtime.setUpClass()
        root = Path(tempfile.mkdtemp(prefix='e2e_bundle_', dir=os.environ['LANE_TEST_OUTPUT']))
        receipt = dict(Runtime.receipt, mdg=dict(block(), lora_rank=4))
        model = copy.deepcopy(Runtime.official)
        with mock.patch.object(run, 'processor_for', side_effect=native_processor):
            proc = run.processor_for_receipt(Runtime.manifest, receipt)
        ground_tokens.initialize(model, proc)
        model.mdg_tokenizer = proc.tokenizer
        model.auxiliary_heads.mdg = MaskGroundingHead(head_config(lm_dim=32, vit_dim=32, phrase_max=8))
        model.mdg_tau, model.mdg_tau_info = .37, {'source': 'init_artifact'}
        mdg_lora.install(model, 4)
        ground_tokens.install_rows(model)
        with torch.no_grad():
            model.auxiliary_heads.mdg_lora['opener_rows'].input_rows.add_(.2)
            model.auxiliary_heads.mdg_lora['opener_rows'].output_rows.add_(.3)
        write(root/'receipt.json', receipt)
        write(root/'code.json', dict(commit='1'*40))
        cfg = dict(Runtime.native, mdg=receipt['mdg'], preparation=file_pin(root/'receipt.json'), code=file_pin(root/'code.json'))
        write(root/'config.json', cfg)
        with RunnerTests().local_collectives(), mock.patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
            run.export(root/'milestone', model, model, cfg, 4)
        bundle = mdg_runtime.make_bundle(root/'bundle', config=root/'config.json', receipt=root/'receipt.json',
            model_manifest=Runtime.sources['model_manifest'], base_dir=Runtime.sources['base_dir'], artifact_dir=root/'milestone')
        with mock.patch.object(run, 'processor_for', side_effect=native_processor), \
                mock.patch.object(run, 'prepared', side_effect=AssertionError('training inputs opened')), \
                mock.patch.object(run, 'load_model', side_effect=AssertionError('base shards opened')):
            loaded, proc, _ = mdg_eval.load_runtime(file_pin(root/'config.json'), file_pin(root/'milestone/artifact.json'),
                root/'milestone/mdg', torch.device('cpu'), file_pin(bundle))
        self.assertEqual(loaded.ground_token_ids, model.ground_token_ids)
        for name, value in model.auxiliary_heads.mdg_lora.state_dict().items():
            self.assertTrue(torch.equal(value, loaded.auxiliary_heads.mdg_lora.state_dict()[name]), name)

    def test_public_decode_attach_binds_and_loads_trained_opener_rows(self):
        import os,tempfile
        from pathlib import Path
        from student_pilot import mdg_lora
        from student_pilot.mdg_decode_attach import attach_mdg
        from student_pilot.mask_grounding_head import save_artifact
        from student_pilot.p3_provenance import file_pin,write
        from student_pilot.carrier_c1_routing import add_routing_tokens
        from tests.test_stageb_mdg import fixture
        model,_,_=fixture(frames=2,lora_rank=4)
        proc=processor();add_routing_tokens(proc,include_ground=True)
        ground_tokens.add(proc);ground_tokens.initialize(model,proc)
        model.mdg_tokenizer=proc.tokenizer;ground_tokens.install_rows(model)
        with torch.no_grad():
            model.auxiliary_heads.mdg_lora['opener_rows'].input_rows.add_(.2)
            model.auxiliary_heads.mdg_lora['opener_rows'].output_rows.add_(.3)
        root=Path(tempfile.mkdtemp(prefix='e2e_attach_',dir=os.environ['LANE_TEST_OUTPUT']))
        write(root/'base.json',dict(fixture=True));base=file_pin(root/'base.json')
        weights=mdg_lora.export(root,model,model.state_dict())
        save_artifact(root,model.auxiliary_heads.mdg,dict(base_artifact=base,trainer_commit='1'*40,step=1,tau=.37,metrics={},calibration={'source':'fixture'},**weights))
        fresh,_,_=fixture(frames=2,lora_rank=0)
        other=processor();add_routing_tokens(other)
        attach_mdg(fresh,other,root,base_artifact_sha256=base['sha256'])
        self.assertEqual(fresh.ground_token_ids,model.ground_token_ids)
        for name,value in model.auxiliary_heads.mdg_lora.state_dict().items():
            self.assertTrue(torch.equal(value,fresh.auxiliary_heads.mdg_lora.state_dict()[name]),name)
