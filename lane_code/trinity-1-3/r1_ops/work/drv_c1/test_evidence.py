"""Exercise sealed evidence validation without copying large archive/frame inputs."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path

def check_mutations(bundle,ready,directory):
    def write(p,v):p.write_text(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n')
    for name,field in [('review.json','config_sha256'),('staging.json','config_sha256'),('archive.json','tree_sha256'),('4.json','config_sha256')]:
        target=directory/('evidence_case_'+name);(target/'k').mkdir(parents=True)
        shutil.copytree(ready/'b',target/'b')
        launch=json.loads((ready/'k/launch.json').read_text())
        names={'k/launch.json','k/7.json','k/4.json'}|{launch[key]['file'] for key in ('config','review','staging','archive')}
        for relative in names:
            p=ready/relative
            if p.stat().st_size>2_000_000:raise ValueError('Unexpected large metadata fixture')
            shutil.copyfile(p,target/'k'/p.name)
        p=target/'k'/name;data=json.loads(p.read_text());data[field]='0'*64;write(p,data)
        launch=json.loads((target/'k/launch.json').read_text())
        key={'review.json':'review','staging.json':'staging','archive.json':'archive'}.get(name)
        if key:launch[key]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        write(target/'k/launch.json',launch)
        command="import importlib.util,sys;from pathlib import Path;s=importlib.util.spec_from_file_location('sealed_deriver',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.validate_evidence(Path(sys.argv[2]))"
        result=subprocess.run([sys.executable,'-B','-c',command,str(bundle/'d.py'),str(target)],capture_output=True,text=True)
        assert result.returncode and ('Evidence identity' in result.stderr or 'Off-scratch source archive is not attested' in result.stderr),result.stderr
    print('PASS sealed evidence validator refuses four wrong identities using metadata-only fixtures')

if __name__=='__main__':
    check_mutations(*map(Path,sys.argv[1:]))
