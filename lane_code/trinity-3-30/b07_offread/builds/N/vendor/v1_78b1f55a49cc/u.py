"""Verify both staged copies and seal the late upload receipt; operator only."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from adapter import load,dump,sha
from o import PREFIX,CLOUD,validate_additions


def verify(family_path,generations,output):
    family=load(family_path);pins=load(generations);records={}
    for key in 'abcd':
        path=Path(PREFIX+key+'.tar');digest=sha(path);size=path.stat().st_size
        expected=family['added'][key].get('sha256')
        if expected and digest!=expected:raise ValueError('primary copy differs from family')
        record=dict(path=str(path),name=CLOUD+key+'.tar',sha256=digest,bytes=size,generation=str(pins[key]),verified=False)
        if not record['generation'].isdigit():raise ValueError('explicit cloud generation required')
        uri='gs://cmu-gpucloud-jjyeung/'+record['name']+'#'+record['generation']
        env=dict(os.environ,CLOUDSDK_CONFIG='/project/community/jjyeung/gcloud');h=hashlib.sha256();total=0
        with subprocess.Popen(['/usr/bin/gcloud','storage','cat',uri],stdout=subprocess.PIPE,env=env) as proc:
            for block in iter(lambda:proc.stdout.read(1024**2),b''):h.update(block);total+=len(block)
            if proc.wait():raise ValueError('second-copy stream failed; no retry')
        if total!=size or h.hexdigest()!=digest:raise ValueError('second copy differs')
        record['verified']=True;records[key]=record
    validate_additions(records);dump(output,records);return records


def main():
    p=argparse.ArgumentParser()
    for n in ('family','generations','out'):p.add_argument('--'+n,required=True)
    a=p.parse_args();verify(a.family,a.generations,a.out)
if __name__=='__main__':main()
