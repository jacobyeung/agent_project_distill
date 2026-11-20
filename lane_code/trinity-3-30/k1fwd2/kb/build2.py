"""Build the step-544 K1 own-phase forward that also writes frozen-FoV depth variants V1 and V2.

Runs on the Orchard login node with /usr/bin/python3. Reuses k1fwd1's pinned builder (build.py 12bc0738)
for job 170235's sealed batch, code bundle and wrapper patches; adds one boundaries.py patch that writes
fov.npz + FOV_RECEIPT.json beside own.npz. The served grid path is unchanged; parity checks it per capture.
"""
import hashlib, json, sys
from pathlib import Path

OLD = Path('/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5')
BUILDER_DIR = Path(__import__('os').environ.get('K1FWD1_BUILDER_DIR', str(OLD)))
OLD_BUILD_SHA = '12bc073820cd904c214d51dc2c2571cd0350715c0a19cc4b2b4e84382f497f5b'
PKG = Path('/project/community/jjyeung/okh7/a15_cot_ap' + sys.argv[2]) if len(sys.argv) > 2 else None
TOKEN, MANIFEST, GHEX = sys.argv[3:6] if len(sys.argv) > 5 else (None, None, None)
ALLOCATION, RESERVE = 7140, 600

BOUND_OWN_OLD = """  own=closed_adapters(torch.no_grad()(_prepare_decode))(self.model,self.processor,batch,max_new_tokens=16384).heads
"""
BOUND_OWN_NEW = """  seen=[];head=self.model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth if s.get('fov_variants') else None
  if head is not None:
   if 'encode' in head.__dict__:raise ValueError('Point-depth encode is already wrapped')
   served_encode=head.encode
   def encode(grid,vit,fov):
    # Observe the served pose-head FoV; the served latent is the unchanged call's result.
    seen.append(fov.detach().clone());return served_encode(grid,vit,fov)
   head.encode=encode
  try:own=closed_adapters(torch.no_grad()(_prepare_decode))(self.model,self.processor,batch,max_new_tokens=16384).heads
  finally:
   if head is not None:head.__dict__.pop('encode')
"""
BOUND_Q_OLD = """  with torch.no_grad():depth=own.depth_head.query(own.depth_map,uv).double().cpu().numpy().reshape(32,51,51)
"""
BOUND_Q_NEW = """  with torch.no_grad():depth=own.depth_head.query(own.depth_map,uv).double().cpu().numpy().reshape(32,51,51)
  if head is not None:
   if own.depth_head is not head:raise ValueError('Served depth head differs')
   self.fov_variants(c,batch,seen,uv,depth)
"""
BOUND_SAM_OLD = """ def sam(self):
  import torch
  from sam3_tower import attach_sam3_tower
  s=self.settings
"""
BOUND_SAM_NEW = """ def fov_variants(self,c,batch,seen,uv,served):
  # PATCH_DONOR3 scale_donor.forward at the donor checkpoint (this export): a separate private feature
  # pass, V1 = private depth.fov on its states, V2 = frozen G3T raw_pose9[anchor_slots,7:9]; one
  # point-depth encode/query per source. Nothing here feeds the served own.npz.
  import math,time,torch
  from student_pilot.decoupled_v import features
  s=self.settings['fov_variants']
  if s.get('schema')!='k1-fov-variants-v1':raise ValueError('FoV variant settings differ')
  if getattr(self,'g3t',None) is None:self.g3t=B.load(B.checked(s['g3t']))['captures']
  dest=Path(s['root'])/B.digest(c['canonical'])[:16]
  if not dest.is_dir() or (dest/'fov.npz').exists() or (dest/'own.npz').exists():raise ValueError('FoV variant destination differs')
  if len(seen)!=1 or tuple(seen[0].shape)!=(32,2):raise ValueError('Expected one served point-depth encode with [32,2] FoV')
  depth=self.model.auxiliary_heads.depth;head=depth.auxiliary_heads.camera.point_depth
  def valid(f):
   return tuple(f.shape)==(32,2) and bool(torch.isfinite(f).all()) and bool(((f>0)&(f<math.pi)).all())
  def grid(cap,f):
   return head.query(head.encode(cap.grids[0],cap.vits[0],f.float()),uv).double().cpu().numpy().reshape(32,51,51)
  arrays=dict(fov_B=seen[0].float().cpu().numpy());missing={};checks={};seconds={}
  start=time.monotonic()
  with torch.no_grad():
   cap=features(depth,batch,allow_short=True)
   if tuple(cap.states.shape[:2])!=(1,32):raise ValueError('Donor feature pass requires one clip with 32 anchor frames')
   seconds['features']=time.monotonic()-start
   control=grid(cap,seen[0])
   checks['second_pass_pose_fov_bit_identical']=bool(np.array_equal(control,served))
   checks['second_pass_pose_fov_max_abs']=float(np.max(np.abs(control-served)))
   fovs={}
   if hasattr(depth,'fov'):fovs['V1']=(1e-4+(math.pi-2e-4)*depth.fov(cap.states.float()).sigmoid())[0]
   else:missing['V1']='MISSING: model.auxiliary_heads.depth.fov'
   r=self.g3t.get(c['canonical'])
   if r is None:missing['V2']='MISSING: no cached G3T FoV for this capture (outside the scored set)'
   else:
    if r['anchor_indices']!=c['anchor_indices'] or r['capture_sha256']!=B.digest(c):raise ValueError('G3T FoV capture/anchor identity differs')
    fovs['V2']=torch.as_tensor(np.asarray(r['fov_hw_rad'],dtype=np.float64),device=cap.states.device,dtype=torch.float32)
   for name,f in fovs.items():
    if not valid(f):raise ValueError('FoV '+name+' requires finite vertical/horizontal radians')
    t=time.monotonic();g=grid(cap,f)
    if g.shape!=(32,51,51) or not np.isfinite(g).all() or np.any(g<=0):raise ValueError('Variant depth must be finite positive 32x51x51: '+name)
    arrays['depth_'+name]=g;arrays['fov_'+name]=f.float().cpu().numpy();seconds[name]=time.monotonic()-t
  np.savez_compressed(dest/'fov.npz',**arrays)
  B.write(dest/'FOV_RECEIPT.json',dict(schema='k1-fov-variants-v1',capture_sha256=B.digest(c),canonical=c['canonical'],
   checkpoint=self.checkpoint,served_depth_sha256=hashlib.sha256(np.ascontiguousarray(served).tobytes()).hexdigest(),
   sources=dict(B='live pose-head FoV, stages[-1][...,7:9] as passed to the served encode',
                V1='1e-4+(pi-2e-4)*sigmoid(depth.fov(states)) on a separate private feature pass (scale_donor V1)',
                V2='frozen G3T raw_pose9[anchor_slots,7:9] from the K1 tower phase cache (scale_donor V2)'),
   g3t=s['g3t'],missing=missing,checks=checks,seconds=seconds,keys=sorted(arrays),
   files={'fov.npz':B.sha(dest/'fov.npz')},boundaries_sha256=B.sha(__file__)))
 def sam(self):
  import torch
  from sam3_tower import attach_sam3_tower
  s=self.settings
"""
BOUND_IMPORT_OLD = """import numpy as np
"""
BOUND_IMPORT_NEW = """import numpy as np
import hashlib
"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def patch_boundaries(K, bound):
    bound = K.replace_once(bound, K.BOUND_STEP_OLD, K.BOUND_STEP_NEW, 'boundary step')
    bound = K.replace_once(bound, K.BOUND_SEL_OLD, K.BOUND_SEL_NEW, 'boundary selection')
    reviewed = bound
    for old, new, what in ((BOUND_IMPORT_OLD, BOUND_IMPORT_NEW, 'import'), (BOUND_OWN_OLD, BOUND_OWN_NEW, 'own'),
                           (BOUND_Q_OLD, BOUND_Q_NEW, 'query'), (BOUND_SAM_OLD, BOUND_SAM_NEW, 'variants')):
        bound = K.replace_once(bound, old, new, 'fov ' + what)
    compile(bound, 'boundaries.py', 'exec')
    return reviewed, bound


def main():
    mode = sys.argv[1]
    sys.path.insert(0, str(BUILDER_DIR))
    assert sha((BUILDER_DIR / 'build.py').read_bytes()) == OLD_BUILD_SHA
    import build as K
    if mode == 'patch':  # local: python3 build2.py patch OLD_BOUNDARIES OUT_DIR
        old = Path(sys.argv[2]).read_text()
        reviewed, new = patch_boundaries(K, old)
        Path(sys.argv[3], 'k1fwd1_boundaries.py').write_text(reviewed)
        Path(sys.argv[3], 'new_boundaries.py').write_text(new)
        return
    assert mode == 'build' and PKG is not None
    assert PKG.is_dir() and not (PKG / 'BUILD.json').exists()
    text, raw, boot = K.old_batch()
    config = json.loads(boot['a.json'])
    names = ['sj/a40fbc19.json', K.KITP + '/native_kit/boundaries.py', K.KITP + '/out/DEPENDENCIES.json']
    code = K.code_members(config, names)
    manifest = json.loads(code['sj/a40fbc19.json'])
    assert K.digest(manifest) == config['manifest_binding_digest']
    old_bound = code[K.KITP + '/native_kit/boundaries.py']
    reviewed, bound = patch_boundaries(K, old_bound.decode())
    assert sha(reviewed.encode()) == '7e2bcd760f9882933a655ffb90efea408abc23234edf079eac6a27fc4edfa8bc'
    bound = bound.encode()
    bound_path = '/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/boundaries.py'
    deps = json.loads(code[K.KITP + '/out/DEPENDENCIES.json'])
    assert deps[bound_path] == sha(old_bound)
    deps[bound_path] = sha(bound)
    deps_raw = (json.dumps(deps, indent=1, sort_keys=True) + '\n').encode()
    wrappers = K.patched_wrappers(boot)
    g_raw = (PKG / ('g_' + GHEX + '.json')).read_bytes()
    g3t = json.loads(g_raw)['captures']
    by_name = {c['canonical']: c for c in manifest['captures']}
    auth = dict(g3t=len(g3t), in_manifest=0, sha_equal=0, anchors_equal=0)
    for name, r in g3t.items():
        c = by_name.get(name)
        if c is None:
            continue
        auth['in_manifest'] += 1
        auth['sha_equal'] += r['capture_sha256'] == K.digest(c)
        auth['anchors_equal'] += r['anchor_indices'] == c['anchor_indices']
    assert auth['in_manifest'] == auth['sha_equal'] == auth['anchors_equal'] == len(g3t) == 242, auth
    g_path = '/scratch/jjyeung/' + GHEX + '.json'
    m = json.loads(code['sj/a40fbc19.json'])
    m['gpu']['export_step'] = 544
    m['gpu']['fov_variants'] = dict(schema='k1-fov-variants-v1', root=config['logical_run'] + '/native/probe',
                                    g3t=dict(path=g_path, sha256=sha(g_raw)))
    m_raw = (json.dumps(m, sort_keys=True) + '\n').encode()
    assert json.loads(m_raw) == m
    overlay_files = {K.KITP + '/native_kit/boundaries.py': bound, K.KITP + '/out/DEPENDENCIES.json': deps_raw,
                     'sj/' + MANIFEST + '.json': m_raw, 'sj/' + GHEX + '.json': g_raw}
    overlay = K.tar_bytes(overlay_files)
    overlay_path = PKG / ('o_' + TOKEN + '.tar')
    overlay_path.write_bytes(overlay)
    c = json.loads(boot['a.json'])
    v = K.VARIANTS['p544']
    c.update(token=TOKEN, pool=str(PKG / TOKEN), pointer=str(PKG / TOKEN / 'a.json'),
             cloud='gs://cmu-gpucloud-jjyeung/q8/' + TOKEN + '/r', allocation_seconds=ALLOCATION,
             capture_reserve_seconds=RESERVE,
             manifest='/scratch/jjyeung/' + MANIFEST + '.json', manifest_sha256=sha(m_raw),
             manifest_binding_digest=K.digest(m),
             export=dict(bytes=K.PART * 4, sha256=v['whole'],
                         parts=[dict(path=str(OLD / v['links'] / str(i)), bytes=K.PART, sha256=s)
                                for i, (_, s) in enumerate(v['parts'])]),
             overlay=dict(path=str(overlay_path), bytes=len(overlay), sha256=sha(overlay),
                          members={n: dict(bytes=len(b), sha256=sha(b)) for n, b in overlay_files.items()}),
             binding_changes={bound_path: sha(bound)})
    boot_v = dict(wrappers)
    boot_v['a.json'] = json.dumps(c, sort_keys=True).encode()
    import gzip, base64, re
    bundle = gzip.compress(K.tar_bytes(boot_v), mtime=0)
    assert len(bundle) < 6 * 1024 ** 2
    script = text.replace(re.search(r"raw=base64\.b64decode\('([A-Za-z0-9+/=]+)'", text).group(1),
                          base64.b64encode(bundle).decode())
    script = K.replace_once(script, sha(raw), sha(bundle), 'payload sha')
    script = K.replace_once(script, "'b7e31d84a90c62f5'", "'" + TOKEN + "'", 'root token')
    batch = PKG / (TOKEN + '.sh')
    batch.write_text(script)
    (PKG / (TOKEN + '.a.json')).write_bytes(boot_v['a.json'])
    (PKG / 'new_boundaries.py').write_bytes(bound)
    (PKG / 'k1fwd1_boundaries.py').write_bytes(reviewed.encode())
    receipt = dict(builder=sha(Path(__file__).read_bytes()), reused_builder=dict(path=str(OLD / 'build.py'), sha256=OLD_BUILD_SHA),
                   old_batch=K.OLD_BATCH_SHA, code_uri=K.CODE_URI, token=TOKEN, job_name='a15_cot_ap' + TOKEN,
                   batch=str(batch), batch_sha256=sha(script.encode()), payload_sha256=sha(bundle),
                   manifest=c['manifest'], manifest_sha256=c['manifest_sha256'], plan=c['manifest_binding_digest'],
                   overlay=c['overlay']['sha256'], export_whole=v['whole'], export_parts=[p['path'] for p in c['export']['parts']],
                   allocation_seconds=ALLOCATION, capture_reserve_seconds=RESERVE,
                   boundaries=dict(old=sha(old_bound), k1fwd1=sha(reviewed.encode()), new=sha(bound)),
                   dependencies=sha(deps_raw), wrappers={n: sha(wrappers[n]) for n in ('stage_job.py', 'batch_entry.py', 'phase_worker.py')},
                   fov_variants=m['gpu']['fov_variants'], g3t_authentication=auth)
    (PKG / 'BUILD.json').write_text(json.dumps(receipt, indent=1, sort_keys=True) + '\n')
    print(json.dumps(receipt, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
