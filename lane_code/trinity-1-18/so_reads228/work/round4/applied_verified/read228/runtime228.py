"""Two-pass private runtime extraction; compatible with the target's Python 3.6."""
import hashlib
import os
from pathlib import Path
import stat
import tarfile
from common228 import Refusal, beneath, local, sha

AP='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap'
FSW='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
UV='/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu'
ABSOLUTE_LINKS={
    'sj/envs/p1cpu/bin/python3.12':'/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12',
    'm/ap/19252904/e/bin/python':UV+'/bin/python3.12'}
CPYTHON='sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12'

def safe_name(name):
    path=Path(name)
    if not name or '\x00' in name or path.is_absolute() or '..' in path.parts:
        raise Refusal('Unsafe runtime member: '+name)
    return str(path)

def runtime_path(name,mapping):
    path=Path(safe_name(name))
    for prefix in sorted(mapping,key=len,reverse=True):
        if beneath(path,prefix):return Path(mapping[prefix])/path.relative_to(prefix)
    if any(beneath(Path(prefix),path) for prefix in mapping):return None
    raise Refusal('Unregistered runtime namespace: '+name)

def link_name(name,link):
    if not link or '\x00' in link:raise Refusal('Unsafe runtime link')
    if Path(link).is_absolute():
        if ABSOLUTE_LINKS.get(name)!=link:raise Refusal('Unregistered absolute runtime link: '+name)
        return CPYTHON
    target=os.path.normpath(str(Path(name).parent/link))
    if target=='..' or target.startswith('../'):raise Refusal('Runtime link escapes private root: '+name)
    return target

def runtime_link(name,link,mapping):
    return runtime_path(link_name(name,link),mapping)

def check_parents(target,cache=None):
    # lstat every existing ancestor; never traverse a symlink or special node.
    for parent in reversed(target.parents):
        if cache is not None and parent in cache:continue
        if parent.is_symlink():raise Refusal('Runtime parent crosses a symlink: '+str(parent))
        if parent.exists() and not parent.is_dir():raise Refusal('Runtime parent is not a directory: '+str(parent))
        if cache is not None:cache.add(parent)
    # A lexical local-root check suffices after every ancestor was checked above.
    if not beneath(target.absolute(),'/scratch/jjyeung'):raise Refusal('Runtime destination must be local scratch')

def check_existing(target,spec,parent_cache=None):
    check_parents(target,parent_cache)
    if not target.exists() and not target.is_symlink():return
    mode=target.lstat().st_mode
    if spec.get('directory'):
        same=stat.S_ISDIR(mode)
    elif 'link' in spec:
        same=stat.S_ISLNK(mode) and os.readlink(str(target))==spec['link']
    else:
        same=stat.S_ISREG(mode) and target.stat().st_size==spec['bytes'] and sha(target)==spec['sha256']
    if not same:raise Refusal('Existing runtime member conflicts; preserved: '+str(target))

def validate_topology(claims,names,mapping):
    # Check all archives together, so a late link cannot redirect an earlier file.
    for name,target in names.items():
        for parent in Path(name).parents:
            physical=names.get(str(parent))
            if physical and not claims[physical].get('directory'):
                raise Refusal('Runtime member parent is a file or symlink: '+name)
    links={name:claims[target]['link'] for name,target in names.items() if 'link' in claims[target]}
    def resolve(name,seen):
        pieces=Path(name).parts
        for i in range(1,len(pieces)+1):
            prefix=str(Path(*pieces[:i]))
            link=links.get(prefix)
            physical=runtime_path(prefix,mapping)
            if link is None and physical is not None and physical.is_symlink():link=os.readlink(str(physical))
            if link is not None:
                if prefix in seen:raise Refusal('Runtime symlink cycle: '+prefix)
                next_name=str(Path(link_name(prefix,link),*pieces[i:]))
                runtime_path(next_name,mapping)
                return resolve(next_name,seen|{prefix})
        runtime_path(name,mapping)
        return name
    for name,link in links.items():resolve(link_name(name,link),{name})

