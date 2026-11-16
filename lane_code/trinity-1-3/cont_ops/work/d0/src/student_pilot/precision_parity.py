"""Measured same-run numerical floors; semantic identities stay exact."""
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path


def tensor_sha(value):
    import torch
    return hashlib.sha256(value.detach().contiguous().view(torch.uint8).cpu().numpy().tobytes()).hexdigest()


def token_sha(ids):
    return hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest()


def attention(model):
    config = model.config
    return {name: getattr(getattr(config, name, config), '_attn_implementation', None)
            for name in ('text_config', 'vision_config')}


@contextmanager
def capture_inputs(model, processor, images):
    """Hash the actual forward inputs, including each unpadded prompt and crop."""
    evidence = []
    def capture(module, args, batch):
        shapes = {k: list(v.shape) for k, v in batch.items() if hasattr(v, 'shape')}
        offset = 0
        for i, image in enumerate(images):
            ids = batch['input_ids'][i][batch['attention_mask'][i].bool()].tolist()
            grid = batch['image_grid_thw'][i]
            count = int(grid.prod())
            evidence.append(dict(crop_rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest(),
                prompt_tokens_sha256=token_sha(ids), prompt_tokens=len(ids),
                processed_pixels_sha256=tensor_sha(batch['pixel_values'][offset:offset+count]),
                image_grid_thw=grid.tolist(), batch_shape=shapes,
                padded_tokens_sha256=tensor_sha(batch['input_ids'][i]),
                padding_side=processor.tokenizer.padding_side,
                padding_tokens=int((batch['attention_mask'][i] == 0).sum()),
                attention_implementation=attention(module)))
            offset += count
        if offset != len(batch['pixel_values']):
            raise ValueError('Image grid does not cover the processed pixels')
    handle = model.register_forward_pre_hook(capture, with_kwargs=True)
    try:
        yield evidence
    finally:
        handle.remove()


def same_inputs(a, b):
    keys = ('crop_rgb_sha256', 'prompt_tokens_sha256', 'processed_pixels_sha256',
            'image_grid_thw', 'attention_implementation', 'padding_side')
    return all(a.get(k) == b.get(k) and k in a and k in b for k in keys)


def probability_parity(results, reference, actual, *, threshold=.5):
    """Pool max |reference B20 - reference grouped| over all crops, never candidate errors."""
    half = reference.get('parameter_dtype') in ('torch.bfloat16', 'torch.float16')
    base = .001 if half else 1e-6
    invalid = sum(not all(math.isfinite(r.get(k, math.nan)) and 0 <= r[k] <= 1
        for k in ('inside', 'reference', 'reference_grouped')) for r in results)
    valid = bool(results) and not invalid
    floor = max((abs(r['reference'] - r['reference_grouped']) for r in results), default=0.) if valid else 0.
    tolerance = max(base, 3*floor) if half else base
    strict = failed = decisions = invalid_inputs = 0
    rows = []
    for r in results:
        error = abs(r['inside'] - r['reference'])
        decision_diff = (r['inside'] >= threshold) != (r['reference'] >= threshold)
        margin = abs(r['reference'] - threshold)
        strict += not math.isfinite(error) or error > .001
        failed += not math.isfinite(error) or error > tolerance
        decisions += decision_diff and (not half or margin > 3*floor)
        inputs_ok = (same_inputs(r.get('reference_inputs', {}), r.get('inside_inputs', {}))
                     and same_inputs(r.get('reference_inputs', {}), r.get('grouped_inputs', {}))
                     and all(k in r.get('grouped_inputs', {}) and k in r.get('inside_inputs', {})
                             and r['grouped_inputs'][k] == r['inside_inputs'][k]
                             for k in ('batch_shape', 'padding_tokens', 'padded_tokens_sha256'))
                     and r.get('reference_token_groups') == r.get('inside_token_groups')
                     and bool(r.get('reference_token_groups')))
        invalid_inputs += not inputs_ok
        rows.append(dict(r, absolute_error=error, signed_difference=r['inside']-r['reference'],
            reference_shape_difference=abs(r['reference']-r.get('reference_grouped', r['reference'])),
            reference_yes=r['reference'] >= threshold, inside_yes=r['inside'] >= threshold,
            reference_grouped_yes=r.get('reference_grouped', math.nan) >= threshold,
            reference_margin=margin, decision_differs=decision_diff, inputs_equal=inputs_ok))
    same = reference == actual
    return dict(policy='pooled-reference-floor-r12', ok=valid and same and not (failed or decisions or invalid_inputs),
        count=len(rows), tolerance=tolerance, strict_tolerance=.001, floor=floor,
        floor_statistic='maximum absolute reference difference across all crops',
        threshold=threshold, threshold_operator='>=', strict_failures=strict,
        acceptance_failures=failed, decision_failures=decisions, input_failures=invalid_inputs,
        invalid_probabilities=invalid, same_card_and_precision=same,
        reference_provenance=reference, actual_provenance=actual, rows=rows)


