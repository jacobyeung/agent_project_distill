def selected400(name):
    import re
    name=name.removeprefix('files') if name.startswith('files/') else name
    parts=PurePosixPath(name).parts
    if name.startswith('/') and '6ed2c7aa' not in parts:return
    for part in parts:
        if part.startswith('checkpoint_'):
            raise ValueError('E83:'+name)
        match=re.fullmatch(r'(?:m|step[_-]?)(\d+)(?:_.*)?',part)
        if match and int(match[1])>400:raise ValueError('E83:'+name)

def small_archive(path,step=400,roots=None):
    values={};metadata={}
    with tarfile.open(path,'r:*') as t:
        members=t.getmembers()
        if len({m.name for m in members})!=len(members):raise ValueError('E14')
        try:manifest=json.load(t.extractfile('MANIFEST.json'))
        except (ValueError,UnicodeError) as error:raise ValueError('E50:MANIFEST.json') from error
        if step not in (400,600) or manifest['schema']!='r7-handover-small-files-v1' or manifest['run']!='6ed2c7aa' or manifest['step']!=step:
            raise ValueError('E15')
        entries={};expected={'MANIFEST.json'};seen=set()
        for item in manifest['files']:
            name='files'+item['path'];expected.add(name)
            if step==400:
                try:selected400(item['path'])
                except ValueError:continue
            entries[item['sha256']]=item
        # A manifest may retain provenance for unselected objects. None of
        # those objects is opened, extracted, or made an input dependency.
        present={m.name for m in members if m.isfile()}
        if present-expected or step==600 and present!=expected:raise ValueError('E18')
        def visit(value):
            if isinstance(value,dict):
                if isinstance(value.get('sha256'),str):
                    if step==400 and isinstance(value.get('path'),str):selected400(value['path'])
                    take(value['sha256'])
                for child in value.values():visit(child)
                if isinstance(value.get('files'),dict):
                    for name,h in value['files'].items():
                        if name.endswith(('.json','.txt','.jinja','.model')) and isinstance(h,str):take(h)
            elif isinstance(value,list):
                for child in value:visit(child)
        def take(h):
            if h in seen or h not in entries:return
            seen.add(h);item=entries[h];name='files'+item['path']
            m=t.getmember(name)
            if not m.isfile() or '..' in PurePosixPath(name).parts or m.size!=item['bytes'] or item.get('match') is not True:
                raise ValueError('E16')
            raw=t.extractfile(m).read()
            if hashlib.sha256(raw).hexdigest()!=h or item.get('pin') not in (None,h):raise ValueError('E17')
            values[h]=dict(member=name,original=item['path'],bytes=len(raw),sha256=h)
            if item['path'].endswith('.json'):
                try:metadata[h]=json.loads(raw)
                except (ValueError,UnicodeError):pass
            if roots is not None and h in metadata and PurePosixPath(item['path']).name!='RP.json':visit(metadata[h])
        if roots is None:
            for h in entries:take(h)
        else:visit(roots)
    return values,metadata
