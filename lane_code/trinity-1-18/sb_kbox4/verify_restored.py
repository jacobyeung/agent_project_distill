"""Direct R1 socket equivalence on the two convert-refused training captures."""
import json,re
import torch
import serving_reference as R
from e2e_reader.grounding import StageOneSocket,ground_session

def main():
    torch.set_num_threads(8)
    manifest=json.loads(R.read(R.ROOT/'pinned_train.json'))
    ids=set(R.read(R.ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines())
    directory=R.SEL/'work/run_iso'
    for ext in ['json','safetensors']:R.read(directory/f'selector_head.{ext}')
    head,_=R.load_head(directory);checks=[]
    for c in manifest['captures']:
        if c['canonical'] not in ['scannetpp/0f69aefe3d','scannetpp/2c7c10379b']:continue
        assert c['k1_split']=='train'
        geo,cache,meta,_,_=R.geometry(c);assert meta['reviewed_guard_refused']
        base=json.loads(R.read(R.OUT/'base'/(c['canonical'].replace('/','__')+'.json')))
        expected={r['row_id']:r for r in base['items'] if r['arm']=='A0_deployed'}
        stage=R.StageOne(R.cache_detect(cache),head,geo,rule='candidates_argmax')
        session=ground_session(geo,StageOneSocket(stage.propose,stage.select,(240,320),32))
        for row in c['rows']:
            if row['id'] not in ids:continue
            for name in row['operands']:session.execute(f'<ground obj="{name}" mode="box">')
            a,b=row['operands'];response=session.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
            m=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',response);pred=float(m[1]) if m else None
            e=expected[row['id']]
            checks.append(dict(capture=c['canonical'],row_id=row['id'],response=response,reader_prediction=pred,
                kit_prediction=e['prediction'],passed=pred==e['prediction'],marked=e['reviewed_guard_refused']))
    assert len(checks)==12
    R.code_pins();passed=all(r['passed'] and r['marked'] for r in checks)
    R.write(R.OUT/'RESTORED_CAPTURE_PARITY.json',dict(status='PASS' if passed else 'BLOCKED',checks=checks,
        matched=sum(r['passed'] for r in checks),total=len(checks),answered=sum(r['reader_prediction'] is not None for r in checks)))
    assert passed
    print(json.dumps(dict(passed=passed,rows=len(checks),answered=sum(r['reader_prediction'] is not None for r in checks))))

if __name__=='__main__':main()
