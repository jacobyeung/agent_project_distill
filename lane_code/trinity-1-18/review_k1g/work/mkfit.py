import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/kc/k1_build/work/kit_k1a/work')
import gt_set as G
F='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/tests_8cc4f9ec/'
sha=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()
tab,out,meta_from=sys.argv[1],sys.argv[2],sys.argv[3]
t=json.load(open(tab+'/TABLE_RECEIPT.json'));mt=json.load(open(meta_from+'/TABLE_RECEIPT.json'))['gt_set'] if meta_from!='none' else None
fit=dict(fixture_only=False,metrics={'accept':{'refit':{'auc':.8,'top1_accept_accuracy':.8},'current':{'auc':.8,'top1_accept_accuracy':.8}}},
 inputs={str(Path(tab).resolve()/n):sha(tab+'/'+n) for n in ['candidates.jsonl','pairs.jsonl']}|{F+'inventory.json':sha(F+'inventory.json')},
 table_receipt=G.pin(tab+'/TABLE_RECEIPT.json'))
if mt is None:fit.pop('table_receipt');json.dump(fit,open(out,'w'),indent=2)
else:G.write(out,fit,mt)
