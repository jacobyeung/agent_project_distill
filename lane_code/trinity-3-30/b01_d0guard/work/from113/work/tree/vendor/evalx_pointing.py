"""Toolprog single-image contract; ground truth stays on Trinity."""
import re


def parse_points(text):
    # Keep toolprog's coordinate filter, including its degenerate-origin rejection.
    if text is None:
        return []
    pattern = r'"point_2d"\s*:\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]'
    points = [[float(m[1]), float(m[2])] for m in re.finditer(pattern, text)]
    return [p for p in points if 0 <= p[0] <= 1000 and 0 <= p[1] <= 1000 and max(p) > 10]


def parsed(text):
    points = parse_points(text)
    null = bool(re.search(r'"point_2d"\s*:\s*null\b', text or '', re.I)) and not points
    return dict(points=points, none=not points, parse_failed=not points and not null)


SIZE = None
PROMPT = None


def messages(task):
    return [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': PROMPT.replace('{obj}', task['obj']) if PROMPT else task['point_prompt']}]}]


def image_prompt(processor, task):
    return processor.apply_chat_template(messages(task), tokenize=False, add_generation_prompt=True,
                                         enable_thinking=False)


def image_batch(processor, task, arrays):
    from PIL import Image
    # infer() in the pinned kit passes no size override for single images.
    extra = dict(size=SIZE) if SIZE else {}
    return processor(text=[image_prompt(processor, task)], images=[Image.fromarray(arrays[0])],
                     return_tensors='pt', padding=True, **extra)


def compare_image(processor, engine, task, arrays, observed_ids, pixels):
    import torch
    from parity import processor_evidence
    expected = image_batch(processor, task, arrays)
    ids = expected['input_ids'][0].tolist()
    result = dict(example_id=task['example_id'], benchmark='pointing', prompt_equal=list(observed_ids)==ids,
                  expected_tokens=len(ids), observed_tokens=len(observed_ids))
    if pixels:
        hf, evidence = processor_evidence(engine, dict(size=SIZE) if SIZE else {})
        actual = image_batch(hf if hf is not None else processor, task, arrays)
        evidence.update(same_processor_class=hf is not None and type(hf) is type(processor),
                        pixels_equal=torch.equal(expected['pixel_values'], actual['pixel_values']),
                        grid_equal=torch.equal(expected['image_grid_thw'], actual['image_grid_thw']))
        evidence['pass'] = all(evidence[k] for k in ('vllm_processor_class_verified', 'same_processor_class',
                                                    'pixels_equal', 'grid_equal'))
        result['pixels'] = evidence
    return result
