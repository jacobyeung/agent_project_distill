"""Pin an ordered project-disk export and run preparation using Python 3 stdlib."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

LOGICAL = '/scratch/jjyeung/b01ec87a6f29b'
REVIEWED_OBJECT = 'q8/8865619b/673bc60f_m200.tar'
REVIEWED_ARCHIVE_BYTES = 10240
REVIEWED_ARCHIVE_SHA256 = '1d5e7d19ff349450031b8464dd1624eb46096c681c224bd0d46602cd7c9c3449'

MEMBERS = dict(artifact='artifact.json', heads='heads.pt',
               full_weights='full_weights/full_weights.json')


def write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class Parts:
    """Hash each part and the entire stream without a joined archive on disk."""
    def __init__(self, paths):
        self.paths = iter(paths); self.stream = None; self.parts = []
        self.digest = hashlib.sha256(); self.size = 0

    def read(self, size):
        if size < 0:raise ValueError('Bounded reads required')
        chunks = []; remaining = size
        while remaining:
            if self.stream is None:
                path = next(self.paths, None)
                if path is None:break
                self.path = Path(path).resolve(); self.stream = self.path.open('rb')
                self.part_hash = hashlib.sha256(); self.part_size = 0
            chunk = self.stream.read(remaining)
            if not chunk:
                self.parts.append(dict(path=str(self.path), bytes=self.part_size,
                                       sha256=self.part_hash.hexdigest()))
                self.stream.close(); self.stream = None
                continue
            self.digest.update(chunk); self.part_hash.update(chunk)
            self.size += len(chunk); self.part_size += len(chunk)
            chunks.append(chunk); remaining -= len(chunk)
        return b''.join(chunks)


def scan(paths, done, object_name):
    fields = Path(done).read_text().split()
    if (len(fields) != 3 or fields[0] != object_name or not fields[1].isdigit()
            or int(fields[1]) <= 0 or not re.fullmatch('[0-9a-f]{64}', fields[2])):
        raise ValueError('Invalid whole-tar .done receipt')
    stream = Parts(paths); files = {}; metadata = {}; seen = set(); total = 0
    try:
        with tarfile.open(fileobj=stream, mode='r|*') as archive:
            for entry in archive:
                path = PurePosixPath(entry.name); name = str(path)
                if path.is_absolute() or '..' in path.parts or name in seen:
                    raise ValueError('Unsafe or duplicate export member')
                seen.add(name)
                if entry.isdir():continue
                if not entry.isfile():raise ValueError('Export must contain regular files')
                total += entry.size
                wanted = path.name in ('artifact.json', 'full_weights.json')
                if wanted and entry.size > 4*1024**2:raise ValueError('Oversized metadata')
                digest = hashlib.sha256(); pieces = []; size = 0
                with archive.extractfile(entry) as source:
                    for chunk in iter(lambda: source.read(1024**2), b''):
                        digest.update(chunk); size += len(chunk)
                        if wanted:pieces.append(chunk)
                if size != entry.size:raise ValueError('Truncated member')
                files[name] = dict(bytes=size, sha256=digest.hexdigest())
                if wanted:metadata[name] = json.loads(b''.join(pieces))
        while stream.read(1024**2):pass
    finally:
        if stream.stream is not None:stream.stream.close()
    if stream.size != int(fields[1]) or stream.digest.hexdigest() != fields[2]:
        raise ValueError('Parts differ from whole-tar .done bytes or sha256')
    artifacts = [n for n in metadata if PurePosixPath(n).name == 'artifact.json']
    if len(artifacts) != 1:raise ValueError('Require exactly one export artifact')
    member = str(PurePosixPath(artifacts[0]).parent)
    if member == '.':raise ValueError('Export needs a member directory')
    result = {k:files[member+'/'+v] for k,v in MEMBERS.items()}
    artifact = metadata[artifacts[0]]
    for name in ('heads', 'full_weights'):
        if artifact[name]['sha256'] != result[name]['sha256']:
            raise ValueError('Artifact member hash differs: '+name)
    full = metadata[member+'/'+MEMBERS['full_weights']]
    if full.get('schema') != 'full-ft-export-v1' or full.get('dtype') != 'bfloat16':
        raise ValueError('Unsupported full-weights export')
    for item in full['files']+[full['index']]:
        if PurePosixPath(item['name']).name != item['name']:raise ValueError('Invalid weight name')
        actual = files[member+'/full_weights/'+item['name']]
        if actual['sha256'] != item['sha256'] or item.get('bytes',actual['bytes']) != actual['bytes']:
            raise ValueError('Weight pin differs: '+item['name'])
    archive = dict(destination='sj/b01ec87a6f29b/d', expanded_bytes=total,
                   parts=stream.parts, sha256=fields[2])
    return dict(member_directory=member, **result), artifact, archive


def preparation(config, receipt, data_receipt, artifact):
    raw = {k:Path(p).read_bytes() for k,p in
           dict(config=config,receipt=receipt,data_receipt=data_receipt).items()}
    cfg, rec, data = [json.loads(raw[k]) for k in ('config','receipt','data_receipt')]
    if (data.get('status') != 'PREPARED' or data.get('schema') != 's1-in-job-data-v1'
            or data.get('real_frames_verified') is not True or data.get('rehearsal') is not False
            or data.get('synthetic',False) is not False):
        raise ValueError('Data receipt status/schema/flags differ')
    if (data['config']['sha256'] != pin(raw['config'])['sha256']
            or data.get('preparation') != cfg.get('preparation')
            or cfg['preparation']['sha256'] != pin(raw['receipt'])['sha256']):
        raise ValueError('Data receipt config/preparation binding differs')
    if (rec.get('config_sha256') != artifact.get('config_sha256')
            or artifact.get('base_identity') != cfg.get('base_identity')
            or rec.get('frame_layout') != cfg.get('frame_layout')
            or artifact.get('frame_layout') != cfg.get('frame_layout')
            or cfg.get('frame_layout') != 'duplicate' or artifact.get('geometry_online')):
        raise ValueError('Export architecture or identity differs')
    sources = dict(config=data['config']['path'],receipt=cfg['preparation']['path'],
                   data_receipt=str(PurePosixPath(data['config']['path']).parent.parent/'data_receipt.json'))
    pins = {k:dict(path='p0/'+k+'.json',source_path=sources[k],**pin(v)) for k,v in raw.items()}
    return pins, raw



def reviewed_binding():
    package = Path(__file__).resolve().parent.parent
    if not (package/'0.tgz').is_file():package = Path(__file__).resolve().parent/'package'
    public = json.loads((package/'0.json').read_text())
    raw = (package/'0.tgz').read_bytes()
    if pin(raw)['sha256'] != public['payload_sha256']:raise ValueError('Reviewed payload differs')
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        cfg = json.load(archive.extractfile('9.json'))
    digest = hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest != public['plan_sha256']:raise ValueError('Reviewed plan differs')
    binding = dict(cfg['export_binding'])
    binding.update(archive_bytes=REVIEWED_ARCHIVE_BYTES, archive_sha256=REVIEWED_ARCHIVE_SHA256)
    return binding

def receipt_review(done):
    fields = Path(done).read_text().split()
    if fields != [REVIEWED_OBJECT, str(REVIEWED_ARCHIVE_BYTES), REVIEWED_ARCHIVE_SHA256]:
        raise ValueError('Reviewed whole-tar receipt differs')


def bind_review(a, export, artifact, archive, prep, binding):
    # These constants are sealed by the delivery manifest, independent of caller input.
    if (a.object != REVIEWED_OBJECT or archive.get('sha256') != REVIEWED_ARCHIVE_SHA256
            or sum(p['bytes'] for p in archive.get('parts', [])) != REVIEWED_ARCHIVE_BYTES):
        raise ValueError('Reviewed whole-tar identity differs')
    for key, expected in [('archive_bytes', REVIEWED_ARCHIVE_BYTES),
                          ('archive_sha256', REVIEWED_ARCHIVE_SHA256)]:
        if key in binding and binding[key] != expected:
            raise ValueError('Reviewed export binding differs: '+key)
    for key, actual in [('object',a.object),('step',a.step),('lineage',a.lineage),
                        ('member_directory',export['member_directory'])]:
        if actual != binding[key]:raise ValueError('Reviewed export binding differs: '+key)
    if artifact.get('step') != binding['step']:raise ValueError('Artifact step differs')
    for key in ('config_sha256','base_identity','frame_layout'):
        if artifact.get(key) != binding[key]:raise ValueError('Artifact identity differs: '+key)
    for name in ('heads','full_weights'):
        path = PurePosixPath(artifact[name]['path'])
        tail = PurePosixPath(binding['run'])/binding['member_directory']/MEMBERS[name]
        if path.parts[-len(tail.parts):] != tail.parts:raise ValueError('Artifact run/member path differs')
    for name, digest in binding['preparation_sha256'].items():
        if prep[name]['sha256'] != digest:raise ValueError('Reviewed preparation differs: '+name)
    export.update(run=binding['run'],object=binding['object'],config_sha256=binding['config_sha256'],
                  archive_sha256=archive['sha256'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parts',nargs='+',required=True); p.add_argument('--done',required=True)
    p.add_argument('--object',required=True); p.add_argument('--config',required=True)
    p.add_argument('--receipt',required=True); p.add_argument('--data-receipt',required=True)
    p.add_argument('--lineage',choices=('SFT','RL'),required=True);p.add_argument('--step',type=int,required=True)
    p.add_argument('--out',required=True);p.add_argument('--prep-tar',required=True)
    p.add_argument('--base-inputs',required=True);p.add_argument('--inputs-out',required=True)
    a = p.parse_args()
    binding=reviewed_binding()
    receipt_review(a.done)
    if (a.object != binding['object'] or a.step != binding['step'] or a.lineage != binding['lineage']):
        raise ValueError('Reviewed run/step/object differs')
    if len(a.parts) != 4:raise ValueError('Require four ordered parts')
    if a.step < 0:raise ValueError('Step must be nonnegative')
    # Refuse missing preparation files before scanning a multi-GB archive.
    for path in (a.config,a.receipt,a.data_receipt):
        if not Path(path).is_file():raise ValueError('Missing preparation file: '+path)
    export, artifact, archive = scan(a.parts,a.done,a.object)
    label = re.fullmatch(r'm(\d+)', PurePosixPath(export['member_directory']).name)
    if label and int(label.group(1)) != a.step:raise ValueError('Step label differs from export member directory')
    prep, raw = preparation(a.config,a.receipt,a.data_receipt,artifact)
    bind_review(a,export,artifact,archive,prep,binding)
    export.update(schema='h1-export-pins-v1',lineage=a.lineage,step=a.step,preparation=prep)
    with tarfile.open(a.prep_tar,'w') as tar:
        for name, data in raw.items():
            entry=tarfile.TarInfo(prep[name]['path']);entry.size=len(data);entry.mode=0o600
            tar.addfile(entry,io.BytesIO(data))
    write(a.out,export)
    inputs=json.loads(Path(a.base_inputs).read_text())
    inputs['archives'][0]=archive
    prep_archive=dict(path=str(Path(a.prep_tar).resolve()),**pin(Path(a.prep_tar).read_bytes()))
    inputs['archives'][4]=dict(destination=archive['destination'],parts=[prep_archive],
                                   sha256=prep_archive['sha256'],expanded_bytes=sum(map(len,raw.values())))
    for name, member in MEMBERS.items():
        inputs['files'][name]=dict(path=LOGICAL+'/d/'+export['member_directory']+'/'+member,**export[name])
    inputs['export_pin']=dict(path='a/export.json',**pin(Path(a.out).read_bytes()))
    # Preserve the reviewed item selection from the base input plan.
    inputs['resume']=None
    write(a.inputs_out,inputs)


if __name__ == '__main__':main()
