"""Exercise the venue entry point with the pinned CPU boundaries."""
from pathlib import Path
import signal
import sys
import coverage
B=Path(__file__).resolve().parents[1]; R=B.parents[1]
sys.path.append(str(B/'code'))
from adapter import dump,load,pin
dest=B/(sys.argv[1] if len(sys.argv)>1 else 'work/rh_cli');dest.mkdir()
cov=coverage.Coverage(data_file=str(dest/'coverage'),source=[str(B/'code')]);cov.start()
import entry
entry.main(['adapt','--items',str(R/'in/vsti/vstibench_repr_450_v3.json'),'--media',str(R/'in/vsti/media.json'),'--frames',str(R/'in/vsti/frames_sample'),'--out',str(dest/'i'),'--sample'])
spec=dict(tree=str(R/'from113/work/tree'),artifact=dict(path='fixture',sha256='fixture'),config=dict(path='fixture',sha256='fixture'),device='cpu')
dump(dest/'SPEC.json',spec)
entry.main(['job','--bound',str(dest/'i/BOUND.json'),'--spec',str(dest/'SPEC.json'),'--out',str(dest/'cell'),'--fixture'])
signal.setitimer(signal.ITIMER_REAL,0)
entry.main(['merge','--bound',str(dest/'i/BOUND.json'),'--out',str(dest/'MERGED.json'),str(dest/'cell/j')])
comparators=[str(R/'in/comparators'/n) for n in ('f17.per_question_scores.jsonl','p1m200.per_question_scores.jsonl')]
entry.main(['report','--merged',str(dest/'MERGED.json'),'--out',str(dest/'report'),'--comparators',*comparators])
entry.main(['score-check','--comparators',*comparators,'--out',str(dest/'SCORER_CHECK.json')])
cov.stop();cov.save();cov.json_report(outfile=str(dest/'coverage.json'))
completion=load(dest/'cell/j/COMPLETE.json')
dump(dest/'RESULT.json',dict(passed=completion['reason']=='complete' and not completion['missing'],synthetic=True,items=len(completion['keys']),captures=len(load(dest/'i/FRAMES.json')['captures']),entry_commands=['adapt','job','merge','report','score-check'],completion=pin(dest/'cell/j/COMPLETE.json'),report=pin(dest/'report/REPORT.json'),coverage=pin(dest/'coverage.json'),not_checked=['GPU model restoration and decode','real checkpoint prefill','real tower in this CLI run','namespace and remote staging']))
