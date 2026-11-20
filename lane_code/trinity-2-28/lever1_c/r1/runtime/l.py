"""Resolve sealed modules and resource paths without descriptive disk entries."""
import builtins
import importlib.abc
import importlib.util
import json
import pathlib
import sys
import types
import io
import j


def install(root):
    j.install()
    root = pathlib.Path(root).resolve()
    for finder in sys.meta_path:
        if getattr(finder, 'root', None) == root:
            return finder
    data = json.loads((root/'l.json').read_text())
    edges = {(k[0], bytes.fromhex(k[1]).decode()): v for k,v in data['edges']}
    modules = {bytes.fromhex(k).decode(): v for k,v in data['modules'].items()}

    def translate(value):
        p = pathlib.Path(value)
        try: parts = p.relative_to(root).parts
        except ValueError: return str(p)
        result = []
        for part in parts:
            result.append(edges.get(('/'.join(result), part), part))
        return str(root.joinpath(*result))

    class Path(type(root)):
        def __init__(self, *args):
            super().__init__(translate(pathlib.Path(*args)))
        def __truediv__(self, other):
            return Path(pathlib.Path(str(self))/other)
        def joinpath(self, *parts):
            return Path(pathlib.Path(str(self)).joinpath(*parts))
        def with_name(self, name):
            return Path(pathlib.Path(str(self)).with_name(name))
        def open(self, mode='r', *args, **kwargs):
            if mode in ('r','rb') and self.suffix == '.json':
                data=pathlib.Path(str(self)).read_bytes()
                data=j.raw(data)
                return io.BytesIO(data) if mode=='rb' else io.StringIO(data.decode())
            return super().open(mode,*args,**kwargs)
        def stat(self, *args, **kwargs):
            result=super().stat(*args,**kwargs)
            if self.suffix == '.json':
                import os
                values=list(result);values[6]=len(j.raw(pathlib.Path(str(self)).read_bytes()))
                return os.stat_result(values)
            return result

    proxy = types.ModuleType('pathlib')
    proxy.__dict__.update(vars(pathlib));proxy.Path = Path
    original_import = builtins.__import__
    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        owner=(globals or {}).get('__name__','')
        physical=owner in ('orchard_h10.job','orchard_h10.export_pins','orchard_stage','orchard_h10.vendor.orchard_stage')
        if name == 'pathlib' and level == 0 and not physical:return proxy
        return original_import(name, globals, locals, fromlist, level)

    class Loader(importlib.abc.SourceLoader):
        def __init__(self, name, entry):self.name=name;self.entry=entry
        def get_filename(self, name):return str(root/self.entry[0])
        def get_data(self, path):return pathlib.Path(path).read_bytes()
        def is_package(self, name):return self.entry[1]
        def exec_module(self, module):
            module.__dict__['__builtins__'] = dict(vars(builtins), __import__=importing)
            if not module.__name__.startswith('orchard_h10.'):
                def opened(file,mode='r',*args,**kwargs):
                    if isinstance(file,(str,pathlib.Path)) and str(file).endswith('.json') and mode in ('r','rb'):
                        return Path(file).open(mode,*args,**kwargs)
                    return builtins.open(file,mode,*args,**kwargs)
                module.__dict__['__builtins__']['open']=opened
            exec(self.get_code(module.__name__), module.__dict__)

    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            entry = modules.get(name)
            if entry is None:return None
            if entry[2]:
                spec=importlib.util.spec_from_loader(name, loader=None, is_package=True)
                spec.submodule_search_locations=[str(root/entry[0])]
                return spec
            return importlib.util.spec_from_file_location(name, root/entry[0],
                loader=Loader(name,entry), submodule_search_locations=[str((root/entry[0]).parent)] if entry[1] else None)
    finder=Finder();finder.root=root;finder.Path=Path
    sys.meta_path.insert(0,finder)
    sys.dont_write_bytecode=True
    return finder
