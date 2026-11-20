cd /tmp && umask 077
export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
P=sj/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot
timeout 600 gcloud storage cat 'gs://cmu-gpucloud-jjyeung/q8/b7e31d84a90c62f5/d6e92a81.tar#1794820770137604' | /usr/bin/python3 -c "
import sys,tarfile,io,base64,gzip,hashlib
want={'$P/'+n for n in ('decoupled_v.py','point_depth_head.py','carrier_c1.py','carrier_c1_decode.py','p3_heads.py','decoupled_vc.py','tower_read.py','ground_context.py','p3_provenance.py','carrier_c1_run.py')}
out=io.BytesIO();w=tarfile.open(fileobj=out,mode='w:gz')
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as a:
  for it in a:
    if it.name in want:
      raw=a.extractfile(it).read();ti=tarfile.TarInfo(it.name.split('/')[-1]);ti.size=len(raw);w.addfile(ti,io.BytesIO(raw));print('GOT',it.name.split('/')[-1],hashlib.sha256(raw).hexdigest(),file=sys.stderr)
w.close();print('B64BEGIN');print(base64.b64encode(out.getvalue()).decode());print('B64END')
"
TZ=UTC squeue -w orchard-community-1 -o '%i %j %u %T %M %l %b %P' ; scontrol show node orchard-community-1 | grep -E 'Gres|AllocTRES|CfgTRES'
