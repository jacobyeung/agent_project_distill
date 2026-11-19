"""Native D builds and release-check compatibility; all writes stay under --work."""
import argparse, ast, base64, gzip, json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pack as P
import test_support as T
import pack_token as K
import pack_checks as Q

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work',required=True);a=parser.parse_args();w=Path(a.work).resolve();w.mkdir(parents=True,exist_ok=False,mode=0o700);P.limits()
    names=['build_d.py','build_support.py','make_items_d.py','place_fill_d.py','dryres_d.py','score_d.py','check_release_d.py','o_build_D.sh','bind_D200.json','bind_D544.json','TIMING_D.json','o_cpu_D.sh','o_sub_D.sh']
    before={n:P.file_digest(T.D/n) for n in names};rawtree=w/'supplied';rawtree.mkdir()
    for n in names:(rawtree/n).write_bytes((T.D/n).read_bytes())
    code='import runpy,sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);ns=runpy.run_path(sys.argv[1]+"/check_release_d.py");ns["main"].__globals__["W"]=Path(sys.argv[2]);ns["main"]()'
    def baseline(label):
        r=subprocess.run(['/usr/bin/python3','-I','-s','-B','-c',code,str(rawtree),str(w)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=P.environment(w),timeout=30)
        (w/(label+'.log')).write_bytes(r.stdout+r.stderr);P.need(r.returncode!=0 and b'AssertionError: score_d.py' in r.stderr,'Supplied drift baseline changed');return r.stderr.decode()
    baseline('raw_before');adapter=Path(__file__).with_name('pack_token.py');(rawtree/'pack_token.py').write_bytes(adapter.read_bytes());(rawtree/'test_pack_token.py').write_bytes(Path(__file__).with_name('test_pack_token.py').read_bytes());baseline('raw_after')
    P.need(before=={n:P.file_digest(rawtree/n) for n in names},'Additive adapter changed native sources')
    # Coherent test snapshot uses the pinned scorer already sealed in o_build_D.sh.
    # The newer loose scorer is never changed or downgraded in the supplied tree.
    here=w/'coherent';here.mkdir()
    for n in names:(here/n).write_bytes((T.D/n).read_bytes())
    assets=ast.literal_eval(next(l for l in (here/'o_build_D.sh').read_text().splitlines() if l.startswith('assets = ')).split('=',1)[1])
    score=gzip.decompress(base64.b64decode(assets['score_d.py']['data']));P.need(P.digest(score)==assets['score_d.py']['sha256'],'Embedded scorer pin differs');(here/'score_d.py').write_bytes(score)
    raw=P.tar_bytes(P.package_files(T.B5));source=w/'1.tgz';source.write_bytes(raw);items=w/'items/dist580.json';items.parent.mkdir();items.write_bytes((T.D/'evidence/items/dist580.json').read_bytes())
    runner=w/'0.py';runner.write_text('''import os,runpy,sys
root,stage,source,sha,items,binding,kind,adapter=sys.argv[1:]
sys.path.insert(0,root);os.urandom=lambda n:bytes([17])*n
sys.argv=[root+'/build_d.py',stage,source,sha,items,binding]
if kind=='native':runpy.run_path(root+'/build_d.py',run_name='__main__')
else:
 sys.argv=[adapter,'--kind','d','--source',root+'/build_d.py']+(['--enable-token','--token',kind] if kind!='default' else [])+['--']+sys.argv[1:]
 runpy.run_path(adapter,run_name='__main__')
''')
    reports={}
    for label,step,kind in [('actual200',200,'native'),('default200',200,'default'),('actual544',544,'a123456789abc')]:
        stage=w/label;stage.mkdir();binding=stage/'binding.json';binding.write_bytes((here/('bind_D'+str(step)+'.json')).read_bytes());env=P.environment(w);env['KROOT']=str(w/('k'+label))
        P.run(['/usr/bin/python3','-I','-s','-B',str(runner),str(here),str(stage),str(source),P.digest(raw),str(items),str(binding),kind,str(adapter)],w,w/(label+'.log'),env);reports[label]=P.read(stage/'BUILD.json')['D']
    import runpy
    native_dry={}
    for label in ('actual200','actual544'):
        files=P.untar((Path(reports[label]['delivery_dir'])/'1.tgz').read_bytes());payload=P.untar(files['0.tgz']);plan=json.loads(payload['9.json']);op_path=w/(label+'_operator.py');op_path.write_bytes(files['a/6.py']);op=runpy.run_path(str(op_path))
        native_dry[label]=Q.native_dry_predicates(json.loads(files['a/0.json']),plan,payload,op,op['descriptors']('unused'),op['memory_bound']())
    first=Path(reports['actual200']['delivery_dir'])/'1.tgz';second=Path(reports['default200']['delivery_dir'])/'1.tgz';P.need(first.read_bytes()==second.read_bytes(),'Default-OFF native delivery differs')
    P.run(['/usr/bin/python3','-I','-s','-B','-c',code,str(here),str(w)],w,w/'coherent_before.log')
    (here/'pack_token.py').write_bytes(adapter.read_bytes());(here/'test_pack_token.py').write_bytes(Path(__file__).with_name('test_pack_token.py').read_bytes())
    P.run(['/usr/bin/python3','-I','-s','-B','-c',code,str(here),str(w)],w,w/'coherent_after.log')
    # Run the public pack build path against the actual native builder and items.
    cfg=dict(work=str(w/'pack_build'),ledger=str(w/'ledger.jsonl'),normalize_wrapper=True,python=P.PYTHON,builder=dict(path=str(adapter),sha256=P.file_digest(adapter),argv=['--kind','d','--source',str(T.D/'build_d.py'),'--enable-token','--token','{token}','--','{work}/stage',str(source),P.digest(raw),str(items),str(T.D/'bind_D200.json')],env={'KROOT':'{work}/k'},report='{work}/stage/BUILD.json',key='D',inputs=[dict(path=str(T.D/'build_d.py'),sha256=P.file_digest(T.D/'build_d.py'))]))
    (w/'ledger.jsonl').write_text('');P.write(w/'build_config.json',cfg)
    P.run([P.PYTHON,'-I','-s','-B',str(Path(__file__).with_name('pack.py')),'build','--config',str(w/'build_config.json'),'--enable','--token','b123456789abc'],w,w/'pack_build.log');built=P.built(cfg)
    try:P.source_preflight(cfg)
    except P.Rejected as error:P.need('score_d.py' in str(error),'Wrong native source rejection')
    else:raise AssertionError('Raw source release was accepted')
    coherent_cfg=dict(builder=dict(path=str(here/'build_d.py'),sha256=P.file_digest(here/'build_d.py'),argv=['stage','source','sha',str(items),'binding']))
    P.need(P.source_preflight(coherent_cfg)['assets']==10,'Coherent native source failed')
    r10=(T.R/'build_r10.py').read_text();P.need(K.adapted(r10,'r10',None,False)==r10,'r10 default differs');compile(K.adapted(r10,'r10','c123456789abc',True),'r10-adapter','exec')
    result=dict(passed=True,native_dry=native_dry,default_off_delivery_bytes=first.stat().st_size,default_off_delivery_sha256=P.file_digest(first),native_checker=P.read(w/'RELEASE_RESULTS.json'),raw_checker_before_after='same pre-existing score_d.py mismatch',raw_sources_unchanged=True,raw_release_preflight_rejected=True,coherent_release_preflight_passed=True,coherent_checker_before_after=True,embedded_score_sha256=P.digest(score),loose_score_sha256=before['score_d.py'],r10_default_source_identical=True,r10_full_build=False,reason='Authenticated original A/B delivery archives required by r10 are absent',pack_build=built)
    P.write(w/'RESULT.json',result);print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
