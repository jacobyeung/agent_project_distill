"""Apply the pinned N removal and physical-room rules to the recovered extract."""
from camera_contract import *
def main():
 frozen();pin(__file__);pin(ROOT/'camera_contract.py');a=Admission()
 total=Counter();keep=Counter();marginal={t:Counter() for t in TYPES};joint={t:Counter() for t in TYPES};hows=Counter();seen=set();held=set();allq=set();source_questions=set()
 with (OUT/'SOURCE_ADMISSION.jsonl').open('w') as f:
  for x,r in a.scan():
   typ=r['routing']['question_type'];total[typ]+=1
   assert x['i'] not in seen and r['qid'] not in allq
   seen.add(x['i']);allq.add(r['qid'])
   hits,canonical,room,how=a.reasons(r);hows[how]+=1
   if not hits:keep[typ]+=1
   marginal[typ].update(hits);joint[typ]['|'.join(hits) or 'kept']+=1
   source_questions.add(r['student_input']['question'])
   f.write(enc(dict(i=x['i'],qid=r['qid'],type=typ,keep=not hits,reasons=hits,canonical=canonical,room=room,proof=how,row_sha256=hashlib.sha256(x['row'].encode()).hexdigest(),target_sha256=hashlib.sha256(x['target'].encode()).hexdigest()))+'\n')
 assert dict(total)==a.manifest['counts'] and sum(total.values())==35423
 (OUT/'SOURCE_WORDING_CORPUS.txt').write_text('\n'.join(sorted(source_questions))+'\n')
 pin(OUT/'SOURCE_ADMISSION.jsonl');pin(OUT/'SOURCE_WORDING_CORPUS.txt');tree=bind_code()
 save(OUT/'SOURCE_AUDIT.json',dict(status='PASS',command='python -B audit_camera_training.py',tree=str(TREE),tree_sha256=tree,rows=sum(total.values()),total=dict(total),kept=dict(keep),dropped={t:total[t]-keep[t] for t in TYPES},drop_reasons_marginal=marginal,drop_reasons_joint=joint,canonical_proofs=dict(hows),unresolved=0,room_set_sizes={k:len(v) for k,v in a.roomsets.items()},removal_files=a.removals.files,source_manifest=a.manifest))
 (ROOT/'STATUS.md').write_text('N source admission complete. Counts kept by type: '+enc(dict(keep))+'. SOURCE_AUDIT.json and SOURCE_ADMISSION.jsonl record every exclusion and authenticated scene resolution. Training generation and scorer patch validation remain.\n')
 print(enc(dict(total=total,kept=keep,marginal=marginal,joint=joint)))
if __name__=='__main__':main()
