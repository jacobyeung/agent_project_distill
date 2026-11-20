"""Render the R8 audit without exposing held-out text or wording partitions."""
import json,time,hashlib
from pathlib import Path
from round7_common import table
ROOT=Path(__file__).resolve().parent;OUT=ROOT.parent/'cap/score_cam';CAM=Path('/scratch/jjyeung/orch_n30/cont_ops25_c/cam');TREE=ROOT/'work/payload/tree'
x=json.loads((OUT/'CAMERA_ITEMS_R8.json').read_text());f=json.loads((OUT/'CAPTURE_FEATURES_R8.json').read_text());p=json.loads((CAM/'out/INPUTS_R8.json').read_text())
def wt(path,s):
    with path.open('x') as out:out.write(s+'\n')
def link(path,line=None):return f'[{path.name}{":"+str(line) if line else ""}]({path}{":"+str(line) if line else ""})'
def fmt(a,n=None):
    if a['mean'] is None:return 'undefined (n=0)'
    s=f"{100*a['mean']:.1f} [{100*a['ci95'][0]:.1f}, {100*a['ci95'][1]:.1f}]"
    return s+(f' (n={n})' if n is not None else '')
def cell(step,ds,cls,typ):return next(r for r in x['tables'] if (r['step'],r['dataset'],r['capture_class'],r['type'])==(step,ds,cls,typ))
def accuracy_table(datasets):
    out=[]
    for ds in datasets:
      for step in (544,400):
       for cls in ('pass','moderate','gross','unclassified-GT','no-GT','all'):
        a=cell(step,ds,cls,'all');out.append(([ds] if len(datasets)>1 else [])+[step,cls,a['captures'],a['items'],*[fmt(cell(step,ds,cls,t)['accuracy'],cell(step,ds,cls,t)['items']) for t in ('displacement','rotation','direction')],fmt(a['accuracy'])])
    return table((['Dataset'] if len(datasets)>1 else [])+['Step','Class','Captures','Items','Displacement % [95% CI]','Rotation % [95% CI]','Direction % [95% CI]','All % [95% CI]'],out)
def loss_table(datasets):
    return table((['Dataset'] if len(datasets)>1 else [])+['Step','Type','Total loss','Reconstructed gross loss','Observed gross share %','Possible full share %'],
      [([r['dataset']] if len(datasets)>1 else [])+[r['step'],r['type'],f"{r['total_loss']:.1f}",f"{r['reconstructed_gross_loss']:.1f}",f"{100*r['observed_gross_share']:.1f}",f"{100*r['possible_gross_share_range'][0]:.1f}–{100*r['possible_gross_share_range'][1]:.1f}"] for r in x['loss'] if r['dataset'] in datasets])
def auc_table(dataset='all'):
    rr=[r for r in f['AUC'] if r['dataset']==dataset];names=list(dict.fromkeys(r['feature'] for r in rr))
    def ac(n,c):
        r=next(r for r in rr if r['feature']==n and r['comparison']==c)
        return ('undefined' if r['auc'] is None else f"{r['auc']:.3f}")+f" ({r['n_positive']}/{r['n_pass']})"
    return table(['Feature','Gross/pass AUC (n/n)','Fail/pass AUC (n/n)'],[[n.replace('_',' '),ac(n,'gross_vs_pass'),ac(n,'fail_vs_pass')] for n in names])
