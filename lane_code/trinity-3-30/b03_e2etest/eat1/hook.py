"""EAT-1 dynamic instruments: file-open audit (A1), model-entry and token-provenance monitor (A2),
executed-line scope for the static scanner (A3), and head/tower call counters (A5, A6).

Three file-open sources, merged:
  * a CPython audit hook ('open' events from io.open/os.open; 'import' events give module files);
  * /proc/self/maps differences around each item (catches mmap'd files such as safetensors);
  * optionally an strace log (`strace -f --seccomp-bpf -e trace=openat,open`), which also sees opens made
    by C, C++ and Rust code. The harness opens a marker path at each generate() start and end so the
    log can be cut to the item windows.
"""
import os
import re
import sys
import threading
import time
import traceback
from collections import deque
from pathlib import Path

EAT1_ROOT = str(Path(__file__).resolve().parent)
MARKER_DIR = '/eat1-marker-nonexistent'
SYSTEM_PREFIXES = ('/usr/', '/lib/', '/lib64/', '/etc/', '/proc/', '/sys/', '/dev/', '/run/', '/bin/', '/sbin/')
CODE_SUFFIXES = ('.py', '.pyc', '.so', '.pyd', '.pth', '.pyi')
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC


def is_harness(path):
    """EAT-1's own files; its toy readers count as reader code."""
    return path.startswith(EAT1_ROOT+'/') and not path.startswith(EAT1_ROOT+'/toy/')


def environment_prefixes():
    import site
    prefixes = {sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix}
    try:
        prefixes.update(site.getsitepackages())
    except Exception:
        pass
    return tuple(sorted(str(Path(p).resolve())+'/' for p in prefixes if p))


# ---------------------------------------------------------------- A1: file opens
class _OpenAudit:
    """Singleton: CPython audit hooks cannot be removed, so the hook is gated by `active`."""

    def __init__(self):
        self.active = False
        self.events = []
        self.lock = threading.Lock()
        self.busy = False
        self.env = environment_prefixes()
        sys.addaudithook(self._hook)

    def _hook(self, event, args):
        if not self.active:
            return
        if event == 'open':
            path, mode, flags = (list(args)+[None, None, None])[:3]
            if isinstance(path, int) or path is None:
                return
            if isinstance(path, bytes):
                path = os.fsdecode(path)
            write = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
                isinstance(flags, int) and bool(flags & WRITE_FLAGS))
            stack = None
            if not self.busy and not str(path).startswith(self.env+SYSTEM_PREFIXES) and not is_harness(str(path)):
                self.busy = True
                try:
                    stack = _reader_stack()
                finally:
                    self.busy = False
            with self.lock:
                self.events.append(('open', str(path), write, stack))
        elif event == 'import':
            filename = args[1] if len(args) > 1 else None
            if filename:
                with self.lock:
                    self.events.append(('import', str(filename), False, None))

    def take(self):
        with self.lock:
            out, self.events = self.events, []
        return out


_AUDIT = None


def open_audit():
    global _AUDIT
    if _AUDIT is None:
        _AUDIT = _OpenAudit()
    return _AUDIT


def mapped_files():
    out = set()
    try:
        with open('/proc/self/maps') as f:
            for line in f:
                parts = line.split(None, 5)
                if len(parts) == 6 and parts[5].startswith('/'):
                    out.add(parts[5].strip().removesuffix(' (deleted)'))
    except OSError:
        pass
    return out


def marker(kind, index):
    """Open a non-existent path so an strace log records the item window."""
    try:
        open(f'{MARKER_DIR}/{kind}-{index}', 'rb')
    except OSError:
        pass


STRACE_LINE = re.compile(r'^(?:\[pid\s+)?(\d+)\]?\s+(?:\d+:\d+:\d+(?:\.\d+)?\s+)?'
                         r'(open|openat)\((?:[^,]+,\s*)?"((?:[^"\\]|\\.)*)",\s*([A-Z_|]+)(?:,\s*\d+)?\)\s*=\s*(-?\d+)')


