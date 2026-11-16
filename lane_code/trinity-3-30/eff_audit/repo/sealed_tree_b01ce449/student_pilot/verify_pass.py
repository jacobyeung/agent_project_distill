"""Same-weight image verification at the closed-ground-call boundary.

Config.backend supplies verify_request(name, context) and
accept_verify(name, result, context), which returns the trained ground text.
Requests contain in-memory RGB frames, candidate masks/crops and explicit slots.
This module opens no frame files and never receives the routed cache.
"""
from contextvars import ContextVar
from dataclasses import dataclass
from copy import deepcopy
import hashlib
import inspect
import resource

import torch

from .reread_isolation import isolated

MAX_NEW_TOKENS = 128

_session = ContextVar('ground_verify_session', default=None)
_inside = ContextVar('ground_verify_subforward', default=False)


@dataclass(frozen=True)
class Config:
    backend: object
    max_queries: int = 256
    max_candidates: int = 5
    identity: str = 'verifykit_v1_same_weights'

    def __post_init__(self):
        if type(self.max_queries) is not int or self.max_queries < 0:
            raise ValueError('max_queries must be a nonnegative integer')
        if type(self.max_candidates) is not int or not 1 <= self.max_candidates <= 20:
            raise ValueError('max_candidates must be in 1..20')
        for method in ('verify_request', 'accept_verify'):
            if not callable(getattr(self.backend, method, None)):
                raise TypeError('Verify backend requires ' + method)


class Budget:
    """Reserve the complete object query before reading any candidate, as in HRP."""
    def __init__(self, limit=256):
        if type(limit) is not int or limit < 0:
            raise ValueError('Invalid query budget')
        self.limit, self.used = limit, 0

    def reserve(self, count):
        if self.used + count > self.limit:
            return False
        self.used += count
        return True


def native_view(model):
    """Use CarrierC1's native wrapper convention without installing video hooks."""
    if 'input_ids' in inspect.signature(model.forward).parameters:
        return model
    from transformers import Qwen3_5ForConditionalGeneration
    with torch.device('meta'):
        native = Qwen3_5ForConditionalGeneration(model.config)
    native.model, native.lm_head = model.model, model.lm_head
    native.training = False
    native.generation_config = deepcopy(getattr(model,'generation_config',None))
    if native.generation_config is None:
        from pathlib import Path
        checkpoint=Path(getattr(model.config,'_name_or_path',''))
        if str(checkpoint).startswith('/scratch/') and (checkpoint/'generation_config.json').is_file():
            from transformers import GenerationConfig
            native.generation_config=GenerationConfig.from_pretrained(checkpoint,local_files_only=True)
    return native


def _rgb(image):
    import numpy as np
    from PIL import Image
    a = np.asarray(image)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3 or min(a.shape[:2]) < 1:
        raise ValueError('Verify requires uint8 RGB images')
    return image if isinstance(image, Image.Image) else Image.fromarray(a)


def _image_receipt(image):
    return dict(rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest(), size=list(image.size))


def _plan(request, max_candidates):
    name = request['name']
    if not isinstance(name, str) or not name.strip() or any(c in name for c in '<>\n\r'):
        raise ValueError('Invalid verify name')
    candidates = request.get('candidates', [])
    if len(candidates) > max_candidates:
        raise ValueError('Verify candidate cap exceeded')
    ids = [c['candidate_id'] for c in candidates]
    if any(not isinstance(c, str) or not c for c in ids) or len(ids) != len(set(ids)):
        raise ValueError('Candidate IDs must be unique nonempty strings')
    forms = tuple(request.get('forms', ('V1',)))
    if not forms or len(forms) != len(set(forms)) or any(f not in ('V1', 'V2', 'V3') for f in forms):
        raise ValueError('Invalid verification forms')
    slots = request.get('v3_slots', [])
    if 'V3' in forms and (not 1 <= len(slots) <= 4 or len(slots) != len(set(slots))):
        raise ValueError('V3 requires one to four distinct presence-ranked slots')
    for slot in [c['slot'] for c in candidates] + (slots if 'V3' in forms else []):
        if type(slot) is not int or not 1 <= slot <= 32:
            raise ValueError('Verify slots are one based in 1..32')
    count = sum(len(candidates) if f == 'V1' else (len(candidates)+4)//5 if f == 'V2' else len(slots)
                for f in forms)
    return forms, candidates, slots, count


def native_mask(mask):
    """Nearest pixel-centre sampling (PIL NEAREST); native SAM masks pass unchanged."""
    import numpy as np
    from PIL import Image
    m=np.asarray(mask)
    if m.dtype != bool or m.ndim != 2 or min(m.shape)<1:
        raise ValueError('Candidate mask must be boolean H by W')
    return m if m.shape==(480,640) else np.asarray(Image.fromarray(m).resize((640,480),Image.Resampling.NEAREST),bool)


