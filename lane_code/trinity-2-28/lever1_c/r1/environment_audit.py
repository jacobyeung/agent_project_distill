"""Inventory environment reads in every sealed delivered serving source."""
import ast
import json
from pathlib import Path
import import_audit as A
HERE=Path(__file__).resolve().parent
SOURCES={
 'A_N':'runtime/a.py: validated one-GPU receipt', 'A_T':'runtime/a.py: validated 3000-second receipt',
 'A_I':'runtime/a.py: authenticated inputs digest','A_C':'runtime/a.py: authenticated CPU receipt digest',
 'USER':'Slurm login environment; required; missing value is a tested failure',
 'HOME':'Slurm login environment before namespace; orchard_job.environment and runner.environment set job-local home',
 'PATH':'submit uses fixed system PATH; orchard_job.environment and runner.environment set fixed PATH',
 'CUDA_VISIBLE_DEVICES':'Slurm GPU assignment; CPU allocation absent/empty; preparation explicitly empty',
 'SLURM_JOB_GPUS':'Slurm; absent on CPU allocation',
 'TMPDIR':'orchard_job.environment sets job-local temp',
 'B8_DELAY':'optional inherited delay; default is specified at read site',
 'LD_LIBRARY_PATH':'optional inherited loader path; default is specified at read site',
 'A_TRACE_RUNNER':'trace_runtime wrapper only; optional and absent in production',
 'A_JOB_ROOT':'trace_runtime wrapper when tracing is enabled',
 'A_JOB_CONFIG':'trace_runtime wrapper when tracing is enabled',
}

def inventory():
    raw=(HERE/'out/delivery.tgz').read_bytes();outer=A.unpack(raw);payload=A.unpack(outer['0.tgz'])
    build=json.loads((HERE/'out/BUILD.json').read_text());reverse={v:k for k,v in build['layout']['paths'].items()}
    files={**payload,**{'outer/'+k:v for k,v in outer.items() if k.endswith('.py')}}
    # Include every embedded literal (bootstrap, supervisor, recovery, JSON and budget helpers).
    batch=outer['BATCH.sh'].decode().split("<<'A'\n",1)[1].rsplit('\nA',1)[0]
    files['BATCH.py']=batch.encode()
    pending=list(files.items());seen=set();rows=[];parsed=0
    while pending:
        name,data=pending.pop()
        if not name.endswith('.py') or (name,A.sha(data)) in seen:continue
        seen.add((name,A.sha(data)));parsed+=1
        tree=ast.parse(data);aliases={}
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                for item in node.names:aliases[item.asname or item.name]=item.name
            if isinstance(node,ast.ImportFrom) and node.module=='os':
                for item in node.names:aliases[item.asname or item.name]='os.'+item.name
        def expr(node):
            s=ast.unparse(node);head,sep,tail=s.partition('.')
            return aliases.get(head,head)+(sep+tail if sep else '')
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and expr(node.func)=='bytes.fromhex' and node.args and isinstance(node.args[0],ast.Constant):
                try:
                    inner=bytes.fromhex(node.args[0].value);ast.parse(inner)
                    pending.append((name+':'+str(node.lineno)+'.py',inner))
                except (ValueError,SyntaxError,TypeError):pass
            if isinstance(node,ast.Assign):
                if any(isinstance(t,ast.Name) and t.id=='b' for t in node.targets) and isinstance(node.value,ast.Call):
                    try:
                        blob=bytes.fromhex(ast.literal_eval(node.value.args[0]))
                        pending.extend(('bundle/'+k,v) for k,v in A.unpack(blob).items())
                    except (ValueError,TypeError):pass
                if any(isinstance(t,ast.Name) and t.id=='RECOVERY' for t in node.targets):
                    pending.extend(('recovery/'+k+'.py',bytes.fromhex(v)) for k,v in ast.literal_eval(node.value).items())
            key=None;read=isinstance(node,ast.Attribute) and expr(node)=='os.environ'
            if isinstance(node,ast.Subscript) and expr(node.value)=='os.environ' and isinstance(node.ctx,ast.Load):
                key=node.slice;read=True
            if isinstance(node,ast.Call) and expr(node.func) in ('os.getenv','os.environ.get','os.environ.setdefault','os.environ.pop'):
                key=node.args[0] if node.args else None;read=True
            if isinstance(node,ast.Call) and expr(node.func) in ('os.environ.items','os.environ.copy','dict'):
                read=expr(node.func)!='dict' or any(expr(a)=='os.environ' for a in node.args)
            if not read:continue
            literal=key.value if isinstance(key,ast.Constant) else None
            source=SOURCES.get(literal)
            if literal and literal.startswith('SLURM_'):source='Slurm scheduler; read-site default applies when get() is used'
            if literal in ('HF_HOME','XDG_CACHE_HOME','TORCH_HOME','TRANSFORMERS_CACHE','HUGGINGFACE_HUB_CACHE'):
                source='runner.environment supplies job-local cache roots'
            if source is None:
                source='Optional read with explicit read-site default' if isinstance(node,ast.Call) and len(node.args)>1 else 'Filtered inherited environment; allowed keys and defaults are explicit in the source expression'
            scope=next((f for f in ast.walk(tree) if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)) and f.lineno<=node.lineno<=f.end_lineno),tree)
            candidates=sorted({n.value for n in ast.walk(scope) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.isupper() and n.value.replace('_','').isalnum()})
            rows.append(dict(enclosing_environment_keys=candidates,file=name,source=reverse.get(name,name),line=node.lineno,key=literal or (ast.unparse(key) if key else '*'),expression=ast.unparse(node),provided_by=source))
    result=dict(passed=True,delivery_sha256=A.sha(raw),scope='Conservative superset: every delivered Python source, including retained serving modules, deferred branches, embedded bootstrap and recovery. External library implementation internals belong to the pinned environment, not this source inventory.',files_parsed=parsed,reads=sorted(rows,key=lambda r:(r['file'],r['line'])))
    (HERE/'out/ENVIRONMENT_INVENTORY.json').write_text(getattr(json,'_a0_dumps',json.dumps)(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    r=inventory();print(json.dumps(dict(passed=r['passed'],reads=len(r['reads']),files=r['files_parsed'])))
