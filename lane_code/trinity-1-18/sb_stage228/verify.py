import os,json,sys
L=[l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
nf=nb=miss=0
for p in L:
    try: s=os.lstat(p)
    except FileNotFoundError: miss+=1; continue
    import stat
    if stat.S_ISREG(s.st_mode): nf+=1; nb+=s.st_size
print(json.dumps(dict(entries=len(L),present=len(L)-miss,missing=miss,files=nf,bytes=nb)))
