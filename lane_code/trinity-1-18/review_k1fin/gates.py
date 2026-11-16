import sys,json,copy,shutil,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
FK='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_finalize_v2/finalize_k1.py'
spec=importlib.util.spec_from_file_location('fk',FK); fk=importlib.util.module_from_spec(spec); spec.loader.exec_module(fk)
ORIG=dict(fk.PATHS); M=Path('/scratch/jjyeung/orch_n30/review_k1fin/mut')
# skip timing (slow & irrelevant to flags) only if requested
if '--skip-timing' in sys.argv:
    fk.fill_timing=lambda m,d,s,t:{'source_counts':{}}
def jl(p): return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
def wjl(p,rows): Path(p).write_text(''.join(json.dumps(r)+'\n' for r in rows))
def run(label,name=None,mutate=None,missing=False):
    fk.PATHS.clear(); fk.PATHS.update(ORIG)
    if name:
        dst=M/(label+'__'+ORIG[name].name)
        if missing: dst=M/'does_not_exist'
        else:
            shutil.copyfile(ORIG[name],dst); mutate(dst)
        fk.PATHS[name]=dst
    try:
        m=fk.finalize(fk.load_bundle())
        r=(m['production_ready'],m['frame_staging_authorized'],m['k1_finalize']['failed'])
    except Exception as e:
        r=('EXC',type(e).__name__,str(e)[:100])
    ok = (name is None and r[0] is True and r[1] is True) or (name is not None and (r[0] is False and r[1] is False or r[0]=='EXC'))
    print(('OK  ' if ok else 'FAIL'),label,r,flush=True)
def edit_json(f):
    def m(p):
        d=json.loads(Path(p).read_text()); f(d); Path(p).write_text(json.dumps(d))
    return m
def edit_jl(f):
    def m(p):
        rows=jl(p); rows=f(rows); wjl(p,rows)
    return m
def setk(d,k,v): d[k]=v; return d
run('baseline')
# verify_mp4
run('mp4_bad','verify_mp4',lambda p:Path(p).write_text(Path(p).read_text().replace('"bad": []','"bad": ["x"]')))
run('mp4_137','verify_mp4',lambda p:Path(p).write_text(Path(p).read_text().replace('"checked": 138','"checked": 137')))
run('mp4_noline','verify_mp4',lambda p:Path(p).write_text('\n'.join(l for l in Path(p).read_text().splitlines() if 'checked' not in l)))
run('mp4_missing','verify_mp4',missing=True)
run('mp4_conflict','verify_mp4',lambda p:Path(p).write_text(Path(p).read_text()+'\n{"checked": 138, "bad": ["y"]}\n'))
# wd / wa
for n in ('wd','wa'):
    run(n+'_droprow',n,edit_jl(lambda r:r[1:]))
    run(n+'_duprow',n,edit_jl(lambda r:r+[r[0]]))
    run(n+'_error',n,edit_jl(lambda r:[setk(r[0],'error','boom')]+r[1:]))
    run(n+'_miss',n,edit_jl(lambda r:[setk(r[0],'misses',[5])]+r[1:]))
    run(n+'_wrongtoken',n,edit_jl(lambda r:[setk(r[0],'s','vXXXXXXXXXXXX')]+r[1:]))
    run(n+'_missing',n,missing=True)
# parity
run('par_nfail1','parity',edit_json(lambda d:d.update(n_failures=1)))
run('par_passfalse','parity',edit_json(lambda d:d.update(pass_=False)))
run('par_failrow','parity',edit_json(lambda d:d.update(failures=[{'x':1}])))
def wrongsha(d):
    k=next(iter(d['new'])); d['new'][k][0]['sha256']='0'*64
run('par_wrongsha','parity',edit_json(wrongsha))
run('par_extra_key','parity',edit_json(lambda d:d.update(note='x')))
def droprow(d):
    k=next(iter(d['new'])); d['new'][k]=d['new'][k][1:]
run('par_droprow','parity',edit_json(droprow))
run('par_missing','parity',missing=True)
# substitutions
run('sub_droprow','substitutions',edit_jl(lambda r:r[1:]))
def sub_wrongsha(r):
    r[0]['frames'][0][1]='0'*64; return r
run('sub_wrongsha','substitutions',edit_jl(sub_wrongsha))
def sub_dropframe(r):
    r[0]['frames']=r[0]['frames'][1:]; return r
run('sub_dropframe','substitutions',edit_jl(sub_dropframe))
def sub_wrongidx(r):
    r[0]['frames'][0][0]=r[0]['frames'][0][0]+1; return r
run('sub_wrongidx','substitutions',edit_jl(sub_wrongidx))
run('sub_kind','substitutions',edit_jl(lambda r:[setk(r[0],'substitution','other')]+r[1:]))
run('sub_missing','substitutions',missing=True)
# accept
run('acc_bad','accept',edit_json(lambda d:d.update(bad=['x'])))
run('acc_pinned','accept',edit_json(lambda d:d.update(pinned_ok=14303)))
run('acc_anchors','accept',edit_json(lambda d:d.update(anchors_ok=299)))
run('acc_missing','accept',missing=True)
# token map
run('tok_dropcanon','tokens',edit_jl(lambda r:[x for x in r if x['canonical']!=r[0]['canonical']]))
