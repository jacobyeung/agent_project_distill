"""Write outcome report and one-capture FoV diagnostics from authenticated receipts."""
import sys,numpy as np
from core import *
from tower_scale_rule import estimate

def main():
 out=ROOT/'out';cpu=read(out/'cpu_b_final/CPU_CHECK.json');tests=read(out/'TEST_RESULTS_B.json');sensitivity=read(out/'env_sensitivity_b/ENV_SENSITIVITY.json');env=read(KIT/'inputs/ENV_REQUIRED.json');stage=read(out/'STAGE_228_B.json')
 c=read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'][0];dest=out/'cpu_b_final/captures'/digest(c['canonical'])[:16];rec=read(dest/'PHASE_COMPLETE.json');checked(dest/'own.npz',rec['files']['own.npz'])
 pins={str(p):sha(p) for p in (out/'cpu_b_final/CPU_CHECK.json',dest/'PHASE_COMPLETE.json',dest/'own.npz',out/'TEST_RESULTS_B.json',out/'env_sensitivity_b/ENV_SENSITIVITY.json',out/'ENV_BOUNDARY_CHECK_FINAL_B.json',KIT/'inputs/ENV_REQUIRED.json',out/'STAGE_228_B.json',out/'BARS_FROZEN.json',out/'BARS_FROZEN_B.json',pathlib.Path(__file__),KIT/'tower_scale_rule.py',KIT/'inputs/TOWER_ONE.npz',KIT/'inputs/OWN544_ONE.npz')}
 with np.load(dest/'own.npz') as z:
  agreement={a+'-'+b:{'median_abs_degrees':float(np.median(np.abs(z['fov_'+a]-z['fov_'+b]))*180/np.pi),'vertical_median_abs_degrees':float(np.median(np.abs(z['fov_'+a][:,0]-z['fov_'+b][:,0]))*180/np.pi),'horizontal_median_abs_degrees':float(np.median(np.abs(z['fov_'+a][:,1]-z['fov_'+b][:,1]))*180/np.pi)} for a,b in [('B','V1'),('B','V2'),('V1','V2')]}
  grids={a:z[k] for a,k in [('B','depth'),('V1','depth_V1'),('V2','depth_V2')]}
 with np.load(KIT/'inputs/TOWER_ONE.npz') as z:t={k:z[k] for k in ('depth_grid','depth_conf_grid')}
 with np.load(KIT/'inputs/OWN544_ONE.npz') as z:da=z['depth']
 sa=estimate(t['depth_grid'],t['depth_conf_grid'],da)[0]
 fixture_scales={arm:estimate(t['depth_grid'],t['depth_conf_grid'],grid)[0] for arm,grid in grids.items()}
 atomic(out/'CPU_VARIANTS_B.json',{'input_sha256':pins,'synthetic':True,'status':'STUB only; pose and private FoV are random-weight fixture outputs, G3T FoV is real cached','capture':c['canonical'],'fov_agreement':{'arkitscenes':agreement},'OwnDepthScale544':sa,'fixture_scales':fixture_scales,'fixture_scale_ratios_vs544':{k:v/sa for k,v in fixture_scales.items()},'variant_seconds':rec['variant_seconds'],'command':'python -B kit/report_b.py'})
 methods={}
 src=out/'cpu_b_final/source/tree/student_pilot'
 for name in ('carrier_c1_decode.py','carrier_c1.py','g3t_online.py','camera_targets.py','point_depth_head.py','decoupled_vc.py'):
  p=src/name;methods[str(p)]=sha(p)
 atomic(out/'METHOD_SOURCES_B.json',{'input_sha256':{**methods,str(KIT/'inputs/A10b_code.tgz'):sha(KIT/'inputs/A10b_code.tgz'),str(KIT/'fov_variants.py'):sha(KIT/'fov_variants.py')},'serving_switch':'carrier_c1_decode.HeadState requires depth_fov_source=pose_head','V1':'carrier_c1.PrivateDepth.forward: 1e-4+(pi-2e-4)*depth.fov(captured.states.float()).sigmoid()','V2':'g3t_online.pose9 already unpads FoV; tower cache raw_pose[anchor_slots,7:9] is vertical,horizontal radians','extension':'fov_variants.encode_grid_with_fov; unchanged source HeadState parity covered by tests'})
 missing=[{'path':p['path'],'sha256':p['sha256'],'status':'MISSING locally'} for a in read(KIT/'inputs/ARCHIVES.json')['archives'] for p in a['parts'] if not pathlib.Path(p['path']).is_file()]
 atomic(out/'MISSING_B.json',{'input_sha256':{str(KIT/'inputs/ARCHIVES.json'):sha(KIT/'inputs/ARCHIVES.json'),str(KIT/'inputs/ENV_REQUIRED.json'):sha(KIT/'inputs/ENV_REQUIRED.json')},'inputs':missing,'real_scores':'MISSING: real B/V1/V2 captures expected in out/gpu_b/captures/<frozen-key>/own.npz','real_fov_agreement':'MISSING: real B/V1/V2 FoVs expected in those same payloads','real_cpu_result':'MISSING: expected out/cpu228_b/CPU_CHECK.json after user runs kit/cpu_check_228.sh'})
 synth=read(out/'synthetic_b_final/SCORE_RESULT.json');pins[str(out/'synthetic_b_final/SCORE_RESULT.json')]=sha(out/'synthetic_b_final/SCORE_RESULT.json')
 result={'input_sha256':pins,'command':'python -B kit/report_b.py','cpu':cpu,'fov_fixture':agreement,'tests':tests,'env_sensitivity':{k:sensitivity[k] for k in ('smallest_increase','closest_decrease')},'missing':missing,'real_variant_scores':'MISSING','real_cpu_result':'MISSING','extra_seconds_fixture':sum(rec['variant_seconds'].values())}
 atomic(out/'KIT_REPORT_B.json',result)
 up=sensitivity['smallest_increase'];down=sensitivity['closest_decrease'];delta=synth['displacement']['combined']['B-A']
 lines=[
 'The frozen-FoV kit is built. Real-weight CPU output, real V1/V2 scores, and dataset-wide real FoV agreement are MISSING. The target command is `kit/cpu_check_228.sh`; it must run on trinity-2-28 after the reader lane prepares its pinned runtime and assets.',
 '',
 f"All {tests['tests']} CPU tests pass. The one-capture fixture for arkitscenes/41048124 produces B, V1, and V2 grids with one LM pass and one private vision pass. The actual PointDepthHead test reproduces the unchanged HeadState pose-FoV path exactly; another test changes pose FoV and confirms V1/V2 grids stay fixed.",
 '',
 '`out/BARS_FROZEN.json` is unchanged. `out/BARS_FROZEN_B.json` freezes the variant arms before scoring. A is step 544 with pose-head FoV; B is step 400 with pose-head FoV. V1 uses the checkpoint’s private `depth.fov`; V2 uses cached G3T FoV. Only A/B can select the donor. V1/V2 comparisons against A and B are report-only, with the same folds, eligibility, metric and paired room bootstrap. Missing arms are explicitly listed and contrasts use paired capture support.',
 '',
 'The serving switch rejects non-pose FoV. `kit/fov_variants.py` therefore adds a separate explicit-FoV encode/query function. It captures the private features from the unchanged serving call and runs two additional head encodes/queries. V1 computes `1e-4 + (pi-2e-4)*sigmoid(depth.fov(captured.states.float()))`. This private branch is unused for training when pose-head conditioning is active, so its calibration is an empirical question.',
 '',
 'G3T’s `pose9` already converts square-raster FoV to the source raster as `2*atan(crop_hw*tan(local_fov/2))`. The cached `raw_pose[anchor_slots,7:9]` therefore needs no second conversion. Its columns match the depth head’s vertical/horizontal radians. The builder authenticates cache hashes, capture identities and anchor indices. Every capture saves `fov_B`, `fov_V1`, `fov_V2`, `depth_V1`, and `depth_V2` beside `depth` in `own.npz`; a missing module yields an explicit MISSING receipt.',
 '',
 f"The fixture forward took {rec['seconds']:.6f} seconds. V1 added {rec['variant_seconds']['V1']:.6f} seconds and V2 added {rec['variant_seconds']['V2']:.6f} seconds, measured inside the shared pass. Total fixture wall time was {cpu['seconds']:.3f} seconds; peak RSS was {cpu['peak_rss_bytes']:,} bytes. These small random-weight timings do not predict checkpoint GPU latency. Production receipts measure each arm separately. All three share the existing 4,320-second hard GPU cap; there is no extra GPU allocation.",
 '',
 'The CPU fixture’s median absolute FoV differences are shown below. Only its G3T values come from a real cached model; the pose/private values are fixture outputs. Real per-dataset values remain MISSING until real captures return.',
 '', '| Dataset / fixture | Pose–private | Pose–G3T | Private–G3T |','|---|---:|---:|---:|',f"| ARKitScenes, 32 anchors, degrees | {agreement['B-V1']['median_abs_degrees']:.6f} | {agreement['B-V2']['median_abs_degrees']:.6f} | {agreement['V1-V2']['median_abs_degrees']:.6f} |",'',
 f"The synthetic scorer smoke run covers {synth['captures']} captures and {synth['pairs']:,} eligible pairs. Its V1 and V2 fixture grids equal B=1.014*A depth, so V1−B and V2−B are zero. Combined B−A is {delta['points']:.6f} MRA points, with 95% CI [{delta['ci95'][0]:.6f}, {delta['ci95'][1]:.6f}]. These are plumbing checks, not step-400 results. The full routed-distance path is implemented but was not run for this fixture; the displacement smoke and unit suite passed.",
 '',
 f"The required interpreter is `{env['target_python']}` with `-B -I`, using base environment `{env['base_env']}`. The pin requires Torch 2.13.0+cu130, Transformers 5.19.0, torchvision 0.28.0+cu130, and SciPy 1.14.1. `ENV_REQUIRED.json` records the reader plan, receipt, runtime parts, and a2/a3/a4 hashes. The launcher checks archive hashes, module versions, and module roots before running. Every new receipt records the required environment; capture bindings also record observed Torch/Transformers/NumPy versions. Fixture receipts explicitly mark synthetic weights.",
 '',
 'The environment is a confound: step 400 runs under Torch 2.13 while A’s step-544 grids came from Torch 2.11.0+cu129 / Transformers 5.12.1. The decision rule remains unchanged. The sensitivity check defines synthetic B scale as m times A’s OwnDepthScale, and sweeps every metric boundary outward from m=1 without assuming monotonicity. It does not measure an actual environment shift.',
 '',
 f"The smallest increasing multiplier is **{up['multiplier']:.16g}**, or **+{up['percent_shift']:.9f}%**. The immediately preceding representable float still selects 400; this multiplier selects 544. The closest decreasing multiplier is {down['multiplier']:.16g}, or {down['percent_shift']:.6f}%. The increasing boundary has tiny margins; it should not be treated as a measured numerical error tolerance.",
 '', '| Increasing multiplier contrast | B−A MRA points | 95% CI |','|---|---:|---|']
 for name,item in zip(('fold1','fold2','combined'),up['B-A']):lines.append(f"| {name} | {item['points']:.9f} | [{item['ci95'][0]:.9f}, {item['ci95'][1]:.9f}] |")
 lines += ['',
 '`kit/cpu_check_228.sh` exposes no GPUs, uses nice 10 and eight threads, and stops at 39 GB RSS. It loads step-400 weights once and forwards only arkitscenes/41048124. It writes all three grids, their OwnDepthScale values, their scale ratios to the bundled 544 grid, and median grid ratios. A BF16 unsupported-operation error alone allows a float32 retry for this CPU run; the receipt records the error and dtype change. Other errors stop. No real forward or target verification was performed here.',
 '',
 f"`out/STAGE_228.txt` and `out/STAGE_228_B.json` separate reported target files from the {stage['copy_bytes']:,} bytes to copy. The reader lane must relocate its base runtime; a2/a3/a4 alone do not provide it. The local wrapper still contains an Orchard interpreter path. Exact missing local inputs are listed in `out/MISSING_B.json`. Earlier outputs remain, and the input kit snapshot is in `out/kit_before_b`.",
 '',
 'Commands producing the reported numbers, from this workspace (CPU Python `/scratch/jjyeung/envs/p1cpu/bin/python`):',
 '', '```bash',
 'export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES=',
 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/build_b.py',
 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/cpu_stub.py --out out/cpu_b_final',
 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/test_400b.py',
 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/env_sensitivity.py --out out/env_sensitivity_b',
 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/score_400b.py --synthetic --displacement-only --out out/synthetic_b_final',
 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/check_env_boundary.py',
 'python -B kit/finalize_b.py',
 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/report_b.py',
 '```','',
 'The builder refuses to overwrite frozen variant bars. Use fresh output names when reproducing forwards or scores. Boundary verification is recorded in `ENV_BOUNDARY_CHECK_FINAL_B.json`; source, input and output hashes accompany the JSON results.',
 '',
 'After staging, the user can run:',
 '', '```bash','kit/cpu_check_228.sh','# GPU run only when the coordinator authorizes it:','kit/launch_gpu.sh --card <i>','# Score returned captures on 1-18:','env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/score_400b.py --own-root out/gpu_b/captures --out out/real_score_b','```','',
 'The no-archaeology skill governs this report. The environment comparison remains because it defines the requested confound. No GPU, SSH, network, Git, tmux operation, process termination, or external write was performed.'
 ]
 (out/'KIT_REPORT_B.md').write_text('\n'.join(lines)+'\n')
 (ROOT/'STATUS.md').write_text(f"The frozen-FoV kit is complete with {tests['tests']} passing CPU tests, exact pose-path parity, and a three-source stub capture. The reader runtime is pinned, the guarded one-capture 2-28 CPU command is ready, and staging files are updated. Synthetic sensitivity flips the unchanged rule at multiplier {up['multiplier']:.16g} (+{up['percent_shift']:.9f}%). Real step-400 scores, real FoV agreement, and the target CPU result remain MISSING pending staged runtime/weights and user execution. See out/KIT_REPORT_B.md.\n")
if __name__=='__main__':main()
