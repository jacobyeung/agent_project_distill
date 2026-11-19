"""Exercise actual H/D step-400 fill blocks with tiny local data; no Orchard I/O."""
import ast
import copy
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parent

def run(kind):
    folder=ROOT/('hcam' if kind=='H' else 'dbuild');sys.path.insert(0,str(folder))
    place=importlib.import_module('place_fill_'+kind.lower())
    work=Path(tempfile.mkdtemp(prefix='fill400_'+kind,dir=str(ROOT/'validation')))
    source=work/'source';source.mkdir()
    binding=json.loads((folder/('bind_'+kind+'400.json')).read_text())
    tree=ast.parse((folder/('place_fill_'+kind.lower()+'.py')).read_text())
    body=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run').body
    start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='reuse' for t in n.targets))
    end=next(i for i,n in enumerate(body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='run')
    module=ast.parse('');module.body=body[start:end];code=compile(module,'<actual step-400 fill block>','exec')
    prep={'config':dict(base_identity=binding['base_identity'],frame_layout='duplicate'),'receipt':dict(config_sha256=binding['config_sha256'],frame_layout='duplicate'),'data_receipt':{'synthetic':True}}
    for key,n in [('config','7'),('receipt','8'),('data_receipt','9')]:
        (source/n).write_text(json.dumps(prep[key]));binding['preparation_sha256'][key]=place.sha(source/n)
    for i in range(4):
        (source/str(i)).write_bytes(('part%d'%i).encode());binding['parts'][i]=dict(bytes=5,sha256=place.sha(source/str(i)))
    done=source/'5';done.write_text('%s %s %s\n'%(binding['object'],binding['archive_bytes'],binding['archive_sha256']))
    def fixture_path(value):return done if str(value)==binding['done'] else Path(value)
    os.environ.update(REUSE_PARTS_FROM=str(source),PREP_FROM=str(source));os.environ.pop('DONE_FROM',None);os.environ.pop('CLAIM_FROM',None)
    def execute(b,label,valid=False):
        dest=work/label;dest.mkdir()
        try:exec(code,dict(place.__dict__,Path=fixture_path,binding=b,e=dest,pf={}))
        except (ValueError,AssertionError,FileNotFoundError):
            assert not valid
            assert not (dest/'0').exists(),'Linked before rejecting invalid inputs'
            return
        assert valid,'Invalid input accepted: '+label
        assert all((dest/str(i)).stat().st_ino==(source/str(i)).stat().st_ino for i in range(4))
    execute(binding,'valid',True)
    mutations=[('base',lambda b:b.update(base_identity='wrong')),('config',lambda b:b.update(config_sha256='0'*64)),('layout',lambda b:b.update(frame_layout='paired')),('last_part_hash',lambda b:b['parts'][3].update(sha256='0'*64)),('last_part_size',lambda b:b['parts'][3].update(bytes=6))]
    for key in prep:mutations.append(('prep_'+key,lambda b,k=key:b['preparation_sha256'].update({k:'0'*64})))
    for label,mutate in mutations:
        bad=copy.deepcopy(binding);mutate(bad);execute(bad,label)
    done.write_text('wrong receipt\n');execute(binding,'wrong_done')
    print(json.dumps(dict(passed=True,kind=kind,valid_hardlinks=4,rejected_before_linking=[x[0] for x in mutations]+['wrong_done'])))

if __name__=='__main__':run(sys.argv[1])
