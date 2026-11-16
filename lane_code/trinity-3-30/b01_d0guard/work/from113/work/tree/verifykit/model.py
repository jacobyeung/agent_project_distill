"""First-token readers and an in-process HF model; no server or cache sharing."""
import inspect
import re
import numpy as np
import torch
from .io import module
from pathlib import Path


def token_groups(tokenizer, labels):
    groups = []
    for label in labels:
        spellings = {label, label.capitalize(), label.upper()}
        variants = {prefix+s for s in spellings for prefix in ('', ' ')}
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


def read_logits(logits, attention_mask, groups):
    """Return full-vocabulary mass and answer-normalized probabilities."""
    if logits.ndim != 3:
        raise ValueError('Expected batch x sequence x vocabulary logits')
    if logits.shape[1] == 1:
        last = logits[:, 0].float()
    else:
        if logits.shape[:2] != attention_mask.shape:
            raise ValueError('Logits and attention shape differ')
        positions = torch.arange(attention_mask.shape[1], device=attention_mask.device)
        last_index = torch.where(attention_mask.bool(), positions, -1).max(-1).values
        if (last_index < 0).any():
            raise ValueError('Empty prompt')
        last = logits[torch.arange(len(logits), device=logits.device), last_index].float()
    normalizer = torch.logsumexp(last, -1, keepdim=True)
    logmass = torch.stack([torch.logsumexp(last[:, ids], -1) for ids in groups], -1)-normalizer
    return dict(probabilities=logmass.softmax(-1).cpu().tolist(),
                vocabulary_mass=logmass.exp().cpu().tolist())


class StubTokenizer:
    words = ['<pad>', 'yes', 'Yes', 'YES', 'no', 'No', 'NO', '0', '1', '2', '3', '4', '5', '<other>']
    def encode(self, word, add_special_tokens=False):
        return [self.words.index(word.strip())] if word.strip() in self.words else [13, 13]
    def decode(self, ids): return ''.join(self.words[i] for i in ids)


class StubModel:
    """Deterministic pixel-only test model, with no candidate scores or labels."""
    def __call__(self, pixel_values, attention_mask, **kwargs):
        b = len(pixel_values)
        logits = torch.full((b, attention_mask.shape[1], 14), -3.)
        p = pixel_values.mean((1, 2, 3)).float()/255
        for i in range(b):
            logits[i, :, 1:4] = p[i]*2
            logits[i, :, 4:7] = (1-p[i])*2
            logits[i, :, 7:13] = torch.arange(6).float()*.1+p[i]
        return type('Output', (), {'logits': logits})()


class StubBackend:
    def __init__(self):
        self.tokenizer, self.model = StubTokenizer(), StubModel()
    def predict(self, requests, images):
        attention = torch.ones((len(images), 3), dtype=torch.long)
        pixels = torch.stack([torch.tensor(np.array(i.resize((32, 32))), dtype=torch.float32) for i in images])
        logits = self.model(pixel_values=pixels, attention_mask=attention, use_cache=False).logits
        if requests[0]['form'] == 'V3':
            return [dict(text='[]', boxes=[], parse_valid=True, stub=True) for _ in images]
        groups = token_groups(self.tokenizer, ['yes', 'no'] if requests[0]['form'] == 'V1' else list('012345'))
        result = read_logits(logits, attention, groups)
        return [dict(probabilities=p, vocabulary_mass=m, stub=True) for p, m in zip(result['probabilities'], result['vocabulary_mass'])]


def parse_boxes(text, coordinate_scale=1000):
    import json
    clean = text.strip()
    if clean.startswith('```'):
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', clean)
    try:
        boxes = json.loads(clean)
        if not isinstance(boxes, list): raise ValueError()
        for item in boxes:
            b = item['bbox_2d']
            if len(b) != 4 or not all(isinstance(x, (float, int)) and np.isfinite(x) for x in b): raise ValueError()
            if not 0 <= b[0] < b[2] <= coordinate_scale or not 0 <= b[1] < b[3] <= coordinate_scale: raise ValueError()
        return boxes, True
    except (ValueError, TypeError, KeyError):
        return [], False


