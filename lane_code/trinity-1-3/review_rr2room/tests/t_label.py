import sys,json
X='/scratch/jjyeung/orch_n30/review_rr2room/x'
sys.path[:0]=[X+'/b',X+'/tree',X]
from h1eval import scorers
m=json.load(open(X+'/items/room134.json'));it={r['id']:r for r in m['items']}
item=it['room_scene0155_00']
out={'finish':'eos','text':'<think>x</think><answer>32.50</answer>','calls':{'records':[]},'scores':{'answer':1.0}}
print('label answer',item['answer'],'ground_truth',item['ground_truth'])
print('room_pair path scorers.benchmark ->',scorers.benchmark(out,item)['score'])
print('job1 tower_pair path scorers.accuracy ->',scorers.accuracy(out,item)['task_accuracy'])
o2=dict(out);o2.pop('scores')
print('accuracy without native scores ->',scorers.accuracy(o2,item)['task_accuracy'])