def parse_strace(path):
    """-> list of (window index or None, path, write) for successful opens inside item windows."""
    out, window = [], None
    for line in Path(path).read_text(errors='replace').splitlines():
        m = STRACE_LINE.search(line)
        if not m:
            continue
        p, flags, rc = m.group(3), m.group(4), int(m.group(5))
        if p.startswith(MARKER_DIR+'/'):
            kind, index = p.rsplit('/', 1)[1].split('-')
            window = int(index) if kind == 'start' else None
            continue
        if rc < 0 or window is None:
            continue
        write = any(f in flags for f in ('O_WRONLY', 'O_RDWR', 'O_CREAT', 'O_APPEND', 'O_TRUNC'))
        out.append((window, p, write))
    return out


def classify_files(records, artifact, input_roots=(), extra_code_roots=()):
    """records: iterable of (source, path, write). Returns dict of lists keyed by category.

    Categories: artifact (sha in manifest), environment (interpreter, site-packages, system),
    input (declared item inputs), self_written (written earlier in the same run), code (reader code
    outside the environment: listed by sha256, scanned under A3), outside_data (A1 failure).
    """
    from .artifact import sha256
    env = environment_prefixes()
    inputs = tuple(str(Path(p).resolve()) for p in input_roots)
    written, seen, stacks = set(), {}, {}
    for record in records:
        source, path, write = record[:3]
        stack = record[3] if len(record) > 3 else None
        try:
            real = str(Path(path).resolve())
        except (OSError, RuntimeError):
            real = path
        if write:
            written.add(real)
            continue
        if real not in seen:
            seen[real] = source
        if stack and real not in stacks:
            stacks[real] = stack
    out = {k: [] for k in ('artifact', 'environment', 'input', 'self_written', 'code', 'outside_data', 'eat1')}
    for real, source in sorted(seen.items()):
        if is_harness(real):
            out['eat1'].append(dict(path=real))
            continue
        if not os.path.isfile(real):
            continue
        if real in written:
            out['self_written'].append(dict(path=real))
            continue
        if real.startswith(env) or real.startswith(SYSTEM_PREFIXES):
            out['environment'].append(dict(path=real, source=source))
            continue
        if any(real == i or real.startswith(i.rstrip('/')+'/') for i in inputs):
            out['input'].append(dict(path=real))
            continue
        digest = sha256(real)
        if artifact is not None and artifact.contains_sha(digest):
            out['artifact'].append(dict(path=real, sha256=digest))
        elif real.endswith(CODE_SUFFIXES):
            out['code'].append(dict(path=real, sha256=digest, source=source))
        else:
            out['outside_data'].append(dict(path=real, sha256=digest, source=source, opened_at=stacks.get(real)))
    return out


# ---------------------------------------------------------------- A2/A5/A6: model monitor
def _ids(value):
    import torch
    if value is None:
        return None
    if isinstance(value, torch.Tensor):
        if value.dim() == 2:
            if value.shape[0] != 1:
                raise ValueError('EAT-1 monitors batch size 1 only')
            value = value[0]
        return [int(v) for v in value.reshape(-1).tolist()]
    return [int(v) for v in value]


def _past_length(cache):
    if cache is None:
        return 0
    for name in ('get_seq_length', 'seq_length'):
        f = getattr(cache, name, None)
        if callable(f):
            return int(f())
    if isinstance(cache, (tuple, list)) and cache and isinstance(cache[0], (tuple, list)):
        return int(cache[0][0].shape[-2])
    raise ValueError('cannot read the key-value cache length')


def _logits(output):
    if hasattr(output, 'logits'):
        return output.logits
    if isinstance(output, dict):
        return output['logits']
    if isinstance(output, (tuple, list)):
        return output[0]
    return output


def _reader_stack(limit=6):
    """Innermost reader frames, without reading source files (no opens inside the audit hook)."""
    frames = []
    summary = traceback.StackSummary.extract(traceback.walk_stack(None), lookup_lines=False)
    for fs in summary:
        f = fs.filename
        if is_harness(f) or '/site-packages/' in f or f.startswith(sys.base_prefix) or f.startswith('<'):
            continue
        frames.append(f'{f}:{fs.lineno} {fs.name}')
        if len(frames) >= limit:
            break
    return frames


