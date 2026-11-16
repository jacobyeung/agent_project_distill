"""Shared fixtures: the tiny Qwen3.5 asset, a scripted fake LM and its engine twin."""
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # the trainer tree (tests/headcall/ -> repo root)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
TINY = os.environ.get("HEADCALL_TINY", "/scratch/jjyeung/phase2_opus/in33/scratch/jjyeung/cursor_lanes/"
                                       "distill_pd_phase2_opus/assets/tiny_qwen35")
CACHE = os.environ.get("HEADCALL_TEST_CACHE", "/tmp/headcall_test_cache")

_TOKENIZER = []


def tokenizer():
    if not _TOKENIZER:
        from transformers import AutoTokenizer
        _TOKENIZER.append(AutoTokenizer.from_pretrained(TINY))
    return _TOKENIZER[0]


def ids(text):
    return tokenizer().encode(text, add_special_tokens=False)


def one(text):
    encoded = ids(text)
    assert len(encoded) == 1, text
    return encoded[0]


def eos_ids():
    return (one("<|im_end|>"), one("<|endoftext|>"))


class Script(object):
    """A deterministic policy over the generated history.

    segments(i) gives the model tokens of segment i; a segment ends where a </tool_response> lands in the history
    (inserted or self-written), so segment i follows the i-th response. Past its end a segment repeats `filler`."""

    def __init__(self, segments, filler=None):
        self.segments = segments if callable(segments) else (lambda i, s=segments: s[min(i, len(s) - 1)])
        self.filler = filler if filler is not None else one("a")
        self.close = one("</tool_response>")

    def __call__(self, history):
        index = history.count(self.close)
        last = max([i for i, t in enumerate(history) if t == self.close], default=-1)
        position = len(history) - last - 1
        segment = self.segments(index)
        return segment[position] if position < len(segment) else self.filler


class FakeCache(object):
    def __init__(self, tokens):
        self.tokens = list(tokens)

    def get_seq_length(self):
        return len(self.tokens)


class FakeLM(object):
    """Callable like an HF causal LM; asserts single-token steps at the right cache_position."""

    def __init__(self, policy, prompt_length, vocab=248320):
        import torch
        self.torch, self.policy, self.prompt_length, self.vocab = torch, policy, prompt_length, vocab
        self.steps = 0

    def __call__(self, input_ids=None, past_key_values=None, use_cache=True, cache_position=None, logits_to_keep=None,
                 output_hidden_states=False, **kwargs):
        torch = self.torch
        if past_key_values is None:
            cache = FakeCache(input_ids[0].tolist())
        else:
            cache = past_key_values
            assert input_ids.shape == (1, 1), "the loop must feed one token per step"
            assert int(cache_position[0]) == len(cache.tokens), "wrong cache_position"
            cache.tokens.append(int(input_ids[0, 0]))
            self.steps += 1
        nxt = self.policy(cache.tokens[self.prompt_length:])
        logits = torch.full((1, 1, self.vocab), -1e4)
        logits[0, 0, nxt] = 0.0
        return SimpleNamespace(logits=logits, past_key_values=cache, hidden_states=None)


def fake_engine(policy, prompt_length):
    def generate(history, max_tokens, stop_token_ids):
        new = []
        while len(new) < max_tokens:
            token = policy(list(history[prompt_length:]) + new)
            new.append(token)
            if token in stop_token_ids:
                break
        return new
    return generate


def tiny_model():
    import torch
    from transformers import AutoModelForImageTextToText
    torch.manual_seed(0)
    return AutoModelForImageTextToText.from_pretrained(TINY, dtype=torch.float32).eval()
