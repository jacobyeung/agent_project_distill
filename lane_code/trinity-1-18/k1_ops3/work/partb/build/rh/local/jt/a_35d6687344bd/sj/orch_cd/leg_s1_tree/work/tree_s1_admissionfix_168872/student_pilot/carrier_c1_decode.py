"""Self-routing decode loop for the C1 model (SELF_ROUTING_DESIGN 1.1).

One prefill with carriers reads the pose head once (32 per-frame codes, gravity, FoV
slots 7:9) and encodes the private depth map once, conditioned on that FoV. Each
sampled token extends the decoded tail; a closed head call (`<depth_at …>`, `<move …>`,
`<pose …>`, `<turn from=i to=j>`) or calculator call (`<dist …>`, `<closest …>`,
`<cam_dist …>`, `<angle …>`, `<turn from=P at=P to=P>`, `<area …>`) gets its response
from the SAME `OwnGeometry` and `PrintedPointRegistry` code the trainer uses for own
values. The response ids are forced into the native KV/recurrent cache, never sampled
or scored. Invalid calls get a typed error response. There is no cap below 16,384.
"""
from contextlib import ExitStack, nullcontext
from . import trace_format313 as trace313
from copy import deepcopy
from .ground_context import closed_adapters
import re
import unicodedata
from types import SimpleNamespace

import torch

from .tower_errors import TowerError, tower_item

from . import carrier_c1_routing as routing
from . import p3_printed_calculator as calculator
from .carrier_c1_data import C1_B, C1_C, frame_position_ids, standard_attention_mask

HEAD_FORMS = (
    ('depth_at', re.compile(r'<depth_at frame=(\d+) pts=\[(\[\d+,\d+\](?:,\[\d+,\d+\])*)\]>$')),
    ('move', re.compile(r'<move from=(\d+) to=(\d+)>$')),
    ('pose', re.compile(r'<pose frame=(\d+)>$')),
    ('turn', re.compile(r'<turn from=(\d+) to=(\d+)>$')),
)
CALCULATOR_TAIL = re.compile(r'<(?:dist|closest|cam_dist|angle|area) [^<>]*>$')
GROUND_TAIL = re.compile(r'<ground\b[^<>\n]*>$|<ground obj="[^"\n]*">$')
GROUND_FORM = re.compile(r'<ground obj="([^"<>]+)">')
GAP_TAIL = re.compile(r'<gap\b[^<>\n]*>$')
GAP_FORM = re.compile(r'<gap a="([^"<>]+)"((?: b="[^"<>]+")+)>')
MAX_CALL_TOKENS = 96
MODES = ('own', 'shuffle')


class CallError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def consume_cache_tokens(model, input_ids, attention_mask, cache, length=None, observer=None):
    """Consume outstanding sampled/injected tokens once using native positions (L1 bundle_decode)."""
    target = input_ids.shape[1] if length is None else length
    at = cache.get_seq_length()
    if not at <= target <= input_ids.shape[1]:
        raise ValueError('Cache continuation length is outside the outstanding suffix')
    output = None
    while at < target:
        upto = at + 1
        prepared = model.prepare_inputs_for_generation(
            input_ids[:, :upto], next_sequence_length=1,
            attention_mask=attention_mask[:, :upto],
            position_ids=model._prepare_position_ids_for_generation(input_ids[:, :upto],
                {'attention_mask': attention_mask[:, :upto], 'past_key_values': cache}),
            past_key_values=cache, use_cache=True, is_first_iteration=False)
        with observer.token(input_ids[:, at:upto]) if observer is not None else nullcontext():
            output = model(**prepared, return_dict=True)
        cache = output.past_key_values
        at = cache.get_seq_length()
        if at != upto:
            raise ValueError('Native cache did not consume exactly one outstanding token')
    return output, cache


