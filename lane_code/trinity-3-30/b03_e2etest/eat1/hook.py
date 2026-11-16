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
import inspect
import sys
import threading
import time
import traceback
from collections import deque
from pathlib import Path

EAT1_ROOT = str(Path(__file__).resolve().parent)
MARKER_DIR = '/eat1-marker-nonexistent'
RUN_NONCE = os.urandom(6).hex()  # strace windows carry it, so a log proves it belongs to this run
SYSTEM_PREFIXES = ('/usr/', '/lib/', '/lib64/', '/etc/', '/proc/', '/sys/', '/dev/', '/run/', '/bin/', '/sbin/')
CODE_SUFFIXES = ('.py', '.pyc', '.so', '.pyd', '.pth', '.pyi')
CHILD_EVENTS = ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.spawn', 'os.fork', 'os.forkpty',
                'pty.spawn')
NATIVE_EVENTS = ('ctypes.call_function', 'ctypes.dlsym', 'ctypes.dlopen', 'ctypes.dlsym/handle', 'ctypes.cdata')


def open_kind(mode, flags):
    """-> (reads, writes). O_RDWR and '+' modes read: their file is judged (A1)."""
    if isinstance(mode, str):
        return ('r' in mode or '+' in mode), any(c in mode for c in 'wax+')
    if isinstance(flags, int):
        acc = flags & os.O_ACCMODE
        return acc in (os.O_RDONLY, os.O_RDWR), acc in (os.O_WRONLY, os.O_RDWR) or bool(
            flags & (os.O_CREAT | os.O_APPEND | os.O_TRUNC))
    return True, False


def fd_path(fd):
    try:
        return os.readlink(f'/proc/self/fd/{fd}')
    except OSError:
        return None


def fd_positions():
    """{fd: (path, pos)} for open regular files; a moved position between two snapshots means the reader read or
    wrote a descriptor opened before generate() (A1: such reads raise no open event)."""
    out = {}
    try:
        fds = os.listdir('/proc/self/fd')
    except OSError:
        return out
    for name in fds:
        path = fd_path(name)
        if not path or not path.startswith('/') or path.startswith(('/proc/', '/dev/')):
            continue
        try:
            with open(f'/proc/self/fdinfo/{name}') as f:
                info = dict(line.split(':', 1) for line in f.read().splitlines() if ':' in line)
            pos, flags = int(info['pos']), int(info['flags'], 8)
        except (OSError, ValueError, KeyError):
            continue
        if flags & os.O_ACCMODE == os.O_WRONLY:  # a log the process writes moves its position without a read
            continue
        out[int(name)] = (path, pos)
    return out


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
            reads, writes = open_kind(mode, flags)
            stack = None
            if not self.busy and not str(path).startswith(self.env+SYSTEM_PREFIXES) and not is_harness(str(path)):
                self.busy = True
                try:
                    stack = _reader_stack()
                finally:
                    self.busy = False
            with self.lock:
                if writes and not reads:
                    self.events.append(('open', str(path), True, stack))
                else:
                    self.events.append(('open', str(path), False, stack))
        elif event == 'mmap.__new__':
            fileno = args[0] if args else -1
            path = fd_path(fileno) if isinstance(fileno, int) and fileno >= 0 else None
            if path and path.startswith('/'):
                with self.lock:
                    self.events.append(('open', path, False, self._stack()))
        elif event.startswith(CHILD_EVENTS):
            with self.lock:
                self.events.append(('child', event, False, self._stack()))
        elif event.startswith(NATIVE_EVENTS):
            stack = self._stack(innermost=True)
            with self.lock:
                self.events.append(('native', event, False, stack))
        elif event == 'import':
            filename = args[1] if len(args) > 1 else None
            if filename:
                with self.lock:
                    self.events.append(('import', str(filename), False, None))

    def _stack(self, innermost=False):
        if self.busy:
            return None
        self.busy = True
        try:
            return _innermost_frame() if innermost else _reader_stack()
        finally:
            self.busy = False

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
        open(f'{MARKER_DIR}/{RUN_NONCE}-{kind}-{index}', 'rb')
    except OSError:
        pass


