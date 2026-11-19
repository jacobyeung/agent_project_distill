from common import *
from student_pilot.r1_handover import stream_identity
track(__file__);cfg=config();receipts={};expected={
 'routing':'4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84',
 'pointing':'c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938',
 'pose':'6d591440','vqa':'210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'}
for name,pin in cfg['streams'].items():
 try:
  path=resolve(pin);r=P.load(path);identity=stream_identity(r,name)
  item=dict(receipt=pin,resolved=str(path),identity=identity,expected=expected[name],identity_check='PASS' if identity.startswith(expected[name]) else 'MISMATCH',count=r.get('count'),schema=r.get('schema'),missing=[])
  def visit(v,field):
   if isinstance(v,dict):
    if 'path' in v and 'sha256' in v:
     if not any(word in field for word in ('database','receipt','order','indices','clips_plan','dense_plan')):return
     try:resolve(v)
     except (FileNotFoundError,ValueError) as e:item['missing'].append(dict(field=field,pin=v,error=str(e)))
    else:
     for k,x in v.items():visit(x,field+'.'+k)
   elif isinstance(v,list):
    for i,x in enumerate(v):visit(x,field+'.'+str(i))
  visit(r,'stream')
  if name=='pose':
   item['sources']=r['sources'];item['source_stores']=[]
   for source in r['sources']:
    child=P.load(resolve(source['receipt']));entry=dict(receipt=source['receipt'],database=child['database'],count=child['count'])
    try:entry.update(status='PASS',resolved=str(resolve(child['database'])))
    except (FileNotFoundError,ValueError) as error:
     entry.update(status='MISSING',error=str(error));item['missing'].append(dict(field='pose.source.database',pin=child['database'],error=str(error)))
    item['source_stores'].append(entry)
  receipts[name]=item
 except (FileNotFoundError,ValueError) as e:receipts[name]=dict(status='MISSING',receipt=pin,error=str(e))
vqa=cfg['r1_training']['direction_twins']['source_database'];p=resolve(vqa)
import sqlite3
con=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True);count=con.execute('SELECT COUNT(*) FROM rows').fetchone()[0];con.close()
mirror_receipt=RO/'n30_mirror/rows_r1/out/a2_vqa_v7/vqa/receipt.json';track(mirror_receipt);mr=P.load(mirror_receipt)
receipts['vqa'].update(source_database=vqa,source_bytes_check='PASS',source_count=count,mirror_receipt=dict(path=str(mirror_receipt),sha256=P.sha256(mirror_receipt)),mirror_receipt_count=mr['count'],count_check='PASS' if count==mr['count'] else 'MISMATCH',mirror_receipt_launch_hash_check='PASS' if P.sha256(mirror_receipt)==cfg['streams']['vqa']['sha256'] else 'MISMATCH')
# Search only the already bounded local database inventory, never the training host or NFS.
inventory=track(W/'work/local_store_paths.txt');candidates=[]
for name in inventory.read_text().splitlines():
 p=Path(name)
 if p.suffix not in ('.sqlite','.db'):continue
 h=P.sha256(p);candidates.append(dict(path=name,sha256=h,bytes=p.stat().st_size))
found={k:[v for v in candidates if v['sha256']==h] for k,h in expected.items() if k!='pose'}
write('out/STORE_AUDIT.json',dict(streams=receipts,matching_local_databases=found,local_database_inventory=candidates,inputs_scope='Pinned receipt identities and exact local database bytes; absent native stores cannot establish final populations.'))
print({k:dict(identity=v.get('identity'),check=v.get('identity_check'),count=v.get('count'),missing=len(v.get('missing',[]))) for k,v in receipts.items()})
print('matching stores',{k:len(v) for k,v in found.items()})