class ModelMonitor:
    """Hooks the LM entry module, the declared heads/towers and the call handlers of one model.

    Events are recorded in one ordered list per item:
      ('forward', input_ids, past_length, argmax_per_position, stack)
      ('handler', name, emitted token ids)
      ('module', role, name, seconds)
    """

    def __init__(self, model, lm, declared, line_scope=None):
        self.model, self.lm, self.declared = model, lm, declared
        self.line_scope = line_scope
        self.events, self.handles, self.depth = [], [], 0
        self.recording = False
        self._t0 = {}
        # lm is one module (ids in, logits out) or a pair (entry module taking ids, module returning logits),
        # for readers whose language model and output projection are separate registered modules.
        entry, head = lm if isinstance(lm, tuple) else (lm, lm)
        if not all(hasattr(m, 'register_forward_pre_hook') for m in (entry, head)):
            raise ValueError('the LM entry must be a torch module')
        self.split = entry is not head
        self.handles.append(entry.register_forward_pre_hook(self._lm_pre, with_kwargs=True))
        if self.split:
            self.handles.append(entry.register_forward_hook(self._entry_post, with_kwargs=True))
            self.handles.append(head.register_forward_hook(self._head_post, with_kwargs=True))
        else:
            self.handles.append(entry.register_forward_hook(self._lm_post, with_kwargs=True))
        for path, mod, role, name in declared:
            if mod is entry or mod is head:
                continue
            if role == 'call_handler':
                self.handles.append(mod.register_forward_hook(self._make_handler_hook(name)))
            else:
                self.handles.append(mod.register_forward_pre_hook(self._make_pre(role, name)))
                self.handles.append(mod.register_forward_hook(self._make_post(role, name)))

    def close(self):
        for h in self.handles:
            h.remove()

    # scope flag: lines executed inside model forwards are model code, not call-path code
    def _enter(self):
        self.depth += 1
        if self.line_scope is not None:
            self.line_scope.inside_model = self.depth > 0

    def _leave(self):
        self.depth = max(0, self.depth-1)
        if self.line_scope is not None:
            self.line_scope.inside_model = self.depth > 0

    def _lm_pre(self, module, args, kwargs):
        self._enter()
        if not self.recording:
            return
        if self.split and getattr(self, '_pending', None) is not None:
            self.events.append(('forward', self._pending, None))  # an entry forward that produced no logits
        ids = kwargs.get('input_ids', args[0] if args else None)
        self._pending = dict(ids=_ids(ids), past=_past_length(kwargs.get('past_key_values')),
                             stack=_reader_stack(), embeds=ids is None and kwargs.get('inputs_embeds') is not None)

    def _lm_post(self, module, args, kwargs, output):
        self._leave()
        if not self.recording:
            return
        self._lm_post_body(output)

    def _lm_post_body(self, output):
        pending = getattr(self, '_pending', None)
        self._pending = None
        if pending is None:
            return
        logits = _logits(output)
        argmax = [int(v) for v in logits[0].argmax(-1).reshape(-1).tolist()]
        self.events.append(('forward', pending, argmax))

    def _entry_post(self, module, args, kwargs, output):
        self._leave()

    def _head_post(self, module, args, kwargs, output):
        if self.recording and getattr(self, '_pending', None) is not None:
            self._lm_post_body(output)

    def _make_pre(self, role, name):
        def pre(module, args):
            self._enter()
            self._t0[id(module)] = time.perf_counter()
        return pre

    def _make_post(self, role, name):
        def post(module, args, output):
            self._leave()
            if self.recording:
                self.events.append(('module', role, name, time.perf_counter()-self._t0.pop(id(module), time.perf_counter())))
        return post

    def _make_handler_hook(self, name):
        def post(module, args, output):
            if self.recording:
                self.events.append(('handler', name, _ids(output)))
        return post

    def begin(self):
        self.events = []
        self.recording = True

    def end(self):
        if self.split and getattr(self, '_pending', None) is not None:
            self.events.append(('forward', self._pending, None))
            self._pending = None
        self.recording = False
        events, self.events = self.events, []
        return events


