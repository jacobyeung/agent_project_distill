"""Document saved signals, their missingness, and descriptive fallback rules."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json, hashlib
from pathlib import Path
from collections import Counter
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'cap/score_conf'
PATH=OUT/'CONF_R10.json'
d=json.loads(PATH.read_text())
rows=d['captures']
bycap={r['capture']:r for r in rows}
cams=json.loads((ROOT.parent/'cap/score_cam/CAMERA_ITEMS_R8.json').read_text())['items']

inventory=[
 ('Camera/pose confidence','Neither local (6D) nor global (5D) camera head predicts confidence.','Not computed','Absent','Absent','tree/student_pilot/g3t_vendor/vggt/heads/camera_head.py:40'),
 ('Local/global pose refinements, FoV and intrinsics','Camera heads refine pose encodings; only final iteration goes into raw_pose9. These are camera parameters, not quality scores.','Final raw_pose9; intermediate refinements discarded','K and camera matrices; no raw iterations','c2w only','tree/student_pilot/tower_read.py:255'),
 ('Depth and depth confidence','DPT predicts positive optical-axis depth and confidence 1+exp(logit); confidence is not a calibrated probability.','Native 32x51x51 grids in TowerState and TowerG3T dict; scale consumes them','Depth SHA256 only; neither grid','Neither grid','tree/student_pilot/tower_read.py:271'),
 ('World points and world-point confidence','DPT predicts XYZ and 1+exp(logit) confidence.','XYZ sampled to 32x51x51, transformed to frame 0, kept; confidence discarded immediately','Neither array (object lift summaries are downstream, not dense tower points)','Neither array','tree/student_pilot/tower_read.py:278'),
 ('Tower gravity_up and its validity','Converter derives reference-frame up from gravity-factorized tower cameras, with a Boolean validity result.','Both discarded after conversion; served gravity instead comes from checkpoint own head','Absent','Absent; gravity field is frozen own-head input','tree/student_pilot/_tower_native.py:95'),
 ('Trajectory step and camera validity mask','encode_cameras returns a translation scale statistic and per-frame validity mask; conversion checks validity.','Not retained in TowerState; not a metric-scale confidence','Absent','Absent','tree/student_pilot/_tower_native.py:93'),
 ('Tokens and normalization activations','Patch/camera/register tokens; frame/global attention features; LayerNorm statistics; camera refinement shift/scale/gate tensors. No scalar token-norm diagnostic is exported.','Selected layers 4,11,17,23 transient; served TowerG3T has no owner and exports no features','Absent','Absent','tree/student_pilot/_tower_native.py:9'),
 ('Metric scale and log scale','Service calls either ScaleHeadCall or OwnDepthScale; the latter takes a median own-depth/tower-depth ratio above clip-median confidence.','One positive scale applies once to depths and translations; log scale is transient','geometry.scale; constant per capture across primary reads','Frozen T1 scale, not a new arm prediction','b/e2e_reader/generate.py:39'),
 ('Scale eligibility and confidence threshold','Default service median_ratio computes finite/positive mask and median confidence; tower_scale_rule additionally gates own depth to (0.1,10) on its separate path.','Eligibility, ratio samples and confidence threshold are transient; no scale uncertainty retained','Absent','Absent','b/e2e_reader/stage1.py:66'),
 ('Checkpoint own gravity','Own gravity head supplies reference-camera up; gravity_reference_rotation normalizes it.','Used to define common gravity world; generated response also exposes own gravity','geometry.gravity_up is world [0,0,1]; normalized origin up recoverable as R0.T@[0,0,1]; original magnitude lost','Raw frozen own gravity vector','b/e2e_reader/real.py:64'),
 ('Checkpoint own depth and own poses','Own depth supplies scale by default; own pose9 is a separate prediction from tower pose9.','Prefill state; generate response exposes own pose9, not in the ground-capture writer','Absent; cannot pair own poses with these distance reads','Absent','b/e2e_reader/real.py:129'),
 ('Grid, crop, raster and frame mapping','grid_uv, coords_1024, source_hw, frame_indices, anchor_slots, world_to_frame0 are deterministic conversion/sampling metadata.','Grid/mapping retained; crop and world_to_frame0 transient','Indices, K, canvas_to_source and scale counters; no confidence','Frame IDs/slots/hashes/shapes; no confidence','b/e2e_reader/real.py:57'),
 ('Image/track outputs in vendor documentation','Vendor forward can return input images. Its docstring mentions tracks/visibility/conf, but implementation has no tracking head.','Served path calls selected heads directly, not vendor forward; no tracks computed','Absent','No image pixels or tracks','tree/student_pilot/g3t_vendor/vggt/models/g3t.py:65'),
 ('Downstream object scores and execution metadata','SAM3 proposal score/presence, selector logits, object lift/box features, timings and memory are recorded.','Separate object pipeline or execution telemetry; not per-frame G3T camera-confidence outputs','Present, outside requested G3T diagnostic scope','Execution/decode telemetry only; token is a run identifier','gpkg/runtime/c.py:55'),
]
d['quantity_inventory']=[dict(quantity=q,computation=c,served=s,captures=cap,k3d=k,source=src) for q,c,s,cap,k,src in inventory]

def explicit_rule(key,threshold,scope='all'):
    available=[r for r in rows if key in r['features'] and (scope=='all' or r['dataset']==scope)]
    flagged=[r for r in available if r['features'][key]>threshold]
    names={r['capture'] for r in flagged}
    return dict(feature=key,operator='>',threshold=threshold,scope=scope,
        flagged_captures=sorted(names),flagged_classes=dict(Counter(r['classification'] for r in flagged)),
        n_available=len(available),n_unmeasured=sum(key not in r['features'] and (scope=='all' or r['dataset']==scope) for r in rows),
        distance_items=sum(r['distance_items'] for r in flagged),
        camera_items={str(step):sum(r['step']==step and r['capture'] in names for r in cams) for step in (544,400)},
        missing_captures=[r['capture'] for r in rows if key not in r['features'] and (scope=='all' or r['dataset']==scope)])

d['illustrative_rules']=[explicit_rule('t1.origin_upright_angle_deg.mean',51),
    explicit_rule('t1.origin_upright_angle_deg.mean',51,'arkitscenes'),
    explicit_rule('t1.camera_gravity_x.rms',.085),
    explicit_rule('k3d_Aprime_vs_t1.rotation_deg.rms',1)]
d['rule_caveats']=[
 'Every rule and score direction is descriptive, selected on this n=38 cohort, with no held-out validation or multiplicity correction. ARKit has only two passing captures.',
 'Origin tilt and transported up measure predicted camera orientation, not error against independent gravity. Legitimate camera tilt or motion can trigger them.',
 'The origin tilt rule reads normalized checkpoint gravity directly; it does not require tower cameras. R0.T world-up recovers it from saved cameras.',
 'Motion and translation second differences are trajectory plausibility proxies, not independent self-consistency tests. Frame gaps vary; second difference is not physical acceleration.',
 'T2/T1 and K3d/T1 require two tower evaluations. K3d also changes preprocessing/numerical conditions; its difference is not isolated stochastic uncertainty.',
 'Dense anchor matrices equal T1 exactly: this is inherited geometry, not an independent validation.',
 'Camera fallback counts map flagged distance captures onto the R8 corpus (900 items per step). They are conditional capture-level routing counts, not recomputed exact camera-read flag decisions. The 37 camera-only captures have no flag assignment from these files.',
 'Distance fallback counts cover the 150 primary routed-distance items; 76 lie on the 38 GT captures. No counterfactual direct-answer score was measured.',
 'Missing features do not count as passes. K3d cannot define flags for 28/38 captures. ARKit binding remains unresolved under REPORT9.',
 'R8 gravity mean/max errors use GT up and cannot be read-time flags. All R10 candidate scores use only served predictions, not GT poses.',
]
# Independent rank-sum check of every AUC, including ties and cohort counts.
checked=0
for a in d['AUC']:
    rr=[r for r in rows if a['feature'] in r['features'] and (a['dataset']=='all' or r['dataset']==a['dataset'])]
    positives={'gross'} if a['comparison']=='gross_vs_pass' else {'gross','moderate'}
    rr=[r for r in rr if r['classification'] in positives|{'pass'}]
    labels=np.array([r['classification'] in positives for r in rr])
    values=np.array([r['features'][a['feature']] for r in rr])
    assert int(labels.sum())==a['n_positive'] and int((~labels).sum())==a['n_pass']
    if a['auc_high'] is None:continue
    rank=np.array([np.sum(values<v)+(np.sum(values==v)+1)/2 for v in values])
    n,m=a['n_positive'],a['n_pass']
    v=(rank[labels].sum()-n*(n+1)/2)/(n*m)
    assert abs(v-a['auc_high'])<1e-12
    checked+=1
for r in d['rules']:
    assert sum(bycap[c]['distance_items'] for c in r['flagged_captures'])==r['distance_items']
    assert r['flagged_class_counts'].get('pass',0)==0
assert sum(r['distance_items'] for r in rows)==76
receipt=json.loads((ROOT/'orchard_tower2x_c/returned/5.1.json').read_text())
raw=(ROOT/'orchard_tower2x_c/returned/5.json').read_bytes()
assert len(raw)==receipt['bytes'] and hashlib.sha256(raw).hexdigest()==receipt['sha256']
d['verification']=dict(independent_rank_sum_AUC_checks=checked,threshold_count_checks=len(d['rules']),
    distance_GT_items=76,k3d_receipt_verified=True,k3d_control_rms_reproduced=10,
    all_capture_schemas_scanned=True, all_primary_read_geometry_identical_within_capture=True,
    dense_anchors_equal_T1=38,CPU_threads=1,address_space_limit_GiB=18)
sourcepaths=[ROOT/'analyze_round10.py',ROOT/'render_round10.py',ROOT/'gpkg/runtime/c.py',ROOT/'gpkg/capture_io.py']
sourcepaths += [ROOT/'work/payload'/v['source'].split(':')[0] for v in d['quantity_inventory'] if not v['source'].startswith('gpkg/')]
sourcepaths += [ROOT/'work/payload/b/e2e_reader/geometry.py',ROOT/'work/payload/tree/student_pilot/g3t_vendor/vggt/heads/head_act.py',ROOT/'orchard_tower2x_c/2.py']
for p in set(sourcepaths):d['input_sha256'][str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
with PATH.open('w') as f:json.dump(d,f,indent=2,allow_nan=False);f.write('\n')

def table(headers,data):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in data])

amap={(r['feature'],r['dataset'],r['comparison']):r for r in d['AUC']}
def auc_cell(key,ds,comp):
    a=amap[key,ds,comp]
    return 'undefined (0/0)' if a['auc_high'] is None else f"{a['auc_high']:.3f} ({a['n_positive']}/{a['n_pass']})"
def auc_row(label,key):
    return [label]+[auc_cell(key,ds,c) for ds in ('all','arkitscenes') for c in ('gross_vs_pass','failing_vs_passing')]
headers=['Candidate (higher means flag)','All gross/pass','All fail/pass','ARKit gross/pass','ARKit fail/pass']
chosen=[('Metric scale','t1.scale.mean'),('World gravity components/norm (constant)','t1.world_gravity_norm.mean'),
 ('Origin up x','t1.origin_gravity_x.mean'),('Origin up y','t1.origin_gravity_y.mean'),('Origin up z (low is worse)','t1.origin_gravity_z.mean'),
 ('Origin tilt from camera-up, degrees','t1.origin_upright_angle_deg.mean'),
 ('Anchor tilt mean','t1.camera_upright_angle_deg.mean'),('Anchor tilt maximum','t1.camera_upright_angle_deg.max'),
 ('Camera-up x RMS','t1.camera_gravity_x.rms'),('Camera-up x maximum','t1.camera_gravity_x.max'),
 ('Consecutive rotation maximum','t1.consecutive_rotation_deg.max'),('Consecutive translation mean','t1.consecutive_translation_m.mean'),
 ('Translation second-difference RMS','t1.translation_second_difference_m.rms'),
 ('T2–T1 relative-rotation RMS','t2_vs_t1.rotation_deg.rms'),('K3d A′–T1 relative-rotation RMS','k3d_Aprime_vs_t1.rotation_deg.rms'),
 ('Dense–T1 anchor difference (inherited)','dense_vs_t1.anchor_camera_max_abs.mean')]
main_table=table(headers,[auc_row(label,key) for label,key in chosen])
summary='''Saved confidence cannot establish whether the tower recognizes its bad cameras: depth confidence is omitted, world-point confidence is discarded, and no pose-confidence head exists. Predicted orientation and motion provide descriptive proxies; they are not independent evidence of camera correctness.

The cohort contains 38 captures: 6 pass, 22 moderate, 10 gross. ARKit contributes 2 pass, 13 moderate, 8 gross; its classes remain conditional on the unresolved REPORT9 pose/RGB binding. AUC counts are positive/pass captures, not frames or items. Failing means moderate+gross.
'''
invtable=table(['Quantity','Computation','Served path','t1/t2/dense captures','K3d return','Source'],[
 [q,c,s,cap,k,src] for q,c,s,cap,k,src in inventory])
md=[summary,invtable,
 'All named quantities absent from the files have n=0 and undefined AUC; absence does not mean confidence is low. A valid depth-confidence summary would average finite confidence over pixels with finite positive depth in each frame, then average equally over frames. Neither those values nor valid-pixel counts are saved, so no such summary is recoverable.',
 'Scalar quantities have mean=min=max=value and zero std/range across their single capture value; they are not 32 independent measurements. Per-frame summaries use the same 32 anchors in every arm, with population std and max−min spread. All primary reads for a capture carry identical scale, gravity and cameras within each arm. T2 has 310 raw records; 150 eligible primary records enter this analysis, as do 150 each from T1/dense.',
 main_table,
 'The following table names every tested scalar candidate. AUC is for increasing values; decreasing-value flags have exactly 1−AUC (also stored explicitly in JSON). The 348 entries include repeated arms and correlated summaries; they are not independent tests. Rounding scores to ten decimals removes meaningless floating-point ties. No performance estimate accounts for selecting signs, summaries or thresholds on this cohort.',
 table(headers,[auc_row(key,key) for key in sorted(d['features'])]),
 'Per-capture summaries follow. Tilt lists mean/min/std/range in degrees; camera-up x lists mean/min/std/range. JSON additionally preserves every quantity’s mean, min, max, std, range and RMS, frame-level up vectors/motion, read counts and per-item fallback identities. Origin up is a unit vector in camera coordinates; captured world gravity is [0,0,1].',
 table(['Capture','Class','Arm','Scale','Origin up x,y,z','Tilt mean/min/std/range','Up x mean/min/std/range'],[
 [r['capture'],r['classification'],arm,f"{ds['scale']['mean']:.6g}",
 ', '.join(f"{ds['origin_gravity_'+a]['mean']:.6g}" for a in 'xyz'),
 '/'.join(f"{ds['camera_upright_angle_deg'][s]:.6g}" for s in ('mean','min','std','range')),
 '/'.join(f"{ds['camera_gravity_x'][s]:.6g}" for s in ('mean','min','std','range'))]
 for r in rows for arm,ds in r['diagnostics'].items() if 'scale' in ds]),
 'K3d A′–T1 is a 496-pair SO(3) difference per capture, independent of common world rotation and metric scale. All ten values reproduce the authenticated existing scorer:',
 table(['Capture','REPORT9 class','A′–T1 rotation RMS °'],[[r['capture'],r['classification'],f"{r['features']['k3d_Aprime_vs_t1.rotation_deg.rms']:.9f}"] for r in rows if 'k3d_Aprime_vs_t1.rotation_deg.rms' in r['features']]),
 'Illustrative rules use rounded, reviewable cutoffs; every cutoff and its resulting flags are descriptive with n=38. The K3d cutoff is the existing 1° control threshold and covers only ten captures. The orientation rule uses g=normalize(own gravity), tilt=acos(−g_y); saved cameras recover g as R0ᵀ[0,0,1]. The lateral-up rule uses sqrt(mean((R_iᵀ[0,0,1])_x²)) over anchors.',
 table(['Rule','Scope','Available/missing','Flagged classes','Distance items','Camera items per step','Flagged captures'],[
 [r['feature']+' > '+str(r['threshold']),r['scope'],f"{r['n_available']}/{r['n_unmeasured']}",r['flagged_classes'],r['distance_items'],r['camera_items'],', '.join(r['flagged_captures'])] for r in d['illustrative_rules']]),
 'For completeness, every feature/scope with gross/pass AUC ≥0.9 in either explicitly stated direction receives the same descriptive threshold convention: strictly beyond the worst passing score in that scope. This yields zero observed passing flags by construction, not by independent validation. Rules on T2 or K3d are hypothetical read-time policies; cross-run differences require both runs. Missing captures remain unknown. For scalar application, round the feature to ten decimals before comparing with these exact cutoffs.',
 table(['Candidate','Scope','Rule','Gross/pass AUC (n/n)','Flagged classes','Distance items','Camera items/step','Missing','Flagged captures'],[
 [r['feature'],r['scope'],r['operator']+' '+str(r['threshold']),f"{r['selected_direction_auc']:.3f} ({r['n_positive']}/{r['n_pass']})",r['flagged_class_counts'],r['distance_items'],r['camera_items']['544'],len(r['unmeasured_captures']),', '.join(r['flagged_captures'])] for r in d['rules']]),
 '\n'.join('- '+s for s in d['rule_caveats']),
 'Depth reprojection, dense point/depth agreement, tower-vs-own pose disagreement and independent tower-vs-own gravity disagreement are all undefined (n=0) from the requested files. They could be computed from live tensors without GT, but the inputs needed for an offline score were not captured. Cycle closure formed solely from one set of camera matrices is algebraically guaranteed and cannot diagnose those cameras.',
 'The R8 GT-gravity AUCs are reproduced below only to prevent mistaking them for available read-time confidence:',
 table(['Feature','Dataset','Comparison','AUC','Positive/pass'],[[r['feature'],r['dataset'],r['comparison'],f"{r['auc']:.6f}",f"{r['n_positive']}/{r['n_pass']}"] for r in d['GT_only_gravity_AUC']]),
 f"Validation: {checked} independent rank-sum AUC checks and {len(d['rules'])} threshold-count checks pass. All three capture hashes and the K3d return receipt match. Ten control RMS values reproduce; all 38 dense anchor camera arrays equal T1 exactly. Extraction took {d['runtime_seconds']:.2f} s and peaked at {d['peak_rss_KiB']/1024:.1f} MiB RSS, with one numerical thread and an 18 GiB address-space limit. No model inference ran.",
 'Reproducibility sources: analyze_round10.py and render_round10.py in gbuild. Source/input hashes, complete schema paths, every AUC and every fallback item identity are in CONF_R10.json. The extractor uses exclusive creation; do not rerun it over existing outputs.'
]
with (OUT/'CONF_R10.md').open('x') as f:f.write('\n\n'.join(md)+'\n')

r0,rark,rlat,rk=d['illustrative_rules']
short_inventory=table(['Quantity','Served path','Existing captures / K3d'],[
 ['Pose/camera confidence','No confidence head','Absent / absent; AUC undefined (n=0)'],
 ['Depth + depth confidence','Kept as 32×51×51 grids; scale consumes confidence','Depth hash only / omitted; confidence AUC undefined (n=0)'],
 ['World points + confidence','Points kept; confidence discarded','Both omitted / omitted; confidence AUC undefined (n=0)'],
 ['Tower gravity, trajectory step, validity','Conversion computes them, then discards them','Absent / absent'],
 ['Tokens, LayerNorm, refinement intermediates','Transient; no exported scalar token norm','Absent / absent'],
 ['Metric scale','One scalar from service scale path','Saved / frozen T1 input'],
 ['Checkpoint gravity','Defines gravity world; direction recoverable from R0','World [0,0,1] plus recoverable normalized origin up / frozen own-head vector'],
 ['Checkpoint own depth/pose','Depth supplies default scale; own poses distinct from tower','Absent / absent'],
 ['Crop/grid/indices/intrinsics','Sampling and binding metadata','Indices/K/transforms saved / IDs/slots saved; not confidence'],
])
report=[
 'The saved tower outputs do not include a camera-confidence score. Predicted orientation gives a descriptive flag: origin-camera tilt has gross/pass AUC 0.917 overall and 1.000 within ARKit. K3d A′–T1 instability also separates its five gross from two passing captures, but needs two runs and covers only ten captures.',
 'The cohort is 38 distance-GT captures (6 pass, 22 moderate, 10 gross); ARKit has 2 pass, 13 moderate, 8 gross. Classes follow CAMERA_SPLIT/REPORT9 and ARKit’s pose/RGB binding remains unresolved. Failing means moderate+gross. Every result and threshold is descriptive with n=38; subgroup and missing-feature counts are explicit.',
 short_inventory,
 'The full inventory distinguishes model outputs from transient conversion quantities, own checkpoint heads, and downstream SAM3/selector scores. G3T confidence is 1+exp(logit), not a calibrated probability. The vendor tracking outputs exist only in its docstring. gpkg/runtime/c.py:55 writes geometry without depth pixels, confidence, points, tokens or own pose9; all records confirm that omission.',
 'AUC below uses increasing scores and half credit for ties; counts are positive/pass captures. Low origin-up z reverses the listed direction. Every arm/summary and both directions appear in CONF_R10.md/JSON. Scalar scale/gravity summaries have no frame spread; per-frame statistics use mean, min, population std and max−min on 32 anchors.',
 main_table,
 'Origin tilt is acos(−g_y), where g is normalized checkpoint gravity in the origin camera; from captured c2w, g=R0ᵀ[0,0,1]. Anchor tilt and lateral-up RMS transport this predicted up through the tower poses. They measure predicted camera orientation, not disagreement with independent gravity. Motion statistics are plausibility proxies; legitimate motion can trigger them, and second differences are not time-normalized acceleration.',
 f"Illustrative read-time rule: if origin tilt >51°, use the direct answer. It flags {len(r0['flagged_captures'])}/38 captures: 8 gross, 11 moderate, 0 pass; {r0['distance_items']}/76 GT-overlap distance items ({r0['distance_items']}/150 total) and {r0['camera_items']['544']}/900 camera items at each step would map to fallback. Restricting the same rule to ARKit flags {len(rark['flagged_captures'])}/23 captures and {rark['distance_items']} distance items; the camera corpus has no ARKit items.",
 'The >51° rule flags ARKit '+', '.join(c.split('/')[1] for c in r0['flagged_captures'] if c.startswith('arkit'))+'; and ScanNet++ '+', '.join(c.split('/')[1] for c in r0['flagged_captures'] if c.startswith('scannetpp'))+'. It misses both non-ARKit gross captures.',
 f"Alternative: camera-up x RMS >0.085 flags {len(rlat['flagged_captures'])}/38 (8 gross, 5 moderate, 0 pass), {rlat['distance_items']} distance items and {rlat['camera_items']['544']} camera items per step. Its gross/pass AUC is 0.950 overall but 0.875 within ARKit. Complete capture lists and thresholds for every ≥0.9 candidate are in CONF_R10.md/JSON; none is validated on held-out captures.",
 f"K3d A′–T1 relative-rotation RMS >1° flags six measured ARKit captures: 41069054, 41291643, 42899535, 44358634, 45663051, 47332598 (5 gross, 1 moderate; {rk['distance_items']} distance items, 0 camera items). Its AUC is 1.000 (5/2) for gross/pass and 0.938 (8/2) for fail/pass. The other 28 captures remain unmeasured, not passing; this is not a one-pass read-time flag. Decode/numerical changes confound interpreting it as stochastic uncertainty.",
 'Camera fallback counts are capture-level mappings from the distance-read flags into the R8 corpus, conditional on transferring that flag across reads. They are not evaluations on the exact camera-read tensors. The 37 camera-only captures lack a flag assignment. No direct-answer counterfactual score was measured.',
 'Depth-confidence valid-pixel means, depth reprojection, point/depth consistency, tower-vs-own pose and tower-vs-own gravity disagreement are undefined (n=0): required tensors were not saved. R8’s gravity-error AUC 0.900 uses GT, so it cannot justify a read-time rule. Dense inherits T1 anchor geometry exactly and supplies no independent consistency test.',
 f"All capture hashes and the K3d receipt verify; 10 instability values reproduce the existing scorer. Independent rank-sum checks reproduce {checked} AUCs; all {len(d['rules'])} rule counts reconcile. Extraction: {d['runtime_seconds']:.2f} s, {d['peak_rss_KiB']/1024:.1f} MiB peak RSS, one numerical thread, 18 GiB address-space cap. No inference, SSH, Git, GPU, network, deletion or submission ran.",
 '[Full inventory, summaries, AUCs and rules](../cap/score_conf/CONF_R10.md) · [Machine-readable evidence](../cap/score_conf/CONF_R10.json). New analysis sources: analyze_round10.py and render_round10.py. All writes are new session files in gbuild or cap/score_conf.'
]
report='\n\n'.join(report)+'\n'
assert len(report.splitlines())<=80,len(report.splitlines())
with (ROOT/'REPORT10.md').open('x') as f:f.write(report)
print(json.dumps(dict(report_lines=len(report.splitlines()),checks=checked,rules=len(d['rules']),
    illustrative_rules=[{k:v for k,v in r.items() if k not in ('flagged_captures','missing_captures')} for r in d['illustrative_rules']])))
