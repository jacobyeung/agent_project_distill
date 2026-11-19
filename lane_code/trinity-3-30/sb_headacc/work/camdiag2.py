import sys, json, re, statistics as st
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
R=K.routed(544, types=['camera_rotation','camera_movement_direction'])
n=0
for r in R:
    if r['type']=='camera_rotation' and n<6:
        print(r['question'][:230].replace('\n',' ')); print('   ', r['calls'][-1]['call'], '|', r['calls'][-1]['response'], '| gt', r['gt'], 'ans', r['answer'], 'score', r['score']); n+=1
m=[r for r in R if r['type']=='camera_movement_direction']
print(m[0]['question'][:400]); print(m[0]['options'], m[0]['calls'][-1], m[0]['gt'], m[0]['answer'], m[0]['score'])
rot=json.load(open('camdiag_camera_rotation.json'))
import collections
print('rotation truth values:', sorted(collections.Counter(round(x['g']) for x in rot).items())[:40])
small=[x for x in rot if x['g']<=10]
print('truth<=10: n', len(small), 'abs err hist', sorted(collections.Counter(round(abs(x['a']-x['g'])) for x in small).items()))
print('  lost MRA mass share by band:', {b: round(sum(1-x['s'] for x in rot if lo<x['g']<=hi)/sum(1-x['s'] for x in rot),2) for b,(lo,hi) in dict(le5=(-1,5), le10=(5,10), le20=(10,20), gt20=(20,999)).items()})
disp=json.load(open('camdiag_camera_displacement.json'))
print('displacement lost MRA share by band:', {b: round(sum(1-x['s'] for x in disp if lo<x['g']<=hi)/sum(1-x['s'] for x in disp),2) for b,(lo,hi) in dict(le025=(-1,.25), le05=(.25,.5), le1=(.5,1), gt1=(1,99)).items()})
sd=[x for x in disp if x['g']<=.25]; print('disp truth<=0.25: abs err median %.3f, truth median %.3f, n over %d of %d' % (st.median(abs(x['a']-x['g']) for x in sd), st.median(x['g'] for x in sd), sum(x['a']>x['g'] for x in sd), len(sd)))
print('   gap hist for truth<=0.25:', sorted(collections.Counter(abs(x['j']-x['i']) for x in sd).items()))
