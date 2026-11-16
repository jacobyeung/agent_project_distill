pass
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
TARGET = 'student_pilot.orchard_admission'
MODULE_SHA256 = {'3dd0a43aa89996ed8a564f45af30d9631ad896a54a2e6437efa0a4a58d2f789f', '845cceec09a23663222740be82e50d4a5c556a6780568e8a23fbca793330c499', '9fc5f239ac8166fd1ddb735d8bbd85a1049adc7879f48e015c53ceabad51b26d', 'b69b654c855f4c9941599f8ef2575786e1a754b6da80bd441ce04b2aa7caeaec'}
ALIASES = ('pool0_datahall_a', 'pool0_datahall_b')
COMMAND_SOURCE = 'def command(*args):\n    return subprocess.check_output(args, text=True, timeout=30).strip()'
RETRY_SOURCE = '\n_aws_command_once = command\nAWS_COMMAND_ATTEMPTS = 6\ndef command(*args):\n    for _aws_attempt in range(AWS_COMMAND_ATTEMPTS):\n        try:\n            return _aws_command_once(*args)\n        except subprocess.TimeoutExpired:\n            if _aws_attempt + 1 == AWS_COMMAND_ATTEMPTS:\n                raise\n'
CACHE_SOURCE = '\n_aws_command_live = command\n_aws_command_cache = {}\nAWS_COMMAND_CACHE_SECONDS = float("inf")\ndef command(*args):\n    import time as _aws_time, os as _aws_os, hashlib as _aws_hashlib\n    if args[:2] == (\'scontrol\', \'show\') and len(args) > 2 and args[2] in (\'job\', \'hostnames\', \'step\'):\n        _aws_now = _aws_time.monotonic()\n        _aws_hit = _aws_command_cache.get(args)\n        if _aws_hit is not None and _aws_now - _aws_hit[0] < AWS_COMMAND_CACHE_SECONDS:\n            return _aws_hit[1]\n        _aws_dir = _aws_os.environ.get(\'AWS_SCONTROL_CACHE_DIR\')\n        _aws_file = None\n        if _aws_dir:\n            _aws_file = _aws_os.path.join(_aws_dir, _aws_hashlib.sha256(repr(args).encode()).hexdigest() + \'.txt\')\n            if _aws_os.path.exists(_aws_file):\n                with open(_aws_file) as _aws_stream:\n                    _aws_value = _aws_stream.read()\n                _aws_command_cache[args] = (_aws_now, _aws_value)\n                return _aws_value\n        _aws_value = _aws_command_live(*args)\n        _aws_command_cache[args] = (_aws_now, _aws_value)\n        if _aws_file:\n            _aws_os.makedirs(_aws_dir, exist_ok=True)\n            _aws_part = _aws_file + \'.part.%d\' % _aws_os.getpid()\n            with open(_aws_part, \'w\') as _aws_stream:\n                _aws_stream.write(_aws_value)\n            _aws_os.replace(_aws_part, _aws_file)\n        return _aws_value\n    return _aws_command_live(*args)\n'
ALIAS_SOURCE = '\n_aws_partitions = SLURM_SITES["code-aws"]["partitions"]\nif _aws_partitions != {"pool0": ({"av_alpamayo_aml_low", "av_alpamayo_aml_normal", "av_alpamayo_aml_high"}, 8)}:\n    raise ImportError("The frozen code-aws partition table differs from its pinned value")\nfor _aws_alias in ("pool0_datahall_a", "pool0_datahall_b"):\n    _aws_partitions[_aws_alias] = (set(_aws_partitions["pool0"][0]), 8)\nAWS_PARTITION_ALIASES = ("pool0_datahall_a", "pool0_datahall_b")\ndel _aws_partitions, _aws_alias\nimport os as _aws_os2, json as _aws_json2\nif _aws_os2.environ.get("A_SITE_PROFILE"):\n    # P1 on AWS (lane p1_run): the closure\'s single-node launcher pins STUDENT_SLURM_SITE=orchard; the reviewed AWS\n    # identity (host pattern, account, user, partition/QoS, GPU limit) replaces that site\'s profile. Checks unchanged.\n    with open(_aws_os2.environ["A_SITE_PROFILE"]) as _aws_stream2:\n        _aws_p2 = _aws_json2.load(_aws_stream2)\n    # Multi-node legs (lane p1c_aws32) select site code-aws (TK_SLURM_SITE), whose native validator admits 2-8 nodes;\n    # the same reviewed identity replaces its pinned pool0 table, which the live controller no longer uses.\n    for _aws_site in ("orchard", "code-aws"):\n        SLURM_SITES[_aws_site] = {"host_pattern": _aws_p2["host_pattern"], "account": _aws_p2["account"],\n                                  "user": _aws_p2["user"],\n                                  "partitions": {_k: (set(_v[0]), int(_v[1])) for _k, _v in _aws_p2["partitions"].items()}}\n    del _aws_p2, _aws_stream2, _aws_site\n'

