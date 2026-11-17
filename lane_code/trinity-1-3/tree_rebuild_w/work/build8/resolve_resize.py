"""Resolve resize sites from their transform and coordinate context."""
import collections,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';P=L/'work/build8/proofs/audit';P.mkdir(parents=True,exist_ok=True)
rows=json.loads((L/'work/build7/proofs/audit/RESIZE_AUDIT.json').read_text())
square={'student_pilot/g3t_online.py','student_pilot/c1r_dense.py','student_pilot/c1r_ref.py',
 'student_pilot/tower_read.py','tools/g3t_patch_grid_store.py','tools/g3t_camera_sidecar_store.py'}
fixed={'verifykit/io.py','verifykit/prepare.py','student_pilot/verify_pass.py'}
feature={'student_pilot/grounding_head.py','student_pilot/point_depth_head.py'}
for r in rows:
 name=r['file'];n=r['line'];lines=(T/name).read_text().splitlines();r['source_sha256']=hashlib.sha256((T/name).read_bytes()).hexdigest()
 r['context']=[dict(line=i+1,text=lines[i]) for i in range(max(0,n-10),min(len(lines),n+5))]
 if r['portrait_aspect_distorted'] is True:
  status='distorting';reason='Independent height and width factors map arbitrary input masks to a fixed coordinate raster. No equal-aspect condition is enforced.'
 elif name in fixed:
  status='distorting';reason='The reader forces arbitrary masks to a 640 by 480 raster without an equal-aspect condition.'
 elif name=='verifykit/render.py':
  status='aspect-preserving';reason='The crop uses one scale from its maximum side, then pads a square canvas; the mask follows that same crop and scale.'
 elif name=='verifykit/model.py':
  status='not applicable';reason='StubBackend downsamples synthetic smoke-test images; this is not the native inference backend.'
 elif name in square or name.endswith('utils/load_fn.py') and n==77:
  status='aspect-preserving';reason='The input is square-padded before uniform square-to-square resizing; padding coordinates retain the original image footprint.'
 elif name.endswith('utils/load_fn.py'):
  status='distorting';reason='The requested resize preserves aspect approximately, but independently rounds the computed dimension to a multiple of the patch size. It does not preserve the exact ratio.'
 elif name in feature or name.endswith('vision_transformer.py') or name.endswith('dpt_head.py'):
  status='not applicable';reason='This operation interpolates feature or position grids, not RGB pixels or a native portrait mask. Image coordinates are established by the upstream image transform.'
 elif name=='student_pilot/mask_grounding_head.py':
  status='not applicable';reason='This operation aligns feature, attention, or loss grids in the model coordinate domain. The RGB grid assertions and upstream input transform establish the image footprint; it is not a separate portrait RGB transform.'
 elif name=='student_pilot/sam3_tower.py':
  status='not applicable';reason='This decoder maps normalized predicted masks back to the supplied native height and width. It restores output coordinates and does not resize the input image.'
 elif name in ('student_pilot/mdg_eval.py','student_pilot/mdg_train.py'):
  status='not applicable';reason='Prediction and target masks are aligned in their common normalized coordinate domain for output or loss computation; this is not an RGB preprocessing transform.'
 elif name=='student_pilot/grounding_targets.py':
  status='distorting';reason='Instance rasters are resized to the RGB dimensions before erosion. There is no equal-aspect assertion; changing this bound coordinate path requires row-byte parity.'
 elif name=='student_pilot/clean_media.py':
  status='distorting';reason='The audit reconstructs a resize to recorded width and height without an equal-aspect assertion. It can reproduce anisotropic source preparation.'
 elif name=='student_pilot/reread.py':
  status='distorting';reason='Raw frame pixels are resized to the requested model grid without padding or an equal-aspect assertion.'
 elif name in ('student_pilot/benchmark_eval/prepare.py','student_pilot/orchard_eval/prepare.py'):
  status='not applicable';reason='The function creates a synthetic color-video fixture, not a production frame transform.'
 else:raise AssertionError((name,n))
 r.update(classification=status,reason=reason,evidence=f'{name}:{n}')
 r['portrait_aspect_distorted']=status=='distorting'
 if status=='distorting':r['known_defect']='portrait share unknown: frame dimensions absent from the bound slices'
 r['code_changed']=False
(P/'RESIZE_AUDIT.json').write_text(json.dumps(rows,indent=2)+'\n')
(P/'PORTRAIT_SUMMARY.json').write_text(json.dumps(dict(classes=dict(collections.Counter(r['classification'] for r in rows)),
 row_byte_parity='Not measured; bound mask coordinates unchanged',portrait_share='portrait share unknown: frame dimensions absent from the bound slices'),indent=2)+'\n')
