<!-- recovered by seal_plan: transcript=71f94277 line=26139 utc=2026-11-13T22:52:36.247Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/leg_s1_tree; sha256sum $C/out/WARM_START_REVIEW2_FIXES_07ca49df.patch $C/out/DONOR_ROW_ORDER_ATTESTATION_07ca49df.json | cut -c1-16,65-; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,sys
v=json.load(open('$C/out/DONOR_ROW_ORDER_ATTESTATION_07ca49df.json'))
print(sorted(v)); print(v.get('scanner_source_sha256','')[:16]); print({k:(x if k=='path' else x[:12]) for k,x in v['config'].items()}); print(sorted(v['preparation'])); print([(s['name'],s['count'],s['sha256'][:8]) for s in v['rows']['streams']], v['rows']['sha256'][:8])
"; cat $C/out/WARM_START_REVIEW2_FIXES_07ca49df.json | cut -c1-1500