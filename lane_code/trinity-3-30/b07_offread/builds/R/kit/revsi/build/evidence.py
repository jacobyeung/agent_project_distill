"""Collect only observed local coverage, keyed by current source SHA256."""
from pathlib import Path
import gzip,hashlib,json,sys
import coverage
K=Path(__file__).resolve().parents[1];sys.path.insert(0,str(K/'proof'))
import lines_report
seen={};sources={};measured=set()
for name in ('coverage.tests3','coverage.proof3'):
    data=coverage.CoverageData(basename=str(K/'build'/name));data.read()
    for filename in data.measured_files():
        p=Path(filename)
        if not p.is_file() or not p.is_relative_to(K):continue
        h=hashlib.sha256(p.read_bytes()).hexdigest();seen.setdefault(h,set()).update(data.lines(filename) or []);measured.add(h)
result=json.loads((K/'proof/local03/RESULT.json').read_text());root=Path(result['job_root'])
for path in (root/'t').glob('*.json.gz'):
    trace=json.loads(gzip.decompress(path.read_bytes()))
    for row in trace['files']:seen.setdefault(row['sha256'],set()).update(row['lines'])
files=[];summaries=[]
cov=coverage.Coverage()
for p in lines_report.inventory():
    h=hashlib.sha256(p.read_bytes()).hexdigest();name=str(p.relative_to(K));observed=seen.get(h,set())
    files.append(dict(file=name,sha256=h,lines=sorted(observed)))
    if h in measured:
        _,statements,excluded,_,_=cov.analysis2(str(p))
        relevant=set(statements);summaries.append(dict(file=name,statements=len(relevant),covered=len(relevant&observed),missing=sorted(relevant-observed)))
trace=dict(schema=1,files=files,source='local coverage.py tests and proof, plus hash-matched stdlib child trace; no Orchard trace')
raw=json.dumps(trace,sort_keys=True).encode();(K/'proof/LOCAL_LINES.json.gz').write_bytes(gzip.compress(raw,mtime=0));(K/'proof/LINES_LOCAL.json').write_text(json.dumps(trace,indent=2)+'\n')
summary=dict(modules=len(summaries),statements=sum(r['statements'] for r in summaries),covered=sum(r['covered'] for r in summaries),files=summaries)
summary['percent']=100*summary['covered']/summary['statements']
(K/'proof/COVERAGE.json').write_text(json.dumps(summary,indent=2)+'\n');(K/'proof/COVERAGE_SUMMARY.json').write_text(json.dumps({k:v for k,v in summary.items() if k!='files'},indent=2)+'\n')
audit=lines_report.report(trace);(K/'proof/LINES_CHECK.json').write_text(json.dumps(audit,indent=2)+'\n')
staging=json.loads((root/'STAGING.json').read_text());plan=json.loads((Path(json.loads((root/'bootstrap/CONFIG.json').read_text())['spec']['run'])/'FRAME_PLAN.json').read_text())
assert staging['videos']['videos']==261 and len(plan['videos'])==261 and all(v['total_frames']==32 and len(v['model_timestamps'])==64 for v in plan['videos'].values())
result.update(staged_videos=261,planned_videos=261,all_tier32=True)
(K/'proof/LOCAL_PROOF.json').write_text(json.dumps(result,indent=2)+'\n')
(K/'proof/SCORER_CHECK.json').write_text(json.dumps(dict(native_metric='unchanged metric.py via scoring.score_item and metric_for with a NumPy torch stand-in',perfect_and_nonuniform_scores='checked in test_kit.py',paired_bootstrap='synthetic identity, unit difference, scene-correlated opposite scores',parent_real_answers_available=False,parent_reported_overall_reproduced=False),indent=2)+'\n')
print(json.dumps(dict(coverage={k:v for k,v in summary.items() if k!='files'},missing=audit['missing'],gaps=audit['gaps'],proof_archive_bytes=result['archive_bytes'])))