def parse_head(text):
    """Strict v3.9 per_frame head calls: frames 1..32, 1-4 points in [20, 980]."""
    for name, form in HEAD_FORMS:
        match = form.search(text)
        if not match or match.start() != 0:
            continue
        values = match.groups()
        if name == 'depth_at':
            frame = int(values[0])
            pts = [[int(a), int(b)] for a, b in re.findall(r'\[(\d+),(\d+)\]', values[1])]
            if not 1 <= frame <= 32:
                raise CallError('bad_frame')
            if not 1 <= len(pts) <= 4:
                raise CallError('bad_point_count')
            if any(not (20 <= x <= 980) for p in pts for x in p):
                raise CallError('point_outside_20_980')
            return dict(name=name, frame=frame, pts=pts)
        frames = [int(v) for v in values]
        if any(not 1 <= k <= 32 for k in frames):
            raise CallError('bad_frame')
        return dict(name=name, frame=frames[0]) if name == 'pose' else dict(name=name, i=frames[0], j=frames[1])
    raise CallError('malformed_call')


def parse_ground(text):
    match = GROUND_FORM.fullmatch(text)
    if match is None or any(unicodedata.category(c) in ('Cc', 'Cf') for c in match[1]):
        if re.fullmatch(r'<ground obj="[^"\n]*">', text):
            raise CallError('bad_object')
        raise CallError('malformed_call')
    return match[1]


def parse_gap(text):
    match = GAP_FORM.fullmatch(text)
    if match is None:
        raise CallError('malformed_call')
    names = re.findall(r' b="([^"<>]+)"', match[2])
    for name in (match[1], *names):
        parse_ground(f'<ground obj="{name}">')
    if len(set(names)) != len(names):
        raise CallError('duplicate_candidate')
    return match[1], names[0] if len(names) == 1 else names


def ground_text(name, prob, uv, tau):
    frames = sorted((i for i, p in enumerate(prob) if p >= tau), key=lambda i: (-prob[i], i))[:3]
    return name + ': ' + (' | '.join(f'f{i+1} [{int(uv[i][0])},{int(uv[i][1])}] {prob[i]:.2f}'
                                    for i in frames) if frames else 'not seen')


@torch.no_grad()
def ground_predictions(model, tokenizer, gh, features, names, memory=None):
    from .grounding_features import phrase_embeddings
    if memory is None:
        memory = gh.encode_video(features.taps, features.vit, features.grid)
    embeds, mask = phrase_embeddings(model, tokenizer, names)
    decoded = gh.decode(gh(memory, gh.encode_query(embeds, mask)))
    prob, uv = decoded['prob'].detach().double().cpu(), decoded['uv'].detach().cpu()
    if (prob.shape != (len(names), 32) or uv.shape != (len(names), 32, 2)
            or not torch.isfinite(prob).all() or not torch.isfinite(uv).all()
            or not ((prob >= 0) & (prob <= 1)).all() or not ((uv >= 0) & (uv <= 1000)).all()
            or not torch.equal(uv, uv.round())):
        raise ValueError('Invalid grounding probabilities or canvas points')
    return [dict(name=name, prob=p.tolist(), uv=v.long().tolist()) for name, p, v in zip(names, prob, uv)]


