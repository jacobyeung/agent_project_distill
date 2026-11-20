"""Retain the fixed train sample's original S4/G1 tables as labelled diagnostics."""
import gzip,json
import serving_reference as R

def main():
    sample=json.loads(R.read(R.OUT/'REPLAY_SAMPLE.json'))['captures']
    manifest=json.loads(R.read(R.ROOT/'train_manifest.json'));train={c['canonical'] for c in manifest['captures']}
    common=dict(R.PINS);dest=R.OUT/'diagnostic_S4_G1';dest.mkdir(exist_ok=True)
    for canonical in sample:
        assert canonical in train
        R.PINS.clear();R.PINS.update(common)
        source=R.SEL/'data/caps_iso'/(canonical.replace('/','__')+'.json.gz')
        rec=json.loads(gzip.decompress(R.read(source)));assert rec['capture']==canonical
        rec.update(role='ORIGINAL S4/G1 LABELLED DIAGNOSTIC ONLY; not a serving reference or oracle label source',split='train',input_sha256=dict(R.PINS))
        with gzip.open(dest/source.name,'wt') as f:json.dump(rec,f,allow_nan=False)
    print('Preserved',len(sample),'original training tables as S4/G1 diagnostics')

if __name__=='__main__':main()
