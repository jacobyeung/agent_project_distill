#!/usr/bin/env python3
"""Rerun independent-review probes read-only; write results under --out."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).absolute().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-root', required=True, type=Path, help='Read-only sb_crrev/scratch/rob')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rob = args.review_root
    base = HERE/'in/cont_ops/work/r1route/out3'
    commands, checks, results, sources = [], [], {}, {str(Path(__file__).absolute()):digest(Path(__file__))}
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(dict(check=name, status='PASS'))
    def run(name, options, expected):
        output = args.out/name
        cmd = [sys.executable,'-B',str(HERE/'callrate.py'),'--input-root',str(HERE/'in'),
               '--out',str(output),'--summary',*map(str,options)]
        commands.append(cmd)
        proc = subprocess.run(cmd, text=True, capture_output=True,
            env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
        (args.out/(name+'.stdout')).write_text(proc.stdout)
        (args.out/(name+'.stderr')).write_text(proc.stderr)
        result = json.loads((output/'callrate.json').read_text())
        results[name] = result
        sources.update({s['path']:s['sha256'] for s in result['sources']})
        for path in [output/'callrate.json', args.out/(name+'.stdout'), args.out/(name+'.stderr')]:
            sources[str(path.absolute())] = digest(path)
        check(name+'/exit', proc.returncode == expected)
        return proc, result
    a4 = ['--a',base/'A4/ret','--a-step',200]
    run('t0',a4,0)
    for name,step,code in [('t1',200,0),('t1b',400,2),('t2',200,2),('t2b',200,2),
                            ('t2c',200,2),('t2d',200,2),('t2e',200,0),('t2f',200,2),('t3b',200,2)]:
        root = rob/('t1' if name == 't1b' else name)/'ret'
        proc,result = run(name,['--a',root,'--a-step',step],code)
        if name == 't2':
            check('t2/refused_stdout',proc.stdout == '')
            check('t2/one_line_reason','PARTIAL' in proc.stderr and len(proc.stderr.splitlines()) == 1)
    proc,result = run('t2_allowed',['--a',rob/'t2/ret','--a-step',200,'--allow-partial','--allow-subset'],0)
    check('t2/banner',proc.stdout.startswith('PARTIAL:'))
    for kind,n,expected in [('object_abs_distance',100,150),('room_size_estimation',20,36)]:
        row = result['types'][kind]
        check('t2/'+kind+'/shared_marginals',row['a']['n'] == row['b']['n'] == row['paired']['n'] == n)
        check('t2/'+kind+'/coverage',row['a']['expected'] == row['b']['expected'] == expected)
        check('t2/'+kind+'/visible_coverage',f'{n}/{expected} / {n}/{expected}' in proc.stdout)
    run('t3',['--a',rob/'t3/f00dfeed1234/ret','--a-step',200],0)
    run('t3c',[*a4,'--a-package',HERE/'in/cont_ops16/work/c15/r1route/out3s/B'],2)
    for name in ('t1','t2e','t3'):
        check(name+'/same_metrics',results[name]['per_item'] == results['t0']['per_item'] or
              all({k:{x:y for x,y in v.items() if x!='source_read'} for k,v in results[name]['per_item'][s].items()} ==
                  {k:{x:y for x,y in v.items() if x!='source_read'} for k,v in results['t0']['per_item'][s].items()} for s in ('a','b')))
    both = [*a4,'--b',base/'B5/ret','--b-step',200]
    proc,_ = run('t4',both,2)
    check('t4/refusal',not proc.stdout and 'ID sets differ' in proc.stderr)
    proc,result = run('t4_allowed',[*both,'--allow-subset'],0)
    room = result['types']['room_size_estimation']
    check('t4/shared_marginals',room['a']['n'] == room['b']['n'] == room['paired']['n'] == 36)
    check('t4/visible_set_sizes','planned A=36 B=134' in proc.stdout)
    check('t4/shared_score',abs(room['b']['score']-0.6888888888888889) < 1e-12)
    result = dict(status='PASS',commands=commands,checks=checks,
                  sources=[dict(path=p,sha256=s) for p,s in sorted(sources.items())])
    (args.out/'review_probes.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS: {len(checks)} independent-review probe checks')


if __name__ == '__main__':
    main()
