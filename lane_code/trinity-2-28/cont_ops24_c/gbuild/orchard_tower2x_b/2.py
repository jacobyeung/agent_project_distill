import contextlib
import hashlib
import importlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time


def digest(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(p, value):
    raw = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) >= 5_000_000:
        raise ValueError('E01')
    with Path(p).open('xb') as f:
        f.write(raw)
    return raw


def binding(row, arm):
    a = row['x4'][arm]
    if a is None:
        return None
    ids, hashes, slots = a['x0'], a['x1'], a['x2']
    if (len(ids) != (32, 63, 94, 32)[arm] or ids != sorted(set(ids))
            or len(hashes) != len(ids) or len(slots) != 32 or slots != sorted(set(slots))
            or slots[0] != 0 or slots[-1] >= len(ids)
            or [ids[s] for s in slots] != row['x4'][0]['x0']
            or any(len(a[k]) != len(ids) for k in ('x3','x5','x6'))):
        raise ValueError('E02')
    anchors = row['x4'][0]['x0']
    expected = anchors if arm in (0,3) else sorted(anchors+[
        round(x+j*(y-x)/6) for x,y in zip(anchors,anchors[1:]) for j in ((3,) if arm==1 else (2,4))])
    if ids != expected:
        raise ValueError('E03')
    return ids, hashes, slots


def tasks(cfg):
    return [(r,a) for a in cfg['xr'] for r in range(len(cfg['x3'])) if cfg['x3'][r]['x4'][a] is not None]


def cost(cfg, a):
    return cfg['x7'][2]*cfg['x7'][3+(0 if a==3 else a)]+cfg['xs']


def forecast(cfg):
    return cfg['x7'][0]+cfg['x7'][1]+sum(cost(cfg,a) for _,a in tasks(cfg)[:cfg['xq']])+cfg['x7'][6]


def adapt(cfg):
    names=(cfg['xa'][0],cfg['xm'][5],cfg['xa'][4])
    mods={}
    for i in (2,1,0):
        name=names[i]
        old,new,count=cfg['xp'][i]
        mod=importlib.import_module(name)
        p=Path(mod.__file__)
        if digest(p)!=cfg['x9'][i][1]:
            raise ValueError('E04')
        raw=p.read_text()
        if raw.count(old)!=count:
            raise ValueError('E05')
        exec(compile(raw.replace(old,new),str(p),'exec'),mod.__dict__)
        mods[i]=mod
    return mods[0]


def images(cfg, row, arm):
    import numpy as np
    from PIL import Image
    a = row['x4'][arm]
    frames, raw_hashes = [], []
    started = time.monotonic()
    for h, name, low, expected in zip(a['x1'],a['x3'],a['x5'],a['x6']):
        root = Path(cfg['xl'] if low else cfg['xc'])
        p = root/name
        if p.is_absolute() and not p.is_relative_to(root) or '..' in Path(name).parts:
            raise ValueError('E06')
        if digest(p) != h:
            raise ValueError('E07')
        with Image.open(p) as im:
            im.load()
            im = im.convert('RGB')
            if low:
                if im.size != (256,192):
                    raise ValueError('E08')
                im = Image.fromarray(np.ascontiguousarray(np.rot90(np.asarray(im),row['x6'])))
                if cfg['xk'][0] == 0:
                    im = im.resize(tuple(reversed(row['x5'])),cfg['xk'][1])
                else:
                    cv = importlib.import_module(cfg['xk'][2])
                    cv.setNumThreads(1)
                    im = Image.fromarray(cv.resize(np.asarray(im),tuple(reversed(row['x5'])),interpolation=cfg['xk'][1]))
            if [im.height,im.width] != row['x5']:
                raise ValueError('E09')
            raw_hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
            if raw_hashes[-1] != expected:
                raise ValueError('E10')
            frames.append(im.copy())
    return frames, raw_hashes, time.monotonic()-started


