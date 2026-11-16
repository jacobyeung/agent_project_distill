from pathlib import Path
p=Path(__file__).resolve().parents[1]/'proof/run.py';s=p.read_text()
s=s.replace("ROOT/'cohort/meta_5130.jsonl'","ROOT/'cohort/COHORT_REVSI5.jsonl'").replace('COHORT_OFFICIAL6.jsonl','COHORT_REVSI5.jsonl')
s=s.replace("r['dataset']+'/'+r['scene_name']+'.mp4'","r['scene']+'.mp4'")
s=s.replace("small_manifest.append(dict(by_rel[rel],sha256=F.sha(source)))","small_manifest.append(dict(by_rel[rel],sha256=F.sha(source),bytes=source.stat().st_size))")
s=s.replace("mode='proof')","mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef')")
# Actual pinned rows remain intact; only the fixture video manifest hashes differ.
s=s.replace("    # Preparation checks", "    # Preparation checks")
s=s.replace("    original_loader=data.official_rows\n    def subset(spec,roots):return [r for r in original_loader(spec,roots) if r['example_id'] in chosen_ids]\n",'')
s=s.replace("    payload[pfx+'TRANSPORT.json']", "    fixture_videos=json.loads((ROOT/'inputs/revsi999_videos_t32.json').read_text())\n    for r in small_manifest:fixture_videos['files'][r['relative_path'][:-4]].update(sha256=r['sha256'],bytes=r['bytes'])\n    video_bytes=(json.dumps(fixture_videos)+'\\n').encode()\n    video_pin=S.hashlib.sha256(video_bytes).hexdigest()\n    payload[pfx+'inputs/revsi999_videos_t32.json']=video_bytes\n    payload[pfx+'TRANSPORT.json']")
s=s.replace("(S,'video_source',lambda row:fixture_media[row['relative_path']]),(S,'question_source',lambda:ROOT/'cohort/COHORT_REVSI5.jsonl'),", "(data,'REVSI999_VIDEOS',{32:video_pin}),(S,'video_source',lambda row,media_root:fixture_media[row['relative_path']]),")
s=s.replace("any(g['items']!=(4 if k=='object_rel_direction' else 2) for k,g in report['groups'].items())","any(g['items']!=2 for k,g in report['groups'].items())")
s=s.replace('items=14','items=10').replace('production_membership=4008','production_membership=679').replace('14 official items','10 ReVSI items')
# Bound adapter must read the staged package, including its ten-item proof selection.
s=s.replace("(A,'EXPORT_SHA',F.sha(ap))", "(A,'HERE',package/'reader'),(A,'EXPORT_SHA',F.sha(ap))")
p.write_text(s)
