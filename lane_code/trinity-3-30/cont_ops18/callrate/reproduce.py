#!/usr/bin/env python3
"""Fail-loud reproduction of the supplied step-200/544 score and call counts."""
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
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-root',type=Path,default=HERE/'in')
    parser.add_argument('--out',type=Path,default=HERE/'out')
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    base=args.input_root/'cont_ops/work/r1route/out3'
    ref=args.input_root/'cont_ops16/work/c15/r1route/out3s/scoresAB/scores.json'
    saved=json.loads(ref.read_text())
    sources={str(ref.absolute()):digest(ref), str(Path(__file__).absolute()):digest(__file__)}
    commands=[]
    results={}
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
    for name,root in [('step200',base/'A4/ret'),('room134',base/'B5/ret')]:
        cmd=[sys.executable,'-B',str(HERE/'callrate.py'),'--input-root',str(args.input_root),'--a',str(root),'--a-step','200','--out',str(args.out/name),'--summary']
        commands.append(cmd)
        # JSON goes to callrate.json; do not keep a redundant stdout copy.
        proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        if proc.returncode:
            raise RuntimeError('Reproduction CLI failed: '+' '.join(cmd)+'\n'+proc.stderr)
        if proc.stderr or proc.stdout != (args.out/name/'callrate.summary.txt').read_text():
            raise AssertionError('Summary stdout differs or stderr is not empty: '+name)
        if len(proc.stdout.splitlines()) > 20:
            raise AssertionError('Summary exceeds one screen: '+name)
        result_path=args.out/name/'callrate.json'
        result=json.loads(result_path.read_text())
        results[name]=result
        sources.update({s['path']:s['sha256'] for s in result['sources']})
        sources[str(result_path.absolute())]=digest(result_path)
    checks=[]
    def equal(label,actual,expected):
        if isinstance(expected,(int,float)):
            matches = actual is not None and abs(actual-expected)<1e-12
        else:
            matches = actual==expected
        if not matches:
            raise AssertionError((label,actual,expected))
        checks.append(dict(check=label,actual=actual,expected=expected,status='PASS'))
    for kind in ('camera_displacement','camera_rotation','camera_movement_direction','object_abs_distance','room_size_estimation'):
        row=results['step200']['types'][kind]
        target=saved['types'][kind]
        for side,ref_side in [('a','current'),('b','baseline')]:
            for key,ref_key in [('score','score'),('n','completed'),('call_count','call_items'),('capped_count','capped')]:
                equal(kind+'/'+side+'/'+key,row[side][key],target[ref_side][ref_key])
                if key == 'score' and row[side][key] != target[ref_side][ref_key]:
                    raise AssertionError(('Score is not bit-for-bit equal',kind,side))
        for key in ('value','ci95','ci9929','upper95','n','rooms'):
            equal(kind+'/paired_score/'+key,row['paired']['score'][key],target['paired'][key])
    room36 = results['step200']['types']['room_size_estimation']
    equal('room36/b/rounded_score',f"{room36['b']['score']:.6f}",'0.116667')
    equal('room36/b/capped',room36['b']['capped_count'],29)
    equal('room36/rounded_delta',f"{room36['paired']['score']['value']:.2f}",'55.28')
    equal('room36/rounded_ci',[f'{v:.2f}' for v in room36['paired']['score']['ci95']],['38.82','70.39'])
    equal('room36/primary_source',room36['source_reads']['b'],['b1/read 0'])
    secondary = results['step200']['room_secondary']
    equal('room36/secondary_source',secondary['source_reads']['b'],['b2/read 0'])
    equal('room36/secondary_capped',secondary['b']['capped_count'],27)
    equal('room36/secondary_delta',f"{secondary['paired']['score']['value']:.2f}",'55.83')
    distance = results['step200']['types']['object_abs_distance']
    for side, copied, answered in [('a',12,150),('b',70,147)]:
        equal('distance/'+side+'/usage',distance[side]['usage'],1.)
        equal('distance/'+side+'/copied',distance[side]['copied_unconverted_count'],copied)
        equal('distance/'+side+'/answer',distance[side]['answer_count'],answered)
    equal('distance/b/not_seen',distance['b']['not_seen_count'],3)
    rooms=results['room134']['types']['room_size_estimation']
    for label,value,expected in [('room134/a/n',rooms['a']['n'],134),('room134/b/n',rooms['b']['n'],134),
                                  ('room134/calls200',rooms['a']['call_count'],0),('room134/calls544',rooms['b']['call_count'],134),
                                  ('room134/capped544',rooms['b']['capped_count'],115)]:
        equal(label,value,expected)
    manifest_path=base/'bases/b2/src/items/room134.json'
    manifest=json.loads(manifest_path.read_text())
    sources[str(manifest_path.absolute())]=digest(manifest_path)
    for name,keys in manifest['sets'].items():
        for side,ref_side in [('a','current'),('b','baseline')]:
            rows=results['room134']['per_item'][side]
            equal('room134/'+name+'/'+side+'/score',sum(rows[k]['score'] for k in keys)/len(keys),saved['rooms'][name][ref_side]['score'])
    from bootstrap import bootstrap
    for population,n in [('dev-S1',36),('R0-dev',98),('all',134)]:
        group=results['room134']['room_mra'][population]
        keys=sorted(manifest['sets'][population] if population!='all' else [i['id'] for i in manifest['items']])
        for side in ('a','b'):
            equal('population/'+population+'/'+side+'/n',group[side]['n'],n)
            rows=results['room134']['per_item'][side]
            equal('population/'+population+'/'+side+'/mra_answer',group[side]['mra_answer'],sum(rows[k]['score'] for k in keys)/n)
        a,b=results['room134']['per_item']['a'],results['room134']['per_item']['b']
        expected=bootstrap([(a[k]['room'],100*(a[k]['score']-b[k]['score'])) for k in keys])
        for key,value in expected.items():
            equal('population/'+population+'/paired/'+key,group['paired'][key],value)
    for side,population,want in [('b','dev-S1','11.11'),('b','R0-dev','4.90'),('b','all','6.57'),
                                  ('a','all','64.40'),('a','R0-dev','62.76')]:
        equal('population/rounded/'+side+'/'+population,f"{100*results['room134']['room_mra'][population][side]['mra_answer']:.2f}",want)
    for population in ('dev-S1','R0-dev'):
        equal('A4/population/'+population+'/n',results['step200']['room_mra'][population]['a']['n'],36 if population=='dev-S1' else 0)
    example = HERE/'examples/devs1_wording_strata.json'
    make_cmd = [sys.executable,'-B',str(HERE/'make_strata_example.py'),'--input',str(args.out/'step200/callrate.json'),'--out',str(example)]
    commands.append(make_cmd)
    subprocess.run(make_cmd, check=True, capture_output=True, text=True, env=env)
    strata_cmd = [*commands[0]]
    strata_cmd[strata_cmd.index('--out')+1] = str(args.out/'strata_example')
    strata_cmd += ['--strata',str(example)]
    commands.append(strata_cmd)
    proc = subprocess.run(strata_cmd, capture_output=True, text=True, env=env)
    if proc.returncode or proc.stderr:
        raise RuntimeError('Strata CLI failed: '+proc.stderr)
    strata_path = args.out/'strata_example/callrate.json'
    stratified = json.loads(strata_path.read_text())
    sources.update({s['path']:s['sha256'] for s in stratified['sources']})
    for path in (strata_path, example, HERE/'make_strata_example.py'):
        sources[str(path.absolute())] = digest(path)
    groups = stratified['types']['object_abs_distance']['by_stratum']
    equal('strata/all_150',sum(g['a']['n'] for g in groups.values()),150)
    equal('strata/same_per_item',stratified['per_item']==results['step200']['per_item'],True)
    for label,group in groups.items():
        equal('strata/'+label+'/paired_n',group['a']['n'],group['paired']['n'])
        equal('strata/'+label+'/call_marginals',group['a']['n'],group['b']['n'])
        equal('strata/'+label+'/units_partition',sum(g['a']['n'] for g in stratified['types']['object_abs_distance']['by_stratum_unit'][label].values()),group['a']['n'])
    result=dict(status='PASS',commands=commands,checks=checks,sources=[dict(path=p,sha256=s) for p,s in sorted(sources.items())])
    (args.out/'reproduction.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('PASS:',len(checks),'reproduction checks; room134 calls200=0, calls544=134, capped544=115')


if __name__=='__main__':
    main()