class HeadState:
    """Head outputs read once per video, plus the response formatter shared with training."""
    def __init__(self, model, batch, hidden, gh=None, taps=None, *, pose_source='own', tower_state=None):
        if pose_source == 'own' and tower_state is not None:
            raise ValueError('own pose_source refuses tower_state')
        if pose_source != 'own':
            from .tower_read import validate_pose_source
            validate_pose_source(pose_source)
        pose = model.auxiliary_heads.pose
        positions = batch['aux_camera_positions']
        if not (positions >= 0).all():
            raise ValueError('Routed decoding requires all 32 frame carriers')
        stages, gravity, _ = pose.predict_all(pose.carrier_states(hidden.float(), positions), key_mask=positions >= 0)
        self.pose9 = stages[-1][0].double().cpu().numpy()
        self.gravity = None if not gravity else gravity[-1][0].double().cpu().numpy()
        self.depth_map, self.depth_head = None, None
        if hasattr(model.auxiliary_heads, 'depth'):
            if model.depth_fov_source != 'pose_head':
                raise ValueError('Routed depth requires the pose-head FoV')
            from .decoupled_v import features
            depth = model.auxiliary_heads.depth
            captured = features(depth, batch, allow_short=True)
            self.depth_head = depth.auxiliary_heads.camera.point_depth
            fov = stages[-1][..., 7:9].float()
            self.depth_map = self.depth_head.encode(captured.grids[0], captured.vits[0], fov[0])
        self.queries = []
        if pose_source == 'tower':
            from .tower_read import apply_tower
            apply_tower(self, tower_state, batch)
        self.ground_queries, self.ground_cache = [], {}
        self.grounding_head = gh if gh is not None else getattr(model, 'grounding_head', None)
        self.grounding_meta = getattr(model, 'grounding_meta', {})
        self.grounding_features = taps
        self.grounding_memory = None
        self.model, self.tokenizer = model, getattr(model, 'grounding_tokenizer', None)
        self.mdg_backend = None
        self.mdg_states = None

    @torch.no_grad()
    def ground(self, name, registry=None):
        if self.mdg_backend is not None:
            return self.mdg_backend.ground(name, self.mdg_states, registry)
        parse_ground(f'<ground obj="{name}">')
        if self.grounding_head is None:
            raise routing.RenderError('head_readout')
        if name not in self.ground_cache:
            if self.grounding_features is None or self.tokenizer is None:
                raise routing.RenderError('head_readout')
            tau = self.grounding_meta.get('tau')
            if type(tau) not in (int, float) or not 0 <= tau <= 1:
                raise ValueError('Grounding artifact requires tau in [0,1]')
            if self.grounding_memory is None:
                f = self.grounding_features
                self.grounding_memory = self.grounding_head.encode_video(f.taps, f.vit, f.grid)
            item = ground_predictions(self.model, self.tokenizer, self.grounding_head,
                                      self.grounding_features, [name], self.grounding_memory)[0]
            item['tau'] = tau
            self.ground_queries.append(item)
            self.ground_cache[name] = ground_text(name, item['prob'], item['uv'], tau)
        return self.ground_cache[name]

    def depth(self, frame, points):
        if self.depth_map is None:
            raise routing.RenderError('own depth head unavailable')
        uv = torch.full((self.depth_map.shape[0], len(points), 2), 500., device=self.depth_map.device)
        uv[frame - 1] = torch.as_tensor(points, dtype=torch.float32, device=uv.device)
        values = self.depth_head.query(self.depth_map, uv)[frame - 1].double().cpu().numpy()
        self.queries.append(dict(frame=frame, depth=values.tolist()))
        return values

    def geometry(self):
        return routing.OwnGeometry(self.pose9, self.gravity, self.depth)


def respond(call_text, registry, geometry, grounder=None, gapper=None):
    """Response text for one closed call; typed errors for invalid calls."""
    try:
        if call_text.startswith('<gap'):
            a, b = parse_gap(call_text)
            return (gapper(a, b) if gapper is not None else 'not seen'), dict(kind='gap', a=a, b=b)
        if call_text.startswith('<ground'):
            name = parse_ground(call_text)
            if grounder is None:
                raise routing.RenderError('head_readout')
            return grounder(name), dict(kind='ground', name=name)
        # v3.9 dispatch: a turn with at= and P labels is the calculator's waypoint turn.
        if CALCULATOR_TAIL.fullmatch(call_text) or (call_text.startswith('<turn ') and ' at=' in call_text):
            return registry.execute(call_text)['text'], dict(kind='calculator')
        if geometry is None:
            raise routing.RenderError('head readout unavailable')
        call = parse_head(call_text)
        if call['name'] == 'depth_at':
            lines = []
            for uv in call['pts']:
                cam, f1, spread = geometry.click(call['frame'], uv)
                lines.append(registry.register(camera=cam, f1=f1, spread=spread, requested_frame=call['frame'],
                                               actual_frame=call['frame'])['line'])
            return '\n'.join(lines), dict(kind='head', **call)
        if call['name'] == 'pose':
            return geometry.pose_text(call['frame']), dict(kind='head', **call)
        if call['name'] == 'move':
            return geometry.move_text(call['i'], call['j']), dict(kind='head', **call)
        return geometry.turn_text(call['i'], call['j']), dict(kind='head', **call)
    except CallError as exc:
        return f'error: {exc.code}', dict(kind='error', code=exc.code)
    except calculator.CalculatorError as exc:
        return f'error: {exc.reason}', dict(kind='error', code=exc.reason)
    except routing.RenderError as exc:
        return f'error: {exc}', dict(kind='error', code='head_readout')


