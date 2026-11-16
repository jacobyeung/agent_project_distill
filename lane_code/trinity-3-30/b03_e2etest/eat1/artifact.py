"""EAT-1 artifact manifest: the one checkpoint artifact a claimed read may load.

Schema `eat1-artifact-v1` (JSON):
  root      directory that holds the artifact files
  files     {relative path: {sha256, role}}; role in lm|vit|head|connector|tower|tokenizer|config
  modules   {dotted module path under reader.model ('' = the model itself): {role, name}}
            role in lm|vit|head|connector|tower|call_handler|fixed_math; `name` is what responses cite.
            fixed_math: a reviewed module that only unprojects with a head's intrinsics (USER ruling 5); its
            outputs may be printed, and its code is judged like any reader code.
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
        for rel, entry in self.files.items():
            if entry.get('role') not in FILE_ROLES:
                raise ValueError(f'file {rel}: unknown role {entry.get("role")}')
        for name, entry in self.modules.items():
            if entry.get('role') not in MODULE_ROLES:
                raise ValueError(f'module {name!r}: unknown role {entry.get("role")}')
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
        for path, mod, role, _ in out:
            if id(mod) not in registered:
                raise ValueError(f'declared module {path!r} is not registered on the model')
        return out


def write_manifest(path, root, files, modules):
    """Helper for builders and the toy: files = {rel: role}."""
    root = Path(root).resolve()
    data = dict(schema=SCHEMA, root=str(root),
                files={rel: dict(sha256=sha256(root/rel), role=role) for rel, role in sorted(files.items())},
                modules=modules)
    Path(path).write_text(json.dumps(data, indent=1, sort_keys=True)+'\n')
    return data
