"""Seal the local review artifact without copying external runtimes or data."""
from pathlib import Path
from .paths import ROOT,OFFKIT,C8,V1,R,B04,REVSI
from .io import dump,sha,tar_bytes

def sources():
    local=[ROOT/'native_read.py']+sorted((ROOT/'offnative').glob('*.py'))+sorted((ROOT/'kit/tests').glob('*.py'))
    local += [ROOT/n for n in ('RUN.md','SIZING.md','DIFF.md')]
    return local

def package():
    local=sources()
    raw=tar_bytes({str(p.relative_to(ROOT)):p.read_bytes() for p in local})
    archive=ROOT/'out/code.tar';archive.write_bytes(raw)
    pins=[]
    external=list(OFFKIT.joinpath('offkit').glob('*.py'))
    external += [V1/n for n in ('budget.py','engine.py','proof.py','venue.py')]
    external += [C8/n for n in ('nomdg.py','perception.py','reader_policy.py','geometry.py','gravity_guard.py')]
    external += [R/'kit/rebind.py',R/'kit/revsi/launcher/orchard_stage.py']
    external += [B04/'e2e_reader'/n for n in ('generate.py','callhook.py','artifact.py','servers.py','geometry.py')]
    external += [REVSI/'reader/evaluator'/n for n in ('scoring.py','metric.py','media.py','evalpath/official.py','evalpath/sampling.py')]
    for p in sorted(set(external)):
        pins.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    dump(ROOT/'out/DEPENDENCY_PINS.json',dict(read_only=True,files=pins))
    dump(ROOT/'out/CODE_PINS.json',dict(archive=dict(path='out/code.tar',sha256=sha(archive),bytes=len(raw)),
        files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in local]))
    return sha(archive)

if __name__=='__main__':print(package())
