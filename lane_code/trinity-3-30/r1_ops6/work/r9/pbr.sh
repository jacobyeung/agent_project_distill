export TZ=UTC; O=/project/community/jjyeung/okh7/pb_61e5cf9d
python3 -c "
import json;r=json.load(open('$O/pb_report.json'));print(json.dumps({k:(round(v['minutes'],2)) for k,v in r['phases'].items()}));print({k:r[k] for k in r if k not in ('phases','files')})
h=json.load(open('$O/h.json'));print('h',h['schema'],h['step'],h['job_id'],h['trainer_commit'],len(h['pins']),sorted(h['pins'])[:4])"
sha256sum $O/*; cat $O/RP.json
sacct -n -j 173049 -o JobID,State,ExitCode,Elapsed,MaxRSS,MaxDiskRead,NodeList