def _frame(request,candidate):
    from .ground_context import GroundContext
    context=request.get('context')
    if context is None:
        context=GroundContext(None,None,None,None,request.get('clip_key',''),
            request['frame_map'],request.get('frames',{}),dict(hrp_frame_indices=request['frame_map'].source_indices))
    return _rgb(context.frame(candidate['slot'],candidate['source_index'],candidate['rgb_sha256']))


def _materialize(request, forms, candidates, slots):
    from verifykit.render import render, sheet
    frames = request.get('frames', {})
    crops, metadata, dropped = [], [], []
    if 'V1' in forms or 'V2' in forms:
        for candidate in candidates:
            try:
                image=_frame(request,candidate)
                if 'crop' in candidate:
                    crop = _rgb(candidate['crop'])
                    if crop.size != (448,448):raise ValueError('Renderer crops must be 448x448')
                    # A supplied crop must reproduce the kit from the bound frame/mask.
                    expected,meta=render(image,native_mask(candidate['mask']),'outline')
                    if _image_receipt(crop) != _image_receipt(expected):raise ValueError('Candidate crop hash differs')
                else:
                    crop, meta = render(image, native_mask(candidate['mask']), 'outline')
                crops.append(crop)
                metadata.append(dict(candidate_id=candidate['candidate_id'],slot=candidate['slot'],
                    source_index=candidate['source_index'],frame_rgb_sha256=candidate['rgb_sha256'],**meta))
            except torch.cuda.OutOfMemoryError:
                raise
            except Exception as exc:
                dropped.append(dict(candidate_id=candidate.get('candidate_id'),error_type=type(exc).__name__,error=str(exc)))
    result = {'_dropped':dropped}
    if 'V1' in forms:result['V1']=(crops,[[m] for m in metadata])
    if 'V2' in forms:
        result['V2']=([sheet(crops[i:i+5]) for i in range(0,len(crops),5)],
                      [metadata[i:i+5] for i in range(0,len(crops),5)])
    if 'V3' in forms:
        mapping=request.get('frame_map') or request['context'].frame_map
        result['V3']=([_frame(request,dict(slot=k,source_index=mapping.source_indices[k-1],
            rgb_sha256=mapping.rgb_sha256[k-1])) for k in slots],[[dict(slot=k)] for k in slots])
    return result


