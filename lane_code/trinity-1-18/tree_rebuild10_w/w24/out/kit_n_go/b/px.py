"""Resolve pins only through the sealed staging inventory."""
from pathlib import Path
import os
from z import load, checked, inside

AWS = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
LUSTRE = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'


def inventory(kit):
    value = load(Path(kit)/'k/l.json')
    entries = {}
    def add(h, path, size=None, field=None, union=False):
        if not isinstance(h,str) or len(h)!=64:raise ValueError('R1_STAGED_PIN_INVALID')
        row = dict(path=path, bytes=size, field=field, union=union)
        if row not in entries.setdefault(h,[]):entries[h].append(row)
    for i,entry in enumerate(value.get('extra',[])+([value['a1rows']] if 'a1rows' in value else [])):
        add(entry['sha256'],entry['dest'],entry.get('bytes'),'extra.'+str(i))
    for i,entry in enumerate(value.get('tars',[])):
        for name,h in entry['files'].items():
            if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('R1_STAGED_PIN_INVALID')
            add(h,AWS+'/'+name,None,'tars.'+str(i)+'.files.'+name,True)
    staged=value.get('staged_inputs',{})
    for i,entry in enumerate(staged.get('files',[])):
        add(entry['sha256'],AWS+'/ap/8865619b/'+entry['destination'],entry.get('bytes'),'staged_inputs.files.'+str(i),True)
    for i,entry in enumerate(staged.get('packages',[])):
        for item in entry['inventory']:
            name=item['name']
            if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('R1_STAGED_PIN_INVALID')
            add(item['sha256'],AWS+'/ap/8865619b/'+entry['destination']+'/'+name,item.get('bytes'),'staged_inputs.packages.'+str(i)+'.'+name,True)
    return entries


def staged_path(path, root, union=False):
    root=Path(root)
    for prefix in (AWS,LUSTRE):
        if path.startswith(prefix+'/'):
            rel=path[len(prefix)+1:]
            if not union and rel.startswith('ap/8865619b/'):
                return inside(root/'x',rel[len('ap/8865619b/'):])
            return inside(root/'s/aws/u',rel)
    raise ValueError('R1_STAGED_PIN_LOCATION_INVALID')


def resolver(kit, root, sources):
    entries=inventory(kit)
    jobroot=Path(os.environ.get('Q_ROOT',str(Path(root).parent)))
    small=None
    def resolve(h, field):
        nonlocal small
        if h in sources:return sources[h]
        choices=entries.get(h)
        if not choices:
            if small is None:small=small_members(kit,jobroot)
            if h in small:
                checked(small[h],h);sources[h]=small[h];return small[h]
            raise ValueError('R1_STAGED_PIN_MISSING:'+h+':'+field)
        # Locations come from the sealed staging map, never from a receipt path.
        for item in choices:
            path=staged_path(item['path'],jobroot,item['union'])
            if path.is_file():
                checked(path,h,item['bytes']);sources[h]=str(path);return str(path)
        raise ValueError('R1_STAGED_PIN_NOT_PRESENT:'+h+':'+field)
    return resolve


def small_members(kit, root):
    from z import sha
    value=load(Path(kit)/"k/l.json").get("small")
    if not value:return {}
    # The shell extracts this SHA-authenticated archive before planning. Its raw
    # tree is private job storage; hash its regular members to build a source map.
    raw=Path(root)/"s/aws"/("raw."+value["sha256"])
    if not raw.is_dir():return {}
    found={}
    for path in sorted(raw.rglob("*")):
        if path.is_symlink():raise ValueError("R1_STAGED_PIN_SYMLINK")
        if path.is_file():found.setdefault(sha(path),str(path))
    return found
