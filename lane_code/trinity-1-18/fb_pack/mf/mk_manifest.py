"""Build the first-boundary manifest on trinity-1-18 from the lane's delivered packets (no new data)."""
import json, hashlib, os, sys
F = '/scratch/jjyeung/orch_n30/fb_pack'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def pin(p):
    return dict(path=p, sha256=sha(p), bytes=os.path.getsize(p))


extra = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
route = json.load(open(F + '/route/out/ROUTE_MANIFEST.json'))
out = dict(schema='fb-pack-first-boundary-manifest-v1', tree_seal_base=route.get('tree_seal_value'), slices={})
for name in ['absolute_distance', 'units', 'coverage_distance', 'coverage_units', 'recovery']:
    s = route['slices'][name]
    e = dict(rows=s['rows'], coverage=s['coverage'], envelope=s['envelope'], native=s['native_counts'],
             refusals=s['native_refusal_reasons'], audit_hits=s['audit_hits'], remove=s.get('remove'),
             prefiltered=s.get('prefiltered'))
    for k in sorted(s):
        if 'upstream' in k or 'portable' in k:
            e[k] = s[k]
    out['slices'][name] = e
cam = F + '/cam/out'
rb = json.load(open(cam + '/REBIND.json'))
out['slices']['camera_wording'] = dict(
    rows=pin(cam + '/rows/camera_wording.jsonl'), coverage=pin(cam + '/coverage/camera_wording.json'),
    envelope=pin(cam + '/envelopes/camera_wording.json'), upstream=pin(cam + '/upstream/camera_wording.json'),
    native=rb.get('counts'), excluded_eval_rooms=len(rb.get('excluded') or []),
    review='fbp_camrev GO (F/camrev/REVIEW_VERDICT.md)')
out['frames'] = pin(F + '/FRAME_STAGE_RECEIPT.json')
for k, p in [('route_manifest', '/route/out/ROUTE_MANIFEST.json'), ('config_handoff', '/route/out/CONFIG_HANDOFF.json'),
             ('localized_index', '/route/out/LOCALIZED_INDEX.json'), ('envelope_index', '/route/out/ENVELOPE_INDEX.json'),
             ('staged_inputs', '/route/out/STAGED_INPUTS_FINAL.json')]:
    out[k] = pin(F + p)
out.update(extra)
json.dump(out, open(F + '/MANIFEST_N_BOUNDARY1.json', 'w'), indent=1)
print(sha(F + '/MANIFEST_N_BOUNDARY1.json'))
for n, e in out['slices'].items():
    print(n, e['rows'].get('row_count', ''), e['rows']['sha256'][:12], 'env', e['envelope']['sha256'][:12], 'native', e.get('native'),
          [k for k in e if 'upstream' in k])
