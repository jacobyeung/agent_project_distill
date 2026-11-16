"""Repack the step-544 stop export inside a job (stdlib only).
Reads the four GCS part objects of SOURCE (M544_SOURCE.json: names, generations, sha256, bytes; whole-archive sha256)
as one stream with the Orchard gcloud configuration, renames members m544/<x> -> ap/8865619b/runs/469ddece/m544/<x> and
m544/artifact.json -> ap/<ART_DIR>/m544/artifact.json, and writes one tar on node-local WORK. It verifies every part, the
whole stream, the artifact, heads and full_weights.json pins of the artifact and every member that manifest lists, then
copies the tar to its project path (DEST, written as DEST.partial and renamed) and, if GCS_OBJECT is given, uploads it.
Writes REPACK.json (member sha256s, tar sha256, sizes, timings) to RECEIPT. No retry: any failure exits nonzero.
Usage: repack_m544.py SOURCE.json ART_DIR WORK_DIR DEST RECEIPT [GCS_OBJECT]"""
import base64, hashlib, io, json, os, re, shutil, subprocess, sys, tarfile, time
from pathlib import Path

BUCKET = 'gs://cmu-gpucloud-jjyeung/'
OLD = 'ap/8865619b/runs/469ddece/'
AS = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
ENV = dict(os.environ, CLOUDSDK_CONFIG=os.environ.get('CLOUDSDK_CONFIG', '/project/community/jjyeung/gcloud'),
           CLOUDSDK_CORE_DISABLE_FILE_LOGGING='1', CLOUDSDK_CORE_DISABLE_PROMPTS='1',
           CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK='1', CLOUDSDK_CORE_DISABLE_USAGE_REPORTING='1',
           CLOUDSDK_STORAGE_PARALLEL_COMPOSITE_UPLOAD_ENABLED='False')  # one non-composite object, so GCS keeps its md5
SOURCE_CMD = os.environ.get('REPACK_SOURCE_CMD')  # tests only: a command template with {name}; production uses gcloud

class Parts(io.RawIOBase):
    """The concatenated part objects, hashed per part and as a whole while read."""
    def __init__(self, parts):
        self.parts, self.i, self.proc, self.part_hash, self.whole, self.count, self.seen = parts, -1, None, None, hashlib.sha256(), 0, []
        self.next()
    def next(self):
        if self.proc is not None:
            rest = self.proc.stdout.read()
            if rest: raise SystemExit('part longer than expected: ' + self.parts[self.i]['name'])
            if self.proc.wait() != 0: raise SystemExit('part read failed: ' + self.parts[self.i]['name'])
            p = self.parts[self.i]
            if self.part_bytes != p['bytes'] or self.part_hash.hexdigest() != p['sha256']: raise SystemExit('part differs: ' + p['name'])
            self.seen.append(dict(name=p['name'], bytes=self.part_bytes, sha256=p['sha256']))
        self.i += 1
        if self.i == len(self.parts): self.proc = None; return
        p = self.parts[self.i]
        cmd = SOURCE_CMD.format(name=p['name']).split() if SOURCE_CMD else ['gcloud', 'storage', 'cat', BUCKET + p['name'] + '#' + str(p['generation'])]
        self.proc = subprocess.Popen(cmd, env=ENV, stdout=subprocess.PIPE)
        self.part_hash, self.part_bytes = hashlib.sha256(), 0
    def readable(self): return True
    def readinto(self, buf):
        while self.proc is not None:
            want = min(len(buf), self.parts[self.i]['bytes'] - self.part_bytes)
            if want == 0: self.next(); continue
            data = self.proc.stdout.read(want)
            if not data: raise SystemExit('part shorter than expected: ' + self.parts[self.i]['name'])
            n = len(data); buf[:n] = data
            self.part_hash.update(data); self.whole.update(data); self.part_bytes += n; self.count += n
            return n
        return 0

class Hashing(io.RawIOBase):
    def __init__(self, f): self.f, self.h, self.n = f, hashlib.sha256(), 0
    def readable(self): return True
    def readinto(self, buf):
        data = self.f.read(len(buf))
        n = len(data); buf[:n] = data; self.h.update(data); self.n += n
        return n

def sha_file(path, md5=False):
    h, m = hashlib.sha256(), hashlib.md5()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
            if md5: m.update(block)
    return (h.hexdigest(), base64.b64encode(m.digest()).decode()) if md5 else h.hexdigest()

