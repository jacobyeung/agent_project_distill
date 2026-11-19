"""Freeze the bars before any priced number: out/v2/BARS_FROZEN.json with the spec's sha256, the UTC time, the spec's
bars section verbatim, the machine-readable bars mc_summary applies, and the builder's resolutions of what the spec
leaves open. Refuses to rewrite an existing freeze whose bars differ.
Usage: python mc_bars.py   (p1cpu interpreter)
"""
import json, time
import mc_common as C

BARS = dict(
    decision_arm=dict(seed_set='S_A0', frame_set='D64', rule='A32 replaces D64 per fold only if A32 completes on all 209 '
                      'captures: fold k takes the frame set whose C_fused MRA is higher on the other four folds (ties D64)'),
    missing='a bar whose arm did not complete on all 209 captures is MISSING; MISSING counts as not passed',
    carry_precision=dict(test='summarize_train.precision over the arm C_fused rows (diag from train_pricing.Objects.get on '
                         'the injected carried track)', min=0.90, reference=dict(t025='390/538=0.724907', t015='426/581', t040='366/501')),
    carry_fusion=dict(test='summarize_train.contrast(C_fused, A0_deployed) on 1,037 rows', min_estimate=2.0, lower_bound_above=0.0),
    size_screen=dict(test='summarize_train.contrast(sizes(C_fused), sizes(A0_deployed))', min_estimate=5.0, lower_bound_above=0.0,
                     source='KIT_SPEC_box_ladder_k1_v2.md lines 88-89'),
    first_seen_screen=dict(test='summarize_train.appearance(C_fused) pair rate', min_rate=0.90, deployed=0.7656,
                           source='KIT_SPEC_box_ladder_k1_v2.md lines 88-89'),
    carry_ceiling=dict(role='diagnostic, no bar', test='S_GT C_fused MRA against fused_cf 78.62; frame recall on S_GT'),
    s_phr='own row of bars, same tests; never replaces S_A0; runs only when PHRASE_FOLDS.json exists',
    decision='carry_precision and carry_fusion pass: the carried fused track joins the stack. carry_precision fails: the '
             'object arms (size, appearance order, counting) stay closed. A size or appearance pass only opens that '
             "category's registered R0-dev comparison; it decides no route.",
    reported_without_bar=['iou member precision (predicted.member_precision, IoU > 0.5) for all seeds and seeds on target',
                          'mask IoU per visible operand-frame and at the priced frame (sb_maskfail stats)',
                          'frame recall (share > 1%, IoU >= 0.5) and false presence', 'C_best1 contrasts'],
)
RESOLUTIONS = [
    'carry_precision, size_screen and first_seen_screen read the decision arm C_fused rows; C_best1 and C_fused share one '
    'carried track per object, so member precision is identical on both.',
    'carried anchor: tracker object score > 0 and a non-empty mask; a positive-score empty mask is counted '
    '(positive_empty) and is not a member, since an empty mask cannot be lifted.',
    'an added member is a carried anchor other than the seed slot; masks enter majority() at 240 x 320 ([::2, ::2]).',
    'S_PHR pair (w1, w2): w2 is called only when w1 leaves the object not seen (A0 refused or no lifted frame).',
    'a seed set with no seed for an object (refused S_A0) gives the empty object and its rows refuse, as A0 does.',
    'the five withheld-80 K1-train captures (25 rows) stay in every bar; a sensitivity row on the other 1,012 rows is '
    'reported beside the bars and decides nothing.',
]


def main():
    spec = C.read(C.SPEC).decode()
    if C.PINS[str(C.SPEC)] != C.SPEC_SHA256:
        raise SystemExit(f'spec sha256 {C.PINS[str(C.SPEC)]} differs from the pinned {C.SPEC_SHA256}')
    a, b = spec.index('## Bars, written before any score'), spec.index('## CPU dry run')
    body = dict(spec=str(C.SPEC), spec_sha256=C.SPEC_SHA256, bars_section=spec[a:b].strip(), bars=BARS,
                builder_resolutions=RESOLUTIONS)
    path = C.OUT/'BARS_FROZEN.json'
    if path.exists():
        old = json.loads(path.read_text())
        if {k: old.get(k) for k in body} != json.loads(json.dumps(body)):
            raise SystemExit('BARS_FROZEN.json exists with different bars; it is never rewritten')
        print('BARS_FROZEN.json already frozen at', old['frozen_utc'])
        return
    C.code_pins()
    sha = C.write_json(path, dict(body, frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                  note='written before any priced number of this kit, dry-run stubs included'))
    print('BARS_FROZEN.json', sha)
    C.status(f'Stage 0 (BARS_FROZEN.json, sha256 {sha[:12]}): bars frozen from the v2 spec before any priced number.')


if __name__ == '__main__':
    main()