STRACE_LINE = re.compile(r'^(?:\[pid\s+)?(\d+)\]?\s+(?:\d+:\d+:\d+(?:\.\d+)?\s+)?'
                         r'(open|openat)\((?:[^,]+,\s*)?"((?:[^"\\]|\\.)*)",\s*([A-Z_|]+)(?:,\s*\d+)?\)\s*=\s*(-?\d+)')


def parse_strace(path, nonce=None, windows=None):
    """-> list of (window index or None, path, write) for successful opens inside item windows. With `windows`
    (a list), the indices of item windows whose start and end markers carry `nonce` are appended to it."""
    out, window = [], None
    for line in Path(path).read_text(errors='replace').splitlines():
        m = STRACE_LINE.search(line)
        if not m:
            continue
        p, flags, rc = m.group(3), m.group(4), int(m.group(5))
        if p.startswith(MARKER_DIR+'/'):
            parts = p.rsplit('/', 1)[1].split('-')
            tag, kind, index = parts if len(parts) == 3 else (None, *parts)
            if nonce is not None and tag != nonce:
                window = None
                continue
            if kind == 'end' and windows is not None and window == int(index):
                windows.append(window)
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


def _innermost_frame():
    """[innermost non-harness frame 'file:line name', 'reader' or 'library']."""
    env = environment_prefixes()
    for fs in traceback.StackSummary.extract(traceback.walk_stack(None), lookup_lines=False):
        f = fs.filename
        if is_harness(f) or f.startswith('<frozen') or f == __file__ or '/ctypes/' in f:
            continue
        lib = f.startswith(env) or f.startswith(sys.base_prefix) or f.startswith('<') or '/site-packages/' in f
        return [f'{f}:{fs.lineno} {fs.name}', 'library' if lib else 'reader']
    return None


def _fingerprint(obj, depth=0):
    """Content fingerprint of a key-value cache: tensors by shape and three sums, int lists exactly."""
    import torch
    if isinstance(obj, torch.Tensor):
        if not obj.numel():
            return ('t', tuple(obj.shape))
        t = obj.detach().double().flatten()
        pos = torch.arange(1, t.numel()+1, device=t.device, dtype=torch.float64)
        sums = torch.stack([t.sum(), t.abs().sum(), (t*t).sum(), (t*pos).sum(), (t*pos.sqrt()).sum()]).tolist()
        return ('t', tuple(obj.shape), tuple(sums))
    if isinstance(obj, (list, tuple)):
        if all(isinstance(v, int) for v in obj):
            return ('ints', tuple(obj))
        return tuple(_fingerprint(v, depth+1) for v in obj) if depth < 4 else ('seq', len(obj))
    if isinstance(obj, dict):
        return tuple((k, _fingerprint(v, depth+1)) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0])))
    if depth < 4 and hasattr(obj, '__dict__'):
        return (type(obj).__name__,)+tuple((k, _fingerprint(v, depth+1)) for k, v in sorted(vars(obj).items())
                                           if not callable(v))
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    return type(obj).__name__


VALUE_ROLES = ('head', 'tower', 'connector', 'fixed_math')


def _tensors(output, depth=0):
    """Detached copies of the tensors a head, tower or fixed-math module returned (response value provenance)."""
    import torch
    if isinstance(output, torch.Tensor):
        return [output.detach().clone()]
    if isinstance(output, (int, float)) and not isinstance(output, bool):
        return [torch.tensor([output], dtype=torch.float64 if isinstance(output, float) else torch.int64)]
    if depth < 3 and isinstance(output, (list, tuple)):
        return [t for o in output for t in _tensors(o, depth+1)]
    if depth < 3 and isinstance(output, dict):
        return [t for o in output.values() for t in _tensors(o, depth+1)]
    return []


