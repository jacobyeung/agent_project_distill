from common import *
from copy import deepcopy
track(__file__)
f=P.load(track(W/'work/native_fixture/FIXTURE.json'));cfg=P.load(track(f['native_config']['path']));receipt=P.load(track(f['prepared_receipt']['path']))
root=W/'work/mix_fixture';root.mkdir(exist_ok=True);scope='FIXTURE_ONLY_NOT_PRODUCTION'
def put(name,v):
 p=write('work/mix_fixture/'+name,dict(v,scope=scope));return P.file_pin(p)
old=receipt['streams']['pose'];n=old['count'];source=dict(kind='rows',database=old['database'],receipt=old['receipt'],count=n//2)
track(old['database']['path'],old['database']['sha256'])
order=[[i%2,i] for i in range(n)];p=root/'pose_order.json';p.write_text(P.encoded(order)+'\n');orderpin=P.file_pin(p);track(p)
pose_receipt=put('pose_receipt.json',dict(schema='c1-pose-mix-v1',sources=[dict(kind='rows',receipt=old['receipt'],frame_prefix=None)]*2))
# The two synthetic source slots reference disjoint even/odd rows of a single fixture database.
stream=dict(kind='mix',sources=[deepcopy(source),deepcopy(source)],count=n,receipt=pose_receipt,order=orderpin)
stream['reader_source']=deepcopy(stream)
receipt['streams']['pose']=stream;receipt['depth']=dict(num_points_per_frame=1)
for s,v in receipt['streams'].items():
 if s!='pose':v['reader_source']=deepcopy(v)
receiptpin=put('receipt.json',receipt);cfg['preparation']=receiptpin;cfg['streams']['pose']=pose_receipt
configpin=put('config.json',cfg);f.update(native_config=configpin,prepared_receipt=receiptpin);f['stream_receipts']['pose']=pose_receipt;f['offset_tables']['pose']=orderpin
put('FIXTURE.json',f)
print('Mix/order fixture ready')
