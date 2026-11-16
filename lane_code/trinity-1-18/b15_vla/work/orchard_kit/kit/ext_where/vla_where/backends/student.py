"""The provider student's own presence and pointing (schema 6.3 steps 2-3, 6.5): the export's full_weights in
transformers Qwen3_5ForConditionalGeneration, single-image prompts, native generate, greedy. No carriers, tower or
routed decoder.

Presence (verify_kit V1, BRIEF_PRES32 item 1; pres32_run.py sha256 1622946b...): the prompt
  "Is the {phrase} visible in this image? Answer yes or no."
through the chat template (enable_thinking=False), processor size V3 = {shortest_edge 65536, longest_edge 602112};
P(yes) = the yes group's share of the yes and no groups' vocabulary mass at the first answer token. token_groups and
read_logits below are vendored from verify_kit/work/verifykit/model.py (sha256 56c6cee9...) unchanged in behaviour.

Pointing (student_pilot/hrp_reread.py read_image, the student's native single-image form):
  'Point to the {obj} in this image. Output the point as JSON {"point_2d": [x, y]} with integer coordinates on a
   0-1000 grid. If there is no {obj} in the image, output {"point_2d": null}.'
parsed by hrp_reread.parse_point; a capped or unparsable answer counts as null.
"""
import hashlib

import numpy as np

PRESENCE_PROMPT = 'Is the {phrase} visible in this image? Answer yes or no.'
POINT_PROMPT = ('Point to the {obj} in this image. Output the point as JSON {{"point_2d": [x, y]}} '
                'with integer coordinates on a 0-1000 grid. If there is no {obj} in the image, '
                'output {{"point_2d": null}}.')
SIZE = dict(shortest_edge=65536, longest_edge=602112)
VERIFY_KIT_MODEL_SHA256 = '56c6cee99b92fdac547772715706f7fb65abc6499d35898feff7776516f4552b'


def token_groups(tokenizer, labels):
    groups = []
    for label in labels:
        spellings = {label, label.capitalize(), label.upper()}
        variants = {prefix + s for s in spellings for prefix in ('', ' ')}
        ids = set()
        for s in sorted(variants):
            encoded = tokenizer.encode(s, add_special_tokens=False)
            if len(encoded) == 1 and tokenizer.decode(encoded).strip().casefold() == label.casefold():
                ids.add(encoded[0])
        if not ids:
            raise ValueError(f'No single-token form for {label!r}')
        groups.append(sorted(ids))
    if len(set(sum(groups, []))) != sum(map(len, groups)):
        raise ValueError('Answer token groups overlap')
    return groups


def yes_share(last_logits, groups):
    """P(yes) = softmax over the groups' log vocabulary mass (read_logits), for one 1-D logit vector."""
    x = np.asarray(last_logits, dtype=np.float64)
    norm = np.logaddexp.reduce(x)
    logmass = np.array([np.logaddexp.reduce(x[ids]) for ids in groups]) - norm
    p = np.exp(logmass - logmass.max())
    return float(p[0] / p.sum())


def parse_point(text):
    from student_pilot.hrp_reread import parse_point as tree_parse
    point, status = tree_parse(text)
    return (None if point is None else (float(point[0]), float(point[1]))), status


class StudentQueries:
    """Presence and Pointer on one frozen model. `last_logits(image, prompt)` and `generate(image, prompt)` are injected
    (qwen_calls builds them from the export on a GPU host); `groups` are the yes and no token groups."""

    def __init__(self, last_logits, generate, groups, *, weights_sha='unpinned'):
        self.last_logits, self.generate, self.groups, self.weights_sha = last_logits, generate, groups, weights_sha
        self.trace = []

    def p_yes(self, image, phrase, view=None):
        return yes_share(self.last_logits(image, PRESENCE_PROMPT.format(phrase=phrase)), self.groups)

    def point(self, image, phrase, view=None):
        raw = self.generate(image, POINT_PROMPT.format(obj=phrase))
        point, status = parse_point(raw)
        self.trace.append(dict(view=view, phrase=phrase, raw=raw, status=status))
        return point

    def pin(self):
        return self.weights_sha

    def sha(self):
        return hashlib.sha256(f'student|{self.weights_sha}|{PRESENCE_PROMPT}|{POINT_PROMPT}|{SIZE}|{self.groups}'
                              .encode()).hexdigest()


def qwen_calls(model, processor, *, max_new_tokens=48):
    """(last_logits, generate, groups) for a transformers Qwen3.5 model and its processor (GPU host)."""
    import torch
    from PIL import Image

    def batch(image, prompt):
        messages = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': prompt}]}]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                             enable_thinking=False)
        encoded = processor(text=[text], images=[Image.fromarray(np.asarray(image))], return_tensors='pt',
                            padding=True, size=SIZE)
        device = model.get_input_embeddings().weight.device
        return {k: v.to(device) for k, v in encoded.items()}

    @torch.inference_mode()
    def last_logits(image, prompt):
        return model(**batch(image, prompt), use_cache=False).logits[0, -1].float().cpu().numpy()

    @torch.inference_mode()
    def generate(image, prompt):
        inputs = batch(image, prompt)
        ids = model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)
        suffix = ids[0, inputs['input_ids'].shape[1]:].tolist()
        eos = processor.tokenizer.eos_token_id
        if len(suffix) >= max_new_tokens and suffix[-1] != eos:
            return ''
        return processor.tokenizer.decode(suffix, skip_special_tokens=True)

    return last_logits, generate, token_groups(processor.tokenizer, ['yes', 'no'])


def load_student(full_weights, device='cuda'):
    """The export's full_weights (HF key names) in Qwen3_5ForConditionalGeneration, bf16, eval; GPU host only."""
    import json
    from pathlib import Path

    import torch
    from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration
    path = Path(full_weights)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(path, torch_dtype=torch.bfloat16,
                                                            local_files_only=True).to(device).eval()
    model.requires_grad_(False)
    processor = AutoProcessor.from_pretrained(path, local_files_only=True)
    processor.tokenizer.padding_side = 'left'
    manifest = path / 'full_weights.json'
    sha = hashlib.sha256(manifest.read_bytes()).hexdigest() if manifest.exists() else 'unpinned'
    return model, processor, sha