def _cpu_peak():
    # Linux ru_maxrss includes native Torch storage; tracemalloc does not.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _forward_form(model, processor, name, form, images, metadata):
    from verifykit.model import HFBackend, read_logits, token_groups, parse_boxes
    from verifykit.render import prompt
    texts = [processor.apply_chat_template(
        [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': prompt(form, name)}]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False) for _ in images]
    encoded = batch = output = logits = generated = None
    tokenizer = processor.tokenizer
    padding_side = tokenizer.padding_side
    try:
        tokenizer.padding_side = 'left'
        encoded = processor(text=texts, images=images, return_tensors='pt', padding=True, size=HFBackend.size(form))
        if any(k in encoded for k in ('past_key_values','cache_position','inputs_embeds')):
            raise ValueError('Processor supplied mutable decode state')
        device = model.get_input_embeddings().weight.device
        batch = {k: v.to(device) if hasattr(v,'to') else v for k, v in encoded.items()}
        if not all(k in batch for k in ('input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw')):
            raise ValueError('Processor did not produce a native image batch')
        width = batch['input_ids'].shape[1]
        cap = MAX_NEW_TOKENS if form == 'V3' else 1
        if width + cap > model.config.text_config.max_position_embeddings:
            raise ValueError('Verify query exceeds model context')
        grid = batch['image_grid_thw'].detach().cpu().tolist()
        rows = [dict(form=form, prompt=prompt(form, name), image=_image_receipt(im), render=meta,
                     processor_grid=grid[i], processor_size=HFBackend.size(form),
                     prompt_tokens=batch['input_ids'][i][batch['attention_mask'][i].bool()].tolist())
                for i, (im, meta) in enumerate(zip(images, metadata))]
        if form == 'V3':
            # Native generation has no routed dispatcher and owns only its fresh cache.
            if getattr(model,'generation_config',None) is None:
                raise ValueError('V3_requires_checkpoint_generation_config')
            generated = model.generate(**batch, do_sample=False, max_new_tokens=MAX_NEW_TOKENS,
                                       use_cache=True, return_dict_in_generate=False)
            for row, sequence in zip(rows, generated[:, width:]):
                ids = sequence.tolist()
                eos = tokenizer.eos_token_id
                if eos in ids:
                    ids = ids[:ids.index(eos)+1]
                capped = len(ids) >= MAX_NEW_TOKENS and (not ids or ids[-1] != eos)
                raw = tokenizer.decode(ids, skip_special_tokens=True)
                boxes, valid = parse_boxes(raw)
                row.update(raw_tokens=ids, raw_output=raw, boxes=boxes if valid else [],
                           capped=capped,parse_status='boxes' if valid and boxes else 'null' if valid else 'invalid',
                           coordinate_scale=1000)
        else:
            kwargs = dict(use_cache=False, return_dict=True)
            if 'logits_to_keep' in inspect.signature(model.forward).parameters:
                kwargs['logits_to_keep'] = 1
            output = model(**batch, **kwargs)
            logits = output.logits
            if not torch.isfinite(logits[:, -1]).all():
                raise ValueError('Nonfinite verification logits')
            groups = token_groups(tokenizer, ['yes', 'no'] if form == 'V1' else list('012345'))
            values = read_logits(logits, batch['attention_mask'], groups)
            raw_ids = logits[:, -1].argmax(-1).tolist()
            for i, row in enumerate(rows):
                row.update(probabilities=values['probabilities'][i], vocabulary_mass=values['vocabulary_mass'][i],
                           token_groups=groups, raw_tokens=[raw_ids[i]],
                           raw_output=tokenizer.decode([raw_ids[i]], skip_special_tokens=True), parse_status='scored')
                if form == 'V1':
                    row.update(candidate_id=metadata[i][0]['candidate_id'], p_yes=values['probabilities'][i][0])
                else:
                    allowed_probs = values['probabilities'][i][:len(metadata[i])+1]
                    choice = max(range(len(allowed_probs)), key=allowed_probs.__getitem__)
                    row.update(choice=choice, candidate_ids=[m['candidate_id'] for m in metadata[i]])
        return rows
    finally:
        tokenizer.padding_side = padding_side
        # Results contain Python values only. No logits, image activations or new cache escape.
        encoded = batch = output = logits = generated = None


@torch.inference_mode()
def verify_pass(model, processor, request, *, budget=None, max_candidates=20):
    """One fresh batched call per form; V3 uses a native decode capped at the kit’s 128 tokens."""
    if _inside.get():
        raise RuntimeError('Recursive verification is disabled')
    if model.training:
        raise ValueError('Verify requires eval mode')
    forms, candidates, slots, count = _plan(request, max_candidates)
    budget = budget if budget is not None else Budget()
    if count == 0:
        return dict(status='empty', response=request['name'] + ': not seen', rows=[],
                    queries_used=budget.used, queries_requested=0, cpu_peak_rss_bytes=_cpu_peak())
    if not budget.reserve(count):
        return dict(status='budget_exceeded', response=request['name'] + ': not seen', rows=[],
                    queries_used=budget.used, queries_requested=count, cpu_peak_rss_bytes=_cpu_peak())
    token = _inside.set(True)
    materialized = None
    try:
        materialized = _materialize(request, forms, candidates, slots)
        rows = []
        for form in forms:
            images, metadata = materialized[form]
            if images:
                rows.extend(isolated(model, lambda: _forward_form(model, processor, request['name'], form, images, metadata)))
        return dict(status='ok' if rows else 'invalid_candidates', rows=rows,dropped=materialized['_dropped'], queries_used=budget.used, queries_requested=count,
                    cpu_peak_rss_bytes=_cpu_peak(), cpu_peak_scope='process high-water RSS',
                    max_new_tokens=MAX_NEW_TOKENS, recursive_tools=False)
    finally:
        materialized = None
        _inside.reset(token)


class Session:
    """Each decoded row owns its budget, receipts and name cache."""
    def __init__(self, model, processor, config):
        self.model,self.processor,self.config=model,processor,config
        self.budget=Budget(config.max_queries)
        self.native=None
        self.receipts={}
        self.queries=[]

    def ground(self,name,context):
        from .scene_state import normalize_name
        from .carrier_c1_decode import CallError
        from .ground_lifting import render_ground
        from .ground_replay import record_mask
        try:canonical=normalize_name(name)
        except ValueError as exc:raise CallError('bad_object') from exc
        context.verify_identity=self.config.identity
        backend=self.config.backend
        registry=context.registry
        if canonical in self.receipts:
            cached=self.receipts[canonical]
            result=deepcopy(cached['result']);result['name']=name
            text=render_ground(result,registry)
            owner=context.heads.mdg_backend
            if owner is not None:owner.results[name]=result
            q=deepcopy(cached['query']);q['name']=name;q['result']=result;self.queries.append(q)
            return text,dict(kind='ground',name=name,verify=deepcopy(cached['receipt']))
        registry_before=deepcopy(vars(registry))
        owner=context.heads.mdg_backend
        owner_before=deepcopy(owner.results) if owner is not None else None
        snapshots=[]
        for target in (owner,backend):
            if target is None:continue
            for field in ('claims','question_slots','queries','gap_queries','query_passes','pending_verify','rescue_attempted'):
                value=getattr(target,field,None)
                if isinstance(value,(dict,list,set)):snapshots.append((value,value.copy()))
            memory=getattr(target,'memory',None)
            if hasattr(memory,'slots'):snapshots.append((memory.slots,memory.slots.copy()))
        def rollback_backend():
            for value,before in snapshots:
                if isinstance(value,(dict,set)):value.clear();value.update(before)
                else:value[:]=before
        try:
            request=backend.verify_request(name,context)
            if request is None:
                # A verified clip-memory hit must keep backend ownership even
                # when an HRP fallback is configured for unhandled requests.
                entry=backend._memory_entry(canonical) if hasattr(backend,'_memory_entry') else None
                marker=entry.get('verified_by') if isinstance(entry,dict) else getattr(entry,'verified_by',None)
                if marker is not None and marker==context.verify_identity:
                    text=backend.ground(name,registry)
                    records=[q for q in backend.queries if q['name']==name]
                    if not records:raise ValueError('verified_memory_missing_replay')
                    self.queries.append(deepcopy(records[-1]))
                    return text,dict(kind='ground',name=name,verify_memory_hit=True)
                text=context.fallback(name)
                fallback_owner=context.rereader if context.rereader is not None else owner
                records=[q for q in getattr(fallback_owner,'queries',[]) if q['name']==name]
                if records:self.queries.append(deepcopy(records[-1]))
                return text,dict(kind='ground',name=name)
            attempts=[]
            for attempt in range(2):
                request=dict(request)
                if request.get('name',name)!=name:raise ValueError('Backend requested a different object name')
                request.update(name=name,context=request.get('context',context))
                if self.native is None:self.native=native_view(self.model)
                receipt=verify_pass(self.native,self.processor,request,budget=self.budget,max_candidates=self.config.max_candidates)
                if receipt['status']=='ok':
                    text=backend.accept_verify(name,receipt,context)
                    if not isinstance(text,str):raise TypeError('accept_verify must return ground response text')
                    if owner is None or name not in owner.results:
                        raise ValueError('accept_verify_must_register_lifted_result_for_gap')
                    result=deepcopy(owner.results[name])
                    records=[q for q in owner.queries if q['name']==name]
                    if not records or 'mask_bits' not in records[-1]:
                        raise ValueError('accept_verify_must_record_replay_masks')
                    q=deepcopy(records[-1])
                else:
                    result=dict(name=name,seen=False)
                    text=name+': not seen'
                    q=dict(name=name,**record_mask(None,None,.5,context.geometry))
                    if owner is not None:owner.results[name]=result
                attempts.append({k:v for k,v in receipt.items() if not k.startswith('cpu_peak')})
                retry=getattr(backend,'retry_verify',None)
                request=retry(name,receipt,context) if attempt==0 and retry is not None else None
                if request is None:break
            if len(attempts)>1:receipt=dict(receipt,attempts=attempts)
        except torch.cuda.OutOfMemoryError:
            vars(registry).clear();vars(registry).update(registry_before)
            rollback_backend()
            if owner is not None:owner.results.clear();owner.results.update(owner_before)
            raise
        except Exception as exc:
            vars(registry).clear();vars(registry).update(registry_before)
            rollback_backend()
            if owner is not None:owner.results.clear();owner.results.update(owner_before)
            receipt=dict(status='error',error_type=type(exc).__name__,error=str(exc),rows=[])
            result=dict(name=name,seen=False);text=name+': not seen'
            q=dict(name=name,**record_mask(None,None,.5,context.geometry))
        # Resource metrics belong in diagnostics, not deterministic decode records.
        receipt={k:v for k,v in receipt.items() if not k.startswith('cpu_peak')}
        q.update(backend='verify',receipt=receipt,result=result)
        self.queries.append(q)
        if receipt['status'] not in ('error','invalid_candidates'):
            self.receipts[canonical]=dict(result=result,receipt=receipt,query=q)
        info=dict(kind='ground',name=name,verify=receipt)
        if receipt['status'] in ('error','invalid_candidates') or receipt.get('dropped'):
            info['verify_error']=True
        return text,info
