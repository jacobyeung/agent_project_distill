"""Header-level B1 binding check of the step-544 export (artifact 1d6eeb28) against base Qwen3.5-9B c2022362, the way
kit/check_b1.py compares names and shapes, but reading only safetensors headers (KBs) instead of 37 GB of tensors.
Reads tar members by seek. usage: python3 b1_header_check.py M_TAR PREFIX ARTIFACT_MEMBER BASE_DIR OUT.json"""
import hashlib, json, os, struct, sys, tarfile
mt, pre, art_member, base, out = sys.argv[1:6]
def hdr(f):
    n = struct.unpack('<Q', f.read(8))[0]; h = json.loads(f.read(n)); h.pop('__metadata__', None)
    return {k: (v['dtype'], tuple(v['shape'])) for k, v in h.items()}
t = tarfile.open(mt, 'r:'); st = {}; info = {}
for m in t:
    if m.name == art_member:
        b = t.extractfile(m).read(); info['artifact_sha256'] = hashlib.sha256(b).hexdigest()
        a = json.loads(b); info['artifact_keys'] = sorted(a)[:40]
        for k in ('heads', 'lm', 'run_id', 'step', 'base', 'base_model', 'export_kind'):
            if k in a: info['artifact_' + k] = a[k]
    elif m.name.startswith(pre + '/full_weights/'):
        n = os.path.basename(m.name)
        if n.endswith('.safetensors'): st.update({k: v + (n,) for k, v in hdr(t.extractfile(m)).items()})
        elif n == 'full_weights.json': info['full_weights_json'] = json.loads(t.extractfile(m).read())
    elif m.name == pre + '/heads.pt': info['heads_pt_bytes'] = m.size
bt = {}
for n in sorted(os.listdir(base)):
    if n.endswith('.safetensors'):
        with open(os.path.join(base, n), 'rb') as f: bt.update(hdr(f))
S = {k: v for k, v in st.items() if not k.startswith('mtp.')}; Bt = {k: v for k, v in bt.items() if not k.startswith('mtp.')}
only_s, only_b = sorted(set(S) - set(Bt)), sorted(set(Bt) - set(S))
shape_diff = {k: (S[k][1], Bt[k][1]) for k in set(S) & set(Bt) if S[k][1] != Bt[k][1]}
dt = {}
for k in set(S) & set(Bt):
    if S[k][0] != Bt[k][0]: dt.setdefault(f'{Bt[k][0]}->{S[k][0]}', []).append(k)
grp = lambda k: 'visual' if '.visual.' in k else ('lm_head' if k.startswith('lm_head') else 'language_model')
counts = {}
for k in S: counts[grp(k)] = counts.get(grp(k), 0) + 1
res = dict(info, export_tensors=len(st), export_tensors_no_mtp=len(S), base_tensors_no_mtp=len(Bt), only_in_export=only_s[:50],
           n_only_in_export=len(only_s), only_in_base=only_b[:50], n_only_in_base=len(only_b), shape_diffs=shape_diff,
           dtype_diffs={k: len(v) for k, v in dt.items()}, dtype_diff_examples={k: v[:5] for k, v in dt.items()}, groups=counts,
           verdict='B1_HEADER_OK' if not only_s and not only_b and not shape_diff else 'B1_HEADER_MISMATCH')
json.dump(res, open(out, 'w'), indent=1, default=list)
print(res['verdict'], {k: res[k] for k in ('artifact_sha256', 'export_tensors', 'export_tensors_no_mtp', 'base_tensors_no_mtp', 'n_only_in_export', 'n_only_in_base', 'dtype_diffs', 'groups', 'heads_pt_bytes')})
print('only_in_export', only_s[:12]); print('only_in_base', only_b[:12]); print('shape_diffs', list(shape_diff.items())[:8])
