from pathlib import Path
import ast,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
rows=[
 dict(write='Python import bytecode, including isolated-mode staging imports',destination='Disabled by -B at every shell/direct/distributed Python start; PYTHONDONTWRITEBYTECODE=1 also inherited',evidence=['runtime.py','STARTS_q.json','STARTS_n.json','BEFORE.json','SEQUENCE.json']),
 dict(write='Scheduler stdout/stderr; otherwise relative to submission directory',destination='/tmp/q_%j.log and /tmp/q_%j.err',evidence=['kits/q/job.sh','kits/n/job.sh']),
 dict(write='Relative runtime files and library-generated files',destination='job.sh changes cwd to node-local $N; j.sh changes cwd to $Q_ROOT; f.sh uses the separate node-local proof sibling',evidence=['runtime.py:local_env']),
 dict(write='Temporary files and caches',destination='TMPDIR, XDG_CACHE_HOME, HF_HOME, TORCH_HOME, TRITON_CACHE_DIR, CUDA_CACHE_PATH and MPLCONFIGDIR below job-local directories',evidence=['runtime.py:local_env','decoded j.sh tk_env']),
 dict(write='Decoded j.sh, staged P helper tree, payload/config/request/export files',destination='$Q_ROOT/{j.sh,h,u,w,n.json,r.json,e,c.json,t.tar}',evidence=['b/z.py:bootstrap','b/z.py:stage_payload']),
 dict(write='Stage locks, stamps, extracted environments, shebang rewrites, overlays, frame/model/init files',destination='$Q_ROOT/{s,x,rp,h,j}; /tmp/jjyeung is only a node-local directory',evidence=['decoded j.sh tk_stage/tk_nx/tk_venv_shebangs']),
 dict(write='Step log, proof/room/training logs, capture args, extracted sealed source and proof outputs',destination='$Q_ROOT/h/o; $Q_ROOT/{q.log,rooms.log,t.log,args.json,p,rooms.json}',evidence=['decoded j.sh','b/a.py','b/w.py','b/d.py']),
 dict(write='Result archive and RESULT.json',destination='Created below $Q_ROOT/o; completed deliverables copied to the unchanged n_root/o/JOB_ID sibling outside both kits',evidence=['b/o.py']),
 dict(write='Resolver result',destination='Caller supplies a path outside the kits; operator uses existing n_root/rn.json',evidence=['b/resolve.py','OPERATOR_24C.md']),
]
J.write(D/'WRITE_AUDIT.json',dict(status='PASS',tree_changed=False,rows=rows,scope='Kit-owned helpers and emitted programs; production GPU/model internals not executed. Strict file-set verification remains unchanged; existing unlisted files still refuse.'))
changed={}
for name in ('q','n'):
 k=L/'work/build24/kits'/name;old=L/'attic/build24c'/('kit_'+name)
 before={str(p.relative_to(old)):J.sha(p) for p in old.rglob('*') if p.is_file()};after={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
 changed[name]={n:dict(before=before.get(n),after=h) for n,h in after.items() if before.get(n)!=h}
 assert set(before)<=set(after)
J.write(D/'FINAL_CHANGES.json',changed)
packages={p.name:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for p in (L/'out').glob('tree_rebuild_*.tar')}
assert packages['tree_rebuild_b24b_7d7a8858.tar']['sha256']=='4bfb9f759f505276cc908be8885942822edb53b7c048adda0e6ae1c171366f01'
assert packages['tree_rebuild_b24_90637cdf.tar']['sha256']=='239a6d2b3ea00f1bce309a11d1082a0b186e465da43f4bb333ba0b3884435654'
J.write(D/'BASELINE_UNCHANGED.json',dict(status='PASS',packages=packages,tree_sha256=J.load(L/'out/TREE_SEAL.json')['tree_sha256']))