def _output_cache(output, kwargs):
    cache = kwargs.get('past_key_values')
    if cache is None:
        cache = getattr(output, 'past_key_values', None) if not isinstance(output, dict) else output.get(
            'past_key_values')
    return cache


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
        self._inputs = {}
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
                self.handles.append(mod.register_forward_pre_hook(self._handler_pre))
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
            self.line_scope.depth = self.depth

    def _leave(self):
        self.depth = max(0, self.depth-1)
        if self.line_scope is not None:
            self.line_scope.inside_model = self.depth > 0
            self.line_scope.depth = self.depth

    def _lm_pre(self, module, args, kwargs):
        self._enter()
        if not self.recording:
            return
        if self.split and getattr(self, '_pending', None) is not None:
            self.events.append(('forward', self._pending, None))  # an entry forward that produced no logits
        ids = kwargs.get('input_ids', args[0] if args else None)
        cache = kwargs.get('past_key_values')
        past = _past_length(cache)
        modified = None
        if past and getattr(self, '_after', None) is not None and _fingerprint(cache) != self._after:
            modified = True
        self._pending = dict(ids=_ids(ids), past=past, stack=_reader_stack(), cache_modified=modified,
                             embeds=ids is None and kwargs.get('inputs_embeds') is not None)

    def _lm_post(self, module, args, kwargs, output):
        self._leave()
        if not self.recording:
            return
        self._snapshot(output, kwargs)
        self._lm_post_body(output)

    def _snapshot(self, output, kwargs):
        cache = _output_cache(output, kwargs)
        self._after = None if cache is None else _fingerprint(cache)

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
        if self.recording:
            self._snapshot(output, kwargs)

    def _head_post(self, module, args, kwargs, output):
        if self.recording and getattr(self, '_pending', None) is not None:
            self._lm_post_body(output)

    def _make_pre(self, role, name):
        def pre(module, args):
            self._enter()
            self._t0[id(module)] = time.perf_counter()
            if role == 'fixed_math' and self.recording:
                self._inputs[id(module)] = _tensors(args)
        return pre

    def _make_post(self, role, name):
        def post(module, args, output):
            self._leave()
            if self.recording:
                self.events.append(('module', role, name, time.perf_counter()-self._t0.pop(id(module), time.perf_counter())))
                if role in VALUE_ROLES:
                    self.events.append(('values', role, name, _tensors(output), self._inputs.pop(id(module), None)))
        return post

    def _handler_pre(self, module, args):
        if self.line_scope is not None:
            self.line_scope.in_handler += 1
            self.line_scope.handler_base.append(self.depth)

    def _make_handler_hook(self, name):
        def post(module, args, output):
            if self.line_scope is not None:
                self.line_scope.in_handler = max(0, self.line_scope.in_handler-1)
                if self.line_scope.handler_base:
                    self.line_scope.handler_base.pop()
            if self.recording:
                self.events.append(('handler', name, _ids(output)))
        return post

    def begin(self):
        self.events = []
        self._after = None
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
    stream, stream_src, frozen, frozen_src = [], [], None, None
    responses = [list(e[2]) for e in events if e[0] == 'handler' and e[2]]
    for event in events:
        if event[0] == 'handler':
            pending.extend(event[2] or [])
            continue
        if event[0] == 'module':
            module_runs.setdefault((event[1], event[2]), []).append(event[3])
            continue
        if event[0] == 'values':
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
        if info.get('cache_modified'):
            violations.append(dict(kind='cache_modified_between_model_entries', at_token=fed_total,
                                   stack=info['stack']))
        if past == 0:
            entries += 1
            if entries > 1:
                violations.append(dict(kind='second_model_entry', at_token=fed_total, stack=info['stack']))
            fed_total = len(ids)
            tokens.extend(('prompt', t) for t in ids)
            if entries > 1 and frozen is None:
                frozen, frozen_src = stream, stream_src
            stream, stream_src = [], []
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
                stream_src.append(src)
            fed_total = past+len(ids)
        prev_argmax, prev_consumed = argmax[-1], False
    if pending:
        violations.append(dict(kind='handler_tokens_not_fed', count=len(pending)))
    final = prev_argmax if not prev_consumed else None
    generated = frozen if frozen is not None else stream+([final] if final is not None else [])
    gsrc = frozen_src if frozen is not None else stream_src+(['model'] if final is not None else [])
    last = max([i for i, s in enumerate(gsrc) if s == 'handler'], default=-1)
    return dict(entries=entries, tokens=tokens, generated=generated, tail=generated[last+1:],
                handler_responses=responses,
                violations=violations, module_runs={f'{r}:{n}': len(v) for (r, n), v in module_runs.items()},
                module_seconds={f'{r}:{n}': sum(v) for (r, n), v in module_runs.items()})


