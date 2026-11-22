"""Resume stage for a later allocation of the same leg (kit side; runs once, before the trainer, inside the
job's view). It lays the newest uploaded full state of the dead allocation into the run output exactly as the
tree's own writer left it, so the tree's latest_resume/restore authenticate and load it.
  1. Forms this allocation's binding exactly as train() does (identity, preparation pin, sealed commit,
     world size) and refuses unless it equals the binding the card names (the dead allocation's attempt record).
  2. Streams the four uploaded parts in offset order through sha256 into tar extraction under a staging name
     the tree ignores, admitting only the members a complete state holds; refuses unless every part, the whole
     archive and the state marker match the publisher's receipt.
  3. Checks the marker's binding and step, writes binding.json (or requires it equal), renames the staging
     folder to the original state name and requires latest_resume to return exactly that marker.
  4. Optionally copies the publisher's receipt for that state into this allocation's publisher state folder,
     so the publisher neither re-archives nor re-sends a state that is already durable.
No byte is removed; a refused stage leaves its staging folder, which the tree never reads.
usage: rs.py <tree> <job config> <card> <stage receipt out> [publisher state folder]"""
import base64, hashlib, importlib, json, os, re, sys, tarfile
from pathlib import Path

PK = bytes.fromhex('73747564656e745f70696c6f74').decode()
MEMBER = re.compile(r'complete\.json|rng\d{3}\.pt|shards/rank\d{3}\.pt')


def read(path):
    value = json.loads(Path(path).read_text())
    if isinstance(value, dict) and 'payload' in value and set(value) <= {'payload', 'sha256', 'encoding'}:
        raw = base64.b64decode(value['payload'], validate=True)
        if 'sha256' in value and hashlib.sha256(raw).hexdigest() != value['sha256']:
            raise ValueError('RS_CARD_CAPSULE')
        return json.loads(raw)
    return value


def say(status, **kw):
    print(json.dumps(dict(event='resume_stage', status=status, **kw), sort_keys=True, default=str), flush=True)


def refuse(code, **kw):
    say('REFUSE', code=code, **kw)
    raise SystemExit(3)


class Joined:
    """The parts in offset order as one read-only stream; hashes each part and the whole as it goes."""
    def __init__(self, parts):
        self.parts, self.index, self.handle, self.whole = parts, -1, None, hashlib.sha256()
        self.seen = [dict(bytes=0, sha=hashlib.sha256()) for _ in parts]
        self.next()

    def next(self):
        if self.handle:
            self.handle.close()
        self.index += 1
        self.handle = open(self.parts[self.index]['path'], 'rb') if self.index < len(self.parts) else None

    def read(self, size=-1):
        out = b''
        while self.handle and (size < 0 or len(out) < size):
            block = self.handle.read(1 << 24 if size < 0 else min(1 << 24, size - len(out)))
            if not block:
                self.next()
                continue
            self.seen[self.index]['bytes'] += len(block)
            self.seen[self.index]['sha'].update(block)
            self.whole.update(block)
            out += block
        return out

    def drain(self):
        while self.read(1 << 24):
            pass


