"""Adapt the frozen trainer's code-aws Slurm admission module to the live AWS controller.

Since 2026-10-20 22:13 PT the AWS job-submit plugin runs every pool0 request in pool0_datahall_a or
pool0_datahall_b, and the AWS controller sometimes answers ``scontrol show job`` after more than the
module's 30-second timeout. When the pinned admission module loads, by import or as ``python -m``, this
hook inserts the partition alias right after its SLURM_SITES table and rebinds ``command`` so that a
subprocess.TimeoutExpired is retried up to six times and the two read-only allocation queries are answered once
per process (see CACHE_SOURCE). Every parse and check stays unchanged.
"""
import ast
import functools
import gc
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
import time

TARGET = "student_pilot.orchard_admission"
# Pinned admission module bytes: neutral trainer b4b2979 (unchanged through 299b0c52) and the 8-node branch 94902f07.
MODULE_SHA256 = {"845cceec09a23663222740be82e50d4a5c556a6780568e8a23fbca793330c499",
                 "9fc5f239ac8166fd1ddb735d8bbd85a1049adc7879f48e015c53ceabad51b26d"}
ALIASES = ("pool0_datahall_a", "pool0_datahall_b")
COMMAND_SOURCE = "def command(*args):\n    return subprocess.check_output(args, text=True, timeout=30).strip()"
RETRY_SOURCE = """
_aws_command_once = command
AWS_COMMAND_ATTEMPTS = 6
def command(*args):
    for _aws_attempt in range(AWS_COMMAND_ATTEMPTS):
        try:
            return _aws_command_once(*args)
        except subprocess.TimeoutExpired:
            if _aws_attempt + 1 == AWS_COMMAND_ATTEMPTS:
                raise
"""
# code-aws controller replies take 1-116 s, and the trainer re-derives its Slurm allocation before every microbatch on
# every rank (lease_check -> allocation -> scontrol show job / show hostnames). A running job's allocation cannot change,
# so these two read-only queries reuse their first reply for the life of the process, and, when AWS_SCONTROL_CACHE_DIR
# names a node-local directory of this job, for the life of the job across processes on the node (lease creation,
# binding and 8 ranks otherwise each wait on the controller and outrun the 300 s lease freshness rule). Every parse and
# check on the reply still runs each time. The step query of the job step these processes run inside is cached the
# same way (a process running in the step proves the step is live); listpids and nvidia-smi stay live.
CACHE_SOURCE = """
_aws_command_live = command
_aws_command_cache = {}
AWS_COMMAND_CACHE_SECONDS = float("inf")
def command(*args):
    import time as _aws_time, os as _aws_os, hashlib as _aws_hashlib
    if args[:2] == ('scontrol', 'show') and len(args) > 2 and args[2] in ('job', 'hostnames', 'step'):
        _aws_now = _aws_time.monotonic()
        _aws_hit = _aws_command_cache.get(args)
        if _aws_hit is not None and _aws_now - _aws_hit[0] < AWS_COMMAND_CACHE_SECONDS:
            return _aws_hit[1]
        _aws_dir = _aws_os.environ.get('AWS_SCONTROL_CACHE_DIR')
        _aws_file = None
        if _aws_dir:
            _aws_file = _aws_os.path.join(_aws_dir, _aws_hashlib.sha256(repr(args).encode()).hexdigest() + '.txt')
            if _aws_os.path.exists(_aws_file):
                with open(_aws_file) as _aws_stream:
                    _aws_value = _aws_stream.read()
                _aws_command_cache[args] = (_aws_now, _aws_value)
                return _aws_value
        _aws_value = _aws_command_live(*args)
        _aws_command_cache[args] = (_aws_now, _aws_value)
        if _aws_file:
            _aws_os.makedirs(_aws_dir, exist_ok=True)
            _aws_part = _aws_file + '.part.%d' % _aws_os.getpid()
            with open(_aws_part, 'w') as _aws_stream:
                _aws_stream.write(_aws_value)
            _aws_os.replace(_aws_part, _aws_file)
        return _aws_value
    return _aws_command_live(*args)
"""
ALIAS_SOURCE = """
_aws_partitions = SLURM_SITES["code-aws"]["partitions"]
if _aws_partitions != {"pool0": ({"av_alpamayo_aml_low", "av_alpamayo_aml_normal", "av_alpamayo_aml_high"}, 8)}:
    raise ImportError("The frozen code-aws partition table differs from its pinned value")
for _aws_alias in ("pool0_datahall_a", "pool0_datahall_b"):
    _aws_partitions[_aws_alias] = (set(_aws_partitions["pool0"][0]), 8)
AWS_PARTITION_ALIASES = ("pool0_datahall_a", "pool0_datahall_b")
del _aws_partitions, _aws_alias
"""