def _prepare_decode(model, processor, batch, *, max_new_tokens=None, mode='own', donor_batch=None, max_calls=200,
             logits_processor=None, pose_source='own', tower_state=None, mask_source=None, ground_backend=None, reread=None, verify=None):
    """Prefill one video and retain its private tool/query state."""
    if batch['input_ids'].ndim != 2 or batch['input_ids'].shape[0] != 1:
        raise ValueError('Pass a sequence of single-row batches for batched routed decode')
    if mode not in MODES or (mode == 'shuffle') != (donor_batch is not None):
        raise ValueError('Shuffle mode needs a donor batch; own mode refuses one')
    if model.training:
        raise ValueError('Routed decoding requires eval mode')
    if batch.get('own_vit_reread') is not None:
        from .reread import validate_batch
        validate_batch(model, batch, mode)
    if reread is not None:
        from .hrp_reread import Config as HRPConfig
        if not isinstance(reread,HRPConfig) or mode != 'own':raise ValueError('reread_requires_own_mode_Config')
        reread.validate(batch)
    if verify is not None:
        from .verify_pass import Config as VerifyConfig
        if not isinstance(verify,VerifyConfig):raise TypeError('verify_requires_Config')
    if mask_source is not None or ground_backend is not None:
        from .ground_v3 import MASK_SOURCES
        if mask_source not in MASK_SOURCES or ground_backend is None or ground_backend.mask_source != mask_source:
            raise ValueError('mask_source_requires_matching_backend')
        source_batch = donor_batch if mode == 'shuffle' else batch
        if source_batch.get('video_sha256') != ground_backend.scene.video_sha256:
            raise ValueError('ground_backend_video_mismatch')
        ground_backend.scene.frames.require(source_batch.get('frame_indices', ()))
        ground_backend.begin_question()
    tokenizer = processor.tokenizer
    tokens = getattr(processor, '_routing_tokens', None)
    if tokens is None:
        raise ValueError('Processor lacks the routing opener tokens')
    openers = set(tokens['ids'].values())
    model.check_placement(batch)
    from transformers import Qwen3_5ForConditionalGeneration
    with torch.device('meta'):
        native = Qwen3_5ForConditionalGeneration(model.config)
    native.model, native.lm_head = model.model, model.lm_head
    context = model.config.text_config.max_position_embeddings
    prompt_length = batch['input_ids'].shape[1]
    if max_new_tokens is not None and (type(max_new_tokens) is not int or max_new_tokens < 16384):
        raise ValueError('Explicit caps must be at least 16384')
    cap = min(max_new_tokens or context, context - prompt_length)
    captured = {}
    if pose_source != 'own':
        from .tower_read import validate_pose_source, prepare_tower, TowerState
        validate_pose_source(pose_source)
        source_batch = donor_batch if mode == 'shuffle' else batch
        if tower_state is None:
            tower_state = prepare_tower(model, source_batch)
        if not isinstance(tower_state, TowerState):
            raise TowerError('tower pose source requires a TowerState')
        tower_state.validate_batch(source_batch)
    gh = getattr(model, 'grounding_head', None) if not trace313.active() else None
    from . import mdg_decode
    mdg = mdg_decode.decoder(model) if not trace313.active() else None
    if reread is not None and ground_backend is None:
        gh,mdg=None,None
    if ground_backend is not None:
        gh = None
        native_prior=ground_backend.stages.presence
        if hasattr(ground_backend.source, 'bind_native_backend') or hasattr(native_prior, 'bind_native_backend'):
            mdg = mdg_decode.decoder(model)
        if mask_source != 'mdg' and not hasattr(native_prior,'bind_native_backend'):
            mdg = None
        elif mdg is None and hasattr(ground_backend.source,'bind_native_backend'):
            raise ValueError('NativeMDG_requires_attached_head')
    if gh is not None and mdg is not None:
        raise ValueError('Attach one grounding backend per decode')
    stream = None  # Ordinary generation never opens the MDG adapter gate.
    if mdg is not None:
        from .mdg_features import bind_processor
        bind_processor(model, processor)

    def prefill_states(target_batch):
        positions = target_batch['aux_camera_positions']
        seen = [False]
        geometry = model.geometry_features(target_batch)

        def replace(module, args, output):
            if seen[0]:
                return output
            seen[0] = True
            return model.carrier_embeddings(output, positions, g3t)

        def prefill(module, args, values):
            if values['inputs_embeds'].shape[1] == target_batch['input_ids'].shape[1]:
                if model.carrier_placement == C1_B:
                    values['position_ids'] = frame_position_ids(values['position_ids'], target_batch)
                if model.carrier_placement == C1_C:
                    values['c1_prefix_mask'] = standard_attention_mask(target_batch, True)
            return args, values

        def norm(module, args, output):
            captured.setdefault('hidden', output)

        hooks = [model.get_input_embeddings().register_forward_hook(replace),
                 model.model.language_model.register_forward_pre_hook(prefill, with_kwargs=True),
                 model.model.language_model.norm.register_forward_hook(norm)]
        inputs = {k: target_batch[k] for k in ('input_ids', 'attention_mask', 'pixel_values_videos',
                                               'video_grid_thw', 'mm_token_type_ids') if k in target_batch}
        try:
            capture = nullcontext()
            if mdg is not None:
                capture = mdg_decode.PrefixCapture(model, target_batch)
            elif gh is not None:
                from .grounding_features import capture_from_hooks
                capture = capture_from_hooks(model, target_batch)
            with ExitStack() as stack:
                g3t = model.patch_injection(stack, target_batch, geometry)
                with capture as taps:
                    result = native(**inputs, use_cache=True, return_dict=True, logits_to_keep=1)
            if taps is not None:
                captured['grounding'] = taps.finish()
            return result
        finally:
            for hook in hooks:
                hook.remove()

    if mode == 'shuffle':
        donor_output = prefill_states(donor_batch)
        if mdg is not None:
            from .mdg_features import expand_cache
            donor_cache = expand_cache(donor_output.past_key_values, 1)
            donor_delta = model.model.rope_deltas.detach().clone()
        donor_output = None
        heads = HeadState(model, donor_batch, captured.pop('hidden'), taps=captured.pop('grounding', None),
                          pose_source=pose_source, tower_state=tower_state)
        model.model.rope_deltas = None
    output = prefill_states(batch)
    hidden = captured.pop('hidden')
    if mode == 'own':
        heads = HeadState(model, batch, hidden, taps=captured.pop('grounding', None),
                          pose_source=pose_source, tower_state=tower_state)
    heads.tokenizer = tokenizer
    geometry_error = None
    try:
        geometry = heads.geometry()
    except routing.RenderError as exc:
        if pose_source == 'tower':
            raise TowerError(str(exc)) from exc
        geometry, geometry_error = None, str(exc)
    if mdg is not None:
        from .ground_lifting import OwnGeometryAdapter
        from .mdg_features import PrefixFeatures, expand_cache
        p = heads.grounding_features
        query_batch = donor_batch if mode == 'shuffle' else batch
        prefix = PrefixFeatures(p.taps, p.vit, p.pixels, p.grid, p.hidden,
            donor_cache if mode == 'shuffle' else expand_cache(output.past_key_values, 1),
            query_batch['input_ids'].shape[1],
            donor_delta if mode == 'shuffle' else model.model.rope_deltas.detach().clone())
        heads.mdg_backend = mdg_decode.Backend(model, prefix, OwnGeometryAdapter(geometry), batch=query_batch)
    if ground_backend is not None:
        if hasattr(ground_backend.source,'bind_native_backend'):
            ground_backend.source.bind_native_backend(heads.mdg_backend)
        if hasattr(ground_backend.stages.presence,'bind_native_backend'):
            ground_backend.stages.presence.bind_native_backend(heads.mdg_backend)
        heads.mdg_backend = ground_backend
    if batch.get('own_vit_reread') is not None:
        from .reread import bind_heads
        bind_heads(model, processor, batch, heads)
    rereader = None
    if reread is not None:
        from .hrp_reread import Backend as HRPBackend
        rereader=HRPBackend(model,processor,geometry,reread)
    from .ground_context import from_row
    tool_context = from_row(heads,geometry,donor_batch if mode == 'shuffle' else batch,ground_backend,rereader)
    verify_session = None
    if verify is not None:
        from .verify_pass import Session
        verify_session=Session(model,processor,verify)
    state = SimpleNamespace(native=native, output=output, heads=heads, geometry=geometry,
                           geometry_error=geometry_error, prompt_length=prompt_length, cap=cap,
                           tokenizer=tokenizer, openers=openers, mdg=mdg, stream=stream,
                           ground_backend=ground_backend, tool_context=tool_context,verify_session=verify_session,rereader=rereader)
    trace313.bind_state(state)
    return state


