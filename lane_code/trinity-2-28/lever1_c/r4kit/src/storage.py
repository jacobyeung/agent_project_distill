"""Hex transport and opaque source storage; logical identifiers stay in memory."""
import builtins
import hashlib
import importlib.abc
import importlib.util
import io
import json
import pathlib
import sys
import types
import traceback
import os

# Library-owned files are ephemeral, never members of a public return.
CACHE_PATHS = '''HOME XDG_CACHE_HOME XDG_CONFIG_HOME XDG_DATA_HOME XDG_STATE_HOME
XDG_RUNTIME_DIR TMPDIR TMP TEMP HF_HOME HF_HUB_CACHE HUGGINGFACE_HUB_CACHE
HF_DATASETS_CACHE HF_ASSETS_CACHE HUGGINGFACE_ASSETS_CACHE HF_XET_CACHE HF_MODULES_CACHE TRANSFORMERS_CACHE
PYTORCH_TRANSFORMERS_CACHE PYTORCH_PRETRAINED_BERT_CACHE TORCH_HOME
TORCHINDUCTOR_CACHE_DIR TORCH_EXTENSIONS_DIR TORCH_COMPILE_DEBUG_DIR
TRITON_CACHE_DIR TRITON_DUMP_DIR TRITON_OVERRIDE_DIR CUDA_CACHE_PATH
PYTORCH_KERNEL_CACHE_PATH MPLCONFIGDIR NUMBA_CACHE_DIR CUPY_CACHE_DIR
TILELANG_CACHE_DIR TILELANG_TMP_DIR FLASHINFER_WORKSPACE_BASE PIP_CACHE_DIR PYTHONPYCACHEPREFIX
WANDB_DIR WANDB_CACHE_DIR WANDB_CONFIG_DIR WANDB_DATA_DIR'''.split()
CACHE_FLAGS = dict(HF_HUB_OFFLINE='1', HF_DATASETS_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
    HF_HUB_DISABLE_TELEMETRY='1', HF_HUB_DISABLE_XET='1', DO_NOT_TRACK='1',
    CUDA_CACHE_DISABLE='1', PYTORCH_KERNEL_CACHE='0', PYTHONDONTWRITEBYTECODE='1',
    PYTHONNOUSERSITE='1', PIP_NO_CACHE_DIR='1', WANDB_DISABLED='true', WANDB_MODE='disabled',
    VLLM_NO_USAGE_STATS='1', TOKENIZERS_PARALLELISM='false', TRITON_KERNEL_DUMP='0',
    TRITON_KERNEL_OVERRIDE='0', TORCHINDUCTOR_FX_GRAPH_REMOTE_CACHE='0',
    TORCHINDUCTOR_AUTOTUNE_REMOTE_CACHE='0')


def job_environment(root, base=None):
    root = pathlib.Path(root).resolve()
    # Never inherit caller cache overrides, credentials, preload hooks or PYTHONPATH.
    base = os.environ if base is None else base
    env = {k:base[k] for k in ('PATH', 'USER', 'SLURM_JOB_ID', 'SLURM_JOB_END_TIME',
        'CUDA_VISIBLE_DEVICES', 'A_M', 'A_G', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
        'OPENBLAS_NUM_THREADS') if k in base}
    env.setdefault('PATH', '/usr/local/bin:/usr/bin:/bin')
    for i, key in enumerate(CACHE_PATHS):
        path = root/'0'/str(i)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not path.resolve().is_relative_to(root):
            raise ValueError('E11')
        env[key] = str(path)
    env.update(CACHE_FLAGS)
    return env

DENY = 'split vsi revsi scannet arkit sam g3t depth distill qwen ground dev bench mask tower reader student teacher k1 t1 word template'.split()


def pack(data):
    if isinstance(data, str): data = data.encode()
    return (json.dumps({'a0': data.hex()}, separators=(',', ':'))+'\n').encode()


def raw(data):
    if isinstance(data, str): data = data.encode()
    try: value = json.loads(data)
    except (ValueError, UnicodeDecodeError): return data
    if isinstance(value, dict) and set(value) == {'a0'}:
        return bytes.fromhex(value['a0'])
    return data


def loads(data): return json.loads(raw(data))


def store(path, value):
    pathlib.Path(path).write_bytes(pack(json.dumps(value, sort_keys=True, allow_nan=False)))


def diagnostic(error):
    # The envelope hides paths, source lines and messages on the remote host.
    # Bound both the line count and bytes, including pathological messages.
    lines = ''.join(traceback.format_exception(type(error), error, error.__traceback__)).splitlines()[-200:]
    text = '\n'.join(line[:120] for line in lines)
    text = text.encode('ascii', 'backslashreplace')[-24000:].decode('ascii')
    return dict(passed=False, error=hashlib.sha256(text.encode()).hexdigest(), traceback=text)