class Engine:
    def __init__(self, cfg, stub):
        self.cfg,self.stub = cfg,stub
        for p in cfg['x8']:
            sys.path.insert(0,p)
        self.np = importlib.import_module('numpy')
        self.pt = importlib.import_module('torch')
        self.pt.set_num_threads(8)
        for p,h in cfg['x9']:
            if digest(p)!=h:
                raise ValueError('E11')
        self.mod = adapt(cfg)
        z = cfg['xa']
        if getattr(self.mod,z[1])!=z[2]:
            raise ValueError('E12')
        self.convert = getattr(importlib.import_module(z[4]),z[5])
        if stub:
            self.unit = self.fake()
        else:
            if self.pt.cuda.device_count()!=1 or 'H100' not in self.pt.cuda.get_device_name(0):
                raise ValueError('E13')
            self.unit = getattr(self.mod,z[3])(cfg['xb'])
            self.unit._load()

    def fake(self):
        pt,z = self.pt,self.cfg['xm']
        class F(pt.nn.Module):
            def __init__(self, local):
                super().__init__()
                self.local = local
            def forward(self, value):
                n = value[0].shape[1]
                vals = [0.,0.,0.,1.,1.,1.2] if self.local else [0.,0.,0.,0.,1.]
                out = pt.tensor(vals).repeat(1,n,1)
                if not self.local:
                    out[0,:,0] = pt.arange(n)/100
                    out[0,:,1] = pt.sin(pt.arange(n)/10)/10
                return [out]
        class D(pt.nn.Module):
            def forward(self, small, images, **kw):
                shape = (1,images.shape[1],518,518)
                return pt.ones(*shape,1),pt.ones(shape)
        unit = pt.nn.Module()
        for key,value in zip(z[:5],[pt.nn.Identity(),F(True),F(False),D(),None]):
            setattr(unit,key,value)
        def aggregate(_, inputs):
            n = inputs.shape[1]
            if tuple(inputs.shape)!=(1,n,3,518,518) or not pt.isfinite(inputs).all():
                raise ValueError('E14')
            blocks=[None]*24
            for k in (4,11,17,23):
                blocks[k]=pt.zeros(1,n,1,1)
            return blocks,0
        setattr(importlib.import_module(z[5]),z[6],aggregate)
        settings = dict(self.cfg['xb'],device='cpu')
        return getattr(self.mod,self.cfg['xa'][3])(settings,module=unit)

    def run(self, row, arm):
        ids,hashes,slots = binding(row,arm)
        start = time.monotonic()
        frames,raw_hashes,decode_seconds = images(self.cfg,row,arm)
        z = self.cfg['xd']
        setattr(self.unit,z[0],len(ids))
        if not self.stub:
            self.pt.cuda.reset_peak_memory_stats()
        batch = {z[1]:frames,z[2]:self.np.array(ids),z[3]:self.np.array(slots),
                 z[4]:self.np.array(row['x4'][0]['x0'])}
        before = time.monotonic()
        value = self.unit.run(batch)
        if getattr(value,z[5]).shape != (len(ids),9):
            raise ValueError('E15')
        r,t,_ = self.convert(getattr(value,z[5]),self.np.asarray(row['x2']))
        c = self.np.tile(self.np.eye(4),(len(ids),1,1))
        c[:,:3,:3],c[:,:3,3] = r,t*row['x1']
        if not self.stub:
            self.pt.cuda.synchronize()
        return dict(status='ok',ids=ids,sha256=hashes,raw_sha256=raw_hashes,slots=slots,c2w=c.tolist(),
                    scale=row['x1'],gravity=row['x2'],seconds=time.monotonic()-start,
                    decode_seconds=decode_seconds,inference_seconds=time.monotonic()-before,
                    shape=[len(ids),row['x5'][0],row['x5'][1],3],
                    peak_bytes=0 if self.stub else self.pt.cuda.max_memory_allocated(),
                    reserved_bytes=0 if self.stub else self.pt.cuda.max_memory_reserved(),
                    rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def run(cfg, stub=False, only=None):
    started=time.monotonic()
    if forecast(cfg)>1500 or cfg['xq']<1 or not cfg['xt']:
        raise ValueError('E16')
    rows=cfg['x3'][:only]
    result=dict(schema=2,token=cfg['x0'],stub=stub,rows=[dict(key=r['x0'],arms=[
        dict(status='unavailable' if a is None else 'budget') for a in r['x4']]) for r in rows],
        complete=False,finished=False,estimate_seconds=forecast(cfg),error=None,ran=[])
    try:
        before=time.monotonic()
        engine=Engine(cfg,stub)
        result['load_seconds']=time.monotonic()-before
        result['load_peak_bytes']=0 if stub else engine.pt.cuda.max_memory_allocated()
        result['load_reserved_bytes']=0 if stub else engine.pt.cuda.max_memory_reserved()
        end=cfg.get('xe',time.time()+1800)
        stop=False
        for a in cfg['xr']:
            for i,row in enumerate(rows):
                if row['x4'][a] is None:
                    continue
                allowance=cost(cfg,a)
                actual=[v['seconds'] for rr in result['rows'] for v in rr['arms'] if v['status']=='ok']
                if actual:
                    allowance=max(allowance,max(actual)*1.5)
                if not stub and time.time()+allowance+cfg['x7'][6]>end:
                    stop=True
                    break
                result['rows'][i]['arms'][a]=engine.run(row,a)
                result['ran'].append([i,a])
            if stop:
                break
        result['complete']=all(v['status'] in ('ok','unavailable') for r in result['rows'] for v in r['arms'])
        result['finished']=True
    except Exception as e:
        result['error']=type(e).__name__
        if isinstance(e,TimeoutError):
            result['finished']=True
    result['seconds']=time.monotonic()-started
    return result


def main():
    p,out=map(Path,sys.argv[1:3])
    cfg=json.loads(p.read_text())
    stub=len(sys.argv)==4 and sys.argv[3]=='0'
    def alarm(*args):
        raise TimeoutError('E17')
    if not stub and 'xe' in cfg:
        signal.signal(signal.SIGALRM,alarm)
        signal.alarm(max(1,int(cfg['xe']-time.time()-60)))
    with open(os.devnull,'w') as sink,contextlib.redirect_stdout(sink),contextlib.redirect_stderr(sink):
        value=run(cfg,stub=stub,only=1 if stub else None)
    signal.alarm(0)
    raw=write(out,value)
    write(out.with_suffix('.1.json'),dict(schema=2,token=cfg['x0'],input_sha256=digest(p),
        sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),complete=value['complete'],stub=stub,
        job=os.environ.get('SLURM_JOB_ID','0')))
    return 0 if value['finished'] else 1


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('E99',file=sys.stderr)
        raise SystemExit(1)
