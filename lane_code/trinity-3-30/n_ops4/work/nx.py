# read-only operand-noun extraction from staged input row stores of one job (n_ops4, ORCH ORDER 0546Z)
import sqlite3,json,re,gzip,hashlib,os,sys,time,resource
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
J=sys.argv[1]; Q='/tmp/q_22c714e1_%s/s/aws/u/ap'%J; OUT=sys.argv[2]
STORES=['/1742c666/s/q127808/vxm_m4','/1742c666/s/q127808/vxm_out','/bb09a77d/v','/5e1d07a4/f/r1','/5e1d07a4/f/h/r9','/5e1d07a4/f/h/r11','/5e1d07a4/f/h/r15','/5e1d07a4/f/h/r16']
CATS=('object_counting','object_rel_distance','object_abs_distance','routing_trace')
R_LIST=re.compile(r'\(([^()]+)\)'); R_TO=re.compile(r'(?:closest|farthest|nearest|furthest) (?:to|from) the ([a-z][a-z0-9 \-/]*?)\?',re.I)
R_PAIR=re.compile(r'(?:between |apart )?the ([a-z][a-z0-9 \-/]*?) and the ([a-z][a-z0-9 \-/]*?)(?: are| is|\?|,| at| in|$)',re.I)
R_CNT=re.compile(r'how many ([a-z][a-z0-9 \-/]*?)(?:\(s\)|s)? (?:do|are|is|can|in)',re.I)
def names(cat,q,opts):
  n=[]
  if cat=='object_counting':
    m=R_CNT.search(q); n+= [m.group(1)] if m else []
  else:
    m=R_LIST.search(q)
    if m and ',' in m.group(1): n+=[x.strip() for x in m.group(1).split(',')]
    m=R_TO.search(q); n+= [m.group(1)] if m else []
    if not n:
      m=R_PAIR.search(q); n+= [m.group(1),m.group(2)] if m else []
  n=[x.split(' the ')[-1] for x in n]
  return [x.lower().strip() for x in n if x and len(x)<40]
clips={}; stats={}; seen=set(); t0=time.time()
for s in STORES:
  f=Q+s+'/rows.sqlite'
  if not os.path.exists(f): stats[s]='missing'; continue
  c=sqlite3.connect('file:'+f+'?mode=ro&immutable=1',uri=True); k=[0,0,0]
  for qid,ds,cat,sc,q,opts in c.execute("select json_extract(row,'$.qid'),json_extract(row,'$.dataset'),json_extract(row,'$.category'),json_extract(row,'$.scene'),json_extract(row,'$.student_input.question'),json_extract(row,'$.student_input.options') from rows"):
    k[0]+=1
    if cat not in CATS or qid in seen: continue
    seen.add(qid); k[1]+=1; q=q or ''
    e=clips.setdefault(sc,{'dataset':ds,'names':{},'unparsed':{}})
    n=names(cat,q,opts)
    if n: e['names'].setdefault(cat,set()).update(n)
    else:
      k[2]+=1; u=e['unparsed'].setdefault(cat,[])
      if len(u)<5 and q not in u: u.append(q)
  stats[s]={'rows':k[0],'kept_unique':k[1],'unparsed':k[2]}; c.close()
for e in clips.values(): e['names']={a:sorted(b) for a,b in e['names'].items()}
doc={'what':'operand object names per clip (row.scene) from rows of categories %s in the staged input stores of job %s; a SUPERSET of N admitted rows (input stores before N selection/removals); unparsed = question text when no template matched (<=5 per clip and category); dataset tag kept (d1/d2/d3), ARKit mapping not applied here'%(','.join(CATS),J),
 'stores':stats,'clips':clips,'n_clips':len(clips),'seconds':round(time.time()-t0)}
b=gzip.compress(json.dumps(doc,sort_keys=True).encode())
open(OUT,'xb').write(b); print('wrote',OUT,len(b),hashlib.sha256(b).hexdigest()); print(json.dumps(stats))
