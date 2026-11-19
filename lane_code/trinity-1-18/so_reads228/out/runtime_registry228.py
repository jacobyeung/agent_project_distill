"""Read the coordinator's tar listings and cross-check the private runtime registry."""
from pathlib import Path
from common228 import HERE,Refusal,canonical,checked,read,sha
from runtime228 import runtime_path,safe_name

def list_headers(path):
    result=[]
    with Path(path).open() as stream:
        for line in stream:
            columns=line.rstrip('\n').split(None,5)
            if len(columns)!=6:raise Refusal('Malformed coordinator tar listing')
            mode,owner,size,date,time,name=columns
            link=''
            if mode[0]=='l':
                name,separator,link=name.partition(' -> ')
                if not separator:raise Refusal('Malformed symlink listing')
            kind={'-':'0','d':'5','l':'2'}.get(mode[0])
            if kind is None:raise Refusal('Unsupported coordinator tar type')
            result.append(dict(name=safe_name(name),bytes=int(size),type=kind,link=link))
    return result

def validate_registry(plan):
    registry=plan['runtime_registry'];root=Path(plan['private_runtime'])
    if root!=Path(plan['stage_root'])/'private_rt':raise Refusal('Private runtime must be stage_root/private_rt')
    if root.is_symlink() or root.resolve()!=root.absolute():raise Refusal('Private runtime crosses a symlink')
    from namespace228 import package_namespace
    from runtime228 import ABSOLUTE_LINKS
    package=package_namespace()
    if ABSOLUTE_LINKS!=package.S.RUNTIME_ABSOLUTE_LINKS:raise Refusal('Runtime link registry differs from sealed package')
    for name,row in registry.items():
        destination=None
        if name.startswith('sj/'):
            destination=str(package.SJ/name[3:])
        elif name.startswith('m/ap/'):
            destination=str(package.AP/name[5:])
        elif name=='fsw':destination=str(package.FSW)
        elif name not in ('x/pull.py','x/need_frames.txt'):raise Refusal('Unregistered runtime registry entry')
        kind='record_only' if destination is None else 'runtime'
        if row['namespace_path']!=destination or row['kind']!=kind or row['host_path']!=str(root/name):
            raise Refusal('Registry destination differs from package namespace')
    mapping={name:str(root/name) for name in registry}
    assets=read(HERE/'A10b/src/orchard_h10/vendor/ORCHARD_ASSETS.json')
    base=str(Path(assets['base_manifest']['path']).relative_to(package.AP)).split('/')[0]
    env=read(HERE/'evidence/q/env.json')
    environment=str(Path(env['python']).relative_to(package.AP)).split('/')[0]
    if 'm/ap/'+base not in registry or 'm/ap/'+environment not in registry:
        raise Refusal('Package base/environment receipt is absent from registry')
    if len(plan['runtime_archives'])!=len(assets['groups']):raise Refusal('Runtime archive group count differs')
    counts={name:0 for name in registry}
    for group,pins in zip(plan['runtime_archives'],assets['groups']):
        if [[p['path'],p['bytes'],p['sha256']] for p in group['parts']]!=pins:
            raise Refusal('Runtime archive parts differ from package receipt')
        if group['namespace_map']!=mapping or group['destination']!=str(root):
            raise Refusal('Runtime extraction mapping is not private')
        listing=HERE/group['member_list']['path'];checked(listing,group['member_list'])
        headers=list_headers(listing)
        if canonical(headers)!=group['member_headers_sha256']:raise Refusal('Runtime header digest differs')
        if sum(h['bytes'] for h in headers if h['type']=='0')!=group['expanded_bytes']:
            raise Refusal('Runtime listing size differs')
        for header in headers:
            runtime_path(header['name'],mapping)
            for prefix in sorted(registry,key=len,reverse=True):
                if header['name']==prefix or header['name'].startswith(prefix+'/'):
                    counts[prefix]+=1;break
    if counts!={name:row['members'] for name,row in registry.items()}:raise Refusal('Runtime registry count differs')
    for name,row in registry.items():
        for receipt in row['receipts']:checked(HERE/receipt['path'],receipt)
    return dict(passed=True,private_root=str(root),namespaces=registry,
                non_runtime=[dict(namespace=n,**row) for n,row in registry.items() if row['kind']=='record_only'])
