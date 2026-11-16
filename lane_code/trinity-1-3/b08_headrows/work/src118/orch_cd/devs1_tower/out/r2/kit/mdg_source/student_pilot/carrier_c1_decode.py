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
from contextlib import nullcontext
import re

import torch

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
GROUND_FORM = re.compile(r'<ground obj="([a-z0-9 _-]{1,40})">')
MAX_CALL_TOKENS = 96
MODES = ('own', 'shuffle')


class CallError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def consume_cache_tokens(model, input_ids, attention_mask, cache, length=None):
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
    if match is None:
        if re.fullmatch(r'<ground obj="[^"\n]*">', text):
            raise CallError('bad_object')
        raise CallError('malformed_call')
    return match[1]


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
    def __init__(self, model, batch, hidden, gh=None, taps=None):
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
        self.ground_queries, self.ground_cache = [], {}
        self.grounding_head = gh if gh is not None else getattr(model, 'grounding_head', None)
        self.grounding_meta = getattr(model, 'grounding_meta', {})
        self.grounding_features = taps
        self.grounding_memory = None
        self.model, self.tokenizer = model, getattr(model, 'grounding_tokenizer', None)

    @torch.no_grad()
    def ground(self, name):
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


def respond(call_text, registry, geometry, grounder=None):
    """Response text for one closed call; typed errors for invalid calls."""
    try:
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


@torch.no_grad()
def generate(model, processor, batch, *, max_new_tokens=None, mode='own', donor_batch=None, max_calls=200,
             logits_processor=None):
    """Greedy routed decode of one prompt-only batch (from insert_frame_carriers)."""
    if mode not in MODES or (mode == 'shuffle') != (donor_batch is not None):
        raise ValueError('Shuffle mode needs a donor batch; own mode refuses one')
    if model.training:
        raise ValueError('Routed decoding requires eval mode')
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
    gh = getattr(model, 'grounding_head', None)

    def prefill_states(target_batch):
        positions = target_batch['aux_camera_positions']
        seen = [False]

        def replace(module, args, output):
            if seen[0]:
                return output
            seen[0] = True
            return model.carrier_embeddings(output, positions)

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
            if gh is not None:
                from .grounding_features import capture_from_hooks
                capture = capture_from_hooks(model, target_batch)
            with capture as taps:
                result = native(**inputs, use_cache=True, return_dict=True, logits_to_keep=1)
            if taps is not None:
                captured['grounding'] = taps.finish()
            return result
        finally:
            for hook in hooks:
                hook.remove()

    if mode == 'shuffle':
        prefill_states(donor_batch)
        heads = HeadState(model, donor_batch, captured.pop('hidden'), taps=captured.pop('grounding', None))
        model.model.rope_deltas = None
    output = prefill_states(batch)
    hidden = captured.pop('hidden')
    if mode == 'own':
        heads = HeadState(model, batch, hidden, taps=captured.pop('grounding', None))
    heads.tokenizer = tokenizer
    geometry_error = None
    try:
        geometry = heads.geometry()
    except routing.RenderError as exc:
        geometry, geometry_error = None, str(exc)
    cache = output.past_key_values
    eos = native.generation_config.eos_token_id if native.generation_config else None
    eos = set(eos if isinstance(eos, (list, tuple)) else [eos or tokenizer.eos_token_id]) | {tokenizer.eos_token_id}
    reserved = [tokenizer.convert_tokens_to_ids('<tool_response>'), tokenizer.convert_tokens_to_ids('</tool_response>'),
                model.carrier_id]
    ids, records, active, registry, finish = [], [], None, calculator.PrintedPointRegistry(), 'context_exhaustion'
    attention = batch['attention_mask']
    while len(ids) < cap:
        logits = output.logits[:, -1, :].float()
        logits[:, reserved] = -float('inf')
        if logits_processor is not None:
            logits = logits_processor(ids, logits)
        token = int(logits.argmax(-1))
        if token in reserved:
            raise ValueError('Generated tokens cannot impersonate injected responses or carriers')
        ids.append(token)
        if token in eos:
            finish = 'eos'
            break
        if token in openers:
            active = len(ids) - 1
        tail = tokenizer.decode(ids[active:] if active is not None else ids[-24:], skip_special_tokens=False)
        call_text = None
        if active is not None and (tail.endswith('>') or len(ids) - active > MAX_CALL_TOKENS):
            match = GROUND_TAIL.search(tail)
            call_text, active = match.group(0) if match else tail, None
        elif active is None and tail.endswith('>'):
            ground_tail = tokenizer.decode(ids[-MAX_CALL_TOKENS:], skip_special_tokens=False)
            match = GROUND_TAIL.search(ground_tail) or CALCULATOR_TAIL.search(tail)
            call_text = match.group(0) if match else None
        if call_text is not None:
            if len(records) >= max_calls:
                finish = 'call_limit'
                break
            text, info = respond(call_text, registry, geometry, heads.ground)
            forced = tokenizer.encode('<tool_response>' + text + '</tool_response>', add_special_tokens=False)
            forced = forced[:max(0, cap - len(ids))]
            records.append(dict(call=call_text, response=text, at_token=len(ids), forced_tokens=len(forced), **info))
            ids.extend(forced)
        full = torch.cat((batch['input_ids'], batch['input_ids'].new_tensor([ids])), 1)
        mask = torch.cat((attention, attention.new_ones((1, len(ids)))), 1)
        output, cache = consume_cache_tokens(native, full, mask, cache)
        if len(ids) >= cap:
            finish = 'max_new_tokens' if max_new_tokens else 'context_exhaustion'
    return dict(tokens=ids, text=tokenizer.decode(ids, skip_special_tokens=False), calls=records, finish=finish,
                mode=mode, heads=dict(pose9=heads.pose9.tolist(),
                                      gravity=None if heads.gravity is None else heads.gravity.tolist(),
                                      depth_queries=heads.queries,
                                      **(dict(ground_queries=heads.ground_queries) if heads.grounding_head is not None else {})),
                geometry_error=geometry_error, prompt_tokens=prompt_length, generated_tokens=len(ids),
                errors=sum(r['kind'] == 'error' for r in records))


def replay(record):
    """Canary C2: recompute every injected response offline from the recorded head outputs."""
    queue = list(record['heads']['depth_queries'])

    def depth(frame, points):
        item = queue.pop(0)
        if item['frame'] != frame or len(item['depth']) != len(points):
            raise routing.RenderError('depth query order differs')
        return item['depth']
    heads = record['heads']
    ground_queries = {q['name']: q for q in heads.get('ground_queries', [])}
    used = set()

    def ground(name):
        if name not in ground_queries:
            raise routing.RenderError('head_readout')
        used.add(name)
        q = ground_queries[name]
        return ground_text(name, q['prob'], q['uv'], q['tau'])

    geometry = routing.OwnGeometry(heads['pose9'], heads['gravity'], depth)
    registry, mismatches = calculator.PrintedPointRegistry(), 0
    for call in record['calls']:
        if call['kind'] == 'error':
            continue
        text, _ = respond(call['call'], registry, geometry, ground)
        mismatches += text != call['response']
    return dict(calls=len(record['calls']), mismatches=mismatches,
                byte_equal=mismatches == 0 and not queue and used == set(ground_queries))
