from common import *
s=(kit('qd')/'b/rb.py').read_text().replace('import importlib.machinery','import importlib.machinery\nimport importlib.util')
a=s.index('        loaded = sys.modules.get(name)');b=s.index('    # No site.addsitedir:',a)
s=s[:a]+'''        loaded = importlib.util.find_spec(name)
        if loaded is not None and loaded.origin is not None:
            if not Path(loaded.origin).resolve().is_relative_to(tree):
                raise ValueError("R1_RECONSTRUCTION_MODULE_SHADOWED:"+name)
'''+s[b:]
a=s.index('        result[name] = dict(');b=s.index('    return result',a)
s=s[:a]+'''        location = getattr(module, "__file__") if hasattr(module, "__file__") else None
        version = getattr(module, "__version__") if hasattr(module, "__version__") else None
        result[name] = dict(path=location, version=version)
        if name.split(".")[0] in tree_names(tree):
            places = list(getattr(module, "__path__")) if hasattr(module, "__path__") else []
            if location:
                places.append(location)
            if not places or any(not Path(p).resolve().is_relative_to(tree) for p in places):
                raise ValueError("R1_RECONSTRUCTION_MODULE_SHADOWED:"+name.split(".")[0])
'''+s[b:]
for n in NAMES:replace(kit(n)/'b/rb.py',s)
J.write(D/'SEALS.json',{n:reseal(kit(n)) for n in NAMES})
