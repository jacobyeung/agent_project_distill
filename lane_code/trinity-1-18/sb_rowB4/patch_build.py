from pathlib import Path
p=Path('build_rows.py');s=p.read_text()
s=s.replace("RULE='Latest recorded", "RULE='Latest recorded",1)
a=s.index('RULE=');b=s.index('\nFAMILIES=',a)
s=s[:a]+'''RULE='For an out-of-view object, cite the latest raster frame before k with share >= visibility_floor (0.002); if none, cite its first visible frame after k.'
SIGHTINGS={}
REVIEW=Path('/scratch/jjyeung/orch_n30/sb_brev3')
B3=Path('/scratch/jjyeung/orch_n30/sb_rowB3')'''+s[b:]
a=s.index('def sighting(');b=s.index('\ndef geometry(',a)
s=s[:a]+'''def prepare_sightings(eligible,facts):
    import numpy as np
    groups=C.defaultdict(list)
    for rr in eligible.values():
        for r in rr:groups[facts[r['qid']]['source_gt']['path']].append(r)
    for i,(path,rr) in enumerate(sorted(groups.items()),1):
        assert sha(path)==facts[rr[0]['qid']]['source_gt']['sha256']
        wanted={o['id'] for r in rr for o in r['provenance']['instances']}
        with np.load(path,allow_pickle=False) as z:raster=z['inst']
        assert len(raster)==32
        counts={obj:[] for obj in wanted}
        for frame in raster:
            ids,nums=np.unique(frame,return_counts=True)
            shares=dict(zip(map(int,ids),nums/frame.size))
            for obj in wanted:counts[obj].append(float(shares.get(obj,0)))
        for r in rr:
            p=r['provenance'];k=p['camera_frame']
            for obj in p['instances']:
                shares=counts[obj['id']]
                assert math.isclose(shares[k-1],p['frame_n_share'][obj['label']],abs_tol=1e-12)
                if shares[k-1]>=p['visibility_floor']:continue
                visible=[j+1 for j,share in enumerate(shares) if share>=p['visibility_floor']]
                assert visible,('MISSING raster sighting',r['qid'],obj['label'])
                before=[j for j in visible if j<k]
                f=max(before) if before else min(visible)
                assert before or f>k
                SIGHTINGS[r['qid'],obj['label']]=(f,'last_before' if before else 'first_after')
        if i%100==0:print('raster sighting groups',i,'/',len(groups),flush=True)

def sighting(r,label):
    return SIGHTINGS[r['qid'],label]
'''+s[b:]
s=s.replace('Sighting references use the latest recorded instance sighting before this frame, or the nearest recorded sighting if none is earlier.','Sighting references use raster visibility at a share of at least 0.002.')
s=s.replace("visibility=f'{name} is out of view in frame {k}; it was last seen in frame {f} ({rule})'", "citation=f'it was last seen in frame {f}' if rule=='last_before' else f'it first appears in frame {f}, after frame {k}'\n            visibility=f'{name} is out of view in frame {k}; {citation}'")
s=s.replace("'prompts/sb_rowB4.md']", "'prompts/sb_rowB4.md','out/CODE_ORIGIN.json']")
s=s.replace("pins={str(p):sha(p) for p in inputs}", "inputs += [REVIEW/'REMOVE_PROPOSED.json',B3/'out/REMOVE.json']\n    pins={str(p):sha(p) for p in inputs}")
s=s.replace("wf=B.WordingFilter();eligible=", "nrows=load(B.N);outside={r['row_key'] for r in nrows if r['reason']=='outside_native_training_division'}\n    proposed=load(REVIEW/'REMOVE_PROPOSED.json');dropped={r['row_key'] for r in proposed}&outside\n    assert len(dropped)==117 and len({r['scene'] for r in proposed if r['row_key'] in dropped})==10\n    wf=B.WordingFilter();eligible=")
s=s.replace("if why:reasons[qid]=why", "if qid in dropped:why.append('outside_native_training_division')\n        if why:reasons[qid]=why")
s=s.replace("assert set(b2ids)=={", "assert set(b2ids)-dropped=={")
s=s.replace("schedule,plan,uses=balanced_schedule(eligible,facts)", "schedule,plan,uses=balanced_schedule(eligible,facts)\n    prepare_sightings(eligible,facts)")
a=s.index("    with (OUT/'REMOVE.json').open('w') as f:");b=s.index("    dump('REFUSALS.json'",a)
s=s[:a]+'''    remove=[r for r in proposed if r['row_key'] not in dropped]
    assert {r['row_key'] for r in remove}==set(uses) and len(remove)==6710
    old_remove=load(B3/'out/REMOVE.json')
    wording=[r for r in old_remove if r['reason']=='heldout_wording_distance_le_0.05']
    missing_remove=[r for r in old_remove if r['row_key'] in missing]
    assert len(wording)==679 and len(missing_remove)==4420
    output_removals={'REMOVE.json':remove,'REMOVE_WORDING.json':wording,'REMOVE_MISSING_GT.json':missing_remove}
    for name,items in output_removals.items():
        with (OUT/name).open('w') as f:
            for item in items:
                assert set(item)==schema
                f.write(json.dumps(item,sort_keys=True,separators=(',',':'))+'\\n')
    dump('REMOVE.provenance.json',dict(input_sha256={**common,str(B.N):pins[str(B.N)],str(REVIEW/'REMOVE_PROPOSED.json'):pins[str(REVIEW/'REMOVE_PROPOSED.json')],str(B3/'out/REMOVE.json'):pins[str(B3/'out/REMOVE.json')]},
        output_sha256={n:sha(OUT/n) for n in output_removals},counts={n:len(rr) for n,rr in output_removals.items()},dropped_native_sources=len(dropped),dropped_native_scenes=10,schema=sorted(schema),format='Compact JSON Lines; exact N n.json schema; hashes in this sidecar'))
'''+s[b:]
p.write_text(s)
p=Path('base_rows.py');s=p.read_text().replace("    row_check(r,'vqa')", "    row_check(r,'vqa')\n    from student_pilot.r2_contract import validate\n    validate(r,'vqa')");p.write_text(s)
