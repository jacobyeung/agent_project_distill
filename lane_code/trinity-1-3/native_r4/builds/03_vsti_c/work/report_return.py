"""Build the comparison report locally while preserving returned absolute pins."""
from pathlib import Path
import argparse,os,subprocess,sys
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import dump,pin
from venue import extract,namespace

p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--root',required=True);a=p.parse_args()
root=Path(a.root).resolve();root.mkdir(parents=True,exist_ok=False)
extract(a.archive,root/'run',1_000_000_000)
(root/'report').mkdir()
bindings=[(R,R,False),(root/'run','/r',False),(root/'report','/report',True)]
cmd=namespace(root,bindings,cpu=True,host_bwrap=True)+['--setenv','PYTHONPATH',os.environ['PYTHONPATH'],
    sys.executable,'-s','-B',str(B/'code/entry.py'),'report','--merged','/r/MERGED.json','--out','/report',
    '--comparators',str(R/'in/comparators/f17.per_question_scores.jsonl'),str(R/'in/comparators/p1m200.per_question_scores.jsonl'),
    '--release-check',str(B/'out/RELEASE_CHECK.json')]
dump(root/'COMMAND.json',dict(argv=cmd,archive=pin(a.archive)))
raise SystemExit(subprocess.run(cmd).returncode)
