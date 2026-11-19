"""Trainer loading and batch construction; no model is instantiated on import."""
from copy import deepcopy


def verify_trainer(selected=None, code=None):
    import json
    from pathlib import Path
    import student_pilot
    from .items import sha256
    root = Path(student_pilot.__file__).resolve().parent
    if selected is None and code is not None:
        from student_pilot.p3_provenance import load, pinned
        seal = load(pinned(code))
        if seal.get('schema') == 'c1-sealed-source-v1':
            selected = dict(source_revision=seal['commit'], root=str(root),
                            sources={name.removeprefix('student_pilot/'): value
                                     for name, value in seal['files'].items() if name.startswith('student_pilot/')})
    pins = selected or json.loads(Path(__file__).with_name('SOURCE_PINS.json').read_text())['trainer']
    different = [name for name, expected in pins['sources'].items() if sha256(root / name) != expected]
    if different:
        raise ValueError('Staged trainer differs from pinned evaluation source: ' + ', '.join(different))
    return pins


def evaluator_init_spec(receipt, artifact_pin):
    from student_pilot.trained_groups import init_groups
    return dict(schema='s1-evaluator-init-v1', artifact=artifact_pin, groups=init_groups(receipt))


def check_init_spec(receipt, artifact_pin, spec=None):
    from student_pilot.p3_provenance import load, pinned
    expected = evaluator_init_spec(receipt, artifact_pin)
    if spec is None:
        spec = expected
    elif set(spec) == {'path', 'sha256'}:
        spec = load(pinned(spec))
    if spec != expected:
        raise ValueError('Evaluator init spec omits or changes trained groups')
    artifact = load(pinned(artifact_pin))
    if artifact.get('b7_inputs'):
        from student_pilot.b7_inputs import reader_layout
        reader_layout(artifact,receipt)
    from student_pilot.source_seal import check_export
    check_export(receipt, artifact)
    from student_pilot.trace_version import resolve
    resolve(artifact, receipt)
    if not isinstance(artifact.get('trained_groups'), dict):
        raise ValueError('Evaluator artifact lacks its trained-group contract')
    if 'grounding' in expected['groups']:
        tau = artifact.get('mdg', {}).get('tau')
        if type(tau) not in (int, float) or not 0 <= tau <= 1:
            raise ValueError('Evaluator grounding artifact lacks its frozen threshold')
    return spec


