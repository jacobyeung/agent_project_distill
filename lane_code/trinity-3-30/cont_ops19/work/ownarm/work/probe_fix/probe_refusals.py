"""Exercise the default scorer on copied synthetic returns."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
W=Path(__file__).resolve().parent;S=W.parents[1];K=S/'kit';B=S/'out/pkg/b200'
root=S/'work/proofc/ret_strict';inputs={}
def pin(p):inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [Path(__file__),*K.glob('*.py'),*K.glob('ref/*'),*K.glob('vendor/*.py'),B/'READ_PLAN.json',B/'tower_sequence.py',B/'package/0.json',B/'src/9.json',B/'src/items/devs1_routed.json',*root.rglob('*')]:
    if p.is_file():pin(p)
sys.path.insert(0,str(K));import ownread
refs,_=ownread.references();results={}
cases=['partial','archive_pin','room','mixed_export','journal_ids']
for case in cases:
    dest=W/'work'/('probe_'+case);shutil.copytree(root,dest)
    journal=dest/'metadata/reads/0/metadata/journals/0/0/items.jsonl'
    if case=='partial':
        lines=journal.read_text().splitlines();lines=[l for l in lines if json.loads(l)['arm']!='own'];journal.write_text('\n'.join(lines)+'\n')
    elif case=='archive_pin':
        p=dest/'metadata/EXPORT_PIN.json';v=json.loads(p.read_text());v['archive_sha256']='0'*64;p.write_text(json.dumps(v))
    elif case=='room':
        lines=journal.read_text().splitlines();v=json.loads(lines[0]);v['room_key']='deliberate-mismatch';lines[0]=json.dumps(v);journal.write_text('\n'.join(lines)+'\n')
    else:
        p=journal.parent/'environment.json';v=json.loads(p.read_text())
        if case=='mixed_export':v['binding']['export_sha256']='0'*64
        else:v['binding']['ids']=[]
        p.write_text(json.dumps(v))
    try:
        rs,_,_,_=ownread.load(dest,B,refs,False)
        results[case]=dict(accepted=True,own_rows=len(rs['own']),tower_rows=len(rs['tower']))
    except ValueError as e:results[case]=dict(accepted=False,error=str(e))
    if case=='partial':
        out=W/'work/probe_partial_score'
        cmd=[sys.executable,'-B',str(K/'ownread.py'),'--root',str(dest),'--package',str(B),'--out',str(out)]
        run=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        (W/'logs/partial_cli.txt').write_text('$ '+' '.join(cmd)+'\nexit='+str(run.returncode)+'\n'+run.stdout+run.stderr)
        results[case].update(cli_exit=run.returncode,cli_stderr=run.stderr.strip(),wrote_output=(out/'ownread.json').exists())
        diag=subprocess.run(cmd[:-1]+[str(out)+'_diag','--allow-partial'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        lines=diag.stdout.splitlines();score=json.loads((Path(str(out)+'_diag')/'ownread.json').read_text())
        results[case].update(allow_partial_exit=diag.returncode,lines=len(lines),lines_marked_partial=sum(l.startswith('PARTIAL') for l in lines),
                             all_complete=score['all_complete'],decision=score['all_within_bar_interval'])
for k,v in results.items():print(k,json.dumps(v))
(W/'REFUSALS.json').write_text(json.dumps(dict(results=results,input_sha256=inputs),indent=2)+'\n')