opening=accuracy_table(['all'])
limitation=('Pass/moderate/gross are **approximate distance-tower reconstructions on 15 overlapping GT captures**, not poses recovered from these camera logs. '
'The logs contain the checkpoint’s own poses: 0/1,025 move calls and 12/450 turn calls replay exactly; multiplying by the tower scale still matches 0 moves. '
'The reconstruction matches 834/842 calls exactly (564/572 moves and 270/270 turns); all eight differences are 0.01 m. '
'Its missing 51 step-400 scales belong to uncalled items; their capture classes use the called items, whose classes are uniform within each capture. '
'No scale is imputed for their per-item distance ratios. Nineteen GT captures remain unclassified; 18 captures lack GT. The full requested tower-class audit is therefore incomplete.')
score=('Scores use `arms.tower.score`, equal to `arms.tower.scores.answer` and `raw.arms.tower.output.scores.answer` on all 1,800 records. '
'Displacement and rotation use the record’s `official_vsi_mra`; direction uses `official_exact_match`. “Accuracy” here means the mean recorded score, expressed as a percentage. '
'Intervals use 10,000 item-weighted bootstrap draws of the 37 corpus rooms (`raw.arms.tower.room_key`), seed 20261120, shared across steps and groups. '
'JSON counts undefined draws, which are omitted from percentiles. No wording groups or question text enter the outputs.')
lossnote=('Loss is Σ(1 − score). Observed gross shares are contributions from the two reconstructed gross captures, not estimates of the full gross share. '
'The ranges assign all remaining unclassified/no-GT loss first to nongross and then to gross, conditional on the reconstructed classes; they are not confidence intervals.')
feature_note=('The feature union contains 57 unique captures: 38 distance GT captures plus 19 additional camera GT captures (15 overlap). '
'AUCs use the 38 distance captures with established classes: 10 gross, 22 moderate, 6 pass. The additional 19 have no served tower classes. '
'AUC = P(failure feature > pass feature) + ½ ties; values below 0.5 retain their direction. These are descriptive comparisons with only six passing captures, not a selected diagnostic or a causal test.')
motion=('The manifests specify 64 tower inputs for 862/900 camera items and 32 for 38/900, at both steps; 32 pose entries are output anchors, not proof of 32 tower inputs. '
'The feature union has 33 captures with 64 inputs and 24 with 32. GT covers only 32 anchors, so motion/overlap statistics on “consecutive anchors” do not measure every consecutive pair in a 64-frame tower input. '
'Exact consecutive-tower metrics are null for those captures. ARKit durations use nominal fps. Trajectory extent is the maximum pairwise camera-centre distance; the JSON also gives the bounding-box diagonal.')
orientation=('GT image orientation uses Rᵀ[0,0,1]: negative/positive camera y gives upright/upside-down when |y|≥|x|; otherwise positive/negative x gives sideways-left/right camera tilt. '
'It measures the projected up direction, including camera roll; it does not establish an EXIF or upstream decode error. '
'Predicted gravity is the checkpoint’s gravity head used by the tower service, transported into each anchor using the served distance-camera rotations. Camera-only captures have origin-gravity errors, but no inferred per-anchor errors.')
conclusion=('Translation gaps separate gross captures more strongly than native portrait orientation (AUC 0.858 versus 0.517); GT non-upright share also separates them (0.800). '
'For all failures, the corresponding AUCs are 0.786, 0.542 and 0.672. Neither property perfectly separates the groups. '
'The association varies by dataset: non-upright share has gross/pass AUC 0.875 in ARKit (8/2), but 0.500 in ScanNet++ (2/3); translation-gap share gives 0.625 and 1.000 respectively. ScanNet has no gross capture in this cohort.')
inputpath=(f'The tower preserves native RGB orientation: {link(TREE/"student_pilot/tower_read.py",23)} names `native_square_pad_bicubic_1024_bilinear_518_v1`; '
 f'{link(TREE/"student_pilot/tower_read.py",220)} takes native RGB, and lines 236–238 apply square preprocessing then bilinear 518×518 interpolation. '
 f'{link(TREE/"student_pilot/g3t_vendor/vggt/utils/load_fn.py",53)} centres the image on a black square and line 77 resizes it bicubically to 1024; no orientation transpose occurs. '
 f'{link(ROOT/"work/payload/b/e2e_reader/real.py",43)} passes these native images to the tower.')
samedecode=(f'The answering and tower anchors use the **same pinned PNG source decode**, verified by frame-index and SHA256 equality in '
 f'{link(ROOT/"work/payload/b/e2e_reader/parity.py",65)} and checked against all camera records here. They are loaded separately, not shared as one in-memory decode: '
 f'{link(ROOT/"work/payload/b/e2e_reader/parity.py",80)} opens tower images; '
 f'{link(TREE/"student_pilot/carrier_c1_data.py",183)} loads answering frames through {link(TREE/"student_pilot/pose_samples.py",172)}. '
 'Neither path rotates the PNG. This checks the pinned rasters, not an independent native RGB-to-GT sensor binding.')
