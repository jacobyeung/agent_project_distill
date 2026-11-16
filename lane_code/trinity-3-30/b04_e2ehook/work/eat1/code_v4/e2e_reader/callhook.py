"""In-forward call hook: one module on the model that closes calls and writes responses.

The decode loop asks the hook after every SAMPLED token whether a call has closed. Call
detection and parsing live only here. A closed call is answered by a server bound for the
current read (camera, ground/gap, room), each fed from tensors of the same generate():
frozen towers run inside the call on the read's own frames, the checkpoint's own gravity
head, the scale head, the selector head. The response ids are returned to the loop, which
forces them into the running KV cache. No prompt is rebuilt and the model is entered once.

Detection is a port of the sealed reader's Row._call (student_pilot.carrier_c1_batch_decode,
tree b01ce449) so a model emits the same calls under this hook as under the old reader.
"""
import re
from collections import Counter

import torch
from torch import nn

MAX_CALL_TOKENS = 1024  # call window; the sealed reader's 96 cut long multi-operand calls
CONTEXT_TOKENS = 32  # text before an opener, read only to see whether the call is quoted
CALCULATOR_TAIL = re.compile(r'<(?:dist|closest|cam_dist|angle|area) [^<>]*>$')
GROUND_TAIL = re.compile(r'<ground\b[^<>\n]*>$|<ground obj="[^"\n]*">$')
GAP_TAIL = re.compile(r'<gap\b[^<>\n]*>$')
EXTRA_TAIL = re.compile(r'<(?:ground|gap|surface_pair|extent_ends)\b[^<>\n]*>$')
ROOM_CALL = '<ground mode="room">'
OPEN, CLOSE = '<tool_response>', '</tool_response>'


def call_family(call):
    if call == ROOM_CALL:
        return 'room'
    for name in ('move', 'turn', 'pose', 'depth_at', 'ground', 'gap'):
        if call.startswith('<' + name):
            return name
    return 'other'


class Unserved(Exception):
    """The artifact has no head for this call; nothing is written, the model continues."""


