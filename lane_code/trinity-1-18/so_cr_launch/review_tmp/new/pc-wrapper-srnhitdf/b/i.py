import os,time
def event(name):
    with open(os.environ["TRACE"], "a") as f: f.write(name+" "+os.environ["SLURM_JOB_ID"]+"\n")
event("i-start")
time.sleep(.15)
event("i-end")