def main(source, art_dir, work, dest, receipt, gcs_object=None):
    t0 = time.time(); src = json.loads(Path(source).read_text()); work = Path(work); work.mkdir(parents=True, exist_ok=True)
    need = src['archive_bytes'] * 1.05 + (50 << 30)
    if shutil.disk_usage(str(work)).free < need: raise SystemExit('node-local space below archive size + 50 GiB')
    if not re.fullmatch('[0-9a-f]{8}', art_dir): raise SystemExit('ART_DIR must be eight hex digits')
    new_art = 'ap/' + art_dir + '/m544/artifact.json'
    out_tar, members, small = work / 'm.tar', {}, {}
    stream = io.BufferedReader(Parts(src['parts']), 8 << 20)
    with tarfile.open(fileobj=stream, mode='r|') as tin, tarfile.open(str(out_tar), 'w', format=tarfile.PAX_FORMAT) as tout:
        for m in tin:
            if m.isdir(): continue
            if not m.isfile() or not m.name.startswith('m544/') or '..' in m.name.split('/'): raise SystemExit('unexpected member ' + m.name)
            name = new_art if m.name == 'm544/artifact.json' else OLD + m.name
            info = tarfile.TarInfo(name); info.size, info.mode, info.mtime = m.size, 0o600, int(m.mtime)
            reader = Hashing(tin.extractfile(m))
            if m.size < (1 << 20):
                data = reader.read(); small[name] = data; tout.addfile(info, io.BytesIO(data))
            else:
                tout.addfile(info, io.BufferedReader(reader, 8 << 20))
            if reader.n != m.size: raise SystemExit('member size differs ' + m.name)
            members[name] = dict(sha256=reader.h.hexdigest(), bytes=m.size)
        rest = stream.read()  # tar padding up to the archive end, so the whole-stream hash covers every byte
    if stream.raw.count != src['archive_bytes'] or stream.raw.whole.hexdigest() != src['archive_sha256']:
        raise SystemExit('whole archive differs from its pin')
    want = sorted(OLD + m['name'] if m['name'] != 'm544/artifact.json' else new_art for m in src['members'])
    if sorted(members) != want: raise SystemExit('member set differs from the source listing')
    if members[new_art]['sha256'] != src['artifact_sha256']: raise SystemExit('artifact differs from its pin')
    art = json.loads(small[new_art].decode())
    rel = lambda p: p[len(AS):] if p.startswith(AS) else None
    for key in ('heads', 'full_weights'):
        r = rel(art[key]['path'])
        if r not in members or members[r]['sha256'] != art[key]['sha256']: raise SystemExit('artifact ' + key + ' pin differs')
    fw_rel = rel(art['full_weights']['path']); fw = json.loads(small[fw_rel].decode()); d = fw_rel.rsplit('/', 1)[0]
    for item in [fw['index']] + fw['files']:
        r = d + '/' + item['name']
        if r not in members or members[r]['sha256'] != item['sha256']: raise SystemExit('export member differs from full_weights.json: ' + item['name'])
    (tar_sha, tar_md5), tar_bytes = sha_file(out_tar, md5=True), out_tar.stat().st_size
    t1 = time.time()
    dest = Path(dest); part = dest.with_name(dest.name + '.partial')
    if dest.exists(): raise SystemExit('destination exists: ' + str(dest))
    if shutil.disk_usage(str(dest.parent)).free < tar_bytes + (50 << 30): raise SystemExit('project space below tar size + 50 GiB')
    shutil.copyfile(str(out_tar), str(part))
    if sha_file(part) != tar_sha: raise SystemExit('project copy differs')
    os.rename(str(part), str(dest))
    t2 = time.time(); upload = None
    if gcs_object:
        rc = subprocess.run(['gcloud', 'storage', 'cp', str(out_tar), BUCKET + gcs_object], env=ENV, timeout=3600).returncode
        if rc: raise SystemExit('upload failed (no retry)')
        meta = subprocess.run(['gcloud', 'storage', 'objects', 'describe', BUCKET + gcs_object, '--format=json'], env=ENV,
                              stdout=subprocess.PIPE, timeout=300, check=True).stdout
        m = json.loads(meta.decode()); upload = dict(object=gcs_object, generation=m.get('generation'), size=m.get('size'),
                                                     md5=m.get('md5_hash', m.get('md5Hash')))
        if int(upload['size'] or -1) != tar_bytes: raise SystemExit('uploaded size differs')
        if upload['md5'] != tar_md5: raise SystemExit('uploaded md5 differs or is absent (composite object?)')
    full_weights = {k: v for k, v in small.items() if k == fw_rel}
    Path(receipt).write_text(json.dumps(dict(schema='r1-repack-v1', source_archive_sha256=src['archive_sha256'], parts=stream.raw.seen,
        members=members, tar=dict(path=str(dest), sha256=tar_sha, md5=tar_md5, bytes=tar_bytes), artifact_logical=new_art,
        full_weights_json=full_weights[fw_rel].decode(), upload=upload,
        seconds=dict(read_and_repack=round(t1 - t0), project_copy=round(t2 - t1), upload=round(time.time() - t2))), indent=1, sort_keys=True) + '\n')
    print('repack verified:', len(members), 'members, tar', tar_sha[:16], flush=True)

if __name__ == '__main__':
    main(*sys.argv[1:])
