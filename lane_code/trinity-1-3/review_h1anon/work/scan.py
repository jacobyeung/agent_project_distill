import re,sys,json
P=re.compile(r"(?i)scannet(pp)?|arkit\w*|scene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b")
for f in sys.argv[1:]:
    try: t=open(f,errors='replace').read()
    except Exception as e: print(f,'ERR',e); continue
    n=0
    for i,l in enumerate(t.splitlines(),1):
        for m in P.finditer(l):
            n+=1
            if '-v' in sys.argv[0:0]: pass
            print(f"{f}:{i}:{m.group(0)}:: {l[max(0,m.start()-80):m.end()+80]}")
    print(f"## {f} hits={n}",file=sys.stderr)