@torch.no_grad()
@closed_adapters
def generate(model, processor, batch, *, max_new_tokens=None, mode='own', donor_batch=None, max_calls=200,
             logits_processor=None, pose_source='own', tower_state=None, mask_source=None, ground_backend=None, reread=None, verify=None, reference_trace=None):
    """Decode one prompt dict, or batch a sequence of prompt-only single-row dicts.

    A dict returns one record. A sequence returns records in input order. For a
    sequence, donor_batch/tower_state/logits_processor are corresponding per-row
    sequences (or None). Video prefills remain serial; token forwards are batched.
    """
    from .scripted_calls import validate_reference
    refs = reference_trace if isinstance(batch,(list,tuple)) else [reference_trace]
    if reference_trace is not None:
        if not isinstance(refs,(list,tuple)) or len(refs)!=(len(batch) if isinstance(batch,(list,tuple)) else 1):
            raise ValueError('One reference trace per row is required')
        for ref in refs: validate_reference(ref)
    kwargs = dict(max_new_tokens=max_new_tokens, mode=mode, donor_batch=donor_batch,
                  max_calls=max_calls, logits_processor=logits_processor,
                  pose_source=pose_source, tower_state=tower_state,mask_source=mask_source,ground_backend=ground_backend,reread=reread,verify=verify,reference_trace=reference_trace)
    if isinstance(batch, (list, tuple)):
        from .carrier_c1_batch_decode import generate_batch
        return generate_batch(model, processor, batch, **kwargs)
    return _generate_one(model, processor, batch, **kwargs)


