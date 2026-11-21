"""Recover a completed shell failure through authenticated pool publication."""
import tempfile


def recover(shared, job):
    shared=Path(shared)
    records=(shared/'a/21').read_text().splitlines()
    status=records[-1].split()
    if len(status)!=3 or status[2]!=job or int(status[0])==0:raise ValueError('E81')
    lines=['E82 '+record for record in records[-2:] if record.split()[2:]==[job]]
    for name in ('19','24'):
        with (shared/'a'/name).open('rb') as stream:
            stream.seek(0,2);size=stream.tell();stream.seek(max(0,size-8192))
            lines.append(name+': '+stream.read(8192).decode('utf-8','replace'))
        if size>=524288:lines.append('E83 '+name)
    for name in ('14.json','16.json'):
        path=shared/'a'/name
        if path.exists():
            value=json.loads(path.read_bytes())
            if set(value)=={'a0'}:value=json.loads(bytes.fromhex(value['a0']))
            lines.extend(value['lines'][-200:])
    parent=Path(tempfile.mkdtemp(prefix='a'+job))
    os.environ['SLURM_JOB_ID']=job
    supervise(parent/'0',b'',failure='\n'.join(lines))
