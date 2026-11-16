"""Presence asked as a yes/no question to the frozen student, per view (AUROC 0.962 for base Qwen3.5-9B on dev objects;
T0 shifted it towards yes, so the threshold is refit on LIBERO renders before use).

p = softmax over the next-token logits of the yes and no answers after the question. The scorer is injected:
`next_logits(image, prompt) -> 1-D logits over the vocabulary` (qwen_next_logits builds it from an HF model and its
processor on a GPU host); `yes_ids` / `no_ids` list the token ids of every accepted spelling (e.g. "yes", "Yes").
"""
import hashlib

import numpy as np

QUESTION = 'Is there a {phrase} in this image? Answer yes or no.'


def yes_probability(logits, yes_ids, no_ids):
    logits = np.asarray(logits, dtype=np.float64)
    y = np.logaddexp.reduce(logits[list(yes_ids)])
    n = np.logaddexp.reduce(logits[list(no_ids)])
    return float(1.0 / (1.0 + np.exp(n - y)))


class YesNoPresence:
    def __init__(self, next_logits, yes_ids, no_ids, *, question=QUESTION, weights_sha='unpinned'):
        self.next_logits, self.yes_ids, self.no_ids = next_logits, tuple(yes_ids), tuple(no_ids)
        self.question, self.weights_sha = question, weights_sha
        self._memo = {}

    def presence(self, obs, view, phrase):
        image = obs.image(view)
        key = (hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest(), phrase)
        if key not in self._memo:
            logits = self.next_logits(image, self.question.format(phrase=phrase))
            self._memo = {key: yes_probability(logits, self.yes_ids, self.no_ids)} | (
                self._memo if len(self._memo) < 64 else {})
        return self._memo[key]

    def sha(self):
        return hashlib.sha256(f'yesno|{self.weights_sha}|{self.question}|{self.yes_ids}|{self.no_ids}'.encode()).hexdigest()


def qwen_next_logits(model, processor, device='cuda'):
    """Next-token logits after the chat-templated question with one image (GPU host; not exercised on CPU)."""
    import torch
    from PIL import Image

    @torch.no_grad()
    def call(image, prompt):
        messages = [dict(role='user', content=[dict(type='image'), dict(type='text', text=prompt)])]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                             enable_thinking=False)
        inputs = processor(text=[text], images=[Image.fromarray(np.asarray(image))], return_tensors='pt').to(device)
        return model(**inputs).logits[0, -1].float().cpu().numpy()
    return call


def answer_ids(tokenizer, words=('yes', 'Yes'), negatives=('no', 'No')):
    def ids(ws):
        out = []
        for w in ws:
            enc = tokenizer.encode(w, add_special_tokens=False)
            if len(enc) == 1:
                out.append(enc[0])
        if not out:
            raise ValueError('No single-token spelling for ' + ', '.join(ws))
        return out
    return ids(words), ids(negatives)
