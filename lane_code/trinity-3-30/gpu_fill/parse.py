import re,sys,json,html,time
s=open(sys.argv[1]).read()
EXCL={'trinity-0-8','trinity-0-23','trinity-3-23','trinity-0-18','trinity-2-18','trinity-2-28'}
out={}
parts=re.split(r'<h2 id="(trinity-[0-9-]+)">',s)
for i in range(1,len(parts),2):
    node=parts[i]; body=parts[i+1]
    upd=re.search(r'Updated at ([^<]+)<',body); scr=re.search(r'/scratch \(HDD\):</td>\s*<td>([^<]+)<',body)
    cards=[]
    tb=body.split('gputable',1)
    if len(tb)>1:
        for row in re.findall(r'<tr>(.*?)</tr>',tb[1],re.S):
            tds=re.findall(r'<td>(.*?)</td>',row,re.S)
            if len(tds)<4: continue
            w=re.search(r'width:\s*([\d.]+)%',tds[2]); av=re.search(r'<div>(\d+)</div>',tds[2])
            jobs=html.unescape(re.sub(r'<[^>]+>','',tds[3])).strip()
            users=sorted(set(re.findall(r'\(([a-z0-9_]+)\)',jobs)))
            cards.append(dict(id=int(re.sub(r'\D','',tds[0]) or -1),name=tds[1].strip(),usedpct=float(w.group(1)) if w else None,avail=int(av.group(1)) if av else None,users=users,jobs=jobs[:120]))
    out[node]=dict(updated=upd.group(1) if upd else '',scratch=scr.group(1) if scr else '',cards=cards,permitted=node not in EXCL)
json.dump(out,open(sys.argv[2],'w'))
def big(c): return ('6000' in c['name'] or 'A6000' in c['name'] or 'A40' in c['name'] or 'L40' in c['name'])
lines=[]
fc=0
for n,d in out.items():
    if not d['permitted']: continue
    bigc=[c for c in d['cards'] if big(c)]
    if not bigc: continue
    free=[c['id'] for c in bigc if not c['users'] and (c['avail'] or 0)>45000]
    fc+=len(free)
    us=sorted({u for c in bigc for u in c['users']})
    lines.append(f"- {n} ({bigc[0]['name'].replace('NVIDIA ','')} x{len(bigc)}; /scratch {d['scratch']}; upd {d['updated'][11:19]}): free {free if free else 'none'}; users {','.join(us)}")
print(fc); print('\n'.join(lines))
