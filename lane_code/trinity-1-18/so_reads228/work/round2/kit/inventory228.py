"""Reconcile named archive destinations without changing another lane's files."""
import os
from pathlib import Path
from common228 import Refusal,checked,local,read,sha

def verify_members(files):
    mismatches=[]
    for name,spec in sorted(files.items()):
        path=Path(name)
        try:
            if 'link' in spec:
                if not path.is_symlink() or os.readlink(str(path))!=spec['link']:raise ValueError('symlink differs')
            elif 'hardlink' in spec:
                if path.is_symlink() or not path.is_file() or not os.path.samefile(str(path),spec['hardlink']):raise ValueError('hardlink differs')
            else:
                if path.is_symlink():raise ValueError('unexpected symlink')
                checked(path,spec)
        except (OSError,ValueError) as error:mismatches.append(dict(path=name,error=str(error)))
    if mismatches:raise Refusal('Archive members differ; existing files preserved: '+str(mismatches))

def prepare_products(data):
    """Enumerate exact products of sealed prepare/stage_restore; never whitelist a subtree."""
    data=Path(data)
    names={'ENVIRONMENT.json','6.json','binding.json','manifest.json','settings.json','READY.json',
           'e/RESTORE.json','e/artifact.json','e/receipt.json','e/model.json','e/heads.pt',
           'e/full_weights/full_weights.json'}
    if (data/'e/model.json').is_file():
        model=read(data/'e/model.json')
        names.update('e/base/'+name for name in model['files'])
    if (data/'e/full_weights/full_weights.json').is_file():
        full=read(data/'e/full_weights/full_weights.json')
        names.update('e/full_weights/'+row['name'] for row in full['files']+[full['index']])
    if any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
        raise Refusal('Unsafe prepare product name')
    return {str(data/name) for name in names}

def unexplained(roots,files,products=()):
    allowed=set(files)|set(products);extras=[]
    roots=sorted(set(str(local(p)) for p in roots))
    for root in roots:
        for base,dirs,names in os.walk(root,followlinks=False):
            # Directory symlinks must also be accounted for; never follow them.
            for name in dirs+names:
                path=Path(base)/name
                if (path.is_symlink() or not path.is_dir()) and str(path) not in allowed:
                    extras.append(str(path))
    if extras:raise Refusal('Unexplained files under archive destinations; preserved for coordinator: '+str(sorted(set(extras))))
    return dict(checked_roots=roots,unexplained_files=[],known_prepare_products=sorted(products))

def runtime_requirements(plan,files,inputs):
    from namespace228 import host_path
    base=Path(plan['environment']['local_base_env'])
    py=Path(plan['environment']['local_base_python'])
    required=[str(py),str(base/'bin/python'),str(base/'pyvenv.cfg'),inputs['python'],
              str(Path(inputs['python']).parent/'boot.py'),str(py.parents[1]/'lib/python3.12/encodings/__init__.py')]
    missing=[name for name in required if name not in files]
    # Every framework required by sealed prepare must come from the authenticated
    # base environment or the authenticated a4 overlay. Runtime import verifies ABI.
    prefixes=[base/'lib/python3.12/site-packages']+[Path(p) for p in inputs['env_roots']]
    for module in plan['environment']['versions']:
        choices=[str(prefix/module/'__init__.py') for prefix in prefixes]
        if not any(name in files for name in choices):missing.append(module+': '+str(choices))
    if missing:raise Refusal('Runtime member inventory cannot supply sealed prepare: '+str(missing))
    return dict(required_paths=required,required_modules=sorted(plan['environment']['versions']),passed=True)
