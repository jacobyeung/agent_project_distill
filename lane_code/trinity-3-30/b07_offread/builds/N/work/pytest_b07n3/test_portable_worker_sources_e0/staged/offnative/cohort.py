"""Question-only inventories; no answer drives membership, ordering, or proposals."""
import hashlib
import json
import re
from .paths import REVSI, VSI
from .io import load
from offkit.report import ReadMode, check_cohort, index, key
from offkit.spec import subtype_group
SAFE = ('id','example_id','dataset','scene_name','question_type','question','options','benchmark')

def questions(path):
    # The input container includes labels. Only this allowlist leaves the loader.
    text = path.read_text()
    raw = json.loads(text) if text.lstrip().startswith('[') else [json.loads(s) for s in text.splitlines() if s.strip()]
    return [{k:r[k] for k in SAFE if k in r} for r in raw]

def cohort(benchmark):
    if benchmark not in ('revsi999t32','vsibench5130'):
        raise ValueError('unknown benchmark')
    q = questions(REVSI/'inputs/i1.json' if benchmark=='revsi999t32' else VSI/'cohort/meta_5130.jsonl')
    mode = ReadMode(benchmark, 'harness')
    check_cohort(mode, q)
    index(q, 'cohort')
    return q

def order_key(row):
    return hashlib.sha256(key(row).encode()).hexdigest()

def canary(cohort, mode):
    groups = subtype_group(mode.spec)
    selected = []
    for group in mode.groups:
        available = [r for r in cohort if groups[r['question_type']] == group]
        selected.append(min(available, key=order_key))
    used = {key(r) for r in selected}
    selected += sorted((r for r in cohort if key(r) not in used), key=order_key)[:10-len(selected)]
    if len(selected) != 10 or not any('abs_distance' in r['question_type'] for r in selected):
        raise ValueError('canary must cover every group and a routed type')
    return [key(r) for r in selected]

def media302(items):
    old = {r['relative_path']:r for r in load(REVSI/'media/NEED_261.json')}
    push = {r['relative']:r for r in load(REVSI/'inputs/REVSI_PUSH_FILES.json')['files']}
    needed = sorted({r['scene_name'] + '.mp4' for r in items})
    if len(needed) != 302 or len(set(needed)-set(old)) != 41:
        raise ValueError('ReVSI media membership differs')
    out = []
    for name in needed:
        if name in old:
            out.append(dict(old[name], upload_required=False))
        else:
            p = push.get(name, {})
            out.append(dict(relative_path=name, bytes=p.get('bytes'), sha256=None,
                source=p.get('source'), source_evidence='REVSI_PUSH_FILES.json' if p else None,
                upload_required=True, status='hash_required' if p else 'manifest_entry_and_hash_required'))
    return out


def media_manifest(benchmark, items):
    if benchmark=='revsi999t32':return media302(items)
    entries=load(VSI/'cohort/MEDIA_MANIFEST.json')
    expected={r['dataset']+'/'+r['scene_name']+'.mp4' for r in items}
    if len(entries)!=288 or {r['relative_path'] for r in entries}!=expected:
        raise ValueError('VSI-Bench media membership differs')
    return [dict(r,bytes=r.get('bytes'),status='bytes_required' if not r.get('bytes') else 'pinned') for r in entries]

def operands(question):
    # This covers the official absolute-distance template, without guessing unmatched text.
    match = re.search(r'between the (.+?) and the (.+?)\s+\(in [^()]+\)\?$', question, re.I)
    if not match:
        return None
    return [re.sub(r'\s+', ' ', s).strip() for s in match.groups()]

def name_inventory(items):
    names, unresolved = {}, []
    for row in items:
        scene = row['dataset'] + ':' + row['scene_name']
        names.setdefault(scene, set())
        if row['question_type'] == 'object_abs_distance':
            found = operands(row['question'])
            if found is None:
                unresolved.append(key(row))
            else:
                names[scene].update(found)
    return dict(names={k:sorted(v) for k,v in names.items()}, unresolved=unresolved,
                name_video_pairs=sum(len(v) for v in names.values()),
                scope='Question-derived distance operands; arbitrary model-emitted aliases remain unbounded.')
