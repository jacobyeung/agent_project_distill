"""Verify reference pins and the edit-distance implementation on CPU."""
import ctypes,random,hashlib,json,sqlite3
from pathlib import Path
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    lib=ctypes.CDLL(str(Path('edit_distance.so').resolve()));lib.nearest.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_int];lib.nearest.restype=ctypes.c_double
    rng=random.Random(19)
    def lev(a,b):
        v=list(range(len(b)+1))
        for i,x in enumerate(a,1):
            w=[i]
            for j,y in enumerate(b,1):w.append(min(w[-1]+1,v[j]+1,v[j-1]+(x!=y)))
            v=w
        return v[-1]/max(len(a),len(b)) if a or b else 0
    for _ in range(100):
        a=''.join(rng.choices('abcdef ',k=rng.randrange(1,550)));bs=[''.join(rng.choices('abcdef ',k=rng.randrange(1,550))) for i in range(5)]
        arr=(ctypes.c_char_p*5)(*[b.encode() for b in bs]);assert abs(lib.nearest(a.encode(),arr,5)-min(lev(a,b) for b in bs))<1e-12
    Path('out/DISTANCE_CHECK.json').write_text(json.dumps(dict(status='PASS',random_cases=100,references_each=5,max_test_length=549,input_sha256={str(Path(p).resolve()):sha(p) for p in ['reference_checks.py','edit_distance.cpp','edit_distance.so']}),indent=1)+'\n')
    store=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite');h=sha(store)
    assert h=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
    refs=[Path('inputs')/p for p in ['B12_COUNT_APPEARANCE_ROWS_20261116.md','R1_M200_TRACE_ANALYSIS_20261119.md','coverage_rows_v2.py','check_cov_v2.py','procedure_sources.jsonl','scorer/h1read7/kit/reader/x7.py','scorer/h1read7/kit/reader/evaluator/evalpath/official.py']]
    Path('out/REFERENCE_INPUTS.json').write_text(json.dumps(dict(input_sha256={str(store):h,**{str(x.resolve()):sha(x) for x in refs},str(Path(__file__).resolve()):sha(__file__)},store_verified=True,scorer='x7.compact carries subtype as count_kind; official.OFFICIAL_NA_TYPES includes object_counting and _parse_numeric_v1 requires one finite number.'),indent=1)+'\n')
    p=Path('inputs/b12/out/PACKET_b12_v4/rows.sqlite');c=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True)
    available={p.name for p in Path('inputs/b12/work/rasters').rglob('*.npz')};missing={}
    for (s,) in c.execute('select row from rows'):
        r=json.loads(s)
        if r['question_type']=='object_counting' and r['provenance']['raster'] not in available:missing[r['provenance']['canonical']]=str((Path('inputs/b12/work/rasters')/r['provenance']['raster']).resolve())
    Path('out/MISSING_RASTERS.json').write_text(json.dumps(dict(status='MISSING',input_sha256={str(p.resolve()):sha(p),str(Path(__file__).resolve()):sha(__file__)},expected_raster_root='inputs/b12/work/rasters (recursive basename index)',excluded_scenes=missing,n_scenes=len(missing)),indent=1)+'\n')
    assert len(missing)==json.load(open('inputs/inventory.json'))['counts']['missing_raster']
    print('PASS: distance, store pin, scorer references; missing raster scenes',len(missing))
if __name__=='__main__':main()
