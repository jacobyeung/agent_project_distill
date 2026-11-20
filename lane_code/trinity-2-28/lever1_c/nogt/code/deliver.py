"""Write the bounded report and checksums from completed machine-readable audits."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from round2 import *

def main():
    repro=read(OUT/'REPRODUCTION.json');builds=read(OUT/'BUILDS.json');checks=read(OUT/'CAPTURE_CHECKS.json')['captures']
    assert len(builds)==22
    assert set(checks)=={c for c,b in builds.items() if b['built']}
    passed=sum(c['passed'] for c in checks.values());built=sum(b['built'] for b in builds.values())
    verdict='PASS' if passed>=15 else 'FAIL'
    lines=['# NOGT capture acceptance', '',f'Verdict: **{verdict}: {passed}/22 pass; bar = 15/22.** {built} new NPZs built; {22-built} captures not built.']
    lines.extend(['Tolerances were registered at 2026-11-20T19:54:15Z before comparisons; their SHA256 is recorded in each reproduction result.',
                  'Integer/string/bool arrays, calibration, and boxes require exact equality. Float32 poses/raycast depth allow 8 eps × max(1, |reference|); depth support must match. ARKit depth requires exact equality.',
                  'Both staging logs contain PIPE_RC 0 0 0 0; that receipt does not establish correct anchor selection.', '',
                  '| Reference | Result | Array comparison |','|---|---|---|'])
    for d,cid in REFS.items():
        r=repro[d]
        if r['passed']:
            exact=sum(a.get('exact_equal',False) for a in r['arrays'].values())
            lines.append(f'| {d}/{cid} | PASS | {exact}/{len(r["arrays"])} arrays exactly equal; NPZ byte-identical |')
        else:
            failed=[k for k,a in r.get('arrays',{}).items() if not a['passed']]
            lines.append(f'| {d}/{cid} | FAIL; required rebuild incomplete | Staged lexical diagnostic differs: {", ".join(failed)} |')
    if not repro['arkitscenes']['passed']:
        r=repro['arkitscenes']
        lines.extend(['', 'ARKit 41069053 lacks all 32 timestamp-sorted anchor depth PNGs and 32 pincams; the staged list selected lexical order across the 999/1000-second boundary.',
                      'The lexical reconstruction is diagnostic only. Its other 9 arrays are exact; no ARKit target was built. Required paths: ARKIT_MISSING_REFERENCE_INPUTS.txt.'])
        for key in ('c2w','depth','inst'):
            a=r['arrays'][key]
            lines.append(f'{key}: {a["different_elements"]:,}/{a["elements"]:,} unequal; max abs {a["max_abs"]:.9g}; RMSE {a["rmse"]:.9g}; outside tolerance {a["outside_tolerance"]:,}'+(f'; depth-support mismatches {a["support_mismatch"]:,}.' if key=='depth' else '.'))
    lines.extend(['', 'Box conventions: SN = full membership-AABB lengths; SPP = half the raw full annotation lengths, doubled for geometry; AK = annotation full lengths.',
                  'For the SPP reference, mesh radius/raw-length ratios range 0.495304–0.500017 (median 0.5), confirming full raw lengths. Per-capture ratios and conventions are in prepared/<capture>/PREPARATION.json and BUILDS.json.',
                  'Self-consistency requires rigid poses, positive depth at every labeled pixel, >50% of visible instance/frames with box/mask-bbox IoU >0.25, and ≥95% lifted-point containment (CHECK_RULES.md).',
                  'Binding uses round-9 raw proposals on authenticated served frames, unique strip/lowercase label joins, visible-anchor medians, shifts ±1/±2 and flips/rotations. Both arms need positive same-frame evidence and no paired alternative gain >0.2.',
                  'The table reports bbox-IoU passing share / containment share, T1 and points same/best-alternative IoU, and SPP COLMAP median camera-center error.', '',
                  '| Capture | Convention | Self bbox/inside | T1 same/alt | Points same/alt | COLMAP m | Result |',
                  '|---|---|---|---|---|---|---|'])
    def f(v):return '—' if v is None else f'{v:.3f}'
    for d,ids in TARGETS.items():
        for cid in ids:
            c=d+'/'+cid;b=builds[c];r=checks.get(c)
            if r is None:
                lines.append(f'| {cid} | none | — | — | — | — | FAIL: reference |');continue
            g=r['geometry'];a=r['arms']['t1'];p=r['arms']['t2'];col=b['evidence'].get('colmap',{}).get('median_m')
            reasons=[s for s,k in [('identity','identity_passed'),('self','geometry'),('binding','binding_passed'),('COLMAP','colmap_passed')] if not (r[k]['passed'] if k=='geometry' else r[k])]
            result='PASS' if r['passed'] else 'FAIL: '+','.join(reasons)
            conv={'scannet':'SN','scannetppv2':'SPP','arkitscenes':'AK'}[d]
            lines.append(f'| {cid} | {conv} | {f(g["bbox_iou_gt025_share"])}/{f(g["containment_share"])} | {f(a["same_median"])}/{f(a["best_alternative_median"])} | {f(p["same_median"])}/{f(p["best_alternative_median"])} | {f(col)} | {result} |')
    lines.extend(['',f'All {built*32} built-capture served PNG hashes and source indices verified. Content agreement does not independently hash-bind native RGB to every pose.',
                  'Files: gt/{t1_gt,arkit_gt}/gt/*.npz; REPRODUCTION.json; CAPTURE_CHECKS.json (all instance/frame and binding scores); BUILDS.json; REPRO_TOLERANCE.md; CHECK_RULES.md; SHA256SUMS.',
                  'Tests: TESTS_ROUND2_COMPLETE.log (14 pass) and TESTS_PREFLIGHT_ROUND2.log (5 pass). Sources: ../code/{round2,build_captures,check_captures,deliver,test_round2}.py; logs: ../logs/.',
                  'CPU only, nice 10, at most four build workers; all input/output paths are local /scratch; no SSH, Git, network, GPU, kills, deletions, or /home or /data* access.'])
    assert len(lines)<=60,len(lines)
    (OUT/'NOGT_REPORT.md').write_text('\n'.join(lines)+'\n')
    write(OUT/'VERDICT.json',dict(passed=passed,total=22,required=15,built=built,verdict=verdict,captures={d+'/'+cid:dict(passed=checks.get(d+'/'+cid,{}).get('passed',False),built=builds[d+'/'+cid]['built']) for d,ids in TARGETS.items() for cid in ids}))
    # Replace obsolete missing-input advice with the current source requirements.
    write(OUT/'REPRO_INPUTS_REQUIRED.json',{d:dict(capture=r['capture'],passed=r['passed'],missing=r.get('missing_required_paths',[])) for d,r in repro.items()})
    pre=read(OUT/'PREFLIGHT.json');pre.update(reproduction=list(repro.values()),accepted=passed,verdict=verdict)
    for r in pre['captures']:
        c=r['dataset']+'/'+r['capture'];q=checks.get(c,{})
        r.update(status='PASS' if q.get('passed') else 'FAIL',accepted=q.get('passed',False),self_consistency=q.get('geometry'),binding=q.get('arms'),applied_box_convention=builds[c].get('evidence',{}).get('box_convention'))
    write(OUT/'PREFLIGHT.json',pre)
    paths=sorted(p for base in (ROOT/'code',OUT,ROOT/'logs') for p in base.rglob('*') if p.is_file() and p!=OUT/'SHA256SUMS')
    (OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in paths))
    print(verdict,passed,'/22;',built,'built;',len(lines),'report lines;',len(paths),'checksummed files')

if __name__=='__main__':main()