logging=(f'The evidence gap is explicit in {link(ROOT/"work/payload/b/e2e_reader/real.py",129)} and '
 f'{link(ROOT/"work/payload/h1eval/reader_core/e2e_reader/real.py",106)}: `heads.pose9` is `state.heads.pose9`. '
 f'Tools instead use `from_tower` in {link(ROOT/"work/payload/b/e2e_reader/generate.py",46)} and `ReadServers` in '
 f'{link(ROOT/"work/payload/b/e2e_reader/servers.py",15)}. '
 f'{link(ROOT/"work/payload/b/e2e_reader/geometry.py",63)} decodes frozen tower pose9 and applies one metric scale; '
 f'{link(TREE/"student_pilot/camera_targets.py",149)} defines the inverse relative pose, and '
 f'{link(TREE/"student_pilot/_tower_native.py",68)} defines native tower conversion. '
 'The missing evidence is the per-read served tower raw pose9 or metric camera matrices, anchor binding, scale and gravity, for these exact reads.')
methods=('Rigid fitting reuses `gt.v2.alignment`: no fitted scale, centre rank ≥2, translation RMS ≤0.10 m, every anchor rotation ≤5°. '
'Gross means rigid rotation max >60°; other failures are moderate. All 496 unordered anchor-pair residuals use `project_round6.pair_errors`, unchanged from REPORT6. '
'Asked-pair rotation error compares the full relative SO(3) transforms; direction error compares camera-i translation vectors; ratio is predicted/GT baseline length. '
'The independently available served-call bins use printed move vectors/distances and gravity-level yaw, with GT formatted by the same payload formatter; their 0.01 m/1° rounding is explicit. Yaw error is not full relative SO(3) error.')
price=('The served asked-pair bins show a direct cost where calls expose the required quantity. At step 544, displacement scores average 92.7% for distance ratio [0.8,1.2) (133 items), '
'38.0% for [0.5,0.8) (10), 32.0% for [1.2,2) (15), and 0% for ≥2 (3). Direction scores are 100% below 30° (179 items) and 0% at ≥30° (10). '
'Rotation scores average 78.0% below 5° served yaw error (128), versus 54.6% at 5–15° (13). These are GT-available items with a served call on the asked pair; uncalled items are excluded, so these are associations, not repair effects.')
compare=('All 15 reconstructed GT captures keep their class across steps and distance reads: 4 pass, 9 moderate, 2 gross. '
'The gross captures are `scannetppv2/307e3262f1` and `scannetppv2/80ffca8a48`. This agreement is not independent replication: the reconstruction reuses frozen distance-camera geometry. '
'Comparisons for the other camera captures remain unavailable.')
missing=table(['Capture without local GT','Items at 544','Items at 400'],[[r['capture'],r['items_per_step']['544'],r['items_per_step']['400']] for r in x['no_GT']])
items_md=[accuracy_table(['all','scannet','scannetppv2']),limitation,score,loss_table(['all','scannet','scannetppv2']),lossnote,methods,price,compare,logging,
 'Missing GT captures (324 items per step):',missing,
 table(['Step','Source of poses','Tool','Calls','Exact matches','Within one printed unit'],[[r['step'],r['source'],r['tool'],r['total'],r['exact'],r.get('within_one_print_unit','not tested')] for r in x['replay']]),
 'Per-capture fits and all-pair errors (approximate reconstruction):',
 table(['Step','Capture','Class','Items','Translation RMS m','Rotation max °','Relative rotation RMS °','Relative translation RMS m'],[[c['step'],c['capture'],','.join(c.get('class_range',[])) or 'unavailable',c['items'],*[f'{v:.4f}' if v is not None else 'unavailable' for v in ((c.get('rigid_fit') or {}).get('translation_rms_m'),(c.get('rigid_fit') or {}).get('rotation_max_deg'),(c.get('relative_errors') or {}).get('rotation_deg',{}).get('rms'),(c.get('relative_errors') or {}).get('translation_m',{}).get('rms'))]] for c in x['captures']]),
 'Full asked-pair error bins on reconstructed poses; empty cells are omitted:',
 table(['Step','Dataset','Type','Error','Bin','Items','Accuracy % [95% CI]'],[[r['step'],r['dataset'],r['type'],r['error'],r['bin'],r['items'],fmt(r['accuracy'])] for r in x['asked_pair_bins'] if r['items']]),
 'Served asked-pair error bins against GT, including all available GT captures; empty cells are omitted:',
 table(['Step','Dataset','Type','Error','Bin','Items','Accuracy % [95% CI]'],[[r['step'],r['dataset'],r['type'],r['error'],r['bin'],r['items'],fmt(r['accuracy'])] for r in x['served_asked_pair_bins'] if r['items']])]
