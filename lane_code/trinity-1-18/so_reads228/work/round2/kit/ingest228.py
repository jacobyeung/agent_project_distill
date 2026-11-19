"""Publish an unpacked return for corpus ingestion using SUMMARY, never EXIT status."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *

def ingest(root,comparison):
    root=local(root)
    if not beneath(root.resolve(),(HERE/'ingest').resolve()):
        raise Refusal('Corpus return must be inside this kit/ingest directory')
    summary=read(root/'SUMMARY.json')
    reasons=[]
    if 'failure' not in summary or summary['failure'] is not None:reasons.append('SUMMARY failure')
    if type(summary.get('completed')) is not int or summary['completed']<50:reasons.append('SUMMARY completed <50')
    if (root/'FAILED.json').exists():reasons.append('FAILED.json exists')
    if comparison.get('verdict')!='SAME_INSTRUMENT' or comparison.get('eligible') is not True:
        reasons.append('comparison is diagnostic-only')
    return dict(status='READY_FOR_CORPUS' if not reasons else 'DIAGNOSTIC_ONLY',
        corpus_return=str(root),summary=summary,reasons=reasons,
        completion_source='SUMMARY.json; EXIT authenticates the envelope, not prefix success')

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--return',dest='root',required=True)
    parser.add_argument('--comparison',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args(argv);value=ingest(args.root,read(args.comparison))
    write(local(args.out),value);print(json.dumps(value,sort_keys=True))
    return 0 if value['status']=='READY_FOR_CORPUS' else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError,KeyError) as error:
        print('REFUSED: '+str(error),file=sys.stderr);raise SystemExit(2)
