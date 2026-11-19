1. **[README.md:12](/scratch/jjyeung/orch_n30/r1_ops6/work/pb/README.md:12), line 24 — submission does not supply the script.** `/dev/stdin` receives no `pbjob.sh` bytes. Replace the two commands with:
   ```bash
   job=$(bash "$OSSH" "sbatch --parsable --job-name=a15_cot_ap${token} --time=04:00:00 /dev/stdin 673bc60f 200 /project/community/jjyeung/okh7/pb_${token} 13800" < pbjob.sh)
   job=$(bash "$OSSH" "test ! -e /project/community/jjyeung/okh7/h_6ed2c7aa/m600/DONE.json && sbatch --parsable --job-name=a15_cot_ap${token} --time=04:00:00 /dev/stdin 6ed2c7aa 600 /project/community/jjyeung/okh7/pb_${token} 13800" < pbjob.sh)
   ```

2. **[pbjob.sh:235](/scratch/jjyeung/orch_n30/r1_ops6/work/pb/pbjob.sh:235) — receipt namespace cannot create missing mount points beneath read-only mounts.** Unlike `hr2.sh:54–63`, it binds `/` read-only. Additionally, staged `u` lacks `ap/8865619b`, and staged `x` lacks `runs`; mounting these parents read-only prevents creating the next destinations. Before constructing `ns`, add:
   ```python
   (nl/'u/ap/8865619b').mkdir(parents=True, exist_ok=True)
   (nl/'x/runs').mkdir(parents=True, exist_ok=True)
   root_args=[]
   for entry in Path('/').iterdir():
       if entry.name in {'home','dev','proc','scratch','lustre','w'}: continue
       if entry.is_symlink():
           root_args += ['--symlink',os.readlink(entry),str(entry)]
       else:
           root_args += ['--ro-bind',str(entry),str(entry)]
   ```
   In **`ns` only**, replace `'--ro-bind','/','/'` with `*root_args`. This retains bwrap’s private root for new destinations and preserves the public pin paths.

3. **[pbjob.sh:249](/scratch/jjyeung/orch_n30/r1_ops6/work/pb/pbjob.sh:249) — the wrapper does not time every receipt hash.** It captures file hashes through `pinned()` and `file_pin()`, but `r1_handover.py:151` calls `digest()`, which directly invokes `hashlib.sha256` at `p3_provenance.py:20`. Replace wrapper lines 249–255 with:
   ```python
   elapsed=0.; count=0
   def timed(fn):
       def measured(*args, **kwargs):
           global elapsed,count
           t=time.monotonic()
           try:return fn(*args, **kwargs)
           finally:elapsed+=time.monotonic()-t;count+=1
       return measured
   p.sha256=timed(p.sha256)
   p.digest=timed(p.digest)
   ```

4. **[pbjob.sh:273](/scratch/jjyeung/orch_n30/r1_ops6/work/pb/pbjob.sh:273) — `stage_minutes` understates preparation before receipt hashing.** It excludes archive verification, extraction and view construction, although these must finish before hashing starts. Retain the individual phase measurements and replace the aggregate with:
   ```python
   report['stage_minutes']=sum(report['phases'].get(k,{}).get('minutes',0) for k in ('preflight','stage','verify','extract','closure','view'))
   ```

5. **[pbjob.sh:70](/scratch/jjyeung/orch_n30/r1_ops6/work/pb/pbjob.sh:70) — a missing parent causes an out-of-scope write.** `nl.parent.mkdir()` creates `/tmp/jjyeung`, outside the permitted `/tmp/jjyeung/pb_<jobid>` tree. Replace it with the following prerequisite; the job environment must already provide that parent:
   ```python
   require(nl.parent.is_dir(),'TMP_PARENT_MISSING')
   ```

**NO-GO**