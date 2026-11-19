"""Check fold isolation, pair alignment, frozen weights, coverage and archive integrity."""
import hashlib, json, math, statistics, tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'


def js(path):return json.loads(path.read_text())


def main():
    d=js(OUT/'TRAIN_DATA.json');cv=js(OUT/'CV_FROZEN.json');held=js(OUT/'HELDOUT.json');summary=js(OUT/'SELREFIT.json')
    assert held['frozen_cv_sha256']==hashlib.sha256((OUT/'CV_FROZEN.json').read_bytes()).hexdigest()
    assert cv['frozen_at_utc']<=held['completed_at_utc']
    train_rooms={c['room'] for c in d['captures']};seen={};counts={}
    for name in ['cv_captures','heldout_captures']:
        ids=set();rooms=set();captures=set();gains={k:[] for k in range(5)}
        for p in sorted((OUT/name).glob('*.json')):
            r=js(p);rooms.add(r['room']);captures.add(r['capture'])
            for path,sha in d['input_sha256'].items():
                if path in r['input_sha256']:
                    assert r['input_sha256'][path]==sha,('input_changed',path)
            a,b=r['arms'];assert [a['arm'],b['arm']]==['old','refit']
            aa={v['row_id']:v for v in a['items']};bb={v['row_id']:v for v in b['items']}
            assert aa.keys()==bb.keys() and not (ids & aa.keys());ids.update(aa)
            assert {v['object_id'] for v in a['choices']}=={v['object_id'] for v in b['choices']}
            for rid in aa:
                x,y=aa[rid],bb[rid];assert x['label']==y['label'] and x['room']==y['room']
                if name=='cv_captures':gains[d['folds'][r['room']]].append(y['mra']-x['mra'])
            assert all(v['exact_serving_features'] for arm in r['arms'] for v in arm['checks'])
        if name=='cv_captures':
            assert rooms==train_rooms and len(captures)==239 and len(ids)==1037
            paired=[statistics.mean(gains[k]) for k in range(5)]
            for k,v in enumerate(paired):assert math.isclose(v,cv['folds'][k]['paired_gain'],abs_tol=1e-12)
            assert math.isclose(statistics.mean(paired),cv['mean_paired_gain'],abs_tol=1e-12)
            assert math.isclose(2*statistics.stdev(paired),cv['spread_2sd'],abs_tol=1e-12)
        else:assert not (rooms & train_rooms) and len(captures)==57 and len(ids)==216
        seen[name]=ids;counts[name]=dict(captures=len(captures),rooms=len(rooms),distance_rows=len(ids))
    assert not (seen['cv_captures']&seen['heldout_captures'])
    for stem in ['selector_head_refit']+[f'fold_{k}' for k in range(5)]:
        m=js(OUT/(stem+'.json'));assert m['weights_sha256']==hashlib.sha256((OUT/m['weights_file']).read_bytes()).hexdigest()
    assert summary['weights_sha256']['refit']==cv['final_weights_sha256']
    assert len((OUT/'REPORT.md').read_text().splitlines())<=60
    assert (OUT/'READ_REQUEST.md').exists()==cv['refit_wins']
    archive=OUT/'sb_selrefit.tar';expected=(OUT/'sb_selrefit.tar.sha256').read_text().split()[0]
    with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
    with tarfile.open(archive) as t:
        for member in t:
            if member.isfile():
                archived=hashlib.sha256(t.extractfile(member).read()).hexdigest()
                assert archived==hashlib.sha256((ROOT/member.name).read_bytes()).hexdigest(),member.name
    print(json.dumps(dict(status='PASS',coverage=counts,paired_fold_metrics=True,room_isolation=True,archive_sha256=expected)))


if __name__=='__main__':main()
