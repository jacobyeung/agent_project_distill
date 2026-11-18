"""Render Cprime operator drivers from C4 sources and rendered scripts."""
import ast,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
from rebind import ROOT,load,write,sha
from cprime_gate import BASE,GO,B1,REMOVE_PATH
OLD=Path('/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1')
DEST=OLD.with_name('drv_cp')

def main():
    DEST.mkdir(mode=0o700,exist_ok=True)
    op=load(ROOT/'out/OPERATOR.json');binding=load(ROOT/'out/BINDING.json')
    assert op['job_name']==binding['job_name'] and binding['config_identity']!=BASE
    archive=ROOT/'out'/op['archive'];assert sha(archive)==op['sha256']
    with tarfile.open(archive) as tf:members={m.name:tf.extractfile(m).read() for m in tf}
    pins=load(OLD/'PACKET_PINS.json')
    pins.update(bundle=op['bundle'],kit=op['kit'],store=binding['store_key'],run=binding['run_key'],
        identity=binding['config_identity'],outer=op['sha256'],archive=op['archive'],archive_bytes=archive.stat().st_size,
        members=len(members),deriver=hashlib.sha256(members['d.py']).hexdigest(),contract=op['contract'],job_name=binding['job_name'])
    write(DEST/'PACKET_PINS.json',pins)
    code='''"""Authenticate Cprime archive and expose operator pins."""
import hashlib,io,json,re,tarfile
from pathlib import Path
W=Path(__file__).resolve().parent
PINS=json.loads((W/'PACKET_PINS.json').read_text())
SNAP=Path(OUT)
ARCHIVE=(SNAP/PINS['archive']).read_bytes()
assert hashlib.sha256(ARCHIVE).hexdigest()==PINS['outer']
with tarfile.open(fileobj=io.BytesIO(ARCHIVE)) as tf:
 MEMBERS={}
 for m in tf:
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and m.name not in MEMBERS
  MEMBERS[m.name]=tf.extractfile(m).read()
SUMS={n:h for h,n in (line.split('  ',1) for line in MEMBERS['sums.txt'].decode().splitlines())}
assert set(SUMS)==set(MEMBERS)-{'sums.txt'}
assert all(hashlib.sha256(MEMBERS[n]).hexdigest()==h for n,h in SUMS.items())
BINDING=json.loads(MEMBERS['BINDING.json'])
assert BINDING['config_identity']==PINS['identity']
'''.replace('Path(OUT)','Path('+repr(str(ROOT/'out'))+')')
    oldpc=(OLD/'packet_config.py').read_text()
    code+=oldpc[oldpc.index('def pending_script('):].replace("dest = W/'fixture_c3'","dest = W/'fixture_cp'")
    (DEST/'packet_config.py').write_text(code)
    helpers=('authority_body.py','derive_body.py','evidence_body.py','q_check.py','selection_runtime.py','staging_check.py',
        'scan_body.py','cert_policy.py','cert_build.py','session_build.py','mint_fresh.py','review_policy.py','review_build.py')
    for n in helpers:
        text=(OLD/n).read_text()
        if n=='session_build.py':text=text.replace('08f3a7b2',op['sha256'][:8])
        if n=='mint_fresh.py':text=text.replace("run != '05b8ac69'","run != "+repr(pins['run']))
        if n=='evidence_body.py':
            text=text.replace("cfg['remove_files'][-1]==dict(path='@REMOVE_PATH@',sha256='@REMOVE_SHA256@')","dict(path='@REMOVE_PATH@',sha256='@REMOVE_SHA256@') in cfg['remove_files']")
            anchor=" assert 'n.json' in binding['record_files']"
            text=text.replace(anchor,anchor+"\n assert cfg['remove_files'][-1]=="+repr(dict(path=REMOVE_PATH,sha256=B1))+"\n assert sha(b/'z.json')==sha(b/'records/z.json')=="+repr(B1))
        if n=='review_policy.py':
            text=text.replace("'review_r1c3')","'review_r1c3', 'review_cprime')",1).replace("'rc3.txt')","'rc3.txt', 'rcp.txt')",1)
            text=text.replace("text = texts[short]","text = texts[short]\n        if name=='review_cprime':text=normalize_cprime(text)")
            text=text.replace("name in ('review_r1c1','review_r1c2','review_r1c3')","name in ('review_r1c1','review_r1c2','review_r1c3','review_cprime')")
            text=text.replace("packet_section(texts['rc3.txt'], 'C')","packet_section(normalize_cprime(texts['rcp.txt']), 'C')")
            text=text.replace("final_reviewer='review_r1c3'","final_reviewer='review_cprime'").replace('all eleven independent verdicts','all twelve independent verdicts')
            text=text.replace('hashlib.sha256(text.encode()).hexdigest()', 'hashlib.sha256(texts[short].encode()).hexdigest()')
            text+="\ndef normalize_cprime(text):\n    return text.replace('Packet C′', 'Packet C').replace(\"Packet C'\", 'Packet C').replace('Packet Cprime', 'Packet C')\n"
        if n=='review_build.py':
            text=text.replace("'r1c3')","'r1c3','cprime')").replace("'REVIEW_VERDICT_R1C3.md')","'REVIEW_VERDICT_R1C3.md','REVIEW_VERDICT_CPRIME.md')")
            text=text.replace('eleven-review','twelve-review').replace('review_r1c3 accepted','review_cprime accepted')
            text=text.replace("if not path.is_file():raise SystemExit('PENDING: missing '+name)","if not path.is_file():\n  fallback=json.loads((W/'ANTECEDENT_TEXTS.json').read_text())\n  if short not in fallback:raise SystemExit('PENDING: missing '+str(path))\n  texts[short]=fallback[short];continue")
        (DEST/n).write_text(text)
    tree=ast.parse((OLD/'rv1.sh').read_text().split("<<'PYCODE'\n",1)[1].rsplit('\nPYCODE',1)[0])
    texts=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='texts' for t in n.targets))
    assert len(texts)==11;write(DEST/'ANTECEDENT_TEXTS.json',texts)
    builder=(OLD/'build_drivers.py').read_text().split("script('pr1.sh'",1)[0]
    begin=builder.index("proof=(EX/");end=builder.index("p=W/'L1_mint.sh'",begin)
    builder=builder[:begin]+builder[end:]
    builder=builder.replace('eleven-review','twelve-review')
    builder=builder.replace('trinity-1-3','trinity-3-30').replace(str(OLD),str(DEST)).replace('08f3a7b2',op['sha256'][:8])
    (DEST/'build_drivers.py').write_text(builder)
    subprocess.run([sys.executable,'-B',str(DEST/'build_drivers.py')],check=True,cwd=DEST)
    for n in ('rv1.sh','sc1.sh','si1.sh'):
        p=DEST/n
        if not p.exists():p.write_text('#!/bin/bash\nset +x\n# C_PACKET_PENDING '+n+'\necho "PENDING: packet C requires '+n+'" >&2\nexit 4\n')
    def repin(text):
        for a,b in ((BASE,pins['identity']),('05b8ac69',pins['run']),('7f1589c1',pins['store']),
            ('08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd',pins['outer'])):text=text.replace(a,b)
        return text
    pre=(OLD/'pre1.sh').read_text().split("old=k.with_name",1)[0]
    pre=pre.replace("need(pointer['rows']=='exact','population equality requires exact continuation')","need(pointer['rows']=='rebind','Cprime requires rebind continuation')")
    pre=pre.replace('[[ $# -le 1 ]]','[[ $# == 0 ]]')
    pre=pre.replace(' "${1:-/tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/runs/05b8ac69/inputs}"','')
    pre=pre.replace(';cinputs=Path(sys.argv[3])','')
    pre=pre.replace('# Optional argument: login-visible preserved C inputs directory from proof 172180.','# Verify the real A donor; rebind mode intentionally changes populations.')
    pre+='print("PASS REAL A resume pointer; Cprime rebind policy verified; production admission runs in job")\nEND\n'
    (DEST/'pre1.sh').write_text(repin(pre))
    template=(ROOT/'tools/cprime_submit.sh.in').read_text()
    for k,v in dict(**pins,go=GO,gate=hashlib.sha256(members['s.sh']).hexdigest(),sums=hashlib.sha256(members['sums.txt']).hexdigest(),wrapper=op['wrapper_sha256']).items():
        template=template.replace('@'+k.upper()+'@',str(v))
    (DEST/('go_submit_canary_delta_'+pins['outer'][:8]+'.sh')).write_text(template)
    mon=repin((OLD/'mon.sh').read_text())
    mon=mon.replace('job=$(cat "$BUN/job.id")','[[ -f "$BUN/training.job.id" ]] || { echo "NOT_SUBMITTED; inspect any training.started marker"; exit 0; }\njob=$(cat "$BUN/training.job.id")')
    mon=mon.replace(' and training !=job','')
    (DEST/'mon.sh').write_text(mon)
    for p in DEST.glob('*.sh'):
        p.chmod(0o600 if p.name=='si1.sh' else 0o700);subprocess.run(['bash','-n',str(p)],check=True)
    helper=Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py')
    assert sha(helper)=='b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d'
    write(DEST/'BUILD_STATUS.json',dict(status='RENDERED_REVIEW_REQUIRED',pins=pins,
        review='events/review_cprime/REVIEW_VERDICT_CPRIME.md',go_sha256=GO,
        verified_mint_helper=dict(path='/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py',sha256='b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d')))
    names=[p for p in DEST.iterdir() if p.is_file() and p.name!='DRIVER_SHA256SUMS.txt']
    (DEST/'DRIVER_SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(names)))
    print(json.dumps(dict(drivers=str(DEST),archive=pins['archive'])),flush=True)
if __name__=='__main__':main()
