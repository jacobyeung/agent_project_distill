import json,glob,os
# card-hours since the first tick from monitor snapshots (10-min ticks): used = distillation cards on 1-13 (user jjyeung), avail = used + free permitted 48 GB cards
def big(c): return any(k in c['name'] for k in ('6000','A40','L40'))
MAIN={('trinity-1-13',6):'20261116T1630Z',('trinity-1-13',7):'20261116T1630Z'}  # cards main holds (also user jjyeung), from stamp
used=free=mainh=0.0; n=0; last=''
for f in sorted(glob.glob('hist/2*.json')):
    d=json.load(open(f)); n+=1; last=os.path.basename(f)[:-5]
    for node,v in d.items():
        if not v['permitted']: continue
        for c in v['cards']:
            if not big(c): continue
            if not c['users'] and (c['avail'] or 0)>45000: free+=1/6
            elif node=='trinity-1-13' and c['users']==['jjyeung']:
                st=MAIN.get((node,c['id']))
                if st and last>=st: mainh+=1/6
                else: used+=1/6
first=os.path.basename(sorted(glob.glob('hist/2*.json'))[0])[:-5]
print(f"Card-hours {first}..{last} ({n} ticks): distillation used {used:.1f} of {used+free:.1f} available on permitted 48 GB cards ({free:.1f} idle; main's 1-13 cards 6,7 {mainh:.1f} excluded; idle mostly 1-13 /dev/shm budget and 0-28 disk).")