# ---------------------------------------------------------------- A3: executed-line scope
def numeric_data(value, allowed, depth=0, tensors=True):
    """Why a module-level or object-state value is numeric data outside the weights, or None. For object state,
    `tensors` is the set of ids of tensors that existed before the item started (per-item head outputs are new)."""
    import torch
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return None if float(value) in allowed else f'number {value!r}'
    if isinstance(value, (torch.nn.Parameter, torch.nn.Module, type)) or callable(value):
        return None
    if isinstance(value, torch.Tensor):
        return f'tensor {tuple(value.shape)}' if tensors is True or (tensors and id(value) in tensors) else None
    if type(value).__module__ == 'numpy' and hasattr(value, 'shape'):
        return f'array {tuple(value.shape)}'
    if depth < 3 and isinstance(value, (list, tuple, set, frozenset, dict)):
        items = list(value.values()) if isinstance(value, dict) else list(value)
        for v in items[:2000]:
            why = numeric_data(v, allowed, depth+1, tensors)
            if why:
                return f'table holding numbers ({why})' if depth == 0 else why
    state = _object_state(value) if depth < 3 else None
    if state:
        return numeric_data(state, allowed, depth+1, tensors)
    return None


_ENV = None


def _object_state(value):
    """The attribute dict of a plain object held in reader state (a namespace, a dataclass, or any instance of a
    class defined in reader code): a fitted policy nested in such an object is data outside the weights too.
    Tokenizers (objects with encode and decode) are vocabularies, not policies."""
    global _ENV
    import dataclasses
    cls = type(value)
    if callable(getattr(value, 'encode', None)) and callable(getattr(value, 'decode', None)):
        return None
    if cls.__module__ in ('types', 'argparse') or dataclasses.is_dataclass(value):
        pass
    else:
        mod = sys.modules.get(cls.__module__)
        f = getattr(mod, '__file__', None)
        if _ENV is None:
            _ENV = environment_prefixes()
        if not f or f.startswith(_ENV) or f.startswith(SYSTEM_PREFIXES) or is_harness(f):
            return None
    state = dict(getattr(value, '__dict__', {}) or {})
    for slot in (k for c in cls.__mro__ for k in (c.__dict__.get('__slots__') or ())):
        if isinstance(slot, str) and slot != '__dict__' and hasattr(value, slot):
            state[slot] = getattr(value, slot)
    return state


_SELF_LOADS = {}


def _self_loads(code):
    """Attribute names a method loads on `self` (stores, such as `self.state = state`, are not reads)."""
    names = _SELF_LOADS.get(code)
    if names is None:
        import dis
        names, prev = [], None
        for ins in dis.get_instructions(code):
            if ins.opname in ('LOAD_ATTR', 'LOAD_METHOD') and prev is not None and prev.opname.startswith(
                    'LOAD_FAST') and (prev.argval == 'self' or (isinstance(prev.argval, tuple) and prev.argval[-1] == 'self')):
                names.append(ins.argval)
            prev = ins
        names = _SELF_LOADS[code] = tuple(dict.fromkeys(names))
    return names


