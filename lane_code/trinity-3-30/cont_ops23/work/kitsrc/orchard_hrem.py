"""Local Orchard orchestration helpers; invoked by the streamed shell scripts."""
import argparse
import json
from pathlib import Path
from build_remainder_h import build
from return_tools_h import package_info, require, read, segment
from fetch_validation import digest
from score_h_merge import score

def publication(p):
    p=Path(p);info=package_info(p)
    saved=p/'a/f'
    names=('0.tgz','EXIT.json','RETURN_RECEIPT.json')
    if any((saved/n).exists() for n in names):
        require(all((saved/n).is_file() for n in names),'Incomplete saved publication')
        return dict(package=str(p),archive=str(saved/'0.tgz'),exit=str(saved/'EXIT.json'),receipt=str(saved/'RETURN_RECEIPT.json'))
    job=int((p/'a/8.txt').read_text().strip());token=info['token']+'%08x'%job
    pool=Path(info['plan_value']['pool'])/token
    # The pool receipts are authenticated before use; never retry a fetch.
    return dict(package=str(p),archive=str(pool/'result.tar.gz'),exit=str(pool/'EXIT.json'),receipt=str(pool/'RETURN_RECEIPT.json'))

def check(stage,parent,step):
    r=read(Path(stage)/'BUILD.json')['H']
    require(r['parent']==str(Path(parent).resolve()) and r['export_binding']['step']==step,'Stage/parent/step mismatch')
    return r

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build','resolve','fetch'])
    for n in ('parent','stage','step'):p.add_argument('--'+n,required=True)
    a=p.parse_args();step=int(a.step);require(step in (200,400,544),'Unsupported step')
    if a.action=='build':
        info=package_info(a.parent);require(info['export_binding']['step']==step,'Parent step mismatch')
        s=publication(a.parent);r=build(a.parent,s['archive'],s['exit'],s['receipt'],a.stage)
        print(json.dumps({k:r[k] for k in ('package','walltime','timing')},sort_keys=True))
    elif a.action=='resolve':
        r=check(a.stage,a.parent,step);print(r['package']);print(r['walltime'])
    else:
        r=check(a.stage,a.parent,step);stage=Path(a.stage)
        rest=publication(r['package'])
        from fetch_validation import fetch
        destination=Path(r['package'])/'a/f'
        token=read(rest['exit'])['token']
        if Path(rest['archive'])!=destination/'0.tgz':
            fetch(r['package'],token,destination)
        rest.update(archive=str(destination/'0.tgz'),exit=str(destination/'EXIT.json'),receipt=str(destination/'RETURN_RECEIPT.json'))
        spec=dict(parent=r['partial'],remainder=rest)
        with (stage/'SCORE_SPEC.json').open('x') as f:json.dump(spec,f,sort_keys=True,indent=2)
        result=score(spec,stage/'score')
        with (stage/'SCORES.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
        print(json.dumps(dict(scores=str(stage/'SCORES.json'),completed=result['meta']['completed'])))
if __name__=='__main__':main()
