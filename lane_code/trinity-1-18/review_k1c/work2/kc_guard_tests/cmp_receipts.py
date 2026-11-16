import json,sys
def norm(p):
    r=json.load(open(p));r['files']={k:v.get('sha256') for k,v in r['files'].items()};return r
roots=sys.argv[1:]
for k in ('48f3924ccb5dd8b6','54c1c9d606f2a398','dfece798227526fb'):
    rs=[norm(f'{x}/{k}/CACHE_COMPLETE.json') for x in roots]
    print(k,all(r==rs[0] for r in rs),rs[0]['gravity_verdict'],sorted(rs[0]['files']),rs[0].get('geometry_refusal'))
for x in roots: print(x.split('/')[-1],json.load(open(x+'/GUARD_REPORT.json'))['K1']['reviewed_refused_count'],json.load(open(x+'/GUARD_REPORT.json'))['K1']['sealed_refused'],json.load(open(x+'/HALTED.json'))['error'][:60])
