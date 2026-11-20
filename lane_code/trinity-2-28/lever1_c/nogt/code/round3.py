"""Reproduce chronological ARKit anchors, then build and audit only ARKit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from round2 import *
from build_arkit_cr import ts
from check_captures import run_checks

BASE = OUT/'round3_baseline'

def preserved_npzs():
    rows=[]
    for line in (BASE/'SHA256SUMS').read_text().splitlines():
        digest, name=line.split('  ',1)
        if name.startswith('out/gt/t1_gt/gt/') and name.endswith('.npz'):
            actual=sha(ROOT/name)
            assert actual==digest, (name, digest, actual)
            rows.append(dict(path=name,sha256=actual,passed=True))
    assert len(rows)==15
    return rows

def verify_listing(cid, indices, listing, require_lexical=False):
    names=listing['depth_names']; chronological=sorted(names,key=ts)
    assert len(names)==len(set(names))
    assert len(indices)==32 and indices==listing['anchors']
    same=sorted(names)==chronological
    if require_lexical:
        assert same and names==chronological, cid
    anchors=[chronological[i] for i in indices]
    src=source('arkitscenes',cid)/f'{cid}_frames'
    for name in anchors:
        assert (src/'lowres_depth'/name).is_file(),name
        assert (src/'lowres_wide_intrinsics'/Path(name).with_suffix('.pincam')).is_file(),name
    return dict(lexical_equals_chronological=same,listing_is_chronological=names==chronological,
                full_depth_count=len(names),anchor_indices=indices,chronological_depth_anchors=anchors,
                anchor_timestamps=[ts(n) for n in anchors],staged_depths=32,staged_pincams=32)

def main():
    assert 'PIPE_RC 0 0 0 0' in (ROOT/'ark_ref_stage.log').read_text()
    assert 'PIPE_RC 0 0 0 0' in (ROOT/'stage.log').read_text()
    staged=(ROOT/'ark_ref_list.txt').read_text().splitlines()
    assert len(staged)==64 and len(set(staged))==64
    assert all((ROOT/'raw'/p).is_file() for p in staged)
    if not BASE.exists():
        BASE.mkdir()
        for name in ['SHA256SUMS','NOGT_REPORT.md','REPRODUCTION.json','CAPTURE_CHECKS.json','BUILDS.json']:
            (BASE/name).write_bytes((OUT/name).read_bytes())
    tolerance_sha=sha(OUT/'REPRO_TOLERANCE.md')
    existing=read(OUT/'REPRODUCTION.json')
    assert tolerance_sha==existing['scannet']['tolerance_sha256']==existing['scannetppv2']['tolerance_sha256']
    old_hashes=preserved_npzs()
    manifest={m['scene']:m for m in read(ROOT/'DEVS1_MANIFEST.json')['captures']}
    cid=REFS['arkitscenes']
    listing=read(ROOT/'ref_arkit_listing.json')[cid]
    with np.load(REFROOT/relpath('arkitscenes',cid)) as ref:
        indices=ref['frame_indices'].tolist()
    ordering={cid:verify_listing(cid,indices,listing)}
    expected={str((source('arkitscenes',cid)/f'{cid}_frames'/folder/Path(n).with_suffix(ext)).relative_to(ROOT/'raw'))
              for n in ordering[cid]['chronological_depth_anchors']
              for folder,ext in [('lowres_depth','.png'),('lowres_wide_intrinsics','.pincam')]}
    assert set(staged)==expected
    target_listing=read(ROOT/'arkit_listing.json')
    for target in TARGETS['arkitscenes']:
        ordering[target]=verify_listing(target,manifest['arkitscenes/'+target]['anchor_indices'],target_listing[target],True)
    write(OUT/'ARKIT_ORDER_CHECKS.json',ordering)
    print('ORDER VERIFIED: chronological reference; all seven target listings lexical == chronological',flush=True)
    path=OUT/'reproduction_round3'/relpath('arkitscenes',cid)
    start=time.monotonic()
    evidence=build_raw('arkitscenes',cid,indices,path)
    reference=REFROOT/relpath('arkitscenes',cid)
    comparison=compare_arrays(path,reference,'arkitscenes')
    comparison.update(dataset='arkitscenes',capture=cid,evidence=evidence,actual=str(path),reference=str(reference),
                      seconds=time.monotonic()-start,compared_utc=datetime.now(timezone.utc).isoformat(),
                      tolerance_sha256=tolerance_sha,byte_identical=sha(path)==sha(reference),
                      reference_sha256=sha(reference),anchor_order='chronological',missing_required_paths=[])
    existing['arkitscenes']=comparison
    write(OUT/'REPRODUCTION.json',existing)
    write(OUT/'REPRODUCTION_ARKIT_ROUND3.json',comparison)
    print('REFERENCE',comparison['passed'],'byte_identical',comparison['byte_identical'],
          [(k,a.get('max_abs')) for k,a in comparison['arrays'].items() if not a['passed']],flush=True)
    if not comparison['passed']:
        with (OUT/'NOGT_REPORT.md').open('a') as f:
            f.write('\n## Round 3: ARKit reproduction failed\nChronological inputs are present, but the frozen array comparison failed; no target was built. See REPRODUCTION_ARKIT_ROUND3.json for per-array differences.\n')
        return
    builds=read(OUT/'BUILDS.json')
    targets=[]
    for target in TARGETS['arkitscenes']:
        canonical='arkitscenes/'+target;targets.append(canonical)
        start=time.monotonic();p=OUT/'gt'/relpath('arkitscenes',target)
        evidence=build_raw('arkitscenes',target,manifest[canonical]['anchor_indices'],p)
        builds[canonical]=dict(built=True,path=str(p),evidence=evidence,seconds=time.monotonic()-start)
        write(OUT/'BUILDS.json',builds)
        print('BUILT',target,evidence['sha256'],flush=True)
    run_checks(set(targets))
    checks=read(OUT/'CAPTURE_CHECKS.json')['captures']
    old_checks=read(BASE/'CAPTURE_CHECKS.json')['captures']
    assert all(checks[c]==r for c,r in old_checks.items())
    assert preserved_npzs()==old_hashes
    assert sha(OUT/'REPRO_TOLERANCE.md')==tolerance_sha
    write(OUT/'ROUND3_PRESERVATION.json',dict(npzs=old_hashes,old_capture_checks_unchanged=True,
          tolerance_sha256=tolerance_sha,verified_utc=datetime.now(timezone.utc).isoformat()))
    passed=sum(r['passed'] for r in checks.values())
    write(OUT/'VERDICT.json',dict(passed=passed,total=22,required=15,built=22,verdict='PASS' if passed>=15 else 'FAIL',
          captures={c:dict(passed=r['passed'],built=True) for c,r in checks.items()}))
    write(OUT/'REPRO_INPUTS_REQUIRED.json',{d:dict(capture=r['capture'],passed=r['passed'],missing=r.get('missing_required_paths',[])) for d,r in existing.items()})
    pre=read(OUT/'PREFLIGHT.json');pre.update(reproduction=list(existing.values()),accepted=passed,verdict='PASS' if passed>=15 else 'FAIL')
    for r in pre['captures']:
        c=r['dataset']+'/'+r['capture'];q=checks[c]
        r.update(status='PASS' if q['passed'] else 'FAIL',accepted=q['passed'],self_consistency=q['geometry'],binding=q['arms'],applied_box_convention=builds[c]['evidence']['box_convention'])
    write(OUT/'PREFLIGHT.json',pre)
    details=[]
    for c in targets:
        r=checks[c];g=r['geometry'];a=r['arms']['t1'];b=r['arms']['t2']
        details.append(f"{c.split('/')[1]} {'PASS' if r['passed'] else 'FAIL'}: {g['bbox_iou_gt025_share']:.3f}/{g['containment_share']:.3f}, {a['same_median']:.3f}/{a['best_alternative_median']:.3f}, {b['same_median']:.3f}/{b['best_alternative_median']:.3f}")
    exact=sum(a['exact_equal'] for a in comparison['arrays'].values())
    lines=['','## Round 3: chronological ARKit anchors',
           f"ARKit 41069053 reproduction PASS: {exact}/12 arrays exact; NPZ byte-identical = {comparison['byte_identical']}; registered tolerance unchanged. All seven target listings have identical lexical and chronological depth order; all 64 reference anchor files match the restaging list.",
           f"Current verdict: {'PASS' if passed>=15 else 'FAIL'}, {passed}/22 accepted; 22/22 built. All 15 existing ScanNet/ScanNet++ NPZ hashes and capture checks are unchanged. ARKit uses annotation full extents, the original 0.03 m assignment margin, and the same chronological builder for reference and targets. A capture with either same-frame binding median equal to zero fails the registered positive-evidence rule.",
           'Per-capture result and self bbox/containment, T1 same/alternative, points same/alternative: '+'; '.join(details)+'.',
           'Artifacts: gt/arkit_gt/gt/*.npz; REPRODUCTION.json; CAPTURE_CHECKS.json; ARKIT_ORDER_CHECKS.json; ROUND3_PRESERVATION.json; TESTS_ROUND3.log. SHA256SUMS preserves its old lines and appends new/current hashes; for repeated paths, use the last entry. Historical receipts are preserved in round3_baseline/.']
    with (OUT/'NOGT_REPORT.md').open('a') as f:f.write('\n'.join(lines)+'\n')
    assert len((OUT/'NOGT_REPORT.md').read_text().splitlines())<=60
    print('VERDICT',passed,'/22; 22 built; prior 15 hashes preserved',flush=True)

if __name__=='__main__':main()
