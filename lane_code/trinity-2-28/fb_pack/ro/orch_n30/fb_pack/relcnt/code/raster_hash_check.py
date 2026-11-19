from common import *
def main():
 census=load(BASE/'in/CENSUS.json');previous=load(BASE/'out/CHECKS.json');rs=list(rows(ROOT/'out/relative_count.jsonl'))
 used={r['provenance']['raster']:r['provenance']['raster_sha256'] for r in rs};matched=[]
 for name,want in sorted(used.items()):
  fact=census['facts'][name];assert fact['sha256']==want
  p=Path(fact['path']);assert previous['input_sha256'][str(p)]==want
  actual=pin(p);assert actual['sha256']==want
  matched.append(dict(raster=name,**actual))
 for r in rs:
  pv=r['provenance'];f=census['facts'][pv['raster']];assert pv['input_sha256'][f['path']]==f['sha256']
 code_pins()
 result=dict(status='PASS',input_sha256=PINS,rows=len(rs),byte_matched_rasters=len(matched),rasters=matched,scope='Fresh SHA-256 verification of every selected local GT raster against b12 row provenance, census, and the existing independently recomputed raster audit. This stage checks bytes, not fresh raster arithmetic.',command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python code/raster_hash_check.py')
 dump(ROOT/'out/RASTER_CHECK.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','rasters')}))
if __name__=='__main__':main()
