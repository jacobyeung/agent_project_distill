"""Map the route lane's 1-18 pins to the local read-only copy (sha256 -> local path)."""
import hashlib
import json
import os
from pathlib import Path

FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
RO = FB/'ro'
ROUTE = RO/'orch_n30/fb_pack/route'
FINAL_CAMERA = RO/'orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl'
STANDIN_CAMERA = ROUTE/'out/rows/camera_wording.jsonl'
FINAL_SHA = 'e8cbda99f794540c9c0f716d1ae8ce451fd84e473598795c67237fe051acd2d0'
STANDIN_SHA = '31914ba5470c1b5b7fac4ba52a13482cb6ce2965a732b69f6f57a55ed1fbe814'


def local(path):
    path = str(path)
    for old, new in (('/scratch/jjyeung/orch_n30/', RO/'orch_n30'), ('/scratch/jjyeung/n30_mirror/', RO/'n30_mirror')):
        if path.startswith(old) and not path.startswith(str(RO)+'/'):
            path = str(new)+'/'+path[len(old):]
            break
    p = Path(path)
    if p.is_symlink():
        return local(os.readlink(p))
    return p


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def build_map():
    maps, used = {}, []
    staged = ROUTE/'out/STAGED_INPUTS_FINAL.json'
    used.append(staged)
    for entry in json.loads(staged.read_text())['files']:
        maps[entry['sha256']] = str(local(entry['source_path']))
    for name in ('COMPOSE_RESULT.json', 'CONFIG_HANDOFF.json', 'ENVELOPE_INDEX.json'):
        used.append(ROUTE/'out'/name)
        for path, value in json.loads((ROUTE/'out'/name).read_text())['inputs'].items():
            p = local(path)
            if p.is_file():
                maps.setdefault(value['sha256'], str(p))
    maps[FINAL_SHA] = str(FINAL_CAMERA)
    return maps, used


def original():
    return json.loads((ROUTE/'out/config/FIRST_BOUNDARY_CANDIDATE.json').read_text())


if __name__ == '__main__':
    maps, used = build_map()
    cfg = original()
    t = cfg['r1_training']
    out = {}
    def look(pin):
        p = Path(maps.get(pin['sha256'], pin['path']))
        return dict(path=str(p), exists=p.is_file(), ok=p.is_file() and sha(p) == pin['sha256'])
    out['row_sources'] = look(t['row_sources'])
    out['source_membership'] = look(t['source_membership'])
    specs = json.loads(Path(maps[t['row_sources']['sha256']]).read_text())
    out['spec_names'] = sorted(specs)
    for k, v in specs.items():
        if isinstance(v, dict) and isinstance(v.get('source'), dict):
            out['source:'+k] = dict(sha=v['source']['sha256'], **look(v['source']))
    for k, v in t['routing_inputs'].items():
        out['envelope:'+k] = look(v)
    for k in ('wording_exclusion', 'camera_wording_exclusion'):
        out[k] = look(t[k])
    out['naming_remove'] = look(cfg['remove_files'][-1])
    out['streams.routing'] = look(cfg['streams']['routing'])
    out['map_entries'] = len(maps)
    out['inputs_sha256'] = {str(p): sha(p) for p in used}
    print(json.dumps(out, indent=1))
