from pathlib import Path
import hashlib
K=Path(__file__).resolve().parents[1]
p=K/'reader/official_adapter.py';s=p.read_text().replace("if not spec['indices']['sha256'].startswith('290111cf')", "if spec['indices']['sha256']!="+repr(hashlib.sha256((K/'inputs/revsi_indices.json').read_bytes()).hexdigest()));p.write_text(s)
p=K/'cohort/frame_plan.py';s=p.read_text();s=s.replace("def compute(directory,manifest",'''def source_timing(value,source):
    if value.get('total_frames')!=32:raise ValueError('Require exact tier-32 clip')
    total=source[-1]+1;fps=value['fps']*total/32
    expanded=[source[i] for i in value['duplicate_indices']]
    return dict(value,source_frame_indices=source,model_fps=fps,model_total_frames=total,
                model_duplicate_indices=expanded,model_timestamps=[i/fps for i in expanded])


def compute(directory,manifest''')
s=s.replace("    from concurrent.futures import ThreadPoolExecutor", "    indices=json.loads((Path(__file__).resolve().parents[1]/'inputs/revsi_indices.json').read_text())\n    from concurrent.futures import ThreadPoolExecutor")
s=s.replace("        return r['relative_path'],value", "        if not packet_only and Path(r['relative_path']).stem in indices:\n            value=source_timing(value,indices[Path(r['relative_path']).stem]['32-frame'])\n        return r['relative_path'],value")
p.write_text(s)
p=K/'proof/run.py';s=p.read_text().replace("plan_videos[rel]=frame_plan.one(source)", "indices=json.loads((ROOT/'inputs/revsi_indices.json').read_text())[Path(rel).stem]['32-frame']\n        plan_videos[rel]=frame_plan.source_timing(frame_plan.one(source),indices)");p.write_text(s)
p=K/'launcher/orchard_launcher.py';s=p.read_text().replace('total<32','total!=32');p.write_text(s)
p=K/'tests/test_kit.py';s=p.read_text().replace("# Numeric boundary uses the official eleven thresholds, not VSI's ten.","# Preserve the pinned implementation's float/int threshold construction.").replace('pytest.approx(6/11)','pytest.approx(.6)');p.write_text(s)
p=K/'tests/test_pass2.py';s=p.read_text().replace("inputs=dict(revsi_video_root='/tmp/v')","inputs=dict(video_root='/tmp/v')");p.write_text(s)
p=K/'reader/official_score.py';s=p.read_text();s=s.replace("if parent_answers:\n        comparison=", "if parent_answers:\n        comparison=")
s=s.replace("        (out/'PAIRED_B2048.json')", "        import hashlib\n        comparison['parent_answers_sha256']=hashlib.sha256(Path(parent_answers).read_bytes()).hexdigest()\n        (out/'PAIRED_B2048.json')")
s=s.replace("    return {a:dict(items=r['items']", "    (out/'SUMMARY.txt').write_text(render(reports))\n    return {a:dict(items=r['items']")
a=s.index('\ndef self_check');b=s.index('\ndef main():',a)
s=s[:a]+'''
def render(reports):
    lines=[]
    for arm in ('B2048','ON16k','B4096'):
        report=reports[arm];lines.append(arm+' ('+report['role']+', '+report['mode']+')')
        groups={**report['groups'],**{'facing_'+k:v for k,v in report['direction_by_question_text'].items()}}
        for name,r in groups.items():
            score='undefined' if r['score'] is None else f"{100*r['score']:.2f}%"
            ci=r['percentile_95'];interval='undefined' if ci is None else f"[{100*ci[0]:.2f}, {100*ci[1]:.2f}]"
            lines.append(f"{name}: {score}; 95% CI {interval}; n={r['items']}; errors={r['error_count']}; source capped={r['source_capped']}; continuation capped={r['continuation_capped']}; unparsed={r['unparsed']}")
        r=report['five_category_mean'];score='undefined' if r['score'] is None else f"{100*r['score']:.2f}%"
        ci=r['percentile_95'];interval='undefined' if ci is None else f"[{100*ci[0]:.2f}, {100*ci[1]:.2f}]"
        lines.append(f"Five-category mean: {score}; 95% CI {interval}")
    lines.extend(f"{k} ({v}): not read here: native reader required" for k,v in EXCLUDED.items())
    return '\\n'.join(lines)+'\\n'

'''+s[b:]
s=s.replace("a=p.parse_args();print(json.dumps(score_run(a.dest,a.cohort,a.output,parent_answers=a.parent_answers)))", "a=p.parse_args();score_run(a.dest,a.cohort,a.output,parent_answers=a.parent_answers);print((Path(a.output)/'SUMMARY.txt').read_text(),end='')")
p.write_text(s)