@tower_item
def _generate_one(model, processor, batch, *, max_new_tokens=None, mode='own', donor_batch=None, max_calls=200,
                  logits_processor=None, pose_source='own', tower_state=None, mask_source=None, ground_backend=None, reread=None, verify=None, reference_trace=None):
    from .carrier_c1_batch_decode import Row
    from .scripted_calls import ReferenceChoice
    choice=ReferenceChoice(reference_trace,processor.tokenizer) if reference_trace is not None else None
    state = _prepare_decode(model, processor, batch, max_new_tokens=max_new_tokens, mode=mode,
        donor_batch=donor_batch, pose_source=pose_source, tower_state=tower_state,
        mask_source=mask_source,ground_backend=ground_backend,reread=reread,verify=verify)
    row=Row(state,processor,model,mode=mode,pose_source=pose_source,max_calls=max_calls,
            max_new_tokens=max_new_tokens,logits_processor=logits_processor,reference_choice=choice)
    output=state.output;cache=output.past_key_values
    while row.finish is None:
        row.step(output.logits[:,-1,:])
        if row.finish is not None:break
        full=torch.cat((batch['input_ids'],batch['input_ids'].new_tensor([row.ids])),1)
        mask=torch.cat((batch['attention_mask'],batch['attention_mask'].new_ones((1,len(row.ids)))),1)
        output,cache=consume_cache_tokens(state.native,full,mask,cache,observer=state.stream)
    return row.record()


def ground_records(state):
    heads=state.heads
    result=deepcopy(dict(ground_queries=heads.mdg_backend.queries,
        gap_queries=heads.mdg_backend.gap_queries,query_passes=heads.mdg_backend.query_passes)
        if heads.mdg_backend is not None else dict(ground_queries=heads.ground_queries)
        if heads.grounding_head is not None else {})
    queries=result.get('ground_queries',[])
    if state.rereader is not None:
        names={q['name'] for q in state.rereader.queries}
        queries=[q for q in queries if q['name'] not in names]+deepcopy(state.rereader.queries)
    if state.verify_session is not None:
        names={q['name'] for q in state.verify_session.queries}
        queries=[q for q in queries if q['name'] not in names]+deepcopy(state.verify_session.queries)
    if queries or 'ground_queries' in result or state.rereader is not None:result['ground_queries']=queries
    if getattr(state,"live_trace_session",None) is not None:
        result["trace313_live"]=True
        if state.live_trace_session.spec_version != "3.13":
            result["trace_program_version"]=state.live_trace_session.spec_version
        result["ground_queries"]=deepcopy(state.live_trace_session.queries)
    return result


