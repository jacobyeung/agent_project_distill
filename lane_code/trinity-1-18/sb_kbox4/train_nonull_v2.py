"""Five room-grouped OOF fits on freshly rebuilt serving-geometry labels."""
import gzip,json,time
import torch
from safetensors.torch import save_file
import serving_reference as R
import math_v2 as M
from selector_nonull import fit

def main():
    torch.set_num_threads(8);start=time.monotonic()
    assert json.loads(R.read(R.ROOT/'out/DRYRUN.json'))['passed']
    frozen=json.loads(R.read(R.OUT/'FREEZE.json'))
    manifest=json.loads(R.read(R.ROOT/'pinned_train.json'))
    rowids=set(R.read(R.ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines())
    caps=[c for c in manifest['captures'] if any(r['id'] in rowids for r in c['rows'])]
    folds=M.folds(c['room'] for c in caps)
    config=json.loads(R.read(R.SEL/'work/run_iso/selector_head.json'))['config'];groups=[]
    for c in caps:
        rec=json.loads(gzip.decompress(R.read(R.TABLES/(c['canonical'].replace('/','__')+'.json.gz'))))
        R.PINS.update(rec['input_sha256']);lab={(r['name'],r['candidate_id']):r['y'] for r in rec['rows']}
        for name in sorted({i['name'] for i in rec['inputs']}):
            rows=[i for i in rec['inputs'] if i['name']==name]
            groups.append(dict(object_id=c['canonical']+'::'+name,name=name,room=c['room'],split='train',
                x=[i['x'] for i in rows],y=[lab[(name,i['candidate_id'])] for i in rows],candidate_ids=[i['candidate_id'] for i in rows]))
    out=R.OUT/'nonull';out.mkdir(exist_ok=True);choices={};records=[]
    R.code_pins()
    for fold in range(5):
        t=time.monotonic();training=[g for g in groups if folds[g['room']]!=fold];test=[g for g in groups if folds[g['room']]==fold]
        assert not ({g['room'] for g in training}&{g['room'] for g in test})
        head=fit(training,config)
        with torch.no_grad():
            for g in test:
                k=int(torch.argmax(head(torch.tensor(g['x'],dtype=torch.float64),None,g['name'])))
                choices[g['object_id']]=g['candidate_ids'][k]
        path=out/f'fold_{fold}.safetensors';save_file({k:v.contiguous() for k,v in head.state_dict().items()},str(path));R.read(path)
        records.append(dict(fold=fold,train_objects=len(training),positive_train_objects=sum(any(g['y']) for g in training),test_objects=len(test),seconds=time.monotonic()-t))
        print(json.dumps(records[-1]),flush=True)
    R.write(out/'TRAIN_OOF.json',dict(config=config,seed=20261116,folds=folds,oof_choices=choices,records=records,
        target='candidate cross entropy; uniform positive mass; zero-positive objects excluded from fit; no null slot',
        local_fold_weights_only=True,deployed_export_created=False,seconds=time.monotonic()-start))
    (R.ROOT/'STATUS.md').write_text('Five non-null selector fits and OOF choices are complete on rebuilt serving labels. No fold trained on a test room. No deployed export was created. Dependent training arms remain; held-out and A6 stay deferred.\n')

if __name__=='__main__':main()
