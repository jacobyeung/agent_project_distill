from load import *
import collections, statistics as st, random
T={'object_size_estimation'}
a=load(P544,T); b=load(PD200,T)
A=load(A544,T); B=load(I200,T)
rows=[]; MM=[]
for k in sorted(a):
    x=a[k]; y=b[k]
    g=num(x['ground_truth']); 
    pa=num(x['extracted_answer']); pb=num(y['extracted_answer'])
    sa=x['score']; sb=y['score']
    assert abs(sa-A[k]['score'])<1e-9 and abs(sb-B[k]['score'])<1e-9, k
    MM.append(int(abs(mra(pa,g)-sa)>1e-9)+int(abs(mra(pb,g)-sb)>1e-9))
    u=unit(x['question'])
    rows.append(dict(id=k,ds=x['dataset'],room=x['room'],q=x['question'],u=u,g=g,pa=pa,pb=pb,sa=sa,sb=sb,ra=(pa/g if pa else None),rb=(pb/g if pb else None),ga=x['raw_generation'],gb=y['raw_generation'],cap_a=x['hit_token_cap'],cap_b=y['hit_token_cap'],pfa=x['parse_failed'],pfb=y['parse_failed']))
json.dump(rows,open('size_rows_544_m200.json','w')); print('mra recompute mismatches (float boundary)',sum(MM))
n=len(rows); print('items',n, 'mean MRA 544 %.2f  m200 %.2f  delta %.2f'%(100*sum(r['sa'] for r in rows)/n,100*sum(r['sb'] for r in rows)/n,100*sum(r['sb']-r['sa'] for r in rows)/n))
print('parse fail 544',sum(r['pfa'] for r in rows),'m200',sum(r['pfb'] for r in rows),'| cap',sum(r['cap_a'] for r in rows),sum(r['cap_b'] for r in rows),'| None pred',sum(r['pa'] is None for r in rows),sum(r['pb'] is None for r in rows))
def lr(v): return math.log(v) if v and v>0 else None
for lab,key in (('544','ra'),('m200','rb')):
    L=[lr(r[key]) for r in rows if lr(r[key]) is not None]
    L.sort()
    print(lab,'log2 ratio: median %.3f mean %.3f sd %.3f  IQR [%.3f, %.3f]  n=%d'%(st.median(L)/math.log(2),st.mean(L)/math.log(2),st.pstdev(L)/math.log(2),L[len(L)//4]/math.log(2),L[3*len(L)//4]/math.log(2),len(L)))
    print('   ratio median %.3f; share pred>gt %.3f; |log ratio|>log2 (off by >2x) %d'%(math.exp(st.median(L)),sum(1 for v in L if v>0)/len(L),sum(1 for v in L if abs(v)>math.log(2))))
print()
print('by unit:')
for u in sorted(set(r['u'] for r in rows)):
    R=[r for r in rows if r['u']==u]
    La=[lr(r['ra']) for r in R if lr(r['ra']) is not None]; Lb=[lr(r['rb']) for r in R if lr(r['rb']) is not None]
    print('  %-3s n=%3d  MRA 544 %.1f  m200 %.1f  d %+.1f | med ratio 544 %.3f m200 %.3f | sd log2 %.2f %.2f'%(u,len(R),100*st.mean(r['sa'] for r in R),100*st.mean(r['sb'] for r in R),100*st.mean(r['sb']-r['sa'] for r in R),math.exp(st.median(La)),math.exp(st.median(Lb)),st.pstdev(La)/math.log(2),st.pstdev(Lb)/math.log(2)))
print('by dataset:')
for u in sorted(set(r['ds'] for r in rows)):
    R=[r for r in rows if r['ds']==u]
    La=[lr(r['ra']) for r in R if lr(r['ra']) is not None]; Lb=[lr(r['rb']) for r in R if lr(r['rb']) is not None]
    print('  %-12s n=%3d  MRA 544 %.1f  m200 %.1f  d %+.1f | med ratio 544 %.3f m200 %.3f | sd log2 %.2f %.2f'%(u,len(R),100*st.mean(r['sa'] for r in R),100*st.mean(r['sb'] for r in R),100*st.mean(r['sb']-r['sa'] for r in R),math.exp(st.median(La)),math.exp(st.median(Lb)),st.pstdev(La)/math.log(2),st.pstdev(Lb)/math.log(2)))
