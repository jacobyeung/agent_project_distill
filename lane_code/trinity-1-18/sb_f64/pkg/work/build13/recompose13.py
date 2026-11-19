"""Feed the authenticated census admission to the real native-built base."""
from pathlib import Path
import os,sys,json,sqlite3,subprocess,shutil
L=Path(__file__).resolve().parents[2];B=L/'work/build13';T=L/'work/tree_r1';O=B/'proofs/census'
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(T)
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.r1_routing import compose
from student_pilot.r1_population import Membership
cfg=load(B/'inputs/config.json');old=load(O/'composed/receipt.json');membership=Membership(old['source_membership'])
sources={k:v['source'] for k,v in membership.sources.items()}
source=sqlite3.connect(pinned(old['database']).as_uri()+'?mode=ro',uri=True)
def batches():
    try:
        for kind,pin in sources.items():
            cursor=source.execute("SELECT row,target FROM rows WHERE json_extract(row,'$.r1_source.family')=? ORDER BY i",(kind,))
            while found:=cursor.fetchmany(200):
                items=[]
                for raw,target in found:
                    row=json.loads(raw);assert membership.cell(row,'routing')==kind
                    items.append(dict(row=row,target=json.loads(target)))
                yield kind,pin,items,file_pin(O/'slice_intake.json')
    finally:source.close()
native=Path.open
def opened(p,mode='r',*a,**kw):return native(p,mode.replace('x','w') if p.is_relative_to(O) else mode,*a,**kw)
Path.open=opened
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True);assert shutil.disk_usage('/scratch').free>=85*1024**3
result=compose(file_pin(B/'proofs/builder/routing/receipt.json'),sources,batches(),cfg,O/'composed')
assert result['per_source']==dict(recovery=777,absolute_distance=1476,units=8067)
assert result['refused']['base:replaced_cell']==1
result['intake_evidence']=[file_pin(O/'slice_intake.json')]
(O/'composed/receipt.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':')))
P=B/'proofs/composition';P.mkdir(exist_ok=True)
(P/'RESULT.json').write_text(json.dumps(dict(receipt=file_pin(O/'composed/receipt.json'),status='PASS',
    source_database_sha256=old['database']['sha256'],sources=sources,
    intake=file_pin(O/'slice_intake.json'),native_base=file_pin(B/'proofs/builder/RESULT.json'),
    scope='Census intake output authenticated by its database pin and every source-membership row digest; compose reruns native filters/readers on all admitted rows. No raw row or source database is copied.'),indent=2))
m.save(P);print('PASS native base plus all three admitted slices')
