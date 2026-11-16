"""Pinned reserve rooms, applied equally to rows, frames and cached features."""
import hashlib
import json
from pathlib import Path
import re

SHA256 = 'f7c458176426e22a13e47908b03abd2c6f5939d3e48eb7c24e7eba45b75ad479'
DATASETS = {'scannet':'d1', 'scannetpp':'d2', 'arkitscenes':'d3'}


def aliases(ds, native):
    ds = {'scannetppv2':'scannetpp', 'd1':'scannet', 'd2':'scannetpp','d3':'arkitscenes'}.get(ds,ds)
    d = DATASETS[ds]
    ns = {'scannetpp':'scannetppv2'}.get(ds,ds)
    names = {d+'/'+native, ds+'/'+native, ns+'/'+native}
    for family in ('v590kgt scene','rung1 scene','rung2 scene'):
        for namespace in ({ns,ds,'scannetpp','scannetppv2'} if ds=='scannetpp' else {ns}):
            token = 'v'+hashlib.sha256((family+' '+namespace+'/'+native).encode()).hexdigest()[:12]
            names.update(prefix+'/'+token for prefix in (d, ds, ns))
    if ds == 'arkitscenes':
        token='v'+hashlib.sha256(('arkitscenes/'+native).encode()).hexdigest()[:12]
        names.update(prefix+'/'+token for prefix in (d,ds))
    return names


class Reserve:
    def __init__(self, path=None):
        path = Path(path) if path else Path(__file__).with_name('r0_scenes.json')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != SHA256: raise ValueError('r0_authority_sha_mismatch')
        value = json.loads(raw)
        self.names = set()
        self.rooms = set()
        for capture in value['captures']:
            ds,native = capture.split('/',1)
            self.names.update(aliases(ds,native))
            if ds == 'scannet': self.rooms.add(re.sub(r'_\d\d$', '', native))

    def matches(self, value):
        names = set()
        def visit(v):
            if isinstance(v, dict):
                if isinstance(v.get('dataset'),str) and isinstance(v.get('scene'),str):
                    names.add(v['dataset']+'/'+v['scene'])
                for x in v.values(): visit(x)
            elif isinstance(v, list):
                for x in v: visit(x)
            elif isinstance(v,str):
                names.add(v)
                names.update(re.findall(r'(?:d[123]|scannetppv2|scannetpp|scannet|arkitscenes)/[\w.-]+',v))
                if re.search(r'\bscene\d+_\d\d\b', v):
                    names.update('scannet/'+s for s in re.findall(r'\bscene\d+_\d\d\b',v))
        visit(value)
        hits = names & self.names
        hits.update(n for n in names if n.startswith(('scannet/','d1/')) and
                    re.sub(r'_\d\d$','',n.split('/')[-1]) in self.rooms)
        return sorted(hits)

    def check(self, value, stream):
        hits = self.matches(value)
        if hits: raise ValueError('r0_room_refused:'+stream+':'+','.join(hits))
        return value
