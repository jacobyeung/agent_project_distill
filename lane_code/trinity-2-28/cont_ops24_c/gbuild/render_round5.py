"""Render per-capture camera evidence without modifying stage results or deliveries."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent/'cap/score_t2'


def main():
    z = json.loads((OUT/'CAMERA_CONVENTIONS_T2.json').read_text())
    lines = [
        'The available evidence does not support changing the GT camera convention. The current OpenCV camera-to-world interpretation passes 6/38 captures; each of the three alternatives passes zero. The ruling remains a center-only rigid fit with no scale, translation RMS ≤0.10 m, and every anchor rotation residual ≤5°.',
        '',
        'All 38 NPZ frame-index lists exactly match the task, reference, T2 capture, captured geometry, RGB manifest, and dense-anchor slots in order. Reader RGB hashes also match the T2 receipt. This verifies the recorded binding, but not the original native RGB-to-pose association: the NPZ files contain no RGB hashes, native frame IDs, or sensor timestamps, and no exact builder configuration/calibration/selection sidecars were found in the supplied payload or kit. Native source numbering therefore remains unverified for every capture.',
        '',
        'For ARKit, the RGB manifest supplies integer frame labels, a nominal 10 Hz rate, timestamps computed as index/10, and a last-anchor+1 lower bound on frame count. These synthetic timestamps do not identify an ARKit trajectory row. The reader opens hash-pinned PNGs in manifest order; it does not seek by timestamp. No code establishes an offset or alternative permutation, so none was searched.',
        '',
        'The code establishes the reader convention. The tower composes OpenCV world-to-camera extrinsics and inverts them in [_tower_native.py](../../../gbuild/work/payload/tree/student_pilot/_tower_native.py:94). [camera_targets.py](../../../gbuild/work/payload/tree/student_pilot/camera_targets.py:149) decodes relative extrinsics to camera-to-world poses and left-multiplies one gravity rotation. [geometry.py](../../../gbuild/work/payload/b/e2e_reader/geometry.py:62) binds anchor slots; [geometry_profiles.py](../../../gbuild/work/payload/tree/student_pilot/geometry_profiles.py:132) applies the deployed scale once to centers and depth. The captured metric and unscaled poses reproduce that scaling for every observed record.',
        '',
        'The available [native GT builder](../../../gbuild/work/payload/tree/generator/derivgen_v7/derivgen/native.py:129) requires `opencv_c2w_raw_z_up_m`, checks calibration indices against selected RGB indices, and stores `camera_poses` as `c2w`. Its output schema matches these NPZs, but the exact file lineage is not established. This code and the `c2w` field favor the current interpretation. The other hypotheses are explicitly requested ambiguity checks, not conventions established by the builder. No convention was selected by fit, either per capture or per dataset.',
        '',
        'For stored pose P, the four hypotheses are C=P (c2w_cv), C=P·F (c2w_gl), C=P⁻¹ (w2c_cv), and C=P⁻¹·F (w2c_gl), where F=diag(1,−1,−1,1). F changes camera axes on the right, preserving camera centers. Each hypothesis refits one proper rigid transform from the same 32 paired centers, then checks all rotations. Repeated point/restricted records have identical camera arrays in every capture; using one unique array reproduces the full-record stage fits within 10⁻⁵.',
        '',
        'A world-up change left-multiplies all GT poses by a common proper rotation, which the unrestricted rigid fit absorbs exactly. A +90° x-axis control changes the reported residuals by at most %.3g (metres/degrees). Thus a different common world up cannot explain these failures. A camera-axis change alone also cannot reduce center residuals.' % max(max(r['world_up_control']['residual_absolute_deltas'].values()) for r in z['captures']),
        '',
        '| Dataset | Captures | c2w_cv passes | c2w_gl passes | w2c_cv passes | w2c_gl passes | Similarity numeric passes, c2w_cv |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for d,s in z['summary'].items():
        h=s['hypotheses']
        lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (d,s['captures'],*(h[k]['rigid_accepted'] for k in z['hypotheses']),h['c2w_cv']['similarity_numeric_passes']))
    lines += ['', 'The following table reports translation RMS in metres / rotation maximum in degrees for every rigid fit. Rotation RMS and all 32 per-anchor residuals are in the JSON; the CSV also provides each hypothesis’s rotation RMS, maximum, similarity scale, and similarity RMS. “Pass” applies only to c2w_cv; every alternative fails.', '',
              '| Capture | c2w_cv: m / ° | c2w_gl: m / ° | w2c_cv: m / ° | w2c_gl: m / ° | Current ruling |',
              '|---|---:|---:|---:|---:|---|']
    flat=[]
    for r in z['captures']:
        values=[]
        for h,f in r['hypotheses'].items():
            a=f['rigid'];s=f['similarity_diagnostic'];q=f['rotation_only_diagnostic']
            values.append('%.4f / %.2f' % (a['translation_rms_m'],a['rotation_max_deg']))
            flat.append(dict(capture=r['capture'],hypothesis=h,accepted=a['accepted'],
                translation_rms_m=a['translation_rms_m'],rotation_rms_deg=a['rotation_rms_deg'],rotation_max_deg=a['rotation_max_deg'],
                similarity_scale=s['scale'],similarity_translation_rms_m=s['translation_rms_m'],
                similarity_rotation_max_deg=s['rotation_max_deg'],similarity_numeric_pass=s['would_meet_numeric_ruling'],
                rotation_fit_translation_rms_m=q['translation_rms_m'],rotation_fit_rotation_rms_deg=q['rotation_rms_deg'],
                rotation_fit_rotation_max_deg=q['rotation_max_deg'],
                pairwise_rotation_disagreement_deg=f['pairwise_rotation_invariant']['max_relative_angle_disagreement_deg'],
                stored_frame_binding_exact=all(r['frame_binding']['checks'].values()),native_source_numbering_verified=False))
        lines.append('| %s | %s | %s |' % (r['capture'],' | '.join(values),'Pass' if r['hypotheses']['c2w_cv']['rigid']['accepted'] else 'Fail'))
    lines += ['', 'Similarity scale s multiplies the reader’s already-metric centers before the rigid transform; it is not the deployed scale. The center least-squares optimum is s=Σ[(R(x−x̄))·(y−ȳ)]/Σ||x−x̄||² with the same proper Kabsch R. It changes no rotation residuals and is never used for S4. Scale contributes to some translation errors, but is insufficient for the large failures: ARKit 41069053 remains at 1.2450 m with s=0.8227, and 41069054 remains at 1.0996 m with s=0.8288. Even allowing diagnostic scale produces no additional passes under the current fit and thresholds.', '',
              'For a separate rotation-consistency diagnostic, R is the proper chordal mean of BᵢAᵢᵀ and t aligns mean centers, with scale fixed to one. This avoids an arbitrary metre/degree weighting. It is not the stage fit. A second diagnostic compares relative rotation angles for every anchor pair. These angles survive any fixed world rotation and any fixed camera-axis rotation; a disagreement above 10° rules out ≤5° residuals at both anchors under any such correction. This necessary-condition test excludes 17/23 ARKit and 3/11 ScanNet++ captures (20 total), irrespective of scale. It cannot identify whether the error comes from the predicted trajectory or the underlying RGB-to-pose association.', '',
              '| Capture | Deployed scale | Diagnostic s | Similarity RMS m | Rotation-fit RMS m / max ° | Max pair-angle disagreement ° |',
              '|---|---:|---:|---:|---:|---:|']
    for r in z['captures']:
        f=r['hypotheses']['c2w_cv'];s=f['similarity_diagnostic'];q=f['rotation_only_diagnostic']
        lines.append('| %s | %.4f | %.4f | %.4f | %.4f / %.2f | %.2f |' % (r['capture'],r['reader']['scale'],s['scale'],s['translation_rms_m'],q['translation_rms_m'],q['rotation_max_deg'],f['pairwise_rotation_invariant']['max_relative_angle_disagreement_deg']))
    lines += ['', 'Changing the fit objective can affect marginal cases. The rotation-only fit satisfies both numeric thresholds in ScanNet scene0166_02 and ScanNet++ 6a217fbcb0 and eb8ef9b4cc, while ScanNet scene0250_01 then exceeds 5°. This is a fit-method sensitivity, not evidence of a convention change, and it does not repair most captures. The center-only stage ruling remains unchanged.', '',
              'Every row below has 32/32 exact ordered index matches through all recorded bindings and matching RGB hashes. “Unverified” means that the native source-frame numbering cannot be independently checked against a GT calibration/selection sidecar. The complete index lists, RGB hashes, dense-anchor slots, individual check booleans, and NPZ field names are preserved per capture in the JSON.', '',
              '| Capture | Ordered anchors | Camera records / absent | Last source index | GT valid | Native numbering |',
              '|---|---:|---:|---:|---:|---|']
    for r in z['captures']:
        b=r['frame_binding']
        lines.append('| %s | 32/32 | %s / %s | %s | %s/32 | Unverified |' % (r['capture'],b['records_with_geometry'],b['records_without_geometry'],b['source_indices'][-1],b['valid_frames']))
    lines += ['', 'The recorded convention table keeps `c2w_cv` for arkitscenes, scannet, and scannetppv2, without certifying the unavailable builder lineage. `gt/v2.py`, GT outputs, stage outputs, and deliveries remain unchanged. No STAGES_T2_v2 files are produced because the condition for changing conventions is not met. Failed alignments still censor S4/S5; these checks do not establish tower error.', '',
              'To resolve the remaining association uncertainty, the needed local evidence is the exact NPZ producer/configuration and its ordered source-index→native RGB filename/timestamp→pose-row mapping, with RGB hashes or the calibration/selection receipts. No assets were fetched. No source-index offsets, permutations, portrait rotations, per-capture axis choices, or fitted scales were applied to GT scoring.', '',
              'The 22 captures without a staged GT file remain outside the pose audit: '+', '.join(z['missing_gt'])+'.', '',
              'Validation: six CPU unit tests cover known rigid recovery, inversion/axis composition, scale isolation, world-up invariance, center preservation under camera flips, and the relative-rotation exclusion test. Real-data assertions reproduce all 38 stage alignment metrics and acceptance decisions, verify every available binding, check one-time metric scaling, and verify world-up invariance. The capture stream contains 310 complete records and matches SHA256 `'+z['capture_read']['raw_sha256']+'`. Only 70,794 compressed bytes of pose/index/valid NPZ members were read; NPZ depth/mask arrays, RGB images, and model weights were not loaded. Analysis peak RSS was %.1f MiB with one CPU thread.' % (z['resources']['max_rss_kib']/1024), '',
              'Artifacts: [JSON evidence](CAMERA_CONVENTIONS_T2.json), [CSV fits](CAMERA_CONVENTIONS_T2.csv), [camera input cache](CAMERAS_T2_R5.json). Reproduce from gbuild with `/scratch/jjyeung/envs/p1cpu/bin/python -B analyze_round5.py extract`, then `analyze_round5.py analyze`, then `render_round5.py`; outputs use exclusive creation, so retain existing artifacts and use a fresh output location for another run. Tests: `/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest test_round5 -v`.', '']
    # Links are absolute because score_t2 and gbuild are sibling subtrees under cap's parent.
    text='\n'.join(lines).replace('../../../gbuild/',str(ROOT)+'/')
    with (OUT/'CAMERA_CONVENTIONS_T2.md').open('x') as f:f.write(text)
    with (OUT/'CAMERA_CONVENTIONS_T2.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)


if __name__ == '__main__':
    main()