def aliased_code(data, path):
    if hashlib.sha256(data).hexdigest() not in MODULE_SHA256:
        raise ImportError("The frozen Slurm admission module differs from its pinned bytes")
    tree = ast.parse(data, path)
    positions = [index for index, node in enumerate(tree.body) if isinstance(node, ast.Assign)
                 and [ast.unparse(target) for target in node.targets] == ["SLURM_SITES"]]
    if len(positions) != 1:
        raise ImportError("The frozen admission module must define SLURM_SITES exactly once")
    commands = [index for index, node in enumerate(tree.body) if isinstance(node, ast.FunctionDef) and node.name == "command"]
    if len(commands) != 1 or ast.unparse(tree.body[commands[0]]) != COMMAND_SOURCE or commands[0] < positions[0]:
        raise ImportError("The frozen admission module's command function differs from its pinned form")
    tree.body[commands[0] + 1:commands[0] + 1] = ast.parse(RETRY_SOURCE).body + ast.parse(CACHE_SOURCE).body
    tree.body[positions[0] + 1:positions[0] + 1] = ast.parse(ALIAS_SOURCE).body
    return compile(ast.fix_missing_locations(tree), path, "exec", dont_inherit=True)


class AliasLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        return aliased_code(self.get_data(self.path), self.path)


# The trainer keeps every row, audit and processor object of its set in each rank's Python heap (about 23 GB per rank for
# 290k rows), and an automatic full garbage collection walks that whole heap on one rank while the other ranks wait in
# the next collective. Large arms show this as runs of 30-265 s steps (median 15-22 s) that begin a fixed number of steps
# after process start and widen as the ranks' collection points drift apart; arms of 29k-48k rows barely show it. Before the first training batch, the hook moves everything built during
# startup into the permanent generation (gc.freeze), so later full collections walk only per-step objects. Numerics and
# every check are unchanged. AWS_GC_FREEZE=0 turns the freeze off; collections of 1 s or more are logged either way.
GC_TARGET = "student_pilot.ddp_training"
GC_STARTED = [None]


def gc_watch(phase, info):
    if phase == "start":
        GC_STARTED[0] = time.perf_counter()
    elif GC_STARTED[0] is not None:
        seconds, GC_STARTED[0] = time.perf_counter() - GC_STARTED[0], None
        if seconds >= 1.0:
            print(f"AWS_GC_PAUSE pid={os.getpid()} generation={info['generation']} seconds={seconds:.1f} "
                  f"collected={info['collected']}", file=sys.stderr, flush=True)


def freeze_once(function):
    frozen = [False]

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if not frozen[0]:
            frozen[0] = True
            started = time.perf_counter()
            gc.collect()
            gc.freeze()
            print(f"AWS_GC_FREEZE pid={os.getpid()} objects={gc.get_freeze_count()} "
                  f"seconds={time.perf_counter() - started:.1f}", file=sys.stderr, flush=True)
        return function(*args, **kwargs)
    return wrapper


# Startup pre-stage (prestage.py, prestage_hooks.py): when the job exported a pre-stage cache (R1_PRESTAGE_DIR and
# R1_PRESTAGE_RECEIPT_SHA256) or a memory-probe registry (R1_PROBE_REGISTRY), these trainer modules get the startup
# hooks of prestage_hooks.py after they execute; a module whose source bytes are not pinned there is left unchanged.
PRESTAGE_TARGETS = ("student_pilot.common", "student_pilot.ddp_admission", "student_pilot.provisional_data",
                    "student_pilot.storage", GC_TARGET)


def prestage_wanted():
    return bool(os.environ.get("R1_PRESTAGE_DIR") or os.environ.get("R1_PROBE_REGISTRY"))


def prestage_patch(module, path):
    if prestage_wanted():
        import prestage_hooks
        with open(path, "rb") as stream:
            prestage_hooks.patch(module, stream.read())


class FreezeLoader(importlib.machinery.SourceFileLoader):
    def exec_module(self, module):
        super().exec_module(module)
        if gc_watch not in gc.callbacks:
            gc.callbacks.append(gc_watch)
        if os.environ.get("AWS_GC_FREEZE", "1") != "0":
            if not callable(getattr(module, "prefetched_batches", None)):
                raise ImportError("The trainer has no prefetched_batches function to freeze the startup heap before")
            module.prefetched_batches = freeze_once(module.prefetched_batches)
        prestage_patch(module, self.path)


class PrestageLoader(importlib.machinery.SourceFileLoader):
    def exec_module(self, module):
        super().exec_module(module)
        prestage_patch(module, self.path)


class AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname not in (TARGET, GC_TARGET) and not (fullname in PRESTAGE_TARGETS and prestage_wanted()):
            return None
        for finder in sys.meta_path:
            if finder is self or not hasattr(finder, "find_spec"):
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is not None:
                break
        else:
            return None
        if not spec.origin or not spec.origin.endswith(".py"):
            raise ImportError("The frozen trainer module has no source origin")
        loader = (AliasLoader if fullname == TARGET else FreezeLoader if fullname == GC_TARGET else PrestageLoader)(
            fullname, spec.origin)
        return importlib.util.spec_from_file_location(fullname, spec.origin, loader=loader)


if not any(isinstance(finder, AliasFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, AliasFinder())
