"""Authenticate candidate training metadata without rewriting signed bytes."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
import sys
import tarfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from guard_core import digest, read, sha, write

ROOT = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/'
TREE_SHA = 'b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'
ARCHIVE_SHA = '845b17895e466671bc5c5ecdb6a5a5d697a43a5e02d07d1555b11be74f8fd415'
BASE_ARTIFACT_SHA = '1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
CONFIG_ID = '4bc5442c5c9ff12e7407c173c2d1bd6f8a87ab75a298ae71cabbe2053c42bf3c'
MAX_BYTES = 64*1024*1024

def members(path):
    result = {}; total = 0; seen = set()
    with tarfile.open(path, 'r:') as archive:
        for m in archive:
            p = PurePosixPath(m.name)
            if (p.is_absolute() or '..' in p.parts or not p.parts or str(p) in seen
                    or not (m.isfile() or m.isdir()) or len(seen) >= 10000):
                raise ValueError('Closure has an unsafe, repeated or linked member')
            seen.add(str(p))
            if m.isdir(): continue
            total += m.size
            if m.size > 16*1024*1024 or total > MAX_BYTES:
                raise ValueError('Closure exceeds its small metadata limit')
            if p.parts[0] not in ('runs', 'k'):
                raise ValueError('Closure has an unexpected member root')
            if p.parts[0] == 'runs' and (len(p.parts) < 3 or p.parts[1] != '359fcc3c'):
                raise ValueError('Closure belongs to a foreign run')
            result[str(p)] = archive.extractfile(m).read()
    return result

def load_member(files, name):
    if name not in files: raise ValueError('Missing closure member: '+name)
    return json.loads(files[name])

def pin_member(files, pin):
    if set(pin) != {'path','sha256'} or not pin['path'].startswith(ROOT):
        raise ValueError('Closure pin is outside the admitted run root')
    name = pin['path'][len(ROOT):]
    if '..' in PurePosixPath(name).parts or name not in files:
        raise ValueError('Missing closure pin: '+name)
    if hashlib.sha256(files[name]).hexdigest() != pin['sha256']:
        raise ValueError('Closure member digest differs: '+name)
    return load_member(files,name)

def authenticate(files, step, trainer, baseline_artifact, exported=None):
    """Use the imported, unchanged trainer.identity; the runtime repeats restoration."""
    if type(step) is not int or step <= 0: raise ValueError('Invalid closure step')
    name = f'runs/359fcc3c/m{step}/artifact.json'
    raw = files.get(name)
    if raw is None: raise ValueError('Closure lacks the requested step artifact')
    if exported is not None and raw != Path(exported).read_bytes():
        raise ValueError('Export artifact is not byte-equal to the closure artifact')
    art = load_member(files,name)
    if art.get('step') != step or art.get('trained_groups',{}).get('step') != step:
        raise ValueError('Closure artifact belongs to a foreign step')
    data = load_member(files,'runs/359fcc3c/inputs/data_receipt.json')
    cfg = pin_member(files,data['config'])
    prep = pin_member(files,cfg['preparation'])
    code = pin_member(files,cfg['code'])
    binding = load_member(files,'runs/359fcc3c/binding.json')
    identity = trainer.identity(cfg)
    if identity != CONFIG_ID or any(x.get('config_sha256') != identity for x in (art,prep,binding)):
        raise ValueError('Candidate training config identity differs')
    if data.get('preparation') != cfg['preparation'] or binding.get('preparation') != cfg['preparation']:
        raise ValueError('Preparation receipt binding differs')
    if (binding.get('trainer_commit') != 'sha256:'+TREE_SHA or binding.get('world_size') != cfg.get('world_size')
            or code.get('tree_sha256') != TREE_SHA or digest(code.get('files')) != TREE_SHA
            or code.get('archive',{}).get('sha256') != ARCHIVE_SHA):
        raise ValueError('Candidate trainer differs from the backend source tree')
    from student_pilot import source_seal
    source_seal.check_binding(prep.get('source_seal'),code,identity)
    source_seal.check_export(prep,art)
    if art.get('training_source_seal') != prep.get('source_seal'):
        raise ValueError('Training source seal differs')
    if sha(baseline_artifact) != BASE_ARTIFACT_SHA:
        raise ValueError('Baseline artifact identity differs')
    base = read(baseline_artifact)
    groups = art['trained_groups']['groups']; old = base['trained_groups']['groups']
    if set(groups) != set(old): raise ValueError('Trained-group membership differs')
    chain = {}
    for group in groups:
        g, b = groups[group],old[group]
        if (g['initial_sha256'] != b['final_sha256'] or g['names'] != b['names']
                or type(g.get('gradient_steps')) is not int or not 0 < g['gradient_steps'] <= step
                or g.get('changed') is not True or g.get('nonzero') is not True):
            raise ValueError('Trained-group chain differs: '+group)
        chain[group] = dict(initial_sha256=g['initial_sha256'],baseline_final_sha256=b['final_sha256'])
    init = cfg.get('init_artifact',{})
    if init.get('artifact',{}).get('sha256') != BASE_ARTIFACT_SHA or set(init.get('heads',[])) != set(groups) or init.get('lm') != 'full':
        raise ValueError('Candidate initialization does not bind the baseline')
    for field in ('base_identity','carrier_position_policy','depth_backing','frame_layout','placement',
                  'pose_backing','trace_program_version','trace_version_binding','training_mode','anchors'):
        if art.get(field) != base.get(field): raise ValueError('Inference artifact contract differs: '+field)
    return dict(status='PASS',step=step,config_identity=identity,artifact_sha256=hashlib.sha256(raw).hexdigest(),
                config=data['config'],data_receipt=dict(path=ROOT+'runs/359fcc3c/inputs/data_receipt.json',
                    sha256=hashlib.sha256(files['runs/359fcc3c/inputs/data_receipt.json']).hexdigest()),
                preparation=cfg['preparation'],source_tree=TREE_SHA,trained_group_chain=chain,
                binding_sha256=hashlib.sha256(files['runs/359fcc3c/binding.json']).hexdigest(),
                tensor_restore_checked=False)

def pack(source, destination, step, trainer, baseline_artifact):
    files = members(source)
    admission = authenticate(files,step,trainer,baseline_artifact)
    dest = Path(destination); dest.mkdir(parents=True,exist_ok=False)
    inventory = {}; reverse = {}
    with tarfile.open(dest/'metadata.tar','x') as archive:
        for name,raw in sorted(files.items()):
            # Same file bytes and run-relative hierarchy, with opaque component names.
            neutral = '/'.join('a'+hashlib.sha256(p.encode()).hexdigest()[:20] for p in PurePosixPath(name).parts)
            if neutral in reverse: raise ValueError('Archive alias collision')
            reverse[neutral] = name
            entry = tarfile.TarInfo(neutral); entry.size=len(raw);entry.mode=0o644
            archive.addfile(entry,io.BytesIO(raw))
            inventory[neutral] = dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    descriptor = dict(schema='g2-closure-v1',step=step,source_sha256=sha(source),
        archive=dict(path=str((dest/'metadata.tar').resolve()),bytes=(dest/'metadata.tar').stat().st_size,
                     sha256=sha(dest/'metadata.tar')),members=inventory,aliases=reverse,admission=admission)
    write(dest/'CLOSURE.json',descriptor)
    return descriptor

def unpack(descriptor, destination):
    from guard_core import verify_archive
    archive=descriptor['archive'];verify_archive(archive['path'],archive)
    dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    actual={}; files={}
    with tarfile.open(archive['path'],'r:') as tar:
        for m in tar:
            if not m.isfile() or m.name in actual or m.name not in descriptor['members']:
                raise ValueError('Candidate metadata inventory differs')
            raw=tar.extractfile(m).read();actual[m.name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            name=descriptor['aliases'][m.name];p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts: raise ValueError('Unsafe closure alias')
            target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);files[name]=raw
    if actual != descriptor['members']: raise ValueError('Candidate metadata member hashes differ')
    return files

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for name in ('source','out','trainer','baseline'):p.add_argument('--'+name,required=True)
    p.add_argument('--step',type=int,required=True);a=p.parse_args()
    sys.path.insert(0,a.trainer)
    from student_pilot import carrier_c1_run as trainer
    pack(a.source,a.out,a.step,trainer,a.baseline)
