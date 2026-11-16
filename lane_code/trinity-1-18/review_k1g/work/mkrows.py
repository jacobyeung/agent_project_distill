import json,sys
F='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/tests_8cc4f9ec/'
m=json.load(open(F+'manifest.json'));keep=sys.argv[1].split(',');out=sys.argv[2];extra=sys.argv[3] if len(sys.argv)>3 else ''
rows=[dict(id=r['id'],canonical=c['canonical'],type=r['type'],gt_value=r['gt_value'],pred=r['gt_value']*1.1,label='trust',printed_cues={'status':0},training_target_available=True) for c in m['captures'] for r in c['rows'] if c['canonical'] in keep]
if extra=='drop':rows=rows[:-1]
if extra=='mislabel':rows[0]['canonical']=[c['canonical'] for c in m['captures'] if c['canonical'] not in keep][0]
open(out,'w').write(''.join(json.dumps(r)+'\n' for r in rows))