def ground_layout_for(state,info):
    return trace313.active() or state.ground_backend is not None or state.verify_session is not None or state.rereader is not None or (info['kind'] in ('ground','gap','error') and (state.mdg is not None or info['kind']=='gap'))


def respond_state(state,call_text,registry):
    formatted=trace313.respond(call_text,registry)
    if formatted is not None:return formatted
    heads=state.heads
    if state.mdg is not None and state.ground_backend is None and call_text.startswith('<ground'):
        try:
            name=parse_ground(call_text)
        except CallError:
            name=None
        if name is not None:
            heads.mdg_states=heads.mdg_backend.query(name)
    context=state.tool_context
    context.registry=registry
    context.mdg_states=heads.mdg_states
    context.fallback=(lambda name:state.rereader.ground(name,registry)) if state.rereader is not None else (lambda name:heads.ground(name,registry))
    gapper=heads.mdg_backend.gap if heads.mdg_backend is not None else None
    if state.verify_session is not None and call_text.startswith('<ground'):
        try:
            name=parse_ground(call_text)
            return state.verify_session.ground(name,context)
        except CallError as exc:
            return 'error: '+exc.code,dict(kind='error',code=exc.code)
        except torch.cuda.OutOfMemoryError as exc:
            return 'error: verify_out_of_memory',dict(kind='error',code='verify_out_of_memory',error_type=type(exc).__name__)
    return respond(call_text,registry,state.geometry,context.fallback,gapper)


def replay(record):
    """Canary C2: recompute every injected response offline from the recorded head outputs."""
    if record["heads"].get("trace313_live"):
        from .live_trace313 import replay
        return replay(record)
    queue = list(record['heads']['depth_queries'])

    def depth(frame, points):
        item = queue.pop(0)
        if item['frame'] != frame or len(item['depth']) != len(points):
            raise routing.RenderError('depth query order differs')
        return item['depth']
    heads = record['heads']
    from collections import defaultdict,deque
    grouped=defaultdict(list)
    for query in heads.get('ground_queries',[]):grouped[query['name']].append(query)
    ground_queries={name:rows[-1] for name,rows in grouped.items()}
    pending={name:deque(rows) for name,rows in grouped.items()
             if any(q.get('backend') in ('ground_v3','verify') for q in rows)}
    used = set()

    def ground(name):
        if name not in ground_queries:
            raise routing.RenderError('head_readout')
        used.add(name)
        q = pending[name].popleft() if pending.get(name) else ground_queries[name]
        if q.get('backend') in ('ground_v3','verify'):
            return v3_replay.ground(name,q)
        if q.get('backend') == 'hrp_reread':
            return hrp_replay.ground(name)
        if q.get('backend') == 'mdg':
            return mdg_replay.ground(name)
        return ground_text(name, q['prob'], q['uv'], q['tau'])

    def gap(a, b):
        if v3_replay is not None:return v3_replay.gap(a,b)
        return 'not seen' if mdg_replay is None else mdg_replay.gap(a, b)

    try:
        geometry = routing.OwnGeometry(heads['pose9'], heads['gravity'], depth)
    except routing.RenderError:
        geometry = None
    registry, mismatches = calculator.PrintedPointRegistry(), 0
    from .mdg_decode import ReplayBackend
    mdg_replay = ReplayBackend(ground_queries, geometry, registry) if any(
        q.get('backend') == 'mdg' for q in ground_queries.values()) else None
    from .ground_replay import ReplayBackend as V3Replay
    v3_replay = V3Replay(ground_queries,geometry,registry) if any(
        q.get('backend') in ('ground_v3','verify') for q in ground_queries.values()) else None
    hrp_replay=None
    if any(q.get('backend')=='hrp_reread' for q in ground_queries.values()):
        from .hrp_reread import ReplayBackend as HRPReplay
        hrp_replay=HRPReplay(ground_queries,geometry,registry)
    for call in record['calls']:
        if call['kind'] == 'error':
            continue
        text, _ = respond(call['call'], registry, geometry, ground, gap)
        mismatches += text != call['response']
    return dict(calls=len(record['calls']), mismatches=mismatches,
                byte_equal=mismatches == 0 and not queue and not any(pending.values()) and used == set(ground_queries))


# A caller supplies its source-bound response session. Off by default.
generate = trace313.bind_generate(generate)
