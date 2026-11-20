"""Freeze the field-of-view source rule for the step-544 scale donor (fb_pack3, ORCH RULING 2315Z item 2)."""
import hashlib, json, os, datetime
O = '/scratch/jjyeung/orch_n30/fb_pack/fov'
os.makedirs(O, exist_ok=True)
P = O + '/BARS_FOV_544.json'
assert not os.path.exists(P), 'bars already frozen'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


K = '/scratch/jjyeung/orch_n30/sb_own400'
pins = {p: sha(p) for p in [K + '/out/BARS_FROZEN.json', K + '/out/BARS_FROZEN_B.json', K + '/kit/inputs/G3T_FOV.json',
                            K + '/kit/score_400.py', K + '/kit/core.py',
                            '/scratch/jjyeung/orch_n30/sb_scale1/code/scale_analysis.py',
                            '/scratch/jjyeung/orch_n30/sb_scale2/code/scale_drift.py']}
assert pins[K + '/out/BARS_FROZEN.json'].startswith('bc080aa9')
bars = {
    'schema': 'fb-pack-donor-fov-bars-v1',
    'frozen_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'authority': 'ORCH RULING 2026-11-19T23:15Z item 2 (events/fb_pack/20261119T2315Z_ORCH_RULING_donor_fov_measured_before_binding.md)',
    'question': 'Which frozen field-of-view source does the step-544 scale donor (PATCH_DONOR3 scale_donor.fov_source) bind: V1, V2, or none?',
    'input_sha256': pins,
    'arms': {
        'A': 'served step-544 depth, pose-head FoV: /scratch/jjyeung/k1/own_170235/native/probe/<key>/own.npz depth (arm A of BARS_FROZEN.json, pinned there per capture)',
        'V1': 'step-544 depth with checkpoint-private FoV 1e-4+(pi-2e-4)*sigmoid(depth.fov(private frame states)), as PATCH_DONOR3 scale_donor defines it: in/own_544_fov/native/probe/<key>/fov.npz depth_V1',
        'V2': 'step-544 depth with frozen G3T FoV raw_pose9[anchor_slots,7:9] (kit/inputs/G3T_FOV.json): in/own_544_fov/native/probe/<key>/fov.npz depth_V2',
    },
    'identical_to_donor_decision': 'Captures (the 242 K1 train captures of BARS_FROZEN.json; GT-missing ones listed and left out, as there), anchor pairs, rooms, the two folds, the metric, the ten thresholds, OwnDepthScale arithmetic (sb_scale1 scale_analysis.estimate on the tower grid and confidence), the paired room bootstrap (10,000 draws, seed 17, 95%) and the routed-distance harm guard (sb_scale2 scale_drift, GT masks) are exactly those of BARS_FROZEN.json bc080aa9. Contrasts are V-A on identical pairs and rooms.',
    'margin_mra_points': 0.25,
    'margin_reason': '0.25 is about half the 0.54-point displacement gap (step 400 minus step 544, combined) that chose the donor checkpoint; 0.50 is that whole gap.',
    'acceptable': {
        'D1': 'combined displacement V-A mean >= -0.25',
        'D2': 'combined displacement V-A 95% CI lower bound >= -0.50',
        'D3': 'displacement V-A mean >= -0.50 in each fold',
        'H': 'routed distance V-A: no harm, i.e. the 95% CI upper bound is not below 0 in either fold or combined',
        'rule': 'A source is acceptable iff D1, D2, D3 and H all hold.',
    },
    'choice': 'V2 if acceptable (no path through the language model or any trained head); else V1 if acceptable (frozen private depth.fov, a trained head module); else NONE: the donor does not bind at this boundary, and the report states what a frozen copy of the pose-head FoV path would need.',
    'integrity_refusals': [
        'Any of the 242 train keys missing under in/own_544_fov/native/probe, or any held-out capture present: refuse the run.',
        'own.npz depth or fov.npz depth differs by any bit from own_170235 own.npz depth for the same key: refuse the run.',
        'PHASE_COMPLETE.json or FOV_RECEIPT.json: synthetic true, capture_sha256 != digest(capture), checkpoint sha256 != 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef, or a file sha256 that does not match the bytes: refuse.',
        'fov_V2 differs from G3T_FOV.json for the capture by more than 1e-6 rad: refuse.',
        'depth_V1/depth_V2 not (32,51,51) finite and > 0, or any FoV not (32,2) finite in (0, pi): refuse.',
    ],
    'report_only': ['FoV agreement per dataset (median absolute degrees, B-V1, B-V2, V1-V2, both axes)', 'per-arm OwnDepthScale ratios to A', 'global fit-half factor per arm'],
    'not_used': 'No R0-dev, dev-S1 or held-out capture enters the choice.',
}
b = (json.dumps(bars, indent=1, sort_keys=True) + '\n').encode()
with open(P, 'xb') as f:
    f.write(b)
os.chmod(P, 0o444)
print(P, len(b), hashlib.sha256(b).hexdigest())
