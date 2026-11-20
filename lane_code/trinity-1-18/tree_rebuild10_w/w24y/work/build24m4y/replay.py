from pathlib import Path
import sys,json,shutil
L=Path.cwd();D=L/"work/build24m4y";U=L/"work/build24m4u"
sys.path[:0]=[str(L/"out/rcj"),str(L/"out/kit_qd/b")]
import x,z
R=U/"real173725";source=U/"publication_source";dest=D/"publication_result";dest.mkdir()
original=z.load(U/"REAL_INPUTS.json")["files"]
for n,v in original.items():assert z.sha(R/n)==v["sha256"] and (R/n).stat().st_size==v["bytes"]
timing=z.load(R/"timings.json")
timing["republication"]=z.load(U/"publication_result/timings.json")["republication"]
x.bounded_publication(source,dest,timing);z.write(dest/"timings.json",timing)
total=sum(p.stat().st_size for p in dest.rglob("*") if p.is_file())
assert total==timing["aggregate_publication_bytes"]<5_000_000
actual={str(p.relative_to(dest)):z.sha(p) for p in dest.rglob("*") if p.is_file()}
baseline={str(p.relative_to(U/"publication_result")):z.sha(p) for p in (U/"publication_result").rglob("*") if p.is_file()}
assert actual==baseline,(actual.keys()^baseline.keys())
z.write(D/"PUBLICATION_REPLAY.json",dict(status="PASS",bytes=total,files=len(actual),same_as_24m4u=True,original_files_verified=len(original),cpu_job_rerun=False,original_job=173725))
print("PUBLICATION PASS",total,len(actual))