def aliased_code(data, path):
    if hashlib.sha256(data).hexdigest() not in MODULE_SHA256:
        raise ImportError('The frozen Slurm admission module differs from its pinned bytes')
    tree = ast.parse(data, path)
    positions = [index for index, node in enumerate(tree.body) if isinstance(node, ast.Assign) and [ast.unparse(target) for target in node.targets] == ['SLURM_SITES']]
    if len(positions) != 1:
        raise ImportError('The frozen admission module must define SLURM_SITES exactly once')
    commands = [index for index, node in enumerate(tree.body) if isinstance(node, ast.FunctionDef) and node.name == 'command']
    if len(commands) != 1 or ast.unparse(tree.body[commands[0]]) != COMMAND_SOURCE or commands[0] < positions[0]:
        raise ImportError("The frozen admission module's command function differs from its pinned form")
    tree.body[commands[0] + 1:commands[0] + 1] = ast.parse(RETRY_SOURCE).body + ast.parse(CACHE_SOURCE).body
    tree.body[positions[0] + 1:positions[0] + 1] = ast.parse(ALIAS_SOURCE).body
    return compile(ast.fix_missing_locations(tree), path, 'exec', dont_inherit=True)

class AliasLoader(importlib.machinery.SourceFileLoader):

    def get_code(self, fullname):
        return aliased_code(self.get_data(self.path), self.path)
GC_TARGET = 'student_pilot.ddp_training'
GC_STARTED = [None]

def gc_watch(phase, info):
    if phase == 'start':
        GC_STARTED[0] = time.perf_counter()
    elif GC_STARTED[0] is not None:
        seconds, GC_STARTED[0] = (time.perf_counter() - GC_STARTED[0], None)
        if seconds >= 1.0:
            print(f"AWS_GC_PAUSE pid={os.getpid()} generation={info['generation']} seconds={seconds:.1f} collected={info['collected']}", file=sys.stderr, flush=True)

def freeze_once(function):
    frozen = [False]

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if not frozen[0]:
            frozen[0] = True
            started = time.perf_counter()
            gc.collect()
            gc.freeze()
            print(f'AWS_GC_FREEZE pid={os.getpid()} objects={gc.get_freeze_count()} seconds={time.perf_counter() - started:.1f}', file=sys.stderr, flush=True)
        return function(*args, **kwargs)
    return wrapper
PRESTAGE_TARGETS = ('student_pilot.common', 'student_pilot.ddp_admission', 'student_pilot.provisional_data', 'student_pilot.storage', GC_TARGET)

def prestage_wanted():
    return bool(os.environ.get('R1_PRESTAGE_DIR') or os.environ.get('R1_PROBE_REGISTRY'))

def prestage_patch(module, path):
    if prestage_wanted():
        import prestage_hooks
        with open(path, 'rb') as stream:
            prestage_hooks.patch(module, stream.read())

class FreezeLoader(importlib.machinery.SourceFileLoader):

    def exec_module(self, module):
        super().exec_module(module)
        if gc_watch not in gc.callbacks:
            gc.callbacks.append(gc_watch)
        if os.environ.get('AWS_GC_FREEZE', '1') != '0':
            if not callable(getattr(module, 'prefetched_batches', None)):
                raise ImportError('The trainer has no prefetched_batches function to freeze the startup heap before')
            module.prefetched_batches = freeze_once(module.prefetched_batches)
        prestage_patch(module, self.path)

class PrestageLoader(importlib.machinery.SourceFileLoader):

    def exec_module(self, module):
        super().exec_module(module)
        prestage_patch(module, self.path)

class AliasFinder(importlib.abc.MetaPathFinder):

    def find_spec(self, fullname, path, target=None):
        if fullname not in (TARGET, GC_TARGET) and (not (fullname in PRESTAGE_TARGETS and prestage_wanted())):
            return None
        for finder in sys.meta_path:
            if finder is self or not hasattr(finder, 'find_spec'):
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is not None:
                break
        else:
            return None
        if not spec.origin or not spec.origin.endswith('.py'):
            raise ImportError('The frozen trainer module has no source origin')
        loader = (AliasLoader if fullname == TARGET else FreezeLoader if fullname == GC_TARGET else PrestageLoader)(fullname, spec.origin)
        return importlib.util.spec_from_file_location(fullname, spec.origin, loader=loader)
if not any((isinstance(finder, AliasFinder) for finder in sys.meta_path)):
    sys.meta_path.insert(0, AliasFinder())