def main(tree, config, card_path, receipt_out, publisher=None):
    sys.path.insert(0, str(tree))
    P = importlib.import_module(PK + '.p3_provenance')
    C = importlib.import_module(PK + '.carrier_c1_run')
    S = importlib.import_module(PK + '.carrier_c1_sweep')
    F = importlib.import_module(PK + '.full_ft')
    cfg, card = P.load(config), read(card_path)
    if card.get('schema') != 'n-resume-card-v1':
        refuse('RS_CARD_SCHEMA')
    bound = dict(config_sha256=C.identity(cfg), preparation=cfg['preparation'],
                 trainer_commit=C.authenticate(cfg), world_size=S.recipe_for(cfg)['world_size'])
    want = card['binding']
    differs = sorted(k for k in set(bound) | set(want) if bound.get(k) != want.get(k))
    if differs:
        refuse('RS_BINDING_DIFFERS', fields=differs, card=want, allocation=bound)
    output = Path(cfg['output'])
    name, done = card['directory'], card['done']
    if not re.fullmatch(r'checkpoint_\d{6}_[0-9a-f]{32}', name):
        refuse('RS_STATE_NAME', name=name)
    final, staging = output/name, output/(name + '.staging')
    if final.exists() or staging.exists():
        refuse('RS_STATE_EXISTS', name=name)
    parts = sorted(card['parts'], key=lambda p: p['offset'])
    cursor = 0
    for part in parts:
        if part['offset'] != cursor or Path(part['path']).stat().st_size != part['bytes']:
            refuse('RS_PART_LAYOUT', part=part['path'])
        cursor += part['bytes']
    if len(parts) != 4 or cursor != done['bytes']:
        refuse('RS_PART_LAYOUT', bytes=cursor)
    output.mkdir(parents=True, exist_ok=True)
    staging.mkdir(mode=0o700)
    (staging/'shards').mkdir(mode=0o700)
    stream, names = Joined(parts), set()
    with tarfile.open(fileobj=stream, mode='r|') as archive:
        for member in archive:
            if not member.isfile() or not MEMBER.fullmatch(member.name) and member.name != F.REPLICATED_FILE:
                refuse('RS_ARCHIVE_MEMBER', member=member.name)
            if member.name in names:
                refuse('RS_ARCHIVE_MEMBER', member=member.name)
            names.add(member.name)
            target = staging/member.name
            with archive.extractfile(member) as source, open(target, 'xb') as sink:
                while True:
                    block = source.read(1 << 24)
                    if not block:
                        break
                    sink.write(block)
                sink.flush()
                os.fsync(sink.fileno())
    stream.drain()
    for part, seen in zip(parts, stream.seen):
        if seen['bytes'] != part['bytes'] or seen['sha'].hexdigest() != part['sha256']:
            refuse('RS_PART_DIGEST', part=part['path'])
    if stream.whole.hexdigest() != done['sha256']:
        refuse('RS_ARCHIVE_DIGEST')
    marker = staging/'complete.json'
    if not marker.is_file() or P.sha256(marker) != done['marker_sha256']:
        refuse('RS_MARKER_DIGEST')
    manifest = P.load(marker)
    if manifest.get('binding') != bound or manifest.get('step') != int(name[11:17]):
        refuse('RS_MARKER_BINDING')
    if set(manifest['files']) | {'complete.json'} != names:
        refuse('RS_ARCHIVE_INVENTORY')
    binding = output/'binding.json'
    if binding.exists():
        if P.load(binding) != bound:
            refuse('RS_OUTPUT_BINDING')
    else:
        P.write(binding, bound)
    if publisher:
        # Before the rename, so no publisher pass sees the state without its durable receipt.
        state = Path(publisher)
        state.mkdir(parents=True, exist_ok=True)
        record = state/('gcs_' + name + '.done')
        if record.exists() and read(record) != done:
            refuse('RS_PUBLISHER_RECORD')
        if not record.exists():
            record.write_text(json.dumps(done, sort_keys=True) + '\n')
    staging.rename(final)
    pin = C.latest_resume(output, bound)
    if Path(pin['path']) != (final/'complete.json').resolve():
        refuse('RS_NOT_NEWEST', newest=pin['path'])
    result = dict(schema='n-resume-stage-v1', pin=pin, step=manifest['step'], binding=bound,
                  card_sha256=P.sha256(card_path), source_job=card.get('source_job'), object=done.get('object'))
    P.write(receipt_out, result)
    say('PASS', step=manifest['step'], pin=pin, source_job=card.get('source_job'))
    return 0


if __name__ == '__main__':
    if len(sys.argv) not in (5, 6):
        refuse('RS_USAGE')
    raise SystemExit(main(*sys.argv[1:]))