def load_model(kind, cfg, *, artifact_pin=None, snapshot=None, device='cuda:0', selected_trainer=None,
               on_stage=None, init_spec=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/runtime.py:load_model')
    def stage(name):
        if on_stage:
            on_stage(dict(phase=name))
    import torch
    from student_pilot import rehearsal
    if torch.device(device).type != 'cuda' and not rehearsal.enabled():
        raise ValueError('Model evaluation is GPU only; CPU model dry runs are forbidden')
    stage('verify_trainer')
    trainer_pin = verify_trainer(selected_trainer, cfg.get('code'))
    if kind == 'base':
        from transformers import Qwen3_5ForConditionalGeneration
        from student_pilot.decoupled_v_run import processor_for
        processor = processor_for(snapshot)
        model = Qwen3_5ForConditionalGeneration.from_pretrained(
            snapshot, local_files_only=True, trust_remote_code=False,
            dtype=torch.bfloat16, attn_implementation='sdpa')
        info = dict(kind=kind, snapshot=str(snapshot), authorization_file_check='not_applicable')
    elif kind == 'routed':
        from student_pilot import carrier_c1_run as trainer
        # Exactly inference(), omitting only its per-job allocation authorization block.
        stage('prepared')
        receipt, manifest = trainer.prepared(cfg, admission=True)
        if selected_trainer:
            manifest = {**manifest, 'root': snapshot}
        stage('processor_for_receipt')
        processor = trainer.processor_for_receipt(manifest, receipt)
        stage('load_model')
        init_spec = check_init_spec(receipt, artifact_pin, init_spec)
        loading_receipt = {key: value for key, value in receipt.items() if key != 'init_artifact'}
        model = trainer.load_model(manifest, loading_receipt, processor, evaluation=True)
        stage('load_artifact')
        model.readout_evaluation_config = cfg
        artifact = trainer.load_artifact(model, artifact_pin)
        if artifact['base_identity'] != cfg['base_identity']:
            raise ValueError('Readout artifact has another base model')
        if artifact['config_sha256'] != trainer.identity(cfg):
            raise ValueError('Readout artifact has another C1 config identity')
        info = dict(kind=kind, artifact=artifact_pin, step=artifact.get('step'), init_spec=init_spec,
                    authorization_file_check='omitted; parent kit owns allocation authorization')
        if not hasattr(processor, '_routing_tokens'):
            if selected_trainer:
                raise ValueError('Final trainer processor must install routing tokens')
            # A legacy mixed export lacks final-mode opener tokens. Keep its vocabulary
            # and weights intact: arm the trainer loop on the native lexical prefix.
            from student_pilot.carrier_c1_routing import OPENERS
            from student_pilot.p3_grammar import RESPONSE_TOKENS
            vocab = processor.tokenizer.get_vocab()
            if any(t not in vocab for t in RESPONSE_TOKENS):
                raise ValueError('Mixed artifact lacks trainer tool-response vocabulary')
            ids = {o: processor.tokenizer.encode(o, add_special_tokens=False)[0] for o in OPENERS}
            processor._routing_tokens = dict(ids=ids, constituents={})
            info['routing_openers'] = 'legacy native lexical prefixes; GPU parity required'
    else:
        raise ValueError('kind must be base or routed')
    stage('model_to_device')
    model.to(device).eval().requires_grad_(False)
    info['trainer'] = trainer_pin
    return model, processor, info


def teacher_batch(processor, row, cfg, kind):
    from student_pilot import carrier_c1_data as data
    layout, gap = data.layout_settings(cfg)
    if kind == 'routed':
        return data.encode(processor, row, {}, 'vqa', cfg['carrier_placement'],
                           cfg.get('training_mode', 'final'), layout, gap,
                           geometry_online=cfg.get('geometry_online'))[0]
    # The same trainer frame/layout encoder, without inserting CAM carriers.
    return data.encode_layout_row(processor, row, layout, gap,
                                 gf1=(cfg.get('geometry_online') or {}).get('gf1'))[0]


def prompt_batch(processor, row, cfg, kind):
    if kind == 'routed':
        from student_pilot.carrier_c1_canary import prompt_batch as trainer_prompt
        batch = trainer_prompt(processor, row, cfg)
        from student_pilot.scene_state import digest
        inputs = row['student_input']
        frames = inputs['frame_indices']
        video = (inputs.get('video_identity') or {}).get('video_sha256')
        batch.setdefault('frame_indices', frames)
        batch.setdefault('video_sha256', video or digest(dict(
            frame_indices=frames, frames=[frame['sha256'] for frame in inputs['frames']])))
        return batch
    import torch
    from student_pilot.carrier_c1_data import READOUT_TARGET
    batch = teacher_batch(processor, {**row, 'target': READOUT_TARGET}, cfg, kind)
    start = int(torch.where(batch['labels'][0] != -100)[0][0])
    return {k: (v[:, :start] if k in ('input_ids', 'attention_mask', 'mm_token_type_ids') else v)
            for k, v in batch.items() if k != 'labels'}


def generate(model, processor, batch, kind, max_new_tokens=None, tap=None, pose_override=None,
             ground_backend=None, mask_source=None, pose_source='own', tower_state=None, reference_trace=None):
    import torch
    if max_new_tokens is not None and (type(max_new_tokens) is not int or max_new_tokens < 16384):
        raise ValueError('Explicit generation caps must be at least 16384')
    if kind == 'routed':
        from student_pilot.carrier_c1_decode import generate as trainer_generate
        if pose_override is not None:
            from .pose_override import generate as override_generate
            return override_generate(trainer_generate, pose_override, model, processor, batch,
                                     max_new_tokens=max_new_tokens, logits_processor=tap)
        return trainer_generate(model, processor, batch, max_new_tokens=max_new_tokens,
                                logits_processor=tap, ground_backend=ground_backend, mask_source=mask_source,
                                pose_source=pose_source, tower_state=tower_state, reference_trace=reference_trace)
    from transformers import LogitsProcessor, LogitsProcessorList
    start = batch['input_ids'].shape[1]
    context = model.config.text_config.max_position_embeddings
    cap = min(max_new_tokens or context, context - start)
    if cap < 1:
        raise ValueError('Prompt exhausts context')

    class Tap(LogitsProcessor):
        def __call__(self, input_ids, scores):
            return tap(input_ids[0, start:].tolist(), scores) if tap else scores

    keys = ('input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw', 'mm_token_type_ids')
    generation_cfg = deepcopy(model.generation_config)
    with torch.no_grad():
        result = model.generate(**{k: batch[k] for k in keys if k in batch},
            generation_config=generation_cfg, do_sample=False, num_beams=1, temperature=None,
            top_p=None, top_k=None, min_p=None, repetition_penalty=1.0, length_penalty=1.0,
            no_repeat_ngram_size=0, min_new_tokens=None, early_stopping=False,
            max_new_tokens=cap, use_cache=True, return_dict_in_generate=True,
            output_scores=False, logits_processor=LogitsProcessorList([Tap()]))
    tokens = result.sequences[0, start:].tolist()
    eos = generation_cfg.eos_token_id
    eos = set(eos if isinstance(eos, (list, tuple)) else [eos])
    finish = 'eos' if tokens and tokens[-1] in eos else (
        'max_new_tokens' if max_new_tokens else 'context_exhaustion')
    return dict(tokens=tokens, text=processor.tokenizer.decode(tokens, skip_special_tokens=False),
                calls=[], errors=0, finish=finish, prompt_tokens=start, generated_tokens=len(tokens))
