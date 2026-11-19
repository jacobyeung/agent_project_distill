"""Tiny local tests of H's actual fill checks; no production placement."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path
from types import SimpleNamespace
import place_fill_h as place

def rejects(fn):
    try:fn()
    except (AssertionError,ValueError,KeyError):return
    raise AssertionError('Accepted invalid input')
def module(path):
    spec=importlib.util.spec_from_file_location('fill_h',str(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args();buildwork=Path(a.work)
    w=Path(tempfile.mkdtemp(prefix='place_',dir='/dev/shm/c18h'));here=Path(__file__).resolve().parent
    tree=ast.parse((here/'place_fill_h.py').read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    start=next(i for i,n in enumerate(run.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='reuse' for t in n.targets))
    end=next(i for i,n in enumerate(run.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='run')
    code=compile(ast.Module(body=run.body[start:end]),'<actual H fill preflight and hardlinks>','exec')
    source=w/'parts';source.mkdir();binding=json.loads((here/'bind_H544.json').read_text())
    vals={'config':dict(base_identity=binding['base_identity'],frame_layout='duplicate'),'receipt':dict(config_sha256=binding['config_sha256'],frame_layout='duplicate'),'data_receipt':{'synthetic':True}}
    for k,n in [('config','7'),('receipt','8'),('data_receipt','9')]:
        (source/n).write_text(json.dumps(vals[k]));binding['preparation_sha256'][k]=place.sha(source/n)
    for i in range(4):
        (source/str(i)).write_bytes(('part%d'%i).encode());binding['parts'][i]=dict(bytes=5,sha256=place.sha(source/str(i)))
    done=source/'5';done.write_text('%s %s %s\n'%(binding['object'],binding['archive_bytes'],binding['archive_sha256']))
    os.environ.update(REUSE_PARTS_FROM=str(source),PREP_FROM=str(source),DONE_FROM=str(done));os.environ.pop('CLAIM_FROM',None)
    def execute(b,label):
        dest=w/label;dest.mkdir();exec(code,dict(place.__dict__,binding=b,e=dest,pf={}))
        return dest
    dest=execute(binding,'valid')
    assert all((dest/str(i)).stat().st_ino==(source/str(i)).stat().st_ino for i in range(4))
    negatives=[]
    for label,mutate in [('base',lambda b:b.update(base_identity='wrong')),('config',lambda b:b.update(config_sha256='0'*64)),('prep_hash',lambda b:b['preparation_sha256'].update(config='0'*64)),('layout',lambda b:b.update(frame_layout='paired')),('part_sha',lambda b:b['parts'][3].update(sha256='0'*64)),('part_size',lambda b:b['parts'][3].update(bytes=6))]:
        bad=copy.deepcopy(binding);mutate(bad);rejects(lambda:execute(bad,label));assert not (w/label/'0').exists();negatives.append(label)
    done.write_text('wrong receipt\n');rejects(lambda:execute(binding,'bad_done'));negatives.append('upstream receipt')
    os.environ.pop('DONE_FROM');rejects(lambda:execute(binding,'missing_done'));negatives.append('missing DONE_FROM544')
    # Reuse E's reviewed streaming archive fixture test with its bounded synthetic data.
    source_test=(here/'reference_test_scan.py').read_text();namespace={};exec(source_test,namespace)
    scans={}
    for step in (200,544):
        sw=buildwork/str(step);fill=module(sw/'package/a/4.py');b=json.loads((here/('bind_H%d.json'%step)).read_text());r=fill.reviewed_binding()
        assert r=={k:v for k,v in b.items() if k in ('base_identity','config_sha256','frame_layout','lineage','member_directory','object','preparation_sha256','run','step','archive_bytes','archive_sha256')}
        args=SimpleNamespace(object=b['object'],step=step,lineage='SFT');artifact={k:b[k] for k in ('base_identity','config_sha256','frame_layout','step')}
        for name in ('heads','full_weights'):artifact[name]={'path':'runs/'+b['run']+'/'+b['member_directory']+'/'+fill.MEMBERS[name]}
        export=dict(member_directory=b['member_directory']);archive=dict(sha256=b['archive_sha256'],parts=b['parts']);prep={k:{'sha256':v} for k,v in b['preparation_sha256'].items()}
        fill.bind_review(args,export,artifact,archive,prep,r)
        for key in ('step','base_identity','config_sha256','frame_layout'):
            bad=dict(artifact);bad[key]='wrong';rejects(lambda:fill.bind_review(args,export,bad,archive,prep,r))
        scan_dir=w/('scan%d'%step);scan_dir.mkdir();scans[str(step)]=namespace['test_scan'](fill,scan_dir)
        for argv in [['--time','03:00:00'],['--gpus','2'],['--gpus','1','--gpus','1'],['--time=05:00:00']]:
            proc=subprocess.run(['/usr/bin/python3','-B',str(sw/'package/3.py'),'submit']+argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            assert proc.returncode and (b'H requires' in proc.stderr or b'Duplicate' in proc.stderr)
    result=dict(passed=True,synthetic_only=True,hardlinks_verified=4,refused_before_linking=negatives,archive_scans=scans,entrypoint_guards=True)
    (buildwork/'PLACE_RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
