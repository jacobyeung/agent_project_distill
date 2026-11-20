"""Amendment 1 to BARS_FOV_544.json: provenance that binds each variant depth to its FoV, anchors and sampling grid.
Frozen before any variant grid exists (review fbp_fovrev MUST B1). D1-D3, H, margin and choice are unchanged."""
import hashlib, json, os, datetime
O = '/scratch/jjyeung/orch_n30/fb_pack/fov'
P = O + '/BARS_FOV_544_AMEND1.json'
assert not os.path.exists(P), 'amendment already frozen'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


base = O + '/BARS_FOV_544.json'
assert sha(base) == 'c1905484873704ae9b8af5cb653cf2cb1b911d789d181811767fa5f8707fa878'
fv = '/scratch/jjyeung/orch_n30/sb_own400/kit/fov_variants.py'
assert not os.path.exists(O + '/../../sb_own400/in/own_544_fov'), 'variant grids already present'
amend = {
    'schema': 'fb-pack-donor-fov-bars-amend-v1',
    'frozen_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'amends': {'path': base, 'sha256': sha(base)},
    'unchanged': 'margin, D1, D2, D3, H, choice order V2 > V1 > NONE, captures, folds, metric, bootstrap',
    'reason': 'Review fbp_fovrev MUST B1: the base integrity refusals did not bind depth_V1/depth_V2 to their FoVs, anchor order and sampling grid, and did not pin the variant-producing code.',
    'code_pins': {
        fv: sha(fv),
        'PATCH_DONOR3 student_pilot/scale_donor.py (trinity-2-28 /scratch/jjyeung/orch_n30/fb_pack/donor3/work/new/student_pilot/scale_donor.py)': '1fca29c9211e19f91a04e72c41a77652a56f3dea363e58fdd71817fe7229a134',
    },
    'added_integrity_refusals': [
        'P1 same-function control: fov.npz depth is computed by the same explicit-FoV encode/query function that computes depth_V1 and depth_V2, called with fov_B (the pose-head FoV of the served pass), not copied from the served output; it must equal own.npz depth and own_170235 own.npz depth bit for bit on every capture, else refuse the run. FOV_RECEIPT.json states control_path: explicit_fov_function and records the max abs difference (0).',
        'P2 fov_B equals the pose-head FoV the served pass used, recorded in FOV_RECEIPT.json; V1 and V2 differ from the control only in the FoV argument.',
        'P3 FOV_RECEIPT.json records frame_indices equal to the capture anchor_indices of BARS_FROZEN.json and grid_uv equal to linspace(0,1000,51) float32; the scorer checks both.',
        'P4 FOV_RECEIPT.json records sources{path: sha256} of every file of the variant computation. The explicit-FoV function file must equal kit/fov_variants.py at the pin above, or the k1fwd2 RESULT must publish its diff against that pin before scoring; a V1 FoV formula other than 1e-4+(pi-2e-4)*sigmoid(depth.fov(private frame states)) as in scale_donor.py at the pin above refuses.',
        'P5 Anchor and grid sanity (data check, no tuning): for every capture the identity orientation of depth_V1 and depth_V2 against arm A (mean per-anchor correlation of centred log depth) beats the transpose and both flips; and over all captures at least 95% of anchors correlate best with the same anchor of arm A (step 400 vs 544 scored 100%; neighbouring video anchors reach 0.99); else refuse.',
    ],
}
b = (json.dumps(amend, indent=1, sort_keys=True) + '\n').encode()
with open(P, 'xb') as f:
    f.write(b)
os.chmod(P, 0o444)
print(P, len(b), hashlib.sha256(b).hexdigest())