class CallHook(nn.Module):
    """Registered on the model as `model.call_hook`. Holds no weights of its own; the heads it
    reads are submodules of the model (scale head, selector head) or frozen towers loaded from
    the artifact. Per-read state (the bound servers) is reset by begin()."""

    def __init__(self, tokenizer, opener_ids, *, ground_layout=True, error_suffix=False):
        super().__init__()
        self.tokenizer = tokenizer
        self.openers = frozenset(int(i) for i in opener_ids)
        self.ground_layout = bool(ground_layout)
        # The old reader appended "; answer directly from the video" to ground/gap errors.
        # That sentence is reader-written fallback text (EAT-1 A4), so it is off by default.
        self.error_suffix = bool(error_suffix)
        self.reserved = [tokenizer.convert_tokens_to_ids(OPEN), tokenizer.convert_tokens_to_ids(CLOSE)]
        self.servers = None
        self.reset_read()

    # ------------------------------------------------------------------ per read
    def reset_read(self):
        self.ids, self.active, self.records = [], None, []
        self.counts, self.unserved = Counter(), Counter()

    def begin(self, servers):
        """Bind the servers of one read. `servers` maps family -> callable(call)->(text, info)."""
        self.reset_read()
        self.servers = dict(servers)

    # ------------------------------------------------------------------ tokens
    def _decode(self, ids):
        return self.tokenizer.decode(ids, skip_special_tokens=False)

    def push_forced(self, token):
        self.ids.append(int(token))

    def push_eos(self, token):
        self.ids.append(int(token))

    def forward(self, token):
        """Handler entry for one sampled token: the response ids to force (empty when no call closed)."""
        return torch.tensor(self.push_sampled(int(token)), dtype=torch.long)

    def push_sampled(self, token):
        """Append one sampled non-EOS token; return the response ids to force (possibly empty)."""
        ids = self.ids
        ids.append(int(token))
        if token in self.openers:
            self.active = len(ids) - 1
        tail = self._decode(ids[self.active:] if self.active is not None else ids[-24:])
        call = None
        if self.active is not None and (tail.endswith('>') or len(ids) - self.active > MAX_CALL_TOKENS):
            before = self._decode(ids[max(0, self.active - CONTEXT_TOKENS):self.active])
            match = GROUND_TAIL.search(tail) or GAP_TAIL.search(tail)
            call = match.group(0) if match else tail
            if quoted(before + tail[:match.start() if match else 0]):
                call = None
            self.active = None
        elif self.active is None and tail.endswith('>'):
            call = self._search(GROUND_TAIL, GAP_TAIL, CALCULATOR_TAIL)
        if call is None and tail.endswith('>'):
            call = self._search(EXTRA_TAIL)
        if call is None:
            return []
        return self.respond(call)

    def _search(self, *patterns):
        window = self._decode(self.ids[-MAX_CALL_TOKENS:])
        for pattern in patterns:
            match = pattern.search(window)
            if match:
                return None if quoted(window[:match.start()]) else match.group(0)
        return None

    # ------------------------------------------------------------------ responses
    def respond(self, call):
        family = call_family(call)
        self.counts[family] += 1
        server = (self.servers or {}).get(family)
        try:
            if server is None:
                raise Unserved(family)
            text, info = server(call)
        except Unserved:
            self.unserved[family] += 1
            self.records.append(dict(call=call, family=family, served=False, at_token=len(self.ids)))
            return []
        if self.error_suffix:
            text = old_reader_suffix(text, info)
        wrapped = ('\n' + OPEN + '\n' + text + '\n' + CLOSE) if self.ground_layout else (OPEN + text + CLOSE)
        forced = self.tokenizer.encode(wrapped, add_special_tokens=False)
        self.records.append(dict(call=call, family=family, served=True, response=text,
                                 at_token=len(self.ids), forced_tokens=len(forced), **info))
        return forced

    def mask_reserved(self, logits):
        """The model may never sample the response delimiters."""
        logits = logits.clone()
        logits[..., self.reserved] = -float('inf')
        return logits

    def report(self):
        return dict(calls=dict(self.counts), unserved=dict(self.unserved),
                    records=[{k: v for k, v in r.items() if k != 'audit'} for r in self.records])


def quoted(before):
    """A call written inside a code span or right after a quote mark is an example, not a call."""
    line = before.rsplit('\n', 1)[-1]
    return line.count('`') % 2 == 1 or line.endswith(('"', "'"))


def old_reader_suffix(text, info):
    """Replay parity only (error_suffix=True): the old reader appended this to ground/gap errors."""
    return text + '; answer directly from the video' if info.get('kind') == 'error' else text


def install(model, hook):
    """Register the hook as a submodule of the model (the artifact's one entry point)."""
    if getattr(model, 'call_hook', None) is not None:
        raise ValueError('call_hook_already_installed')
    model.add_module('call_hook', hook) if isinstance(model, nn.Module) else setattr(model, 'call_hook', hook)
    return hook


@torch.no_grad()
def decode_loop(step, prefill_output, hook, *, eos_ids, cap, logits_processor=None):
    """One sequence, greedy. `step(token_ids)` consumes the given ids into the running cache
    (one forward per id, native positions) and returns the last output. The model is entered
    exactly once per prefill; responses go through the same cache. `cap` bounds sampled plus
    forced tokens; a response is never cut, and every sampled and forced id enters the cache
    before the loop stops."""
    output, finish = prefill_output, None
    eos_ids = set(int(e) for e in eos_ids)
    while finish is None:
        logits = hook.mask_reserved(output.logits[:, -1, :].float())
        if logits_processor is not None:
            logits = logits_processor(hook.ids, logits)
        token = int(logits.argmax(-1))
        if token in hook.reserved:
            raise ValueError('sampled_reserved_token')
        if token in eos_ids:
            hook.push_eos(token)
            finish = 'eos'
            break
        forced = hook(token).tolist()
        for t in forced:
            hook.push_forced(t)
        output = step([token] + list(forced))
        if len(hook.ids) >= cap:
            finish = 'max_new_tokens'
    return finish