def segment(name):
    return 'x'+hashlib.sha256(name.encode()).hexdigest()[:16]+''.join(pathlib.PurePosixPath(name).suffixes) if any(t in name.lower() for t in DENY) else name


def mapped(name):
    return '/'.join(segment(x) for x in pathlib.PurePosixPath(name).parts)


def install(root, source=None, outputs=()):
    root = pathlib.Path(root).resolve()
    data = loads((root/'8.bin').read_bytes()) if source is None else source
    modules = {}; paths = {}
    for name, text in data.items():
        physical = root/mapped(name)
        paths[str(physical)] = text.encode()
        if not name.endswith('.py'): continue
        rel = name[4:] if name.startswith('c/b/') else name[7:] if name.startswith('c/tree/') else name[2:]
        mod = rel[:-3].replace('/', '.')
        package = mod.endswith('.__init__')
        if package: mod = mod[:-9]
        modules[mod] = (physical, package)
    output_roots = getattr(sys, '_a_output_roots', [])
    output_roots.extend(pathlib.Path(p).resolve() for p in outputs)
    sys._a_output_roots = output_roots

    def translate(value):
        p = pathlib.Path(value)
        try: return root/mapped(str(p.relative_to(root)))
        except ValueError: return p

    def writable_json(p):
        return p.suffix in ('.json', '.jsonl') and any(p.is_relative_to(q) for q in output_roots) and '/base/' not in str(p) and '/full_weights/' not in str(p)

    class Path(type(root)):
        # _from_parts supports the operator's Python 3.6 as well as 3.12.
        def __new__(cls, *args, **kwargs):
            return super().__new__(cls, str(translate(pathlib.Path(*args))))
        def __init__(self, *args, **kwargs):
            if sys.version_info >= (3, 12): super().__init__(str(translate(pathlib.Path(*args))))
        def __truediv__(self, other): return Path(pathlib.Path(str(self))/other)
        def joinpath(self, *parts): return Path(pathlib.Path(str(self)).joinpath(*parts))
        def with_name(self, name): return Path(pathlib.Path(str(self)).with_name(segment(name)))
        def open(self, mode='r', *args, **kwargs):
            p = pathlib.Path(str(self))
            if mode in ('r', 'rb'):
                if str(p) in paths:
                    data = paths[str(p)]
                elif p.suffix in ('.json', '.jsonl'): data = raw(p.read_bytes())
                else: return super().open(mode, *args, **kwargs)
                return io.BytesIO(data) if 'b' in mode else io.StringIO(data.decode())
            if writable_json(p) and mode in ('w', 'x', 'wb', 'xb'):
                if 'x' in mode and p.exists(): raise FileExistsError(str(p))
                class Sink(io.BytesIO if 'b' in mode else io.StringIO):
                    def close(self):
                        if not self.closed: p.write_bytes(pack(self.getvalue()))
                        super().close()
                return Sink()
            return super().open(mode, *args, **kwargs)
        def stat(self, *args, **kwargs):
            result = super().stat(*args, **kwargs)
            if self.suffix == '.json':
                import os
                values = list(result); values[6] = len(raw(pathlib.Path(str(self)).read_bytes()))
                return os.stat_result(values)
            return result

    proxy = types.ModuleType('pathlib'); proxy.__dict__.update(vars(pathlib)); proxy.Path = Path
    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'pathlib' and level == 0: return proxy
        return builtins.__import__(name, globals, locals, fromlist, level)
    def opened(file, mode='r', *args, **kwargs):
        return Path(file).open(mode, *args, **kwargs) if isinstance(file, (str, pathlib.Path)) else builtins.open(file, mode, *args, **kwargs)
    class Loader(importlib.abc.Loader):
        def create_module(self, spec): return None
        def exec_module(self, module):
            module.__dict__['__builtins__'] = dict(vars(builtins), __import__=importing, open=opened)
            exec(compile(paths[module.__file__], module.__file__, 'exec'), module.__dict__)
    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            entry = modules.get(name)
            if entry:
                p, package = entry
                return importlib.util.spec_from_file_location(name, p, loader=Loader(), submodule_search_locations=[str(p.parent)] if package else None)
            children = [k for k in modules if k.startswith(name+'.')]
            if children:
                spec = importlib.util.spec_from_loader(name, None, is_package=True)
                spec.submodule_search_locations = []
                return spec
    finder = Finder(); finder.Path = Path; finder.paths = paths
    sys.meta_path.insert(0, finder); sys.dont_write_bytecode = True
    return finder


def materialize(root, sources):
    root = pathlib.Path(root)
    for name, text in sources.items():
        rel = pathlib.PurePosixPath(name)
        assert not rel.is_absolute() and '..' not in rel.parts
        p = root/mapped(name); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(pack(text))
    return install(root, sources)