class LineScope:
    """Records (file, line) of reader code executed during generate(): call handlers, reader functions, the
    forwards and methods of model modules defined in reader code, and module and class bodies run by lazy
    imports. Interpreter, site-packages and EAT-1 lines are disabled after their first event.

    At the first start of each reader function it also resolves the global names the function reads: a
    module-level number outside the allowlist, or a module-level container, array or tensor (not a
    parameter) holding numbers, is a table or constant outside the weights (A3.module_data)."""
    TOOL = 4

    def __init__(self, allowed_numbers=None, exempt_names=()):
        self.exempt = set(exempt_names)
        self._pre, self.epoch = set(), 0  # ids of state tensors alive before the current item (set by the runner)
        self.handler_lines = {}
        self.in_handler = 0
        self.depth = 0  # model-forward depth (set by the monitor); a head forward inside a handler is model code
        self.handler_base = []
        self.lines = {}
        self.globals_read = []
        self.inside_model = False
        self.active = False
        self.env = environment_prefixes()
        self.mon = sys.monitoring
        self.allowed = allowed_numbers if allowed_numbers is not None else {0., 1., -1.}
        self._seen_codes = set()
        self._seen_self, self._held = set(), {}

    @property
    def preexisting(self):
        return self._pre

    @preexisting.setter
    def preexisting(self, ids):
        self._pre, self.epoch = ids, self.epoch+1

    def _skip(self, f):
        return f.startswith(self.env) or is_harness(f) or f.startswith('<') or f.startswith(SYSTEM_PREFIXES)

    def _line(self, code, line):
        f = code.co_filename
        if self._skip(f):
            return self.mon.DISABLE
        if not self.active:
            return None
        self.lines.setdefault(f, set()).add(line)
        if self.in_handler and self.depth == (self.handler_base[-1] if self.handler_base else 0):
            self.handler_lines.setdefault(f, set()).add(line)
        return self.mon.DISABLE

    def _start(self, code, offset):
        if self._skip(code.co_filename):
            return self.mon.DISABLE
        if not self.active:
            return None
        if not code.co_flags & inspect.CO_OPTIMIZED:
            return self.mon.DISABLE
        try:
            frame = sys._getframe(1)
            g = frame.f_globals if frame.f_code is code else None
        except ValueError:
            g = None
        if id(code) not in self._seen_codes:
            self._seen_codes.add(id(code))
            for name in code.co_names if g is not None else ():
                if name in g:
                    why = numeric_data(g[name], self.allowed)
                    if why:
                        self.globals_read.append(dict(file=code.co_filename, line=code.co_firstlineno,
                                                      function=code.co_qualname, name=name,
                                                      detail='module-level '+why))
        if g is None or code.co_varnames[:1] != ('self',):
            return self.mon.DISABLE
        # attributes the function reads on `self`: instance state and reader-code class attributes holding numbers,
        # judged for every instance a shared method runs on, once per item (the event stays enabled for methods)
        obj = frame.f_locals.get('self')
        key = (id(code), id(obj), self.epoch)
        if obj is None or key in self._seen_self:
            return None
        self._seen_self.add(key)
        self._held[id(obj)] = obj  # keeps ids unique while the scope lives
        inst = getattr(obj, '__dict__', {})
        classes = [c for c in type(obj).__mro__ if not self._skip(getattr(sys.modules.get(c.__module__),
                                                                           '__file__', None) or '<')]
        for name in _self_loads(code):
            if name in self.exempt:
                continue
            if name in inst:
                value, where = inst[name], 'instance'
            else:
                owner = next((c for c in classes if name in c.__dict__), None)
                if owner is None:
                    continue
                value, where = owner.__dict__[name], 'class '+owner.__qualname__
            why = numeric_data(value, self.allowed, tensors=True if where != 'instance' else self.preexisting)
            if why:
                self.globals_read.append(dict(file=code.co_filename, line=code.co_firstlineno,
                                              function=code.co_qualname, name='self.'+name,
                                              detail=f'{where} state {why}'))
        return None

    def start(self):
        try:
            self.mon.use_tool_id(self.TOOL, 'eat1')
        except ValueError:
            pass
        self.mon.register_callback(self.TOOL, self.mon.events.LINE, self._line)
        self.mon.register_callback(self.TOOL, self.mon.events.PY_START, self._start)
        self.mon.set_events(self.TOOL, self.mon.events.LINE | self.mon.events.PY_START)
        self.active = True

    def pause(self):
        self.active = False

    def resume(self):
        self.active = True

    def stop(self):
        self.active = False
        self.mon.set_events(self.TOOL, 0)
        self.mon.register_callback(self.TOOL, self.mon.events.LINE, None)
        self.mon.register_callback(self.TOOL, self.mon.events.PY_START, None)
        self.mon.restart_events()
        try:
            self.mon.free_tool_id(self.TOOL)
        except ValueError:
            pass
        return {f: sorted(v) for f, v in self.lines.items()}
