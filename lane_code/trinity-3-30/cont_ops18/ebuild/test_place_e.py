"""Exercise placement preflight and single-pull orchestration with tiny local fixtures."""
import ast
import copy
import json
import os
import tempfile
from pathlib import Path
import place_fill_e
from test_e import rejects

HERE=Path(__file__).resolve().parent


def main():
    work=Path(tempfile.mkdtemp(prefix='place_',dir='/dev/shm/c18e'))
    tree=ast.parse((HERE/'place_fill_e.py').read_text())
    run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    # Execute the actual preparation/receipt and transfer blocks, without placement or subprocess I/O.
    start=next(i for i,n in enumerate(run.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='reuse' for t in n.targets))
    end=next(i for i,n in enumerate(run.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
             and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='run'
             and isinstance(n.value.args[0],ast.BinOp))
    code=compile(ast.Module(body=run.body[start:end]),'<actual place_fill_e preflight and part loop>','exec')
    source=work/'prep';source.mkdir();binding=json.loads((HERE/'bind_E200.json').read_text())
    cfg=dict(base_identity=binding['base_identity'],frame_layout='duplicate')
    rec=dict(config_sha256=binding['config_sha256'],frame_layout='duplicate')
    data={'synthetic':True}
    paths={}
    for key,name,value in [('config','config.json',cfg),('receipt','prepared/s1_receipt.json',rec),('data_receipt','data_receipt.json',data)]:
        p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));paths[key]=p
        binding['preparation_sha256'][key]=place_fill_e.sha(p)
    binding['prep_paths']={k:str(v) for k,v in paths.items()}
    # PREP_FROM's relative fallback uses the sealed D0 paths. Keep those paths for alternate layouts.
    real=json.loads((HERE/'bind_E200.json').read_text())
    binding['prep_paths']=real['prep_paths']
    done=work/'upstream.done';done.write_text('%s %s %s\n'%(binding['object'],binding['archive_bytes'],binding['archive_sha256']))
    binding['done']=str(done)
    binding['parts']=[dict(p,bytes=4) for p in binding['parts']]
    os.environ['PREP_FROM']=str(source)
    os.environ.pop('REUSE_PARTS_FROM',None);os.environ.pop('DONE_FROM',None);os.environ.pop('CLAIM_FROM',None)
    calls=[]
    class FakeProcess:
        @staticmethod
        def run(argv,**kw):
            calls.append(argv)
            assert argv[0]=='gsutil' and 'Boto:num_retries=0' in argv and '-m' not in argv
            Path(argv[-1]).write_bytes(b'part')
    def execute(b,label):
        e=work/label;e.mkdir()
        namespace=dict(place_fill_e.__dict__,binding=b,e=e,subprocess=FakeProcess)
        exec(code,namespace)
        return e
    e=execute(binding,'valid')
    assert len(calls)==4 and [c[-2] for c in calls]==[p['uri'] for p in binding['parts']]
    assert all((e/str(i)).read_bytes()==b'part' for i in range(4))
    for name,mutate in [('base',lambda b:b.update(base_identity='wrong')),
                         ('config',lambda b:b.update(config_sha256='0'*64)),
                         ('prep_hash',lambda b:b['preparation_sha256'].update(config='0'*64)),
                         ('layout',lambda b:b.update(frame_layout='paired'))]:
        b=copy.deepcopy(binding);mutate(b);calls[:]=[]
        rejects(lambda:execute(b,'bad_'+name));assert not calls
    done.write_text('wrong receipt\n');calls[:]=[];rejects(lambda:execute(binding,'bad_done'));assert not calls
    result=dict(passed=True,synthetic=True,part_pull_count=4,ordered_once=True,
                failures_before_download=['base_identity','config_identity','preparation_sha256','frame_layout','upstream_receipt'],
                actual_whole_archive_scan_test='test_e.py',work=str(work))
    (work/'PLACE_RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
