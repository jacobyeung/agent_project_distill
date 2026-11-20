from common import *
import base64
closure=J.load(D/'IMPORT_CLOSURE.json')
s=(L/'attic/build24m4j/out/kit_qd/b/rb.py').read_text()
s=s.replace('import tarfile','import tarfile\nimport os\nimport importlib\nimport importlib.machinery\nimport time')
start=s.index('\ndef command(')
helper='''

def environment():
    import site
    # Capture the interpreter's effective paths, including overlays added by its
    # launcher. The active source tree and kit directory are code, not sites.
    from student_pilot import p3_provenance
    code = Path(p3_provenance.__file__).resolve().parents[1]
    helper = Path(__file__).resolve().parent
    paths = []
    for value in list(sys.path) + site.getsitepackages():
        if not value:
            continue
        path = Path(value).absolute()
        if path.resolve() in (code, helper) or not path.exists():
            continue
        if str(path) not in paths:
            paths.append(str(path))
    binds = []
    for value in [sys.base_prefix, sys.prefix, str(Path(sys.executable).resolve().parent.parent)] + paths:
        if value not in binds and Path(value).exists():
            binds.append(value)
    return dict(paths=paths, binds=binds, executable=sys.executable)


def tree_names(tree):
    names = set()
    for p in Path(tree).iterdir():
        if p.is_file() and p.suffix == ".py":
            names.add(p.stem)
        elif p.is_dir() and any(p.rglob("*.py")):
            names.add(p.name)
    return sorted(names)


def import_probe(tree, paths, modules):
    tree = Path(tree).resolve()
    for name in tree_names(tree):
        for path in paths:
            if Path(path).resolve() == tree:
                continue
            if importlib.machinery.PathFinder.find_spec(name, [path]) is not None:
                raise ValueError("R1_RECONSTRUCTION_MODULE_SHADOWED:"+name)
        loaded = sys.modules.get(name)
        if loaded is not None:
            location = getattr(loaded, "__file__", None)
            if location is None or not Path(location).resolve().is_relative_to(tree):
                raise ValueError("R1_RECONSTRUCTION_MODULE_SHADOWED:"+name)
    # No site.addsitedir: .pth startup hooks must not mutate the sealed producer.
    sys.path[:] = [str(tree)] + [p for p in paths if Path(p).resolve() != tree]
    importlib.invalidate_caches()
    result = {}
    for name in modules:
        try:
            module = importlib.import_module(name)
            # Transformers exposes several classes lazily; force the CPU
            # processor path while no row build has started.
            if name == "transformers":
                getattr(module, "AutoProcessor")
                getattr(module, "AddedToken")
        except Exception as error:
            missing = getattr(error, "name", None) or name
            raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+missing) from error
        result[name] = dict(path=getattr(module, "__file__", None),
                            version=getattr(module, "__version__", None))
    for name, module in list(sys.modules.items()):
        if name.split(".")[0] not in tree_names(tree):
            continue
        location = getattr(module, "__file__", None)
        places = list(getattr(module, "__path__", []))
        if location:
            places.append(location)
        if not places or any(not Path(p).resolve().is_relative_to(tree) for p in places):
            raise ValueError("R1_RECONSTRUCTION_MODULE_SHADOWED:"+name.split(".")[0])
    return result


def probe_modules():
    import base64
    return json.loads(base64.b64decode("ENCODED_MODULES"))
'''.replace('ENCODED_MODULES',base64.b64encode(json.dumps(closure['probe']).encode()).decode())
s=s[:start]+helper+s[start:]
s=s.replace('def command(root, control, tree, mounts):','def command(root, control, tree, mounts, env=None):')
s=s.replace('    for p in (Path(sys.base_prefix), Path(sys.prefix), Path(__file__).resolve().parent, Path(root)):', '    env = environment() if env is None else env\n    for p in [*env["binds"], Path(__file__).resolve().parent, Path(root)]:')
s=s.replace('sys.executable, "-I", "-s", "-B",','env["executable"], "-I", "-s", "-S", "-B",')
s=s.replace('    write(control, dict(config=p, recipe=recipe, root=str(root), directory=directory))','    env = environment()\n    write(control, dict(config=p, recipe=recipe, root=str(root), directory=directory, environment=env))')
s=s.replace('command(root, control, tree, mounts)', 'command(root, control, tree, mounts, env)')
s=s.replace('    sys.path.insert(0, str(tree))\n', '''    value = json.loads(Path(control).read_text())
    root = Path(value["root"]); directory = value["directory"]
    started = time.monotonic()
    probe_path = root/(directory+"_imports.json")
    probe = dict(status="REFUSE", elapsed_seconds=0)
    try:
        probe["modules"] = import_probe(tree, value["environment"]["paths"],
                                        value.get("probe_modules", probe_modules()))
        probe["status"] = "PASS"
    except BaseException as error:
        probe["refusal"] = str(error)
        raise
    finally:
        probe["elapsed_seconds"] = time.monotonic()-started
        probe_path.write_text(json.dumps(probe, sort_keys=True, indent=2)+"\\n")
    if value.get("probe_only"):
        return
''')
# Only cache the top-level inventory once per child scan.
s=s.replace('    for name, module in list(sys.modules.items()):\n        if name.split(".")[0] not in tree_names(tree):','    names = set(tree_names(tree))\n    for name, module in list(sys.modules.items()):\n        if name.split(".")[0] not in names:')
for n in NAMES:replace(kit(n)/'b/rb.py',s)
J.write(D/'SEALS.json',{n:reseal(kit(n)) for n in NAMES})
print('RB EDIT',len(s),'bytes; modules',len(closure['probe']))