def check_probabilities(out, results, reference, actual, *, threshold):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    numeric = probability_parity(results, reference, actual, threshold=threshold)
    (out/'crops.json').write_text(json.dumps(results, indent=2)+'\n')
    (out/'P_YES_PARITY.json').write_text(json.dumps(numeric, indent=2)+'\n')
    print(json.dumps(dict(p_yes_parity={k:v for k,v in numeric.items() if k!='rows'})), flush=True)
    if not numeric['ok']:
        raise AssertionError('Kit HFBackend P(yes) parity failed; inspect P_YES_PARITY.json')
    return numeric


def feature_parity(reference, repeat, actual):
    """Pool the reference packed/chunked floor over all taps, frames and elements."""
    import torch
    if not reference or set(reference) != set(repeat) or set(reference) != set(actual):
        return dict(passed=False, identity_equal=False, reason='tap identity differs')
    if any(reference[k].shape != repeat[k].shape or reference[k].shape != actual[k].shape for k in reference):
        return dict(passed=False, identity_equal=False, reason='feature shape differs')
    if any(reference[k].dtype != repeat[k].dtype or reference[k].dtype != actual[k].dtype
           or reference[k].device != repeat[k].device or reference[k].device != actual[k].device for k in reference):
        return dict(passed=False, identity_equal=False, reason='feature precision or device differs')
    if not all(torch.isfinite(v).all() for d in (reference, repeat, actual) for v in d.values()):
        return dict(passed=False, identity_equal=True, reason='nonfinite features')
    floor = max(float((reference[k].float()-repeat[k].float()).abs().max()) for k in reference)
    half = next(iter(reference.values())).dtype in (torch.bfloat16, torch.float16)
    tolerance = max(.001, 3*floor) if half else 1e-6
    rows = {}
    for k, expected in reference.items():
        error = (actual[k].float()-expected.float()).abs()
        rows[str(k)] = dict(shape=list(expected.shape), reference_sha256=tensor_sha(expected),
            repeat_sha256=tensor_sha(repeat[k]), actual_sha256=tensor_sha(actual[k]),
            floor=float((expected.float()-repeat[k].float()).abs().max()),
            max_abs=float(error.max()),
            strict_failures=int((error > .02+.02*expected.float().abs()).sum()),
            acceptance_failures=int((error > tolerance).sum()))
    strict = sum(r['strict_failures'] for r in rows.values())
    failed = sum(r['acceptance_failures'] for r in rows.values())
    return dict(policy='pooled-reference-floor-r12', passed=not failed, identity_equal=True,
        floor=floor, tolerance=tolerance, strict_tolerance=dict(rtol=.02, atol=.02),
        strict_failures=strict, acceptance_failures=failed, taps=rows)


def record_parity(reference, repeat, actual, *, half=True):
    """Bound numeric audit fields; keep tokens, calls, responses, answers and structure exact."""
    numeric, identities = [], []
    def walk(a, b, c, path):
        if type(a) is not type(b) or type(a) is not type(c):
            identities.append(path)
        elif isinstance(a, dict):
            if a.keys() != b.keys() or a.keys() != c.keys(): identities.append(path)
            else:
                for k in sorted(a): walk(a[k], b[k], c[k], path+'/'+str(k))
        elif isinstance(a, list):
            if len(a) != len(b) or len(a) != len(c): identities.append(path)
            else:
                for i, (x, y, z) in enumerate(zip(a, b, c)): walk(x, y, z, path+'/'+str(i))
        elif isinstance(a, float):
            numeric.append(dict(path=path, reference=a, repeat=b, actual=c))
        elif a != b or a != c:
            identities.append(path)
    walk(reference, repeat, actual, '')
    invalid = sum(not all(math.isfinite(r[k]) for k in ('reference','repeat','actual')) for r in numeric)
    floor = max((abs(r['reference']-r['repeat']) for r in numeric), default=0.) if not invalid else 0.
    tolerance = max(.001, 3*floor) if half else 1e-6
    failed = 0
    for r in numeric:
        r['absolute_error'] = abs(r['actual']-r['reference'])
        r['floor_difference'] = abs(r['repeat']-r['reference'])
        failed += not math.isfinite(r['absolute_error']) or r['absolute_error'] > tolerance
    strict = abs(len(reference)-len(actual))+sum(a != b for a,b in zip(reference,actual))
    return dict(policy='pooled-reference-floor-r12', ok=bool(reference) and not (identities or failed or invalid),
        rows=len(reference), records_equal=reference==actual, strict_failures=strict,
        strict_numeric_failures=sum(not math.isfinite(r['absolute_error']) or r['absolute_error'] > .001 for r in numeric),
        decision_failures=len(identities), decision_paths=identities,
        acceptance_failures=failed+len(identities)+invalid, invalid_values=invalid,
        floor=floor, tolerance=tolerance, numeric_fields=numeric)