class HFBackend:
    def __init__(self, checkpoint, device='cuda', max_new_tokens=128):
        from transformers import AutoProcessor, AutoModelForImageTextToText
        self.processor = AutoProcessor.from_pretrained(checkpoint, local_files_only=True)
        self.processor._student_pilot_student = 'qwen35'
        self.processor.tokenizer.padding_side = 'left'
        self.tokenizer = self.processor.tokenizer
        # Reject metadata-only or incomplete tokenizer snapshots before loading weights.
        token_groups(self.tokenizer, ['yes', 'no'])
        token_groups(self.tokenizer, list('012345'))
        self.model = AutoModelForImageTextToText.from_pretrained(checkpoint, local_files_only=True,
            torch_dtype=torch.bfloat16 if device.startswith('cuda') else torch.float32).to(device).eval()
        self.device, self.max_new_tokens = device, max_new_tokens
        self.pointing = module('_verify_evalx_pointing', Path(__file__).resolve().parents[1]/'vendor/evalx_pointing.py')
        self.parity_checked = set()
        self.parity = []
        self.last_only = 'logits_to_keep' in inspect.signature(self.model.forward).parameters

    @staticmethod
    def size(form):
        return dict(shortest_edge=65536, longest_edge={'V1':200704, 'V2':1204224, 'V3':602112}[form])

    def batch(self, requests, images):
        form = requests[0]['form']
        tasks = [dict(obj=r['name'], point_prompt=r['prompt']) for r in requests]
        texts = [self.pointing.image_prompt(self.processor, t) for t in tasks]
        size = self.size(form)
        batch = self.processor(text=texts, images=images, return_tensors='pt', padding=True, size=size)
        if form not in self.parity_checked:
            self.pointing.SIZE = size
            expected = self.pointing.image_batch(self.processor, tasks[0], np.asarray(images[0])[None])
            first = self.processor(text=[texts[0]], images=[images[0]], return_tensors='pt', padding=True, size=size)
            checks = {k: torch.equal(expected[k], first[k]) for k in ('input_ids', 'pixel_values', 'image_grid_thw')}
            batch_ids = batch['input_ids'][0][batch['attention_mask'][0].bool()]
            checks['batch_ids'] = torch.equal(batch_ids, expected['input_ids'][0])
            n_pixels = len(expected['pixel_values'])
            checks['batch_pixels'] = torch.equal(batch['pixel_values'][:n_pixels], expected['pixel_values'])
            checks['batch_grid'] = torch.equal(batch['image_grid_thw'][0], expected['image_grid_thw'][0])
            if not all(checks.values()): raise ValueError(f'evalx processor parity failed: {checks}')
            self.parity.append(dict(form=form, **checks)); self.parity_checked.add(form)
        return batch.to(self.device)

    @torch.inference_mode()
    def predict(self, requests, images):
        batch = self.batch(requests, images)
        if requests[0]['form'] == 'V3':
            output = self.model.generate(**batch, do_sample=False, max_new_tokens=self.max_new_tokens,
                                         use_cache=True)
            texts = self.processor.batch_decode(output[:, batch['input_ids'].shape[1]:], skip_special_tokens=True)
            result = []
            for text in texts:
                boxes, valid = parse_boxes(text)
                result.append(dict(text=text, boxes=boxes, parse_valid=valid, coordinate_scale=1000))
            return result
        labels = ['yes', 'no'] if requests[0]['form'] == 'V1' else list('012345')
        groups = token_groups(self.tokenizer, labels)
        kwargs = dict(use_cache=False)
        if self.last_only: kwargs['logits_to_keep'] = 1
        output = self.model(**batch, **kwargs)
        result = read_logits(output.logits, batch['attention_mask'], groups)
        return [dict(probabilities=p, vocabulary_mass=m, token_groups=groups)
                for p, m in zip(result['probabilities'], result['vocabulary_mass'])]
