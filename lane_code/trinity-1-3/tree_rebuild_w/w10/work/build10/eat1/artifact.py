"""EAT-1 artifact manifest: the one checkpoint artifact a claimed read may load.

Schema `eat1-artifact-v1` (JSON):
  root      directory that holds the artifact files
  files     {relative path: {sha256, role}}; role in lm|vit|head|connector|tower|tokenizer|config
  modules   {dotted module path under reader.model ('' = the model itself): {role, name}}
            role in lm|vit|head|connector|tower|call_handler|fixed_math; `name` is what responses cite.
            fixed_math: parameter-free arithmetic with declared inputs/outputs and artifact-bound buffers.
            Its outputs may be printed; constants outside declared modules remain reader code.
A file is inside the artifact when its sha256 equals one listed here (A1).
"""
import hashlib
import json
from pathlib import Path

SCHEMA = 'eat1-artifact-v1'
FILE_ROLES = {'lm', 'vit', 'head', 'connector', 'tower', 'tokenizer', 'config'}
MODULE_ROLES = {'lm', 'vit', 'head', 'connector', 'tower', 'call_handler', 'fixed_math'}
MODEL_ROLES = {'lm', 'vit', 'head', 'connector', 'tower'}


def sha256(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


class Artifact:
    def __init__(self, path, verify=True):
        self.path = Path(path).resolve()
        data = json.loads(self.path.read_text())
        if data.get('schema') != SCHEMA:
            raise ValueError('artifact manifest schema differs: '+str(data.get('schema')))
        self.root = Path(data['root'])
        if not self.root.is_absolute():
            self.root = (self.path.parent/self.root).resolve()
        self.files = data['files']
        self.modules = data.get('modules', {})
        self.buffer_offenders = []
        for rel, entry in self.files.items():
            if entry.get('role') not in FILE_ROLES:
                raise ValueError(f'file {rel}: unknown role {entry.get("role")}')
        for name, entry in self.modules.items():
            if entry.get('role') not in MODULE_ROLES:
                raise ValueError(f'module {name!r}: unknown role {entry.get("role")}')
            if entry.get('role') == 'fixed_math':
                if not all(isinstance(entry.get(k), list) and entry[k] for k in ('inputs', 'outputs')):
                    raise ValueError(f'fixed_math {name!r} requires declared inputs and outputs')
                if not isinstance(entry.get('buffers'), dict):
                    raise ValueError(f'fixed_math {name!r} requires declared buffers')
        self.shas = {e['sha256'] for e in self.files.values()}
        self.manifest_sha256 = sha256(self.path)
        if verify:
            bad = [rel for rel, e in self.files.items()
                   if not (self.root/rel).is_file() or sha256(self.root/rel) != e['sha256']]
            if bad:
                raise ValueError('artifact files differ from manifest: '+', '.join(bad[:8]))

    def contains_sha(self, digest):
        return digest in self.shas

    def module_roles(self, model):
        """Resolve declared modules on the live model -> list of (path, module, role, name)."""
        out = []
        for path, entry in self.modules.items():
            mod = model
            for part in [p for p in path.split('.') if p]:
                mod = getattr(mod, part)
            out.append((path, mod, entry['role'], entry.get('name', path or 'model')))
        registered = {id(m) for m in model.modules()}
        self.buffer_offenders = []
        for path, mod, role, _ in out:
            if id(mod) not in registered:
                raise ValueError(f'declared module {path!r} is not registered on the model')
            if role == 'fixed_math':
                if any(True for _ in mod.parameters()):
                    raise ValueError(f'fixed_math {path!r} must have zero parameters')
                self._check_buffers(path, mod)
        return out

    def _check_buffers(self, path, mod):
        import torch
        declared = self.modules[path]['buffers']
        live = dict(mod.named_buffers())
        if set(declared) != set(live) or not set(live) <= set(mod.state_dict()):
            raise ValueError(f'fixed_math {path!r} must declare every persistent buffer')
        for name, binding in declared.items():
            rel, key = binding['file'], binding['key']
            if rel not in self.files or sha256(self.root/rel) != self.files[rel]['sha256']:
                raise ValueError(f'fixed_math {path!r} buffer file is not authenticated')
            if rel.endswith('.safetensors'):
                from safetensors.torch import load_file
                tensors = load_file(str(self.root/rel))
            else:
                tensors = torch.load(self.root/rel, map_location='cpu', weights_only=True)
            saved = tensors[key]
            value = live[name].detach().cpu().contiguous()
            saved = saved.detach().cpu().contiguous()
            def digest(t):
                return hashlib.sha256(str((t.dtype, tuple(t.shape))).encode()+t.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()
            expected, actual = digest(saved), digest(value)
            if actual != expected:
                self.buffer_offenders.append(dict(kind='fixed_math_buffer_mismatch', module=path,
                    buffer=name, file=str(self.root/rel), expected_sha256=expected, actual_sha256=actual))


def write_manifest(path, root, files, modules):
    """Helper for builders and the toy: files = {rel: role}."""
    root = Path(root).resolve()
    data = dict(schema=SCHEMA, root=str(root),
                files={rel: dict(sha256=sha256(root/rel), role=role) for rel, role in sorted(files.items())},
                modules=modules)
    Path(path).write_text(json.dumps(data, indent=1, sort_keys=True)+'\n')
    return data
