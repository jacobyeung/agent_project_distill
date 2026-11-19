from pathlib import Path
p=Path('verify_rows.py');s=p.read_text()
a=s.index("                frames_available=");b=s.index("                viscounts['out_of_view_objects']",a)
s=s[:a]+'''                chosen=ev['recorded_frame']
                if ev['rule']=='last_before':
                    assert chosen<k and f'it was last seen in frame {chosen};' in line
                else:
                    assert ev['rule']=='first_after' and chosen>k
                    assert f'it first appears in frame {chosen}, after frame {k};' in line
'''+s[b:]
s=s.replace("assert max(source_uses.values())<=3 and unique_source==set(b2)","assert max(source_uses.values())<=3\n    proposed=load(Path('/scratch/jjyeung/orch_n30/sb_brev3/REMOVE_PROPOSED.json'))\n    nrows=load(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/n.json'))\n    outside={r['row_key'] for r in nrows if r['reason']=='outside_native_training_division'}\n    expected={r['row_key'] for r in proposed}-outside\n    assert unique_source==expected==set(b2)-outside and len(set(b2)&outside)==117")
s=s.replace("assert len(removal)==len(sources) and {r['row_key'] for r in removal}==set(sources)","assert len(removal)==len(unique_source) and {r['row_key'] for r in removal}==unique_source")
s=s.replace("        assert len(poses)==len(raster)==32", "        assert len(poses)==len(raster)==32\n        raster_visibility={}")
needle="            sem,values=computed[old];trace=row['target']"
s=s.replace(needle,'''            for obj in p['instances']:
                oid=obj['id'];label=obj['label']
                if oid not in raster_visibility:
                    raster_visibility[oid]=[j+1 for j in range(32) if np.count_nonzero(raster[j]==oid)/raster[j].size>=p['visibility_floor']]
                visible_frames=raster_visibility[oid]
                ev=row['provenance']['sb_rowB4']['visibility'][label]
                assert ev['in_view']==(k in visible_frames)
                if ev['in_view']:continue
                before=[f for f in visible_frames if f<k]
                want=max(before) if before else min(visible_frames)
                line=next(l for l in row['target'].splitlines() if 'the object labelled "'+label+'" is ' in l)
                if before:
                    match=re.search(r'it was last seen in frame (\\d+);',line)
                    assert match and int(match[1])==want
                    frames['last_before']+=1
                else:
                    match=re.search(r'it first appears in frame (\\d+), after frame (\\d+);',line)
                    assert match and int(match[1])==want and int(match[2])==k and want>k
                    frames['first_after']+=1
                assert ev['recorded_frame']==want
            sem,values=computed[old];trace=row['target']''')
s=s.replace("all_b2_sources_retained=True", "all_eligible_b2_sources_retained=True,false_citations=0")
s=s.replace("ROOT/'inputs/GT_FACTS.jsonl']", "ROOT/'inputs/GT_FACTS.jsonl',Path('/scratch/jjyeung/orch_n30/sb_brev3/REMOVE_PROPOSED.json'),Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/n.json')]")
p.write_text(s)
p=Path('select_samples.py');s=p.read_text().replace("    chosen=[];selection={}","    prior=json.loads(Path('/scratch/jjyeung/orch_n30/sb_rowB3/out/READ30_REVIEW.json').read_text())\n    old_rows={r['qid']:r for r in [json.loads(s) for s in Path('/scratch/jjyeung/orch_n30/sb_rowB3/out/rows.jsonl').read_text().splitlines()]}\n    excluded={old_rows[q]['provenance']['sb_rowB3']['source_qid'] for q in prior['reviewed_qids']}\n    rows=[r for r in rows if r['provenance']['sb_rowB4']['source_qid'] not in excluded]\n    rows.sort(key=lambda r:hashlib.sha256(('sb_rowB4|READ30|'+r['qid']).encode()).hexdigest())\n    chosen=[];selection={}")
s=s.replace("Path(__file__),OUT/'rows.jsonl'", "Path(__file__),OUT/'rows.jsonl',Path('/scratch/jjyeung/orch_n30/sb_rowB3/out/READ30_REVIEW.json'),Path('/scratch/jjyeung/orch_n30/sb_rowB3/out/rows.jsonl')")
p.write_text(s)
