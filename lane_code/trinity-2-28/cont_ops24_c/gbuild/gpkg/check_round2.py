"""Run CPU checks under the requested host resource bound and retain evidence."""
import ast
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tag',default='')
    tag=parser.parse_args().tag
    if tag and not tag.replace('_','').isalnum():raise ValueError('invalid log tag')
    suffix='_'+tag if tag else ''
    resource.setrlimit(resource.RLIMIT_AS,(15*1024**3,15*1024**3))
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',TMPDIR=str(ROOT/'work/tests'))
    commands=[('TESTS_FINAL.txt',[sys.executable,'-B','-m','unittest','discover','-s','gpkg','-p','test_*.py','-v']),
              ('TESTS_KIT_FINAL.txt',[sys.executable,'-B','-m','unittest','discover','-s','kit2/kit/rerun2','-p','test_*.py','-v']),
              ('TESTS_FUNNEL_FINAL.txt',[sys.executable,'-B','-m','unittest','discover','-s','kit2/kit','-p','test_funnel.py','-v'])]
    results=[]
    for log,cmd in commands:
        log=log.replace('.txt',suffix+'.txt')
        with (ROOT/'out2'/log).open('x') as f:
            result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
        results.append(dict(command=cmd,log=log,returncode=result.returncode))
        if result.returncode:break
    source_paths=list((ROOT/'gpkg').glob('*.py'))+list((ROOT/'gpkg/point_runtime').glob('*.py'))+list((ROOT/'gpkg/runtime').glob('*.py'))+[ROOT/'gt/adapter.py',ROOT/'gt/v2.py',ROOT/'kit2/kit/rerun2/join.py']
    for path in source_paths:ast.parse(path.read_text(),filename=str(path))
    output=dict(commands=results,address_space_limit_bytes=15*1024**3,blas_threads=1,gpu_visibility='',
                child_peak_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                python_sources_parsed=len(source_paths),all_passed=len(results)==3 and all(r['returncode']==0 for r in results))
    (ROOT/'out2'/('CHECKS'+suffix+'.json')).write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output))
    return 0 if output['all_passed'] else 1


if __name__=='__main__':raise SystemExit(main())
