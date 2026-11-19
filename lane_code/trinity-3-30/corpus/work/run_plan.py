import json,subprocess,sys
plan=json.load(open('work/INGEST_PLAN.json'))
only=set(sys.argv[1:])
for p in plan:
    if only and p['read_id'] not in only: continue
    cmd=['python3','tool/ingest_read.py','ingest','--source',p['source'],'--read-id',p['read_id'],'--meta','work/meta/%s.json'%p['read_id'],'--out','stage','--format',p['format']]
    if p.get('inputs'): cmd+=['--inputs',p['inputs']]
    if p.get('partial'): cmd+=['--archive-partial']
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
    print(p['read_id'], 'rc=%d'%r.returncode, r.stdout.strip().splitlines()[-1][:400] if r.stdout.strip() else '', flush=True)