def scan_group(group,archive_mapping,limit,claims,names,parent_cache):
    """Read all headers AND bodies/pins without creating even the destination root."""
    from stage228 import PartStream
    stream=PartStream(group['parts'],archive_mapping);members=[];inventory={};seen=set();total=0
    mapping=group['namespace_map']
    try:
        with tarfile.open(fileobj=stream,mode='r|*') as archive:
            for member in archive:
                name=safe_name(member.name)
                if name in seen:raise Refusal('Duplicate runtime member: '+name)
                seen.add(name)
                if len(seen)>200000 or member.size<0:raise Refusal('Invalid runtime inventory')
                if not (member.isdir() or member.isfile() or member.issym()):
                    raise Refusal('Unsafe runtime type (only file/dir/symlink): '+name)
                target=runtime_path(name,mapping)
                members.append(dict(name=name,bytes=member.size,type=member.type.decode('ascii'),link=member.linkname))
                if target is None:
                    if not member.isdir():raise Refusal('Namespace parent must be a directory')
                    continue
                if member.isdir():spec=dict(directory=True)
                elif member.issym():
                    if runtime_link(name,member.linkname,mapping) is None:raise Refusal('Runtime link targets namespace parent')
                    spec=dict(link=member.linkname)
                else:
                    total+=member.size
                    if total>limit:raise Refusal('Runtime expansion exceeds aggregate allowance')
                    digest=hashlib.sha256();count=0
                    with archive.extractfile(member) as source:
                        for block in iter(lambda:source.read(1024*1024),b''):digest.update(block);count+=len(block)
                    if count!=member.size:raise Refusal('Truncated runtime member')
                    spec=dict(bytes=count,sha256=digest.hexdigest())
                key=str(target)
                if key in claims and claims[key]!=spec:raise Refusal('Runtime groups disagree on a member: '+name)
                check_existing(target,spec,parent_cache)
                claims[key]=spec;names[name]=key
                if not member.isdir():inventory[key]=spec
        while stream.read(1024*1024):pass
        if group.get('sha256') and group['sha256']!=stream.digest.hexdigest():raise Refusal('Runtime archive hash differs')
        if 'expanded_bytes' in group and total!=group['expanded_bytes']:raise Refusal('Runtime expanded size differs')
        if 'member_headers_sha256' in group:
            from common228 import canonical
            if canonical(members)!=group['member_headers_sha256']:raise Refusal('Runtime headers differ from coordinator lists')
    finally:stream.close()
    return dict(files=inventory,members=members,expanded_bytes=total,archive_sha256=stream.digest.hexdigest())

def preflight_runtime(groups,archive_mapping,*,limit):
    claims={};names={};results={};files={};total=0;mapping={};parent_cache=set()
    for index,group in enumerate(groups):
        for key,value in group['namespace_map'].items():
            if key in mapping and mapping[key]!=value:raise Refusal('Runtime namespace mappings disagree')
            mapping[key]=value
        got=scan_group(group,archive_mapping,limit-total,claims,names,parent_cache)
        total+=got['expanded_bytes'];files.update(got['files'])
        results[group.get('id',str(index))]=got
    validate_topology(claims,names,mapping)
    return dict(files=files,groups=results,expanded_bytes=total,passed=True,passes=2)

def apply_group(group,archive_mapping,proof):
    from stage228 import PartStream
    stream=PartStream(group['parts'],archive_mapping);members=[]
    try:
        with tarfile.open(fileobj=stream,mode='r|*') as archive:
            for member in archive:
                name=safe_name(member.name)
                row=dict(name=name,bytes=member.size,type=member.type.decode('ascii'),link=member.linkname)
                index=len(members)
                if index>=len(proof['members']) or row!=proof['members'][index]:raise Refusal('Runtime changed after preflight')
                members.append(row);target=runtime_path(name,group['namespace_map'])
                if target is None:continue
                spec=dict(directory=True) if member.isdir() else proof['files'][str(target)]
                check_existing(target,spec)
                if member.isdir():target.mkdir(parents=True,exist_ok=True);continue
                target.parent.mkdir(parents=True,exist_ok=True)
                if member.issym():
                    if not target.is_symlink():target.symlink_to(member.linkname)
                    continue
                exists=target.exists();digest=hashlib.sha256();count=0
                output=None if exists else target.open('xb')
                try:
                    with archive.extractfile(member) as source:
                        for block in iter(lambda:source.read(1024*1024),b''):
                            digest.update(block);count+=len(block)
                            if output is not None:output.write(block)
                finally:
                    if output is not None:output.close()
                if dict(bytes=count,sha256=digest.hexdigest())!=spec:raise Refusal('Runtime changed during extraction')
                if not exists:target.chmod(member.mode&0o777)
        while stream.read(1024*1024):pass
        if members!=proof['members'] or stream.digest.hexdigest()!=proof['archive_sha256']:
            raise Refusal('Runtime changed after preflight; stop without retry')
    finally:stream.close()

def extract_runtimes(groups,archive_mapping,*,limit):
    proof=preflight_runtime(groups,archive_mapping,limit=limit)
    # This is the only mutation boundary: ALL archives have passed first.
    for index,group in enumerate(groups):apply_group(group,archive_mapping,proof['groups'][group.get('id',str(index))])
    return proof

def extract_runtime(group,archive_mapping,*,limit):
    proof=extract_runtimes([group],archive_mapping,limit=limit)
    return proof['groups'][group.get('id','0')]

def relocate_runtime(plan,*,enabled=False):
    raise Refusal('Runtime relocation is OFF and unavailable: use the package namespace; pinned bytes must remain unchanged')