wt(OUT/'CAMERA_ITEMS_R8.md','\n\n'.join(items_md))
feat_md=[feature_note,auc_table(),orientation,motion,conclusion,inputpath,samedecode,
 'Capture features; all per-anchor orientations, gravity errors, source indices, temporal statistics, and class availability are retained in the JSON.',
 table(['Capture','Distance class','RGB H×W','Tower frames','Span s','Upright/upside-down/left/right shares','Gravity mean/max °','Anchor rot mean/max °','Anchor translation mean m','Overlap proxy','Extent m'],[[r['capture'],r['distance_class'] or 'unclassified','×'.join(map(str,r['native_rgb_hw'])),len(r['tower_source_frame_indices']),f"{r['features']['time_span_s']:.2f}",'/'.join(f"{r['features']['orientation_'+k+'_share']:.3f}" for k in ('upright','upside_down','sideways_left','sideways_right')),('/'.join(f"{r['features'][k]:.2f}" for k in ('gravity_mean_deg','gravity_max_deg')) if r['features']['gravity_mean_deg'] is not None else 'unavailable'),'/'.join(f"{r['features'][k]:.2f}" for k in ('consecutive_anchor_rotation_mean_deg','consecutive_anchor_rotation_max_deg')),f"{r['features']['consecutive_anchor_translation_mean_m']:.3f}",f"{r['features']['overlap_proxy_either']:.3f}",f"{r['features']['trajectory_diameter_m']:.3f}"] for r in f['captures']])]
for ds in ('arkitscenes','scannet','scannetppv2'):feat_md += [f'Dataset: {ds}',auc_table(ds)]
wt(OUT/'CAPTURE_FEATURES_R8.md','\n\n'.join(feat_md))
commands='''```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
/scratch/jjyeung/envs/p1cpu/bin/python -B analyze_round8.py
/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest test_round8 -v
/scratch/jjyeung/envs/p1cpu/bin/python -B render_round8.py
sha256sum --check SHA256SUMS8
```'''
hash_table=table(['Input','SHA256'],[[Path(k).name,v] for k,v in p['files'].items() if Path(k).suffix=='.gz' or Path(k).name in ('need.json','c25_gt34.sha','GT.json','FRAMES.json','DENSE_MANIFEST.json')])
end=(f'Seven tests passed: payload encode/decode, rigid and relative invariance, score/loss reconciliation, replay, GT overlap, feature counts/AUCs, and held-out field exclusion. '
 f'All 34 c2w member hashes match label provenance; file hashes are the supplied `c25_gt34.sha` values matched to `need.json`, not a new full-file rehash. '
 f'The optional 254 MB full-file hash check was not run because the required heavy-I/O approval has not arrived. '
 f'Analysis runtime: {p["runtime_seconds"]:.2f} s; peak RSS {p["max_rss_KiB"]/1024:.1f} MiB; one numerical thread and a 15 GiB address-space limit. '
 'No GPU, SSH, Git, network, deletion or job submission ran. No earlier delivery changed.')
report=[opening,limitation,score,loss_table(['all']),lossnote,auc_table(),feature_note,motion,orientation,conclusion,inputpath,samedecode,logging,methods,price,compare,
 f'Complete dataset tables, bins, missing-GT capture counts and per-item errors: {link(OUT/"CAMERA_ITEMS_R8.md")} and {link(OUT/"CAMERA_ITEMS_R8.json")}. '
 f'All 57 capture features and dataset AUCs: {link(OUT/"CAPTURE_FEATURES_R8.md")} and {link(OUT/"CAPTURE_FEATURES_R8.json")}.',commands,
 f'Input hashes (all consumed direct source/input pins and member provenance are in {link(CAM/"out/INPUTS_R8.json")}):',hash_table,end]
s='\n\n'.join(report)+'\n';assert len(s.splitlines())<=150,len(s.splitlines());wt(ROOT/'REPORT8.md',s)
paths=[ROOT/n for n in ('analyze_round8.py','render_round8.py','test_round8.py','REPORT8.md')]+sorted(OUT.glob('*R8.*'))+sorted((CAM/'out').glob('*R8*'))
with (ROOT/'SHA256SUMS8').open('x') as out:
    for path in paths:
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        out.write(digest+'  '+str(path)+'\n')
print(json.dumps(dict(report_lines=len(s.splitlines()),manifest_files=len(paths),rendered=True)))