def provenance(events):
    """Classify every token fed to the LM: prompt, model (argmax of the previous position), handler
    (emitted by a call-handler module registered on the model) or injected (anything else)."""
    entries, fed_total, prev_argmax, prev_consumed = 0, 0, None, True
    pending = deque()
    tokens, violations, module_runs = [], [], {}
    stream, frozen = [], None
    for event in events:
        if event[0] == 'handler':
            pending.extend(event[2] or [])
            continue
        if event[0] == 'module':
            module_runs.setdefault((event[1], event[2]), []).append(event[3])
            continue
        info, argmax = event[1], event[2]
        ids, past = info['ids'], info['past']
        if argmax is None:  # split entry run without the logits module: counts as an entry only when it restarts
            if past == 0 and ids is not None:
                entries += 1
                if entries > 1:
                    violations.append(dict(kind='second_model_entry_without_logits', at_token=fed_total,
                                           stack=info['stack']))
            continue
        if ids is None:
            violations.append(dict(kind='inputs_embeds_without_ids', stack=info['stack']))
            continue
        if past == 0:
            entries += 1
            if entries > 1:
                violations.append(dict(kind='second_model_entry', at_token=fed_total, stack=info['stack']))
            fed_total = len(ids)
            tokens.extend(('prompt', t) for t in ids)
            if entries > 1:
                frozen = stream if frozen is None else frozen
            stream = []
        else:
            if past != fed_total:
                violations.append(dict(kind='cache_discontinuity', expected=fed_total, got=past, stack=info['stack']))
            for i, tok in enumerate(ids):
                expected = prev_argmax if i == 0 else argmax[i-1]
                if pending and tok == pending[0]:
                    pending.popleft()
                    src = 'handler'
                elif tok == expected and (i > 0 or not prev_consumed):
                    src = 'model'
                    if i == 0:
                        prev_consumed = True
                else:
                    src = 'injected'
                    violations.append(dict(kind='injected_token', token=tok, expected=expected,
                                           position=past+i, stack=info['stack']))
                tokens.append((src, tok))
                stream.append(tok)
            fed_total = past+len(ids)
        prev_argmax, prev_consumed = argmax[-1], False
    if pending:
        violations.append(dict(kind='handler_tokens_not_fed', count=len(pending)))
    final = prev_argmax if not prev_consumed else None
    generated = frozen if frozen is not None else stream+([final] if final is not None else [])
    return dict(entries=entries, tokens=tokens, generated=generated,
                violations=violations, module_runs={f'{r}:{n}': len(v) for (r, n), v in module_runs.items()},
                module_seconds={f'{r}:{n}': sum(v) for (r, n), v in module_runs.items()})


# ---------------------------------------------------------------- A3: executed-line scope
class LineScope:
    """Records (file, line) executed during generate() outside the forwards of model modules
    (lm, vit, head, connector, tower). Call-handler code is recorded. Interpreter, site-packages and
    EAT-1 lines are disabled after their first event."""
    TOOL = 4

    def __init__(self):
        self.lines = {}
        self.inside_model = False
        self.active = False
        self.env = environment_prefixes()
        self.mon = sys.monitoring

    def _line(self, code, line):
        f = code.co_filename
        if (f.startswith(self.env) or is_harness(f) or f.startswith('<')
                or f.startswith(SYSTEM_PREFIXES)):
            return self.mon.DISABLE
        if not self.active or self.inside_model:
            return None
        self.lines.setdefault(f, set()).add(line)
        return self.mon.DISABLE

    def start(self):
        try:
            self.mon.use_tool_id(self.TOOL, 'eat1')
        except ValueError:
            pass
        self.mon.register_callback(self.TOOL, self.mon.events.LINE, self._line)
        self.mon.set_events(self.TOOL, self.mon.events.LINE)
        self.active = True

    def pause(self):
        self.active = False

    def resume(self):
        self.active = True

    def stop(self):
        self.active = False
        self.mon.set_events(self.TOOL, 0)
        self.mon.register_callback(self.TOOL, self.mon.events.LINE, None)
        self.mon.restart_events()
        try:
            self.mon.free_tool_id(self.TOOL)
        except ValueError:
            pass
        return {f: sorted(v) for f, v in self.lines.items()}
