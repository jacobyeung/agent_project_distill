import base64,hashlib,json,sys,os,time
from pathlib import Path
from copy import deepcopy
S=Path(sys.argv[1]);KIT=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/restage_r1c')
sys.path.insert(0,str(S/'s'))
def read(p):
    v=json.loads(p.read_text());r=base64.b64decode(v['payload'],validate=True);return json.loads(r)
from launch_r1 import entry
cfg=read(KIT/'k/c.json');h=read(KIT/'k/h.json');out={}
base=Path('/tmp')/('jjyeung_rvn5b_'+str(int(time.time())));base.mkdir(mode=0o700)
def run(name,fn):
    try:r=fn();out[name]=('RESULT',r.get('status'),r.get('blockers',r.get('errors')),r.get('assertions')) if isinstance(r,dict) else ('RETURN',str(r))
    except Exception as e:out[name]='REFUSED '+type(e).__name__+': '+str(e)[:150]
    print(name,'=>',out[name],flush=True)
def fh(jt,token,c=cfg,req=None,root=None):
    q=deepcopy(h if req is None else req);q['job_tmp']=str(jt)
    return entry.frame_host(c,root or jt/'p',q,job_tmp_token=token)
a=base/'a';t=entry.create_job_tmp(a);run('fresh_token',lambda:fh(a,t))
run('token_reuse',lambda:fh(a,t))
b=base/'b';b.mkdir();run('existing_dir_no_token',lambda:fh(b,None))
c=base/'c';tc=entry.create_job_tmp(c);d=base/'d';d.mkdir(mode=0o700);run('token_for_c_used_on_d',lambda:fh(d,tc))
e=base/'e';te=entry.create_job_tmp(e);os.chmod(e,0o755);run('mode_0755_after_create',lambda:fh(e,te))
f=base/'f';tf=entry.create_job_tmp(f);os.rename(f,base/'f_old');f.mkdir(mode=0o700);run('dir_replaced_same_path',lambda:fh(f,tf))
g=base/'g';tg=entry.create_job_tmp(g);bad=deepcopy(cfg);bad['extra_input']='/home/jjyeung/x';run('cfg_abs_path_outside',lambda:fh(g,tg,c=bad))
g2=base/'g2';tg2=entry.create_job_tmp(g2);lnk=g2/'lnk';lnk.symlink_to('/home');bad=deepcopy(cfg);bad['extra_input']=str(lnk/'x');run('cfg_symlink_inside_to_outside',lambda:fh(g2,tg2,c=bad))
g3=base/'g3';tg3=entry.create_job_tmp(g3);(g3/'rl').symlink_to('/home');bad=deepcopy(cfg);bad['extra_input']='rl/x';run('cfg_relative_via_symlink_outside',lambda:fh(g3,tg3,c=bad))
i=base/'i';ti=entry.create_job_tmp(i);run('root_outside_job_tmp',lambda:fh(i,ti,root=base/'elsewhere'))
j=base/'j';tj=entry.create_job_tmp(j);rq=deepcopy(h);rq['staging']='/data2/x';run('request_path_outside',lambda:fh(j,tj,req=rq))
k=base/'k';tk=entry.create_job_tmp(k);(k/'pre').write_text('x');run('job_tmp_nonempty_with_token',lambda:fh(k,tk))
g4=base/'g4';tg4=entry.create_job_tmp(g4);(g4/'b').symlink_to('/home');(g4/'a').symlink_to('b');bad=deepcopy(cfg);bad['extra_input']='a/x';run('cfg_relative_symlink_chain_outside',lambda:fh(g4,tg4,c=bad))
g5=base/'g5';tg5=entry.create_job_tmp(g5);(g5/'d').mkdir();bad=deepcopy(cfg);bad['extra_input']='d/x';run('cfg_relative_inside_nonempty_dir',lambda:fh(g5,tg5,c=bad))
k2=base/'k2';tk2=entry.create_job_tmp(k2);(k2/'.hidden').write_text('x');run('job_tmp_nonempty_hidden_file',lambda:fh(k2,tk2))
k3=base/'k3';tk3=entry.create_job_tmp(k3);(k3/'sub').mkdir();run('job_tmp_nonempty_empty_subdir',lambda:fh(k3,tk3))
run('job_tmp_slash_tmp',lambda:entry.create_job_tmp('/tmp'))
run('job_tmp_outside_tmp',lambda:entry.create_job_tmp('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/jt'))
out['env_after']={n:os.environ.get(n) for n in ('TMPDIR','XDG_CACHE_HOME','HF_HOME')};out['cwd_after']=os.getcwd()
out['abs_paths_in_kit_cfg']=sorted({v for v in json.dumps(cfg).split('"') if v.startswith('/')})[:20]
out['abs_paths_in_h']=sorted({v for v in json.dumps(h).split('"') if v.startswith('/')})[:20]
out['h_keys']=sorted(h)
print(json.dumps(out,indent=1,default=str));Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/N5.json').write_text(json.dumps(dict(out,base=str(base)),indent=1,default=str))
